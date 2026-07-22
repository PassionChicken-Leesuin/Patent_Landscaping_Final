"""[4a] Quality-aware technology-axis synthesis with explicit provenance."""
from __future__ import annotations

import json

from src.mas.llm import StructuredLLM, Usage
from src.agentic.localdocs import owner_docs_block
from src.agentic.schemas import AxisSynthesisOut, CorpusDigestOut, QueryScopeOut
from src.agentic.workspace import Workspace


_AXIS_SYSTEM = """
You are the Technology-Axis Synthesis agent for a patent-landscaping system.
Create the smallest complete set of technical axes needed to define and judge the domain.

SOURCE ROLES (do not collapse them):
- user_query states the user's intended target, but is not a factual technical source;
- owner_doc is the highest authority for the owner's intended SCOPE, but may be incomplete,
  vague, or factually weak, so assess its quality instead of assuming perfection;
- web evidence supplies external factual support and missing technical coverage;
- corpus evidence shows what is present in the actual patent pool, but a corpus-only cluster
  must not silently redefine the domain;
- HITL answers, when present, are binding scope decisions for this run only.

First assess the owner document on scope clarity, technical completeness, and factual
reliability. Then anchor axes explicitly supported by the query/owner document. Autonomously
add supplemental axes when authoritative research or repeated corpus evidence reveals a
material gap. A corpus-only cluster without external or query support should normally be
disputed or excluded, not promoted to core. Record material conflicts as disputed axes and
unresolved_conflicts so they can reach HITL.

Every axis must carry at least one source_refs item. Use only references shown in the input:
source_type=user_query for the supplied query; owner_doc for local:// references; web for
http(s) references; corpus for named clusters/cases. Do not invent URLs or sources. Keep
axis ids canonical A1, A2, ... and output JSON only.
"""


class AxisSynthesisBlocked(RuntimeError):
    """Raised when the axis inventory has no auditable active content."""


_AXIS_REPAIR = """

Your previous axis draft violated the source-reference contract. Repair only the reported
faults. Every reference must be copied character-for-character from ALLOWED SOURCE REFERENCES.
Do not remove a supported axis merely to avoid fixing its provenance. Output the full corrected
AxisSynthesisOut JSON only.
"""


def evidence_catalog(ws: Workspace) -> str:
    """Preserve note-level URLs; the ordinary research summary intentionally drops them."""
    lines: list[str] = []
    for n in ws.read_jsonl(ws.notes_jsonl):
        ref = str(n.get("source_url", "")).strip()
        if not ref:
            continue
        source_type = "owner_doc" if ref.startswith("local://") else "web"
        lines.append(
            f"- [{source_type}] {ref} | {n.get('evidence_type', '?')} | "
            f"{n.get('confidence', '?')} | {n.get('claim', '')}"
        )
    return "\n".join(lines) or "(no extracted research notes)"


def allowed_source_references(ws: Workspace, digest: CorpusDigestOut) -> set[str]:
    refs = {"query.json"}
    refs |= {str(n.get("source_url", "")).strip() for n in ws.read_jsonl(ws.notes_jsonl)
             if str(n.get("source_url", "")).strip()}
    if ws.owner_docs_json.exists():
        refs |= {f"local://{d.get('name')}" for d in ws.read_json(ws.owner_docs_json).get("docs", [])
                 if d.get("name")}
    corpus_items = [*digest.main_clusters, *digest.representative_cases,
                    *digest.suspected_boundary_cases, *digest.mismatch_with_web_evidence]
    refs |= {f"corpus: {item}" for item in corpus_items if str(item).strip()}
    return refs


def _renumber_axes(out: AxisSynthesisOut) -> AxisSynthesisOut:
    for i, axis in enumerate(out.technology_axes, 1):
        axis.id = f"A{i}"
    return out


def canonicalize_source_refs(refs, allowed_refs: set[str]) -> None:
    """Repair only lossless prefix omissions; never fuzzy-match or invent a source."""
    for ref in refs:
        if ref.reference in allowed_refs:
            continue
        candidates = []
        if ref.source_type == "corpus":
            candidates.append(f"corpus: {ref.reference}")
        elif ref.source_type == "owner_doc":
            candidates.append(f"local://{ref.reference}")
        exact = [candidate for candidate in candidates if candidate in allowed_refs]
        if len(exact) == 1:
            ref.reference = exact[0]


def _canonicalize_reference_prefixes(out: AxisSynthesisOut,
                                     allowed_refs: set[str]) -> AxisSynthesisOut:
    for axis in out.technology_axes:
        canonicalize_source_refs(axis.source_refs, allowed_refs)
    return out


def _axis_faults(out: AxisSynthesisOut, allowed_refs: set[str]) -> list[str]:
    faults = []
    if not out.technology_axes:
        faults.append("no technology axes")
    if not any(a.status in ("core", "supplemental") for a in out.technology_axes):
        faults.append("no core or supplemental axis")
    faults += [f"{a.id} has no source_refs" for a in out.technology_axes
               if not a.source_refs]
    faults += [f"{a.id} cites unknown source {ref.reference}"
               for a in out.technology_axes for ref in a.source_refs
               if ref.reference not in allowed_refs]
    return faults


def render_axis_md(out: AxisSynthesisOut) -> str:
    a = out.owner_document_assessment
    lines = [
        "# Technology-axis synthesis", "",
        "## Owner-document assessment", "",
        f"- Present: {a.present}",
        f"- Overall quality: {a.overall_quality}",
        f"- Scope clarity: {a.scope_clarity}",
        f"- Technical completeness: {a.technical_completeness}",
        f"- Factual reliability: {a.factual_reliability}",
    ]
    if a.gaps:
        lines += ["- Gaps:"] + [f"  - {x}" for x in a.gaps]
    if a.conflicts:
        lines += ["- Conflicts:"] + [f"  - {x}" for x in a.conflicts]
    lines += ["", "## Technology axes", ""]
    for axis in out.technology_axes:
        lines.append(f"### {axis.id}. {axis.name} [{axis.status}; {axis.confidence}]")
        lines.append("")
        lines.append(axis.description)
        lines.append("")
        lines.append(f"- Owner documented: {axis.owner_documented}")
        lines.append(f"- Observed in corpus: {axis.observed_in_corpus}")
        lines.append(f"- Rationale: {axis.rationale}")
        lines.append("- Sources:")
        for ref in axis.source_refs:
            lines.append(
                f"  - [{ref.source_type}/{ref.strength}] {ref.reference}: {ref.claim}"
            )
        lines.append("")
    if out.unresolved_conflicts:
        lines += ["## Unresolved conflicts", ""]
        lines += [f"- {x}" for x in out.unresolved_conflicts]
    return "\n".join(lines).rstrip() + "\n"


def synthesize_axes(ws: Workspace, llm: StructuredLLM, scope: QueryScopeOut,
                    digest: CorpusDigestOut, usage: Usage,
                    force: bool = False) -> AxisSynthesisOut:
    allowed_refs = allowed_source_references(ws, digest)
    if ws.axis_synthesis_json.exists() and not force:
        cached = AxisSynthesisOut(**ws.read_json(ws.axis_synthesis_json))
        cached = _canonicalize_reference_prefixes(cached, allowed_refs)
        faults = _axis_faults(cached, allowed_refs)
        if faults:
            raise AxisSynthesisBlocked("cached axis synthesis blocked: " + "; ".join(faults))
        ws.axis_synthesis_blocked_json.unlink(missing_ok=True)
        return cached

    owner = owner_docs_block(ws)
    owner_manifest = ws.read_json(ws.owner_docs_json) if ws.owner_docs_json.exists() else {"docs": []}
    for item in owner_manifest.get("docs", []):
        item.pop("full_text", None)
    user = (
        f"=== USER QUERY / SCOPING ===\n"
        f"Canonical domain: {scope.canonical_name_en}\n"
        f"Disambiguation: {scope.disambiguation_notes}\n"
        f"Initial task hypotheses: {json.dumps(scope.initial_task_hypotheses, ensure_ascii=False)}\n"
        f"Query reference: query.json\n\n"
        f"=== OWNER DOCUMENT MANIFEST ===\n"
        f"{json.dumps(owner_manifest, ensure_ascii=False)}\n\n"
        f"=== OWNER DOCUMENT TEXT (short documents only) ===\n"
        f"{owner or '(no short full text; use owner_doc evidence notes if present)'}\n\n"
        f"=== EVIDENCE CATALOG WITH REFERENCES ===\n{evidence_catalog(ws)}\n\n"
        f"=== ALLOWED SOURCE REFERENCES (copy exactly; do not invent) ===\n"
        + "\n".join(f"- {ref}" for ref in sorted(allowed_refs)) + "\n\n"
        f"=== ACTUAL PATENT-POOL DIGEST ===\n"
        f"{json.dumps(digest.model_dump(), ensure_ascii=False)}"
    )
    out, pt, ct = llm.parse(_AXIS_SYSTEM, user, AxisSynthesisOut)
    usage.add(pt, ct)
    out = _canonicalize_reference_prefixes(_renumber_axes(out), allowed_refs)
    faults = _axis_faults(out, allowed_refs)
    if faults:
        repair_user = (
            user + "\n\n=== PREVIOUS AXIS DRAFT ===\n"
            + json.dumps(out.model_dump(), ensure_ascii=False)
            + "\n\n=== CONTRACT FAULTS TO REPAIR ===\n"
            + "\n".join(f"- {fault}" for fault in faults)
        )
        repaired, rpt, rct = llm.parse(_AXIS_SYSTEM + _AXIS_REPAIR,
                                       repair_user, AxisSynthesisOut)
        usage.add(rpt, rct)
        out = _canonicalize_reference_prefixes(_renumber_axes(repaired), allowed_refs)
        faults = _axis_faults(out, allowed_refs)
    if faults:
        report = {"status": "blocked", "faults": faults,
                  "draft": out.model_dump()}
        ws.write_json(ws.axis_synthesis_blocked_json, report)
        raise AxisSynthesisBlocked("axis synthesis blocked: " + "; ".join(faults))
    ws.write_json(ws.axis_synthesis_json, out.model_dump())
    ws.axis_synthesis_md.write_text(render_axis_md(out), encoding="utf-8")
    ws.axis_synthesis_blocked_json.unlink(missing_ok=True)
    return out
