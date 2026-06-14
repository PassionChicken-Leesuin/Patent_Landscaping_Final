# MAS Implementation — v2 (single-domain, 10-key parallel, local-runnable)

This is the **delta** from `MAS_LangGraph_구현스펙_v1.md`. The v1 design (nodes A/B/C,
routing, deterministic scoring, hard-negative-as-flag) is unchanged. v2 adapts it to
our actual data and environment, and adds parallel execution.

## What changed from v1

| v1 assumption | v2 reality |
|---|---|
| Multi-domain ("Bergeaud 6분야"), per-row `domain`, per-domain rubric | **Single domain** = `autonomous_driving`. One static rubric (`rubrics/autonomous_driving_v1.json`), no rubric-gen call needed. |
| "Candidate pool" / "Gold set" abstract | candidate pool = `DataSet/processed/training_clean.csv` (6,139, leakage removed); gold = `Evaluation_Set.csv` (test only). |
| `record_id` generic | `record_id = patent_id`. |
| Provider-agnostic, LangGraph required | Primary path = **OpenAI SDK direct** (robust on Python 3.14, best for multi-key). LangGraph wrapper kept optional (`src/mas/graph.py`). |
| single LLM | **10 API keys round-robined in parallel** for throughput. |

The leakage-dedup the spec demanded (§0/§11: gold must not sit in the candidate pool)
is already done — see `DataSet/leakage/leaked_train_patent_ids.csv` (56 patents removed).

## Module map (`src/mas/`)

| file | role | needs API/langgraph? |
|---|---|---|
| `config.py` | thresholds (TAU_POS/NEG, EX_*), model tiering, paths | no |
| `schemas.py` | Pydantic structured outputs + `PatentState` | no |
| `scoring.py` | Stage C `score_and_type` + routing (deterministic) | no |
| `prompts.py` | rubric/relevance/exclusion prompts + AD hard-negative few-shot | no |
| `rubric.py` | load static rubric JSON | no |
| `llm.py` | key loading, `OpenAIStructuredLLM`, `MockStructuredLLM`, usage/cost | openai |
| `nodes.py` | Node A/B + `process_patent` orchestration | no (takes llm) |
| `graph.py` | optional LangGraph wrapper (same callables) | langgraph |
| `runner.py` | `KeyPool` + parallel ThreadPool driver + Stage D CSV | openai |
| `tests/test_scoring.py` | deterministic-core unit tests | no |

## 10-key parallelism (how throughput is maximized)

* `KeyPool` builds one client pair `(fast, strong)` per key (10 total).
* `run_pool` submits all patents to a `ThreadPoolExecutor(max_workers=workers)`.
* Each task is assigned a key by **round-robin** (`key = (idx + attempt) % 10`).
* On `RateLimitError`/timeout/transient → **exponential backoff + rotate to the next
  key** (up to `max_attempts`). LLM calls are I/O-bound, so threads scale well.
* Per-key + aggregate usage and cost are tracked; per-key call counts are logged.

**Verified (12-patent real run):** 10 keys loaded, calls distributed `[3,3,2,1,1,1,1,1,1,1]`,
0 failures, **~1.25 calls/patent**, $0.004. Extrapolated full run (6,139 patents):
**≈ $2, ~10 min at `--workers 40`.**

## Run it (local `.venv`, Python 3.14)

```bash
# one-time
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt   # local subset installs on 3.14

# unit tests (no API)
.venv/Scripts/python.exe -m src.mas.tests.test_scoring

# offline smoke test (no API)
.venv/Scripts/python.exe -m scripts.run_mas --mock --limit 50

# pilot (real API, 80 patents from candidate pool — NEVER gold)
.venv/Scripts/python.exe -m scripts.run_mas --limit 80 --workers 20

# full candidate pool
.venv/Scripts/python.exe -m scripts.run_mas --workers 40
```

Outputs (git-ignored, regenerated):
- `DataSet/mas/mas_ranked_scores.csv` — Stage D: rank, score, record_id, patent_id, domain, title, abstract, candidate_type
- `DataSet/mas/mas_audit.jsonl` — full per-patent reasoning (route, evidence, exclusion) for debugging/refinement

## Downstream hand-off (Snorkel-comparable)

`candidate_type` → training labels for the **same** SciBERT harness used by the Snorkel arm:
- `positive` → SEED(1)
- `easy_negative` (sampled) + **all** `hard_negative` → NOT_SEED(0)  ← augmented anti-seed
- `boundary` / `abstain` → dropped (parallels Snorkel ABSTAIN)
- For a fair fight, match N to the Snorkel-labeled training-set size (equal-N), and run the
  hard-negative ablation (with vs without `hard_negative`).

## Guardrails (kept from v1 §11)
- Gold is never an input to MAS. Thresholds are fixed in `config.py`, not gold-tuned.
- temperature=0, seed fixed. Rubric is versioned. Full state in audit JSONL; CSV is the slim schema.
