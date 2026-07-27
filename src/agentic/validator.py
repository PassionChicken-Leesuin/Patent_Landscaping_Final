"""[5] Criteria validator + feedback-loop controller.

The validator criticizes the sentence-form criteria document; its action drives
the loop: revise (redraft with the critique), collect_more (re-enter the research
agent with targeted searches), ask_human (HITL), approve (finalize). Budgeted by
CRITERIA_MAX_ITERS; budget exhaustion with a critical issue or unresolved external
action writes criteria_blocked.json and stops without a final document.
"""
from __future__ import annotations
import json
import re

import pandas as pd

from src.mas.llm import StructuredLLM, Usage
from src.mas.runner import KeyPool
from src.agentic import config as AC
from src.agentic import research as R
from src.agentic.axes import allowed_source_references
from src.agentic.boundary_probe import measured_questions, probe_boundaries
from src.agentic.criteria import (PatchApplyError, draft_criteria, patch_criteria,
                                  resolve_open_questions, save_final)
from src.agentic.hitl import HITL
from src.agentic.schemas import (AxisSynthesisOut, CriteriaCritiqueOut, CriteriaDocOut,
                                 CorpusDigestOut, CritiqueIssue, HITLQuestion,
                                 IssueResolutionOut, QueryScopeOut)
from src.agentic.search import SearchClient
from src.agentic.workspace import Workspace

_CRITIQUE_SYSTEM = (
    "You are the Criteria Validator — an adversarial patent-domain expert reviewing the "
    "criteria document that will govern patent judgments for the domain: {domain}.\n"
    "Check rigorously:\n"
    "1. TESTABILITY CONTRACT: a C/E criterion is testable when it (a) states a functional "
    "task and (b) lists non-exclusive observable_signals (title/abstract cues). Flag "
    "testability ONLY when a criterion lacks a functional task or has no usable signals. "
    "Signals are indicative cues, never required keywords; do not demand certainty from a "
    "title+abstract, and never reject a criterion merely for relying on indicative terms.\n"
    "2. Do the C-criteria cover ALL defining functional tasks found in the evidence, and do "
    "they demand that the invention PERFORMS a task (not merely mentions vocabulary)?\n"
    "3. Are the E-criteria genuinely 'rule-match-but-not-the-task' shaped (adjacent/look-"
    "alike technologies), not just restatements of 'irrelevant'?\n"
    "4. Does boundary_guidance actually resolve the borderline patterns reported in the "
    "pool digest?\n"
    "4b. Do scope_decisions cover EVERY main cluster of the pool digest, and is each "
    "verdict's rationale actually supported by evidence (not an unexamined narrow default)? "
    "A major pool cluster ruled out with a weak rationale is a critical fault — if the "
    "call genuinely cannot be settled from evidence, that is what ask_human is for.\n"
    "4c. CONSISTENCY: a scope verdict that contradicts an exclusion criterion is a critical "
    "fault (e.g. an assist-technology cluster ruled 'in' while an E-criterion excludes "
    "assist technologies). 'Important/essential to the domain' used as an in-rationale is a "
    "critical fault. A dual-form cluster with a blanket in/out instead of 'conditional' + "
    "decisive test is a critical fault.\n"
    "5. Is the definition faithful to the user's query scope (no silent narrowing or "
    "broadening)? Are cited sources plausible?\n"
    "Rate every issue's severity: 'critical' = it would MATERIALLY change judgment outcomes "
    "on the pool (wrong scope ruling, untestable criterion, missing whole task family); "
    "'minor' = polish (an extra example, finer wording, a sub-technique not named but "
    "already generically covered by an existing criterion).\n"
    "Decide ONE action:\n"
    "- approve: no CRITICAL issues remain — approve even when minor issues exist (list them; "
    "do not hold the document hostage to perfection).\n"
    "- revise: at least one critical issue is fixable by rewriting.\n"
    "- collect_more: evidence is insufficient on some aspect — propose targeted follow-up "
    "searches (followup_queries).\n"
    "- ask_human: a genuine scope decision only the human owner can make (e.g. whether an "
    "ambiguous sub-area is in scope) — write clear natural-language human_questions with "
    "options where possible.\n"
    "ESCALATION RULE: if you challenge a scope_decision verdict (a cluster's in/out ruling) "
    "and the available evidence cannot settle it, the action MUST be ask_human — rewriting "
    "cannot resolve a question of the owner's intent. Never spend a revise round on a scope "
    "dispute.\n"
    "Output JSON only."
)


_PROVENANCE_CRITIQUE = (
    "\n6. AXIS COVERAGE: every core/supplemental technology axis must map to at least one "
    "C-criterion through axis_ids; disputed axes must remain explicit boundaries.\n"
    "7. PROVENANCE: every axis and every C/E criterion must carry typed source_refs whose "
    "references exist in the supplied evidence/axis synthesis. Legacy sources alone are "
    "insufficient. Missing whole-axis coverage or provenance is critical.\n"
    "8. OWNER-DOCUMENT QUALITY: respect owner scope intent, but verify that documented gaps "
    "were supplemented where research/corpus evidence supports doing so.\n"
)

_LEDGER_CRITIQUE = (
    "\nISSUE IDENTITY & LEDGER PROTOCOL:\n"
    "- For EVERY issue fill category, target_ids (the specific C/E/A ids or scope topics "
    "affected), and issue_code formatted 'CATEGORY:TARGET' (e.g. TESTABILITY:C1, "
    "PROVENANCE:E5, SCOPE_CONFLICT:FUEL_CELLS).\n"
    "- When a PRIOR OPEN ISSUES ledger is supplied, adjudicate each entry FIRST: if the "
    "current document resolves it, do not re-report it; if unresolved, re-report it with "
    "EXACTLY the same issue_code — never a reworded new code for the same problem.\n"
    "- category=scope_decision marks a genuine owner-intent question. It is settled by the "
    "owner, never by rewriting. Do not re-litigate an explicitly recorded human ruling, and "
    "when an unattended run documents a provisional system assumption for a boundary (kept "
    "in open_questions), accept it as resolved-for-this-run instead of repeating the "
    "conflict every round.\n"
    "- NEW-CRITICAL CONSTRAINT (after a targeted patch revision): a NEW critical on an "
    "untouched field is allowed only with concrete evidence — a violated invariant, the "
    "conflicting criterion ids in target_ids, or an affected patent counterexample. "
    "Otherwise report it as minor.\n"
)


class CriteriaValidationBlocked(RuntimeError):
    """Raised when the criteria budget ends with material faults unresolved."""

    def __init__(self, path, critical_count: int):
        self.path = path
        self.critical_count = critical_count
        super().__init__(
            f"criteria validation blocked with {critical_count} critical issue(s); see {path}"
        )


def _norm_code(code: str) -> str:
    return re.sub(r"[^A-Za-z0-9:_,.-]+", "_", str(code).strip()).upper()[:80]


def issue_code_for(issue: CritiqueIssue) -> str:
    """Stable structural identity: prose wording drifts every round, codes must not."""
    if issue.issue_code.strip():
        return _norm_code(issue.issue_code)
    target = "-".join(issue.target_ids) if issue.target_ids else issue.field
    return _norm_code(f"{issue.category}:{target}")


# Codes in this namespace come from deterministic checks — they can never be
# downgraded by the new-critical constraint.
_DETERMINISTIC_PREFIXES = ("AXIS_COVERAGE:", "AXIS_IDS:", "PROVENANCE", "EXCL_COVERAGE:",
                           "ALIGN_COVERAGE:")

# Generic words that do not distinguish one exclusion family from another.
_EXCL_STOP = {"and", "or", "the", "of", "for", "with", "technologies", "technology",
              "systems", "system", "robot", "robotic", "robots", "general", "based",
              "other", "device", "devices", "method", "methods", "look", "alike",
              "adjacent", "excluded", "exclusion", "non", "type"}


def _family_tokens(name: str) -> list[str]:
    import re as _re
    return [t for t in _re.findall(r"[a-z]{4,}", (name or "").lower())
            if t not in _EXCL_STOP]


def exclusion_coverage_issues(doc: CriteriaDocOut,
                              exclusion_families: list[dict] | None) -> list[CritiqueIssue]:
    """Every exclusion family the case-mapping stage identified (a design-plan E-tier =
    an empirically-found look-alike cluster) MUST be encoded as an enforceable exclusion,
    or the pool's look-alikes leak into the positives (the precision failure mode). This
    is domain-general: it fires for any domain's adjacent-out-of-scope families, not just
    the humanoid industrial-lookalike cluster."""
    issues: list[CritiqueIssue] = []
    if not exclusion_families:
        return issues
    haystack = " ".join(c.statement.lower() for c in doc.exclusion_criteria)
    haystack += " " + " ".join(
        (s.topic + " " + s.rationale).lower()
        for s in doc.scope_decisions if s.verdict in ("out", "conditional"))
    for fam in exclusion_families:
        toks = _family_tokens(fam.get("name", ""))
        if not toks:
            continue                              # no distinctive term to check
        if not any(t in haystack for t in toks):
            slug = fam.get("name", "?")[:40]
            issues.append(CritiqueIssue(
                field="exclusion_criteria",
                problem=(f"Exclusion family '{fam.get('name','')}' found by case-mapping "
                         f"has no exclusion criterion. Its look-alike patents will be "
                         f"admitted as positives."),
                suggestion=(f"Add an E-criterion for '{fam.get('name','')}' stating the "
                            f"decisive CLAIM-SCOPE test (exclude when the claim is bound to "
                            f"this use/process; keep the transferable capability in scope): "
                            f"{fam.get('definition','')[:160]}"),
                severity="critical", category="coverage", target_ids=[],
                issue_code=f"EXCL_COVERAGE:{slug}"))
    return issues


def alignment_coverage_issues(doc: CriteriaDocOut, digest) -> list[CritiqueIssue]:
    """Every web<->pool alignment row that flags a look-alike to EXCLUDE (relation
    pool_only/conflict, implies=exclusion) MUST be cited by an exclusion criterion. This
    grounds each exclusion in the auditable web<->pool comparison — the precision lever — and
    makes the comparison procedure deterministically checkable (paper: 'auditable comparison').
    Fires only when such alignment rows exist, so domains without web evidence are unaffected."""
    issues: list[CritiqueIssue] = []
    rows = getattr(digest, "alignment", None) or []
    if not rows:
        return issues
    cited = {str(ref.reference).strip() for e in doc.exclusion_criteria for ref in e.source_refs}
    cited |= {str(s).strip() for e in doc.exclusion_criteria for s in e.sources}
    for a in rows:
        if (a.relation in ("pool_only", "conflict") and a.implies == "exclusion"
                and a.id and a.id not in cited):
            issues.append(CritiqueIssue(
                field="exclusion_criteria",
                problem=(f"Web<->pool alignment {a.id} ({a.relation}) flags a look-alike to "
                         f"exclude, but no exclusion criterion cites it: {a.statement}"),
                suggestion=(f"Add or extend an exclusion criterion whose source_refs cite "
                            f"{a.id} (source_type 'alignment'), excluding this look-alike by "
                            f"its decisive claim-scope test."),
                severity="critical", category="coverage", target_ids=[a.id],
                issue_code=f"ALIGN_COVERAGE:{a.id}"))
    return issues


def criteria_integrity_issues(doc: CriteriaDocOut,
                              axes: AxisSynthesisOut,
                              allowed_refs: set[str] | None = None,
                              exclusion_families: list[dict] | None = None) -> list[CritiqueIssue]:
    """Deterministic checks that cannot be waived by a prose validator."""
    issues: list[CritiqueIssue] = list(exclusion_coverage_issues(doc, exclusion_families))
    axis_ids = {a.id for a in axes.technology_axes}
    anchored_refs = {ref.reference for a in axes.technology_axes for ref in a.source_refs}
    valid_refs = anchored_refs | (allowed_refs or set())
    active_ids = {a.id for a in axes.technology_axes
                  if a.status in ("core", "supplemental")}
    mapped = {aid for c in doc.domain_criteria for aid in c.axis_ids}
    for aid in sorted(active_ids - mapped):
        issues.append(CritiqueIssue(
            field="domain_criteria.axis_ids",
            problem=f"Active technology axis {aid} lacks a C-criterion mapping.",
            suggestion="Map the axis to a testable inclusion criterion.",
            severity="critical", category="coverage", target_ids=[aid],
            issue_code=f"AXIS_COVERAGE:{aid}"))
    if not axes.technology_axes:
        issues.append(CritiqueIssue(
            field="technology_axes", problem="No technology axes were synthesized.",
            suggestion="Synthesize an auditable axis inventory before drafting criteria.",
            severity="critical", category="coverage", target_ids=[],
            issue_code="AXIS_COVERAGE:NONE"))
    for axis in axes.technology_axes:
        if not axis.source_refs:
            issues.append(CritiqueIssue(
                field=f"technology_axes.{axis.id}.source_refs",
                problem=f"Axis {axis.id} has no typed provenance.",
                suggestion="Attach a real query/owner/web/corpus source reference.",
                severity="critical", category="provenance", target_ids=[axis.id],
                issue_code=f"PROVENANCE:{axis.id}"))
        for ref in axis.source_refs:
            malformed = ((ref.source_type == "web"
                          and not ref.reference.startswith(("http://", "https://", "web:")))
                         or (ref.source_type == "owner_doc" and not ref.reference.startswith("local://"))
                         or (ref.source_type == "corpus" and not ref.reference.startswith("corpus:"))
                         or (ref.source_type == "alignment" and not ref.reference.startswith("align:")))
            if malformed:
                issues.append(CritiqueIssue(
                    field=f"technology_axes.{axis.id}.source_refs",
                    problem=f"Axis {axis.id} has a malformed {ref.source_type} reference: {ref.reference}",
                    suggestion="Use the exact typed reference format from the input catalog.",
                    severity="critical", category="provenance", target_ids=[axis.id],
                    issue_code=f"PROVENANCE_FORMAT:{axis.id}"))
    for item in [*doc.domain_criteria, *doc.exclusion_criteria]:
        unknown = sorted(set(item.axis_ids) - axis_ids)
        if unknown:
            issues.append(CritiqueIssue(
                field=f"{item.id}.axis_ids",
                problem=f"Criterion {item.id} cites unknown axes: {unknown}",
                suggestion="Use only ids from the approved axis synthesis.",
                severity="critical", category="consistency", target_ids=[item.id],
                issue_code=f"AXIS_IDS:{item.id}"))
        if not item.source_refs:
            issues.append(CritiqueIssue(
                field=f"{item.id}.source_refs",
                problem=f"Criterion {item.id} has no typed provenance.",
                suggestion="Copy supporting typed references from mapped axes/evidence.",
                severity="critical", category="provenance", target_ids=[item.id],
                issue_code=f"PROVENANCE:{item.id}"))
        unknown_refs = sorted({ref.reference for ref in item.source_refs
                               if ref.source_type != "hitl"
                               and ref.reference not in valid_refs})
        if unknown_refs:
            issues.append(CritiqueIssue(
                field=f"{item.id}.source_refs",
                problem=f"Criterion {item.id} cites references absent from the allowed evidence catalog: {unknown_refs}",
                suggestion="Cite an exact reference id from the allowed evidence catalog.",
                severity="critical", category="provenance", target_ids=[item.id],
                issue_code=f"PROVENANCE_REF:{item.id}"))
    return issues


class IssueLedger:
    """Cross-round identity for critical issues (criteria_issue_ledger.json).
    Prose critics reword the same fault every round; the ledger pins each fault to a
    structural code so convergence is measurable and re-reports stay recognizable."""

    def __init__(self, ws: Workspace):
        self.ws = ws
        self.data = (ws.read_json(ws.criteria_issue_ledger_json)
                     if ws.criteria_issue_ledger_json.exists() else {"issues": {}})

    def open_codes(self) -> set[str]:
        return {code for code, rec in self.data["issues"].items()
                if rec.get("status") == "open"}

    def update(self, rnd: int, version: int, critique: CriteriaCritiqueOut) -> None:
        seen: set[str] = set()
        for issue in critique.issues:
            if issue.severity != "critical":
                continue
            code = issue_code_for(issue)
            issue.issue_code = code
            seen.add(code)
            rec = self.data["issues"].setdefault(code, {
                "issue_code": code, "first_round": rnd, "rounds_open": 0})
            rec.update({"status": "open", "last_round": rnd, "last_version": version,
                        "category": issue.category, "target_ids": issue.target_ids,
                        "field": issue.field, "problem": issue.problem,
                        "rounds_open": rec.get("rounds_open", 0) + 1})
        for code, rec in self.data["issues"].items():
            if rec.get("status") == "open" and code not in seen:
                rec["status"] = "resolved"
                rec["resolved_round"] = rnd
        self.ws.write_json(self.ws.criteria_issue_ledger_json, self.data)

    def prompt_block(self) -> str:
        rows = [rec for rec in self.data["issues"].values()
                if rec.get("status") == "open"]
        if not rows:
            return ""
        return ("\n=== PRIOR OPEN ISSUES (adjudicate each; reuse the exact issue_code "
                "when re-reporting) ===\n"
                + "\n".join(f"- {r['issue_code']} [{r.get('category', '?')}] "
                            f"(open {r.get('rounds_open', 1)} round(s)): {r.get('problem', '')}"
                            for r in rows))


_VERIFY_SYSTEM = (
    "You are a fresh verification judge for a patent-criteria document. You are given ONE "
    "previously reported issue and the CURRENT document. Decide whether the current "
    "document demonstrably resolves this specific issue.\n"
    "- Judge ONLY this issue, from the document text alone.\n"
    "- Default to resolved=false unless you can cite the exact criterion id, scope "
    "decision, or sentence that resolves it (put it in evidence).\n"
    "- For a scope_decision issue, an explicit conditional ruling with a decisive test, "
    "or an explicitly documented provisional assumption, counts as resolved for this "
    "document (the owner question may still be listed for later review).\n"
    "Output JSON only."
)


def verify_issue_resolution(llm: StructuredLLM, doc: CriteriaDocOut,
                            issue: CritiqueIssue, usage: Usage) -> IssueResolutionOut:
    """Blind check by a clean context: no ledger, no critique history — this breaks
    critic anchoring (관찰: C6가 MOF를 명시 커버해도 COVERAGE:MOFS를 계속 재보고)."""
    user = (f"=== REPORTED ISSUE ===\n{json.dumps(issue.model_dump(), ensure_ascii=False)}\n\n"
            f"=== CURRENT DOCUMENT ===\n{json.dumps(doc.model_dump(), ensure_ascii=False)}")
    out, pt, ct = llm.parse(_VERIFY_SYSTEM, user, IssueResolutionOut)
    usage.add(pt, ct)
    return out


def constrain_new_criticals(critique: CriteriaCritiqueOut, prev_open: set[str],
                            touched: set[str]) -> list[str]:
    """After a targeted patch: a brand-new critical on an untouched field must carry
    invariant-level evidence (consistency category naming >= 2 concrete ids), else it
    is demoted to minor. Deterministic codes are never demoted. Returns demoted codes."""
    demoted: list[str] = []
    for issue in critique.issues:
        if issue.severity != "critical":
            continue
        code = issue_code_for(issue)
        if code in prev_open or code.startswith(_DETERMINISTIC_PREFIXES):
            continue
        touches_patched = any(t in touched for t in issue.target_ids) or (
            issue.field in touched)
        if touches_patched:
            continue
        evidenced = issue.category == "consistency" and len(set(issue.target_ids)) >= 2
        if not evidenced:
            issue.severity = "minor"
            issue.suggestion += (" [demoted: new issue on an untouched field without "
                                 "invariant-level evidence]")
            demoted.append(code)
    return demoted


def critique_criteria(llm: StructuredLLM, doc: CriteriaDocOut, scope: QueryScopeOut,
                      digest: CorpusDigestOut, axes: AxisSynthesisOut,
                      evidence_summary: str,
                      usage: Usage,
                      allowed_refs: set[str] | None = None,
                      ledger_block: str = "",
                      exclusion_families: list[dict] | None = None) -> CriteriaCritiqueOut:
    user = (f"=== Criteria document ===\n{json.dumps(doc.model_dump(), ensure_ascii=False)}\n\n"
            f"=== Approved axis synthesis ===\n{json.dumps(axes.model_dump(), ensure_ascii=False)}\n\n"
            f"=== Pool digest ===\n{json.dumps(digest.model_dump(), ensure_ascii=False)}\n\n"
            f"=== Evidence notes ===\n{evidence_summary}"
            + (f"\n{ledger_block}" if ledger_block else ""))
    out, pt, ct = llm.parse(_CRITIQUE_SYSTEM.format(domain=scope.canonical_name_en)
                            + _PROVENANCE_CRITIQUE + _LEDGER_CRITIQUE,
                            user, CriteriaCritiqueOut)
    usage.add(pt, ct)
    deterministic = (criteria_integrity_issues(doc, axes, allowed_refs, exclusion_families)
                     + alignment_coverage_issues(doc, digest))
    out.issues = reconcile_issues(out.issues, deterministic)
    if any(i.severity == "critical" and i.issue_code.startswith(_DETERMINISTIC_PREFIXES)
           for i in out.issues):
        out.approved = False
        if out.action == "approve":
            out.action = "revise"
    return out


def reconcile_issues(llm_issues: list[CritiqueIssue],
                     deterministic: list[CritiqueIssue]) -> list[CritiqueIssue]:
    """Mechanical truth belongs to code: a deterministic-namespace code the current
    checks no longer produce is FIXED, however insistently the prose critic re-reports
    it (observed: ledger echo kept AXIS_COVERAGE:A6/A7 open after C6/C7 covered them)."""
    det_codes = {issue_code_for(i) for i in deterministic}
    kept = []
    for issue in llm_issues:
        issue.issue_code = issue_code_for(issue)
        if (issue.issue_code.startswith(_DETERMINISTIC_PREFIXES)
                and issue.issue_code not in det_codes):
            continue
        kept.append(issue)
    known = {i.issue_code for i in kept}
    kept.extend(i for i in deterministic if issue_code_for(i) not in known)
    return kept


def criteria_loop(ws: Workspace, llm: StructuredLLM, client: SearchClient,
                  scope: QueryScopeOut, digest: CorpusDigestOut,
                  axes: AxisSynthesisOut, usage: Usage,
                  hitl: HITL, pool_df: pd.DataFrame | None = None,
                  probe_pool: KeyPool | None = None,
                  front_matter: str = "",
                  exclusion_families: list[dict] | None = None) -> CriteriaDocOut:
    """Draft -> (probe + ask author's own scope questions) -> critique -> {approve |
    revise | collect_more | ask_human} loop."""
    evidence_summary = R.notes_summary_by_type(ws)
    allowed_refs = allowed_source_references(ws, digest)
    # Research-run isolation: only answers collected during THIS criteria loop
    # enter later drafts. No user ruling from another run is seeded here.
    human_qa_all: list[dict] = []
    ver = 1                                              # next unused criteria version

    # Batch-HITL resume: if a pending draft was persisted and answers are now available,
    # reuse that EXACT draft (same question ids) instead of redrafting non-deterministically.
    resuming = ws.criteria_pending_json.exists() and ws.answers_json.exists()
    if resuming:
        doc = CriteriaDocOut(**ws.read_json(ws.criteria_pending_json))
        print(f"  [criteria] resuming pending draft with {len(doc.open_questions)} "
              f"answered question(s)")
    else:
        doc = draft_criteria(ws, llm, scope, digest, axes, evidence_summary, usage, version=1,
                             human_qa=human_qa_all or None, front_matter=front_matter)

    # PROACTIVE scope questions: the author flags candidate boundaries; we MEASURE each by
    # judging a pool sample under its broad vs narrow rule and keep only those that flip a
    # real number of patents (ranked by measured impact). Then ask the human BEFORE spending
    # the critique budget (answers are authoritative and baked into a revised draft).
    if doc.open_questions:
        if not resuming and pool_df is not None and probe_pool is not None and len(pool_df):
            ranked = probe_boundaries(doc.open_questions, pool_df, probe_pool,
                                      scope.canonical_name_en, ws.boundary_probe_jsonl)
            kept = measured_questions(ranked)
            ws.append_jsonl(ws.boundary_probe_jsonl,
                            {"summary": [{"id": q.id, "flip": f, "n": n} for q, f, n in ranked]})
            print(f"  [criteria] probed {len(doc.open_questions)} candidate boundaries "
                  f"-> {len(kept)} move real patents")
            doc.open_questions = kept
            # Enrich these scope questions into decision cards (stake/포함·제외 논리+예시/영향/
            # 권고, Korean) so the UI shows them with the SAME card as the upfront decisions.
            from src.agentic.decisions import enrich_open_questions
            kept_ids = {q.id for q in kept}
            enrich_open_questions(ws, llm, [(q, f, n) for q, f, n in ranked if q.id in kept_ids],
                                  usage)
        if doc.open_questions:
            # persist BEFORE asking so a batch-mode stop resumes on the same questions
            ws.write_json(ws.criteria_pending_json, doc.model_dump())
            print(f"  [criteria] asking human {len(doc.open_questions)} scope question(s)")
            doc, qa = resolve_open_questions(ws, llm, scope, digest, axes, evidence_summary,
                                             doc, hitl, usage, version=ver)
            human_qa_all += qa
            ver = 2
            ws.criteria_pending_json.unlink(missing_ok=True)   # answered -> clear

    versions: dict[int, tuple[CriteriaDocOut, int, CriteriaCritiqueOut]] = {}
    ledger = IssueLedger(ws)
    prev_open: set[str] | None = None
    no_progress = 0
    touched: set[str] = set()          # fields edited by the LAST revision
    last_was_patch = False
    stop_reason = "criteria loop budget exhausted"

    for rnd in range(1, AC.CRITERIA_MAX_ITERS + 1):
        critique = critique_criteria(llm, doc, scope, digest, axes, evidence_summary, usage,
                                     allowed_refs=allowed_refs,
                                     ledger_block=ledger.prompt_block(),
                                     exclusion_families=exclusion_families)
        if last_was_patch:
            demoted = constrain_new_criticals(critique, prev_open or set(), touched)
            if demoted:
                print(f"  [criteria] {len(demoted)} unevidenced new critical(s) on "
                      f"untouched fields demoted to minor: {demoted}")
        # Blind verification: a persistent non-deterministic critical gets one clean
        # per-issue check; a critic anchored on the ledger cannot close its own reports.
        for issue in [i for i in list(critique.issues) if i.severity == "critical"
                      and i.issue_code in (prev_open or set())
                      and not i.issue_code.startswith(_DETERMINISTIC_PREFIXES)]:
            verdict = verify_issue_resolution(llm, doc, issue, usage)
            if verdict.resolved:
                critique.issues.remove(issue)
                print(f"  [criteria] blind verification closed {issue.issue_code} "
                      f"({verdict.evidence[:80]})")
        ledger.update(rnd, ver, critique)
        ws.write_json(ws.critique_json(ver), critique.model_dump())
        criticals = [i for i in critique.issues if i.severity == "critical"]
        n_crit = len(criticals)
        versions[ver] = (doc, n_crit, critique)
        print(f"  [criteria] v{ver} validator: action={critique.action} "
              f"issues={len(critique.issues)} (critical={n_crit})")

        if not criticals and critique.action in ("approve", "revise"):
            if critique.action == "revise":
                print("  [criteria] only minor issues — treating as approve")
            save_final(ws, doc)
            return doc

        # Unattended run + every remaining critical is an owner decision: the recorded
        # system assumptions (tentative defaults) let work proceed — that is exactly what
        # ScopeQuestion.tentative_default exists for. The questions stay open in the
        # ledger for the owner; only quality faults hard-block an unattended run.
        quality_criticals = [i for i in criticals if i.category != "scope_decision"]
        if rnd > 1 and not quality_criticals and hitl.mode == "off":
            pending = [i.issue_code for i in criticals]
            print(f"  [criteria] finalizing UNATTENDED with {len(pending)} scope "
                  f"assumption(s) pending owner review: {pending}")
            save_final(ws, doc)
            return doc

        if rnd == AC.CRITERIA_MAX_ITERS:
            break

        # Convergence guard: a round that resolves NO open ledger critical is churn,
        # not progress — burning the remaining budget on it never converges (관찰: 8→7→6→6→7).
        open_now = {issue_code_for(i) for i in criticals}
        if prev_open is not None and not (prev_open - open_now):
            no_progress += 1
            if no_progress >= AC.CRITERIA_NO_PROGRESS_LIMIT:
                stop_reason = (f"no ledger critical resolved for {no_progress} "
                               "consecutive rounds")
                print(f"  [criteria] early stop: {stop_reason}")
                break
        else:
            no_progress = 0
        prev_open = open_now

        # ---- routing by issue class ----
        # scope decisions belong to the owner; rewriting cannot settle them
        scope_issues = [i for i in criticals if i.category == "scope_decision"]
        if scope_issues or (critique.action == "ask_human" and critique.human_questions):
            questions = critique.human_questions or [HITLQuestion(
                id=i.issue_code, question=f"{i.problem} 어떻게 처리할까요? ({i.suggestion})",
                why_needed=i.problem, options=[]) for i in scope_issues]
            # Stable-identity guard: a validator re-flagging the same boundary in new
            # words must not re-ask a boundary the owner already decided this run.
            from src.agentic.judge import _prior_rulings, settle_against_prior
            fresh, settled = settle_against_prior(llm, questions, _prior_rulings(ws), usage)
            for q, ruling in settled:
                entry = {"stage": hitl.stage, "id": q.id, "question": q.question,
                         "answer": ruling.get("answer", ""), "answered_by": "human_prior",
                         "settled_from": ruling.get("question", "")}
                ws.append_jsonl(ws.human_qa_jsonl, entry)
                human_qa_all.append({"id": q.id, "question": q.question,
                                     "answer": ruling.get("answer", ""),
                                     "answered_by": "human_prior"})
            if settled:
                print(f"  [criteria] {len(settled)} validator boundary(s) already decided "
                      f"-> reapplied prior ruling")
            human_qa_all += hitl.ask(fresh, context=f"기준서 v{ver} 검증 중 범위 결정")
        if critique.action == "collect_more" and critique.followup_queries:
            R.collect_more(ws, llm, client, critique.followup_queries,
                           scope.canonical_name_en, usage)
            evidence_summary = R.notes_summary_by_type(ws)
            allowed_refs = allowed_source_references(ws, digest)

        # ---- issue-specific patch first; whole-document redraft only when there is
        # nothing to patch (fresh human answers / new evidence) or patching fails ----
        if criticals:
            try:
                doc, touched, unresolvable = patch_criteria(
                    ws, llm, scope, digest, axes, doc, criticals, usage,
                    version=ver + 1, human_qa=human_qa_all or None)
                last_was_patch = True
                if unresolvable:
                    print(f"  [criteria] patch reviser left unresolved: {unresolvable}")
            except PatchApplyError as err:
                print(f"  [criteria] patch failed ({err}) — full redraft fallback")
                doc = draft_criteria(ws, llm, scope, digest, axes, evidence_summary, usage,
                                     version=ver + 1, prior=doc, critique=critique,
                                     human_qa=human_qa_all or None)
                touched = set()
                last_was_patch = False
        else:
            doc = draft_criteria(ws, llm, scope, digest, axes, evidence_summary, usage,
                                 version=ver + 1, prior=doc, critique=critique,
                                 human_qa=human_qa_all or None)
            touched = set()
            last_was_patch = False
        ver += 1

    # Budget exhausted or non-convergent: a criteria document with material faults is
    # not a valid output. Persist an actionable report and stop instead of blessing it.
    best_v_checked = min(versions, key=lambda v: (versions[v][1], -v))
    checked_doc, checked_n, checked_critique = versions[best_v_checked]
    checked_criticals = [i for i in checked_critique.issues if i.severity == "critical"]
    human_pending = [i for i in checked_criticals if i.category == "scope_decision"]
    quality = [i for i in checked_criticals if i.category != "scope_decision"]
    unresolved_action = checked_critique.action in ("ask_human", "collect_more")
    status = ("approved_without_more_revisions" if not (checked_n or unresolved_action)
              else "blocked_pending_human" if human_pending and not quality
              else "blocked")
    blocked_report = {
        "status": status,
        "reason": stop_reason,
        "best_version": best_v_checked,
        "critical_counts": {str(v): versions[v][1] for v in versions},
        # 미결 소유자 결정(human_pending)과 품질 결함(quality)은 다른 처방을 가진다
        "quality_critical_issues": [i.model_dump() for i in quality],
        "human_pending_issues": [i.model_dump() for i in human_pending],
        "critical_issues": [i.model_dump() for i in checked_criticals],
        "unresolved_action": checked_critique.action if unresolved_action else None,
        "issue_ledger": str(ws.criteria_issue_ledger_json),
    }
    if checked_n or unresolved_action:
        ws.write_json(ws.criteria_blocked_json, blocked_report)
        reported_n = max(1, checked_n)
        print(f"  [criteria] BLOCKED ({status}): v{best_v_checked} has "
              f"{len(quality)} quality critical(s) + {len(human_pending)} pending owner "
              f"decision(s); final criteria were not written.")
        raise CriteriaValidationBlocked(ws.criteria_blocked_json, reported_n)
    save_final(ws, checked_doc)
    return checked_doc
