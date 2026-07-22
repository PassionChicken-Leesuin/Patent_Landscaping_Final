"""Decode Korean PDFs whose fonts have broken/missing ToUnicode CMaps.

Some HWP-exported PDFs (e.g. KIMM policy reports) embed subset fonts whose
extracted "unicode" is really the font's internal glyph index. Empirically the
glyph layout is: ASCII at a fixed shift (+0x1F) and the full 11,172 Hangul
syllable block contiguous in Unicode order at another fixed per-font shift.
We recover the shift per font by maximizing the number of characters that land
inside the Hangul syllable block, then decode span-by-span.

Usage:
    python -m scripts.decode_cid_pdf --input <pdf> --output <txt>
"""
from __future__ import annotations
import argparse
import collections
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import fitz

HANGUL_LO, HANGUL_HI = 0xAC00, 0xD7A3
ASCII_SHIFT = 0x1F          # glyph 0x01..0x5E -> ' '..'}'


def collect_font_chars(doc) -> dict[str, collections.Counter]:
    font_chars: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    for page in doc:
        for b in page.get_text("rawdict")["blocks"]:
            for line in b.get("lines", []):
                for span in line["spans"]:
                    for ch in span["chars"]:
                        font_chars[span["font"]][ch["c"]] += 1
    return font_chars


def hangul_offset(cnt: collections.Counter) -> tuple[int, float]:
    """Best shift K putting the font's high (non-ASCII) chars into the Hangul
    block. Returns (K, coverage). K=0 means the text is already real Unicode."""
    high = {ord(c): n for c, n in cnt.items() if ord(c) > 0x80}
    if not high:
        return 0, 0.0
    total = sum(high.values())
    best_k, best_score = 0, sum(n for o, n in high.items() if HANGUL_LO <= o <= HANGUL_HI)
    # candidate shifts: those that map SOME observed char onto a Hangul syllable
    candidates = set()
    for o in list(high)[:400]:
        candidates.update((HANGUL_LO - o, HANGUL_HI - o))
    lo_k = min(candidates)
    hi_k = max(candidates)
    for k in range(lo_k, hi_k + 1):
        score = sum(n for o, n in high.items() if HANGUL_LO <= o + k <= HANGUL_HI)
        if score > best_score:
            best_score, best_k = score, k
    return best_k, best_score / total


def make_decoder(cnt: collections.Counter):
    k, cov = hangul_offset(cnt)
    if k == 0 or cov < 0.5:          # already-unicode font (or undecodable)
        return None, k, cov

    def dec(c: str) -> str:
        o = ord(c)
        if o > 0x80:
            m = o + k
            return chr(m) if HANGUL_LO <= m <= HANGUL_HI else ""
        if 0x01 <= o <= 0x5E:
            return chr(o + ASCII_SHIFT)
        return c
    return dec, k, cov


def decode_pdf(path: str) -> list[str]:
    doc = fitz.open(path)
    font_chars = collect_font_chars(doc)
    decoders = {}
    for font, cnt in font_chars.items():
        dec, k, cov = make_decoder(cnt)
        decoders[font] = dec
        print(f"  font {font!r}: chars={sum(cnt.values())} shift=+0x{k:04X} "
              f"hangul_cov={cov:.2f} -> {'decode' if dec else 'pass-through'}")

    pages = []
    for page in doc:
        out = []
        for b in page.get_text("rawdict")["blocks"]:
            for line in b.get("lines", []):
                for span in line["spans"]:
                    dec = decoders.get(span["font"])
                    for ch in span["chars"]:
                        out.append(dec(ch["c"]) if dec else ch["c"])
                out.append("\n")
            out.append("\n")
        pages.append("".join(out))
    return pages


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    pages = decode_pdf(args.input)
    text = "\n".join(f"[페이지 {i+1}]\n{p.strip()}" for i, p in enumerate(pages))
    Path(args.output).write_text(text, encoding="utf-8")
    print(f"decoded {len(pages)} pages -> {args.output} ({len(text):,} chars)")


if __name__ == "__main__":
    main()
