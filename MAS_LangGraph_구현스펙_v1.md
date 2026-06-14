# MAS Pseudo-Labeling System — LangGraph 구현 스펙 (v1)

> 대상 독자: LangGraph로 실제 실험을 구현하는 연구자
> 목적: title+abstract 특허를 Snorkel의 labeling function 없이 MAS로 pseudo-labeling하여,
> 다운스트림 학습용 후보 점수표(ranked score file)를 생성한다.

---

## 0. 가장 먼저 — 데이터 경계 (leakage 방지, 반드시 준수)

| 데이터 | 역할 | MAS가 보는가? |
| --- | --- | --- |
| **Candidate pool** (별도 수집, unlabeled) | MAS의 입력. 여기에 score/rank/candidate_type 부여 | **O (입력)** |
| **Gold set** (Bergeaud 6분야, seed/anti-seed 0/1) | 다운스트림 fine-tuned 모델의 **test set 전용** | **X (절대 입력 금지)** |
| **Domain spec** (정의/태스크/대표 키워드/CPC 일부) | Rubric 생성용 입력 | O (rubric 1회) |

규칙:
- MAS는 **gold 특허를 어떤 단계에서도 입력으로 받지 않는다.** gold는 다운스트림 평가에만 쓴다.
- gold label은 rubric 생성·scoring·threshold 결정 어디에도 쓰지 않는다 (Snorkel과의 공정 비교 조건).
- threshold(tau_pos, tau_neg 등)는 **고정값**으로 둔다. gold를 보고 튜닝하지 않는다.

---

## 1. 시스템 개요

MAS는 특허 1건을 입력받아 도메인 관련성 `score(0~1)`와 `candidate_type`을 산출한다.
최종 학습셋(top-K / threshold / equal-N)은 이 산출물을 보고 **후속 단계에서** 구성한다.

설계 원칙: **쉬운 다수는 LLM 1콜로 끝내고, 어려운 소수만 2번째 콜로 escalate.** 특허당 평균 약 1.1~1.3콜.

```
[per-domain, 1회]  Domain Rubric Agent ──► rubric.json
                                              │
[per-patent graph]                            ▼
  START ─► A. Relevance & Route (LLM) ─┬─(easy_pos/easy_neg)─────────────► C. Score & Type (no LLM) ─► END
                                       └─(boundary/hard_negative)─► B. Exclusion (LLM) ─►┘
[batch, no LLM]   D. Ranked Score Output Builder  (전체 결과를 모아 정렬 + CSV)
[batch, 선택]      Calibration  (파일럿 분포 점검 → 필요 시 rubric 1회 수정)
```

| Stage | LLM? | 콜/특허 | 역할 |
| --- | --- | --- | --- |
| 0. Domain Rubric | O | 도메인당 1 (amortized ≈0) | 판단 기준표 생성 |
| A. Relevance & Route | O | 1 | functional/technical 근거 추출 + core_score + route |
| B. Exclusion | O | boundary/hard_neg일 때만 ≈0.1–0.3 | 닮은꼴(confusable) 판별, hard negative 확정 |
| C. Score & Type | X | 0 | final_score + candidate_type (결정론적) |
| D. Output Builder | X | 0 | 도메인별 score 내림차순 rank + CSV |

> Stage A는 기존 설계서의 Evidence-Router(Stage 1)와 Core Relevance(Stage 2)를 **한 콜로 병합**한 것이다.
> 짧은 텍스트에서 둘은 강하게 상관(double counting)하고 콜만 두 배이므로 병합한다.
> functional/technical 근거는 한 콜 안에서 **별도 필드**로 유지해 관점 구분은 보존한다.

---

## 2. State 스키마

LangGraph 그래프는 특허 1건을 처리한다. State는 다음 TypedDict를 사용한다.

```python
from typing import TypedDict, Literal, Optional
from typing_extensions import NotRequired

class EvidenceUnit(TypedDict):
    source: Literal["title", "abstract"]
    exact_text: str                 # 원문에 실제 등장한 표현
    mapped_task: str                # rubric의 어떤 task/confusable에 연결되는지
    status: Literal["present", "implied", "absent", "contradicted"]
    strength: int                   # 0~3

class PatentState(TypedDict):
    # ---- 입력 (candidate pool 1행) ----
    record_id: str
    patent_id: str
    domain: str
    title: str
    abstract: str
    rubric: dict                    # 도메인 rubric (1회 생성, 주입)

    # ---- Stage A 출력 ----
    functional_evidence: NotRequired[list[EvidenceUnit]]
    technical_evidence: NotRequired[list[EvidenceUnit]]
    core_stance: NotRequired[Literal["related", "unrelated", "abstain"]]
    core_score: NotRequired[float]  # 0~1
    route: NotRequired[Literal["easy_positive", "easy_negative",
                               "boundary", "hard_negative", "abstain_candidate"]]

    # ---- Stage B 출력 (조건부) ----
    exclusion_stance: NotRequired[Optional[Literal["not_excluded", "possible_exclusion", "hard_negative"]]]
    exclusion_risk: NotRequired[Optional[float]]      # 0~1
    confusable_category: NotRequired[Optional[str]]
    exclusion_reason: NotRequired[Optional[str]]

    # ---- Stage C 출력 ----
    final_score: NotRequired[float]
    candidate_type: NotRequired[Literal["positive", "easy_negative",
                                         "hard_negative", "boundary", "abstain"]]
```

내부 감사 로그(audit)에는 위 전체를 저장하지만, **최종 CSV에는 산출물 스키마(§6)의 컬럼만** 남긴다.

---

## 3. 노드 명세

### Node A — `relevance_route` (LLM)
- 입력: `rubric, title, abstract`
- 출력: `functional_evidence, technical_evidence, core_stance, core_score, route`
- 책임: (1) title+abstract에서 도메인 task에 연결되는 근거를 functional/technical로 나눠 추출,
  (2) 종합해 단일 `core_score(0~1)`와 `core_stance` 산출,
  (3) `route` 태그 부여. **불확실한 positive는 `easy_positive`가 아니라 `boundary`로 보낸다** (라우팅을 route 하나로만 결정하기 위함).

### Node B — `exclusion_check` (LLM, 조건부)
- 실행 조건: `route ∈ {boundary, hard_negative}` 일 때만.
- 입력: `rubric(out_of_scope_confusables, hard_negative_patterns), title, abstract, functional/technical_evidence`
- 출력: `exclusion_stance, exclusion_risk(0~1), confusable_category, exclusion_reason`
- 책임: 관련 단어가 있어도 도메인 밖(닮은꼴)인지 판정. 예: blockchain 도메인의 generic cryptography, self-driving 도메인의 driver-assist.

### Node C — `score_and_type` (결정론적, LLM 아님)
- 입력: `core_score, route, core_stance, exclusion_risk`
- 출력: `final_score, candidate_type`
- 규칙은 §5.

### Stage D — `output_builder` (배치, LLM 아님)
- 전체 특허 결과를 모아 **도메인별** `final_score` 내림차순 rank 부여 후 CSV 출력. §6.

---

## 4. 엣지 & 라우팅 로직

```python
from langgraph.graph import StateGraph, START, END

def route_after_relevance(state: PatentState) -> str:
    # route 하나로만 분기 → 분기 단순, 비용 최소
    if state["route"] in ("boundary", "hard_negative"):
        return "exclusion_check"
    return "score_and_type"

def build_graph(llm_fast, llm_strong):
    g = StateGraph(PatentState)
    g.add_node("relevance_route", make_relevance_route_node(llm_fast))
    g.add_node("exclusion_check", make_exclusion_node(llm_strong))   # 저빈도 → 강한 모델 허용
    g.add_node("score_and_type", score_and_type)                    # 순수 함수

    g.add_edge(START, "relevance_route")
    g.add_conditional_edges(
        "relevance_route", route_after_relevance,
        {"exclusion_check": "exclusion_check", "score_and_type": "score_and_type"},
    )
    g.add_edge("exclusion_check", "score_and_type")
    g.add_edge("score_and_type", END)
    return g.compile()
```

---

## 5. 결정론적 Scoring & candidate_type 규칙 (Stage C)

```python
TAU_POS    = 0.75   # 고정. gold로 튜닝 금지
TAU_NEG    = 0.25   # 고정
EX_TRIGGER = 0.70   # exclusion_risk 이상이면 override
EX_CAP     = 0.40   # override 시 score 상한

def score_and_type(state: PatentState) -> dict:
    core   = state["core_score"]
    ex     = state.get("exclusion_risk") or 0.0
    score  = core
    if ex >= EX_TRIGGER:
        score = min(score, EX_CAP)               # 닮은꼴은 점수 상한 제한

    # candidate_type: hard_negative는 점수 구간이 아니라 '플래그'로 결정한다 (핵심)
    if state["route"] == "hard_negative" or ex >= EX_TRIGGER:
        ctype = "hard_negative"
    elif state["route"] == "abstain_candidate" or state.get("core_stance") == "abstain":
        ctype = "abstain"
    elif score >= TAU_POS:
        ctype = "positive"
    elif score <= TAU_NEG:
        ctype = "easy_negative"
    else:
        ctype = "boundary"

    return {"final_score": round(score, 6), "candidate_type": ctype}
```

**왜 candidate_type을 플래그로 결정하나 (중요):**
hard negative는 도메인 신호가 많아 core_score가 높게 나오는데, override로 0.40에 캡되면 `score ≤ TAU_NEG(0.25)` 규칙으로는 negative로도 안 뽑히고 boundary에 갇힌다. 그래서 score 구간과 별개로 `candidate_type="hard_negative"` 플래그를 남긴다. 그래야 다운스트림에서 **`negative = easy_negative 샘플 + hard_negative 전체`** 로 Bergeaud식 augmented anti-seed를 구성할 수 있고, "hard negative를 넣으면 다운스트림이 좋아지는가" ablation이 가능해진다.

---

## 6. 산출물 (Stage D)

### 6.1 최종 CSV: `mas_ranked_scores.csv`

| 컬럼 | 필수 | 설명 |
| --- | --- | --- |
| rank | O | **domain별** score 내림차순 순위 (1 = 가장 관련 가능성 높음) |
| score | O | MAS final_score (0~1) |
| record_id | O | 입력 행 추적용 공통 ID |
| patent_id | 권장 | 특허번호 있으면 저장, 없으면 공란 |
| domain | O | 점수 계산 기준 도메인 |
| title | O | 특허 제목 |
| abstract | 권장 | 초록 (파일 크면 앞부분만) |
| **candidate_type** | O | positive / easy_negative / hard_negative / boundary / abstain |

```
rank,score,record_id,patent_id,domain,title,abstract,candidate_type
1,0.932,US9635000B1,US9635000B1,blockchain,"...ledger...","A system using a distributed ledger...",positive
2,0.887,US0000002,US0000002,blockchain,"Smart contract...","A method for executing transaction rules...",positive
3,0.380,US0000003,US0000003,blockchain,"Secure authentication device","...cryptographic authentication without ledger...",hard_negative
```

### 6.2 내부 audit 로그 (CSV에는 미포함)
`route, core_score, exclusion_risk, confusable_category, evidence_units, raw responses` 는 JSONL 등 별도 로그에만 보관 → 디버깅/refinement용.

### 6.3 다운스트림 학습셋 구성 규칙 (참고; MAS 밖)

| 구성 | 규칙 |
| --- | --- |
| positive | `candidate_type == positive` 또는 score 상위 K |
| easy negative | `candidate_type == easy_negative` 샘플 |
| hard negative | `candidate_type == hard_negative` **전체** (희소하므로) |
| Snorkel과 equal-N | Snorkel training set과 동일 N만 선택 |
| coverage 분석 | threshold 완화 시 usable 후보 수 변화 측정 |

---

## 7. 프롬프팅 전략 (일반 원칙)

1. **structured output 고정.** 각 LLM 노드는 Pydantic 스키마로 강제(`with_structured_output`). 자유 서술 금지.
2. **temperature=0**, 가능하면 seed 고정. Stage C가 결정론적이므로 입력 score가 안정적이어야 한다.
3. **rubric은 compact JSON으로 1회 주입.** 매 콜에 들어가는 최대 토큰원이므로 산문 말고 키워드/리스트로.
4. **model tiering (비용 레버).** 고빈도 Node A는 저렴한 모델, 저빈도 Node B는 (원하면) 더 강한 모델. 평균 콜 1.x이므로 총비용 영향 작음.
5. **score 앵커링.** gold calibration이 없으므로, 프롬프트에 score 기준선을 명시해 특허 간 비교 가능성을 확보한다. 예: `0.9~1.0 = 핵심 task를 명시적으로 수행 / 0.6~0.75 = task 암시되나 메커니즘 불명확(boundary) / 0.25 이하 = 도메인 신호 없음`.
6. **few-shot은 hard example 1~2개만.** 쉬운 예가 아니라 **경계 예**(blockchain vs generic crypto, self-driving vs driver-assist)를 넣어 결정 경계를 가르친다. 토큰 절약 + 가장 가치 있는 지점 학습.
7. **gold 금지 명문화.** 프롬프트에 "정답 라벨을 가정하거나 추측하지 말라"를 넣는다.

---

## 8. 프롬프트 템플릿 + 예시

### 8.1 Domain Rubric Agent (도메인당 1회)

System:
```
You build a rubric for patent landscaping. You receive a domain definition.
Produce a compact JSON rubric. Do NOT use or assume any ground-truth labels.
Keep each list short and concrete. Output JSON only.
```
User:
```
Domain: {domain_name}
Short definition: {definition}            # functional-application level
Core functional tasks: {tasks}            # 예: ["decentralized transaction verification", "consensus", ...]
Indicative keywords: {keywords}           # 소수만
CPC/IPC hints (optional): {cpc}

Produce JSON:
{
  "in_scope_tasks":            [ {"task_id": "T1", "desc": "..."} , ... ],
  "key_technical_signals":     [ "distributed ledger", "consensus mechanism", ... ],
  "out_of_scope_confusables":  [ "generic cryptography", "generic authentication", ... ],
  "hard_negative_patterns":    [ "encryption without distributed ledger", ... ],
  "score_anchors": {
     "0.9_1.0": "explicitly performs an in_scope_task with a concrete mechanism",
     "0.6_0.75": "task implied but mechanism unclear -> boundary",
     "0.0_0.25": "no domain signal or only confusable signal"
  }
}
```

### 8.2 Relevance & Route Agent (Node A, 모든 특허)

System:
```
You are the Relevance & Route agent for patent landscaping on title+abstract only.
Extract evidence, judge core relevance, assign a route. Output JSON only.
Do NOT assume any ground-truth label. Score using the rubric's score_anchors.
If relevance is uncertain (task implied but mechanism unclear), set route="boundary",
not "easy_positive".
```
User:
```
Rubric: {rubric_json}
Title: {title}
Abstract: {abstract}

Steps:
1. Extract functional_evidence: units tied to in_scope_tasks (the invention DOES the task).
2. Extract technical_evidence: concrete mechanism/method/device supporting that task.
3. Judge core_stance (related/unrelated/abstain) and core_score (0-1) per score_anchors.
4. Assign route: easy_positive | easy_negative | boundary | hard_negative | abstain_candidate.
   - easy_positive: clear task + mechanism, no confusable signal
   - easy_negative: no domain signal
   - hard_negative: domain words present but looks like an out_of_scope_confusable
   - boundary: task implied but mechanism unclear, or mixed signals
   - abstain_candidate: title+abstract too thin to judge

Output JSON:
{
  "functional_evidence": [{"source":"...","exact_text":"...","mapped_task":"T1","status":"present","strength":3}],
  "technical_evidence":  [{"source":"...","exact_text":"...","mapped_task":"T1","status":"present","strength":2}],
  "core_stance": "related|unrelated|abstain",
  "core_score": 0.0,
  "route": "easy_positive|easy_negative|boundary|hard_negative|abstain_candidate"
}
```

Few-shot (예: blockchain) — 경계를 가르치는 hard example 1개:
```
EXAMPLE (hard_negative):
Title: "Secure authentication device"
Abstract: "A device for cryptographic authentication of users without any distributed ledger."
-> functional_evidence: [] (no in_scope_task performed)
-> technical_evidence: [{"exact_text":"cryptographic authentication","mapped_task":"confusable:generic cryptography","status":"present","strength":2}]
-> core_stance: "unrelated", core_score: 0.2, route: "hard_negative"
(이유: cryptography 신호는 있으나 distributed ledger/consensus 부재 → 닮은꼴)
```

### 8.3 Exclusion Agent (Node B, 조건부)

System:
```
You are the Exclusion agent. The patent is borderline or looks like a domain look-alike.
Decide whether it should be EXCLUDED as out-of-scope. Output JSON only. Do NOT use labels.
```
User:
```
Rubric out_of_scope_confusables: {confusables}
Rubric hard_negative_patterns:   {hard_neg_patterns}
Title: {title}
Abstract: {abstract}
Evidence so far: {functional_evidence} {technical_evidence}

Output JSON:
{
  "exclusion_stance": "not_excluded|possible_exclusion|hard_negative",
  "exclusion_risk": 0.0,            # 0=clearly in-scope, 1=clearly a look-alike
  "confusable_category": "...",     # 해당 시
  "exclusion_reason": "..."
}
```

---

## 9. LangGraph 스켈레톤 코드

LLM 호출부는 추상화했다. OpenAI/Anthropic 등 원하는 provider로 교체 가능.
```python
from pydantic import BaseModel, Field
from typing import Literal, Optional
import csv, json
from langgraph.graph import StateGraph, START, END

# ---------- 1) 구조화 출력 스키마 ----------
class Evidence(BaseModel):
    source: Literal["title", "abstract"]
    exact_text: str
    mapped_task: str
    status: Literal["present", "implied", "absent", "contradicted"]
    strength: int = Field(ge=0, le=3)

class RelevanceOut(BaseModel):
    functional_evidence: list[Evidence] = []
    technical_evidence: list[Evidence] = []
    core_stance: Literal["related", "unrelated", "abstain"]
    core_score: float = Field(ge=0, le=1)
    route: Literal["easy_positive","easy_negative","boundary","hard_negative","abstain_candidate"]

class ExclusionOut(BaseModel):
    exclusion_stance: Literal["not_excluded","possible_exclusion","hard_negative"]
    exclusion_risk: float = Field(ge=0, le=1)
    confusable_category: Optional[str] = None
    exclusion_reason: Optional[str] = None

# ---------- 2) 노드 ----------
def make_relevance_route_node(llm_fast):
    model = llm_fast.with_structured_output(RelevanceOut)   # temperature=0로 생성
    def node(state):
        out: RelevanceOut = model.invoke(
            render_relevance_prompt(state["rubric"], state["title"], state["abstract"])
        )
        return out.model_dump()
    return node

def make_exclusion_node(llm_strong):
    model = llm_strong.with_structured_output(ExclusionOut)
    def node(state):
        out: ExclusionOut = model.invoke(
            render_exclusion_prompt(state["rubric"], state["title"], state["abstract"],
                                    state.get("functional_evidence"), state.get("technical_evidence"))
        )
        return out.model_dump()
    return node

# score_and_type, route_after_relevance 는 §4–5 그대로 사용

# ---------- 3) 그래프 ----------
app = build_graph(llm_fast, llm_strong)   # §4

# ---------- 4) 배치 드라이버 ----------
def run_pool(candidate_rows, rubric_by_domain):
    raw = []
    for row in candidate_rows:
        state = {
            "record_id": row["record_id"],
            "patent_id": row.get("patent_id", ""),
            "domain": row["domain"],
            "title": row["title"],
            "abstract": row["abstract"],
            "rubric": rubric_by_domain[row["domain"]],
        }
        result = app.invoke(state)
        raw.append(result)
        log_audit(result)                  # 전체 state를 JSONL로 (CSV엔 미포함)
    return raw

# ---------- 5) Stage D: 도메인별 rank + CSV ----------
def write_ranked_csv(raw, path="mas_ranked_scores.csv"):
    by_dom = {}
    for r in raw:
        by_dom.setdefault(r["domain"], []).append(r)
    rows = []
    for dom, items in by_dom.items():
        items.sort(key=lambda r: r["final_score"], reverse=True)
        for i, r in enumerate(items, 1):
            rows.append({
                "rank": i, "score": r["final_score"],
                "record_id": r["record_id"], "patent_id": r.get("patent_id",""),
                "domain": dom, "title": r["title"], "abstract": r["abstract"],
                "candidate_type": r["candidate_type"],
            })
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["rank","score","record_id","patent_id",
                                          "domain","title","abstract","candidate_type"])
        w.writeheader(); w.writerows(rows)
```

---

## 10. (선택) Calibration — 도메인당 1회 배치 보정

per-patent 루프는 비용 폭탄이라 금지. 파일럿 분포만 보고 필요 시 rubric 1회 수정.
```python
def calibrate_rubric(pilot_raw, rubric, llm):
    n = len(pilot_raw)
    dist = {}
    for r in pilot_raw:
        dist[r["route"]] = dist.get(r["route"], 0) + 1
    frac = {k: v/n for k, v in dist.items()}
    # 병적 신호 (비-LLM, 공짜):
    pathological = (
        frac.get("easy_positive", 0) > 0.90 or                       # rubric 너무 느슨
        frac.get("abstain_candidate", 0) + frac.get("boundary", 0) > 0.50 or  # rubric 모호
        frac.get("easy_negative", 0) > 0.95                          # 한 클래스 붕괴
    )
    if not pathological:
        return rubric
    low_conf = [r for r in pilot_raw if r["route"] in ("boundary","abstain_candidate")][:5]
    return llm_revise_rubric(llm, rubric, frac, low_conf)            # rubric 수정 콜 1회
```
> 파일럿은 candidate pool에서 뽑는다 (gold 아님). 50~100건 권장.

---

## 11. 재현성 & 비용 체크리스트

- [ ] 모든 LLM 노드 temperature=0, 모델 버전·seed 기록
- [ ] rubric은 버전 태그(`rubric_{domain}_v1.json`)로 고정·저장
- [ ] threshold(TAU_POS/NEG, EX_*)는 config에 고정, gold 미사용
- [ ] 특허당 평균 콜 수 로깅(목표 ≈1.1–1.3), 총 토큰·비용 집계
- [ ] Node A 저렴한 모델 / Node B 강한 모델 (model tiering) 적용 여부 명시
- [ ] 전체 state는 audit JSONL, 최종 CSV는 §6.1 컬럼만
- [ ] gold 특허가 candidate pool에 섞이지 않았는지 검증(중복 제거)

---

## 12. 구현자가 정해야 할 knob (기본값 제시)

| knob | 기본값 | 비고 |
| --- | --- | --- |
| TAU_POS / TAU_NEG | 0.75 / 0.25 | 고정, gold 튜닝 금지 |
| EX_TRIGGER / EX_CAP | 0.70 / 0.40 | exclusion override |
| llm_fast / llm_strong | 저가형 / (선택)상위형 | 비용 레버 |
| 파일럿 크기 | 50–100 | calibration용, candidate pool에서 |
| few-shot 예시 수 | 1–2 (hard example) | 토큰 절약 |
| score_anchors | rubric에 정의 | 점수 비교가능성 확보 |

---

### 한 줄 요약
상시 1콜(Relevance & Route) + 어려울 때만 1콜(Exclusion) + 결정론적 scoring.
gold는 MAS에 안 들어가고 다운스트림 test 전용. hard negative는 점수가 아니라 candidate_type 플래그로 보존해 augmented anti-seed 구성과 ablation을 가능하게 한다.
