# MAS 재설계 — "골드셋 구축 프로시저" 기반 유효특허 선별 시스템 (2026-07-25)

## 0. 목적

2026-07-24~25 대화에서 사람(도메인 소유자)과 Claude가 **휴머노이드 A2 골드셋(1,246건)** 을 만든 그 절차 자체를, 기존 `src/agentic/` MAS의 **기준서 작성 전(前)단계**로 이식한다. 즉 "기준서를 어떻게 뽑느냐"를, LLM이 한 번에 기준서를 쓰는 방식에서 → **정합 진단 → 설계안 → 카테고리 사례 매핑(확정/경계/오탐) → 인사이트 → HITL 결정 → 초기 기준서** 의 절차로 바꾼다.

**바뀌는 것(前단계)** = 스테이지 [3.5]~[4d] 신설.
**그대로인 것(後단계)** = [5] 기준서 validator 루프, [6] 판정, [7] 판정 validator — 현행 유지.

핵심 요구:
1. 카테고리 사례 매핑이 **Streamlit에 그대로 보일 것** + 스스로 고쳐가는 과정도 화면에 보일 것.
2. HITL 질문은 **결정 카드 포맷**(쟁점 / 포함 논리+대표사례 / 제외 논리+대표사례 / 영향 규모 / 권고)으로 낼 것.
3. 초기 자료(도메인·설명서·핵심자료·raw)가 **충분한지 판단**하고, 부족하면 Wikipedia 검색까지 진행할 것.

---

## 1. 대화 프로시저 → 파이프라인 단계 매핑

| 대화에서 한 일 | 신규/재사용 | 파이프라인 단계 | 담당 모듈 |
|---|---|---|---|
| 도메인·설명서·핵심자료·raw 4종 입력 검토 | 재사용 | [1] scoping + [2b] local docs | `scoping.py`, `localdocs.py` |
| ① 문제 파악 ② 보고서 파악 | 재사용(확장) | [2b]/[3] 문서·코퍼스 리딩 | `localdocs.py`, `corpus.py` |
| **자료 충분성 판단 → 부족 시 Wikipedia** | **변경(게이팅)** | [2] research를 [3.5]가 조건부 호출 | `research.py`+신규 게이트 |
| **③ 정합 진단**(직접언급 %, 대기업 비중, 국적, 패밀리 중복, AI요약 6열) | **신규** | **[3.5] 정합 진단** | **`diagnose.py`(신규)** |
| 정답셋 구축계획 §5 (Tier1/Tier2/E 계층, 축 앵커링) | 재사용(확장) | [4a] axes → **설계안** | `axes.py`+`designplan.py`(신규) |
| **카테고리별 사례 매핑**(확정/경계/오탐 표) + 스스로 수정 | **신규(핵심)** | **[4b-map] 사례 매핑** | **`casemap.py`(신규)** |
| 대표 확정 사례 + 핵심 인사이트 5가지 | 신규 | [4b-map] 집계 | `casemap.py` |
| **HITL 결정 ①②③**(쟁점/논리/영향/권고) | **변경(포맷)** | **[4c] 결정 HITL** | `hitl.py`+`boundary_probe.py` 확장 |
| 초기 기준서 확정 | 재사용(입력 확장) | [4d] 기준서 초안 | `criteria.py` |
| 기준서 판정→수정 루프 | **재사용(불변)** | [5] validator 루프 | `validator.py` |
| 3,323건 판정 | 재사용(불변) | [6] judge | `judge.py` |
| 판정 검증·boundary-loop | 재사용(불변) | [7] | `validator.py`, `boundary_probe.py` |

---

## 2. 신규/변경 모듈

### 신규 파일
- **`src/agentic/diagnose.py`** — 정합 진단 + 충분성 게이트
- **`src/agentic/designplan.py`** — 축 앵커링 계층(Tier) 설계안
- **`src/agentic/casemap.py`** — 카테고리 사례 매핑 + 자기수정 루프
- **`src/agentic/schemas.py`** 에 신규 모델 추가 (아래 §3)

### 변경 파일
- **`pipeline.py`** — `build_criteria()` 안에 [3.5]→[4a]→[4b-map]→[4c] 삽입, [4d]에 사례매핑·결정 주입
- **`hitl.py`/`boundary_probe.py`** — `ScopeQuestion` → `DecisionQuestion`(결정 카드) 확장, 영향규모는 기존 flip-count 재사용
- **`app/streamlit_app.py`** — 탭 3개 추가(정합 진단 / 사례 매핑 / 핵심 인사이트) + 결정 카드 HITL 렌더

### 불변 파일
`corpus.py`, `criteria.py`(입력만 확장), `validator.py`, `judge.py`, `research.py`(호출 위치만 변경), `leakage.py`, `reproducibility.py`, `workspace.py`, `config.py`

---

## 3. 신규 데이터 계약 (schemas.py 추가)

```python
class PoolProfile(BaseModel):                 # [3.5] 정량 프로파일 (LLM 아님, 코드 산출)
    n_total: int; n_family_dedup: int; family_dup_rows: int
    direct_domain_mention: int; direct_domain_pct: float   # "humanoid/biped 직접언급 74건(2%)"
    top_assignees: list[tuple[str, int]]      # 정규화 후
    big_player_share: float                   # 산업용 대기업군 비중 (24.5%)
    nationality_dist: list[tuple[str, int]]
    cpc_main_dist: list[tuple[str, int]]
    ai_summary_fill_rate: float               # AI요약 6열 채움률
    report_company_coverage: list[tuple[str, int, int]]  # (기업, positive후보, 풀존재)

class AlignmentDiagnosisOut(BaseModel):       # [3.5] LLM 해석 + 충분성
    problem_understanding: str                # ① 문제 파악
    reference_understanding: str              # ② 핵심자료 파악
    alignment_notes: list[str]                # ③ 정합 진단 서술 (경계 이슈 지목)
    sufficiency: Literal["sufficient", "need_web"]
    gaps: list[str]                           # 부족하면 무엇이 부족한가 → 웹 검색 질의로 사용

class DesignTier(BaseModel):
    tier: Literal["T1", "T2", "E"]
    name: str; axis_ids: list[str]            # 축 앵커링
    definition: str; expected_signals: list[str]
    est_count_lo: int; est_count_hi: int

class DesignPlanOut(BaseModel):               # [4a] 정답셋 설계안 §5
    tiers: list[DesignTier]
    judging_unit: str                         # "패밀리 대표 1건"
    notes: list[str]

class CaseRow(BaseModel):
    patent_id: str; assignee: str; gist: str  # 제목 요지
    verdict: Literal["confirmed", "boundary", "false_positive"]
    tier: Optional[str]                        # 확정/권고 귀속
    basis: str                                 # 근거 / 무엇이 애매한가 / 왜 오탐
    recommendation: Optional[str]              # 경계행: 권고 귀속

class CaseMapCategoryOut(BaseModel):          # [4b-map] 카테고리 1개 결과
    category: str                             # "T1_직접휴머노이드", "E_수술로봇" ...
    sample_n: int; cross_matched: int
    confirmed: list[CaseRow]
    boundary: list[CaseRow]
    false_positive: list[CaseRow]
    false_positive_cues: list[str]            # 오탐 사전 기여 ('recycling≠재활' 등)

class CaseMapReviseOut(BaseModel):            # 자기수정 1스텝 (화면에 보임)
    category: str; changed: list[CaseRow]     # 재분류된 행
    rationale: str                            # 왜 바꿨나

class CaseInsight(BaseModel):
    title: str; detail: str                   # "OEM 3분할이 필수" 등 5가지
    evidence_ids: list[str]

class DecisionQuestion(BaseModel):            # [4c] 결정 카드 (ScopeQuestion 확장)
    id: str; stake: str                       # 쟁점
    include_argument: str; include_examples: list[str]   # 포함 논리 + 대표사례
    exclude_argument: str; exclude_examples: list[str]   # 제외 논리 + 대표사례
    impact_flips: int; impact_sample_n: int   # 영향 규모 (boundary_probe 측정 재사용)
    recommendation: str                       # 권고안
    options: list[str]; tentative_default: str
    broad_rule: str; narrow_rule: str         # 기계 판정용 (기존 유지)
```

`CriteriaDocOut` 는 그대로 두되, [4d]에서 `casemap`·`design_plan`·`decisions` 를 **프롬프트 근거로 주입**만 한다 (스키마 불변 → 後단계 무수정).

---

## 4. 단계별 상세 설계

### [3.5] 정합 진단 (`diagnose.py`)
1. **정량 프로파일**(코드): dedup·정규화·키워드 카운트 — 이번에 만든 `build_humanoid_pool_v2.py` 로직을 함수화(`profile_pool(pool_df, domain_terms)` → `PoolProfile`). 도메인 용어(humanoid/biped 등)는 scoping이 뽑은 canonical terms 사용.
2. **LLM 해석**: 프로파일 + owner 문서 노트 → `AlignmentDiagnosisOut`. 여기서 ①②③ 산출 + **충분성 판정**.
3. **충분성 게이트**: `sufficiency=="need_web"` 면 `gaps` 를 검색 질의로 `research.py` 호출(누출차단 유지). `sufficient` 면 웹 스킵(현행은 항상 호출 → 조건부로 변경). Owner 문서만으로 축이 서면 웹 생략, 도메인 정의가 얕으면 Wikipedia 폴백.
   - 산출: `ws/diagnosis.json`, `ws/pool_profile.json`.

### [4a] 설계안 (`designplan.py`)
- 입력: `AxisSynthesisOut`(기존 axes.py) + `PoolProfile`.
- 출력: `DesignPlanOut` — 축을 T1/T2/E 계층으로 접고, 각 tier에 예상 신호·건수레인지. = "구축계획 §5". `ws/design_plan.json`.

### [4b-map] 사례 매핑 (`casemap.py`) — **핵심**
카테고리 = T1 축 + T2 축(7) + E 축(5) 를 `DesignPlan`에서 파생.
카테고리별 루프:
1. **후보 추출**(코드): 카테고리 신호로 풀 필터 → 표본 뽑되 **교차매칭(제외×Tier 동시매칭) 우선** (이번 `extract_candidates.py` 로직 함수화). map은 gpt-4o-mini.
2. **1차 매핑**(LLM): 표본의 제목+초록+AI요약6열 → `CaseMapCategoryOut`(확정/경계/오탐 + 오탐 사전).
3. **자기수정 루프**(신규, 화면 노출): 비평자 LLM이 확정/오탐을 재검(예: "휴머노이드 팔인데 '엔터' 응용례로 E에 걸림") → `CaseMapReviseOut` 스트림. **N=2 라운드 무변화 시 종료** (기존 loop-until-dry 패턴 재사용). 각 revise를 `ws/casemap/<category>.revisions.jsonl` 로 append → Streamlit이 실시간 diff 렌더.
4. **집계**: 전 카테고리 오탐 사전 병합 → `ws/false_positive_cues.json`(기계 판정용, 규칙 12의 어휘 배제). 대표 확정 사례 + **핵심 인사이트**(`CaseInsight[]`) 추출 → `ws/insights.json`.

산출: `ws/casemap/<category>.json`(전 카테고리), `ws/casemap_summary.json`.

### [4c] 결정 HITL (`hitl.py`+`boundary_probe.py` 확장)
- 사례 매핑의 **경계 다발 카테고리**에서 결정거리(예: 4족/물류학습/산업용 회색지대)를 `DecisionQuestion`으로 승격.
- **영향 규모**: 기존 `probe_boundaries()`가 이미 broad/narrow flip-count를 **측정** → 그대로 `impact_flips`에. 대표사례는 casemap의 boundary/confirmed에서 각 side 2건 인용.
- batch 모드: `questions_pending.json`에 결정 카드 스키마로 기록, `answers.json`로 재개(기존 해시 ID·`human_prior` 재사용 로직 유지). **교훈 반영**: 답변을 scope_decision에 **축약 없이 그대로 기록**하도록 [4d] 프롬프트에 "record verbatim" 지시(이번 비수렴 원인 해결).

### [4d] 초기 기준서 (`criteria.py`, 입력만 확장)
- 프롬프트 근거에 `design_plan` + `casemap_summary`(확정 사례·오탐 사전·인사이트) + 확정된 `decisions` 주입.
- 산출은 기존 `CriteriaDocOut` → [5] 이후 파이프라인 **무수정**.

---

## 5. Streamlit 표면 (app/streamlit_app.py)

기존 탭: 기준서 / HITL Q&A / 리서치·코퍼스 / 경계 검증. **추가:**

1. **📊 정합 진단 탭**: `PoolProfile` 지표 카드(총건/dedup/직접언급%/대기업비중/국적·CPC 분포/AI요약 채움률/보고서기업 커버리지) + `AlignmentDiagnosisOut` 서술 + 충분성 배지(웹 검색 여부).
2. **🗂️ 사례 매핑 탭(핵심)**: 카테고리 선택 → 확정/경계/오탐 **3개 표**(대화에서 준 그 표 그대로: 등록번호·출원인·제목요지·근거/애매점/권고). **자기수정은 `revisions.jsonl`을 타임라인으로 렌더** — 각 라운드마다 "이 특허를 E→T2로 재분류: 이유…"를 diff 카드로. live_panel처럼 stage 폴링으로 실시간 갱신.
3. **💡 핵심 인사이트 탭**: `CaseInsight[]` 카드 + 대표 확정 사례.
4. **결정 카드 HITL**(render_hitl 교체): 질문마다 쟁점 / [포함 논리 + 대표사례 칩] / [제외 논리 + 대표사례 칩] / **영향규모 게이지(flip N/표본)** / 권고 배너 / 선택 라디오. 답변 → answers.json.

렌더는 전부 파일 기반(ws의 json/jsonl 폴링) → 러너와 UI 디커플링(기존 패턴 유지, HITL-in-UI 이미 지원).

---

## 6. 구현 순서 (단계별, 각 단계 독립 검증)

1. **schemas + diagnose.py** — 정량 프로파일 함수화(기존 스크립트 이식) + 충분성 게이트. mock으로 [3.5] 단독 검증.
2. **designplan.py** — axes 출력을 tier로 접기. 
3. **casemap.py** — 후보추출 함수화 + 1차 매핑 + 자기수정 루프. **가장 큰 작업.** 이번 A2 표본으로 회귀 검증(휴머노이드 재실행 시 대화와 유사한 확정/경계/오탐이 나오는지).
4. **hitl 결정카드** — DecisionQuestion + probe 재사용. 
5. **pipeline 배선** — [3.5]→[4a]→[4b-map]→[4c]→[4d] 삽입, 캐시·resume 규약 준수.
6. **Streamlit 4표면**.
7. **E2E**: 휴머노이드 A2로 재실행 → gold v1.1과 대조(재현성). 그 다음 hydro 등 타 도메인 회귀.

---

## 7. 리스크·미결정 (착수 전 확인)

- **비용**: 카테고리 12 × 표본 110 × 자기수정 2라운드 → map은 mini라 회당 소폭이나, casemap이 판정만큼 커질 수 있음. 표본 상한·자기수정 라운드 수를 config로.
- **범용성**: 이번 카테고리(T1/T2 7축/E 5종)는 휴머노이드 특화. 타 도메인에선 `DesignPlan.tiers`에서 카테고리를 **자동 파생**해야 함(하드코딩 금지). axes가 도메인마다 다르게 서므로 casemap 카테고리도 축에서 생성.
- **자기수정 종료조건**: loop-until-dry(2라운드 무변화) vs 비용 상한. 판정 validator와 동일 패턴.
- **後단계 계약**: [4d] 출력이 `CriteriaDocOut`로 동일해야 [5]~[7] 무수정. 사례매핑·인사이트는 근거 주입일 뿐 스키마 확장 아님 — 이 불변식을 테스트로 고정.
- **결정 미해소(off 모드)**: 사람 없으면 권고안을 default로 확정하고 open_questions에 기록(기존 규약).

---

## 7.5 E2E 검증 결과 (2026-07-25, 휴머노이드 라이브)

`--variant goldset-v2-casemap`, 입력=pool_v2.csv(3,323) + KIMM 정리본·도메인설명(판정규칙 문서는 **의도적으로 미주입** — 규칙 자체 도출 검증). 새 파이프라인이 절차를 그대로 재현:

- **[2-게이트]**: KIMM 자료를 "충분"으로 판정 → **웹 검색 스킵** (게이트 작동 확인)
- **[3.5]**: 직접 도메인 언급 222건(6.7%), 풀 프로파일 산출
- **[4a+]**: 축에서 **8개 tier 자동 파생**(하드코딩 아님 — 범용성 확인)
- **[4b-map]**: 실제 사례 매핑 172확정/38경계/오탐 + 자기수정 + 인사이트 3 + 오탐사전(‘robotic control is not humanoid-specific’ 등)
- **[4c]**: **3개 결정 자체 도출**(비휴머노이드 시스템 55/60 flip, 웨어러블 13/60, 안전 17/60) — 우리 결정 ①②③와 동일 포맷
- 판정 3,323건 133초 $1.37 실패0

**회귀(gold v1.1 대조)**: recall **0.964**(1201/1246 포착, 미스 45) / precision 0.566(positive 2,121, FP 920) / F1 0.713 / positive Jaccard 0.554 / κ 0.457.

해석: 절차·리콜은 gold를 충실히 재현(96% 포착). 이후 3개 후속 fix로 precision 개선:

**후속 개선(2026-07-25)** — 동일 워크스페이스에서 기준서만 재생성하며 측정:
| 단계 | precision | recall | F1 | κ | positive | 커밋 |
|---|---|---|---|---|---|---|
| 초기(off-mode) | 0.566 | 0.964 | 0.713 | 0.457 | 2,121 | — |
| (a) 경계 재질문 해시 안정화 | 0.550 | 0.950 | 0.697 | 0.423 | 2,151 | f039a64 |
| (b) E-tier 커버리지 결정론 강제 | 0.559 | 0.923 | 0.696 | 0.430 | 2,057 | f5bca26 |
| (c) 제외 문구 날카롭게(도피조항 제거) | **0.750** | 0.795 | **0.772** | **0.629** | **1,321** | b… |

- **(a)** `settle_against_prior`(judge 단계 것)를 criteria 루프 두 질문 지점에 적용 → 같은 경계 재질문 무한루프 해소, batch 모드 자연 수렴 (검증: "reapplied prior ruling").
- **(b)** design-plan E-tier(=casemap이 찾은 look-alike 패밀리)는 반드시 E기준으로 커버돼야 함을 코드 결정론 검사(`EXCL_COVERAGE:`)로 강제. 축→C기준 커버리지와 동형. **도메인 범용**. E1(웨어러블)·E2(산업용팔) 생성됨 — 그러나 "unless transferable" 도피조항으로 실효 없음.
- **(c)** 도피조항 금지 + 청구항-범위 결정 테스트 강제 → **precision 0.56→0.75, F1 0.70→0.77, κ 0.43→0.63**. 산업용 FP 907→166, positive 1,321(gold 1,246 근접).

**남은 트레이드오프**: (c)에서 recall 0.92→0.80(FN 255) — 날카로운 제외가 이전가능 코어 일부까지 과잉 제외. **현재 최고 지점 = P0.750/R0.795/F0.772/κ0.629.**

## 7.6 Tier-B 청구항 재판정 — 시도했으나 실패(음성 결과, 2026-07-25)

"둘 다 올리려면 경계 판별력을 올려야 한다"는 가설로 **[6.5] Tier-B**를 구현: contested 클러스터(현 positive 전체 = FP위험 + E-fired negative = FN위험, ~2,600건)를 **초록이 아니라 청구항(rep_claim) + 강한 모델(gpt-4o) + casemap IN/OUT 앵커**로 재판정. 진단 근거는 견고했음 — 청구항 100% 존재(1,409자), 오답이 전부 confidence 0.85~0.90(자신만만한 오답), FP·FN이 같은 청구항-범위 경계에 집중.

**결과: 실패.** 2,600건 중 688건 flip했으나 flip이 gold와 반상관 — IN→OUT 40%만 정답(진짜 positive 209건 오제외), OUT→IN 26%만 정답(진짜 negative 252건 오포함). **P 0.750→0.662, R 0.795→0.699 둘 다 하락.** 원인: 단일 rep_claim(대표청구항 1개, 2,600자 절단) + 이분법 "process-bound→OUT" 프롬프트로는 gpt-4o가 어느 쪽으로도 근거를 찾아 노이즈 생성. gold의 전문가 전체맥락 청구항-범위 판정을 단일 청구항+블런트 테스트가 대체 못 함. → **`BOUNDARY_TIER_ENABLED=False`로 비활성(코드는 기록용 보존).** 재시도하려면 전체 독립청구항+다청구항 추론+앙상블 투표 필요, 성공 보장 없음.

**결론**: 자동 판정자의 F1 상한이 이 수동 튜닝 gold 대비 ~0.77 부근. 단일 강한모델 재판정으로는 프론티어를 못 밀었음. 남은 진짜 레버: 앙상블 투표+confidence 재보정, 또는 F0.772를 운용점으로 수용.

## 8. 요약

前단계(기준서 생성)를 "한 방 LLM"에서 **정합 진단 → 설계안 → 사례 매핑(자기수정) → 인사이트 → 결정 카드 → 기준서**로 교체. 신규 3모듈(diagnose/designplan/casemap) + 스키마 7종 + Streamlit 4표면. 後단계(validator·judge)는 계약(`CriteriaDocOut`) 유지로 **무수정**. 이번 A2 골드셋이 그대로 회귀 검증 기준.
