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
from src.agentic.schemas import (AlignmentOut, CorpusBatchDigestOut, CorpusDigestOut,
                                 CorpusReduceOut)
from src.agentic.workspace import Workspace

_MAP_SYSTEM = (
    "You are the Corpus-Reading agent of a patent-landscaping system.\n"
    "You are given a batch of REAL patents (title + abstract) from the pool that will later "
    "be judged for membership in the domain: {domain}.\n"
    "Read every patent and report:\n"
    "- clusters: the main technical clusters present in THIS batch (short phrases).\n"
    "- vocabulary: domain vocabulary that actually recurs in these patents.\n"
    "- boundary_examples: EVERY patent in this batch that looks BORDERLINE / look-alike for "
    "the domain (mentions its vocabulary but may not perform its defining task) — be exhaustive, "
    "not just one or two — format each as 'title — why it is borderline'.\n"
    "Ground everything in the given texts only. Output JSON only."
)

_REDUCE_SYSTEM = (
    "You are the Corpus-Synthesis agent. You receive per-batch digests covering the ENTIRE "
    "patent pool to be judged for the domain: {domain}.\n"
    "Synthesize (merged across batches, grounded in the digests only):\n"
    "- clusters: the pool's main technical clusters.\n"
    "- vocabulary: the vocabulary that actually characterizes the pool.\n"
    "- representative_examples: typical clearly-in-domain patent examples (titles).\n"
    "- boundary_examples: the recurring KINDS of borderline / look-alike patents — be "
    "EXHAUSTIVE, list every distinct look-alike kind the digests reveal (aim for 8-15, not "
    "just a few), each as a full sentence citing an example title. These become the pool's "
    "exclusion candidates, so missing one lets a look-alike leak into the positives.\n"
    "Output JSON only."
)

_ALIGN_SYSTEM = (
    "You are the Evidence-Alignment agent. You compare (a) external WEB EVIDENCE about the "
    "domain: {domain} against (b) what is ACTUALLY in the patent pool (POOL FINDINGS). "
    "Produce `alignment`: a list of comparison rows. For EACH genuine comparison output one "
    "row with:\n"
    "- dimension: what the comparison is about (definition/task/technique/signal_term/"
    "confusable/boundary/cpc_code/synonym).\n"
    "- relation: 'confirmed' (web says it AND pool shows it), 'web_only' (web emphasizes it "
    "but the pool rarely/never shows it), 'pool_only' (a pool cluster the web never mentioned "
    "— a likely look-alike), or 'conflict' (web and pool disagree on meaning).\n"
    "- web_refs: the web:<n> ids this row draws on (may be empty for pool_only).\n"
    "- pool_refs: the corpus:<kind>:<n> ids this row draws on (may be empty for web_only).\n"
    "- statement: one sentence describing the comparison.\n"
    "- implies: the criterion it motivates — 'inclusion' (confirmed core), 'exclusion' "
    "(pool_only/conflict look-alike to exclude), 'scope_boundary' (web_only; do not require), "
    "or 'none'.\n"
    "ACTIVELY HUNT LOOK-ALIKES (this is the precision lever, do not skip it): every POOL "
    "FINDING that is a corpus:boundary:* item, or a corpus:cluster:* that mentions the domain "
    "vocabulary but is NOT the domain's core task, or that matches something the evidence marks "
    "OUT of scope, MUST become a row with relation 'pool_only' (or 'conflict' if the evidence "
    "explicitly excludes it) and implies 'exclusion', citing that corpus id in pool_refs. Do "
    "NOT default everything to 'confirmed' — a pool with look-alikes should yield several "
    "pool_only exclusion rows.\n"
    "Cite ONLY the web:/corpus: ids given below; never invent ids. Leave `id` blank (it is "
    "stamped after you output). Output JSON only."
)


def _web_reference_ids(ws: Workspace) -> list[tuple[str, dict]]:
    """Assign stable citable ids web:1, web:2, ... to research notes (in file order)."""
    return [(f"web:{i}", n) for i, n in enumerate(ws.read_jsonl(ws.notes_jsonl), 1)]


def _pool_finding_ids(core: CorpusReduceOut) -> dict[str, str]:
    """Same id scheme as axes.corpus_reference_ids (cluster/case/boundary), from the core digest."""
    out: dict[str, str] = {}
    for kind, items in (("cluster", core.clusters), ("case", core.representative_examples),
                        ("boundary", core.boundary_examples)):
        for i, item in enumerate(items, 1):
            if str(item).strip():
                out[f"corpus:{kind}:{i}"] = str(item).strip()
    return out


def _batch_text(batch: pd.DataFrame) -> str:
    lines = []
    for _, r in batch.iterrows():
        title = str(r.get("title", ""))[:AC.CORPUS_TITLE_CHARS]
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

    # reduce-1: core digest (clusters / vocabulary / representative + boundary examples)
    user = (f"Per-batch digests ({len(digests)} batches, {n} patents total):\n"
            f"{json.dumps(digests, ensure_ascii=False)}")
    core, pt, ct = llm.parse(_REDUCE_SYSTEM.format(domain=domain), user, CorpusReduceOut)
    usage.add(pt, ct)

    # assign citable ids, then reduce-2: structured web<->pool alignment
    web_ids = _web_reference_ids(ws)
    pool_ids = _pool_finding_ids(core)
    web_block = "\n".join(
        f"- {wid} | {nd.get('evidence_type','?')} | {nd.get('claim','')}" for wid, nd in web_ids
    ) or "(no web evidence)"
    pool_block = "\n".join(f"- {pid} — \"{text}\"" for pid, text in sorted(pool_ids.items())) \
        or "(no pool findings)"
    align_user = (f"WEB EVIDENCE:\n{web_block}\n\nPOOL FINDINGS:\n{pool_block}")
    alignment = []
    if web_ids or pool_ids:
        try:
            al, apt, act = llm.parse(_ALIGN_SYSTEM.format(domain=domain), align_user, AlignmentOut)
            usage.add(apt, act)
            valid_ids = {w for w, _ in web_ids} | set(pool_ids)
            for i, a in enumerate(al.alignment, 1):
                a.id = f"align:{i}"                                  # stamp deterministically
                a.web_refs = [r for r in a.web_refs if r in valid_ids]   # drop invented ids
                a.pool_refs = [r for r in a.pool_refs if r in valid_ids]
            alignment = al.alignment
        except Exception as e:  # noqa: BLE001 — alignment is additive; never fail the pipeline on it
            print(f"  [corpus] alignment step skipped ({type(e).__name__})")

    # keep the deprecated free-text mismatch populated (relation != confirmed) so legacy
    # readers (axes corpus:mismatch ids, old UI) keep working until they migrate to `alignment`.
    mismatch = [a.statement for a in alignment if a.relation != "confirmed"]
    final = CorpusDigestOut(**core.model_dump(), alignment=alignment,
                            mismatch_with_web_evidence=mismatch)
    print(f"  [corpus] {len(alignment)} web<->pool alignment rows "
          f"({sum(1 for a in alignment if a.relation=='pool_only')} pool_only)")
    ws.write_json(ws.corpus_digest_json, final.model_dump())
    return final
