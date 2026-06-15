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

# ---------------- search query ----------------
# CPC group prefixes (match cpc_group startswith). Grouped by subtopic for reporting.
CPC_TARGETS = {
    "self_driving":     ["B60W60"],                          # autonomous road vehicles
    "drive_control":    ["B60W30"],                          # ACC, lane-keep, collision-avoid
    "veh_state":        ["B60W40", "B60W50"],                # road/driver state estimation
    "cruise":           ["B60K31"],                          # (older) cruise control
    "auto_steering":    ["B62D15"],                          # automatic steering
    "auton_nav":        ["G05D1"],                           # autonomous navigation (land/air/sea)
    "traffic_v2x_anti": ["G08G1"],                           # road traffic ctrl / anti-collision
    "veh_radar_lidar":  ["G01S13/93", "G01S17/93"],          # vehicle anti-collision sensing
    "driving_scene_cv": ["G06V20/56", "G06V20/58", "G06V20/59"],
    "v2x_comms":        ["H04W4/40", "H04W4/44", "H04W4/46"],
    # NB: dedicated aircraft classes (B64*) dropped — they over-collected conventional
    # aviation (~23% vs gold's ~8%). Genuinely autonomous aerial is still caught by
    # auton_nav (G05D1) + the keyword intersection, keeping the road focus of the gold set.
}
ALL_PREFIXES = [(sub, p) for sub, ps in CPC_TARGETS.items() for p in ps]

# keyword vocabulary (>=1 must appear in title+abstract) — autonomous-driving signal
KEYWORDS = [
    "autonomous", "self-driving", "self driving", "driverless", "automated driving",
    "automated vehicle", "autonomous vehicle", "autonomous driving", "autonomous navigation",
    "adas", "driver assistance", "advanced driver", "cruise control", "adaptive cruise",
    "lane keeping", "lane departure", "lane detection", "lane centering", "lane following",
    "collision avoidance", "collision warning", "blind spot", "parking assist", "autopilot",
    "auto-pilot", "unmanned aerial", "unmanned ground", "unmanned vehicle", " uav ", " ugv ",
    "drone", "vehicle-to-vehicle", "vehicle to vehicle", "vehicle-to-everything", " v2x",
    " v2v", " v2i", "platooning", "ego vehicle", "ego-vehicle", "sensor fusion", "lidar",
    "point cloud", "occupancy grid", "trajectory planning", "motion planning", "path planning",
    "traffic sign", "obstacle detection", "automated guided vehicle",
]
KW_RE = re.compile("|".join(re.escape(k) for k in KEYWORDS), re.I)


def _q(s: str) -> str:
    return s.strip().strip('"')


def stream_cpc(path: Path):
    """patent_id -> set of matched subtopics (only for CPC-matching patents)."""
    matched: dict[str, set] = defaultdict(set)
    t0 = time.time(); n = 0
    with open(path, encoding="utf-8") as f:
        f.readline()
        for line in f:
            n += 1
            p = line.rstrip("\n").split("\t")
            if len(p) < 7:
                continue
            grp = _q(p[6])
            for sub, pref in ALL_PREFIXES:
                if grp.startswith(pref):
                    matched[_q(p[0])].add(sub)
                    break
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
