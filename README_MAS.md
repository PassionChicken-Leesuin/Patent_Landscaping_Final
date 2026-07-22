# Patent Landscaping MAS — 2026-07 질의 기반 유효특허 선별 시스템

> **문서 범위:** 이 문서는 7월에 확장한 **학습 없는 직접판정 시스템**만 다룬다.
> 6월 논문의 Snorkel-vs-MAS 약지도·SciBERT 비교는
> [Patent_Landscaping_Final](https://github.com/PassionChicken-Leesuin/Patent_Landscaping_Final),
> 통합 작업 폴더에서 두 프로젝트의 전체 관계는 `PROJECT_MAP.md`를 참고한다. 여기서
> MAS는 학습용 의사라벨러가 아니라 기준서를 만들고 특허를 최종 판정하는 실행 시스템이다.

자연어 도메인 질의 하나로 **어떤 기술 도메인이든** 특허 풀에서 유효특허(domain-valid
patents)를 선별하는 Multi-Agent System. 학습이 필요 없고, 도메인 정의(판단 기준서)를
스스로 수집·작성하며, 범위가 애매한 지점은 **Human-in-the-Loop 질문**으로 사용자에게
묻는다. Streamlit UI에서 업로드→실행→질문 답변→선별 결과 다운로드까지 한 화면에서
진행된다.

> 6개 골드 도메인(Bergeaud & Verluise) 전수 평가에서 평균 **Macro-F1 0.849 / AUC 0.928**
> — 같은 골드셋으로 학습한 MAS+SciBERT(0.833)를 무학습·벤치마크 블라인드 조건에서 상회.
> 실험 기록: `experiments/EXPERIMENTS.md`, `experiments/FINAL_REPORT.md`.

## 현재 상태

- 6개 벤치마크 도메인 full5 평가는 완료됐다.
- 사용자 문서 우선 처리와 HITL 질문 ID 무결성은 구현됐다.
- 연구 실행의 독립성을 위해 도메인 판결 프로파일 영속화는 폐기했다. 과거 실행의
  사용자 질의·답변은 새 실행에 주입되지 않는다.
- 기술축 앵커링·구조화 출처, C/E 기반 포함 판정, 독립 실행 재현성 회귀평가가 구현됐다.
- 기존 휴머노이드 A/B 결과는 위 수정 전 실행이므로 최신 코드로 통제 재실행해야 한다.

## 실행 격리 원칙

각 실행은 독립된 연구 관측치다. 한 실행에서 받은 HITL 답변은 그 실행의 기준서 작성,
중단 후 재개, 판정 후 경계 재검토에만 사용한다. 실행이 끝난 뒤 해당 답변을 도메인
프로파일이나 사용자 이력으로 축적하여 다음 실행에 재사용하지 않는다.

`human_qa.jsonl`과 `query.json`은 해당 실행의 결과를 감사·재현하기 위한 **실행 내부
산출물**이다. 새 UI 실행은 고유 run id/variant의 별도 작업공간에서 시작하며, 다른
작업공간의 질의·답변을 읽지 않는다.

## 파이프라인

```
자연어 질의 → [1] 스코핑 → [2] 웹 리서치(Tavily/Wikipedia, 벤치마크 누출 3중 차단)
            → [2b] 사용자 참고자료 반영(pdf/txt/md)
            → [3] 판정 풀 전체 통독(map-reduce corpus digest)
            → [4a] 사용자 문서 품질평가 + 기술축 합성(문서 앵커, 웹·특허 풀 자율 보강,
                   축별 구조화 출처)
            → [4b] 문장형 판단 기준서(C/E 기준 + 축 매핑 + 클러스터별 scope 판결)
            → [5] 기준서 Validator 루프 (경계는 broad/narrow 규칙으로 표본 실판정하여
                  실제로 라벨이 갈리는 질문만 인간에게 질문 — HITL)
            → [6] 기준 인용 엄밀 판정 (포함 = in_domain + C 충족 + E 충돌 없음,
                  relevance_score는 순위용, decision_confidence는 재검사용)
            → [7] 판정 Validator 루프 (의심 판정 감사 → 재판정)
            → [옵션] 경계 피드백 루프 (판정 후 애매 구간에서 새 범위질문 도출)
```

모든 중간 산출물(리서치 노트, corpus digest, 기준서 버전들, 검증 critique, HITL Q&A,
판정 audit)은 `DataSet/agentic/<run-slug>/`에 파일로 남고 단계별로 캐시된다. 캐시는
같은 실행의 중단·재개에만 사용하고, 새 실행의 판단 컨텍스트로 가져오지 않는다.

## Streamlit UI

```bash
python -m venv .venv-mac && .venv-mac/bin/pip install -r requirements.txt
.venv-mac/bin/streamlit run app/streamlit_app.py
```

1. **업로드** — WIPS 다운로드 xlsx(자동 인식·패밀리 중복제거) 또는 title/abstract CSV,
   도메인 자연어 질의 + 상세 설명, 참고자료(pdf/txt/md).
2. **실행** — 파이프라인이 백그라운드로 돌며 단계 진행도·실시간 로그가 표시된다.
3. **HITL** — 시스템이 범위 질문을 만들면 화면에 폼이 뜨고, 답변을 제출하면 그
   지점부터 즉시 이어서 실행된다(질문·답변은 모두 기준서에 반영되고 기록됨).
4. **산출물** — 기준서 버전별 열람, HITL Q&A 로그, 리서치·코퍼스 요약, 경계 검증
   (broad/narrow flip 실측), 검증 이력.
5. **다운로드** — C/E 계약을 통과한 전체 유효특허 또는 그 안의 관련도 상위 N건을
   원본 컬럼과 병합한 xlsx(+판단기준서 시트)로 내려받는다. 점수 컷은 포함 여부를
   바꾸지 않는다.

## CLI

```bash
# 오프라인 스모크 (키 불필요)
python -m scripts.run_agentic --query "hydrogen storage technology" --input pool.csv \
       --mock --limit 20 --hitl off
# 실전 (.env에 OPENAI_API_KEY_1..N, 선택 TAVILY_API_KEY)
python -m scripts.run_agentic --query "휴머노이드 로봇 상용화 기술" --input pool.csv \
       --workers 40 --boundary-loop
```

일반 CLI 실행은 자동으로 고유 run id를 만들어 과거 동일 질의 작업공간과 분리한다.
중단된 batch 실행을 이어갈 때만 출력된 run id를 `--variant <run-id> --resume`으로
명시한다. `--resume`에 run id가 없으면 과거 실행을 잘못 고르는 것을 막기 위해 중단한다.

`--hitl interactive`(콘솔 질문) / `batch`(questions_pending.json → answers.json 작성 후
같은 run id로 재개) / `off`(무인: 보수적 자동답변 기록).

## 독립 실행 재현성 회귀(P6)

같은 질의·자료·특허 풀을 서로 다른 run id로 두 번 실행한 뒤 비교한다. 한 실행의
질의·HITL 답변이나 캐시는 다른 실행에 전달하지 않는다.

```bash
python -m scripts.reproducibility_report \
  --run-a <첫번째-run-slug> --run-b <두번째-run-slug> --top-n 1000 --strict
```

JSON 보고서와 판정이 달라진 특허 CSV가 `outputs/`에 생성된다. `--strict`는 stance,
κ, positive 자카드, top-N 중복, 축 일치도, 출처 커버리지 중 하나라도 기준에 못 미치면
종료 코드 1을 반환한다.

## 레포 구성

```
app/            Streamlit UI (pool 변환 / 실행 관리 / 산출물 뷰어)
src/agentic/    파이프라인 (research, corpus, criteria, validator, judge, hitl, ...)
src/mas/        LLM 계층 (다중 키 병렬 KeyPool, 구조화 출력, mock)
scripts/        run_agentic, eval_agentic, score_agentic, reproducibility_report 등
experiments/    실험 기록 (E1~full5) + 평가 결과
```

6월 논문 연구(Snorkel vs MAS 약지도 비교, SciBERT 다운스트림)는 별도 레포
[Patent_Landscaping_Final](https://github.com/PassionChicken-Leesuin/Patent_Landscaping_Final)에,
이 7월 시스템은
[Patent_Landscaping_MAS](https://github.com/PassionChicken-Leesuin/Patent_Landscaping_MAS)에 저장한다.
