# Patent Landscaping MAS — 질의 기반 유효특허 선별 시스템

자연어 도메인 질의 하나로 **어떤 기술 도메인이든** 특허 풀에서 유효특허(domain-valid
patents)를 선별하는 Multi-Agent System. 학습이 필요 없고, 도메인 정의(판단 기준서)를
스스로 수집·작성하며, 범위가 애매한 지점은 **Human-in-the-Loop 질문**으로 사용자에게
묻는다. Streamlit UI에서 업로드→실행→질문 답변→선별 결과 다운로드까지 한 화면에서
진행된다.

> 6개 골드 도메인(Bergeaud & Verluise) 전수 평가에서 평균 **Macro-F1 0.849 / AUC 0.928**
> — 같은 골드셋으로 학습한 MAS+SciBERT(0.833)를 무학습·벤치마크 블라인드 조건에서 상회.
> 실험 기록: `experiments/EXPERIMENTS.md`, `experiments/FINAL_REPORT.md`.

## 파이프라인

```
자연어 질의 → [1] 스코핑 → [2] 웹 리서치(Tavily/Wikipedia, 벤치마크 누출 3중 차단)
            → [2b] 사용자 참고자료 반영(pdf/txt/md)
            → [3] 판정 풀 전체 통독(map-reduce corpus digest)
            → [4] 문장형 판단 기준서(C/E 기준 + 클러스터별 scope 판결 + open questions)
            → [5] 기준서 Validator 루프 (경계는 broad/narrow 규칙으로 표본 실판정하여
                  실제로 라벨이 갈리는 질문만 인간에게 질문 — HITL)
            → [6] 기준 인용 엄밀 판정 (다중 API 키 병렬, C∩E 충돌 시 2차 확인)
            → [7] 판정 Validator 루프 (의심 판정 감사 → 재판정)
            → [옵션] 경계 피드백 루프 (판정 후 애매 구간에서 새 범위질문 도출)
```

모든 중간 산출물(리서치 노트, corpus digest, 기준서 버전들, 검증 critique, HITL Q&A,
판정 audit)은 `DataSet/agentic/<slug>/`에 파일로 남고 단계별로 캐시되어, 중단·재실행
시 끝난 단계는 건너뛴다.

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
5. **다운로드** — score 임계값 또는 상위 N건으로 유효특허를 선별해 원본 컬럼이
   병합된 xlsx(+판단기준서 시트)로 내려받는다.

## CLI

```bash
# 오프라인 스모크 (키 불필요)
python -m scripts.run_agentic --query "hydrogen storage technology" --input pool.csv \
       --mock --limit 20 --hitl off
# 실전 (.env에 OPENAI_API_KEY_1..N, 선택 TAVILY_API_KEY)
python -m scripts.run_agentic --query "휴머노이드 로봇 상용화 기술" --input pool.csv \
       --workers 40 --boundary-loop
```

`--hitl interactive`(콘솔 질문) / `batch`(questions_pending.json → answers.json 작성 후
재실행) / `off`(무인: 보수적 자동답변 기록).

## 레포 구성

```
app/            Streamlit UI (pool 변환 / 실행 관리 / 산출물 뷰어)
src/agentic/    파이프라인 (research, corpus, criteria, validator, judge, hitl, ...)
src/mas/        LLM 계층 (다중 키 병렬 KeyPool, 구조화 출력, mock)
scripts/        run_agentic, eval_agentic, score_agentic, hitl_report 등
experiments/    실험 기록 (E1~full5) + 평가 결과
```

원 팀 프로젝트(Snorkel vs MAS 약지도 비교, SciBERT 다운스트림)는 별도 레포
[Patent_Landscaping_Final](https://github.com/PassionChicken-Leesuin/Patent_Landscaping_Final)에 있다.
