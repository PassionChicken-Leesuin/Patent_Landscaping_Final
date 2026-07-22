"""Benchmark-leakage guard for the web research stage.

The 6 evaluation domains come from the Bergeaud & Verluise benchmark. The research
agent must never read that paper (or derivatives) — otherwise the "generalization"
measurement is contaminated. Three enforcement layers:

  1. server-side: exclude_domains passed to the search provider
  2. result-level: is_blocked_result(url, title) before fetching
  3. content-level: content_leak_scan(text) on every fetched page
     (+ a 4th soft check: the note-extraction LLM's page_is_benchmark_leak flag)

Every block is appended to research/blocked.jsonl for auditability.
Extend the lists below for future benchmarks — logic never changes.
"""
from __future__ import annotations
import json
import re
from pathlib import Path

# URL substrings (lowercase match) — the PLOS ONE paper, author repos/pages, PatCit.
BLOCK_URL_SUBSTRINGS = [
    "journal.pone.0295587",          # Bergeaud & Verluise (2024), any mirror carrying the DOI path
    "10.1371/journal.pone.0295587",
    "patcit",
    "cverluise",                      # C. Verluise GitHub / pages
    "verluise",
    "bergeaud",                       # author site / profile pages
    "github.com/antoineberg",
]

# Domains passed to the search provider's exclude_domains (best-effort, layer 1).
EXCLUDE_SEARCH_DOMAINS = [
    "journals.plos.org",
    "github.com",                     # PatCit & replication repos live here; low research value anyway
    "cverluise.github.io",
]

# Title/content regexes (case-insensitive). Any hit blocks a TITLE; a page BODY is
# blocked when >= CONTENT_MIN_HITS distinct patterns hit (single generic hits like
# "seed patents" in a survey are left to the LLM leak flag).
BLOCK_PATTERNS = [
    r"anti-?seed",
    r"\bpatcit\b",
    r"bergeaud.{0,60}verluise",
    r"verluise.{0,60}bergeaud",
    r"patent\s+landscap\w*\s+benchmark",
    r"s2\s+appendix",
    r"expansion[\s_-]?level",
    r"seed\s*/\s*anti-?seed",
]
CONTENT_MIN_HITS = 2

_COMPILED = [re.compile(p, re.IGNORECASE | re.DOTALL) for p in BLOCK_PATTERNS]


def is_blocked_url(url: str) -> str | None:
    """Return the matched rule if the URL is blocklisted, else None."""
    low = (url or "").lower()
    for sub in BLOCK_URL_SUBSTRINGS:
        if sub in low:
            return f"url:{sub}"
    return None


def is_blocked_result(url: str, title: str) -> str | None:
    """Layer 2: search-result filter (URL substrings + any title pattern hit)."""
    rule = is_blocked_url(url)
    if rule:
        return rule
    for pat in _COMPILED:
        if pat.search(title or ""):
            return f"title:{pat.pattern}"
    return None


def content_leak_scan(text: str) -> tuple[bool, list[str]]:
    """Layer 3: page-body scan. Blocked when >= CONTENT_MIN_HITS distinct patterns hit."""
    hits = [pat.pattern for pat in _COMPILED if pat.search(text or "")]
    return len(hits) >= CONTENT_MIN_HITS, hits


def log_block(blocked_jsonl: Path, entry: dict) -> None:
    blocked_jsonl.parent.mkdir(parents=True, exist_ok=True)
    with open(blocked_jsonl, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
