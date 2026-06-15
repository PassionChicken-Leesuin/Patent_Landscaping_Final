"""SciBERT fine-tuning (shared by both arms). Requires torch + transformers (Colab/GPU).

Held identical across arms — only the input train_df (label source) changes.
"""
from __future__ import annotations
from dataclasses import dataclass

import numpy as np
import pandas as pd

MODEL_NAME = "allenai/scibert_scivocab_uncased"


@dataclass
class TrainCfg:
    model_name: str = MODEL_NAME
    max_len: int = 256          # title+abstract (~150-200 tok); baseline used 128 (tech-field)
    epochs: int = 4
    lr: float = 2e-5            # standard BERT FT; baseline tuned 5e-7 for its data
    batch_size: int = 16
    weight_decay: float = 0.01
    warmup_ratio: float = 0.1
    val_frac: float = 0.1
    class_weight: bool = True   # safety against residual imbalance
    seed: int = 42


def _compute_metrics(eval_pred):
    """Per-epoch validation accuracy + macro-F1 (so we get baseline-style curves)."""
    from sklearn.metrics import accuracy_score, f1_score
    logits, labels = eval_pred
    preds = logits.argmax(-1)
    return {"accuracy": accuracy_score(labels, preds),
            "f1_macro": f1_score(labels, preds, average="macro", zero_division=0)}


def _datasets(train_df, tok, cfg):
    from datasets import Dataset
    df = train_df.sample(frac=1.0, random_state=cfg.seed).reset_index(drop=True)
    n_val = int(len(df) * cfg.val_frac)
    val_df, tr_df = df.iloc[:n_val], df.iloc[n_val:]

    def enc(batch):
        return tok(batch["text"], truncation=True, max_length=cfg.max_len, padding=False)

    ds_tr = Dataset.from_pandas(tr_df[["text", "label"]], preserve_index=False).map(enc, batched=True)
    ds_val = Dataset.from_pandas(val_df[["text", "label"]], preserve_index=False).map(enc, batched=True)
    return ds_tr, ds_val


def train(train_df: pd.DataFrame, out_dir: str, cfg: TrainCfg = TrainCfg()):
    import torch
    from torch import nn
    from transformers import (AutoTokenizer, AutoModelForSequenceClassification,
                              TrainingArguments, Trainer, DataCollatorWithPadding)

    tok = AutoTokenizer.from_pretrained(cfg.model_name)
    model = AutoModelForSequenceClassification.from_pretrained(cfg.model_name, num_labels=2)
    ds_tr, ds_val = _datasets(train_df, tok, cfg)

    # class weights (inverse frequency)
    cw = None
    if cfg.class_weight:
        y = train_df["label"].astype(int).values
        freq = np.bincount(y, minlength=2)
        w = freq.sum() / (2 * np.maximum(freq, 1))
        cw = torch.tensor(w, dtype=torch.float)

    class WeightedTrainer(Trainer):
        def compute_loss(self, model, inputs, return_outputs=False, **kw):
            labels = inputs.pop("labels")
            out = model(**inputs)
            loss = nn.functional.cross_entropy(
                out.logits, labels,
                weight=cw.to(out.logits.device) if cw is not None else None)
            return (loss, out) if return_outputs else loss

    args = TrainingArguments(
        output_dir=out_dir, num_train_epochs=cfg.epochs,
        per_device_train_batch_size=cfg.batch_size, per_device_eval_batch_size=32,
        learning_rate=cfg.lr, weight_decay=cfg.weight_decay, warmup_ratio=cfg.warmup_ratio,
        eval_strategy="epoch", save_strategy="epoch", load_best_model_at_end=True,
        metric_for_best_model="eval_loss", greater_is_better=False,
        logging_steps=50, seed=cfg.seed, report_to="none",
    )
    import inspect
    tk = dict(model=model, args=args, train_dataset=ds_tr, eval_dataset=ds_val,
              data_collator=DataCollatorWithPadding(tok), compute_metrics=_compute_metrics)
    # `tokenizer` was renamed to `processing_class` in recent transformers
    if "processing_class" in inspect.signature(Trainer.__init__).parameters:
        tk["processing_class"] = tok
    else:
        tk["tokenizer"] = tok
    trainer = WeightedTrainer(**tk)
    trainer.train()
    trainer.save_model(out_dir)
    tok.save_pretrained(out_dir)

    # save the full log history (train loss per step + val loss/acc/F1 per epoch)
    import json, os, dataclasses
    with open(os.path.join(out_dir, "history.json"), "w", encoding="utf-8") as f:
        json.dump(trainer.state.log_history, f, indent=2)
    # save the exact hyperparameters used (reproducibility)
    with open(os.path.join(out_dir, "train_config.json"), "w", encoding="utf-8") as f:
        json.dump(dataclasses.asdict(cfg), f, indent=2)
    return out_dir
