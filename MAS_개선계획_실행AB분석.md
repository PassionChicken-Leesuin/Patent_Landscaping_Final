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
- [x] 동일 질문(텍스트 정규화 기준)이 **같은 실행 안에서** 재등장하면 그 실행의
  `human_qa.jsonl` 답변을 재사용(`answered_by: human_prior`) — batch 중단·재개와
  criteria→boundary-loop 연결에만 사용한다. 다른 실행의 답변은 참조하지 않는다.
- 검증: mock batch E2E — 1라운드 답변 정확 매칭, 2라운드 신규 질문은 별개 해시 ID로 재질문(구버전이라면 오배정됐을 시나리오), 기답변 질문 재등장 시 재사용 확인.

### P3. 실행 간 사용자 판결 영속화 — 폐기, 실행 단위 격리로 변경 (2026-07-22)
- [x] 연구 설계상 각 실행은 독립 관측치여야 하므로 `DataSet/agentic/_profiles/` 기반
  교차 실행 저장·조회 기능을 제거했다.
- [x] HITL 답변은 현재 실행의 `human_qa.jsonl`에만 기록하고, 같은 실행의 batch 재개와
  후속 경계 루프에서만 재사용한다.
- [x] 새 실행은 과거 실행의 사용자 질의·답변을 기준서 v1에 주입하지 않는다.
- [x] 기존 `_profiles/humanoid-robot-commercialization-technology.jsonl`도 제거했다.
  실행별 `human_qa.jsonl`은 해당 결과의 감사 기록으로만 유지한다.
- 검증: run-a의 인간 답변은 run-a 재개에서는 재사용되고, 별도 run-b에서는 상속되지
  않는 단위테스트를 추가했다.

### P4. 축 앵커링 + 근거 출처 라벨 — ✅ 완료 (2026-07-22)
- [x] `axes.py`가 사용자 문서의 범위 명확성·기술 완전성·사실 신뢰성을 별도 평가한다.
  사용자 문서는 범위 의도의 우선 앵커지만 완전하다고 가정하지 않으며, 빠진 축은 웹 연구와
  실제 특허 풀에서 자율 보강한다. corpus-only 축은 자동으로 core가 되지 않는다.
- [x] 기술축을 core/supplemental/disputed/excluded로 구조화하고, 활성 축마다 C기준 ≥1을
  deterministic validator가 강제한다.
- [x] 축과 모든 C/E 기준에 `user_query/owner_doc/web/corpus/hitl` 유형의
  `source_refs(reference, claim, strength)`를 기록한다. 누락은 critical 오류다.

### P5. 판정 안정화 — ✅ 완료 (2026-07-22)
- [x] 최종 포함은 `stance=in_domain AND C≥1 AND E=0`으로만 결정한다. 모순은 boundary로
  정규화하고 2차 판정에서 C/E 인용 목록까지 다시 받는다.
- [x] `relevance_score`는 유효특허 내부 랭킹·AUC·감사용이며 포함 컷이 아니다.
  `decision_confidence`는 2차 확인·의심 판정 감사·판정 후 경계 발견 대상을 정한다.
- [x] UI/Excel은 전체 positive 또는 positive 내 상위 N만 출력한다.

### P6. 재현성 회귀 지표 — ✅ 완료 (2026-07-22)
- [x] `scripts/reproducibility_report.py`가 서로 다른 두 실행 폴더의 stance 일치도,
  Cohen's κ, positive 자카드, top-N overlap, 관련도 Spearman, 기술축 일치도,
  C/E 출처 커버리지, HITL 질문 일치도를 비교한다. `--strict`는 기준 미달 시 실패한다.
- [x] validator 예산 소진 시 critical이 남으면 `criteria_blocked.json`을 기록하고
  `CriteriaValidationBlocked`로 중단한다. `criteria_final`을 자동 확정하지 않는다.

### P7. 이슈 원장 + 라우팅 + issue-specific 패치 리바이저 — ✅ 완료 (2026-07-22)
repro-live-a 차단 분석(critical 8→7→6→6→7 비수렴)의 처방. critical은 세 부류이며 각각
다른 처리기를 가진다.

- [x] **결정론 수리(mechanical)**: corpus 근거에 `corpus:<kind>:<n>` 안정 ID 발급(문장은
  표시용으로 분리, `axes.corpus_reference_ids`). 인용 복구는 (i) 접두사 누락, (ii) 동일
  source_type + 정규화 토큰 경계 + 후보 유일일 때의 unique-prefix 매칭만 허용, 전부
  `provenance_repairs.jsonl`에 감사 기록. 미해결 ref는 **다른 유효 출처가 있을 때만**
  drop — 유일한 근거는 남겨서 critical로 유지(조용한 provenance 약화 방지).
- [x] **구조적 이슈 원장**: `CritiqueIssue`에 `category/target_ids/issue_code` 추가,
  결정론 검사는 코드 직접 발급(`AXIS_COVERAGE:A6`, `PROVENANCE_REF:E5`...). 비평자는
  이전 open 이슈를 같은 코드로 재보고하거나 해소 처리(`criteria_issue_ledger.json`).
  **수렴 가드**: 원장 critical이 하나도 해소되지 않는 라운드가 `CRITERIA_NO_PROGRESS_LIMIT`
  (2)회 연속이면 예산을 태우지 않고 조기 차단.
- [x] **라우팅**: `scope_decision` critical은 재작성 금지 → 즉시 HITL. 나머지 critical은
  **필드 단위 패치 리바이저**(`patch_criteria`/`apply_patches`)가 지목된 필드만 수정하고
  나머지는 동결(전체 재작성 churn 제거). 패치 불가 시에만 full redraft fallback.
- [x] **제약된 재비평**: 패치 후 건드리지 않은 필드의 신규 critical은 invariant 수준
  근거(consistency + 구체 id ≥2) 또는 결정론 검사 출신일 때만 인정, 아니면 minor로 강등
  (`constrain_new_criticals`). 차단 보고서는 `quality_critical_issues`와
  `human_pending_issues`(미결 소유자 결정)를 분리하고 status `blocked_pending_human` 구분.
- [x] **HITL 권위 오인 수정**: `ask()` 반환에 `answered_by` 포함. auto 답변은
  "Human expert answers (authoritative)"가 아닌 **"SYSTEM ASSUMPTIONS (NOT owner
  decisions)"** 블록으로 주입되고, judge amendment 라벨도 "Provisional system assumption"으로
  구분. 사람이 결정해야 할 것은 open_questions에 유지된다.
- [x] **testability 계약 고정**: `CriterionOut.observable_signals`(비배타적 관찰 단서)
  추가. 기준은 "기능 task + signals"면 testable로 인정, signal 부재만으로 제외 금지
  (드래프터·비평자·judge 프롬프트 3곳에 명시) — v5→v6 골대 이동 재발 방지.
- 검증: 단위테스트 37개 통과(신규 13: prefix 수리 조건 4종, sole-ref 보존, 원장
  open→resolved, 강등 규칙, 패치 적용 4종), mock E2E(축→기준서→판정→검증) 정상.

부가: TAVILY 키 확보 (현재 Wikipedia fallback — A의 웹 리서치가 Boston Dynamics 1페이지였음).

## 5. 다음 A2 재실행 체크리스트 (P1·P2 + 실행 격리 적용 후)

1. 참고자료 **둘 다** 주입: `DataSet/humanoid/A2_도메인설명.md` + `휴머노이드문제/휴머노이드_핵심자료_decoded.txt` (PDF 대신 decoded.txt 권장)
2. 실행 직후 `research/blocked.jsonl` 확인 — 소유자 문서 차단 여부
3. `research/notes.jsonl`에서 A2 노트 존재 확인 (source_url이 `local://A2_...`)
4. 새 실행에서 제시된 HITL 질문에 다시 답변한다. 과거 도메인 프로파일은 재사용하지 않는다.
5. 새 결과는 score 컷이 아니라 `included=true` positive 집합으로 확정하고, 관련도 점수는
   positive 내부 검토 순서에만 사용한다.
6. 동일 입력의 별도 run id 실행을 한 번 더 만든 뒤 `scripts.reproducibility_report --strict`로
   통제 재현성을 측정한다. 과거 A/B 0.584는 입력도 달랐던 역사적 참고선으로만 둔다.
