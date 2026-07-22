"""[2b] Local-document ingestion: user-supplied reference material (PDF/TXT/MD)
enters the research notes store through the SAME evidence-extraction agent as
web pages, so the criteria stage sees one uniform evidence pool.

OWNER DOCUMENTS ARE FIRST-CLASS. Unlike web pages, a --local-doc file was chosen
by the domain owner, so the benchmark-leak guard must never silently discard it:
 - the regex content scan fail-louds (raises) instead of silently skipping, with
   an explicit override (allow_flagged) for the case where the hit is intended;
 - the note-extraction LLM's page_is_benchmark_leak flag is advisory only
   (logged to blocked.jsonl, chunk kept) — it misfired on the A2 owner document
   in the 2026-07-19 run and cost the entire drafting round its anchor;
 - per-doc ingestion status (chunks / notes / flags + full text when short) is
   persisted to owner_docs.json so the criteria stage can inject short owner
   documents verbatim and the pipeline can warn when a document went unreflected.

Each document is chunked; every chunk gets a pseudo-URL `local://<name>#chunkN`
and is cached under research/pages/ exactly like a fetched web page, so re-runs
skip already-ingested chunks for free.

PDFs are read via scripts.decode_cid_pdf.decode_pdf, which transparently fixes
Korean PDFs with broken ToUnicode CMaps (HWP exports) and passes healthy fonts
through unchanged.
"""
from __future__ import annotations
from pathlib import Path

from src.mas.llm import StructuredLLM, Usage
from src.agentic import config as AC
from src.agentic import leakage as LK
from src.agentic.research import _NOTES_SYSTEM
from src.agentic.schemas import EvidenceNotesOut
from src.agentic.workspace import Workspace, url_hash

CHUNK_CHARS = 6000
CHUNK_OVERLAP = 300


class OwnerDocBlocked(RuntimeError):
    """An owner document hit the benchmark-leak content scan (fail-loud)."""


def _read_document(path: Path) -> str:
    if path.suffix.lower() == ".pdf":
        from scripts.decode_cid_pdf import decode_pdf
        pages = decode_pdf(str(path))
        return "\n".join(f"[페이지 {i + 1}]\n{p.strip()}" for i, p in enumerate(pages))
    return path.read_text(encoding="utf-8")


def _chunks(text: str) -> list[str]:
    text = "\n".join(line for line in text.splitlines() if line.strip())
    out = []
    start = 0
    while start < len(text):
        end = start + CHUNK_CHARS
        if end < len(text):  # cut at a line break so sentences stay whole
            nl = text.rfind("\n", start + CHUNK_CHARS // 2, end)
            if nl != -1:
                end = nl
        out.append(text[start:end])
        start = max(end - CHUNK_OVERLAP, start + 1)
        if end >= len(text):
            break
    return out


def _seen_chunk_urls(ws: Workspace) -> set[str]:
    urls = set()
    for p in ws.pages_dir.glob("*.json"):
        try:
            u = Workspace.read_json(p).get("url", "")
        except Exception:
            continue
        if u.startswith("local://"):
            urls.add(u)
    return urls


def _doc_note_count(ws: Workspace, doc_name: str) -> int:
    """Notes attributed to this document across ALL runs (chunk cache makes the
    per-run counter 0 on resume, so the store is the only honest count)."""
    if not ws.notes_jsonl.exists():
        return 0
    prefix = f"local://{doc_name}#"
    return sum(1 for n in ws.read_jsonl(ws.notes_jsonl)
               if str(n.get("source_url", "")).startswith(prefix))


def ingest_local_docs(ws: Workspace, llm: StructuredLLM, paths: list[str],
                      canonical_name: str, usage: Usage,
                      allow_flagged: bool = False) -> int:
    """Extract evidence notes from owner documents into notes.jsonl and persist
    per-doc status to owner_docs.json. Returns the number of notes appended this
    run. Idempotent per (doc, chunk). Raises OwnerDocBlocked when the leak scan
    hits and allow_flagged is False (never a silent skip)."""
    seen = _seen_chunk_urls(ws)
    total_notes = 0
    statuses = []
    for raw in paths:
        path = Path(raw)
        if not path.exists():
            raise FileNotFoundError(f"--local-doc not found: {path}")
        text = _read_document(path)
        chunks = _chunks(text)
        new = scan_hits = llm_flags = 0
        for i, chunk in enumerate(chunks):
            url = f"local://{path.name}#chunk{i}"
            if url in seen:
                continue
            blocked, hits = LK.content_leak_scan(chunk)
            if blocked:
                scan_hits += 1
                LK.log_block(ws.blocked_jsonl, {"layer": "content", "rule": hits,
                                                "url": url, "title": path.name,
                                                "intent_type": "local_document",
                                                "overridden": allow_flagged})
                if not allow_flagged:
                    raise OwnerDocBlocked(
                        f"[local-doc] 소유자 문서 '{path.name}' chunk {i + 1}/{len(chunks)}이 "
                        f"벤치마크 유출 스캔에 걸렸습니다 (rules: {hits}).\n"
                        f"  문서가 정말 평가 벤치마크를 인용한다면 빼고 재실행하세요. "
                        f"오탐이면 --local-doc-allow-flagged 로 재실행하면 그대로 반영됩니다. "
                        f"(소유자 문서는 조용히 버리지 않습니다 — 기록: {ws.blocked_jsonl})")
                print(f"  !! [local-doc] {path.name} chunk {i + 1}: leak-scan hit "
                      f"({hits}) — allow-flagged 로 강행 반영")
            user = (f"Domain: {canonical_name}\n"
                    f"Research intent: local_document — reference material supplied by the "
                    f"DOMAIN OWNER (authoritative source about the domain's intended scope)\n"
                    f"Page title: {path.name} (part {i + 1}/{len(chunks)})\n"
                    f"Page URL: {url}\n\nPage text:\n{chunk}")
            out, pt, ct = llm.parse(_NOTES_SYSTEM, user, EvidenceNotesOut)
            usage.add(pt, ct)
            if out.page_is_benchmark_leak:
                # advisory only for owner documents: log, warn, KEEP the chunk
                llm_flags += 1
                LK.log_block(ws.blocked_jsonl, {"layer": "llm_flag_advisory",
                                                "rule": "page_is_benchmark_leak",
                                                "url": url, "title": path.name,
                                                "intent_type": "local_document"})
                print(f"  !! [local-doc] {path.name} chunk {i + 1}: LLM이 벤치마크 유출을 "
                      f"의심했으나 소유자 문서이므로 반영합니다 (blocked.jsonl 확인)")
            h = url_hash(url)
            ws.write_json(ws.pages_dir / f"{h}.json",
                          {"url": url, "title": f"{path.name} (part {i + 1})",
                           "source": "local_document",
                           "intent_type": "local_document", "text": chunk})
            # owner-doc notes are kept even when the page_is_relevant heuristic
            # says no — relevance filtering is for anonymous web pages
            for note in out.notes:
                ws.append_jsonl(ws.notes_jsonl,
                                {**note.model_dump(), "source_url": url,
                                 "page_hash": h, "intent_type": "local_document"})
                new += 1
        n_notes = _doc_note_count(ws, path.name)
        full_text = text if len(text) <= AC.OWNER_DOC_FULLTEXT_MAX_CHARS else None
        statuses.append({"name": path.name, "path": str(path), "chars": len(text),
                         "chunks": len(chunks), "notes": n_notes,
                         "full_text_injected": full_text is not None,
                         "full_text": full_text,
                         "leak_scan_hits": scan_hits, "llm_leak_flags": llm_flags})
        inj = " + 원문 전체를 기준서 프롬프트에 주입" if full_text is not None else ""
        print(f"  [local-doc] {path.name}: {len(chunks)} chunks -> +{new} notes "
              f"(누적 {n_notes}){inj}")
        if n_notes == 0 and full_text is None:
            print(f"  !!!! [local-doc] 경고: 소유자 문서 '{path.name}'에서 노트가 0개이고 "
                  f"원문 주입 한도({AC.OWNER_DOC_FULLTEXT_MAX_CHARS}자)도 넘습니다 — "
                  f"이 문서는 기준서에 반영되지 않습니다. blocked.jsonl 을 확인하세요.")
        total_notes += new
    ws.write_json(ws.owner_docs_json, {"docs": statuses})
    return total_notes


def owner_docs_block(ws: Workspace) -> str:
    """Verbatim OWNER DOMAIN DEFINITION block for the criteria prompt (short docs
    only). Empty string when no owner doc qualifies."""
    if not ws.owner_docs_json.exists():
        return ""
    docs = Workspace.read_json(ws.owner_docs_json).get("docs", [])
    bodies = [f"--- {d['name']} ---\n{d['full_text']}"
              for d in docs if d.get("full_text")]
    if not bodies:
        return ""
    return ("\n=== OWNER DOMAIN DEFINITION (문서 원문 — 최상위 권위) ===\n"
            + "\n\n".join(bodies))


def unreflected_owner_docs(ws: Workspace) -> list[str]:
    """Owner documents that contributed zero notes AND were too long to inject
    verbatim — i.e. invisible to the criteria stage. Names, for warnings."""
    if not ws.owner_docs_json.exists():
        return []
    docs = Workspace.read_json(ws.owner_docs_json).get("docs", [])
    return [d["name"] for d in docs
            if not d.get("full_text") and _doc_note_count(ws, d["name"]) == 0]
