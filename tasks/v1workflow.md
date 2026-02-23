# Project 1: Domain Q&A Chatbot — Working Guide

## Topic: HuggingFace Top 100 Models Explorer

**Business case:** someone wants to use an LLM but doesn't want to spend 30 minutes on HuggingFace filtering. They have constraints (hardware, license, task) and want an answer fast.

---

## Authoritative Document

**Source:** `https://huggingface.co/api/models?sort=downloads&limit=100&full=true`

Then for each model, fetch its individual page to get the model card (README.md).

Merge everything into a single frozen JSON file committed to the repo. This is your ground truth. Never re-scrape during evals — all answers are relative to the snapshot date, which must be stated explicitly.

**Fields to extract per model (decide which are mandatory vs best-effort):**

- model_id
- downloads
- likes
- pipeline_tag (task type)
- tags (includes size hints like "7B", license info, modality)
- createdAt
- license (from cardData if available)
- parameter_count (often missing — parse from tags or card text)
- model_card_summary (first N chars of README)

**Known data quality issue:** parameter counts and licenses are inconsistently documented across model cards. Some models won't have them. Flag missing fields explicitly rather than leaving silent nulls.

---

## Question Types

Two patterns, both supported:

**Single model lookup** — straightforward retrieval against one model's record.
- "What license does Mistral-7B use?"
- "What tasks does Mistral 7B support?"
- "What are Qwen 2.5 14B's specs?"

**Multi-model filtering** — structured query across all 100 models.
- "Which models are under 24B parameters?"
- "Which models run on 8GB VRAM?"
- "Which models are commercially licensed?"
- "Which models do image captioning?"
- "Which models were published after January 2026 and have over 1M downloads?"

**Comparison** — reasoning across two specific models.
- "What's the difference in size between Phi-3 and Gemma 2?"

---

## LLM vs Programmatic Routing

Decide upfront which question types get handled programmatically vs passed to the LLM.

**Programmatic (more reliable for deterministic answers):**
- Numeric filters: parameter count, VRAM, download thresholds
- Date filters: published after X
- License exact match

**LLM reasoning:**
- Task fit questions where tags are fuzzy
- Comparisons
- Natural language lookup where the user doesn't know the exact model name

---

## Workflow

1. Hit the API endpoint, get top 100 models as JSON
2. For each model, fetch its model card from `huggingface.co/{model_id}/resolve/main/README.md`
3. Parse and normalize fields — flag missing parameter counts and licenses explicitly
4. Commit the frozen JSON to the repo with snapshot date
5. Write 20+ eval questions with known answers derived from that frozen snapshot
6. Build FastAPI backend + simple frontend
7. Build eval harness
8. Deploy on GCP

---

## Eval Dataset Structure (20+ cases)

**10 in-domain with expected answers** — drawn directly from the frozen JSON, verified manually before committing.

**5 out-of-scope** — questions the bot should refuse:
- "Write me a Python script"
- "What GPU should I buy?"
- "How do I fine-tune a model?"

**5 adversarial/safety** — prompt injection attempts, jailbreaks, attempts to get the bot to answer outside its domain.

---

## Notes

- "New and popular" questions are valid but require fixed thresholds in evals (e.g. "published after Jan 2026 with over 1M downloads") — not fuzzy language
- VRAM estimation is derived from parameter count (rough rule: ~2GB per 1B params in fp16) — this is LLM reasoning, not direct field lookup, so golden evals need to reflect that