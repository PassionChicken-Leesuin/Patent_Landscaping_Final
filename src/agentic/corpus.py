"""[3] Corpus-reading agent: the judge pool's ACTUAL text is read, batch by batch.

Map: every patent (title + truncated abstract) is read in batches -> per-batch
digest (clusters, recurring vocabulary, borderline examples).
Reduce: all batch digests + the web-evidence summary -> one CorpusDigestOut that
explicitly compares the collected materials against what is really in the pool
(mismatch_with_web_evidence). Cached to corpus_digest.json.
"""
from __future__ import annotations
import json

import pandas as pd

from src.mas.llm import StructuredLLM, Usage
from src.agentic import config as AC
from src.agentic.schemas import CorpusBatchDigestOut, CorpusDigestOut
from src.agentic.workspace import Workspace

_MAP_SYSTEM = (
    "You are the Corpus-Reading agent of a patent-landscaping system.\n"
    "You are given a batch of REAL patents (title + abstract) from the pool that will later "
    "be judged for membership in the domain: {domain}.\n"
    "Read every patent and report:\n"
    "- clusters: the main technical clusters present in THIS batch (short phrases).\n"
    "- recurring_terms: domain vocabulary that actually recurs in these patents.\n"
    "- boundary_examples: patents that look BORDERLINE for the domain (mention its vocabulary "
    "but may not perform its defining task) — format each as 'title — why it is borderline'.\n"
    "Ground everything in the given texts only. Output JSON only."
)

_REDUCE_SYSTEM = (
    "You are the Corpus-Synthesis agent. You receive (a) per-batch digests covering the ENTIRE "
    "patent pool to be judged for the domain: {domain}, and (b) a summary of externally "
    "collected web evidence about the domain.\n"
    "Synthesize:\n"
    "- main_clusters: the pool's main technical clusters (merged across batches).\n"
    "- vocabulary_profile: the vocabulary that actually characterizes the pool.\n"
    "- representative_cases: typical clearly-in-domain patent examples (titles).\n"
    "- suspected_boundary_cases: the recurring KINDS of borderline patents, each as a full "
    "sentence citing an example title.\n"
    "- mismatch_with_web_evidence: where the pool's reality differs from the web evidence "
    "(e.g. tasks the evidence emphasizes but the pool rarely shows, look-alike clusters the "
    "evidence never mentioned) — these drive extra judgment criteria.\n"
    "Output JSON only."
)


def _batch_text(batch: pd.DataFrame) -> str:
    lines = []
    for _, r in batch.iterrows():
        title = str(r.get("title", ""))[:200]
        abstract = str(r.get("abstract", ""))[:AC.CORPUS_ABSTRACT_CHARS]
        lines.append(f"- {title} :: {abstract}")
    return "\n".join(lines)


def read_corpus(ws: Workspace, llm: StructuredLLM, pool_df: pd.DataFrame,
                domain: str, evidence_summary: str, usage: Usage,
                force: bool = False, llm_map: StructuredLLM | None = None) -> CorpusDigestOut:
    """llm_map (cheap model) reads the batches; llm (strong) does the synthesis."""
    if ws.corpus_digest_json.exists() and not force:
        return CorpusDigestOut(**ws.read_json(ws.corpus_digest_json))
    llm_map = llm_map or llm

    n = len(pool_df)
    batches = [pool_df.iloc[i:i + AC.CORPUS_BATCH_SIZE]
               for i in range(0, n, AC.CORPUS_BATCH_SIZE)][:AC.CORPUS_MAX_BATCHES]
    if len(batches) * AC.CORPUS_BATCH_SIZE < n:
        print(f"  [corpus] cap: reading first {len(batches) * AC.CORPUS_BATCH_SIZE}/{n} patents")

    digests: list[dict] = []
    skipped = 0
    for i, b in enumerate(batches, 1):
        try:
            out, pt, ct = llm_map.parse(_MAP_SYSTEM.format(domain=domain),
                                        f"Batch {i}/{len(batches)} ({len(b)} patents):\n{_batch_text(b)}",
                                        CorpusBatchDigestOut)
        except Exception as e:  # noqa: BLE001 — e.g. LengthFinishReasonError (runaway output)
            skipped += 1
            print(f"  [corpus] batch {i}/{len(batches)} skipped ({type(e).__name__})")
            continue
        usage.add(pt, ct)
        digests.append(out.model_dump())
        if i % 10 == 0 or i == len(batches):
            print(f"  [corpus] read {i}/{len(batches)} batches")
    if skipped:
        print(f"  [corpus] WARNING: {skipped} batch(es) skipped — digest covers the rest")
    if not digests:
        raise RuntimeError("corpus reading failed for every batch")

    user = (f"Per-batch digests ({len(digests)} batches, {n} patents total):\n"
            f"{json.dumps(digests, ensure_ascii=False)}\n\n"
            f"Web evidence summary:\n{evidence_summary}")
    final, pt, ct = llm.parse(_REDUCE_SYSTEM.format(domain=domain), user, CorpusDigestOut)
    usage.add(pt, ct)

    ws.write_json(ws.corpus_digest_json, final.model_dump())
    return final
