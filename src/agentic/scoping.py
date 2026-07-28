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

_OWNER_ANCHOR = (
    "\n\nIMPORTANT — an OWNER SCOPE DOCUMENT is provided below. It is AUTHORITATIVE for this "
    "domain's scope. Anchor initial_task_hypotheses and the in-/out-of-scope on it, and "
    "PRESERVE its specific CORE-TECHNOLOGY terms (including acronyms such as GNSS, AR/VR) — do "
    "NOT broaden, generalize, or drop the core technology from the user query.\n"
    "BUT keep canonical_name_en at the CORE-TECHNOLOGY level (the technology the invention IS). "
    "Do NOT append an application/industry CONTEXT (e.g. 'for marine/offshore use', 'for "
    "automotive') to the canonical name UNLESS the owner document states that context is a "
    "REQUIRED element of every in-scope patent. When the owner marks a context as NON-required "
    "('not a hard requirement', 'application context', 'including but not limited to'), treat it "
    "as OPTIONAL — never fold it into the canonical name or as a scope restriction."
)


def scope_query(llm: StructuredLLM, query: str, usage: Usage,
                owner_context: str = "") -> QueryScopeOut:
    system = _SYSTEM + (_OWNER_ANCHOR if owner_context.strip() else "")
    user = f"User query: {query}"
    if owner_context.strip():
        user += f"\n\nOWNER SCOPE DOCUMENT (authoritative):\n{owner_context.strip()[:4000]}"
    out, pt, ct = llm.parse(system, user, QueryScopeOut)
    usage.add(pt, ct)
    return out
