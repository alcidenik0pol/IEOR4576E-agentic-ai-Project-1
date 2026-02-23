# Requirements Review: Project 1 - Domain Q&A Chatbot

**Generated:** 2026-02-22 14:45
**Reviewer:** Claude Code
**Topic:** HuggingFace Models Explorer

---

## Requirements Checklist

### 1. App Requirements

| Requirement | Status | Implementation |
|-------------|--------|----------------|
| Niche topic for 20+ test questions | DONE | HuggingFace top 100 models - `data/models_snapshot_20260221.json` |
| Backend: FastAPI | DONE | `app/main.py` - 3 endpoints: `/health`, `/chat`, `/` |
| Frontend: simple web UI | DONE | `static/index.html` - dark theme, confidence bar, source links |
| Deploy on GCP + live URL | PENDING | `Dockerfile` configured; credentials in `credentials/`; NOT YET DEPLOYED |

---

### 2. Prompt Requirements

| Requirement | Status | Implementation |
|-------------|--------|----------------|
| Role/persona | DONE | `app/prompts/system_prompt.py:10` - "HuggingFace Models Assistant" |
| Few-shot examples (>=3) | DONE | 6 examples: license, task filter, top model, license filter, comparison, date |
| Organization method | DONE | `build_context_prompt()` + `format_chat_prompt()` |
| Positive constraints | DONE | SCOPE section lists available data fields (no "don't" rules) |
| Escape hatch | DONE | "I'm not sure - the available data doesn't contain..." |

---

### 3. Out-of-Scope Handling

| Requirement | Status | Implementation |
|-------------|--------|----------------|
| 3+ out-of-scope categories | DONE | 5 categories: `coding_help`, `hardware_advice`, `ml_education`, `non_hf_models`, `prompt_injection` |
| Python backstop (regex/classifier) | DONE | 2-layer: regex patterns + LLM intent classifier |
| Safety fallback | OPTIONAL | No explicit distress keyword detection (mentioned as example, not required) |

---

### 4. Evaluation Harness

| Requirement | Status | Implementation |
|-------------|--------|----------------|
| Golden dataset 20+ cases | DONE | 25 cases in `eval/golden_dataset.json` |
| 10 in-domain (expected answer) | DONE | 10 in-domain with `maaj_golden` eval |
| 5 out-of-scope (expected refusal) | DONE | 5 out-of-scope with `golden_reference` (deterministic) |
| 5 adversarial/safety | DONE | 5 adversarial with `rubric` eval |
| Runnable eval script | DONE | `eval/run_evals.py` |
| Runs all tests | DONE | `run_evaluations()` iterates all cases |
| Reports pass/fail per test | DONE | Colored console output per case |
| Category summaries | DONE | Summary section prints rates by category |
| >=1 deterministic metric | DONE | String matching, model ID detection, out-of-scope detection |

---

### 5. MaaJ (Model-as-a-Judge) Requirements

| Requirement | Status | Implementation |
|-------------|--------|----------------|
| 10 golden-reference MaaJ evals | **DONE** | 10 cases with `"evaluation": "maaj_golden"` → `evaluate_maaJ_golden()` at line 195 |
| 10 rubric MaaJ evals | **DONE** | 10 cases with `"evaluation": "rubric"` → `evaluate_rubric_maaJ()` at line 149 |

**MaaJ Golden Cases (10 total):**
1. `single_model_001` - bert license
2. `single_model_002` - MiniLM downloads
3. `single_model_003` - mpnet task
4. `multi_filter_001` - MIT license models
5. `multi_filter_002` - top 5 models
6. `multi_filter_003` - sentence similarity models
7. `multi_filter_004` - FacebookAI models
8. `comparison_003` - MiniLM vs MPNet downloads
9. `in_domain_011` - nsfw_image_detection pipeline
10. `in_domain_012` - bert creation date

**MaaJ Rubric Cases (10 total):**
1. `comparison_001` - MiniLM vs MPNet differences
2. `comparison_002` - BERT vs RoBERTa
3. `adversarial_001` - joke request
4. `adversarial_002` - pirate roleplay
5. `adversarial_003` - prompt leak
6. `adversarial_004` - fake authority
7. `adversarial_005` - forced output
8. `edge_case_001` - parameter filter
9. `edge_case_002` - unknown model
10. `edge_case_003` - empty question

---

### 6. Repo Contents

| Requirement | Status | Implementation |
|-------------|--------|----------------|
| README.md | **MISSING** | No README.md in project root |
| pyproject.toml (uv-based) | DONE | Configured with all dependencies |
| App code (FastAPI + frontend) | DONE | `app/` directory complete |
| eval (single command) | DONE | `uv run python eval/run_evals.py` |

---

## Summary

| Status | Count |
|--------|-------|
| DONE | 21 |
| PENDING | 1 (GCP deployment) |
| MISSING | 1 (README.md) |

---

## Corrected Assessment

Previous review incorrectly marked MaaJ golden evals as "PARTIAL". Upon re-examination:

- `eval/golden_dataset.json` has exactly 10 cases with `"evaluation": "maaj_golden"`
- `eval/run_evals.py` routes these to `evaluate_maaJ_golden()` (lines 300-307)
- This function uses the LLM to judge if the response matches expected
- **Requirement is fully met**

---

## Remaining Action Items

1. **MISSING: README.md** - Create with topic, local run, eval run, live URL
2. **PENDING: GCP deployment** - Run `gcloud run deploy`, add URL to README
