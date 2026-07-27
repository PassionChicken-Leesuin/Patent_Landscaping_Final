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
# Tier-B boundary specialist: re-judges only the contested look-alike cluster, reading the
# CLAIM (not just the abstract) with case-mapping exemplars as anchors. Only ~1k patents hit
# this, so a strong model is affordable. Set to your GPT-5 id (e.g. "gpt-5") to use it — kept
# at gpt-4o by default so a run can't fail on a model id your keys may not have.
MODEL_JUDGE_BOUNDARY = "gpt-4o"
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
# Caps sized from measured corpora (KISTA 241,818 + Bergeaud 6 domains): title max=600;
# abstract p99.9 <= 4934 across all corpora (Bergeaud blockchain/hydrogen run longest).
# 5000 covers every corpus's p99.9 and truncates only genuine malformed outliers (>5k chars).
CORPUS_TITLE_CHARS = 600         # per-patent title truncation in corpus reading (= observed max)
CORPUS_ABSTRACT_CHARS = 5000     # per-patent abstract truncation (covers all-corpora p99.9)

# ---- case-mapping-based criteria authoring (front-half) ----
DIAGNOSE_TITLE_SAMPLE = 40        # pool titles shown to the alignment-diagnosis LLM
DIAGNOSE_TOP_ASSIGNEES = 20       # assignees profiled
CASEMAP_TEXT_CHARS = 6000         # per-candidate text (title+abstract concat) in case-mapping reads
CASEMAP_SAMPLE_PER_CATEGORY = 110 # candidate patents mapped per category
CASEMAP_CROSS_PRIORITY = 60       # cross-matched (exclusion x tier) candidates prioritized
CASEMAP_REVISE_ROUNDS = 2         # self-correction rounds with no change -> settle
CASEMAP_MAX_CATEGORIES = 20       # safety cap on categories derived from the design plan

# ---- Tier-B boundary specialist judge (claim-reading, anchored, strong model) ----
# OFF by default: a documented NEGATIVE result. Re-judging the contested cluster from the
# representative claim with gpt-4o + case-mapping anchors flipped 688/2600 verdicts but the
# flips were anti-correlated with the gold (IN->OUT 40% correct, OUT->IN 26% correct), so it
# LOWERED both precision (0.750->0.662) and recall (0.795->0.699). The single rep_claim plus a
# blunt "process-bound => OUT" test is not a reliable substitute for the gold's expert
# full-context claim-scope review. Kept for the record; do not enable without a redesign
# (full independent claim, calibrated multi-claim reasoning, ensemble voting).
BOUNDARY_TIER_ENABLED = False     # re-judge the contested look-alike cluster from the claim
BOUNDARY_TIER_MAX = 2600          # cost cap: at most this many patents re-judged
BOUNDARY_CLAIM_CHARS = 2600       # representative-claim truncation fed to the specialist
BOUNDARY_ANCHORS_PER_SIDE = 4     # case-mapping IN / OUT exemplars shown per patent

# ---- proactive scope questions (boundary probing) ----
BOUNDARY_PROBE_SAMPLE = 60       # pool patents judged under broad-vs-narrow rules
BOUNDARY_MIN_FLIP_RATE = 0.08    # a boundary is "real" only if >= this share of the sample flips
BOUNDARY_MAX_QUESTIONS = 4       # cap the questions actually shown to the human

# ---- feedback loops ----
CRITERIA_MAX_ITERS = 5           # criteria validator loop budget; critical remains -> block
CRITERIA_NO_PROGRESS_LIMIT = 2   # consecutive rounds resolving no ledger critical -> stop early
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
