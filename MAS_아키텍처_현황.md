# MAS 유효특허 선별 시스템 — 아키텍처 현황 (living doc)

성능을 하나씩 갈고 닦기 위한 "현재 시스템의 정확한 지도". 코드 기준(`src/agentic/`). 개선할 때마다 갱신.

## 파이프라인 (`pipeline.build_criteria` → judge)

| # | 단계 | 하는 일 | 모델 | 입력 → 출력(스키마) | 산출물 |
|---|---|---|---|---|---|
| [1] | scoping | 질의 → 정규화 도메인·초기 task 가설 | 4o | query → `QueryScopeOut` | query.json |
| [2b] | local docs | owner 참고문서 주입(노트+원문) | 4o | 파일 → notes | research/notes.jsonl |
| [2-gate] | sufficiency | 자료 충분? → 웹 필요여부 | 4o | scope → precheck | — |
| [2] | research | 검색→필터→페치→근거추출→gap루프 | 4o | 웹 → `EvidenceNote[]`(evidence_type 8종) | research/{searches,notes,pages,blocked} |
| [3] | corpus | 풀 title+abstract 통독(Map/Reduce) | 4o-mini→4o | pool → `CorpusDigestOut` | corpus_digest.json |
| [3.5] | diagnose | 정량 풀프로파일 + 정합진단 | 4o | digest+pool → `AlignmentDiagnosisOut`+`PoolProfile` | diagnosis/pool_profile |
| [4a] | axes | 축 합성 + 출처타입 검증(fail-loud) | 4o | query+notes+digest → `AxisSynthesisOut` | axis_synthesis.* |
| [4a+] | design plan | 축 → T1/T2/E tier | 4o | axes → `DesignPlanOut` | design_plan.json |
| [4b-map] | casemap | tier별 후보 샘플→확정/경계/오탐 + 자기수정 | 4o-mini→4o | pool → `CaseMap*` | casemap/ |
| [4c] | decisions | 경계 결정카드(영향 계측) → HITL | 4o | casemap → `DecisionQuestion[]` | decisions.json |
| [4b-5] | criteria loop | 기준서 초안 + validator 루프(AXIS_COVERAGE/EXCL_COVERAGE 강제 + blind검증 + 패치리바이저) | 4o | 전부 → `CriteriaDocOut`(C/E) | criteria_final.* |
| judge | 판정 | 특허별 stance + C/E 불변식 | 4o-mini | 특허 → included/score | judge/audit.jsonl |

## "웹 ↔ 풀" 결합 지점
- 리서치 = `EvidenceNote`(외부 이상), corpus = `CorpusDigestOut`(풀 현실). 두 스키마는 의도적으로 다름.
- 결합은 [3] reduce의 대비 필드 + [4a] axes의 typed `source_refs`(`SourceType`)+참조검증에서 일어남.

## 성능 결정 지점 (KISTA GOCS 실증)
- **Recall ← [1]scoping + [2]research/owner-doc + [3.5]diagnose (스코프 정의).** owner-doc가 R 0.15→0.50 회복.
- **Precision ← [4a+]E-tier → [4b-map]오탐 → [4b-5]EXCL_COVERAGE → judge C/E ("제외 사슬").** FP 과다 = 이 사슬이 약함.
- AP는 살아있는데(0.28) F1(0.35) 낮음 → operating point가 과포함 쪽.

## 실험 현황 (KISTA, Choi 2022 TFSC head-to-head)
그들 baseline(F1): APL 0.574 / PatentBERT 0.640 / TRF+DIFF 0.620 (AP 0.409).

| 조건 | P | R | F1 | AP | FP |
|---|---|---|---|---|---|
| GOCS query-only (naive) | 0.123 | 0.153 | 0.136 | 0.053 | 143 |
| GOCS owner-doc (구코드, full) | 0.272 | 0.504 | 0.353 | 0.277 | 177 |
| GOCS owner-doc (#1 신코드, full) | 0.199 | 0.557 | 0.294 | 0.252 | 293 |
| MPUART owner-doc 구코드 (full) | 0.791 | 0.766 | 0.778 | 0.752 | 19 |
| MPUART 앵커링(과협소, full) | 1.000 | 0.489 | 0.657 | 0.581 | 0 |
| **MPUART refined앵커링+#1 (full)** | 0.779 | 0.787 | **0.783** | **0.757** | 21 |

핵심 정리(정직):
- **owner-doc ≫ query-only** (스코프 주입이 최대 레버; GOCS F1 0.136→0.35대).
- **MPUART: 깨끗한 스코프면 지도학습 baseline을 능가**(APL·PatentBERT 0.53 대비 0.778, AP는 TRF+DIFF 0.704도 상회 0.752). 라벨 0개로.
- **#1 성능효과는 미확정**: GOCS 신코드 full(0.294)이 구코드(0.353)보다 낮으나, 이는 scoping이 스코프를 broad하게(GNSS 탈락) 잡은 **확률변동**이 지배적(2k샘플에선 반대로 좋았음). **단일 실행으론 #1 개선/회귀 결론 불가 → multi-seed 통제평가 필요.**
- **#1 감사가능성 목표는 달성**: alignment→제외기준 추적, validator 강제, UI 표시.

## 개선 백로그
1. **[완료·감사가능성 달성 / 성능효과 미확정] 웹↔풀 alignment 구조화 + 명칭통일** — `EvidenceAlignment`(corpus reduce 2단계 생성), `web:n`/`align:n` 인용 id, validator `ALIGN_COVERAGE`(pool_only/conflict+exclusion 제외기준 인용 강제) + provenance 형식(web:n/align:n) 인정 fix, 드래프터 지시, artifacts/streamlit 감사표. corpus boundary_examples 촘촘화(map+reduce). **실측: alignment→제외 자동포착·인용·추적 성립(감사가능성 ✓). 단 성능은 2k샘플(개선)↔full(회귀)로 scoping 변동에 지배 → 개선/회귀 결론 불가, multi-seed 통제평가 필요.** 계약 테스트 5/5, 하위호환 유지.
2. casemap→E-tier→EXCL_COVERAGE 사슬 계측·강화 (FP 누수 지점 특정).
3. judge operating point / stance 보정 (라벨·dev 없이).
4. corpus/casemap 대표성(10k cap·셔플) 잔여 점검.
5. **[신규 발견] --force가 판정 audit 미삭제 → 재판정 안 됨** (eval_kista는 수정함; run_mas/eval_agentic도 점검 필요).
6. **[완료] 스코프 앵커링 (drift 방지)** — scoping이 owner-doc보다 먼저 돌아 canonical/scope가 확률적으로 broad화(GOCS: GNSS 탈락→FP급증)되던 문제. `scope_query`가 owner-doc 원문을 받아 앵커링. **양날 발견**: 응용맥락 강조 owner-doc은 과협소화(MPUART 0.778→0.657, marine 좁힘). **refinement**: canonical은 core-tech 수준 유지·비필수 응용맥락 배제 → GOCS는 GNSS 유지, MPUART는 core AR/VR/MR 복귀(F1 0.783, recall 0.79). Path import·슬러그 80자 상한 버그fix 동반.

## 개선 #1 설계 (웹↔풀 Evidence Alignment)
- 신규 `EvidenceAlignment{id(align:n), dimension(EvidenceDimension 공유), relation(confirmed/web_only/pool_only/conflict), web_refs[web:n], pool_refs[corpus:kind:n], statement, implies(inclusion/exclusion/scope_boundary/none)}`.
- corpus reduce가 자유서술 `mismatch_with_web_evidence` 대신 구조화 `alignment` 출력(웹 노트에 `web:n`, 풀 발견에 `corpus:kind:n` id 부여 후 2차 호출로 연결).
- 명칭통일: 배치·종합 공유키 동일화(clusters/vocabulary/representative_examples/boundary_examples), SourceType += `alignment`, 하위호환은 pydantic alias+property.
- validator: `EXCL_FROM_ALIGN`(모든 제외기준은 pool_only/conflict alignment 인용), `ALIGN_RESOLVE`(참조 실존 검증).
