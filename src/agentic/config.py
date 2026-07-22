"""Agentic system configuration — query-driven domain-valid patent identification.

Model tiering: low-volume reasoning stages (scoping / evidence notes / criteria /
validators) use MODEL_RESEARCH; the high-volume per-patent judge uses MODEL_JUDGE.
Judgment thresholds are FIXED a priori (never tuned on gold sets).
"""
from __future__ import annotations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AGENTIC_DIR = ROOT / "DataSet" / "agentic"
OUTPUTS_DIR = ROOT / "outputs"

# ---- models ----
MODEL_RESEARCH = "gpt-4o"        # scoping, note extraction, criteria, validators
MODEL_CORPUS_MAP = "gpt-4o-mini"     # per-batch corpus reading (mass volume, cheap)
MODEL_JUDGE_FAST = "gpt-4o-mini"     # per-patent judgment (mass volume)
MODEL_JUDGE_STRONG = "gpt-4o-mini"   # second-pass boundary confirmation
LLM_TEMPERATURE = 0.0

# ---- web research budget ----
SEARCH_PROVIDER = "tavily"
TAVILY_ENV = "TAVILY_API_KEY"
SEARCH_MAX_RESULTS = 5           # results requested per search call
MAX_PAGES_PER_SEARCH = 3         # pages kept (after filtering) per search
MAX_ROUNDS = 2                   # research rounds (initial plan + 1 gap-driven)
MAX_FOLLOWUPS = 5                # follow-up searches per gap analysis
MAX_TOTAL_PAGES = 30             # hard cap on fetched pages per domain
PAGE_TEXT_CHARS = 8000           # page text truncation before note extraction
FETCH_TIMEOUT_S = 15

# ---- owner documents (--local-doc: the domain owner's own reference material) ----
# A short owner document is injected verbatim as the top authority for intended
# scope; the axis stage separately assesses completeness and factual reliability.
OWNER_DOC_FULLTEXT_MAX_CHARS = 8000

# ---- corpus reading (the judge pool is actually read, in batches) ----
CORPUS_BATCH_SIZE = 50           # patents (title+abstract) per map call
CORPUS_MAX_BATCHES = 200         # safety cap (200*50 = 10k patents)
CORPUS_ABSTRACT_CHARS = 600      # per-patent abstract truncation in corpus reading

# ---- proactive scope questions (boundary probing) ----
BOUNDARY_PROBE_SAMPLE = 60       # pool patents judged under broad-vs-narrow rules
BOUNDARY_MIN_FLIP_RATE = 0.08    # a boundary is "real" only if >= this share of the sample flips
BOUNDARY_MAX_QUESTIONS = 4       # cap the questions actually shown to the human

# ---- feedback loops ----
CRITERIA_MAX_ITERS = 5           # criteria validator loop budget; critical remains -> block
JUDGE_VALIDATE_MAX_ITERS = 2     # judgment validator loop budget
JUDGE_AUDIT_SAMPLE = 40          # suspicious judgments re-examined per validator round
DECISION_CONFIDENCE_AUDIT_MAX = 0.65  # low certainty -> confirmation/audit, not exclusion

# ---- evaluation ----
PILOT_SIZE = 80

# ---- scope breadth (recall lever) ----
# Patent landscaping includes inventions that IMPLEMENT / IMPROVE / provide an enabling
# component or a specific application of the domain technology — not only the single core
# end-task. Turning this on widens criteria + judgment toward recall (the Bergeaud gold
# sets are landscaping-scale, so this matches them). Off = strict end-task purity.
LANDSCAPING_INCLUSIVE = True
