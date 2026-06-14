"""Assemble the SciBERT training set from a labeled pool + out-of-domain negatives.

Shared by BOTH arms — only the `labeled_pool` differs (Snorkel vs MAS). Everything
else (out-of-domain negatives, dedup, balancing) is held identical for a fair fight.

Training set =
  positives     : pool rows the arm labeled SEED                    -> label 1
  in-pool negs  : pool rows the arm labeled NOT_SEED / hard_negative-> label 0  (optional)
  out-of-domain : negatives_pool.csv (5 other domains, fixed)       -> label 0

Pure pandas — runs locally (no torch). label convention: 1=SEED, 0=NOT_SEED.
"""
from __future__ import annotations
import pandas as pd

POS, NEG = 1, 0


def _norm_key(s: pd.Series) -> pd.Series:
    return s.str.lower().str.replace(r"[^a-z0-9]+", " ", regex=True).str.strip()


def _ensure_text(df: pd.DataFrame) -> pd.Series:
    """Return a text column; build it from title + abstract if 'text' is absent."""
    if "text" in df.columns:
        return df["text"]
    title = df.get("title", "").fillna("") if hasattr(df.get("title", ""), "fillna") else df.get("title", "")
    abstract = df.get("abstract", "").fillna("") if hasattr(df.get("abstract", ""), "fillna") else df.get("abstract", "")
    return (title.str.strip() + ". " + abstract.str.strip()).str.strip(". ").str.strip()


def from_snorkel(labeled_pool: pd.DataFrame) -> pd.DataFrame:
    """labeled_pool has snorkel_label (1/0/-1) and text (or title+abstract)."""
    df = labeled_pool.copy()
    df["text"] = _ensure_text(df)
    df = df[df["snorkel_label"].astype(int) != -1]
    out = pd.DataFrame({"text": df["text"].values,
                        "label": df["snorkel_label"].astype(int).values})
    out["group"] = ["pool_pos" if v == POS else "pool_neg" for v in out["label"]]
    return out


def from_mas(ranked: pd.DataFrame, include_hard_neg: bool = True) -> pd.DataFrame:
    """ranked has candidate_type and text (or title+abstract)."""
    df = ranked.copy()
    df["text"] = _ensure_text(df)
    pos = df[df["candidate_type"] == "positive"]
    neg_types = ["easy_negative"] + (["hard_negative"] if include_hard_neg else [])
    neg = df[df["candidate_type"].isin(neg_types)]
    rows = pd.concat([
        pd.DataFrame({"text": pos["text"].values, "label": POS, "group": "pool_pos"}),
        pd.DataFrame({"text": neg["text"].values, "label": NEG,
                      "group": ["pool_neg_hard" if t == "hard_negative" else "pool_neg"
                                for t in neg["candidate_type"]]}),
    ], ignore_index=True)
    return rows


def assemble(labeled_pool_part: pd.DataFrame, negatives: pd.DataFrame,
             use_inpool_neg: bool = True, drop_dup_text: bool = True,
             seed: int = 42) -> pd.DataFrame:
    """Combine arm-labeled pool rows with out-of-domain negatives -> shuffled train df."""
    parts = []
    if use_inpool_neg:
        parts.append(labeled_pool_part)
    else:
        parts.append(labeled_pool_part[labeled_pool_part["label"] == POS])

    ood = pd.DataFrame({"text": negatives["text"], "label": NEG,
                        "group": "ood_" + negatives.get("source_domain", "neg").astype(str)})
    parts.append(ood)

    df = pd.concat(parts, ignore_index=True)
    df = df[df["text"].str.strip() != ""]
    if drop_dup_text:
        df = df.assign(_k=_norm_key(df["text"])).drop_duplicates("_k").drop(columns="_k")
    df = df.sample(frac=1.0, random_state=seed).reset_index(drop=True)
    return df


def summary(df: pd.DataFrame) -> str:
    n = len(df)
    pos = int((df["label"] == POS).sum())
    lines = [f"train rows: {n}  | pos: {pos} ({pos/n:.1%})  neg: {n-pos}",
             "by group:"]
    for g, c in df["group"].value_counts().items():
        lines.append(f"  {g:18s} {c}")
    return "\n".join(lines)
