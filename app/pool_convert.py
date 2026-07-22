"""Uploaded patent file (WIPS xlsx / generic csv-xlsx) -> agentic judge pool CSV.

Formats
-------
wips    WIPS ON bulk download (sheet '다운로드', Korean columns). Same mapping as
        scripts/build_humanoid_pool.py: record_id=출원번호, patent_id=등록번호,
        title=발명의 명칭, abstract=요약 (fallback 대표청구항), meta passthrough,
        optional family dedup (earliest-filed row per WIPS패밀리 ID).
ready   already has title/abstract columns -> used as-is.
mapped  user maps the columns in the UI.
"""
from __future__ import annotations

import io
from pathlib import Path

import pandas as pd

WIPS_SHEET = "다운로드"
WIPS_TITLE = "발명의 명칭"
WIPS_ABSTRACT = "요약"
WIPS_ID = "출원번호"

# WIPS column -> pool meta column (matches scripts/build_humanoid_pool.py)
WIPS_META = {
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


def read_uploaded(name: str, data: bytes) -> pd.DataFrame:
    """Read an uploaded xlsx/csv into a string DataFrame."""
    suffix = Path(name).suffix.lower()
    if suffix in (".xlsx", ".xls"):
        xl = pd.ExcelFile(io.BytesIO(data))
        sheet = WIPS_SHEET if WIPS_SHEET in xl.sheet_names else xl.sheet_names[0]
        df = xl.parse(sheet, dtype=str)
    else:
        df = pd.read_csv(io.BytesIO(data), dtype=str, encoding="utf-8-sig")
    return df.fillna("")


def sniff_format(df: pd.DataFrame) -> str:
    cols = set(df.columns)
    if WIPS_TITLE in cols and WIPS_ABSTRACT in cols:
        return "wips"
    if "title" in cols and "abstract" in cols:
        return "ready"
    return "unknown"


def convert_wips(df: pd.DataFrame, family_dedup: bool = True
                 ) -> tuple[pd.DataFrame, list[str]]:
    report: list[str] = [f"WIPS 포맷 인식: 원본 {len(df)}행"]
    out = pd.DataFrame({
        "record_id": df[WIPS_ID].str.strip(),
        "patent_id": df.get("등록번호", df[WIPS_ID]).str.strip(),
        "title": df[WIPS_TITLE].str.strip(),
        "abstract": df[WIPS_ABSTRACT].str.strip(),
    })
    rep_claim = df.get("대표청구항")
    if rep_claim is not None:
        empty = out["abstract"].str.len() < 30
        out.loc[empty, "abstract"] = rep_claim[empty].str.strip()
        if int(empty.sum()):
            report.append(f"요약이 비어 대표청구항으로 대체: {int(empty.sum())}행")
    for src, dst in WIPS_META.items():
        if src in df.columns:
            out[dst] = df[src].str.strip()
    if family_dedup and "family_id" in out.columns:
        before = len(out)
        sort_col = "app_date" if "app_date" in out.columns else "record_id"
        out = (out.sort_values(sort_col)
                  .drop_duplicates(subset="family_id", keep="first")
                  .reset_index(drop=True))
        report.append(f"패밀리 중복제거 (WIPS패밀리 ID, 최선출원 대표 1건): "
                      f"{before} → {len(out)}행")
    out = out[out["title"].str.len() + out["abstract"].str.len() > 0].reset_index(drop=True)
    report.append(f"판정 풀 최종: {len(out)}건")
    return out, report


def convert_mapped(df: pd.DataFrame, title_col: str, abstract_col: str,
                   id_col: str | None) -> tuple[pd.DataFrame, list[str]]:
    out = pd.DataFrame({
        "record_id": (df[id_col].astype(str).str.strip() if id_col
                      else [f"row{i}" for i in range(len(df))]),
        "patent_id": (df[id_col].astype(str).str.strip() if id_col
                      else [f"row{i}" for i in range(len(df))]),
        "title": df[title_col].astype(str).str.strip(),
        "abstract": df[abstract_col].astype(str).str.strip(),
    })
    for c in df.columns:
        if c not in (title_col, abstract_col, id_col) and c not in out.columns:
            out[c] = df[c]
    out = out[out["title"].str.len() + out["abstract"].str.len() > 0].reset_index(drop=True)
    dup = out["record_id"].duplicated().sum()
    if dup:
        out = out.drop_duplicates(subset="record_id", keep="first").reset_index(drop=True)
    report = [f"컬럼 매핑 변환: {len(out)}건" + (f" (중복 id {dup}건 제거)" if dup else "")]
    return out, report


def convert_ready(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    idc = next((c for c in ("record_id", "family_id", "patent_id") if c in df.columns), None)
    return convert_mapped(df, "title", "abstract", idc)
