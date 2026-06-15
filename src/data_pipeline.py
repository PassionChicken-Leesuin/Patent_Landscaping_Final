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
from pathlib import Path

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
                 abs_threshold: float = C.LEAKAGE_ABS_THRESHOLD,
                 title_threshold: float = C.LEAKAGE_TITLE_THRESHOLD) -> pd.DataFrame:
    """Return ALL training patents that are family members of an eval patent.

    A train patent is flagged if (abstract Jaccard >= abs_threshold) OR (title Jaccard >=
    title_threshold) with any eval patent. Title-awareness + a lower abstract threshold
    catch cross-jurisdiction family members (EP/WO<->US) whose abstracts are translated/
    amended and so score lower on raw abstract Jaccard. We flag EVERY matching train row
    (not just the single best), since a gold family can have multiple US members in the pool.
    """
    train_abs = train["abstract"].map(tokens).tolist()
    train_tit = train["title"].map(tokens).tolist()
    inv: dict[str, list[int]] = defaultdict(list)
    for i, s in enumerate(train_abs):
        for w in s:
            inv[w].append(i)
    tinv: dict[str, list[int]] = defaultdict(list)
    for i, s in enumerate(train_tit):
        for w in s:
            tinv[w].append(i)

    flagged: dict[int, dict] = {}
    for _, ev_row in ev.iterrows():
        es = tokens(ev_row["abstract"]); ts = tokens(ev_row["title"])
        cand = Counter()
        for w in es:
            for i in inv.get(w, ()):
                cand[i] += 1
        for w in ts:
            for i in tinv.get(w, ()):
                cand[i] += 1
        for i, _ in cand.most_common(80):
            ja = len(es & train_abs[i]) / len(es | train_abs[i]) if (es and train_abs[i]) else 0.0
            jt = len(ts & train_tit[i]) / len(ts | train_tit[i]) if (ts and train_tit[i]) else 0.0
            if ja >= abs_threshold or jt >= title_threshold:
                prev = flagged.get(i)
                score = max(ja, jt)
                if prev is None or score > prev["_score"]:
                    flagged[i] = {
                        "train_patent_id": train.iloc[i]["patent_id"],
                        "eval_family_id": ev_row["family_id"],
                        "eval_expansion_level": ev_row["expansion_level"],
                        "eval_label": ev_row["label"],
                        "abs_jaccard": round(ja, 4), "title_jaccard": round(jt, 4),
                        "train_title": str(train.iloc[i]["title"])[:80], "_score": score,
                    }
    res = pd.DataFrame(list(flagged.values()))
    if len(res):
        res = res.drop(columns="_score").sort_values("abs_jaccard", ascending=False).reset_index(drop=True)
    return res


def build_negative_pool(ev: pd.DataFrame | None = None) -> pd.DataFrame:
    """Load the 5 out-of-domain CSVs into a unified NOT_SEED negative pool.

    All rows are negatives for autonomous driving. We tag source_domain and
    hardness (computervision = hard), dedup by family_id, and drop any family_id
    that leaks into the autonomous-driving eval set.
    """
    import glob
    if ev is None:
        ev = load_eval()
    eval_fams = set(ev["family_id"].astype(str))

    frames = []
    for fp in sorted(glob.glob(str(C.NEG_DIR / "*.csv"))):
        dom = Path(fp).stem.replace("training_", "")
        d = pd.read_csv(fp, encoding="utf-8-sig", dtype=str).fillna("")
        text_col = "text"
        keep = pd.DataFrame({
            "family_id": d["family_id"].astype(str),
            "source_domain": dom,
            "in_domain_is_seed": d.get("is_seed", ""),
            "text": d[text_col].str.replace(r"\s+", " ", regex=True).str.strip(),
            "hardness": "hard" if dom in C.NEG_HARD_DOMAINS else "easy",
        })
        frames.append(keep)

    neg = pd.concat(frames, ignore_index=True)
    neg = neg.drop_duplicates(subset="family_id").reset_index(drop=True)
    before = len(neg)
    neg = neg[~neg["family_id"].isin(eval_fams)].reset_index(drop=True)   # drop eval leaks
    neg.attrs["eval_leaks_removed"] = before - len(neg)
    neg["label"] = 0                                                       # NOT_SEED
    return neg


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
    negatives = build_negative_pool(ev)

    if write:
        leaked.to_csv(C.LEAKED_IDS_CSV, index=False, encoding="utf-8")
        clean.to_csv(C.TRAINING_CLEAN_CSV, index=False, encoding="utf-8")
        ev.to_csv(C.EVAL_PROCESSED_CSV, index=False, encoding="utf-8")
        negatives.to_csv(C.NEG_CLEAN_CSV, index=False, encoding="utf-8")

    return {"train_raw": train, "eval": ev, "leaked": leaked,
            "train_clean": clean, "negatives": negatives}
