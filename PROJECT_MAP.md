# Patent Landscaping 프로젝트 안내

이 작업공간에는 서로 이어지지만 **연구 질문과 평가 방식이 다른 두 프로젝트**가 함께 있다.
성과 수치와 실행 방법을 혼동하지 않도록 아래 문서를 각각의 기준 문서로 사용한다.

## 두 프로젝트 구분

| 구분 | 6월 논문 연구 | 7월 범용 시스템 |
|---|---|---|
| 정식 명칭 | Snorkel vs MAS 약지도 비교 연구 | 질의 기반 Agentic 특허 선별 시스템 |
| 핵심 질문 | MAS 의사라벨이 Snorkel 의사라벨보다 SciBERT 학습에 유용한가? | 도메인별 학습 없이 자연어 질의만으로 유효특허를 직접 판정할 수 있는가? |
| 처리 경로 | 후보 풀 → Snorkel/MAS 의사라벨 → SciBERT 학습 → 골드 평가 | 질의·자료 → 기준서 작성·HITL → LLM 직접 판정·검증 |
| 대표 결과 | MAS+SciBERT 평균 Macro-F1 0.833 / AUC 0.945 | Agentic full5 평균 Macro-F1 0.849 / AUC 0.928 |
| 기준 문서 | `README.md` | `README_MAS.md` |
| 주요 산출물 | `paper/`, `notebooks/`, `figures/` | `experiments/`, `app/`, `DataSet/agentic/` |
| 코드 중심 | `src/snorkel_arm/`, `src/downstream/`, `src/mas/` | `src/agentic/`, `app/`, `scripts/run_agentic.py` |
| 저장소 | `Patent_Landscaping_Final` | `Patent_Landscaping_MAS` |
| 현재 상태 | 연구·논문 산출물 완료 | 벤치마크 완료, 실전 안정화와 휴머노이드 재실행 진행 중 |

`src/mas/`의 LLM 호출·병렬 실행 계층은 두 프로젝트가 공유한다. 그러나 6월 연구의
MAS는 **학습용 의사라벨 생성기**이고, 7월 시스템은 **최종 특허 직접 판정기**다.
따라서 두 결과의 Macro-F1과 AUC는 참고 비교는 가능하지만 동일한 파이프라인의 버전별
성능으로 해석하면 안 된다.

## 읽는 순서

### 6월 논문 연구를 이해하려면

1. `README.md` — 연구 질문, 데이터, 통제 실험, 재현 방법
2. `paper/A_Multi_Agent_Weak_Supervision_Framework_for_Domain_Relevant_Patent_Identification.md`
3. `notebooks/colab_experiment_alldomains.ipynb` — 6개 도메인 학습·평가
4. `기술혁신 팀플_기말발표.pdf` — 발표 자료

### 7월 범용 시스템을 이해하려면

1. `README_MAS.md` — 시스템 사용법과 구성
2. `experiments/FINAL_REPORT.md` — full1~full5 종합 결과
3. `experiments/EXPERIMENTS.md` — 실험 변경 이력과 진단
4. `MAS_개선계획_실행AB분석.md` — 휴머노이드 A/B 원인 분석과 남은 개선
5. `DataSet/agentic/<slug>/criteria_final.md` — 실행별 최종 판단 기준서

## 폴더 소유권

### 6월 논문 연구

- `paper/`: 논문 원고, Word/PDF 생성 코드와 렌더 결과
- `notebooks/`: Colab SciBERT 학습·평가
- `figures/`: 논문·발표용 연구 프레임워크 그림
- `rubrics/`: 6개 벤치마크 도메인의 MAS 루브릭
- `DataSet/processed/`, `DataSet/mas/`, `DataSet/leakage/`: 전처리·의사라벨·누출 점검 자료
- `src/snorkel_arm/`, `src/downstream/`: 비교군과 공통 다운스트림

### 7월 범용 시스템

- `src/agentic/`: 리서치, 코퍼스 분석, 기술축 합성·출처, 기준서, HITL, 직접 판정, 검증
- `app/`: Streamlit 업로드·실행·질문·다운로드 UI
- `experiments/`: E1~full5 실험 로그와 결과 보고서
- `DataSet/agentic/`: 실행별 기준서·판정·감사 산출물
- `DataSet/humanoid/`, `휴머노이드문제/`: 휴머노이드 A2 실전 입력과 결과
- `outputs/`: 실행 로그
- `scripts/reproducibility_report.py`: 서로 격리된 두 실행의 P6 회귀 비교

## 현재 경계

- 6월 논문과 발표 자료에는 7월 Agentic full5 및 휴머노이드 결과가 포함되어 있지 않다.
- 7월 실험 보고서의 Snorkel/MAS+SciBERT 수치는 6월 연구를 비교 기준으로 인용한 것이다.
- 기존 휴머노이드 A/B 결과는 입력·HITL 무결성 문제가 수정되기 전 실행이므로 최종 결과가 아니다.
- 7월 시스템의 사용자 질의·HITL 답변은 실행 간 누적·재사용하지 않는다. 실행 폴더의
  기록은 해당 결과의 감사와 재현에만 사용한다.
- 7월 시스템의 유효특허 포함 여부는 stance와 C/E 충족으로 결정하며, 관련도 점수는
  positive 내부 순위와 평가에만 사용한다.
- 7월 시스템의 다음 확정 산출물은 최신 수정 반영 후 동일 조건 휴머노이드 재실행 결과다.
