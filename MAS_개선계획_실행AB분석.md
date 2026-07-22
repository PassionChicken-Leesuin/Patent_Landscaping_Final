# 휴머노이드 A2 실행 A/B 비교 분석과 시스템 개선 계획 (2026-07-19)

> **용도**: 다음 세션에서 시스템을 개선할 때 **이 문서부터 읽고 §4 우선순위대로 구현**한다.
> 모든 수치·파일 경로·라인 번호는 2026-07-19 실행 산출물에서 실측·검증한 것이다.

---

## 1. 두 실행 개요

| | 실행 A (유효특허_선별결과.xlsx) | 실행 B (유효특허_선별결과2.xlsx) |
|---|---|---|
| 실행 경로 | CLI (`scripts.run_agentic`), 이 맥 | Streamlit UI, **다른 기기 추정** (워크스페이스가 이 맥에 없음) |
| 워크스페이스 | `DataSet/agentic/humanoid-robot-commercialization-technology/` | slug `humanoid-robot-commercialization-technology-ui20260719105922` (미발견) |
| 특허 풀 | `DataSet/humanoid/pool_wips.csv` 3,319건 | **동일 풀** (record_id 100% 일치) |
| 참고자료(--local-doc/업로드) | `A2_도메인설명.md`(출제문 요지) + `휴머노이드_핵심자료_decoded.txt`(KIMM) | **`휴머노이드_핵심자료.pdf`만** (사용자 확인). **출제문 없음** |
| HITL | batch 모드 6문항 답변 (단, 3건 오배정 — §3.2) | **흔적 없음** (기준서·시트 모두) |
| 산출 | 선별 1,595건 / score≥0.75 = 1,143건 | 1,064건 (0.75 컷 적용된 상태) |

주의: 두 xlsx의 `patent_id`는 표기 형식이 달라 직접 비교하면 틀어진다. **비교는 반드시 `record_id`로** 할 것.

## 2. 결과 차이 (양쪽 모두 score ≥ 0.75, record_id 기준)

- A 1,143건 / B 1,064건, **공통 814건** (자카드 0.584, B의 76.5%가 A에 포함)
- A에만 329건 (그중 320건이 정확히 0.75 — A의 컷 경계층)
- B에만 250건 — 이들이 A 실행에서 받은 점수: **0.7 × 123건, 0.1 × 126건(+0.2 ×1)**
  → 절반은 컷 바로 아래 경계 사례, **절반은 기준서 변경으로 판정이 완전히 뒤집힌 것**
- 주제 성향 (제목+초록 키워드, 배타 집합 비중):

| 주제 | A에만(329) | B에만(250) | Δ |
|---|---|---|---|
| 안전/충돌감지/비상정지 | 1.2% | **15.6%** | +14.4pp |
| 로봇손/파지/조작 | **37.4%** | 28.8% | −8.6pp |
| 액추에이터/관절/감속기 | **32.5%** | 20.4% | −12.1pp |
| 보행/이족/균형 | **8.8%** | 0.8% | −8.0pp |

- 기준서 차이가 직접 원인:
  - **A**: 소유자 판결 3건이 CONDITIONAL로 반영(보행 전이 기술 포함 / 액추에이터·로봇손 병목 포함 / 협동안전은 HRI 한정 포함). 단 안전축 빈약.
  - **B**: `Autonomous mobile robots` 통째 OUT(→보행 전멸), `Soft robotics` 통째 OUT, `Collaborative robots` 통째 IN(→협동로봇 안전 특허 대량 유입). C3~C6이 **출제문에 없는 비즈니스 기준**(양산·공급망 / 인프라 상호운용·통신 / 음성·제스처 UI / 노동력·경제성)으로 표류, 경계지침엔 "렌탈 등 경제모델 특허 in"까지 등장. 보행·균형, 액추에이터·전원(출제문 축 2·3의 핵심)이 기준서 어디에도 없음. E4("generic robotic systems … excluded")는 C기준의 부정형을 되풀이한 순환 기준.

## 3. 원인 분석 (인풋 · 질문 · 답변 실측)

### 3.1 [A] 출제문이 초안 작성 시점에 "벤치마크 누출"로 차단됨 ← 가장 큰 발견
`research/blocked.jsonl`에 기록:
```json
{"layer": "llm_flag", "rule": "page_is_benchmark_leak", "url": "local://A2_도메인설명.md#chunk0"}
```
- 골드 도메인 실험용 누출 3중 차단 장치가 실전 모드에서 **도메인 소유자 문서를 차단**. A2 문서의 "수집된 특허 모집단은 B25J 계열…" 같은 풀 구성 설명을 평가셋 정보로 오판한 것으로 추정.
- 콘솔에는 `[local-doc] A2_도메인설명.md: 1 chunks -> +0 notes`만 출력 — **조용한 실패**.
- 그 결과 **v1 초안 + HITL 질문 3건은 출제문 없이 작성됨**. 그 시점 증거 풀: KIMM 56노트 + 웹 5노트(TAVILY 키 없음 → Wikipedia fallback, **5개 전부 Boston Dynamics 문서 1페이지**) = 82%가 KIMM → A 기준서의 하드웨어 편향.
- 재실행(HITL 답변 후) 때 차단 경로가 페이지 캐시를 안 남긴 덕에 재처리됐고, 이번엔 (비결정적으로) 통과 → **+7노트, 3축·경계사례를 완벽히 담은 내용**. 하지만 v1 골격·질문이 확정된 뒤라 v2~v4 수정에만 참고됨.
- validator는 예산 소진으로 **critical 이슈 3개가 남은 v4를 그대로 확정** (로그: `WARNING: budget exhausted — finalizing v4 (fewest critical issues: 3)`).

### 3.2 [A] HITL 배치 답변 오배정 — 질문 ID 충돌 버그 (코드 확정)
- [criteria.py:145](src/agentic/criteria.py#L145) `id=q.id`: 질문 ID를 **기준서 작성 LLM이 버전마다 Q1부터 다시 매김**.
- [hitl.py:88](src/agentic/hitl.py#L88) `answers[q.id]`: batch 모드는 `answers.json`을 ID로만 매칭.
- 실측: `answers.json` 키는 Q1~Q3뿐인데 `human_qa.jsonl`엔 6문항이 모두 `human_batch`로 기록 — **2라운드 신규 질문 3건(소프트로보틱스 재질문 / 일반 로봇제어 / 로봇 학습)이 1라운드 답변을 그대로 오배정**받음. 기록상 사람이 답한 것처럼 보이는 조용한 오염.

### 3.3 [B] 출제문 미입력 + HITL 부재 → "상용화"의 의미 표류
- 사용자 확인: B에는 **KIMM PDF만 업로드**, A2 출제문 없음. HITL 반영 흔적도 없음.
- 앵커가 없으니 LLM이 "commercialization"을 일반 지식(비즈니스 관점)으로 해석 → C3~C6.
- **미확인 항목**: B 기준서에 KIMM의 병목 강조(액추에이터·감속기)조차 없다 → PDF 인제스트가 실제로 노트를 냈는지 의심. 확인법: B를 돌린 기기에서 `DataSet/agentic/humanoid-robot-commercialization-technology-ui20260719105922/research/{notes,blocked}.jsonl` 확인. (PDF는 CID 디코딩 경유 — decoded.txt와 달리 실패 여지 있음. UI 업로드→localdoc 주입 경로 자체도 CLI와 동일 동작인지 검증 필요.)

### 3.4 [공통] 점수 해상도 붕괴 + 컷 위치
- [judge.py:87](src/agentic/judge.py#L87)이 "연속 확률, 기본값 반복 금지"를 지시하지만 실제 출력은 **{0.1, 0.2, 0.7, 0.75, 0.8, 0.85}로 스냅**되고 중앙값이 정확히 0.75 = 사용자 컷. 프롬프트의 점수 가이드(0.8/0.6/0.45…)가 오히려 앵커로 작동.
- 컷이 최대 질량 위를 지나므로 기준서가 조금만 흔들려도 수백 건이 플립(실측 123건).

### 3.5 [공통] 근거 추적 불가
- A 최종 기준서의 근거 라벨은 전부 `corpus:*` (task×6, technique×2, boundary×4). **소유자 문서/웹/HITL에서 왔는지 구분이 안 남아** 사후 감사가 불가능.

## 4. 개선 구현 계획 (우선순위순)

### P1. 소유자 문서 1급 처리 — `src/agentic/localdocs.py`, `criteria.py` ✅ 완료 (2026-07-20)
- [x] LLM `page_is_benchmark_leak` 플래그는 소유자 문서에 **advisory로만** 기록(`layer: llm_flag_advisory`, 청크는 유지). 정규식 content scan 히트는 **fail-loud**: `OwnerDocBlocked` 예외로 중단 + 안내, 의도된 경우 `--local-doc-allow-flagged`로 강행(blocked.jsonl에 `overridden: true` 기록).
- [x] ≤8KB 문서(`AC.OWNER_DOC_FULLTEXT_MAX_CHARS`)는 원문 전체를 `owner_docs.json`에 저장 → `draft_criteria`가 "OWNER DOMAIN DEFINITION (최상위 권위)" 블록으로 주입 + 시스템 프롬프트 `_OWNER_CLAUSE`(축별 C기준 ≥1 강제, `owner_doc:` 소스 인용). 추가: 소유자 문서 노트는 `page_is_relevant` 필터도 우회(웹 페이지용 필터).
- [x] 노트 0 + 원문 주입 불가 문서는 콘솔 `!!!!` 경고 + `criteria_final.md` 상단 blockquote 경고(`pipeline.build_criteria`, `unreflected_owner_docs`).
- 검증: 단위테스트 17개 통과, mock E2E(A2 문서 주입·재실행 멱등·차단·강행 4경로) 확인.

### P2. HITL 무결성 — `hitl.py` 중심 ✅ 완료 (2026-07-20)
- [x] `hitl.question_id()`: 질문 정규화 텍스트의 sha1 해시로 **전역 고유 ID** — `HITL.ask()` 진입 시 모든 질문 ID를 일괄 재부여(`_uniquify`, 배치 내 중복 질문도 제거). LLM이 부여한 Q1.. ID는 표시용으로만 남음.
- [x] ID=텍스트해시이므로 batch 매칭은 구조적으로 텍스트 대조와 동치. long-form `{"question","answer"}` 답변은 추가 교차검증, 불일치 시 무시+재질문(`PendingHumanInput`). 구식 Q1 키는 매칭 실패 → 재질문(fail-loud).
- [x] 동일 질문(텍스트 정규화 기준)이 재등장하면 `human_qa.jsonl`/프로파일의 기존 인간 답변을 재사용(`answered_by: human_prior`) — off 모드에서도 auto보다 우선. (의미적 유사-중복은 human_qa 전체가 draft에 주입되므로 프롬프트 수준에서 흡수)
- 검증: mock batch E2E — 1라운드 답변 정확 매칭, 2라운드 신규 질문은 별개 해시 ID로 재질문(구버전이라면 오배정됐을 시나리오), 기답변 질문 재등장 시 재사용 확인.

### P3. 소유자 판결(HITL Q&A) 영속화 — 도메인 프로파일 ✅ 완료 (2026-07-20)
- [x] `hitl.profile_path(canonical_name, mock)` → `DataSet/agentic/_profiles/<canonical-slug>.jsonl`. `HITL._log`가 인간 답변(human/human_batch)을 자동 append. mock은 `mock-` 접두 별도 파일(실전 오염 방지).
- [x] `criteria_loop`가 시작 시 `hitl.profile_qa()`로 판결 전체를 human_qa_all에 시딩 → **v1 초안부터** "Human expert answers (authoritative)" 블록으로 주입 (질문이 재등장하지 않아도 반영). judge/boundary-loop HITL에도 프로파일 연결.
- [x] **A실행의 정당한 판결 3건을 실전 프로파일에 시딩 완료** (`_profiles/humanoid-robot-commercialization-technology.jsonl`; §3.2에서 오배정으로 판명된 boundary-loop 3건은 제외).
- 검증: mock E2E — p3a 워크스페이스에서 답변 → 새 p3b 워크스페이스에서 "domain profile: 1건 주입" + 동일 질문 재질문 없이 재사용 확인.

### P4. 축 앵커링 + 근거 출처 라벨 — `criteria.py`, `validator.py`
- [ ] 소유자 문서에서 기술축을 추출해 기준서 스키마의 골격으로 강제: **축마다 C기준 ≥1 + 경계 판례**.
- [ ] validator에 **축 커버리지 체크** 추가 — 미커버 축은 곧 HITL 질문으로. 소유자 축에 없는 기준(B의 C3~C6류)은 근거 출처 명시 + 소유자 확인 질문.
- [ ] 근거 라벨을 `owner_doc:` / `corpus:` / `web:` / `hitl:`로 구분 (§3.5 해결).

### P5. 판정 안정화 — `judge.py` + 선별 컷 전략
- [ ] 선별을 원점수 임계값 대신 **stance(positive) 기반**으로, 점수는 랭킹용으로만. 또는 C/E 만족 구조에서 결정론적 점수 산출.
- [ ] 최소한: 컷을 점수 질량 밀집점(0.75) 위에 두지 않기 — 점수 분포 출력 후 컷 위치 경고.

### P6. 재현성 회귀 지표 — `experiments/`
- [ ] 동일 풀·동일 답변·동일 자료로 2회 실행 → 선별 자카드를 정식 지표로. 이번 A/B 0.584가 참고선(단, 입력도 달랐으므로 통제 재실행으로 진짜 기준선을 먼저 측정).
- [ ] validator 예산 소진 시 critical 잔존이면 자동 확정 대신 경고 + HITL 에스컬레이션.

부가: TAVILY 키 확보 (현재 Wikipedia fallback — A의 웹 리서치가 Boston Dynamics 1페이지였음).

## 5. 다음 A2 재실행 체크리스트 (P1~P3 적용 후)

1. 참고자료 **둘 다** 주입: `DataSet/humanoid/A2_도메인설명.md` + `휴머노이드문제/휴머노이드_핵심자료_decoded.txt` (PDF 대신 decoded.txt 권장)
2. 실행 직후 `research/blocked.jsonl` 확인 — 소유자 문서 차단 여부
3. `research/notes.jsonl`에서 A2 노트 존재 확인 (source_url이 `local://A2_...`)
4. HITL 답변은 기존 소유자 판결 3건(도메인 프로파일) 재사용 + 신규 질문만 답변
5. 결과를 A/B와 record_id 자카드로 비교 — 개선 전 0.584 대비 상승 확인
