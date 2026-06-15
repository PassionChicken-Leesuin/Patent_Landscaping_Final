"""Collect an expanded autonomous-driving candidate pool from PatentsView USPTO bulk.

Search query = (CPC in the autonomous-driving landscape) AND (title+abstract contains
an autonomous-driving keyword). The CPC net targets the gold SEED subtopics, especially
the ones our current pool under-covers (cruise control, ADAS, lane, V2X, autonomous
aviation); the keyword intersection enforces text similarity to the gold set and strips
off-topic CPC noise.

Usage:
  python scripts/collect_expanded_pool.py --bulk "C:/.../Patent_Bulk" --out DataSet/expanded

Streams three TSVs (cpc 2GB, patent 1.1GB, abstract 6.2GB) once each (~3 min).
"""
from __future__ import annotations
import argparse
import csv
import re
import sys
import time
from pathlib import Path
from collections import defaultdict

# ---------------- search query (Bergeaud & Verluise S2 Appendix, Self-Driving Vehicle) ----------------
# Official CPC list used by the gold-set authors to select candidates. Matched by
# cpc_group startswith. We follow their list verbatim for fidelity to the gold definition.
CPC_PREFIXES = sorted(set("""
G08G1/02 G08G1/0967 G08G1/0968 G08G1/00 G08G1/01 G08G1/09 G08G1/127 G08G1/16 G08G1/164 G08G1/20 G08G1/161 G08G1/22
G01S7/003 G01S7/00 G01S7/02 G01S7/52 G01S7/48
G07B15/063
G07C5/00 G07C5/12 G07C5/01 G07C5/02 G07C5/03 G07C5/04 G07C5/05 G07C5/06 G07C5/07 G07C5/08
E01F E01F9/00 E01F9/40
H04W36/00 H04W76/50 H04W4/44 H04W4/46
B61L3/00 B61L25/00
G05D1/0011 G05D1/0027 G05D1/0287 G05D1/0297 G05D1/00 G05D1/0257 G05D1/0088 G05D1/021 G05D1/0212 G05D1/0276 G05D1/02
G01S13/93 G01S13/00 G01S13/86 G01S13/87 G01S13/931
G01S15/88 G01S15/93 G01S15/00 G01S15/025 G01S15/87 G01S15/931
G01S17/88 G01S17/93 G01S17/00 G01S17/023 G01S17/06 G01S17/87 G01S17/936
G06K9/00 G06K9/00362 G06K9/00785 G06K9/00791
B60L2240/70 B60L2240/60 B60L2240/62
B60W2420/52 B60W2420/42 B60W30/16 B60W2050/008 B60W2550/402 B60W2550/408 B60W30/00 B60W40/00 B60W30/095 B60W50/0097
B60Y2400/3017 B60Y2400/3015
B60R19/00 G01S2013/9332 G06T1/0007 G06T1/0014 G06T1/20 H04N5/335 B60S1/56
G01C21/00 G01C21/26 G01C21/34
F16D2500/31 F16D2500/508
B60G17/015 B60G17/016 B60G17/0195 B60G2800/00 B60K28/04 G05D2201/0212
""".split()))
CPC_TARGETS = {"bergeaud_sdv": CPC_PREFIXES}
ALL_PREFIXES = [("bergeaud_sdv", p) for p in CPC_PREFIXES]

# Official keyword list (>=1 must appear in title+abstract). We intersect CPC AND keyword
# to keep the pool tractable and gold-text-similar (Bergeaud's union over all rules is ~137k).
KEYWORDS = [
    "self-driving vehicle", "autopilot", "driverless vehicle", "autonomous vehicle",
    "automated vehicle", "vehicle connectivity", "vehicle-to-vehicle communication",
    "fleet management", "vehicle lidar", "vehicle sonar", "vehicle radar", "vehicle camera",
    "object detection", "obstacle detection", "object classification", "cruise control",
    "pedestrian detection", "environment mapping", "surround view", "blind spot detection",
    "park assistance", "lane departure", "traffic sign recognition", "drive assist system",
    "trajectory generation", "reactive control", "path trajectory planning", "manoeuvres planning",
]
KW_RE = re.compile("|".join(re.escape(k) for k in KEYWORDS), re.I)


def _q(s: str) -> str:
    return s.strip().strip('"')


def stream_cpc(path: Path):
    """patent_id -> set of matched subtopics (only for CPC-matching patents)."""
    matched: dict[str, set] = defaultdict(set)
    pref_tuple = tuple(CPC_PREFIXES)                 # C-optimized multi-prefix startswith
    t0 = time.time(); n = 0
    with open(path, encoding="utf-8") as f:
        f.readline()
        for line in f:
            n += 1
            p = line.rstrip("\n").split("\t")
            if len(p) < 7:
                continue
            if _q(p[6]).startswith(pref_tuple):
                matched[_q(p[0])].add("bergeaud_sdv")
    print(f"  cpc: scanned {n:,} rows in {time.time()-t0:.0f}s -> {len(matched):,} CPC-matched patents", flush=True)
    return matched


def stream_titles(path: Path, ids: set):
    out = {}
    t0 = time.time()
    with open(path, encoding="utf-8") as f:
        f.readline()
        for line in f:
            p = line.rstrip("\n").split("\t")
            if len(p) < 4:
                continue
            pid = _q(p[0])
            if pid in ids:
                out[pid] = {"title": _q(p[3]), "date": _q(p[2])}
    print(f"  patent: titles for {len(out):,} ids in {time.time()-t0:.0f}s", flush=True)
    return out


def stream_abstracts(path: Path, ids: set):
    out = {}
    t0 = time.time()
    with open(path, encoding="utf-8") as f:
        f.readline()
        for line in f:
            p = line.rstrip("\n").split("\t", 1)
            if len(p) < 2:
                continue
            pid = _q(p[0])
            if pid in ids:
                out[pid] = _q(p[1])
    print(f"  abstract: abstracts for {len(out):,} ids in {time.time()-t0:.0f}s", flush=True)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bulk", required=True, help="Patent_Bulk dir with g_*.tsv")
    ap.add_argument("--out", default="DataSet/expanded")
    args = ap.parse_args()
    bulk = Path(args.bulk)
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)

    print("[1/4] CPC filter ...", flush=True)
    cpc = stream_cpc(bulk / "g_cpc_at_issue.tsv")
    ids = set(cpc)

    print("[2/4] titles ...", flush=True)
    titles = stream_titles(bulk / "g_patent.tsv", ids)
    print("[3/4] abstracts ...", flush=True)
    abstracts = stream_abstracts(bulk / "g_patent_abstract.tsv", ids)

    print("[4/4] keyword intersection + write ...", flush=True)
    rows = []
    sub_counts = defaultdict(int)
    for pid in ids:
        title = titles.get(pid, {}).get("title", "")
        date = titles.get(pid, {}).get("date", "")
        abstract = abstracts.get(pid, "")
        text = f"{title}. {abstract}"
        if not KW_RE.search(text):          # keyword intersection
            continue
        subs = ";".join(sorted(cpc[pid]))
        rows.append({"patent_id": pid, "Patent_title": title, "Patent_abstract": abstract,
                     "date": date, "matched_subtopics": subs})
        for s in cpc[pid]:
            sub_counts[s] += 1

    raw = out / "expanded_candidates_raw.csv"
    with open(raw, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["patent_id", "Patent_title", "Patent_abstract", "date", "matched_subtopics"])
        w.writeheader(); w.writerows(rows)

    print(f"\nCPC-matched: {len(ids):,}  ->  after keyword intersection: {len(rows):,}")
    print("by subtopic (CPC, among kept):")
    for s in CPC_TARGETS:
        print(f"  {s:18s} {sub_counts[s]:>8,}")
    print(f"\nsaved -> {raw}")


if __name__ == "__main__":
    main()
