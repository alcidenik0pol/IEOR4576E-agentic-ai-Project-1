# HuggingFace Top 100 Models Explorer

A domain-specific Q&A chatbot that helps users discover and compare the most popular models on HuggingFace.

**Live URL:** https://hf-explorer-62w56e2yga-uc.a.run.app

---

## Business Case

Choosing an LLM from HuggingFace is time-consuming. Users spend 30+ minutes filtering by hardware constraints, license requirements, and task type. This chatbot provides instant answers about the top 100 most-downloaded models—helping practitioners find the right model fast.

---

## How to Run

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager
- Google Cloud credentials (for Vertex AI)

### Local Development

```bash
# Install dependencies
uv sync

# Set up environment
cp .env.example .env
# Edit .env with your GCP project ID and credentials path

# Run the server
uv run uvicorn app.main:app --reload
```

The app will be available at `http://localhost:8000`.

### Docker

```bash
docker build -t hf-explorer:latest .
docker run -p 8080:8080 -e GOOGLE_CLOUD_PROJECT=agenticaicolumbia hf-explorer:latest
```

### Cloud Run Deployment

```bash
# Deploy via Cloud Build (recommended)
gcloud builds submit --config=cloudbuild.yaml --service-account='projects/agenticaicolumbia/serviceAccounts/hf-explorer-builder@agenticaicolumbia.iam.gserviceaccount.com'
```

See `tasks/deploy-instructions.md` for full setup (service accounts, IAM, Artifact Registry).

### Rate Limiting

The app has two layers of request limiting:

1. **Application-level (per user)** — 20 requests/minute per IP via `slowapi`. Returns `429` with a friendly message. Protects against abuse and contains costs.

2. **Vertex AI quota (per project)** — Google's API limit (free tier: ~15-20 req/min). Returns `429 Quota exceeded...` when exceeded.

The app-level limit triggers first in most cases, providing faster failure and better UX. Once you increase Vertex quota in production, the app-level limit becomes the primary abuse protection.

### Run Evaluations

```bash
uv run python eval/run_evals.py
```

---

## Requirements Compliance

### App Architecture

- **Niche topic for 20+ test questions** → ✅ `data/models_snapshot_20260221.json` contains 100 HuggingFace models — narrow enough to write deterministic tests
- **Backend: FastAPI** → ✅ `app/main.py:15` defines app with `/health`, `/chat`, `/` endpoints
- **Frontend: simple web UI** → ✅ `static/index.html` — dark theme UI with confidence bar and source links
- **Deploy on GCP + live URL** → ✅ Deployed to Cloud Run via `cloudbuild.yaml`

### Prompting Strategy

- **Role/persona** → ✅ `app/prompts/system_prompt.py:10` — "HuggingFace Models Assistant" with domain voice and boundaries
- **Few-shot examples (>=3)** → ✅ `app/prompts/system_prompt.py:51-116` — 6 examples: license lookup, task filter, top models, license filter, comparison, date filter
- **Organization method** → ✅ `app/prompts/system_prompt.py:build_context_prompt()` + `format_chat_prompt()` — structured sections: role → scope → examples → format
- **Positive constraints** → ✅ `app/prompts/system_prompt.py:28-48` — SCOPE section lists available fields (no "don't" rules)
- **Escape hatch** → ✅ `app/prompts/system_prompt.py:45-48` — "I'm not sure - the available data doesn't contain..." when uncertain

### Out-of-Scope Handling

- **3+ out-of-scope categories** → ✅ `app/backstop.py:12-45` — 5 categories defined: `coding_help`, `hardware_advice`, `ml_education`, `non_hf_models`, `prompt_injection`
- **Python backstop (regex/classifier)** → ✅ `app/backstop.py:check_out_of_scope()` — 2-layer detection: regex patterns on query, then LLM intent classifier for ambiguous cases

### Evaluation Harness

- **Golden dataset 20+ cases** → ✅ `eval/golden_dataset.json` — 25 total cases
- **10 in-domain (expected answer)** → ✅ `eval/golden_dataset.json` — 10 cases with `expected_answer` field, evaluated via `maaj_golden`
- **5 out-of-scope (expected refusal)** → ✅ `eval/golden_dataset.json` — 5 cases with `expected_refusal`, evaluated via deterministic string matching
- **5 adversarial/safety** → ✅ `eval/golden_dataset.json` — 5 cases (jailbreak, prompt injection, roleplay), evaluated via `rubric`
- **Runnable eval script** → ✅ `eval/run_evals.py` — single command `uv run python eval/run_evals.py`
- **Runs all tests + pass/fail per test** → ✅ `eval/run_evals.py:run_evaluations()` — iterates all cases, prints colored PASS/FAIL per case
- **Category summaries** → ✅ `eval/run_evals.py:305-320` — prints pass rates grouped by category
- **>=1 deterministic metric** → ✅ `eval/run_evals.py:evaluate_golden_reference()` — string matching, model ID detection, refusal detection without LLM

### MaaJ (Model-as-a-Judge)

- **10 golden-reference MaaJ evals** → ✅ `eval/golden_dataset.json` — 10 cases with `"evaluation": "maaj_golden"` → routed to `evaluate_maaJ_golden()` at line 195 which uses LLM to compare response against expected answer
- **10 rubric MaaJ evals** → ✅ `eval/golden_dataset.json` — 10 cases with `"evaluation": "rubric"` → routed to `evaluate_rubric_maaJ()` at line 149 which grades response against a rubric using LLM

### Repo Contents

- **README.md** → ✅ This file
- **pyproject.toml (uv-based)** → ✅ `pyproject.toml` — configured with FastAPI, uvicorn, google-cloud-aiplatform, pytest
- **App code (FastAPI + frontend)** → ✅ `app/` directory with `main.py`, `prompts/`, `backstop.py`
- **eval (single command)** → ✅ `uv run python eval/run_evals.py`

---

## Data Source

Model data is frozen from the HuggingFace API:

- **Endpoint:** `https://huggingface.co/api/models?sort=downloads&limit=100&full=true`
- **Snapshot date:** 2026-02-21
- **Location:** `data/models_snapshot_20260221.json`

All answers are relative to this snapshot. Answers about new models or changed statistics will not reflect current HuggingFace data.
