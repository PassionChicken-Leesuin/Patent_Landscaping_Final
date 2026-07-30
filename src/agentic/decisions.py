"""[4c] Decision cards: frame the hard boundary calls for the human owner.

The system form of the "결정 ①②③" the assistant put to the human (4족 / 물류학습 /
산업용 회색지대): each is a stake with the include and exclude arguments, example patents
for each side, a MEASURED impact (how many pool patents flip — reused from boundary_probe,
not re-derived), and a recommendation. The human answers once; the answers are binding scope
context for the criteria draft. broad_rule/narrow_rule keep every card machine-testable.
"""
from __future__ import annotations

import pandas as pd

from src.agentic.boundary_probe import probe_boundaries
from src.agentic.hitl import HITL, question_id
from src.agentic.schemas import (CaseMapCategoryOut, CaseMapSummaryOut, CardedHITLQuestion,
                                 DecisionEnrichOut, DecisionQuestion, DecisionQuestionsOut,
                                 ScopeQuestion, ScopeQuestionsOut)
from src.agentic.workspace import Workspace
from src.mas.llm import StructuredLLM, Usage
from src.mas.runner import KeyPool

_SYSTEM = """
You are the Decision-Framing agent of a patent-landscaping system. From the case-mapping
results — especially the categories with many boundary cases and the cross-cutting insights —
identify the FEW genuine scope decisions that only the domain owner should make (typically 2-4:
a look-alike form to include or not, a component/application that transfers or not, an
industrial-lookalike cluster's dividing line).

For each decision produce:
- stake: what exactly is being decided (one or two sentences).
- include_argument + include_examples: the case FOR inclusion, with 2-3 patent_ids from the
  mapping that exemplify it.
- exclude_argument + exclude_examples: the case AGAINST, with 2-3 patent_ids.
- recommendation: your recommended call with its one-line justification.
- options: the concrete choices (usually ["include ...", "exclude ..."]).
- tentative_default: the option to apply if the human does not answer.
- broad_rule / narrow_rule: one-sentence inclusion rules under the broad vs narrow reading,
  written so a judge can apply them to a single patent (these MEASURE the decision's impact).
Leave impact_flips and impact_sample_n at 0 — they are measured after you output.

LANGUAGE: write stake, include_argument, exclude_argument, recommendation, options, and
tentative_default in KOREAN (자연스러운 한국어) — these are shown to a Korean domain owner.
Keep patent_ids verbatim. broad_rule / narrow_rule may stay in English (judge-facing).
Output JSON only.
"""


def derive_decisions(ws: Workspace, llm: StructuredLLM, cats: list[CaseMapCategoryOut],
                     summary: CaseMapSummaryOut, usage: Usage) -> list[DecisionQuestion]:
    blocks = []
    for c in cats:
        if not c.boundary:
            continue
        ex = "; ".join(f"[{r.patent_id}] {r.gist} — {r.basis} (rec: {r.recommendation})"
                       for r in c.boundary[:6])
        blocks.append(f"### {c.category} ({len(c.boundary)} boundary)\n{ex}")
    ins = "\n".join(f"- {i.title}: {i.detail} (ev: {', '.join(i.evidence_ids[:4])})"
                    for i in summary.insights)
    user = ("INSIGHTS:\n" + ins + "\n\nBOUNDARY-HEAVY CATEGORIES:\n" + "\n\n".join(blocks))
    out, pt, ct = llm.parse(_SYSTEM, user, DecisionQuestionsOut)
    usage.add(pt, ct)
    # stamp each id = hash of the stake text so it joins to the HITL answer + the UI card
    for d in out.questions:
        d.id = question_id(d.stake)
    return out.questions


def measure_decisions(decisions: list[DecisionQuestion], pool_df: pd.DataFrame,
                      probe_pool: KeyPool, domain: str, ws: Workspace) -> list[DecisionQuestion]:
    """Reuse the boundary probe to fill impact_flips (measured, not guessed)."""
    if not decisions:
        return decisions
    shims = [ScopeQuestion(id=d.id, question=d.stake, why_it_matters="", options=d.options,
                           tentative_default=d.tentative_default, broad_rule=d.broad_rule,
                           narrow_rule=d.narrow_rule) for d in decisions]
    ranked = probe_boundaries(shims, pool_df, probe_pool, domain, ws.boundary_probe_jsonl)
    flips = {q.id: (f, n) for q, f, n in ranked}
    for d in decisions:
        d.impact_flips, d.impact_sample_n = flips.get(d.id, (0, 0))
    ws.write_json(ws.decisions_json, {"decisions": [d.model_dump() for d in decisions]})
    return decisions


def as_hitl_questions(decisions: list[DecisionQuestion]) -> list[CardedHITLQuestion]:
    """Present the rich card through the standard answer channel (batch/interactive).
    The card rides along in the question payload (decisions.json keeps the archival
    copy), so the UI never depends on an id-join to render example patents."""
    out = []
    for d in decisions:
        why = (f"영향: 표본 {d.impact_sample_n}건 중 {d.impact_flips}건 판정이 갈림. "
               f"[포함] {d.include_argument} [제외] {d.exclude_argument} "
               f"[권고] {d.recommendation}")
        # embed the full card so the UI renders the unified decision card (with example
        # patents) directly from the question, independent of the decisions.json id-join
        out.append(CardedHITLQuestion(id=d.id, question=d.stake, why_needed=why,
                                      options=d.options, card=d.model_dump()))
    return out


_ENRICH_SYSTEM = """
You turn a raw scope question raised during criteria drafting into a decision card for the
Korean domain owner — the SAME shape the upfront decisions use. Given the question, its
broad-vs-narrow inclusion rules, and verified boundary example patents, produce (in KOREAN):
- stake: 무엇을 결정하는지 (1-2문장)
- include_argument + include_examples: 포함하자는 논리 + 근거 patent_id 2-3개 (예시 목록에서만)
- exclude_argument + exclude_examples: 제외하자는 논리 + 근거 patent_id 2-3개
- recommendation: 권고안과 한 줄 근거
Cite only patent_ids from the supplied examples; copy them verbatim. Output JSON only.
"""


def _boundary_examples(ws: Workspace) -> list[tuple[str, str]]:
    out = []
    d = ws.casemap_dir
    if d.exists():
        for p in sorted(d.glob("*.json")):
            c = Workspace.read_json(p)
            for r in (c.get("boundary", []) + c.get("confirmed", [])[:3]
                      + c.get("false_positive", [])[:3]):
                out.append((str(r.get("patent_id", "")), str(r.get("gist", ""))))
    return out[:60]


def _example_block(ws: Workspace) -> str:
    ex = _boundary_examples(ws)
    return "\n".join(f"[{pid}] {gist}" for pid, gist in ex if pid) or "(none)"


def asked_text(q: ScopeQuestion) -> str:
    """The exact wording a scope question is asked in — the one place that decides it,
    so card ids and HITL question ids cannot drift apart."""
    return f"{q.question} (현재 가정: {q.tentative_default})"


def _build_card(ws: Workspace, llm: StructuredLLM, q: ScopeQuestion, flip: int, n: int,
                usage: Usage, ex_block: str) -> DecisionQuestion | None:
    """One scope question -> one decision card (stake / 포함·제외 논리 + 예시특허 / 권고)."""
    user = (f"QUESTION: {q.question}\nBROAD RULE (include): {q.broad_rule}\n"
            f"NARROW RULE (include): {q.narrow_rule}\n\nBOUNDARY EXAMPLE PATENTS:\n{ex_block}")
    try:
        out, pt, ct = llm.parse(_ENRICH_SYSTEM, user, DecisionEnrichOut)
        usage.add(pt, ct)
    except Exception:
        return None
    return DecisionQuestion(
        id=question_id(asked_text(q)), stake=out.stake,
        include_argument=out.include_argument, include_examples=out.include_examples,
        exclude_argument=out.exclude_argument, exclude_examples=out.exclude_examples,
        impact_flips=flip, impact_sample_n=n, recommendation=out.recommendation,
        options=q.options, tentative_default=q.tentative_default,
        broad_rule=q.broad_rule, narrow_rule=q.narrow_rule)


def _archive_cards(ws: Workspace, cards: list[DecisionQuestion]) -> None:
    """Append to the audit record of cards shown to the owner.

    Deliberately NOT decisions.json: that file is [4c]'s ask-list, reloaded verbatim on
    every resume, so a criteria-stage card written there comes back as an upfront
    decision and the owner is asked the same boundary twice under two different ids.
    """
    for c in cards:
        ws.append_jsonl(ws.decision_cards_jsonl, c.model_dump())


def carded_questions(ws: Workspace, llm: StructuredLLM,
                     ranked: list[tuple[ScopeQuestion, int, int]], usage: Usage,
                     id_prefix: str = "") -> list[CardedHITLQuestion]:
    """Measured scope questions -> HITL questions that CARRY their decision card.

    Every human scope decision goes through this, so the owner always sees the same
    card (쟁점 / 포함·제외 논리 + 예시 특허 / 영향 / 권고) instead of a bare sentence.
    A question whose card cannot be built still goes out — unanswered is worse than
    uncarded — it just falls back to the plain rendering."""
    if not ranked:
        return []
    ex_block = _example_block(ws)
    out, cards = [], []
    for q, flip, n in ranked:
        card = _build_card(ws, llm, q, flip, n, usage, ex_block)
        if card:
            cards.append(card)
        out.append(CardedHITLQuestion(
            id=f"{id_prefix}{q.id}", question=asked_text(q),
            why_needed=q.why_it_matters, options=q.options,
            card=card.model_dump() if card else None))
    _archive_cards(ws, cards)
    return out


_AS_BOUNDARY_SYSTEM = """
The criteria validator raised scope questions that only the domain owner can settle.
Restate each one as ONE testable scope boundary, preserving the order given. Per question:
- question: 도메인 소유자에게 묻는 결정 질문 (KOREAN, 한 문장, 무엇을 포함/제외할지 묻는 형태)
- why_it_matters: 이 결정이 판정 결과에 어떤 차이를 만드는지 (KOREAN)
- options: 구체적 선택지 (예: ["포함", "제외"])
- tentative_default: 답이 없을 때 유지할 현재 가정 (KOREAN)
- broad_rule / narrow_rule: ENGLISH, one sentence each, stating what an individual patent
  must claim to be INCLUDED under the broad and the narrow reading. They must be applicable
  to a single patent's title+abstract with no further context — they are executed against a
  pool sample to measure how many judgments actually flip.
Output JSON only.
"""


def cards_for_raw_questions(ws: Workspace, llm: StructuredLLM,
                            raw: list[tuple[str, str]], doc, pool_df, probe_pool,
                            domain: str, usage: Usage) -> list[CardedHITLQuestion]:
    """Validator-raised scope questions -> measured, carded HITL questions.

    A boundary the validator blocks on is the same kind of decision the criteria author
    raises, so it earns the same treatment: restate it as broad/narrow rules, MEASURE it
    on a pool sample, and render it as a decision card. The measurement threshold is
    dropped to 0 here — unlike candidate boundaries, these questions are not being
    selected, they are already known to need an answer.

    Returns [] on any failure so the caller can fall back to plain questions."""
    if not raw:
        return []
    try:
        ctx = "\n".join(f"- {q}\n  (근거/제안: {why})" for q, why in raw)
        user = (f"DOMAIN: {getattr(doc, 'domain_name', domain)}\n"
                f"DEFINITION: {getattr(doc, 'domain_definition', '')}\n\n"
                f"SCOPE QUESTIONS RAISED:\n{ctx}")
        out, pt, ct = llm.parse(_AS_BOUNDARY_SYSTEM, user, ScopeQuestionsOut)
        usage.add(pt, ct)
        qs = out.questions[:len(raw)]
        if not qs:
            return []
        ranked = [(q, 0, 0) for q in qs]
        if pool_df is not None and probe_pool is not None and len(pool_df):
            measured = probe_boundaries(qs, pool_df, probe_pool, domain,
                                        ws.boundary_probe_jsonl,
                                        min_flip_rate=0.0, max_questions=len(qs))
            if measured:
                ranked = measured
        return carded_questions(ws, llm, ranked, usage)
    except Exception as e:                     # never block the loop on card generation
        print(f"  !! [decisions] 검증기 범위질문 카드 생성 실패 ({e}) — 기본 질문으로 진행")
        return []


def run_decisions(ws: Workspace, llm: StructuredLLM, cats: list[CaseMapCategoryOut],
                  summary: CaseMapSummaryOut, pool_df: pd.DataFrame, probe_pool: KeyPool,
                  domain: str, hitl: HITL, usage: Usage) -> list[dict]:
    """Derive -> measure -> ask. Returns the answered decisions (binding scope context)."""
    if ws.decisions_json.exists():
        decisions = [DecisionQuestion(**d)
                     for d in Workspace.read_json(ws.decisions_json)["decisions"]]
    else:
        decisions = derive_decisions(ws, llm, cats, summary, usage)
        decisions = measure_decisions(decisions, pool_df, probe_pool, domain, ws)
    if not decisions:
        return []
    print(f"  [decisions] {len(decisions)} scope decision(s) framed for the owner")
    return hitl.ask(as_hitl_questions(decisions), context="사례 매핑에서 도출된 범위 결정")
