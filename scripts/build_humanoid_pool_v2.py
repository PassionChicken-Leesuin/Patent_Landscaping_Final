# -*- coding: utf-8 -*-
"""A2 정답셋 v1 전처리 파이프라인.

휴머노이드특허_Raw.xlsx(3,757건, US 등록특허)에 대해:
  [1] 패밀리 dedup (WIPS패밀리 ID당 대표 1건 = 최초 출원)
  [2] 출원인 정규화 (도치 복원 + 법인접미사 제거 + 그룹 매핑) -> applicant_map.csv
  [3] 카테고리 플래그 (제목+초록 EN, AI요약 6열 KR) + 오탐 배제 사전 (규칙 9)
  [4] 규칙 기반 1차 라벨: T1_auto / E_auto / GRAY -> labels_v1.csv

확정 판정 규칙 v1 (A2_정답셋_사례매핑.md §8·§14, 2026-07-24 사용자 확정):
  - 4족·다족 전신제어·다리 기술 T2 (규칙 기반으로는 GRAY로 보내 agentic 판정)
  - 물류 학습: 스킬 학습 T2 / 워크플로 학습 E (GRAY -> agentic)
  - 산업용 회색지대: 힘 기반 교시·시뮬 튜닝 T2, 주변기술 E (GRAY -> agentic)
  규칙 기반 pass는 보수적으로: 확실한 T1(휴머노이드 명시/전건 T1 OEM)과
  확실한 E(제외 전용 + Tier 신호 전무)만 자동 확정, 나머지는 GRAY.

사용:
  python -m scripts.build_humanoid_pool_v2 --input <xlsx|parquet> --outdir DataSet/humanoid
"""
import argparse
import io
import re
import sys

import pandas as pd

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

AI_COLS = [
    "AI 요약[KR,US,JP,CN,EP,PCT,TW]",
    "기술분야 요약[KR,US,JP,CN,EP,PCT,TW]",
    "해결과제 요약[KR,US,JP,CN,EP,PCT,TW]",
    "해결수단 요약[KR,US,JP,CN,EP,PCT,TW]",
    "특징 요약[KR,US,JP,CN,EP,PCT,TW]",
    "효과 요약[KR,US,JP,CN,EP,PCT,TW]",
]

LEGAL_SUFFIX = (
    r"KABUSHIKI KAISHA|CO LTD|CORPORATION|CORP|INCORPORATED|INC|LLC|LTD|GMBH"
    r"|AKTIENGESELLSCHAFT|AG|AB|SA|SAS|SE|BV|NV|KK|COMPANY|LIMITED|HOLDINGS?"
    r"|SRL|S\.?P\.?A|OY|APS|PLC"
)

# 그룹 매핑: 정규화명 부분일치 -> 그룹명 (출원 시점 법인 라벨은 norm에 보존, 그룹은 주석용)
GROUP_MAP = [
    (r"^X DEVELOPMENT|^GOOGLE|^INTRINSIC INNOVATION|^DEEPMIND|^VERILY|^WAYMO", "ALPHABET"),
    (r"^BOSTON DYNAMICS", "HYUNDAI MOTOR GROUP(2021~)/구글·소프트뱅크(이전)"),
    (r"^HYUNDAI|^KIA\b", "HYUNDAI MOTOR GROUP"),
    (r"^KUKA", "KUKA"),
    (r"^PANASONIC", "PANASONIC"),
    (r"^TOYOTA|^WOVEN", "TOYOTA"),
    (r"^HONDA", "HONDA"),
    (r"^SAMSUNG", "SAMSUNG"),
    (r"^LG\b|^LG ", "LG"),
    (r"^AMAZON", "AMAZON"),
    (r"^ABB\b", "ABB"),
    (r"^MITSUBISHI ELECTRIC", "MITSUBISHI ELECTRIC"),
    (r"^SOFTBANK ROBOTICS|^ALDEBARAN", "SOFTBANK ROBOTICS"),
    (r"^UBTECH", "UBTECH"),
    (r"^SONY", "SONY"),
    (r"^KASTANIENBAUM|^FRANKA|^AGILE ROBOTS", "FRANKA"),
    (r"^GM GLOBAL|^GENERAL MOTORS", "GM"),
    (r"^DENSO", "DENSO"),
    (r"^KAWASAKI JUKOGYO|^KAWASAKI HEAVY", "KAWASAKI HEAVY INDUSTRIES"),
    (r"^YASKAWA", "YASKAWA"),
    (r"^SEIKO EPSON", "SEIKO EPSON"),
    (r"^FANUC", "FANUC"),
    (r"^CANON", "CANON"),
    (r"^SOFT ROBOTICS|^OXIPITAL", "SOFT ROBOTICS/OXIPITAL"),
]

# 전건 T1 OEM (사례매핑 §2: Figure/Sanctuary/Agility 전건 T1 확정)
OEM_ALL_T1 = r"^FIGURE AI|^SANCTUARY|^AGILITY ROBOTICS"

# 직접 휴머노이드 신호 (T1_auto): 엄격 패턴
HUMANOID_STRICT = (
    r"humanoid|anthropomorph|\bbiped|two-legged|휴머노이드|이족|2족 보행|인간형 로봇"
)

# Tier 신호 (E_auto 판정 시 '있으면 GRAY로 보존'용 — 넓게)
TIER_SIGNAL = (
    r"grasp|gripper|robot(ic)? hand|finger|tactile|dexterous|manipulat|robot(ic)? arm"
    r"|actuator|reducer|joint|servo|balanc|gait|locomotion|legged|fall recovery"
    r"|imitation|reinforcement|neural|machine learning|teleoperat|master.slave"
    r"|sim.to.real|domain randomiz|human.robot|collaborative|collision"
    r"|파지|그리퍼|로봇 ?손|손가락|촉각|매니퓰레|조작|액추에이터|감속기|관절|서보"
    r"|균형|보행|모방 ?학습|강화 ?학습|신경망|원격 ?조작|협동|협업|충돌"
)

# 제외 전용 신호
EXCL = {
    "수술": r"surgic|surgery|endoscop|catheter|laparoscop|수술|내시경|카테터",
    "외골격": r"exoskeleton|prosthe|orthosis|orthotic|외골격|의족|의수|보행 보조|착용형 로봇",
    "청소": r"vacuum clean|cleaning robot|robot cleaner|lawn ?mower|로봇 ?청소기|청소 로봇|잔디",
    "물류전용": r"automated guided vehicle|\bagv\b|palletiz|depalletiz|sortation|conveyor"
    r"|warehouse|무인 ?반송|팔레타이징|팔레트 적재|분류 시스템|컨베이어|창고",
    "완구": r"\btoy\b|amusement|theme park|완구|장난감|놀이공원",
}

# 오탐 배제 사전 (규칙 9): 이 패턴이 있으면 해당 신호를 무효화
NEG = {
    "load_balancing": r"load balanc|서버 부하|부하 분산",
    "gravity_balancer": r"gravity balancer|balancer (spring|device)|중력 밸런서|밸런서",
    "pedestrian_nav": r"pedestrian",
    "recycling": r"recycl",  # '재활' 오매칭 방지: 외골격 신호 무효화에만 사용
}


def norm_applicant(raw: str) -> str:
    s = str(raw).upper().strip()
    s = re.sub(r"[.,]+$", "", s)
    # 도치 복원: "CORPORATION, FANUC" -> "FANUC CORPORATION"
    m = re.match(rf"^({LEGAL_SUFFIX}),\s*(.+)$", s)
    if m:
        s = f"{m.group(2)} {m.group(1)}"
    s = re.sub(r"[.,]", "", s)
    s = re.sub(rf"\b({LEGAL_SUFFIX})\b", "", s)
    return re.sub(r"\s+", " ", s).strip()


def group_of(norm: str) -> str:
    for pat, grp in GROUP_MAP:
        if re.search(pat, norm):
            return grp
    return norm


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--outdir", default="DataSet/humanoid")
    args = ap.parse_args()

    if args.input.endswith(".parquet"):
        df = pd.read_parquet(args.input)
    else:
        df = pd.read_excel(args.input, sheet_name=0)
    n0 = len(df)

    # ---- [0] 데이터 결함 보정 대상 표시 ----
    df["_결함"] = ""
    blank_reg = df["등록번호"].isna() | (df["등록번호"].astype(str).str.strip() == "")
    df.loc[blank_reg, "_결함"] = "등록번호누락"

    # ---- [1] 패밀리 dedup: 최초 출원 대표 ----
    df["_출원일"] = pd.to_datetime(df["출원일"], errors="coerce")
    df = df.sort_values(["WIPS패밀리 ID", "_출원일", "출원번호"])
    fam_size = df.groupby("WIPS패밀리 ID")["출원번호"].transform("size")
    df["_패밀리내건수"] = fam_size
    dedup = df.drop_duplicates("WIPS패밀리 ID", keep="first").copy()
    print(f"[1] 패밀리 dedup: {n0} -> {len(dedup)} (제거 {n0 - len(dedup)})")

    # ---- [2] 출원인 정규화 ----
    first_app = dedup["출원인"].astype(str).str.split(r"\s*\|\s*").str[0]
    dedup["출원인_norm"] = first_app.map(norm_applicant)
    dedup["출원인_그룹"] = dedup["출원인_norm"].map(group_of)
    dedup["출원인_전체"] = dedup["출원인"]
    nat = dedup["출원인 국적"].astype(str).str.split(r"\s*\|\s*").str[0].str.strip()
    dedup["출원인_국적1"] = nat.replace("", "미상").replace("nan", "미상")
    amap = (
        dedup.groupby([first_app.name if first_app.name else "출원인"])
        .first()
        .reset_index()
    )
    amap_df = pd.DataFrame(
        {
            "raw": first_app,
            "norm": dedup["출원인_norm"],
            "group": dedup["출원인_그룹"],
            "국적": dedup["출원인_국적1"],
        }
    ).drop_duplicates("raw").sort_values("norm")
    print(f"[2] 출원인: raw {amap_df['raw'].nunique()} -> norm {amap_df['norm'].nunique()} -> 그룹 {amap_df['group'].nunique()}")

    # ---- [3] 텍스트 결합 + 신호 ----
    en = (dedup["발명의 명칭"].fillna("") + " " + dedup["요약"].fillna("")).str.lower()
    kr = dedup[AI_COLS].fillna("").agg(" ".join, axis=1)
    full = en + " §§ " + kr.str.lower()

    has_humanoid = full.str.contains(HUMANOID_STRICT, regex=True)
    has_tier = full.str.contains(TIER_SIGNAL, regex=True)
    neg_hits = {k: full.str.contains(p, regex=True) for k, p in NEG.items()}

    excl_flags = {}
    for k, p in EXCL.items():
        f = full.str.contains(p, regex=True)
        if k == "외골격":  # 'recycling' 오매칭 무효화
            f = f & ~neg_hits["recycling"]
        excl_flags[k] = f
    any_excl = pd.concat(excl_flags.values(), axis=1).any(axis=1)

    oem_t1 = dedup["출원인_norm"].str.contains(OEM_ALL_T1, regex=True)

    # ---- [4] 1차 라벨 ----
    label = pd.Series("GRAY", index=dedup.index)
    src = pd.Series("", index=dedup.index)

    # E_auto: 제외 전용 신호만 있고 Tier·휴머노이드 신호 전무 (보수적)
    e_auto = any_excl & ~has_tier & ~has_humanoid & ~oem_t1
    label[e_auto] = "E_auto"
    src[e_auto] = "제외전용신호+Tier신호없음"

    # T1_auto: 휴머노이드 명시 or 전건 T1 OEM (단, 제외 전용 신호가 강하면 GRAY 유지)
    t1_auto = (has_humanoid | oem_t1) & ~e_auto
    label[t1_auto] = "T1_auto"
    src[t1_auto] = "휴머노이드명시/전건T1_OEM"
    # 휴머노이드 명시라도 제외 신호 동반 시 검증 필요 표시 (Sarcos·완구 등)
    t1_check = t1_auto & any_excl
    src[t1_check] = "T1후보-제외신호동반(검증필요)"

    dedup["label_v1"] = label
    dedup["label_source"] = src
    dedup["신호_휴머노이드"] = has_humanoid
    dedup["신호_Tier"] = has_tier
    for k, f in excl_flags.items():
        dedup[f"신호_제외_{k}"] = f

    print("[4] 1차 라벨 분포:")
    print(dedup["label_v1"].value_counts().to_string())
    print("  - T1 중 검증필요:", (src == "T1후보-제외신호동반(검증필요)").sum())

    # ---- 저장 ----
    import os

    os.makedirs(args.outdir, exist_ok=True)
    keep = [
        "출원번호", "등록번호", "출원일", "발명의 명칭", "출원인", "출원인_norm",
        "출원인_그룹", "출원인_국적1", "WIPS패밀리 ID", "_패밀리내건수",
        "Current CPC Main", "label_v1", "label_source",
        "신호_휴머노이드", "신호_Tier",
    ] + [f"신호_제외_{k}" for k in EXCL] + ["_결함"]
    dedup[keep].to_csv(f"{args.outdir}/labels_v1.csv", index=False, encoding="utf-8-sig")
    amap_df.to_csv(f"{args.outdir}/applicant_map.csv", index=False, encoding="utf-8-sig")
    dedup.to_parquet(f"{args.outdir}/pool_v2.parquet")
    print(f"저장: {args.outdir}/labels_v1.csv, applicant_map.csv, pool_v2.parquet")


if __name__ == "__main__":
    main()
