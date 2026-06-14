"""Central configuration: paths, column names, constants.

Single-domain project (autonomous driving). Two CSVs are the whole dataset:
  - Training_Set.csv  : candidate pool (unlabeled) -> labeled by Snorkel OR MAS
  - Evaluation_Set.csv : gold benchmark (test only). NEVER fed to Snorkel/MAS.
"""
from pathlib import Path

# ---- paths ----
ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "DataSet"
PROCESSED_DIR = DATA_DIR / "processed"
LEAKAGE_DIR = DATA_DIR / "leakage"

TRAINING_CSV = DATA_DIR / "Training_Set.csv"
EVAL_CSV = DATA_DIR / "Evaluation_Set.csv"

# pipeline outputs
TRAINING_CLEAN_CSV = PROCESSED_DIR / "training_clean.csv"          # candidate pool, leakage removed
EVAL_PROCESSED_CSV = PROCESSED_DIR / "eval_processed.csv"          # gold, text split into title/abstract
LEAKED_IDS_CSV = LEAKAGE_DIR / "leaked_train_patent_ids.csv"       # patents to drop from training

# ---- domain ----
DOMAIN = "autonomous_driving"

# ---- raw column names ----
TRAIN_ID = "patent_id"
TRAIN_TITLE = "Patent_title"
TRAIN_ABSTRACT = "Patent_abstract"

EVAL_ID = "family_id"
EVAL_LEVEL = "expansion_level"          # SEED / ANTISEED-manual / ANTISEED-AF
EVAL_TEXT = "text"                       # 'Title\n\nAbstract'
EVAL_LABEL = "cats.SEED"                 # 1 = SEED (positive), 0 = NOT_SEED

# ---- leakage detection ----
LEAKAGE_JACCARD_THRESHOLD = 0.7          # abstract token-set Jaccard >= this => near-duplicate
MIN_TOKENS = 5                           # ignore ultra-short abstracts
