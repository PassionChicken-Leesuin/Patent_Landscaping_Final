"""Quick diagnostic: distribution shift between TRAIN labels and GOLD eval set.

No torch. Pure pandas + sklearn TF-IDF. Answers:
  1. Class balance the downstream model actually sees (per arm).
  2. Text-length / vocabulary distribution: train-positives vs gold-SEED vs gold-ANTISEED.
  3. Domain separability: can a TF-IDF LR tell train-pos from gold-SEED? (high AUC => they look different)
  4. Where do gold-SEED land in the arm's own scoring? (label-noise proxy)
"""
from __future__ import annotations
import re, numpy as np, pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / "DataSet"

eval_df  = pd.read_csv(D / "processed" / "eval_processed.csv")
train    = pd.read_csv(D / "processed" / "training_clean.csv")
negs     = pd.read_csv(D / "processed" / "negatives_pool.csv")
mas      = pd.read_csv(D / "mas" / "mas_ranked_scores.csv")

def words(s): return len(re.findall(r"\w+", str(s)))

print("=" * 70)
print("1) GOLD EVAL composition (the test set)")
print(eval_df["expansion_level"].value_counts())
print("  label balance:", dict(eval_df["label"].value_counts()))

print("=" * 70)
print("2) MAS labeling of the autonomous_driving pool (training source)")
print(mas["candidate_type"].value_counts())
n = len(mas)
pos = (mas["candidate_type"] == "positive").sum()
print(f"  -> pool positives: {pos}/{n} = {pos/n:.1%}")

print("=" * 70)
print("3) Text length (word count) by group")
seed   = eval_df[eval_df["expansion_level"] == "SEED"]["text"]
anti_m = eval_df[eval_df["expansion_level"] == "ANTISEED-manual"]["text"]
anti_a = eval_df[eval_df["expansion_level"] == "ANTISEED-AF"]["text"]
mas_pos_txt = mas[mas["candidate_type"] == "positive"]
mas_pos_txt = (mas_pos_txt["title"].fillna("") + ". " + mas_pos_txt["abstract"].fillna(""))
groups = {
    "TRAIN pool (all AD)": train["text"],
    "TRAIN MAS-positives": mas_pos_txt,
    "OOD negatives":       negs["text"],
    "GOLD SEED (pos)":     seed,
    "GOLD ANTISEED-manual":anti_m,
    "GOLD ANTISEED-AF":    anti_a,
}
for name, col in groups.items():
    wc = col.map(words)
    print(f"  {name:22s} n={len(col):5d}  words mean={wc.mean():6.1f} median={wc.median():6.0f}")

print("=" * 70)
print("4) Separability: TF-IDF LogReg, TRAIN-positives vs GOLD-SEED")
print("   (AUC ~0.5 => same distribution; AUC ~1.0 => clearly different sources)")
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_score

def sep_auc(a: pd.Series, b: pd.Series, label_a="A", label_b="B"):
    a = a.dropna().astype(str); b = b.dropna().astype(str)
    X = pd.concat([a, b], ignore_index=True)
    y = np.r_[np.ones(len(a)), np.zeros(len(b))]
    vec = TfidfVectorizer(max_features=20000, ngram_range=(1, 2), min_df=2)
    Xv = vec.fit_transform(X)
    auc = cross_val_score(LogisticRegression(max_iter=1000), Xv, y, cv=5, scoring="roc_auc")
    print(f"   {label_a} vs {label_b}: AUC = {auc.mean():.3f} ± {auc.std():.3f}")

sep_auc(mas_pos_txt, seed, "TRAIN MAS-pos", "GOLD SEED")
sep_auc(train["text"], seed, "TRAIN pool(all)", "GOLD SEED")
sep_auc(seed, anti_m, "GOLD SEED", "GOLD ANTISEED-manual")
sep_auc(train["text"], negs["text"], "TRAIN pool", "OOD negs (easy)")

print("=" * 70)
print("5) Vocabulary overlap (top-300 TF-IDF terms): train-pos vs gold-SEED vs gold-ANTISEED")
def top_terms(series, k=300):
    series = series.dropna().astype(str)
    vec = TfidfVectorizer(max_features=5000, ngram_range=(1, 1), min_df=2, stop_words="english")
    X = vec.fit_transform(series)
    scores = np.asarray(X.mean(axis=0)).ravel()
    terms = np.array(vec.get_feature_names_out())
    return set(terms[scores.argsort()[::-1][:k]])

t_pos  = top_terms(mas_pos_txt)
t_seed = top_terms(seed)
t_anti = top_terms(anti_m)
def jac(a, b): return len(a & b) / len(a | b)
print(f"   Jaccard(TRAIN-pos, GOLD-SEED)          = {jac(t_pos, t_seed):.3f}")
print(f"   Jaccard(GOLD-SEED, GOLD-ANTISEED-man)  = {jac(t_seed, t_anti):.3f}")
print(f"   Jaccard(TRAIN-pos, GOLD-ANTISEED-man)  = {jac(t_pos, t_anti):.3f}")
print("   GOLD-SEED terms missing from TRAIN-pos top300 (sample):")
print("   ", sorted(list(t_seed - t_pos))[:40])
