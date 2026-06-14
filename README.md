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
| `DataSet/Training_Set.csv` (6,195) | **candidate pool** — labeled by Snorkel OR MAS | none (`patent_id`, title, abstract) |
| `DataSet/Evaluation_Set.csv` (1,208) | **gold benchmark** — test only, never seen by the labelers | `cats.SEED` (313 SEED / 895 NOT_SEED) |

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

## Layout

```
src/
  config.py          paths, columns, constants
  data_pipeline.py   load / preprocess / leakage-dedup / save
scripts/
  build_dataset.py   run pipeline + print EDA   ->  python -m scripts.build_dataset
DataSet/
  processed/         training_clean.csv, eval_processed.csv   (pipeline output)
  leakage/           leaked_train_patent_ids.csv
MAS_LangGraph_구현스펙_v1.md   MAS design spec
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
