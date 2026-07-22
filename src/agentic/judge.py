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

AUDIT_KEYS = ("record_id", "patent_id", "domain", "stance", "included",
              "relevance_score", "decision_confidence", "score",
              "matched_criteria", "violated_exclusions", "rationale",
              "second_pass", "final_score", "candidate_type", "decision_reason",
              "judge_pass")
SLIM_KEYS = ("record_id", "patent_id", "domain", "title", "abstract",
             "included", "relevance_score", "decision_confidence", "final_score",
             "candidate_type", "stance")


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
    if doc.technology_axes:
        lines += ["", "TECHNOLOGY AXES (anchored inventory):"]
        lines += [f"  [{a.status.upper()}] {a.id}. {a.name}: {a.description}"
                  for a in doc.technology_axes]
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
    "- relevance_score: a CONTINUOUS ranking value (0-1) for degree of domain relevance, "
    "calibrated to "
    "evidence strength — use the full scale and differentiate between patents, never repeat "
    "one default value. Guide: ~0.95+ explicit mechanism satisfying multiple criteria; "
    "~0.8 one criterion clearly satisfied; ~0.6 task implied but mechanism thin; ~0.45 "
    "genuinely conflicted; ~0.3 domain vocabulary but task unlikely; ~0.15 look-alike with "
    "a clear exclusion; ~0.05 no domain signal at all.\n"
    "- decision_confidence: confidence (0-1) that the stance and cited C/E ids are correct. "
    "This is decision certainty, not domain relevance.\n"
    "- rationale: 1-3 full sentences that explicitly reference the cited ids.\n"
    "Never guess ground-truth labels; judge only the given text. Output JSON only."
)

_JUDGE_SYSTEM += (
    "\nFINAL DECISION CONTRACT:\n"
    "- relevance_score estimates degree of domain relevance for ranking and AUC only. It "
    "must NEVER determine whether a patent is included.\n"
    "- decision_confidence estimates confidence that the stated stance and C/E citations "
    "are correct. Low confidence triggers review; it does not itself exclude the patent.\n"
    "- in_domain is valid only with at least one genuinely satisfied C-id and no applicable "
    "E-id. out_of_domain is valid only with no genuinely satisfied C-id. A C/E conflict, "
    "an in_domain stance without a C-id, or an out_of_domain stance with a C-id must be "
    "reported as boundary pending confirmation.\n"
)

_SECOND_PASS_SYSTEM = (
    "You are the Confirmation agent. A first-pass judgment was borderline or internally "
    "conflicted. Re-read the patent against the criteria document, focusing on the "
    "exclusion criteria and boundary guidance, and commit to final C/E citations and stance. "
    "Remember: exclusion criteria identify look-alikes (vocabulary without the task); they "
    "never veto an inclusion criterion that is genuinely satisfied by a real mechanism. "
    "Return the confirmed C-id list and E-id list as well as stance, relevance_score, and "
    "decision_confidence. Identify the SINGLE decisive criterion id. Score never overrides "
    "the C/E decision rule. Output JSON only."
)


# ----------------------------------------------------------------- process_fn
def _valid_criterion_ids(values: list[str], prefix: str,
                         allowed: set[str] | None) -> list[str]:
    out = []
    for value in values or []:
        value = str(value).strip()
        if value.startswith(prefix) and (not allowed or value in allowed) and value not in out:
            out.append(value)
    return out


def _normalize_decision(stance: str, matched: list[str], excluded: list[str],
                        c_ids: set[str] | None = None,
                        e_ids: set[str] | None = None) -> tuple[str, bool, list[str], list[str], str]:
    """Make inclusion a deterministic stance+C/E invariant, never a score cutoff."""
    matched = _valid_criterion_ids(matched, "C", c_ids)
    excluded = _valid_criterion_ids(excluded, "E", e_ids)
    if stance == "in_domain" and matched and not excluded:
        return stance, True, matched, excluded, "in_domain with satisfied C and no E conflict"
    if stance == "out_of_domain" and not matched:
        return stance, False, matched, excluded, "out_of_domain with no satisfied C"
    if stance == "abstain" and not matched and not excluded:
        return stance, False, matched, excluded, "insufficient text to apply C/E criteria"
    return ("boundary", False, matched, excluded,
            "C/E citations and stance are unresolved or internally inconsistent")


def _candidate_type(stance: str, relevance_score: float,
                    violated_exclusions: list[str] | None = None) -> str:
    """Subtype is descriptive only; inclusion is determined before this function."""
    if stance == "in_domain":
        return "positive"
    if stance == "out_of_domain":
        # E citations plus residual relevance indicate a look-alike/hard negative.
        return ("hard_negative" if violated_exclusions and relevance_score > 0.25
                else "easy_negative")
    return stance


def judge_patent(state: dict, fast: StructuredLLM, strong: StructuredLLM,
                 usage: Usage) -> dict:
    """Judge, confirm when needed, then enforce the score-independent C/E contract."""
    block = state["rubric"]["block"]
    user = (f"{block}\n\nPATENT\nTitle: {state['title']}\n"
            f"Abstract: {state['abstract']}")
    out, pt, ct = fast.parse(_JUDGE_SYSTEM, user, JudgmentOut)
    usage.add(pt, ct)
    res = dict(state)
    res.update(out.model_dump())
    res["judge_pass"] = state.get("judge_pass", 1)

    c_ids = set(state["rubric"].get("c_ids") or [])
    e_ids = set(state["rubric"].get("e_ids") or [])
    normalized_first = _normalize_decision(
        out.stance, out.matched_criteria, out.violated_exclusions, c_ids, e_ids)
    first_inconsistent = normalized_first[0] != out.stance
    second_pass_on = state["rubric"].get("second_pass", True)
    needs_confirmation = (
        out.stance in ("boundary", "abstain")
        or out.decision_confidence <= AC.DECISION_CONFIDENCE_AUDIT_MAX
        or first_inconsistent
    )

    if second_pass_on and needs_confirmation:
        sp_user = (user + "\n\nFIRST-PASS JUDGMENT:\n"
                   + json.dumps(out.model_dump(), ensure_ascii=False))
        if first_inconsistent:
            sp_user += ("\nThe first pass violates the stance+C/E contract. Decide whether "
                        "the C evidence is genuine, whether an E applies, and return corrected "
                        "citation lists. Do not use score to break the conflict.")
        sp, pt2, ct2 = strong.parse(_SECOND_PASS_SYSTEM, sp_user, SecondPassOut)
        usage.add(pt2, ct2)
        res["second_pass"] = sp.model_dump()
        res["stance"] = sp.confirmed_stance
        res["matched_criteria"] = sp.confirmed_matched_criteria
        res["violated_exclusions"] = sp.confirmed_violated_exclusions
        res["relevance_score"] = sp.confirmed_relevance_score
        res["decision_confidence"] = sp.confirmed_decision_confidence
        res["rationale"] = sp.rationale
    else:
        res["second_pass"] = None

    (res["stance"], res["included"], res["matched_criteria"],
     res["violated_exclusions"], res["decision_reason"]) = _normalize_decision(
        res["stance"], res["matched_criteria"], res["violated_exclusions"], c_ids, e_ids)
    res["relevance_score"] = float(res["relevance_score"])
    res["decision_confidence"] = float(res["decision_confidence"])
    # Backward-compatible ranking aliases. Neither is consulted for inclusion.
    res["score"] = res["relevance_score"]
    res["final_score"] = res["relevance_score"]
    res["candidate_type"] = _candidate_type(
        res["stance"], res["relevance_score"], res["violated_exclusions"])
    res.pop("rubric", None)
    return res


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
    rubric = {"block": criteria_prompt_block(doc, amendments), "second_pass": second_pass,
              "c_ids": [c.id for c in doc.domain_criteria],
              "e_ids": [e.id for e in doc.exclusion_criteria]}
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


def write_ranked_csv(results: list[dict], path) -> str:
    """Agentic-only export: decision columns plus backward-compatible score."""
    import csv
    items = sorted(
        results,
        key=lambda r: r.get("relevance_score", r.get("final_score", 0.0)),
        reverse=True,
    )
    rows = []
    for rank, row in enumerate(items, 1):
        relevance = row.get("relevance_score", row.get("final_score"))
        included = row.get("included", row.get("candidate_type") == "positive")
        rows.append({
            "rank": rank, "relevance_score": relevance,
            "decision_confidence": row.get("decision_confidence"),
            "included": bool(included), "score": relevance,
            "record_id": row["record_id"], "patent_id": row.get("patent_id", ""),
            "domain": row.get("domain", ""), "title": row.get("title", ""),
            "abstract": row.get("abstract", ""),
            "candidate_type": row.get("candidate_type", ""),
            "source": row.get("source", ""),
        })
    fields = ["rank", "relevance_score", "decision_confidence", "included", "score",
              "record_id", "patent_id", "domain", "title", "abstract",
              "candidate_type", "source"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    return str(path)


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
    picks = []
    for e in latest.values():
        stance = e.get("stance", "")
        conflict = bool(e.get("matched_criteria")) and bool(e.get("violated_exclusions"))
        confidence = float(e.get("decision_confidence", 0.0))
        invariant_fault = ((stance == "in_domain" and not e.get("matched_criteria"))
                           or (stance == "out_of_domain" and e.get("matched_criteria")))
        if (stance in ("boundary", "abstain")
                or confidence <= AC.DECISION_CONFIDENCE_AUDIT_MAX
                or conflict or invariant_fault):
            picks.append(e)
    picks.sort(key=lambda e: float(e.get("decision_confidence", 0.0)))
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
                    f"JUDGMENT UNDER AUDIT:\n{json.dumps({k: e.get(k) for k in ('stance', 'included', 'relevance_score', 'decision_confidence', 'matched_criteria', 'violated_exclusions', 'rationale')}, ensure_ascii=False)}")
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
    "them with low decision confidence). Find the 1-3 RECURRING SCOPE AMBIGUITIES behind "
    "these hard cases — the "
    "boundaries whose resolution would settle many of them at once. For each, write a "
    "ScopeQuestion the domain owner can answer, with a broad_rule and a narrow_rule (each a "
    "single sentence a judge could apply), 2-3 options, and a tentative_default. Do not "
    "invent ambiguities that these patents do not actually exhibit. Output JSON only."
)


def _uncertain_rows(ws: Workspace, rows_by_id: dict[str, dict]) -> list[dict]:
    out = []
    for e in judgments_from_audit(ws).values():
        confidence = float(e.get("decision_confidence", 0.0))
        if (e.get("stance") in ("boundary", "abstain")
                or confidence <= AC.DECISION_CONFIDENCE_AUDIT_MAX):
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
