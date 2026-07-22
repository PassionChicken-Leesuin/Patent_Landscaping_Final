"""[2] Web research agent: staged search -> filter -> read -> evidence notes -> gap loop.

Logic per round:
  1. execute each SearchIntent (server-side exclude_domains = leakage layer 1)
  2. filter results: leakage layer 2 (URL/title) -> dedupe -> quality ranking
  3. per kept page: acquire text, leakage layer 3 (content scan), then one LLM call
     extracts structured EvidenceNotes (layer 4: the LLM's own leak flag)
  4. end of round: gap analysis decides follow-up searches (bounded by config)

Everything is cached under research/ (searches.jsonl, pages/, notes.jsonl,
blocked.jsonl); already-seen URLs are skipped, so re-runs resume for free.
`collect_more()` is the re-entry point used by the validator feedback loops.
"""
from __future__ import annotations
import json

from src.mas.llm import StructuredLLM, Usage
from src.agentic import config as AC
from src.agentic import leakage as LK
from src.agentic.fetch import page_text
from src.agentic.schemas import (EvidenceNotesOut, GapAnalysisOut, INTENT_TYPES,
                                 QueryScopeOut, SearchIntent)
from src.agentic.search import SearchClient, SearchResult
from src.agentic.workspace import Workspace, url_hash

_PREFERRED_HINTS = ("wikipedia.org", ".edu", ".gov", ".org", "epo.org", "uspto.gov",
                    "wipo.int", "cooperativepatentclassification.org", "iea.org")

_NOTES_SYSTEM = (
    "You are the Evidence-Extraction agent of a patent-landscaping research system.\n"
    "You are given one web page collected for a specific research intent about a technology "
    "domain. Extract structured evidence notes strictly grounded in the page text.\n"
    "- claim: one self-contained factual sentence useful for defining the domain, its tasks, "
    "techniques, terminology, classification codes, adjacent-but-out-of-scope technologies, "
    "or borderline cases.\n"
    "- quote: a short supporting excerpt (<=200 chars) copied from the page.\n"
    "- Do NOT invent facts absent from the page.\n"
    "- page_is_relevant: false if the page is off-topic for the domain.\n"
    "- page_is_benchmark_leak: true if the page appears to describe an academic patent-"
    "landscaping BENCHMARK with seed/anti-seed gold sets (such content must not be used).\n"
    "Output JSON only."
)

_GAP_SYSTEM = (
    "You are the Research-Planning agent. Given the evidence notes collected so far "
    "(grouped by evidence type) for a technology domain, decide whether the research is "
    "sufficient to write an expert-grade criteria document for judging whether patents "
    "belong to the domain.\n"
    "- covered / missing: which of these intent types are sufficiently covered: "
    + ", ".join(INTENT_TYPES) + "\n"
    "- The document will need: a precise definition, defining functional tasks, technical "
    "signals, adjacent-but-out-of-scope technologies (for exclusion criteria), terminology, "
    "and classification codes.\n"
    "- If something is missing, propose concrete follow-up search queries (few, targeted).\n"
    "Output JSON only."
)


# ----------------------------------------------------------------- filtering
def _quality_key(r: SearchResult) -> tuple:
    preferred = any(h in r.url for h in _PREFERRED_HINTS)
    return (1 if preferred else 0, r.score)


def _filter_results(ws: Workspace, results: list[SearchResult], seen_urls: set[str],
                    intent_type: str) -> list[SearchResult]:
    kept = []
    for r in results:
        rule = LK.is_blocked_result(r.url, r.title)
        if rule:
            LK.log_block(ws.blocked_jsonl, {"layer": "result", "rule": rule,
                                            "url": r.url, "title": r.title,
                                            "intent_type": intent_type})
            continue
        if r.url in seen_urls:
            continue
        if len(r.content) < 200 and not r.raw_content:
            continue
        kept.append(r)
    kept.sort(key=_quality_key, reverse=True)
    return kept[:AC.MAX_PAGES_PER_SEARCH]


# ----------------------------------------------------------------- page -> notes
def _read_and_note(ws: Workspace, llm: StructuredLLM, result: SearchResult,
                   intent: SearchIntent, canonical_name: str, usage: Usage) -> int:
    """Acquire page text, run leak scan, extract notes. Returns #notes appended."""
    acquired = page_text(result)
    if not acquired:
        return 0
    text, source = acquired

    blocked, hits = LK.content_leak_scan(text)
    if blocked:
        LK.log_block(ws.blocked_jsonl, {"layer": "content", "rule": hits,
                                        "url": result.url, "title": result.title,
                                        "intent_type": intent.intent_type})
        return 0

    user = (f"Domain: {canonical_name}\n"
            f"Research intent: {intent.intent_type} — {intent.query_en}\n"
            f"Page title: {result.title}\nPage URL: {result.url}\n\n"
            f"Page text:\n{text}")
    out, pt, ct = llm.parse(_NOTES_SYSTEM, user, EvidenceNotesOut)
    usage.add(pt, ct)

    if out.page_is_benchmark_leak:
        LK.log_block(ws.blocked_jsonl, {"layer": "llm_flag", "rule": "page_is_benchmark_leak",
                                        "url": result.url, "title": result.title,
                                        "intent_type": intent.intent_type})
        return 0

    h = url_hash(result.url)
    ws.write_json(ws.pages_dir / f"{h}.json",
                  {"url": result.url, "title": result.title, "source": source,
                   "intent_type": intent.intent_type, "text": text})
    if not out.page_is_relevant:
        return 0
    n = 0
    for note in out.notes:
        ws.append_jsonl(ws.notes_jsonl, {**note.model_dump(), "source_url": result.url,
                                         "page_hash": h, "intent_type": intent.intent_type})
        n += 1
    return n


# ----------------------------------------------------------------- driving
def _seen_urls(ws: Workspace) -> set[str]:
    urls = set()
    for p in ws.pages_dir.glob("*.json"):
        try:
            urls.add(json.loads(p.read_text(encoding="utf-8"))["url"])
        except Exception:
            continue
    return urls


def run_intents(ws: Workspace, llm: StructuredLLM, client: SearchClient,
                intents: list[SearchIntent], canonical_name: str, usage: Usage) -> int:
    """Execute a list of search intents. Returns total notes appended."""
    seen = _seen_urls(ws)
    total_notes = 0
    for intent in intents:
        if len(seen) >= AC.MAX_TOTAL_PAGES:
            print(f"  [research] page cap {AC.MAX_TOTAL_PAGES} reached — stopping searches")
            break
        results = client.search(intent.query_en, max_results=AC.SEARCH_MAX_RESULTS,
                                exclude_domains=LK.EXCLUDE_SEARCH_DOMAINS)
        ws.append_jsonl(ws.searches_jsonl,
                        {"intent_type": intent.intent_type, "query": intent.query_en,
                         "n_results": len(results),
                         "urls": [r.url for r in results]})
        for r in _filter_results(ws, results, seen, intent.intent_type):
            seen.add(r.url)
            total_notes += _read_and_note(ws, llm, r, intent, canonical_name, usage)
    return total_notes


def notes_summary_by_type(ws: Workspace) -> str:
    """Aggregated claims grouped by evidence type — input for gap analysis / criteria."""
    notes = ws.read_jsonl(ws.notes_jsonl)
    by_type: dict[str, list[str]] = {}
    for n in notes:
        by_type.setdefault(n.get("evidence_type", "?"), []).append(n.get("claim", ""))
    lines = []
    for etype in ("definition", "task", "technique", "signal_term", "confusable",
                  "boundary_case", "cpc_code", "synonym"):
        claims = by_type.get(etype, [])
        lines.append(f"[{etype}] ({len(claims)} notes)")
        lines.extend(f"  - {c}" for c in claims)
    return "\n".join(lines)


def gap_analysis(ws: Workspace, llm: StructuredLLM, canonical_name: str,
                 usage: Usage) -> GapAnalysisOut:
    user = (f"Domain: {canonical_name}\n\nEvidence notes so far:\n{notes_summary_by_type(ws)}")
    out, pt, ct = llm.parse(_GAP_SYSTEM, user, GapAnalysisOut)
    usage.add(pt, ct)
    return out


def research(ws: Workspace, llm: StructuredLLM, client: SearchClient,
             scope: QueryScopeOut, usage: Usage) -> None:
    """Full staged research: initial plan + up to MAX_ROUNDS-1 gap-driven rounds."""
    intents = list(scope.search_plan)
    for rnd in range(1, AC.MAX_ROUNDS + 1):
        n = run_intents(ws, llm, client, intents, scope.canonical_name_en, usage)
        print(f"  [research] round {rnd}: {len(intents)} searches -> +{n} notes")
        if rnd == AC.MAX_ROUNDS:
            break
        gap = gap_analysis(ws, llm, scope.canonical_name_en, usage)
        if gap.research_complete or not gap.followup_queries:
            break
        intents = gap.followup_queries[:AC.MAX_FOLLOWUPS]


def collect_more(ws: Workspace, llm: StructuredLLM, client: SearchClient,
                 intents: list[SearchIntent], canonical_name: str, usage: Usage) -> int:
    """Validator-loop re-entry: run extra targeted searches, return #new notes."""
    intents = intents[:AC.MAX_FOLLOWUPS]
    n = run_intents(ws, llm, client, intents, canonical_name, usage)
    print(f"  [research] collect_more: {len(intents)} searches -> +{n} notes")
    return n
