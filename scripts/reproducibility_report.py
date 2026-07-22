"""Compare two isolated July-system runs and optionally fail CI on regression.

Example:
  python -m scripts.reproducibility_report --run-a <slug-a> --run-b <slug-b> --strict
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.agentic import config as AC
from src.agentic.reproducibility import compare_independent_runs


def _run_path(value: str) -> Path:
    direct = Path(value)
    return direct if direct.exists() else AC.AGENTIC_DIR / value


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-a", required=True, help="run slug or workspace path")
    ap.add_argument("--run-b", required=True, help="run slug or workspace path")
    ap.add_argument("--top-n", type=int, default=100)
    ap.add_argument("--output", default=None, help="JSON output path")
    ap.add_argument("--strict", action="store_true",
                    help="exit non-zero when any reproducibility threshold fails")
    args = ap.parse_args()

    a, b = _run_path(args.run_a), _run_path(args.run_b)
    report, changed = compare_independent_runs(a, b, top_n=args.top_n)
    AC.OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    stem = f"reproducibility_{a.name}_vs_{b.name}"
    json_path = Path(args.output) if args.output else AC.OUTPUTS_DIR / f"{stem}.json"
    csv_path = json_path.with_suffix(".changed.csv")
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=float),
                         encoding="utf-8")
    pd.DataFrame(changed).to_csv(csv_path, index=False, encoding="utf-8")

    m = report["metrics"]
    print(f"passed={report['passed']} common={report['pool']['n_common']} "
          f"stance={m['stance_agreement']:.3f} kappa={m['cohen_kappa']:.3f} "
          f"positive_jaccard={m['positive_jaccard']:.3f} "
          f"rank_spearman={m['relevance_spearman']:.3f}")
    print(f"report -> {json_path}\nchanged decisions -> {csv_path}")
    if args.strict and not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
