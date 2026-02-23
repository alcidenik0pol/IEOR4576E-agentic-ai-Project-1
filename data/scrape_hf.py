"""
HuggingFace Top 100 Models Scraper

Fetches the top 100 models by downloads from HuggingFace API
and saves them as a frozen JSON snapshot for use as ground truth.
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx

HF_API_BASE = "https://huggingface.co/api"
MODELS_ENDPOINT = f"{HF_API_BASE}/models"
README_TEMPLATE = "https://huggingface.co/{model_id}/raw/main/README.md"

# Rate limiting: HF allows ~1000 req/hr for anonymous users
REQUEST_TIMEOUT = 30.0
MAX_RETRIES = 3


def extract_parameter_count(tags: list[str], card_text: str) -> tuple[int | None, str]:
    """
    Extract parameter count from tags or model card text.
    Returns (count, source) where source is 'tags', 'card_text', or 'missing'.
    """
    # First, check tags for patterns like "7B", "13B", "70B"
    param_pattern = re.compile(r"(\d+(?:\.\d+)?)[Bb]")
    for tag in tags:
        match = param_pattern.search(tag)
        if match:
            value = float(match.group(1))
            return int(value * 1e9), "tags"

    # Then check model card text
    if card_text:
        # Look for patterns like "7B parameters", "7 billion parameters"
        card_patterns = [
            r"(\d+(?:\.\d+)?)[Bb]\s*(?:illion)?\s*parameters?",
            r"(\d+(?:\.\d+)?)[Bb]\s+model",
        ]
        for pattern in card_patterns:
            match = re.search(pattern, card_text, re.IGNORECASE)
            if match:
                value = float(match.group(1))
                return int(value * 1e9), "card_text"

    return None, "missing"


def extract_license(tags: list[str], card_text: str) -> tuple[str | None, str]:
    """
    Extract license from tags or YAML front matter in model card.
    Returns (license, source) where source is 'tags', 'card_yaml', or 'missing'.
    """
    # First, check tags for "license:*" pattern
    for tag in tags:
        if tag.startswith("license:"):
            license_val = tag[8:]  # Remove "license:" prefix
            return license_val, "tags"

    # Then check YAML front matter in model card
    if card_text and card_text.startswith("---"):
        # Find the end of YAML front matter
        yaml_end = card_text.find("---", 3)
        if yaml_end != -1:
            yaml_content = card_text[3:yaml_end]
            # Look for license: line
            license_match = re.search(r"^license:\s*(\S+)", yaml_content, re.MULTILINE)
            if license_match:
                return license_match.group(1), "card_yaml"

    return None, "missing"


def fetch_model_card(model_id: str, client: httpx.Client) -> str:
    """Fetch the README.md for a model."""
    url = README_TEMPLATE.format(model_id=model_id)
    try:
        response = client.get(url, timeout=REQUEST_TIMEOUT)
        if response.status_code == 200:
            return response.text[:2000]  # First 2000 chars for summary
    except Exception:
        pass
    return ""


def fetch_top_models(limit: int = 100) -> list[dict[str, Any]]:
    """Fetch top models by downloads from HuggingFace API."""
    params = {
        "sort": "downloads",
        "direction": "-1",
        "limit": limit,
        "full": "true",
    }

    with httpx.Client(timeout=REQUEST_TIMEOUT) as client:
        response = client.get(MODELS_ENDPOINT, params=params)
        response.raise_for_status()
        models_data = response.json()

        results = []
        for model in models_data:
            model_id = model.get("id", "")
            if not model_id:
                continue

            # Fetch model card for additional info
            card_text = fetch_model_card(model_id, client)

            # Extract tags
            tags = model.get("tags", [])

            # Extract parameter count
            param_count, param_source = extract_parameter_count(tags, card_text)

            # Extract license from tags or model card YAML
            license_info, license_source = extract_license(tags, card_text)

            # Build model record
            record = {
                "model_id": model_id,
                "downloads": model.get("downloads", 0),
                "likes": model.get("likes", 0),
                "pipeline_tag": model.get("pipeline_tag", "unknown"),
                "tags": tags,
                "createdAt": model.get("createdAt", ""),
                "license": license_info,
                "parameter_count": param_count,
                "model_card_summary": card_text[:500] if card_text else "",
                "_metadata": {
                    "snapshot_date": datetime.now().strftime("%Y-%m-%d"),
                    "parameter_count_source": param_source,
                    "license_source": license_source,
                },
            }
            results.append(record)

        return results


def main():
    """Main entry point for scraping."""
    print("Fetching top 100 HuggingFace models...")

    models = fetch_top_models(limit=100)

    # Generate filename with date
    date_str = datetime.now().strftime("%Y%m%d")
    output_file = Path(__file__).parent / f"models_snapshot_{date_str}.json"

    # Save to JSON
    output_data = {
        "snapshot_date": datetime.now().isoformat(),
        "model_count": len(models),
        "models": models,
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(f"Saved {len(models)} models to {output_file}")

    # Print summary stats
    licenses_missing = sum(1 for m in models if m["license"] is None)
    params_missing = sum(1 for m in models if m["parameter_count"] is None)
    print(f"Missing licenses: {licenses_missing}/{len(models)}")
    print(f"Missing parameter counts: {params_missing}/{len(models)}")


if __name__ == "__main__":
    main()
