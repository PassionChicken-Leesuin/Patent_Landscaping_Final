"""[4a+] Design plan: fold the technology axes into a tiered selection design.

This is the system form of the "정답셋 설계 (안) §5" step: the axes from [4a] and the
pool profile from [3.5] are folded into T1 (direct/core), T2 (transferable core), and E
(excluded look-alikes) tiers. The tiers, NOT a hardcoded list, are what the case-mapping
stage iterates over — so the procedure generalizes to any domain whose axes differ.
"""
from __future__ import annotations

from src.agentic import config as AC
from src.agentic.schemas import (AlignmentDiagnosisOut, AxisSynthesisOut, DesignPlanOut,
                                 PoolProfile)
from src.agentic.workspace import Workspace
from src.mas.llm import StructuredLLM, Usage

_SYSTEM = """
You are the Design-Plan agent of a patent-landscaping system. Given the domain's technology
axes, the pool profile, and the alignment diagnosis, produce the tiered selection design that
the case-mapping stage will iterate over.

Tiers:
- T1 (direct / core): patents that ARE the domain itself — its proper subject, complete
  products/platforms, or whole-system control. Anchor to the axes the diagnosis marks as
  directly defining the domain.
- T2 (transferable core): enabling component/function technologies from the value chain that
  transfer INTO the domain. Create ONE T2 tier PER core technology axis (A1, A2, ...) so each
  axis becomes its own case-mapping category. Name each tier after its axis.
- E (excluded look-alikes): technologies that surface in the same search but do not perform
  the domain's defining task — adjacent fields, single-purpose equipment, and out-of-scope
  applications. Create one E tier per distinct exclusion family you expect in this pool
  (grounded in the corpus boundary cases and adjacent-out-of-scope evidence), not a generic one.

For every tier give: tier, name, the anchoring axis_ids, a one-paragraph definition, the
title/abstract expected_signals that mark it, and an est_count_lo..est_count_hi range grounded
in the pool profile (they need not sum to the pool size; tiers overlap and E is the remainder).
Set judging_unit to the family-representative convention. Output JSON only.
"""


def build_design_plan(ws: Workspace, llm: StructuredLLM, axes: AxisSynthesisOut,
                      profile: PoolProfile, diagnosis: AlignmentDiagnosisOut, usage: Usage,
                      *, force: bool = False) -> DesignPlanOut:
    if ws.design_plan_json.exists() and not force:
        return DesignPlanOut(**Workspace.read_json(ws.design_plan_json))

    axis_lines = [
        f"- {a.id} [{a.status}] {a.name}: {a.description}"
        for a in axes.technology_axes
    ]
    user = (
        f"POOL SIZE: {profile.n_total} (family-dedup {profile.n_family_dedup})\n"
        f"DIRECT-DOMAIN mentions: {profile.direct_domain_mention} "
        f"({profile.direct_domain_pct:.1%}) — terms: {', '.join(profile.direct_domain_terms)}\n"
        f"TOP ASSIGNEES: " + ", ".join(f"{a.name}({a.count})" for a in profile.top_assignees[:12]) + "\n"
        f"ALIGNMENT NOTES:\n" + "\n".join(f"- {n}" for n in diagnosis.alignment_notes) + "\n\n"
        f"TECHNOLOGY AXES:\n" + "\n".join(axis_lines) + "\n"
    )
    out, pt, ct = llm.parse(_SYSTEM, user, DesignPlanOut)
    usage.add(pt, ct)
    out.tiers = out.tiers[:AC.CASEMAP_MAX_CATEGORIES]
    ws.write_json(ws.design_plan_json, out.model_dump())
    return out
