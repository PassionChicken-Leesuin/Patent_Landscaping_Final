"""Rubric loading. Static JSON by default (no LLM call needed to run).

Optionally regenerate via an LLM (Domain Rubric Agent), but for a single fixed
domain the hand-seeded rubric is versioned and reused — cost ≈ 0.
"""
from __future__ import annotations
import json
from pathlib import Path

from src.mas import config as MC


def load_rubric(path: Path | str = MC.RUBRIC_PATH) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)
