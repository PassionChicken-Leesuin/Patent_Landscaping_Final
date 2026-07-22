"""[1] Scoping agent: NL query (any language) -> canonical scope + typed search plan."""
from __future__ import annotations

from src.mas.llm import StructuredLLM, Usage
from src.agentic.schemas import INTENT_TYPES, QueryScopeOut

_SYSTEM = (
    "You are the Scoping agent of a patent-landscaping research system.\n"
    "Given a user's natural-language query naming a technological domain (the query may be "
    "in any language, e.g. Korean), produce:\n"
    "1. canonical_name_en — the standard English name of the technology domain.\n"
    "2. language_detected — ISO code of the query language.\n"
    "3. disambiguation_notes — if the query is ambiguous, state the interpretation chosen and why.\n"
    "4. initial_task_hypotheses — 3-6 hypotheses about the FUNCTIONAL TASKS that define this "
    "domain (what an invention must actually DO to belong), phrased as full sentences.\n"
    "5. search_plan — EXACTLY one web-search intent per intent_type, in this order: "
    + ", ".join(INTENT_TYPES) + ".\n"
    "   Each intent has an effective English search query and a one-sentence rationale.\n"
    "   - adjacent_out_of_scope must target technologies that LOOK like the domain but do not "
    "perform its defining tasks (these become exclusion criteria later).\n"
    "   - classification_codes must target official CPC/IPC classes for the domain.\n"
    "Output JSON only."
)


def scope_query(llm: StructuredLLM, query: str, usage: Usage) -> QueryScopeOut:
    out, pt, ct = llm.parse(_SYSTEM, f"User query: {query}", QueryScopeOut)
    usage.add(pt, ct)
    return out
