# Requirements Review: Project 1 - Domain Q&A Chatbot

**Generated:** 2026-02-22 14:30
**Reviewer:** Claude Code
**Topic:** HuggingFace Models Explorer

---

## Requirements Checklist

### 1. App Requirements

| Requirement | Status | Implementation |
|-------------|--------|----------------|
| Niche topic for 20+ test questions | DONE | HuggingFace top 100 models (frozen snapshot) - `data/models_snapshot_20260221.json` |
| Backend: FastAPI | DONE | `app/main.py:18-214` - 3 endpoints: `/health`, `/chat`, `/` |
| Frontend: simple web UI | DONE | `static/index.html` (361 lines) - dark theme, confidence bar, source links |
| Deploy on GCP + live URL | PENDING | `Dockerfile` configured for Cloud Run; credentials in `credentials/`; NOT YET DEPLOYED |

---

### 2. Prompt Requirements

| Requirement | Status | Implementation |
|-------------|--------|----------------|
| Role/persona (domain voice + boundaries) | DONE | `app/prompts/system_prompt.py:10` - "You are the HuggingFace Models Assistant" |
| Few-shot examples (>=3) | DONE | `app/prompts/system_prompt.py:45-87` - 6 examples (license, task filter, top model, license filter, comparison, date) |
| Static or dynamic examples | DONE | Static examples embedded in system prompt |
| Organization method | DONE | `app/prompts/system_prompt.py:97-115` - `build_context_prompt()` + `format_chat_prompt()` |
| Positive constraints | DONE | `app/prompts/system_prompt.py:12-21` - SCOPE section lists available data (no "don't" rules) |
| Escape hatch for uncertainty | DONE | `app/prompts/system_prompt.py:88-94` - "I'm not sure - the available data doesn't contain..." |

---

### 3. Out-of-Scope Handling

| Requirement | Status | Implementation |
|-------------|--------|----------------|
| 3+ out-of-scope categories (positive framing) | DONE | `app/backstop.py:31-94` - 5 categories: `coding_help`, `hardware_advice`, `ml_education`, `non_hf_models`, `prompt_injection` |
| Python backstop (keyword/regex/classifier) | DONE | `app/backstop.py:97-182` - 2-layer: regex patterns + LLM intent classifier for prompt injection |
| Safety fallback (distressed keywords) | NOT IMPLEMENTED | No explicit mental health/distress keyword detection |

---

### 4. Evaluation Harness

| Requirement | Status | Implementation |
|-------------|--------|----------------|
| Golden dataset 20+ cases | DONE | `eval/golden_dataset.json` - 25 cases |
| 10 in-domain (expected answer) | DONE | 10 in-domain: `single_model_*`, `multi_filter_*` |
| 5 out-of-scope (expected refusal) | DONE | 5 out-of-scope: `out_of_scope_001-005` |
| 5 adversarial/safety-trigger | DONE | 5 adversarial: `adversarial_001-005` |
| Runnable eval script | DONE | `eval/run_evals.py` (334 lines) |
| Runs all tests | DONE | `eval/run_evals.py:288-334` - `run_all_evaluations()` |
| Reports pass/fail per test | DONE | Per-case colored output in console |
| Prints pass rates by category | DONE | Category summaries: deterministic, maaj_golden, maaj_rubric, out_of_scope |
| >=1 deterministic metric | DONE | `eval/run_evals.py:103-146` - string matching, model ID presence, out-of-scope detection |

---

### 5. MaaJ (Model-as-a-Judge) Requirements

| Requirement | Status | Implementation |
|-------------|--------|----------------|
| 10 golden-reference MaaJ evals (judge compares to expected) | PARTIAL | `eval/run_evals.py:195-240` - `evaluate_maaj_golden()` exists but most golden cases use deterministic matching |
| 10 rubric MaaJ evals (judge grades against rubric) | DONE | 10 rubric cases: `comparison_*`, `adversarial_*`, `edge_case_*` - `eval/run_evals.py:149-192` |

---

### 6. Repo Contents

| Requirement | Status | Implementation |
|-------------|--------|----------------|
| README.md (topic, local run, live URL) | MISSING | **No README.md in project root** |
| pyproject.toml (uv-based) | DONE | `pyproject.toml` - uv config with all dependencies |
| App code (FastAPI + frontend) | DONE | `app/` directory with `main.py`, `backstop.py`, `prompts/`, `models/` |
| eval (single command in README) | BLOCKED | Script exists (`uv run python eval/run_evals.py`) but README missing |

---

## Summary

| Status | Count | Items |
|--------|-------|-------|
| DONE | 20 | Core app, prompts, backstop, eval harness |
| PARTIAL | 2 | MaaJ golden evals, GCP deployment |
| MISSING | 1 | README.md |
| NOT IMPLEMENTED | 1 | Safety/distress keyword fallback |

---

## Gap Analysis

### Critical (Blocks Submission)
1. **README.md** - Must create with:
   - Topic: HuggingFace Models Explorer
   - Local run: `uv sync && uv run uvicorn app.main:app --reload`
   - Eval run: `uv run python eval/run_evals.py`
   - Live URL: placeholder until deployment

### Required Before Deploy
2. **GCP Deployment** - Dockerfile ready, need to:
   - `gcloud run deploy` command
   - Add live URL to README

### Recommended (Not Blocking)
3. **MaaJ Golden Evals** - Consider using `evaluate_maaj_golden()` for more cases instead of deterministic matching
4. **Safety Fallback** - Add distress keyword detection (mentioned as "great example" in requirements)

---

## File Reference Map

```
project-1/
├── app/
│   ├── main.py              # FastAPI: /health, /chat, /
│   ├── backstop.py          # 5 out-of-scope categories + LLM intent check
│   ├── prompts/
│   │   └── system_prompt.py # Persona + 6 few-shot + scope + escape hatch
│   └── models/
│       └── schemas.py       # ChatRequest, ChatResponse, HealthResponse
├── eval/
│   ├── golden_dataset.json  # 25 test cases
│   └── run_evals.py         # Deterministic + MaaJ golden + MaaJ rubric
├── static/
│   └── index.html           # Web UI
├── data/
│   └── models_snapshot_20260221.json  # 100 HF models
├── pyproject.toml           # uv dependencies
├── Dockerfile               # Cloud Run config
└── README.md               # MISSING
```

---

## Next Steps

1. Create `README.md`
2. Deploy to GCP Cloud Run
3. Update README with live URL
4. (Optional) Add safety fallback
5. (Optional) Expand MaaJ golden evals
