"""CPU2026 A2 (휴머노이드 로봇 상용화): WIPS raw xlsx -> agentic judge pool CSV.

- 9,917 US granted patents (2015-2025), WIPS download sheet '다운로드'.
- A2 spec: 패밀리 기준 중복 제거 -> keep one representative per WIPS패밀리 ID
  (the earliest-filed grant; all rows are already 등록 so 등록-우선 is moot).
- Output columns: record_id/patent_id/title/abstract (agentic pipeline contract)
  + analysis metadata (CPC, dates, assignee, citations, family size) passed
  through untouched for the downstream cluster/bottleneck analysis.

python -m scripts.build_humanoid_pool
"""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW_XLSX = ROOT / "휴머노이드문제" / "CPU2026_Raw.xlsx"
OUT_DIR = ROOT / "DataSet" / "humanoid"

META_COLS = {
    "출원번호": "app_no", "등록번호": "grant_no", "공개번호": "pub_no",
    "출원일": "app_date", "등록일": "grant_date",
    "출원인": "assignee", "현재권리자[KR,JP,US,CN,CA,AU]": "current_owner",
    "출원인 국적": "assignee_country",
    "Original CPC Main": "cpc_main_orig", "Current CPC Main": "cpc_main",
    "Current CPC All": "cpc_all",
    "WIPS패밀리 ID": "family_id", "WIPS패밀리 문헌 수(출원기준)": "family_size",
    "인용 문헌 수(B1)": "n_backward_cites", "피인용 문헌 수(F1)": "n_forward_cites",
    "청구항 수": "n_claims", "WIPS ON key": "wips_key",
}


def main():
    df = pd.read_excel(RAW_XLSX, sheet_name="다운로드", dtype=str).fillna("")
    print(f"raw rows: {len(df)}")

    out = pd.DataFrame({
        "record_id": df["출원번호"].str.strip(),
        "patent_id": df["등록번호"].str.strip(),
        "title": df["발명의 명칭"].str.strip(),
        "abstract": df["요약"].str.strip(),
        "rep_claim": df["대표청구항"].str.strip(),
    })
    for src, dst in META_COLS.items():
        out[dst] = df[src].str.strip()

    # abstract fallback: the rare empty 요약 -> use the representative claim
    empty = out["abstract"].str.len() < 30
    out.loc[empty, "abstract"] = out.loc[empty, "rep_claim"]
    print(f"abstract fallback -> rep_claim: {int(empty.sum())} rows")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT_DIR / "pool_all.csv", index=False, encoding="utf-8")

    # family dedup: keep the earliest-filed grant per family
    dedup = (out.sort_values("app_date")
                .drop_duplicates(subset="family_id", keep="first")
                .reset_index(drop=True))
    dedup.to_csv(OUT_DIR / "pool.csv", index=False, encoding="utf-8")
    print(f"pool_all.csv: {len(out)} | pool.csv (family-deduped): {len(dedup)}")
    print(f"-> {OUT_DIR}")


if __name__ == "__main__":
    main()
