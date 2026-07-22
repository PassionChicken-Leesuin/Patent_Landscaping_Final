"""Human-in-the-loop channel used by both validator loops.

Modes:
  interactive — ask on the console (input()); Q&A appended to human_qa.jsonl
  batch       — questions written to questions_pending.json and PendingHumanInput is
                raised; on the next run, answers are read from answers.json
                (format: {"<question_id>": "<answer>", ...}) and the stage resumes
  off         — no human available: a conservative auto-answer is recorded so the
                validator resolves on its own (used for unattended eval runs)

QUESTION IDENTITY (P2): LLM-assigned ids (Q1, Q2, ...) restart from Q1 on every
redraft, so batch answers keyed by id were silently re-assigned to DIFFERENT
questions on resume (observed in the 2026-07-19 A2 run: 3 of 6 answers wrong).
Every question id is therefore rewritten here to a hash of its normalized text —
an id can only ever match the exact question it was answered for. A previously
human-answered question is reused only inside the SAME run workspace (for batch
resume or a later stage of that run), labeled answered_by="human_prior".

RUN ISOLATION: HITL decisions are never read from or written to a cross-run
domain profile. Each run starts without user-query/answer memory from prior runs.
"""
from __future__ import annotations
import hashlib
import re
from typing import Literal

from src.agentic.schemas import HITLQuestion
from src.agentic.workspace import Workspace

HITLMode = Literal["interactive", "batch", "off"]


def question_id(text: str) -> str:
    """Globally-unique, drift-proof question id: hash of the normalized text."""
    norm = re.sub(r"\s+", " ", (text or "")).strip().lower()
    return "q" + hashlib.sha1(norm.encode("utf-8")).hexdigest()[:10]


def _uniquify(questions: list[HITLQuestion]) -> list[HITLQuestion]:
    """Rewrite ids to text hashes; drop exact-duplicate questions within the batch."""
    seen, out = set(), []
    for q in questions:
        q = q.model_copy()
        q.id = question_id(q.question)
        if q.id in seen:
            continue
        seen.add(q.id)
        out.append(q)
    return out

_AUTO_ANSWER = ("No human expert is available for this run. Resolve the question yourself: "
                "keep the ruling best supported by the collected evidence; if the evidence "
                "genuinely cannot settle it, KEEP the current ruling unchanged and state "
                "the open question explicitly in the document so a human can revisit it. "
                "Do not broaden or narrow the scope beyond what the evidence supports.")


class PendingHumanInput(Exception):
    """Raised in batch mode when questions await answers in answers.json."""
    def __init__(self, questions: list[HITLQuestion]):
        self.questions = questions
        super().__init__(f"{len(questions)} human question(s) pending — "
                         "fill answers.json and re-run")


class HITL:
    def __init__(self, ws: Workspace, mode: HITLMode = "interactive", stage: str = ""):
        self.ws = ws
        self.mode = mode
        self.stage = stage

    def ask(self, questions: list[HITLQuestion], context: str = "") -> list[dict]:
        """Return [{'id', 'question', 'answer'}, ...] for every question."""
        if not questions:
            return []
        questions = _uniquify(questions)
        # A question already answered in THIS run (identical text, any stage) is
        # resolved from the run-local record — never from another run.
        prior = self._prior_human_answers()
        answered = [self._log(q, prior[q.id], "human_prior")
                    for q in questions if q.id in prior]
        if answered:
            print(f"  [HITL/{self.stage}] {len(answered)}건은 이 실행의 기존 인간 답변 재사용 "
                  f"(run-local human_qa.jsonl 동일 질문)")
        questions = [q for q in questions if q.id not in prior]
        if not questions:
            return answered
        if self.mode == "off":
            return answered + [self._log(q, _AUTO_ANSWER, "auto") for q in questions]
        if self.mode == "batch":
            return answered + self._batch(questions, context)
        return answered + self._interactive(questions, context)

    def _prior_human_answers(self) -> dict[str, str]:
        """question-text-hash -> answer, for every question a human actually
        answered earlier in this run (auto answers are never reused as human
        decisions). No cross-run store is consulted."""
        out: dict[str, str] = {}
        if self.ws.human_qa_jsonl.exists():
            for e in self.ws.read_jsonl(self.ws.human_qa_jsonl):
                if e.get("answered_by") in ("human", "human_batch", "human_prior"):
                    out[question_id(e.get("question", ""))] = str(e.get("answer", ""))
        return out

    # ------------------------------------------------------------- interactive
    def _interactive(self, questions: list[HITLQuestion], context: str) -> list[dict]:
        out = []
        print("\n" + "=" * 60)
        print(f"[HITL/{self.stage}] 시스템이 인간 판단을 요청합니다 ({len(questions)}건)")
        if context:
            print(f"맥락: {context}")
        for q in questions:
            print("-" * 60)
            print(f"Q ({q.id}): {q.question}")
            if q.why_needed:
                print(f"   이유: {q.why_needed}")
            if q.options:
                for i, opt in enumerate(q.options, 1):
                    print(f"   {i}. {opt}")
                print("   (번호 또는 자유 답변 입력)")
            raw = input("A> ").strip()
            if q.options and raw.isdigit() and 1 <= int(raw) <= len(q.options):
                raw = q.options[int(raw) - 1]
            out.append(self._log(q, raw or "(no answer)", "human"))
        print("=" * 60 + "\n")
        return out

    # ------------------------------------------------------------- batch
    def _batch(self, questions: list[HITLQuestion], context: str) -> list[dict]:
        answers = {}
        if self.ws.answers_json.exists():
            answers = self.ws.read_json(self.ws.answers_json)

        def answer_for(q: HITLQuestion) -> str:
            """Ids are text hashes, so an id match IS a text match. The long form
            {"question": ..., "answer": ...} is additionally cross-checked; a
            text mismatch means the answer belongs to a different question —
            re-ask rather than silently reuse."""
            v = answers.get(q.id, "")
            if isinstance(v, dict):
                if v.get("question") and question_id(v["question"]) != q.id:
                    print(f"  !! [HITL/{self.stage}] answers.json '{q.id}': 질문 텍스트 "
                          f"불일치 — 이 답변은 무시하고 재질문합니다")
                    return ""
                v = v.get("answer", "")
            return str(v).strip()

        missing = [q for q in questions if not answer_for(q)]
        if missing:
            self.ws.write_json(self.ws.questions_pending_json, {
                "stage": self.stage, "context": context,
                "questions": [q.model_dump() for q in missing],
                "how_to_answer": ("write answers.json as {\"<id>\": \"<answer>\"} using the "
                                  "EXACT ids above (they are content hashes — stable across "
                                  "re-runs for the same question text), then re-run"),
            })
            raise PendingHumanInput(missing)
        if self.ws.questions_pending_json.exists():
            self.ws.questions_pending_json.unlink()
        return [self._log(q, answer_for(q), "human_batch") for q in questions]

    def _log(self, q: HITLQuestion, answer: str, who: str) -> dict:
        entry = {"stage": self.stage, "id": q.id, "question": q.question,
                 "why_needed": q.why_needed, "answer": answer, "answered_by": who}
        self.ws.append_jsonl(self.ws.human_qa_jsonl, entry)
        return {"id": q.id, "question": q.question, "answer": answer}
