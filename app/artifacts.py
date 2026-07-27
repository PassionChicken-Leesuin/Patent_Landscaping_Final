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


def research_sources(ws: Path) -> list[dict]:
    """Verified external sources ACTUALLY fetched during research (research/pages/*.json).

    A page file is written only after the URL was retrieved and its text acquired, so every
    entry here is a real URL that was reachable at collection time — never an LLM-hallucinated
    citation. Joined with notes.jsonl to show how many evidence notes each source produced."""
    pdir = ws / "research" / "pages"
    if not pdir.exists():
        return []
    from collections import Counter
    ncount = Counter(n.get("source_url") for n in _read_jsonl(ws / "research" / "notes.jsonl"))
    out = []
    for p in sorted(pdir.glob("*.json")):
        d = _read_json(p) or {}
        url = d.get("url")
        if not url:
            continue
        out.append({"url": url, "title": (d.get("title") or url).strip(),
                    "source": d.get("source", ""), "n_notes": int(ncount.get(url, 0))})
    out.sort(key=lambda r: (r["n_notes"], r["title"]), reverse=True)
    return out


def corpus_alignment(ws: Path) -> list[dict]:
    """Structured web<->pool alignment rows from the corpus digest — the auditable comparison
    that grounds each inclusion/exclusion criterion (see EvidenceAlignment / ALIGN_COVERAGE)."""
    d = _read_json(ws / "corpus_digest.json") or {}
    return d.get("alignment", []) or []


def web_ref_urls(ws: Path) -> dict[str, str]:
    """web:n -> source_url (research-notes file order), so alignment web_refs can link out."""
    notes = _read_jsonl(ws / "research" / "notes.jsonl")
    return {f"web:{i}": str(n.get("source_url", "")).strip() for i, n in enumerate(notes, 1)}


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


# ---- case-mapping front-half surfaces ----
def pool_profile(ws: Path) -> dict | None:
    return _read_json(ws / "pool_profile.json")


def diagnosis(ws: Path) -> dict | None:
    return _read_json(ws / "diagnosis.json")


def design_plan(ws: Path) -> dict | None:
    return _read_json(ws / "design_plan.json")


def casemap_categories(ws: Path) -> list[dict]:
    d = ws / "casemap"
    if not d.exists():
        return []
    out = []
    for p in sorted(d.glob("*.json")):
        c = _read_json(p)
        if c:
            out.append(c)
    return out


def casemap_revisions(ws: Path, category: str) -> list[dict]:
    from src.agentic.workspace import slugify
    return _read_jsonl(ws / "casemap" / f"{slugify(category)}.revisions.jsonl")


def casemap_summary(ws: Path) -> dict | None:
    return _read_json(ws / "casemap_summary.json")


def decisions(ws: Path) -> list[dict]:
    d = _read_json(ws / "decisions.json") or {}
    return d.get("decisions", [])


def pool_lookup(run_dir: Path) -> dict:
    """patent_id / record_id -> (title, abstract) from the run's judge pool, so decision
    cards can show the example patents' real title + abstract."""
    p = Path(run_dir) / "pool.csv"
    if not p.exists():
        return {}
    try:
        df = pd.read_csv(p, dtype=str).fillna("")
    except Exception:
        return {}
    out: dict = {}
    for _, r in df.iterrows():
        t, a = str(r.get("title", "")), str(r.get("abstract", ""))
        for key in (r.get("patent_id", ""), r.get("record_id", "")):
            k = str(key).strip()
            if k:
                out.setdefault(k, (t, a))
    return out


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
