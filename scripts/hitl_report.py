"""Collect all HITL questions (esp. auto-answered ones from unattended runs) into a
single review file so the human owner can revisit scope decisions later.

python -m scripts.hitl_report   -> experiments/PENDING_QUESTIONS.md
"""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from src.agentic import config as AC
from src.agentic.workspace import Workspace


def main():
    lines = ["# HITL 질문 리포트 (무인 실행 중 자동응답된 항목 검토용)", ""]
    n = 0
    if AC.AGENTIC_DIR.exists():
        for qa_path in sorted(AC.AGENTIC_DIR.glob("*/human_qa.jsonl")):
            entries = Workspace.read_jsonl(qa_path)
            if not entries:
                continue
            lines.append(f"## {qa_path.parent.name}")
            for e in entries:
                n += 1
                who = e.get("answered_by", "?")
                lines.append(f"- **[{e.get('stage', '?')}/{who}] Q:** {e.get('question', '')}")
                if e.get("why_needed"):
                    lines.append(f"  - 이유: {e['why_needed']}")
                lines.append(f"  - A: {e.get('answer', '')}")
            lines.append("")
    out = Path("experiments/PENDING_QUESTIONS.md")
    out.parent.mkdir(exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"{n} Q&A entries -> {out}")


if __name__ == "__main__":
    main()
