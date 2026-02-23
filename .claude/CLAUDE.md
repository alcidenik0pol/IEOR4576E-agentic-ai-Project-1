# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is **Project 1: Domain Q&A Chatbot** for Columbia University's Agentic AI course.

**Goal**: Build and deploy a chatbot that answers questions in a narrow domain with an automated eval harness.

**Tech Stack**:
- Backend: FastAPI
- Frontend: Simple web UI
- Deployment: GCP
- Package manager: uv (pyproject.toml required)

**Core Requirements**:
- Few-shot prompting (≥3 examples)
- Positive constraints (define scope, no "don't do X")
- Escape hatch for uncertainty handling
- 3+ out-of-scope categories with Python backstop (keyword/regex/classifier)
- Golden dataset: 20+ cases (10 in-domain, 5 out-of-scope, 5 adversarial/safety)
- Eval harness with ≥1 deterministic metric
- 10 golden-reference MaaJ evals + 10 rubric MaaJ evals

## Commands

```bash
# Install dependencies (when uv is set up)
uv sync

# Run the app locally
uv run uvicorn app.main:app --reload

# Run evaluation harness
uv run python eval/run_evals.py
```

## Architecture

```
project-1/
├── app/                 # FastAPI backend + frontend
│   ├── main.py          # FastAPI app entry point
│   ├── prompts/         # Prompt templates and few-shot examples
│   └── backstop.py      # Out-of-scope detection
├── eval/                # Evaluation harness
│   ├── golden_dataset.json
│   └── run_evals.py
├── pyproject.toml       # uv-based dependencies
└── README.md
```

---

## Workflow Orchestration

### 1. Plan Mode Default
- Enter plan mode for ANY non-trivial task (3+ steps or architectural decisions)
- If something goes sideways, STOP and re-plan immediately – don't keep pushing
- Use plan mode for verification steps, not just building
- Write detailed specs upfront to reduce ambiguity

### 2. Subagent Strategy
- Use subagents liberally to keep main context window clean
- Offload research, exploration, and parallel analysis to subagents
- For complex problems, throw more compute at it via subagents
- One task per subagent for focused execution

### 3. Self-Improvement Loop
- After ANY correction from the user: update `tasks/lessons.md` with the pattern
- Write rules for yourself that prevent the same mistake
- Ruthlessly iterate on these lessons until mistake rate drops
- Review lessons at session start for relevant project

### 4. Verification Before Done
- Never mark a task complete without proving it works
- Diff behavior between main and your changes when relevant
- Ask yourself: "Would a staff engineer approve this?"
- Run tests, check logs, demonstrate correctness

### 5. Demand Elegance (Balanced)
- For non-trivial changes: pause and ask "is there a more elegant way?"
- If a fix feels hacky: "Knowing everything I know now, implement the elegant solution"
- Skip this for simple, obvious fixes – don't over-engineer
- Challenge your own work before presenting it

### 6. Autonomous Bug Fixing
- When given a bug report: just fix it. Don't ask for hand-holding
- Point at logs, errors, failing tests – then resolve them
- Zero context switching required from the user
- Go fix failing CI tests without being told how

## Task Management

1. **Plan First**: Write plan to `tasks/todo.md` with checkable items
2. **Verify Plan**: Check in before starting implementation
3. **Track Progress**: Mark items complete as you go
4. **Explain Changes**: High-level summary at each step
5. **Document Results**: Add review section to `tasks/todo.md`
6. **Capture Lessons**: Update `tasks/lessons.md` after corrections

## Core Principles

- **Simplicity First**: Make every change as simple as possible. Impact minimal code.
- **No Laziness**: Find root causes. No temporary fixes. Senior developer standards.
- **Minimal Impact**: Changes should only touch what's necessary. Avoid introducing bugs.

## History
The `LEARNING.md` file contains insights, tips, and best practices discovered during previous tasks. Read this file before running new tasks to benefit from prior knowledge. Update it with any new findings after each task run if necessary (only when new information is available or when you need to update existing information). 

You have full access to the entire memory, plus you can track changes via git. Every entry is timestamped.

## Plan mode Specific Instructions

Review this plan thoroughly before making any code changes. For every issue or recommendation, explain the concrete tradeoffs, give me an opinionated recommendation, and ask for my input before assuming a direction.

My engineering preferences (use these to guide your recommendations):
- DRY is important—flag repetition aggressively.
- Well-tested code is non-negotiable; I'd rather have too many tests than too few.
- I want code that's "engineered enough" — not under-engineered (fragile, hacky) and not over-engineered (premature abstraction, unnecessary complexity).
- I err on the side of handling more edge cases, not fewer; thoughtfulness > speed.
- Bias toward explicit over clever.

**1. Architecture review**

Evaluate:
- Overall system design and component boundaries.
- Dependency graph and coupling concerns.
- Data flow patterns and potential bottlenecks.
- Scaling characteristics and single points of failure.
- Security architecture (auth, data access, API boundaries).

**2. Code quality review**

Evaluate:
- Code organization and module structure.
- DRY violations—be aggressive here.
- Error handling patterns and missing edge cases (call these out explicitly).
- Technical debt hotspots.
- Areas that are over-engineered or under-engineered relative to my preferences.

**3. Test review**

Evaluate:
- Test coverage gaps (unit, integration, e2e).
- Test quality and assertion strength.
- Missing edge case coverage—be thorough.
- Untested failure modes and error paths.

**4. Performance review**

Evaluate:
- N+1 queries and database access patterns.
- Memory-usage concerns.
- Caching opportunities.
- Slow or high-complexity code paths.

**For each issue you find**

For every specific issue (bug, smell, design concern, or risk):
- Describe the problem concretely, with file and line references.
- Present 2–3 options, including "do nothing" where that's reasonable.
- For each option, specify: implementation effort, risk, impact on other code, and maintenance burden.
- Give me your recommended option and why, mapped to my preferences above.
- Then explicitly ask whether I agree or want to choose a different direction before proceeding.

**Workflow and interaction**
- Do not assume my priorities on timeline or scale.
- After each section, pause and ask for my feedback before moving on.

---

**BEFORE YOU START:**

Ask if I want one of two options:

1/ BIG CHANGE: Work through this interactively, one section at a time (Architecture → Code Quality → Tests → Performance) with at most 4 top issues in each section.

2/ SMALL CHANGE: Work through interactively ONE question per review section

FOR EACH STAGE OF REVIEW: output the explanation and pros and cons of each stage's questions AND your opinionated recommendation and why, and then use AskUserQuestion. Also NUMBER issues and then give LETTERS for options and when using AskUserQuestion make sure each option clearly labels the issue NUMBER and option LETTER so the user doesn't get confused. Make the recommended option always the 1st option.