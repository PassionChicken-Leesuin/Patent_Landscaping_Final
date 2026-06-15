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


def _sample_ood(negatives: pd.DataFrame, n: int, seed: int) -> pd.DataFrame:
    """Sample n OOD negatives, stratified proportionally across source_domain."""
    if n is None or n >= len(negatives):
        return negatives
    if n <= 0:
        return negatives.iloc[0:0]
    if "source_domain" not in negatives.columns:
        return negatives.sample(n=n, random_state=seed)
    frac = n / len(negatives)
    parts = [g.sample(n=max(1, round(len(g) * frac)), random_state=seed)
             for _, g in negatives.groupby("source_domain")]
    return pd.concat(parts).sample(frac=1.0, random_state=seed).head(n)


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


def from_labeled_all(df: pd.DataFrame, arm: str, include_hard_neg: bool = True):
    """Unified-framework split: one labeled set (autonomous pool + OOD, with `source`)
    -> (pool_part, ood_negatives), so the existing assemble() can reuse the OOD-mix knobs.

    pool_part      : autonomous_pool rows -> text/label/group (positives + in-domain negs)
    ood_negatives  : ood_* rows the LABELER marked NOT_SEED -> text/source_domain
    """
    df = df.copy()
    df["text"] = _ensure_text(df)
    src = df.get("source", pd.Series(["autonomous_pool"] * len(df)))

    if arm == "snorkel":
        lab = df["snorkel_label"].astype(int)
        is_pos, is_neg, is_hard = (lab == POS), (lab == NEG), pd.Series(False, index=df.index)
    else:
        ct = df["candidate_type"]
        is_pos = ct == "positive"
        is_hard = ct == "hard_negative"
        is_neg = ct.isin(["easy_negative"] + (["hard_negative"] if include_hard_neg else []))

    is_ood = src.str.startswith("ood_")
    auto = ~is_ood

    # Framework-consistent: positives = whatever the LABELER marked SEED, regardless of source
    # (do not override the labeler with a source prior). Only the NEGATIVE side is split by
    # source, so the in-domain-vs-OOD negative mix can be controlled in the ablation.
    pos = df[is_pos]
    inpool_neg = df[is_neg & auto]
    pool_part = pd.concat([
        pd.DataFrame({"text": pos["text"].values, "label": POS, "group": "pool_pos"}),
        pd.DataFrame({"text": inpool_neg["text"].values, "label": NEG,
                      "group": ["pool_neg_hard" if h else "pool_neg" for h in is_hard[is_neg & auto]]}),
    ], ignore_index=True)

    ood_rows = df[is_neg & is_ood]
    ood_negatives = pd.DataFrame({"text": ood_rows["text"].values,
                                  "source_domain": src[is_neg & is_ood].str.replace("ood_", "", regex=False).values})
    return pool_part, ood_negatives


def assemble(labeled_pool_part: pd.DataFrame, negatives: pd.DataFrame,
             use_inpool_neg: bool = True, drop_dup_text: bool = True,
             ood_n=None, neg_pos_ratio=None, seed: int = 42) -> pd.DataFrame:
    """Combine arm-labeled pool rows with out-of-domain (OOD) negatives.

    Negative composition is controllable (the recall ablation):
      - use_inpool_neg : include in-pool NOT_SEED/hard_negative rows (in-domain, the
                         boundary the model must learn).
      - ood_n          : how many OOD negatives to include — None=all, 0=none, int=sample
                         that many (stratified across the 5 domains).
      - neg_pos_ratio  : if set, cap TOTAL negatives to ratio*positives, filling with
                         in-pool negatives FIRST (in-domain priority) then OOD. Overrides ood_n.

    Default (None/None) reproduces the original "all OOD" baseline.
    """
    pos = labeled_pool_part[labeled_pool_part["label"] == POS]
    inpool_neg = (labeled_pool_part[labeled_pool_part["label"] == NEG]
                  if use_inpool_neg else labeled_pool_part.iloc[0:0])

    if neg_pos_ratio is not None:
        target_neg = int(round(neg_pos_ratio * len(pos)))
        # in-domain negatives first; downsample them if they already exceed the target
        if len(inpool_neg) > target_neg:
            inpool_neg = inpool_neg.sample(n=target_neg, random_state=seed)
        ood_take = max(0, target_neg - len(inpool_neg))
    elif ood_n is not None:
        ood_take = int(ood_n)
    else:
        ood_take = len(negatives)

    ood = _sample_ood(negatives, ood_take, seed)
    ood_part = pd.DataFrame({"text": ood["text"], "label": NEG,
                             "group": "ood_" + ood.get("source_domain", "neg").astype(str)})

    df = pd.concat([pos, inpool_neg, ood_part], ignore_index=True)
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
