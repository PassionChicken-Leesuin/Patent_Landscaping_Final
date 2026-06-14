"""MAS configuration — single-domain (autonomous driving).

Thresholds are FIXED and must NOT be tuned on the gold set (fair-comparison
condition vs Snorkel). See MAS spec §0, §5, §12.
"""
from __future__ import annotations
from pathlib import Path

# ---- paths ----
ROOT = Path(__file__).resolve().parents[2]
RUBRIC_DIR = ROOT / "rubrics"
MAS_OUT_DIR = ROOT / "DataSet" / "mas"
AUDIT_JSONL = MAS_OUT_DIR / "mas_audit.jsonl"
RANKED_CSV = MAS_OUT_DIR / "mas_ranked_scores.csv"

# ---- domain (single) ----
DOMAIN = "autonomous_driving"
# v2 = grounded in Bergeaud & Verluise (2023), the paper that built the gold set.
# Decisive axis: automate driving (SEED) vs assist a human driver (NOT_SEED).
RUBRIC_PATH = RUBRIC_DIR / f"{DOMAIN}_v2.json"

# ---- deterministic scoring knobs (Stage C). FIXED — do not gold-tune. ----
TAU_POS = 0.75      # final_score >= -> positive
TAU_NEG = 0.25      # final_score <= -> easy_negative
EX_CAP = 0.40       # score ceiling when exclusion is CONFIRMED (stance=="hard_negative")
# NOTE: a confirmed exclusion is the model's categorical exclusion_stance=="hard_negative",
# NOT a numeric risk threshold. The old EX_TRIGGER=0.70 collided with the model's
# "possible_exclusion" hedge (risk 0.7) and over-rejected true positives — removed.

# ---- model tiering (cost lever) ----
# high-frequency Node A -> cheap model ; low-frequency Node B -> (optional) stronger model
LLM_FAST = "gpt-4o-mini"     # or "claude-haiku-4-5", "gemini-2.0-flash-001"
LLM_STRONG = "gpt-4o-mini"   # set to a stronger model if desired; Node B is rare
LLM_TEMPERATURE = 0.0
LLM_PROVIDER = "openai"      # "openai" | "anthropic" | "google"

# ---- pilot / calibration ----
PILOT_SIZE = 80              # sampled from candidate pool (never gold)
