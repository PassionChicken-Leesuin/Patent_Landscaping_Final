# HITL 답변 방법 (사용자용)

시스템이 무인 실행 중 자동응답한 범위 질문에 직접 답하려면:

## 방법 1 — interactive 재실행 (권장)
```bash
python -m scripts.run_agentic --query "수소 저장 기술" --input <csv> --hitl interactive
```
기준서 검증 중 콘솔로 질문이 나오면 답변 → 기준서에 반영되어 재판정.

## 방법 2 — batch (파일로 답변)
1. 실행: `python -m scripts.run_agentic --query "..." --input <csv> --hitl batch`
   - 콘솔에 출력된 고유 `run id`를 기록한다.
2. 질문이 있으면 `DataSet/agentic/<slug>/questions_pending.json` 이 생기고 중단됨.
3. 같은 폴더에 `answers.json` 작성:
```json
{
  "HQ1": "수소 생산·정제·연료전지 시스템도 도메인에 포함한다",
  "HQ2": "MOF 저장 소재 포함"
}
```
4. 같은 입력 명령에 `--variant <출력된-run-id> --resume`을 붙여 재실행한다.
   해당 실행의 답변만 반영하고, 다른 실행에는 전달하지 않는다.

## 현재 대기 중인 핵심 질문
- **수소 저장 도메인에 수소 생산·정제·연료전지(공급계) 특허를 포함할 것인가?**
  (골드셋 기준으로는 포함이 정답 — 포함으로 답하면 hydro recall이 크게 오를 것으로 예상)
- 세부 질문 목록: `experiments/PENDING_QUESTIONS.md`
