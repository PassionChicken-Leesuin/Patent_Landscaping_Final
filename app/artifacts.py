"""Read-side helpers: workspace artifacts -> UI-friendly objects, final xlsx export."""
from __future__ import annotations

import io
import json
from pathlib import Path

import pandas as pd

from app import runner


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def _read_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


# ------------------------------------------------------------------ criteria
def criteria_versions(ws: Path) -> list[tuple[str, str]]:
    """[(label, markdown), ...] oldest->newest, final last if present."""
    out = []
    versions = sorted(ws.glob("criteria_v*.md"),
                      key=lambda p: int(p.stem.split("v")[-1]))
    for p in versions:
        out.append((f"v{p.stem.split('v')[-1]}", p.read_text(encoding="utf-8")))
    final = ws / "criteria_final.md"
    if final.exists():
        out.append(("최종 승인본", final.read_text(encoding="utf-8")))
    return out


def critiques(ws: Path) -> list[dict]:
    out = []
    for p in sorted(ws.glob("critique_v*.json"),
                    key=lambda p: int(p.stem.split("v")[-1])):
        d = _read_json(p) or {}
        d["_version"] = p.stem.split("v")[-1]
        out.append(d)
    return out


def human_qa(ws: Path) -> list[dict]:
    return _read_jsonl(ws / "human_qa.jsonl")


def axis_md(ws: Path) -> str | None:
    p = ws / "axis_synthesis.md"
    return p.read_text(encoding="utf-8") if p.exists() else None


def blocked_report(ws: Path) -> dict | None:
    """criteria_blocked.json — fail-loud stop report (quality vs human_pending)."""
    return _read_json(ws / "criteria_blocked.json")


def issue_ledger(ws: Path) -> list[dict]:
    """Ledger rows sorted open-first then by first_round."""
    d = _read_json(ws / "criteria_issue_ledger.json") or {}
    rows = list(d.get("issues", {}).values())
    return sorted(rows, key=lambda r: (r.get("status") != "open",
                                       r.get("first_round", 0)))


def provenance_repairs(ws: Path) -> list[dict]:
    return _read_jsonl(ws / "provenance_repairs.jsonl")


def research_notes(ws: Path) -> pd.DataFrame:
    notes = _read_jsonl(ws / "research" / "notes.jsonl")
    if not notes:
        return pd.DataFrame()
    return pd.DataFrame(notes)


def blocked_pages(ws: Path) -> list[dict]:
    return _read_jsonl(ws / "research" / "blocked.jsonl")


def corpus_digest(ws: Path) -> dict | None:
    return _read_json(ws / "corpus_digest.json")


def boundary_probe(ws: Path) -> list[dict]:
    return _read_jsonl(ws / "boundary_probe.jsonl")


def judge_progress(ws: Path) -> int:
    """Distinct record_ids already judged (audit.jsonl grows during stage [6])."""
    seen = set()
    p = ws / "judge" / "audit.jsonl"
    if not p.exists():
        return 0
    for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            seen.add(json.loads(line).get("record_id"))
        except (json.JSONDecodeError, AttributeError):
            continue
    seen.discard(None)
    return len(seen)


def ranked(ws: Path) -> pd.DataFrame:
    p = ws / "judge" / "ranked.csv"
    if not p.exists():
        return pd.DataFrame()
    df = pd.read_csv(p, dtype={"record_id": str, "patent_id": str})
    df["score"] = pd.to_numeric(df["score"], errors="coerce")
    if "relevance_score" not in df.columns:
        df["relevance_score"] = df["score"]
    df["relevance_score"] = pd.to_numeric(df["relevance_score"], errors="coerce")
    if "decision_confidence" in df.columns:
        df["decision_confidence"] = pd.to_numeric(df["decision_confidence"], errors="coerce")
    if "included" not in df.columns:
        df["included"] = df.get("candidate_type", "").eq("positive")
    else:
        df["included"] = df["included"].astype(str).str.lower().isin(("true", "1", "yes"))
    return df


# ------------------------------------------------------------------ export
def selected_slice(ranked_df: pd.DataFrame, mode: str, threshold: float,
                   top_n: int) -> pd.DataFrame:
    score_col = "relevance_score" if "relevance_score" in ranked_df.columns else "score"
    if "included" in ranked_df.columns:
        mask = ranked_df["included"].astype(bool)
    else:
        mask = ranked_df.get("candidate_type", pd.Series(index=ranked_df.index,
                                                          dtype=str)).eq("positive")
    df = ranked_df[mask].sort_values(score_col, ascending=False)
    if mode == "all_positive":
        return df
    if mode == "threshold":
        return df[df[score_col] >= threshold]
    return df.head(top_n)


def build_result_xlsx(run_dir: Path, selected: pd.DataFrame,
                      criteria_md: str | None) -> bytes:
    """Selected patents + original uploaded columns + the criteria document."""
    from app.pool_convert import read_uploaded

    m = runner.load_manifest(run_dir)
    out = selected.reset_index(drop=True).copy()
    out.insert(0, "선별순위", range(1, len(out) + 1))

    src_files = list((run_dir / "uploads").glob("source.*"))
    if src_files and m.get("id_col"):
        raw = read_uploaded(src_files[0].name, src_files[0].read_bytes())
        idc = m["id_col"]
        if idc in raw.columns:
            raw = raw.copy()
            raw["record_id"] = raw[idc].astype(str).str.strip()
            raw = raw.drop_duplicates(subset="record_id", keep="first")
            keep = [c for c in raw.columns
                    if c not in ("record_id",) and c not in out.columns]
            out = out.merge(raw[["record_id"] + keep], on="record_id", how="left")

    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        out.to_excel(writer, sheet_name="선별특허", index=False)
        if criteria_md:
            crit = pd.DataFrame({"판단 기준서": criteria_md.splitlines()})
            crit.to_excel(writer, sheet_name="판단기준서", index=False)
    return buf.getvalue()
