"""Per-run workspace: audit/cache layout under DataSet/agentic/<run-slug>/.

Artifacts may be reused to resume the same interrupted run. User questions and
answers must never be loaded from a different workspace/run.
"""
from __future__ import annotations
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path

from src.agentic import config as AC


def slugify(name: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return (s[:80].rstrip("-") or "domain")   # cap length -> avoid Windows path-length limits


def url_hash(url: str) -> str:
    return hashlib.sha1(url.encode("utf-8")).hexdigest()[:16]


@dataclass
class Workspace:
    slug: str

    @property
    def root(self) -> Path:
        return AC.AGENTIC_DIR / self.slug

    # ---- stage artifacts ----
    @property
    def query_json(self) -> Path: return self.root / "query.json"
    @property
    def research_dir(self) -> Path: return self.root / "research"
    @property
    def searches_jsonl(self) -> Path: return self.research_dir / "searches.jsonl"
    @property
    def pages_dir(self) -> Path: return self.research_dir / "pages"
    @property
    def notes_jsonl(self) -> Path: return self.research_dir / "notes.jsonl"
    @property
    def blocked_jsonl(self) -> Path: return self.research_dir / "blocked.jsonl"
    @property
    def owner_docs_json(self) -> Path: return self.root / "owner_docs.json"
    @property
    def corpus_digest_json(self) -> Path: return self.root / "corpus_digest.json"
    # ---- case-mapping front-half artifacts ----
    @property
    def pool_profile_json(self) -> Path: return self.root / "pool_profile.json"
    @property
    def diagnosis_json(self) -> Path: return self.root / "diagnosis.json"
    @property
    def design_plan_json(self) -> Path: return self.root / "design_plan.json"
    @property
    def casemap_dir(self) -> Path: return self.root / "casemap"
    def casemap_json(self, category: str) -> Path:
        return self.casemap_dir / f"{slugify(category)}.json"
    def casemap_revisions_jsonl(self, category: str) -> Path:
        return self.casemap_dir / f"{slugify(category)}.revisions.jsonl"
    @property
    def casemap_summary_json(self) -> Path: return self.root / "casemap_summary.json"
    @property
    def false_positive_cues_json(self) -> Path: return self.root / "false_positive_cues.json"
    @property
    def decisions_json(self) -> Path: return self.root / "decisions.json"
    @property
    def axis_synthesis_json(self) -> Path: return self.root / "axis_synthesis.json"
    @property
    def axis_synthesis_md(self) -> Path: return self.root / "axis_synthesis.md"
    @property
    def axis_synthesis_blocked_json(self) -> Path: return self.root / "axis_synthesis_blocked.json"
    @property
    def human_qa_jsonl(self) -> Path: return self.root / "human_qa.jsonl"
    @property
    def questions_pending_json(self) -> Path: return self.root / "questions_pending.json"
    @property
    def answers_json(self) -> Path: return self.root / "answers.json"
    @property
    def boundary_probe_jsonl(self) -> Path: return self.root / "boundary_probe.jsonl"
    @property
    def criteria_pending_json(self) -> Path: return self.root / "criteria_pending.json"
    @property
    def criteria_final_json(self) -> Path: return self.root / "criteria_final.json"
    @property
    def criteria_final_md(self) -> Path: return self.root / "criteria_final.md"
    @property
    def criteria_blocked_json(self) -> Path: return self.root / "criteria_blocked.json"
    @property
    def criteria_issue_ledger_json(self) -> Path: return self.root / "criteria_issue_ledger.json"
    @property
    def provenance_repairs_jsonl(self) -> Path: return self.root / "provenance_repairs.jsonl"
    @property
    def judge_dir(self) -> Path: return self.root / "judge"
    @property
    def judge_audit_jsonl(self) -> Path: return self.judge_dir / "audit.jsonl"
    @property
    def second_pass_jsonl(self) -> Path: return self.judge_dir / "second_pass.jsonl"
    @property
    def judge_validation_jsonl(self) -> Path: return self.judge_dir / "validation.jsonl"
    @property
    def ranked_csv(self) -> Path: return self.judge_dir / "ranked.csv"
    @property
    def metrics_json(self) -> Path: return self.root / "metrics.json"

    def criteria_json(self, version: int) -> Path:
        return self.root / f"criteria_v{version}.json"

    def criteria_md(self, version: int) -> Path:
        return self.root / f"criteria_v{version}.md"

    def critique_json(self, version: int) -> Path:
        return self.root / f"critique_v{version}.json"

    def ensure(self) -> "Workspace":
        self.pages_dir.mkdir(parents=True, exist_ok=True)
        self.judge_dir.mkdir(parents=True, exist_ok=True)
        return self

    # ---- small json/jsonl helpers ----
    @staticmethod
    def write_json(path: Path, obj) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")

    @staticmethod
    def read_json(path: Path):
        return json.loads(path.read_text(encoding="utf-8"))

    @staticmethod
    def append_jsonl(path: Path, obj) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")

    @staticmethod
    def read_jsonl(path: Path) -> list:
        if not path.exists():
            return []
        out = []
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    out.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return out
