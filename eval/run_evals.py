"""
Evaluation harness for HuggingFace Models Explorer.

This script runs evaluations against the chatbot using:
1. Deterministic metrics for golden reference cases
2. MaaJ (Model-as-a-Judge) for rubric-based evaluations

Usage:
    uv run python eval/run_evals.py
"""

import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any

import vertexai
from vertexai.generative_models import GenerativeModel, GenerationConfig

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.backstop import check_out_of_scope

# Configuration
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "agenticaicolumbia")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
MODEL_ID = os.getenv("VERTEX_MODEL_ID", "gemini-2.0-flash-exp")
DATA_FILE = Path(__file__).parent.parent / "data" / "models_snapshot_20260221.json"
GOLDEN_DATASET = Path(__file__).parent / "golden_dataset.json"
CREDENTIALS_FILE = Path(__file__).parent.parent / "credentials" / "agenticaicolumbia-c7e402d63456.json"

# Set credentials if not already set
if "GOOGLE_APPLICATION_CREDENTIALS" not in os.environ and CREDENTIALS_FILE.exists():
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(CREDENTIALS_FILE)


def load_data():
    """Load model data and golden dataset."""
    with open(DATA_FILE, encoding="utf-8") as f:
        model_data = json.load(f)

    with open(GOLDEN_DATASET, encoding="utf-8") as f:
        golden_dataset = json.load(f)

    return model_data["models"], golden_dataset


def format_context_for_llm(models_data: list[dict]) -> str:
    """Format model data for LLM context - matches main app format."""
    lines = ["Here is the data for the top 100 HuggingFace models by downloads:\n"]
    for m in models_data[:50]:  # Include more models
        created = m.get('createdAt', '')[:10] if m.get('createdAt') else 'Unknown'
        params = f", params={m['parameter_count']/1e9:.1f}B" if m.get('parameter_count') else ""
        lines.append(f"- {m['model_id']}: {m['downloads']:,} downloads, {m['pipeline_tag']}, license={m['license']}, created={created}{params}")
    return "\n".join(lines)


def call_chat_api(question: str, models_data: list[dict], llm: GenerativeModel) -> dict:
    """Simulate the chat API call locally."""
    # Check backstop
    is_oos, oos_response = check_out_of_scope(question)
    if is_oos:
        return {
            "answer": oos_response,
            "confidence": 1.0,
            "sources": [],
            "out_of_scope": True,
        }

    # Build prompt
    context = format_context_for_llm(models_data)
    prompt = f"""You are the HuggingFace Models Assistant. Answer questions about the top 100 HuggingFace models.

{context}

Question: {question}

Provide a helpful, accurate answer based on the model data above. If you don't have information, say so."""

    # Call LLM
    try:
        config = GenerationConfig(temperature=0.3, max_output_tokens=1024)
        response = llm.generate_content(prompt, generation_config=config)
        return {
            "answer": response.text,
            "confidence": 0.8,
            "sources": [],
            "out_of_scope": False,
        }
    except Exception as e:
        return {
            "answer": f"Error: {str(e)}",
            "confidence": 0.0,
            "sources": [],
            "out_of_scope": False,
        }


def evaluate_golden_reference(case: dict, response: dict) -> tuple[bool, str]:
    """
    Evaluate a golden reference case.
    Returns (passed, explanation).
    """
    # Out-of-scope cases
    if case.get("expected_out_of_scope"):
        if response["out_of_scope"]:
            return True, "Correctly identified as out of scope"
        return False, "Should have been identified as out of scope"

    # Single model / multi filter cases
    answer = response["answer"].lower()

    # Check expected answer
    if "expected_answer" in case:
        expected = case["expected_answer"].lower()
        # Normalize answer for comparison (remove hyphens, commas, spaces)
        normalized_answer = answer.lower().replace("-", "").replace(",", "").replace(" ", "")
        normalized_expected = expected.replace("-", "").replace(",", "").replace(" ", "")
        if normalized_expected in normalized_answer:
            return True, f"Found expected answer '{case['expected_answer']}' in response"
        return False, f"Expected '{case['expected_answer']}' not found in response"

    # Check expected models
    if "expected_models" in case:
        found = []
        missing = []
        for model_id in case["expected_models"]:
            # Check both with and without organization prefix
            model_name = model_id.split("/")[-1].lower()
            full_id = model_id.lower()
            if model_name in answer or full_id in answer:
                found.append(model_id)
            else:
                missing.append(model_id)

        if not missing:
            return True, f"All expected models found: {found}"
        if found:
            return False, f"Partial match. Found: {found}, Missing: {missing}"
        return False, f"No expected models found. Expected: {case['expected_models']}"

    return False, "No evaluation criteria defined"


def evaluate_rubric_maaJ(case: dict, response: dict, llm: GenerativeModel) -> tuple[float, str]:
    """
    Use MaaJ to evaluate a rubric-based case.
    Returns (score, explanation).
    """
    rubric = case.get("rubric", {})

    # Build evaluation prompt
    eval_prompt = f"""You are an evaluator for a HuggingFace Models chatbot.

Question: {case['question']}
Response: {response['answer']}

Evaluate the response on these criteria (score each 0-1):

"""
    for criterion, description in rubric.items():
        eval_prompt += f"- {criterion}: {description}\n"

    eval_prompt += """
Respond in JSON format:
{
  "scores": {"criterion_name": 0-1, ...},
  "total_score": average of all scores,
  "explanation": "brief explanation"
}
"""

    try:
        config = GenerationConfig(temperature=0.1, max_output_tokens=512)
        eval_response = llm.generate_content(eval_prompt, generation_config=config)
        eval_text = eval_response.text

        # Parse JSON from response
        json_match = re.search(r"\{[\s\S]*\}", eval_text)
        if json_match:
            result = json.loads(json_match.group())
            score = result.get("total_score", 0)
            explanation = result.get("explanation", "")
            return score, explanation
    except Exception as e:
        pass

    return 0.0, "Could not evaluate"


def evaluate_maaJ_golden(case: dict, response: dict, llm: GenerativeModel) -> tuple[bool, str]:
    """
    Use MaaJ to evaluate if a golden reference answer matches.
    Returns (passed, explanation).
    """
    # Use custom eval_prompt if provided, otherwise build default
    if case.get("eval_prompt"):
        eval_prompt = f"""You are an evaluator for a HuggingFace Models chatbot.

Question: {case['question']}
Actual Response: {response['answer']}

Evaluation criteria: {case['eval_prompt']}

Respond in JSON format:
{{"passed": true/false, "explanation": "brief explanation"}}
"""
    else:
        expected = case.get('expected_answer', case.get('expected_models', 'N/A'))
        eval_prompt = f"""You are an evaluator for a HuggingFace Models chatbot.

Question: {case['question']}
Expected Answer: {expected}
Actual Response: {response['answer']}

Does the actual response contain the key information from the expected answer?

For model IDs, check if the model names appear in the response.

Respond in JSON format:
{{"passed": true/false, "explanation": "brief explanation"}}
"""

    try:
        config = GenerationConfig(temperature=0.1, max_output_tokens=256)
        eval_response = llm.generate_content(eval_prompt, generation_config=config)
        eval_text = eval_response.text

        json_match = re.search(r"\{[\s\S]*\}", eval_text)
        if json_match:
            result = json.loads(json_match.group())
            return result.get("passed", False), result.get("explanation", "")
    except Exception:
        pass

    return False, "Could not evaluate"


def run_evaluations(models_data: list[dict], golden_dataset: list[dict], llm: GenerativeModel):
    """Run all evaluations and print results."""
    results = {
        "deterministic": {"passed": 0, "total": 0},
        "maaj_golden": {"passed": 0, "total": 0, "total_score": 0.0},
        "maaj_rubric": {"total": 0, "total_score": 0.0},
        "out_of_scope": {"passed": 0, "total": 0},
    }

    print("=" * 60)
    print("HuggingFace Models Explorer - Evaluation Results")
    print("=" * 60)
    print()

    for case in golden_dataset:
        case_id = case["id"]
        question = case["question"]
        category = case["category"]
        eval_type = case["evaluation"]

        # Skip empty questions (edge case test)
        if not question:
            print(f"[SKIP] {case_id}: Empty question")
            continue

        print(f"\n[{case_id}] {question[:60]}...")

        # Get response
        response = call_chat_api(question, models_data, llm)

        # Rate limit avoidance
        time.sleep(5)

        # Evaluate based on type
        if category == "out_of_scope":
            results["out_of_scope"]["total"] += 1
            if eval_type == "golden_reference":
                passed, explanation = evaluate_golden_reference(case, response)
            else:
                passed, explanation = evaluate_maaJ_golden(case, response, llm)

            if passed:
                results["out_of_scope"]["passed"] += 1
                print(f"  [OK] PASSED: {explanation}")
            else:
                print(f"  [X] FAILED: {explanation}")

        elif eval_type == "golden_reference":
            results["deterministic"]["total"] += 1
            passed, explanation = evaluate_golden_reference(case, response)
            if passed:
                results["deterministic"]["passed"] += 1
                print(f"  [OK] PASSED: {explanation}")
            else:
                print(f"  [X] FAILED: {explanation}")
                print(f"    Response: {response['answer'][:200]}...")

        elif eval_type == "maaj_golden":
            results["maaj_golden"]["total"] += 1
            passed, explanation = evaluate_maaJ_golden(case, response, llm)
            if passed:
                results["maaj_golden"]["passed"] += 1
                print(f"  [OK] MaaJ PASSED: {explanation}")
            else:
                print(f"  [X] MaaJ FAILED: {explanation}")

        elif eval_type == "rubric":
            results["maaj_rubric"]["total"] += 1
            score, explanation = evaluate_rubric_maaJ(case, response, llm)
            results["maaj_rubric"]["total_score"] += score
            print(f"  Score: {score:.2f}/1.0 - {explanation}")

    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    det = results["deterministic"]
    if det["total"] > 0:
        pct = det["passed"] / det["total"] * 100
        print(f"Deterministic: {det['passed']}/{det['total']} ({pct:.0f}%)")

    maaj_gold = results["maaj_golden"]
    if maaj_gold["total"] > 0:
        pct = maaj_gold["passed"] / maaj_gold["total"] * 100
        print(f"MaaJ Golden Reference: {maaj_gold['passed']}/{maaj_gold['total']} ({pct:.0f}%)")

    oos = results["out_of_scope"]
    if oos["total"] > 0:
        pct = oos["passed"] / oos["total"] * 100
        print(f"Out-of-scope detection: {oos['passed']}/{oos['total']} ({pct:.0f}%)")

    rubric = results["maaj_rubric"]
    if rubric["total"] > 0:
        avg = rubric["total_score"] / rubric["total"] * 5  # Scale to 1-5
        print(f"MaaJ Rubric: {rubric['total']} cases (avg score: {avg:.1f}/5)")

    # Overall
    total_passed = det["passed"] + oos["passed"] + maaj_gold["passed"]
    total_cases = det["total"] + oos["total"] + rubric["total"] + maaj_gold["total"]
    print(f"\nOverall: {total_passed}/{total_cases} passed")
    print(f"Coverage: {total_cases} test cases")


def main():
    """Main entry point."""
    print("Initializing Vertex AI...")
    vertexai.init(project=PROJECT_ID, location=LOCATION)
    llm = GenerativeModel(MODEL_ID)

    print("Loading data...")
    models_data, golden_dataset = load_data()

    print(f"Loaded {len(models_data)} models and {len(golden_dataset)} test cases\n")

    run_evaluations(models_data, golden_dataset, llm)


if __name__ == "__main__":
    main()
