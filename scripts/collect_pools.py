"""Collect candidate pools for the 5 added domains in ONE pass over the PatentsView bulk.

Same query as collect_expanded_pool (the Bergeaud S2 query): a candidate matches a domain if
its cpc_group startswith one of that domain's CPC prefixes AND its title+abstract contains
one of that domain's keywords. Streaming the 6.2GB abstract TSV once for all 5 domains (instead
of 5x) is the whole point of this script.

Usage:
  python -m scripts.collect_pools --bulk "C:/.../Patent_Bulk"
  python -m scripts.collect_pools --bulk "..." --domains blockchain genomeediting

Writes DataSet/expanded/<domain>/expanded_candidates_raw.csv per domain.
"""
from __future__ import annotations
import argparse
import csv
import re
import sys
import time
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from src import domains as D

DEFAULT_BULK = r"C:/Users/User/OneDrive/문서/이수인/서울대학교/Biblo+Text/Patent_Bulk"


def _q(s: str) -> str:
    return s.strip().strip('"')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bulk", default=DEFAULT_BULK, help="Patent_Bulk dir with g_*.tsv")
    ap.add_argument("--domains", nargs="*", default=D.NEW_DOMAINS, help="domain keys to collect")
    args = ap.parse_args()
    bulk = Path(args.bulk)

    specs = {k: D.DOMAINS[k] for k in args.domains}
    dom_tuples = {k: tuple(s.cpc_prefixes) for k, s in specs.items()}
    dom_kw = {k: re.compile("|".join(re.escape(w) for w in s.keywords), re.I)
              for k, s in specs.items()}
    global_prefixes = tuple(sorted({p for s in specs.values() for p in s.cpc_prefixes}))
    print(f"domains: {list(specs)}")
    print(f"global CPC prefixes: {len(global_prefixes)}  | per-domain kw regex ready")

    # ---- [1/3] CPC filter (one pass) -> per-domain matched id sets ----
    print("\n[1/3] CPC scan ...", flush=True)
    matched: dict[str, set] = {k: set() for k in specs}
    union: set[str] = set()
    t0 = time.time(); n = 0
    with open(bulk / "g_cpc_at_issue.tsv", encoding="utf-8") as f:
        f.readline()
        for line in f:
            n += 1
            p = line.split("\t")
            if len(p) < 7:
                continue
            g = _q(p[6])
            if not g.startswith(global_prefixes):
                continue
            pid = _q(p[0])
            for k, tup in dom_tuples.items():
                if g.startswith(tup):
                    matched[k].add(pid)
                    union.add(pid)
    print(f"  scanned {n:,} cpc rows in {time.time()-t0:.0f}s")
    for k in specs:
        print(f"    {k:22s} CPC-matched: {len(matched[k]):,}")
    print(f"  union ids: {len(union):,}", flush=True)

    # ---- [2/3] titles for union ids ----
    print("\n[2/3] titles ...", flush=True)
    titles: dict[str, tuple] = {}
    t0 = time.time()
    with open(bulk / "g_patent.tsv", encoding="utf-8") as f:
        f.readline()
        for line in f:
            p = line.rstrip("\n").split("\t")
            if len(p) < 4:
                continue
            pid = _q(p[0])
            if pid in union:
                titles[pid] = (_q(p[3]), _q(p[2]))      # (title, date)
    print(f"  titles for {len(titles):,} ids in {time.time()-t0:.0f}s", flush=True)

    # ---- [3/3] abstracts (one pass) + keyword filter + streaming write ----
    print("\n[3/3] abstracts + keyword intersection + write ...", flush=True)
    writers, files, counts = {}, {}, defaultdict(int)
    for k, s in specs.items():
        s.pool_raw.parent.mkdir(parents=True, exist_ok=True)
        fh = open(s.pool_raw, "w", newline="", encoding="utf-8")
        w = csv.DictWriter(fh, fieldnames=["patent_id", "Patent_title", "Patent_abstract",
                                           "date", "matched_subtopics"])
        w.writeheader()
        writers[k], files[k] = w, fh

    t0 = time.time(); seen = 0
    with open(bulk / "g_patent_abstract.tsv", encoding="utf-8") as f:
        f.readline()
        for line in f:
            p = line.rstrip("\n").split("\t", 1)
            if len(p) < 2:
                continue
            pid = _q(p[0])
            if pid not in union:
                continue
            seen += 1
            abstract = _q(p[1])
            title, date = titles.get(pid, ("", ""))
            text = f"{title}. {abstract}"
            for k in specs:
                if pid in matched[k] and dom_kw[k].search(text):
                    writers[k].writerow({"patent_id": pid, "Patent_title": title,
                                         "Patent_abstract": abstract, "date": date,
                                         "matched_subtopics": k})
                    counts[k] += 1
    for fh in files.values():
        fh.close()
    print(f"  scanned union abstracts ({seen:,}) in {time.time()-t0:.0f}s")

    print("\n=== POOL SIZES (after CPC AND keyword) ===")
    for k, s in specs.items():
        print(f"  {k:22s} {counts[k]:>8,}  -> {s.pool_raw.relative_to(D.ROOT)}")


if __name__ == "__main__":
    main()
