"""[6]+[7] Judgment engine: strict criteria-based per-patent judgment + validator loop.

[6] judge_patent (process_fn injected into src/mas/runner.run_pool):
    Node A': judge STRICTLY by the approved sentence-form criteria, citing C/E ids.
    Node B': confirmation pass for borderline scores / boundary / abstain stances.
[7] validate_judgments: an auditor re-examines suspicious judgments; its actions can
    amend the criteria (clarifications), trigger extra research, or ask the human
    (HITL); flagged cases are re-judged under the amended criteria. Re-judged rows
    are APPENDED to the audit JSONL — the last entry per record_id wins.
"""
from __future__ import annotations
import json

import pandas as pd

from src.mas.llm import StructuredLLM, Usage
from src.mas.runner import KeyPool, run_pool
from src.agentic import config as AC
from src.agentic import research as R
from src.agentic.hitl import HITL
from src.agentic.schemas import (BoundaryFeedbackOut, CriteriaDocOut, HITLQuestion,
                                 JudgeAuditOut, JudgmentOut, SecondPassOut)
from src.agentic.search import SearchClient
from src.agentic.workspace import Workspace

AUDIT_KEYS = ("record_id", "patent_id", "domain", "stance", "score",
              "matched_criteria", "violated_exclusions", "rationale",
              "second_pass", "final_score", "candidate_type", "judge_pass")
SLIM_KEYS = ("record_id", "patent_id", "domain", "title", "abstract",
             "final_score", "candidate_type", "stance")


# ----------------------------------------------------------------- prompt
_LANDSCAPING_JUDGE_CLAUSE = (
    "\nThis is a PATENT LANDSCAPING judgment, which prizes RECALL. Count the patent as "
    "in_domain if it implements, improves, provides a domain-specific enabling component/"
    "method/material, OR is a specific application of the domain technology — the invention "
    "need NOT perform the full canonical end-task. Rule out_of_domain only when the invention "
    "is a genuine look-alike (domain vocabulary used for a different field) or is generic "
    "with no domain-specific contribution. When a patent is domain-specific but you are "
    "unsure it performs the full end-task, prefer in_domain (score ~0.6-0.7).\n"
)


def criteria_prompt_block(doc: CriteriaDocOut, amendments: list[str] | None = None) -> str:
    lines = [f"DOMAIN: {doc.domain_name}",
             f"DEFINITION: {doc.domain_definition}",
             f"SCOPE OF ANALYSIS: {doc.scope_statement}"]
    if doc.scope_decisions:
        lines += ["", "SCOPE DECISIONS (binding per-cluster rulings; CONDITIONAL = apply the "
                      "stated decisive test to the individual patent):"]
        lines += [f"  [{s.verdict.upper()}] {s.topic}: {s.rationale}" for s in doc.scope_decisions]
    lines += ["", "INCLUSION CRITERIA (a patent is domain-valid when it satisfies at least one):"]
    lines += [f"  {c.id}. {c.statement}" for c in doc.domain_criteria]
    lines += ["", "EXCLUSION CRITERIA (a patent is NOT domain-valid when one applies):"]
    lines += [f"  {e.id}. {e.statement}" for e in doc.exclusion_criteria]
    lines += ["", "BOUNDARY GUIDANCE:"]
    lines += [f"  - {g}" for g in doc.boundary_guidance]
    if amendments:
        lines += ["", "BINDING AMENDMENTS (added after validation — these override the above on conflict):"]
        lines += [f"  - {a}" for a in amendments]
    if AC.LANDSCAPING_INCLUSIVE:
        lines += ["", _LANDSCAPING_JUDGE_CLAUSE]
    return "\n".join(lines)


_JUDGE_SYSTEM = (
    "You are the Judgment agent of a patent-landscaping system. Judge whether the patent "
    "below is DOMAIN-VALID, STRICTLY and ONLY by the official criteria document given. "
    "Do not use any standard other than the document.\n"
    "First identify, from the text alone, what the invention is FOR (its own purpose/"
    "application). A domain mechanism or material employed for a DIFFERENT purpose does "
    "not satisfy an inclusion criterion unless the criterion explicitly covers that use; "
    "conversely, an enabling step whose purpose IS the domain's defining task satisfies "
    "the criterion even if the vocabulary differs.\n"
    "- matched_criteria: ids (C..) of every inclusion criterion the patent clearly satisfies, "
    "based on explicit title/abstract evidence.\n"
    "- violated_exclusions: ids (E..) of every exclusion criterion that applies.\n"
    "CONFLICT RULE: exclusion criteria identify LOOK-ALIKES — patents that use the domain's "
    "vocabulary or components WITHOUT performing a defining task. They are NOT a veto. If "
    "the invention genuinely satisfies an inclusion criterion (real mechanism, not a mere "
    "mention), it is in_domain even when it ALSO produces, converts, or uses the stored/"
    "processed subject for an application; cite the C-ids and leave violated_exclusions "
    "empty. Cite an E-id only when NO inclusion criterion is genuinely satisfied.\n"
    "- stance: in_domain | out_of_domain | boundary (criteria conflict or evidence unclear) "
    "| abstain (text too thin to judge).\n"
    "- score: a CONTINUOUS probability (0-1) that the patent is domain-valid, calibrated to "
    "evidence strength — use the full scale and differentiate between patents, never repeat "
    "one default value. Guide: ~0.95+ explicit mechanism satisfying multiple criteria; "
    "~0.8 one criterion clearly satisfied; ~0.6 task implied but mechanism thin; ~0.45 "
    "genuinely conflicted; ~0.3 domain vocabulary but task unlikely; ~0.15 look-alike with "
    "a clear exclusion; ~0.05 no domain signal at all.\n"
    "- rationale: 1-3 full sentences that explicitly reference the cited ids.\n"
    "Never guess ground-truth labels; judge only the given text. Output JSON only."
)

_SECOND_PASS_SYSTEM = (
    "You are the Confirmation agent. A first-pass judgment was borderline or internally "
    "conflicted. Re-read the patent against the criteria document, focusing on the "
    "exclusion criteria and boundary guidance, and commit to a final stance and score. "
    "Remember: exclusion criteria identify look-alikes (vocabulary without the task); they "
    "never veto an inclusion criterion that is genuinely satisfied by a real mechanism. "
    "Identify the SINGLE decisive criterion id. Output JSON only."
)


# ----------------------------------------------------------------- process_fn
def judge_patent(state: dict, fast: StructuredLLM, strong: StructuredLLM,
                 usage: Usage) -> dict:
    """process_fn for run_pool. state['rubric'] = {'block': <criteria text>}."""
    block = state["rubric"]["block"]
    user = (f"{block}\n\n"
            f"PATENT\nTitle: {state['title']}\nAbstract: {state['abstract']}")
    out, pt, ct = fast.parse(_JUDGE_SYSTEM, user, JudgmentOut)
    usage.add(pt, ct)
    res = dict(state)
    res.update(out.model_dump())
    res["judge_pass"] = state.get("judge_pass", 1)

    lo, hi = AC.SECOND_PASS_BAND
    second_pass_on = state["rubric"].get("second_pass", True)
    # C/E conflict (matched inclusion yet excluded) is logically unstable -> always arbitrate
    conflict = bool(out.matched_criteria) and (bool(out.violated_exclusions)
                                               or out.stance == "out_of_domain")
    if second_pass_on and (out.stance in ("boundary", "abstain")
                           or lo <= out.score <= hi or conflict):
        sp_user = user
        if conflict:
            sp_user += ("\n\nFIRST-PASS CONFLICT: the first judgment cited satisfied "
                        f"inclusion criteria {out.matched_criteria} yet ruled the patent out "
                        f"({out.violated_exclusions}). Apply the conflict rule: exclusions "
                        "never veto a genuinely satisfied inclusion criterion — decide "
                        "whether the inclusion evidence is real or vocabulary-only.")
        sp, pt2, ct2 = strong.parse(_SECOND_PASS_SYSTEM, sp_user, SecondPassOut)
        usage.add(pt2, ct2)
        res["second_pass"] = sp.model_dump()
        res["stance"] = sp.confirmed_stance
        res["score"] = sp.confirmed_score
    else:
        res["second_pass"] = None

    res["final_score"] = float(res["score"])
    res["candidate_type"] = _candidate_type(res["stance"], res["final_score"])
    res.pop("rubric", None)
    return res


def _candidate_type(stance: str, score: float) -> str:
    if stance == "in_domain":
        return "positive"
    if stance == "out_of_domain":
        return "easy_negative" if score <= 0.25 else "hard_negative"
    return stance  # boundary | abstain


# ----------------------------------------------------------------- driving
def mock_pool(n: int = 3) -> KeyPool:
    from src.agentic.mockllm import MockAgentLLM
    pool = KeyPool.__new__(KeyPool)
    m = MockAgentLLM()
    pool.clients = [(m, m) for _ in range(n)]
    pool.n = n
    from src.mas.llm import Usage as U
    pool.per_key_usage = [U() for _ in range(n)]
    return pool


def judge_rows(ws: Workspace, doc: CriteriaDocOut, rows: list[dict], pool: KeyPool,
               workers: int = 40, append: bool = False,
               amendments: list[str] | None = None, judge_pass: int = 1,
               second_pass: bool = True) -> dict:
    rubric = {"block": criteria_prompt_block(doc, amendments), "second_pass": second_pass}
    for r in rows:
        r["judge_pass"] = judge_pass
    return run_pool(rows, rubric, pool, workers=workers,
                    audit_path=ws.judge_audit_jsonl, append=append,
                    process_fn=judge_patent, audit_keys=AUDIT_KEYS, slim_keys=SLIM_KEYS)


def judgments_from_audit(ws: Workspace) -> dict[str, dict]:
    """Latest judgment per record_id (re-judged rows override pass-1 rows)."""
    latest: dict[str, dict] = {}
    for entry in ws.read_jsonl(ws.judge_audit_jsonl):
        latest[entry["record_id"]] = entry
    return latest


# ----------------------------------------------------------------- [7] validator
_AUDIT_SYSTEM = (
    "You are the Judgment Validator of a patent-landscaping system. Audit ONE judgment: "
    "did the Judgment agent apply the criteria document STRICTLY and cite the right ids? "
    "Typical faults: an exclusion criterion obviously applies but was not cited; a cited "
    "criterion's condition is not actually evidenced by the text; a boundary case ignored "
    "the boundary guidance.\n"
    "Decide ONE action:\n"
    "- confirm: the judgment stands.\n"
    "- re_judge: the judgment is faulty — explain the fault in `problem`; if a recurring "
    "ambiguity in the criteria caused it, add a clarifying full-sentence rule to "
    "criteria_amendments.\n"
    "- collect_more: external domain facts are needed to decide (propose followup_queries).\n"
    "- ask_human: only the human owner can settle the scope question (write human_questions).\n"
    "Output JSON only."
)


def _suspicious(latest: dict[str, dict]) -> list[dict]:
    lo, hi = AC.SECOND_PASS_BAND
    picks = []
    for e in latest.values():
        s = float(e.get("final_score", 0.0))
        stance = e.get("stance", "")
        conflict = bool(e.get("matched_criteria")) and bool(e.get("violated_exclusions"))
        if stance in ("boundary", "abstain") or lo <= s <= hi or conflict:
            picks.append(e)
    picks.sort(key=lambda e: abs(float(e.get("final_score", 0.5)) - 0.5))
    return picks[:AC.JUDGE_AUDIT_SAMPLE]


def validate_judgments(ws: Workspace, doc: CriteriaDocOut, llm: StructuredLLM,
                       client: SearchClient | None, hitl: HITL, pool: KeyPool,
                       rows_by_id: dict[str, dict], canonical_name: str,
                       usage: Usage, workers: int = 40) -> list[str]:
    """Audit suspicious judgments; amend criteria / collect / ask human; re-judge.
    Returns the accumulated amendment sentences (also logged to validation.jsonl)."""
    amendments: list[str] = []
    block = criteria_prompt_block(doc)
    audited: set[str] = set()          # never re-audit a case the auditor already ruled on

    for it in range(1, AC.JUDGE_VALIDATE_MAX_ITERS + 1):
        latest = judgments_from_audit(ws)
        picks = [e for e in _suspicious(latest) if e["record_id"] not in audited]
        if not picks:
            print(f"  [judge-val] round {it}: no suspicious judgments — done")
            break
        print(f"  [judge-val] round {it}: auditing {len(picks)} suspicious judgments")

        re_ids: list[str] = []
        questions = []
        followups = []
        for e in picks:
            row = rows_by_id.get(e["record_id"])
            if row is None:
                continue
            audited.add(e["record_id"])
            user = (f"{block}\n\nPATENT\nTitle: {row['title']}\nAbstract: {row['abstract']}\n\n"
                    f"JUDGMENT UNDER AUDIT:\n{json.dumps({k: e.get(k) for k in ('stance', 'score', 'matched_criteria', 'violated_exclusions', 'rationale')}, ensure_ascii=False)}")
            audit, pt, ct = llm.parse(_AUDIT_SYSTEM, user, JudgeAuditOut)
            usage.add(pt, ct)
            ws.append_jsonl(ws.judge_validation_jsonl,
                            {"round": it, "record_id": e["record_id"],
                             **audit.model_dump()})
            if audit.action == "re_judge":
                re_ids.append(e["record_id"])
                amendments += [a for a in audit.criteria_amendments if a not in amendments]
            elif audit.action == "collect_more":
                followups += audit.followup_queries
            elif audit.action == "ask_human":
                questions += audit.human_questions

        if questions:
            for qa in hitl.ask(questions, context=f"판정 감사 round {it}"):
                amendments.append(f"Human decision — Q: {qa['question']} A: {qa['answer']}")
        if followups and client is not None:
            R.collect_more(ws, llm, client, followups, canonical_name, usage)
            # fresh evidence informs future amendments only via the auditor's next round

        targets = set(re_ids)
        if amendments:
            # amended rules apply to every still-uncertain case, not just flagged ones
            targets |= {e["record_id"] for e in picks}
        if not targets:
            print(f"  [judge-val] round {it}: all audited judgments confirmed")
            break

        rows = [dict(rows_by_id[rid]) for rid in targets if rid in rows_by_id]
        print(f"  [judge-val] round {it}: re-judging {len(rows)} cases "
              f"({len(amendments)} amendment(s))")
        judge_rows(ws, doc, rows, pool, workers=workers, append=True,
                   amendments=amendments, judge_pass=it + 1)

    if amendments:
        ws.append_jsonl(ws.judge_validation_jsonl,
                        {"final_amendments": amendments})
    return amendments


# ----------------------------------------------------------------- [3] closed loop
_FEEDBACK_SYSTEM = (
    "You are the Boundary-Discovery agent. Below are patents that the judge could NOT "
    "confidently place for the domain '{domain}' (it marked them boundary/abstain or scored "
    "them near 0.5). Find the 1-3 RECURRING SCOPE AMBIGUITIES behind these hard cases — the "
    "boundaries whose resolution would settle many of them at once. For each, write a "
    "ScopeQuestion the domain owner can answer, with a broad_rule and a narrow_rule (each a "
    "single sentence a judge could apply), 2-3 options, and a tentative_default. Do not "
    "invent ambiguities that these patents do not actually exhibit. Output JSON only."
)


def _uncertain_rows(ws: Workspace, rows_by_id: dict[str, dict]) -> list[dict]:
    lo, hi = AC.SECOND_PASS_BAND
    out = []
    for e in judgments_from_audit(ws).values():
        s = float(e.get("final_score", 0.5))
        if e.get("stance") in ("boundary", "abstain") or lo <= s <= hi:
            r = rows_by_id.get(e["record_id"])
            if r:
                out.append(r)
    return out


def boundary_feedback_round(ws: Workspace, doc: CriteriaDocOut, llm: StructuredLLM,
                            hitl: HITL, judge_pool: KeyPool, probe_pool: KeyPool,
                            pool_df: pd.DataFrame, rows_by_id: dict[str, dict],
                            canonical_name: str, usage: Usage,
                            workers: int = 40) -> list[dict]:
    """Cluster the judge's uncertain cases -> propose scope questions -> probe-measure ->
    ask human -> re-judge the uncertain set under the answers. Returns the human Q&A."""
    from src.agentic.boundary_probe import measured_questions, probe_boundaries

    uncertain = _uncertain_rows(ws, rows_by_id)
    if len(uncertain) < 5:
        print(f"  [boundary-loop] only {len(uncertain)} uncertain cases — skipping")
        return []
    sample = uncertain[:AC.JUDGE_AUDIT_SAMPLE]
    listing = "\n".join(f"- {r['title']} :: {str(r['abstract'])[:200]}" for r in sample)
    out, pt, ct = llm.parse(_FEEDBACK_SYSTEM.format(domain=canonical_name),
                            f"Hard cases ({len(sample)}):\n{listing}", BoundaryFeedbackOut)
    usage.add(pt, ct)
    if not out.questions:
        print("  [boundary-loop] no recurring boundary found")
        return []

    ranked = probe_boundaries(out.questions, pool_df, probe_pool, canonical_name,
                              ws.boundary_probe_jsonl)
    kept = measured_questions(ranked)
    print(f"  [boundary-loop] {len(out.questions)} discovered -> {len(kept)} move real patents")
    if not kept:
        return []

    # namespace the ids: answers.json is shared with the criteria stage, so a bare
    # "Q1" here would silently reuse the criteria answer for a DIFFERENT question
    hqs = [HITLQuestion(id=f"BL-{q.id}", question=f"{q.question} (현재 가정: {q.tentative_default})",
                        why_needed=q.why_it_matters, options=q.options) for q in kept]
    qa = hitl.ask(hqs, context=f"{canonical_name} 판정 후 미해결 경계")
    amendments = [f"Scope decision (post-judgment) — {a['question']} => {a['answer']}" for a in qa]
    rows = [dict(r) for r in uncertain]
    print(f"  [boundary-loop] re-judging {len(rows)} uncertain cases under {len(amendments)} answer(s)")
    judge_rows(ws, doc, rows, judge_pool, workers=workers, append=True,
               amendments=amendments, judge_pass=9)
    ws.append_jsonl(ws.judge_validation_jsonl, {"boundary_loop_amendments": amendments})
    return qa
