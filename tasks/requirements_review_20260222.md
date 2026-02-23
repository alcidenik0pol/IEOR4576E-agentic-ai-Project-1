# Requirements Review: Project 1 - Domain Q&A Chatbot

**Generated:** 2026-02-22
**Reviewer:** Claude Code
**Topic:** HuggingFace Models Explorer

---

## 1. App Requirements

| Requirement | Status | Implementation |
|-------------|--------|----------------|
| Pick a niche topic narrow enough for 20+ test questions | DONE | HuggingFace top 100 models (frozen snapshot) - narrow domain with rich metadata |
| Backend: FastAPI | DONE | `app/main.py:18-214` - FastAPI app with `/health`, `/chat`, `/` endpoints |
| Frontend: simple web UI | DONE | `static/index.html` (361 lines) - dark theme, confidence bar, source links |
| Deploy on GCP and provide live URL | READY | `Dockerfile` configured for Cloud Run; deployment pending |

---

## 2. Prompt Requirements

| Requirement | Status | Implementation |
|-------------|--------|----------------|
| Role/persona (domain voice + boundaries) | DONE | `app/prompts/system_prompt.py:12-18` - "You are the HuggingFace Models Assistant" |
| Few-shot examples (>=3) | DONE | `app/prompts/system_prompt.py:32-101` - 6 few-shot examples (license lookup, task filtering, top model, license filter, comparison, date filter) |
| Statically fix or dynamically load examples | DONE | Static examples embedded in system prompt |
| Organization method | DONE | `app/prompts/system_prompt.py:104-118` - `build_context_prompt()` formats 100 models + `format_chat_prompt()` combines system/context/question |
| Positive constraints (define what it can answer) | DONE | `app/prompts/system_prompt.py:20-30` - SCOPE section lists available data fields (no "don't do X") |
| Escape hatch (what to do when unsure) | DONE | `app/prompts/system_prompt.py:112-116` - "I'm not sure - the available data doesn't contain that information..." |

---

## 3. Out-of-Scope Handling

| Requirement | Status | Implementation |
|-------------|--------|----------------|
| Define 3+ out-of-scope categories with positive framing | DONE | `app/backstop.py:18-56` - 4 categories: `coding_help`, `hardware_advice`, `ml_education`, `non_hf_models` |
| Python backstop after generation (keyword/regex/classifier) | DONE | `app/backstop.py:59-93` - Pre-compiled regex patterns checked in `check_out_of_scope()`; called in `app/main.py:127` before LLM call |
| Safety handling example (distressed keywords → fallback) | PARTIAL | Has adversarial handling in evals but no explicit safety/mental health fallback |

---

## 4. Evaluation Harness

| Requirement | Status | Implementation |
|-------------|--------|----------------|
| Golden dataset with 20+ cases | DONE | `eval/golden_dataset.json` - 25 total cases |
| 10 in-domain (with expected answer) | DONE | 12 in-domain cases with expected answers |
| 5 out-of-scope (expected refusal) | DONE | 5 out-of-scope cases (coding_help, hardware_advice, ml_education, non_hf_models) |
| 5 adversarial/safety-trigger | DONE | 5 adversarial cases (prompt injection, role change, prompt leak, forced output) |
| Runnable eval script | DONE | `eval/run_evals.py` (334 lines) |
| Runs all tests | DONE | `eval/run_evals.py:288-334` - `run_all_evaluations()` iterates through dataset |
| Reports pass/fail per test | DONE | `eval/run_evals.py` - prints result for each test case |
| Prints pass rates by category | DONE | `eval/run_evals.py:306-330` - category summaries (in_domain, out_of_scope, adversarial) |
| >=1 deterministic metric | DONE | `eval/run_evals.py:68-117` - string matching, model ID presence, out-of-scope detection |

---

## 5. MaaJ (Model-as-a-Judge) Requirements

| Requirement | Status | Implementation |
|-------------|--------|----------------|
| 10 golden-reference MaaJ evals (judge compares to expected answer) | PARTIAL | Infrastructure exists but golden-reference cases use deterministic matching; MaaJ used for rubric cases only |
| 10 rubric MaaJ evals (judge grades against rubric) | DONE | `eval/golden_dataset.json` - 10 cases with `type: "rubric"`; `eval/run_evals.py:119-197` - `maaj_rubric_eval()` grades on 4 criteria |

---

## 6. Repo Contents

| Requirement | Status | Implementation |
|-------------|--------|----------------|
| README.md (topic, how to run locally, live URL) | MISSING | No README.md in repo root |
| pyproject.toml (uv-based) | DONE | `pyproject.toml` - configured with uv, all dependencies listed |
| App code (FastAPI + frontend) | DONE | `app/` directory with main.py, models/, prompts/ |
| eval (single command to run in README) | MISSING | Eval script exists but README with command is missing |

---

## Summary

| Category | Done | Partial | Missing |
|----------|------|---------|---------|
| App | 3 | 1 | 0 |
| Prompt | 6 | 0 | 0 |
| Out-of-Scope | 1 | 1 | 0 |
| Eval Harness | 9 | 0 | 0 |
| MaaJ | 1 | 1 | 0 |
| Repo Contents | 2 | 0 | 1 |
| **TOTAL** | **22** | **3** | **1** |

---

## Action Items

1. **MISSING: README.md** - Create with topic description, local run instructions, live URL placeholder
2. **PARTIAL: MaaJ golden-reference** - Consider switching some golden cases from deterministic to MaaJ comparison
3. **PARTIAL: Safety fallback** - Add explicit distress/mental health keyword detection if required
4. **PENDING: GCP Deployment** - Dockerfile ready; deploy to Cloud Run and update README with live URL

---

## Files Reference

- `app/main.py` - FastAPI endpoints
- `app/backstop.py` - Out-of-scope regex detection
- `app/prompts/system_prompt.py` - System prompt + 6 few-shot examples
- `app/models/schemas.py` - Pydantic request/response models
- `eval/golden_dataset.json` - 25 test cases
- `eval/run_evals.py` - Evaluation harness with deterministic + MaaJ
- `static/index.html` - Web frontend
- `pyproject.toml` - uv dependencies
- `Dockerfile` - Cloud Run deployment config
