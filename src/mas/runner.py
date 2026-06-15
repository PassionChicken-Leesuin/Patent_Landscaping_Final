"""Parallel batch runner — 10 OpenAI keys round-robined for max throughput.

* One client pair (fast, strong) per key.
* ThreadPoolExecutor: many patents in flight; each task assigned a key by
  round-robin, with key rotation + exponential backoff on rate-limit / transient
  errors.
* Thread-safe audit JSONL; per-key + aggregate usage/cost; Stage D ranked CSV.
"""
from __future__ import annotations
import json
import random
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from src.mas import config as MC
from src.mas.llm import OpenAIStructuredLLM, StructuredLLM, Usage
from src.mas.nodes import process_patent


# ----------------------------------------------------------------- key pool
class KeyPool:
    def __init__(self, keys: list[str], model_fast: str, model_strong: str,
                 temperature: float = 0.0):
        if not keys:
            raise ValueError("no OpenAI keys found (.env OPENAI_API_KEY_1..N)")
        self.clients: list[tuple[StructuredLLM, StructuredLLM]] = []
        for k in keys:
            fast = OpenAIStructuredLLM(api_key=k, model=model_fast, temperature=temperature)
            strong = (fast if model_strong == model_fast
                      else OpenAIStructuredLLM(api_key=k, model=model_strong, temperature=temperature))
            self.clients.append((fast, strong))
        self.n = len(self.clients)
        self.per_key_usage = [Usage() for _ in range(self.n)]

    @classmethod
    def mock(cls, n: int = 3) -> "KeyPool":
        from src.mas.llm import MockStructuredLLM
        self = cls.__new__(cls)
        m = MockStructuredLLM()
        self.clients = [(m, m) for _ in range(n)]
        self.n = n
        self.per_key_usage = [Usage() for _ in range(n)]
        return self


def _is_retryable(exc: Exception) -> bool:
    try:
        import openai
        return isinstance(exc, (openai.RateLimitError, openai.APITimeoutError,
                                openai.APIConnectionError, openai.InternalServerError))
    except Exception:
        return False


def _backoff(attempt: int, base: float = 1.5, cap: float = 30.0) -> float:
    return min(cap, base * (2 ** attempt)) + random.uniform(0, 0.75)


# ----------------------------------------------------------------- driver
def run_pool(rows: list[dict], rubric: dict, pool: KeyPool,
             workers: int = 40, max_attempts: int = 6,
             audit_path=MC.AUDIT_JSONL, log_every: int = 200, append: bool = False) -> dict:
    MC.MAS_OUT_DIR.mkdir(parents=True, exist_ok=True)
    lock = threading.Lock()
    agg = Usage()
    results: list[dict] = []
    failures: list[dict] = []
    t0 = time.time()
    audit_f = open(audit_path, "a" if append else "w", encoding="utf-8")

    def work(idx: int, row: dict):
        state0 = {
            "record_id": row["record_id"], "patent_id": row.get("patent_id", ""),
            "domain": row.get("domain", MC.DOMAIN),
            "title": row["title"], "abstract": row["abstract"], "rubric": rubric,
        }
        last_err = None
        for attempt in range(max_attempts):
            key_idx = (idx + attempt) % pool.n
            fast, strong = pool.clients[key_idx]
            u = Usage()
            try:
                res = process_patent(state0, fast, strong, u)
                with lock:
                    pool.per_key_usage[key_idx].merge(u)
                    agg.merge(u)
                return res
            except Exception as e:  # noqa: BLE001
                last_err = e
                if _is_retryable(e) and attempt < max_attempts - 1:
                    time.sleep(_backoff(attempt))
                    continue
                if attempt < max_attempts - 1:        # non-retryable: try next key once
                    time.sleep(0.3)
                    continue
        return {"_error": repr(last_err), "record_id": row["record_id"]}

    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(work, i, r): i for i, r in enumerate(rows)}
        done = 0
        for fut in as_completed(futs):
            res = fut.result()
            done += 1
            with lock:
                if res.get("_error"):
                    failures.append(res)
                else:
                    audit_f.write(json.dumps(_audit_view(res), ensure_ascii=False) + "\n")
                    results.append(_slim(res))
            if done % log_every == 0 or done == len(rows):
                el = time.time() - t0
                print(f"[{done}/{len(rows)}] {el:5.0f}s  calls={agg.calls}  "
                      f"~${agg.cost_usd():.3f}  fail={len(failures)}  "
                      f"rate={done/el:.1f}/s", flush=True)

    audit_f.close()
    return {"results": results, "failures": failures, "usage": agg, "pool": pool,
            "elapsed_s": time.time() - t0}


def _audit_view(res: dict) -> dict:
    keep = ("record_id", "patent_id", "domain", "route", "core_stance", "core_score",
            "exclusion_stance", "exclusion_risk", "confusable_category",
            "final_score", "candidate_type", "functional_evidence", "technical_evidence")
    return {k: res.get(k) for k in keep}


def _slim(res: dict) -> dict:
    return {k: res.get(k) for k in
            ("record_id", "patent_id", "domain", "title", "abstract",
             "final_score", "candidate_type", "route")}


# ----------------------------------------------------------------- Stage D
def write_ranked_csv(results: list[dict], path=MC.RANKED_CSV) -> str:
    import csv
    by_dom: dict[str, list[dict]] = {}
    for r in results:
        by_dom.setdefault(r.get("domain", MC.DOMAIN), []).append(r)
    rows = []
    for dom, items in by_dom.items():
        items.sort(key=lambda r: r.get("final_score", 0.0), reverse=True)
        for i, r in enumerate(items, 1):
            rows.append({
                "rank": i, "score": r.get("final_score"),
                "record_id": r["record_id"], "patent_id": r.get("patent_id", ""),
                "domain": dom, "title": r.get("title", ""),
                "abstract": r.get("abstract", ""), "candidate_type": r.get("candidate_type"),
                "source": r.get("source", ""),
            })
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["rank", "score", "record_id", "patent_id",
                                          "domain", "title", "abstract", "candidate_type", "source"])
        w.writeheader()
        w.writerows(rows)
    return str(path)
