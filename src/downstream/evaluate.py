"""Evaluate a fine-tuned model on the gold eval set (shared by both arms).

Reports overall metrics (imbalanced -> Macro-F1/AUC primary) AND a breakdown by
expansion_level: SEED recall, ANTISEED-manual specificity (hard negatives),
ANTISEED-AF specificity (easy negatives). The hard-negative column is where the
Snorkel-vs-MAS difference should show.
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


def evaluate(model_dir: str, eval_df: pd.DataFrame, threshold: float = 0.5,
             max_len: int = 256) -> dict:
    from sklearn.metrics import (accuracy_score, precision_score, recall_score,
                                 f1_score, roc_auc_score, confusion_matrix)
    y = eval_df["label"].astype(int).values
    p = predict_proba(model_dir, eval_df["text"].tolist(), max_len=max_len)
    yhat = (p >= threshold).astype(int)

    res = {
        "n": len(y),
        "accuracy": accuracy_score(y, yhat),
        "precision": precision_score(y, yhat, zero_division=0),
        "recall": recall_score(y, yhat, zero_division=0),
        "macro_f1": f1_score(y, yhat, average="macro", zero_division=0),
        "auc": roc_auc_score(y, p),
        "confusion": confusion_matrix(y, yhat).tolist(),
    }

    # per expansion_level breakdown
    bl = {}
    if "expansion_level" in eval_df.columns:
        for lvl in ["SEED", "ANTISEED-manual", "ANTISEED-AF"]:
            m = eval_df["expansion_level"] == lvl
            if m.sum() == 0:
                continue
            yl, yhl = y[m.values], yhat[m.values]
            if lvl == "SEED":
                bl[lvl] = {"n": int(m.sum()), "recall(TP rate)": recall_score(yl, yhl, zero_division=0)}
            else:  # negatives: specificity = correctly predicted 0
                spec = float((yhl == 0).mean())
                bl[lvl] = {"n": int(m.sum()), "specificity(TN rate)": spec}
    res["by_expansion_level"] = bl
    return res


def print_report(res: dict, arm: str = ""):
    print(f"\n=== EVAL {arm} (n={res['n']}) ===")
    for k in ["accuracy", "precision", "recall", "macro_f1", "auc"]:
        print(f"  {k:10s}: {res[k]:.4f}")
    print(f"  confusion [[TN,FP],[FN,TP]]: {res['confusion']}")
    print("  by expansion_level:")
    for lvl, d in res["by_expansion_level"].items():
        extra = {k: round(v, 4) for k, v in d.items() if k != "n"}
        print(f"    {lvl:16s} (n={d['n']:4d}): {extra}")
