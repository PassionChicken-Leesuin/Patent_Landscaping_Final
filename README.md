# Patent Landscaping — Snorkel vs MAS (weak supervision comparison)

We reproduce the patent-identification framework of Sofean (2026, *World Patent
Information*) and replace its **Snorkel** weak-supervision step with a
**Multi-Agent System (MAS)**. The research question: *does MAS pseudo-labeling
beat Snorkel labeling functions when everything downstream is held fixed?*

## Task & data (single domain: autonomous driving)

Binary classification: **SEED (domain-relevant) vs NOT_SEED**. Input = **Title +
Abstract** (we deliberately skip the technical-field segmentation of the baseline).

| File | Role | Labels? |
|---|---|---|
| `DataSet/Training_Set.csv` (6,195) | **candidate pool** (positives) — labeled by Snorkel OR MAS | none (`patent_id`, title, abstract) |
| `DataSet/학습용 음성/*.csv` (5 files, 6,296) | **out-of-domain negatives** (5 other Bergeaud domains) — anti-seed, NOT_SEED | per-domain seed labels (we treat all as NOT_SEED) |
| `DataSet/Evaluation_Set.csv` (1,208) | **gold benchmark** — test only, never seen by the labelers | `cats.SEED` (313 SEED / 895 NOT_SEED) |

The candidate pool is ~84% autonomous-driving (positive-dominated), so negatives are
scarce in-pool. We supply them from 5 **other** domains (blockchain, computer vision,
genome editing, hydrogen storage, additive manufacturing) as out-of-domain anti-seed —
the same trick the baseline used (blood-plasma negatives). `computervision` is tagged a
**hard negative** (it overlaps autonomous-driving perception).

Eval negatives come in two flavors: `ANTISEED-manual` (hard negatives, vehicle
domain but not the target tech) and `ANTISEED-AF` (easy/random negatives).
Positive rate is **25.9% → report Macro-F1 / Precision / Recall / AUC, not just accuracy.**

## Controlled-variable design

Only the **labeler** changes; everything downstream is identical.

```
            ┌─ Arm A: Snorkel (LFs + LabelModel) ─┐
candidate ──┤                                      ├─► SciBERT fine-tune ─► eval on gold
  pool      └─ Arm B: MAS (LangGraph agents) ──────┘        (fixed)         (fixed metrics)
```
(Optional Arm C: in-context learning, as in the baseline paper.)

## ⚠️ Leakage (handled)

Eval and Training use different id schemes (`family_id` vs `patent_id`), so id
overlap is meaningless. On **abstract text** (token Jaccard ≥ 0.7) we found **56
training patents that duplicate eval gold** — 51 are SEED (= **16.3% of all
positives**). These are dropped from the candidate pool (6,195 → 6,139); the gold
set is left untouched. List: `DataSet/leakage/leaked_train_patent_ids.csv`.

## Training set assembled per arm (shared negatives)

```
positives    = candidate-pool rows the arm labeled SEED            (Snorkel vs MAS differ here)
in-pool negs = candidate-pool rows the arm labeled NOT_SEED/hard   (MAS mines more/better)
out-of-domain= 6,296 negatives from 5 other domains (FIXED, shared by both arms)
```
Only the labeler changes; the negative pool, SciBERT recipe, eval, and metrics are identical.

## Layout

```
src/
  config.py            paths, columns, constants
  data_pipeline.py     load / preprocess / leakage-dedup / negative-pool / save
  mas/                 MAS arm (LangGraph design, 10-key parallel OpenAI runner)
  snorkel_arm/         labeling functions + LabelModel pipeline + local LF analyzer
  downstream/          build_trainset (shared) + SciBERT train + eval (Macro-F1/AUC + by-level)
scripts/
  build_dataset.py     pipeline + EDA            ->  python -m scripts.build_dataset
  analyze_lfs.py       local LF coverage (no snorkel)
  run_mas.py           MAS labeling (10 keys)    ->  python -m scripts.run_mas
  run_snorkel.py       Snorkel labeling (Colab)
  run_downstream.py    assemble+train+eval one arm (Colab)
notebooks/
  colab_experiment.ipynb   Colab GPU side (Snorkel + both arms' SciBERT)
DataSet/
  processed/           training_clean.csv, eval_processed.csv, negatives_pool.csv
  leakage/             leaked_train_patent_ids.csv
MAS_LangGraph_구현스펙_v1.md   MAS spec (v1)
MAS_implementation_v2.md      MAS v2 delta (single-domain, 10-key, local-runnable)
```

## Run order

```
# LOCAL (.venv, Python 3.14 — no GPU)
python -m scripts.build_dataset          # dedup + negative pool
python -m scripts.run_mas --workers 40   # MAS labels the pool with 10 keys -> mas_ranked_scores.csv

# COLAB (GPU) — notebooks/colab_experiment.ipynb
#   run_snorkel  -> snorkel_labeled_pool.csv
#   run_downstream --arm snorkel ; --arm mas   -> metrics_{arm}.json
```

## Environment

- **Local** (this machine): no GPU, Python 3.14 → use only for code, EDA, dedup, git.
- **Training** (SciBERT) and **Snorkel labeling**: run on **Google Colab (free T4)**
  or Kaggle with Python 3.10/3.11. SciBERT fine-tune of ~6k examples ≈ 20–40 min on a T4.
  We keep SciBERT as the fixed downstream model (do **not** switch to API fine-tuning —
  it would confound the Snorkel-vs-MAS comparison).

## Run

```bash
pip install pandas numpy
python -m scripts.build_dataset
```
