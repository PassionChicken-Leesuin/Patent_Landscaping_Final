"""Snorkel labeling pipeline + a snorkel-free local coverage analyzer.

* apply_lfs_pure / coverage_report : pure python, run locally on Python 3.14 to
  sanity-check LF coverage/overlap BEFORE spending Colab time.
* run_snorkel : the real LabelModel run (cardinality=2). Requires snorkel (Colab).
"""
from __future__ import annotations
from collections import Counter

import numpy as np

from src.snorkel_arm.lfs import LF_SPECS, SEED, NOT_SEED, ABSTAIN


# ---------------- pure local analyzer (no snorkel) ----------------
def apply_lfs_pure(texts) -> np.ndarray:
    names = [n for n, _ in LF_SPECS]
    L = np.empty((len(texts), len(LF_SPECS)), dtype=int)
    for j, (_, fn) in enumerate(LF_SPECS):
        for i, t in enumerate(texts):
            L[i, j] = fn(t)
    return L


def coverage_report(L: np.ndarray) -> dict:
    names = [n for n, _ in LF_SPECS]
    m, n = L.shape
    voted = L != ABSTAIN
    rows = []
    for j, name in enumerate(names):
        col = L[:, j]
        cov = voted[:, j].mean()
        # overlap: fraction of points where this LF votes AND >=1 other LF votes
        others = voted.sum(axis=1) - voted[:, j].astype(int)
        overlap = ((voted[:, j]) & (others > 0)).mean()
        pol = Counter(col[col != ABSTAIN].tolist())
        rows.append({"lf": name, "coverage": round(cov, 4), "overlap": round(overlap, 4),
                     "polarity": {("SEED" if k == SEED else "NOT_SEED"): int(v) for k, v in pol.items()}})

    # majority-vote proxy label (pre-LabelModel) just to preview class balance
    def mv(row):
        votes = [v for v in row if v != ABSTAIN]
        if not votes:
            return ABSTAIN
        c = Counter(votes)
        top, cnt = c.most_common(1)[0]
        # tie -> abstain
        if list(c.values()).count(cnt) > 1:
            return ABSTAIN
        return top

    mv_labels = [mv(L[i]) for i in range(m)]
    dist = Counter(mv_labels)
    any_label = voted.any(axis=1).mean()
    return {
        "n": m, "lf_table": rows,
        "fraction_with_any_label": round(any_label, 4),
        "fraction_all_abstain": round(1 - any_label, 4),
        "majority_vote_preview": {
            "SEED": dist.get(SEED, 0), "NOT_SEED": dist.get(NOT_SEED, 0),
            "ABSTAIN(tie/none)": dist.get(ABSTAIN, 0),
        },
    }


# ---------------- snorkel run (Colab) ----------------
def run_snorkel(df, text_col: str = "text", n_epochs: int = 500, lr: float = 0.001,
                seed: int = 123, drop_abstain: bool = True):
    """Fit LabelModel and attach 'snorkel_label'. df must have `text_col`.

    Returns (labeled_df, lf_summary_df, L). Requires snorkel.
    """
    from snorkel.labeling import PandasLFApplier, LFAnalysis
    from snorkel.labeling.model import LabelModel
    from src.snorkel_arm.lfs import build_snorkel_lfs

    lfs = build_snorkel_lfs()
    applier = PandasLFApplier(lfs)
    L = applier.apply(df)

    label_model = LabelModel(cardinality=2, verbose=True)
    label_model.fit(L, n_epochs=n_epochs, lr=lr, log_freq=50, seed=seed)

    df = df.copy()
    df["snorkel_label"] = label_model.predict(L=L, tie_break_policy="abstain")
    # probabilistic labels too (for noise-aware training, optional)
    probs = label_model.predict_proba(L=L)
    df["snorkel_prob_seed"] = probs[:, SEED]

    summary = LFAnalysis(L=L, lfs=lfs).lf_summary()
    if drop_abstain:
        df = df[df["snorkel_label"] != ABSTAIN].reset_index(drop=True)
    return df, summary, L
