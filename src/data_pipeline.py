"""Data pipeline: load -> preprocess -> leakage dedup -> save processed sets.

Run via: python -m scripts.build_dataset   (or import these functions in a notebook)

Design notes
------------
* Eval and Training use DIFFERENT id schemes (family_id vs patent_id), so id-based
  overlap is meaningless. We detect leakage on ABSTRACT TEXT (token-set Jaccard).
* Eval is the fixed gold benchmark -> we NEVER drop from it. We drop the leaking
  patents from the TRAINING (candidate) pool only. This satisfies the MAS spec
  requirement (gold must not sit inside the candidate pool).
"""
from __future__ import annotations
import re
from collections import defaultdict, Counter

import pandas as pd

from src import config as C


# ---------------------------------------------------------------- text utils
def normalize(s: str) -> str:
    """Lowercase, strip everything non-alphanumeric -> single spaces."""
    s = (s or "").lower()
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def tokens(s: str) -> set[str]:
    return {w for w in normalize(s).split() if len(w) > 2}


def split_eval_text(text: str) -> tuple[str, str]:
    """Eval 'text' field is 'Title\\n\\nAbstract'. Return (title, abstract)."""
    parts = (text or "").split("\n", 1)
    title = parts[0].strip()
    abstract = parts[1].strip() if len(parts) > 1 else ""
    return title, abstract


# ---------------------------------------------------------------- loaders
def load_training() -> pd.DataFrame:
    df = pd.read_csv(C.TRAINING_CSV, encoding="utf-8-sig", dtype=str).fillna("")
    df = df.rename(columns={C.TRAIN_ID: "patent_id",
                            C.TRAIN_TITLE: "title",
                            C.TRAIN_ABSTRACT: "abstract"})
    # combined model input (Title + Abstract; no technical-field segmentation)
    df["text"] = (df["title"].str.strip() + ". " + df["abstract"].str.strip()).str.strip(". ").str.strip()
    df["record_id"] = df["patent_id"]
    df["domain"] = C.DOMAIN
    return df[["record_id", "patent_id", "domain", "title", "abstract", "text"]]


def load_eval() -> pd.DataFrame:
    df = pd.read_csv(C.EVAL_CSV, encoding="utf-8-sig", dtype=str).fillna("")
    titles, abstracts = zip(*df[C.EVAL_TEXT].map(split_eval_text))
    out = pd.DataFrame({
        "family_id": df[C.EVAL_ID],
        "expansion_level": df[C.EVAL_LEVEL],
        "title": titles,
        "abstract": abstracts,
        "text": df[C.EVAL_TEXT].str.replace(r"\s+", " ", regex=True).str.strip(),
        "label": df[C.EVAL_LABEL].astype(int),     # 1 = SEED, 0 = NOT_SEED
    })
    return out


# ---------------------------------------------------------------- leakage
def find_leakage(train: pd.DataFrame, ev: pd.DataFrame,
                 threshold: float = C.LEAKAGE_JACCARD_THRESHOLD) -> pd.DataFrame:
    """Return rows of training patents that are near-duplicates of an eval patent.

    Match on abstract token-set Jaccard via an inverted index (efficient).
    """
    train_sets = train["abstract"].map(tokens).tolist()
    inv: dict[str, list[int]] = defaultdict(list)
    for i, s in enumerate(train_sets):
        for w in s:
            inv[w].append(i)

    hits = []
    for _, ev_row in ev.iterrows():
        es = tokens(ev_row["abstract"])
        if len(es) < C.MIN_TOKENS:
            continue
        cand = Counter()
        for w in es:
            for i in inv.get(w, ()):
                cand[i] += 1
        best, best_i = 0.0, -1
        for i, shared in cand.most_common(40):
            jac = shared / len(es | train_sets[i])
            if jac > best:
                best, best_i = jac, i
        if best >= threshold:
            hits.append({
                "train_patent_id": train.iloc[best_i]["patent_id"],
                "eval_family_id": ev_row["family_id"],
                "eval_expansion_level": ev_row["expansion_level"],
                "eval_label": ev_row["label"],
                "jaccard": round(best, 4),
                "train_title": train.iloc[best_i]["title"][:80],
            })
    res = pd.DataFrame(hits).sort_values("jaccard", ascending=False).reset_index(drop=True)
    return res


def build_clean_training(train: pd.DataFrame, leaked: pd.DataFrame) -> pd.DataFrame:
    drop_ids = set(leaked["train_patent_id"]) if len(leaked) else set()
    clean = train[~train["patent_id"].isin(drop_ids)].reset_index(drop=True)
    return clean


# ---------------------------------------------------------------- driver
def run(write: bool = True) -> dict:
    C.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    C.LEAKAGE_DIR.mkdir(parents=True, exist_ok=True)

    train = load_training()
    ev = load_eval()
    leaked = find_leakage(train, ev)
    clean = build_clean_training(train, leaked)

    if write:
        leaked.to_csv(C.LEAKED_IDS_CSV, index=False, encoding="utf-8")
        clean.to_csv(C.TRAINING_CLEAN_CSV, index=False, encoding="utf-8")
        ev.to_csv(C.EVAL_PROCESSED_CSV, index=False, encoding="utf-8")

    return {"train_raw": train, "eval": ev, "leaked": leaked, "train_clean": clean}
