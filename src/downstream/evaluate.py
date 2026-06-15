"""Evaluate a fine-tuned model on the gold eval set (shared by both arms).

Reports overall metrics (imbalanced -> Macro-F1 / AUC / Average-Precision primary)
AND a breakdown by expansion_level: SEED recall, ANTISEED-manual specificity (hard
negatives), ANTISEED-AF specificity (easy negatives).

Also supports threshold calibration: the default 0.5 threshold is often badly placed
when negatives are very easy (OOD domains), crushing recall. tune_threshold() picks
the macro-F1-optimal threshold on a VALIDATION set (never the gold set).
"""
from __future__ import annotations
import numpy as np
import pandas as pd


def predict_proba(model_dir: str, texts: list[str], max_len: int = 256, batch: int = 64) -> np.ndarray:
    import torch
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    tok = AutoTokenizer.from_pretrained(model_dir)
    model = AutoModelForSequenceClassification.from_pretrained(model_dir).eval()
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    model.to(dev)
    probs = []
    with torch.no_grad():
        for i in range(0, len(texts), batch):
            enc = tok(texts[i:i + batch], truncation=True, max_length=max_len,
                      padding=True, return_tensors="pt").to(dev)
            logits = model(**enc).logits
            probs.append(torch.softmax(logits, -1)[:, 1].cpu().numpy())
    return np.concatenate(probs)


def tune_threshold(y: np.ndarray, p: np.ndarray, grid: int = 199) -> tuple[float, float]:
    """Return (threshold, macro_f1) maximizing macro-F1 over a probability grid."""
    from sklearn.metrics import f1_score
    best_t, best_f1 = 0.5, -1.0
    for t in np.linspace(0.01, 0.99, grid):
        f1 = f1_score(y, (p >= t).astype(int), average="macro", zero_division=0)
        if f1 > best_f1:
            best_t, best_f1 = float(t), float(f1)
    return best_t, best_f1


def report_from_probs(y: np.ndarray, p: np.ndarray, eval_df: pd.DataFrame,
                      threshold: float = 0.5) -> dict:
    from sklearn.metrics import (accuracy_score, precision_score, recall_score,
                                 f1_score, roc_auc_score, average_precision_score,
                                 confusion_matrix)
    yhat = (p >= threshold).astype(int)
    res = {
        "n": int(len(y)), "threshold": round(float(threshold), 4),
        "accuracy": accuracy_score(y, yhat),
        "precision": precision_score(y, yhat, zero_division=0),
        "recall": recall_score(y, yhat, zero_division=0),
        "macro_f1": f1_score(y, yhat, average="macro", zero_division=0),
        "auc": roc_auc_score(y, p),
        "average_precision": average_precision_score(y, p),
        "confusion": confusion_matrix(y, yhat).tolist(),
    }
    bl = {}
    if "expansion_level" in eval_df.columns:
        lvl_series = eval_df["expansion_level"].values
        for lvl in ["SEED", "ANTISEED-manual", "ANTISEED-AF"]:
            m = (lvl_series == lvl)
            if m.sum() == 0:
                continue
            if lvl == "SEED":
                bl[lvl] = {"n": int(m.sum()), "recall(TP rate)": recall_score(y[m], yhat[m], zero_division=0)}
            else:
                bl[lvl] = {"n": int(m.sum()), "specificity(TN rate)": float((yhat[m] == 0).mean())}
        # threshold-free discrimination of SEED against EACH negative type separately.
        # SEED vs ANTISEED-manual = the hard automate-vs-assist boundary (the crux).
        seed_m = (lvl_series == "SEED")
        for neg_lvl, key in [("ANTISEED-manual", "auc_seed_vs_hard"), ("ANTISEED-AF", "auc_seed_vs_easy")]:
            sub = seed_m | (lvl_series == neg_lvl)
            if seed_m.sum() and (lvl_series == neg_lvl).sum():
                res[key] = roc_auc_score(y[sub], p[sub])
    res["by_expansion_level"] = bl
    return res


def evaluate(model_dir: str, eval_df: pd.DataFrame, threshold: float = 0.5,
             max_len: int = 256) -> dict:
    y = eval_df["label"].astype(int).values
    p = predict_proba(model_dir, eval_df["text"].tolist(), max_len=max_len)
    return report_from_probs(y, p, eval_df, threshold)


def print_report(res: dict, arm: str = ""):
    print(f"\n=== EVAL {arm} (n={res['n']}, thr={res.get('threshold')}) ===")
    for k in ["accuracy", "precision", "recall", "macro_f1", "auc", "average_precision",
              "auc_seed_vs_hard", "auc_seed_vs_easy"]:
        if k in res:
            print(f"  {k:18s}: {res[k]:.4f}")
    print(f"  confusion [[TN,FP],[FN,TP]]: {res['confusion']}")
    print("  by expansion_level:")
    for lvl, d in res["by_expansion_level"].items():
        extra = {k: round(v, 4) for k, v in d.items() if k != "n"}
        print(f"    {lvl:16s} (n={d['n']:4d}): {extra}")
