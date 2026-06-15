"""Training/validation curves, baseline-style (Sofean 2026, Fig 3/4).

Reads outputs/scibert_{arm}/history.json (saved by train()) and plots:
  - left : training loss + validation loss vs epoch
  - right: validation accuracy + macro-F1 vs epoch
"""
from __future__ import annotations
import json
from pathlib import Path


def load_history(arm: str, out_root: str = "outputs") -> list[dict]:
    with open(Path(out_root) / f"scibert_{arm}" / "history.json", encoding="utf-8") as f:
        return json.load(f)


def plot_history(arm: str, out_root: str = "outputs", show: bool = True):
    import matplotlib.pyplot as plt
    h = load_history(arm, out_root)

    train = [(e["epoch"], e["loss"]) for e in h if "loss" in e and "eval_loss" not in e]
    ev = [e for e in h if "eval_loss" in e]
    ep = [e["epoch"] for e in ev]

    fig, ax = plt.subplots(1, 2, figsize=(11, 4))
    if train:
        ax[0].plot([x for x, _ in train], [y for _, y in train], color="tab:blue", label="training loss")
    if ev:
        ax[0].plot(ep, [e["eval_loss"] for e in ev], color="tab:orange", marker="o", label="validation loss")
    ax[0].set_xlabel("epoch"); ax[0].set_ylabel("loss"); ax[0].set_title(f"{arm}: training & validation loss")
    ax[0].legend(); ax[0].grid(alpha=0.3)

    if ev:
        ax[1].plot(ep, [e.get("eval_accuracy") for e in ev], color="tab:green", marker="o", label="val accuracy")
        ax[1].plot(ep, [e.get("eval_f1_macro") for e in ev], color="tab:red", marker="s", label="val macro-F1")
    ax[1].set_xlabel("epoch"); ax[1].set_ylabel("score"); ax[1].set_title(f"{arm}: validation metrics")
    ax[1].legend(); ax[1].grid(alpha=0.3)

    plt.tight_layout()
    out_png = Path(out_root) / f"curves_{arm}.png"
    plt.savefig(out_png, dpi=120)
    if show:
        plt.show()
    return str(out_png)


def roc_pr(curves: dict, out_root: str = "outputs", show: bool = True):
    """curves = {arm: (y, p)}. Plot ROC + PR for all arms together (threshold-free)."""
    import matplotlib.pyplot as plt
    from sklearn.metrics import roc_curve, precision_recall_curve, auc, average_precision_score
    fig, ax = plt.subplots(1, 2, figsize=(11, 4.5))
    for arm, (y, p) in curves.items():
        fpr, tpr, _ = roc_curve(y, p)
        ax[0].plot(fpr, tpr, label=f"{arm} (AUC={auc(fpr, tpr):.3f})")
        prec, rec, _ = precision_recall_curve(y, p)
        ax[1].plot(rec, prec, label=f"{arm} (AP={average_precision_score(y, p):.3f})")
    ax[0].plot([0, 1], [0, 1], "k--", alpha=0.3)
    ax[0].set_xlabel("FPR"); ax[0].set_ylabel("TPR"); ax[0].set_title("ROC"); ax[0].legend(); ax[0].grid(alpha=0.3)
    ax[1].set_xlabel("recall"); ax[1].set_ylabel("precision"); ax[1].set_title("Precision-Recall")
    ax[1].legend(); ax[1].grid(alpha=0.3)
    plt.tight_layout()
    path = Path(out_root) / "roc_pr.png"
    plt.savefig(path, dpi=120)
    if show:
        plt.show()
    return str(path)


def score_hist(arm: str, y, p, out_root: str = "outputs", show: bool = True):
    """Histogram of P(SEED) for gold positives vs negatives — shows the threshold problem."""
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.hist(p[y == 1], bins=40, alpha=0.6, density=True, color="tab:green", label="SEED (gold +)")
    ax.hist(p[y == 0], bins=40, alpha=0.6, density=True, color="tab:red", label="NOT_SEED (gold -)")
    ax.axvline(0.5, color="k", ls="--", alpha=0.4, label="thr=0.5")
    ax.set_xlabel("P(SEED)"); ax.set_ylabel("density"); ax.set_title(f"{arm}: score distribution")
    ax.legend(); ax.grid(alpha=0.3)
    plt.tight_layout()
    path = Path(out_root) / f"scorehist_{arm}.png"
    plt.savefig(path, dpi=120)
    if show:
        plt.show()
    return str(path)
