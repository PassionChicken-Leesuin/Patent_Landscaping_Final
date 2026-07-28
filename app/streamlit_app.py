"""MAS 유효특허 선별 시스템 — Streamlit UI.

실행:
  Windows:  python -m streamlit run app/streamlit_app.py
  macOS:    .venv-mac/bin/streamlit run app/streamlit_app.py

업로드(특허 xlsx + 도메인 설명 + 참고자료) → agentic 파이프라인 실행(batch HITL) →
질문이 나오면 UI에서 실시간 답변 → 중간 산출물(기준서·기술축·Q&A·이슈원장·판정)을
모두 표시 → 선별 특허 xlsx 다운로드. 기준서 차단(fail-loud) 시 차단 보고서와
재시작 버튼을 제공한다.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import os

import pandas as pd
import streamlit as st

from app import artifacts, pool_convert, runner

# Streamlit Cloud injects API keys via Secrets; bridge them into os.environ so the
# pipeline subprocess (scripts.run_agentic -> load_openai_keys) inherits OPENAI_API_KEY(_N).
try:
    for _k, _v in dict(st.secrets).items():
        if isinstance(_v, str):
            os.environ.setdefault(_k, _v)
except Exception:
    pass

st.set_page_config(page_title="MAS 유효특허 선별", page_icon="🛰️", layout="wide")

STATUS_LABEL = {
    "new": ("⚪ 대기", "실행 전입니다."),
    "running": ("🔵 실행 중", "파이프라인이 동작하고 있습니다."),
    "waiting_human": ("🟠 인간 답변 대기", "시스템이 범위 질문에 대한 답을 기다립니다."),
    "blocked": ("🛑 기준서 차단", "기준서에 critical 결함이 남아 판정을 시작하지 않았습니다 "
                                "(fail-loud). 아래 차단 보고서를 확인하세요."),
    "done": ("🟢 완료", "판정이 끝났습니다. 아래에서 결과를 확인하세요."),
    "stopped": ("⏹️ 중단됨", "사용자가 중단했습니다. 재시작하면 이어서 실행됩니다."),
    "error": ("🔴 오류", "로그를 확인하세요. 재시작하면 캐시된 단계부터 이어서 실행됩니다."),
}


# ================================================================ helpers
@st.cache_data(ttl=86400, show_spinner=False)
def _url_reachable(url: str) -> str:
    """Best-effort liveness check so we never present a link that 404s.
    Returns 'ok' (status < 400), 'dead' (>= 400 / connection error), or 'unknown' (check
    itself failed, e.g. no network). Cached 1 day per URL. HEAD first, GET fallback."""
    ua = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"}
    try:
        import requests
    except Exception:
        return "unknown"
    try:
        try:
            r = requests.head(url, allow_redirects=True, timeout=6, headers=ua)
            if r.status_code >= 400 or r.status_code == 405:   # some hosts reject HEAD
                r = requests.get(url, allow_redirects=True, timeout=8, headers=ua, stream=True)
        except requests.RequestException:
            r = requests.get(url, allow_redirects=True, timeout=8, headers=ua, stream=True)
        return "ok" if r.status_code < 400 else "dead"
    except requests.RequestException:
        return "dead"
    except Exception:
        return "unknown"


def _render_research_sources(ws: Path):
    """Verified, clickable research sources — only pages actually fetched (never
    hallucinated), with dead links hidden so the user never clicks into a 404."""
    srcs = artifacts.research_sources(ws)
    if not srcs:
        st.caption("수집된 외부 자료가 없습니다 (도메인 질의·특허 풀 기반으로 기준서를 합성).")
        return
    st.markdown(f"**🔗 수집 자료 {len(srcs)}건** — 실제로 페치·인용된 출처만 (지어낸 링크 없음)")
    check = st.checkbox("링크 접속 확인 후 표시 (404 자동 숨김)", value=True, key="chk_src_live")
    shown = dead = 0
    for s in srcs:
        status = _url_reachable(s["url"]) if check else "ok"
        if status == "dead":
            dead += 1
            continue
        meta = f"— 근거 노트 {s['n_notes']}건" + (f" · {s['source']}" if s.get("source") else "")
        warn = " ⚠︎(접속 확인 안 됨)" if status == "unknown" else ""
        st.markdown(f"- [{s['title']}]({s['url']}) {meta}{warn}")
        shown += 1
    if dead:
        st.caption(f"접속 불가 {dead}건은 숨겼습니다 (404 방지).")
    if check and shown == 0 and dead:
        st.info("수집 시점엔 유효했으나 현재 모두 접속 불가로 확인됩니다.")


def _render_alignment(ws: Path):
    """Web<->pool alignment audit table: how external evidence was compared against the actual
    pool, and which comparisons drove exclusions (the precision lever). Fully traceable —
    web_refs link to real sources, pool_refs cite corpus findings."""
    align = artifacts.corpus_alignment(ws)
    if not align:
        return
    st.markdown("---")
    from collections import Counter
    rel = Counter(a.get("relation") for a in align)
    st.markdown(f"**🔗↔ 웹↔풀 정합 정렬 {len(align)}행** — 웹 근거와 실제 특허 풀을 대비한 감사 표")
    st.caption(f"confirmed {rel.get('confirmed',0)} · web_only {rel.get('web_only',0)} · "
               f"pool_only {rel.get('pool_only',0)} · conflict {rel.get('conflict',0)}  "
               f"— pool_only/conflict + implies=exclusion 이 look-alike 제외를 강제합니다.")
    urlmap = artifacts.web_ref_urls(ws)
    icon = {"confirmed": "🟢", "web_only": "🔵", "pool_only": "🟠", "conflict": "🔴"}
    # overview table (sortable)
    st.dataframe(pd.DataFrame([{
        "id": a.get("id"), "dimension": a.get("dimension"),
        "relation": a.get("relation"), "implies": a.get("implies"),
        "web_refs": " ".join(a.get("web_refs", [])),
        "pool_refs": " ".join(a.get("pool_refs", [])),
        "statement": a.get("statement", ""),
    } for a in align], columns=["id", "dimension", "relation", "implies",
                                "web_refs", "pool_refs", "statement"]), width="stretch")
    # exclusion-driving rows in detail, with clickable web sources
    excl = [a for a in align if a.get("relation") in ("pool_only", "conflict")
            and a.get("implies") == "exclusion"]
    if excl:
        st.markdown(f"**⛔ 제외를 유발한 정렬 {len(excl)}행 (precision 레버 — 기준서 E가 이걸 인용)**")
        for a in excl:
            webs = " · ".join(f"[{w}]({urlmap[w]})" if urlmap.get(w) else w
                              for w in a.get("web_refs", [])) or "(웹 근거 없음)"
            pools = " · ".join(a.get("pool_refs", [])) or "(풀 근거 없음)"
            st.markdown(f"- {icon.get(a.get('relation'),'')} **`{a.get('id')}`** "
                        f"({a.get('relation')}) — {a.get('statement','')}  \n"
                        f"  <small>웹: {webs} · 풀: {pools}</small>", unsafe_allow_html=True)


@st.cache_data(show_spinner="파일을 읽는 중...")
def _read_upload(name: str, data: bytes) -> pd.DataFrame:
    return pool_convert.read_uploaded(name, data)


def _go(run_dir: Path | None):
    st.session_state.run_dir = str(run_dir) if run_dir else None
    st.session_state.pop("last_status", None)
    st.rerun()


# ================================================================ sidebar
with st.sidebar:
    st.title("🛰️ MAS 특허 선별")
    st.caption("질의 → 정합 진단 → 설계안 → 사례 매핑(자기수정) → "
               "범위 결정(HITL) → 기준서 → 전수 판정")
    if st.button("➕ 새 실행 만들기", width="stretch"):
        _go(None)
    runs = runner.list_runs()
    if runs:
        st.subheader("실행 이력")
        for rd in runs[:15]:
            m = runner.load_manifest(rd)
            status = runner.get_status(rd)
            icon = STATUS_LABEL[status][0].split()[0]
            label = f"{icon} {m.get('run_id','?')} · {m.get('query','')[:18]}"
            if st.button(label, key=f"open_{rd.name}", width="stretch"):
                _go(rd)


# ================================================================ setup page
def render_setup():
    st.header("새 실행 — 데이터·도메인 정의 업로드")
    col1, col2 = st.columns([3, 2], gap="large")

    with col1:
        st.subheader("1) 특허 풀 파일")
        up = st.file_uploader("WIPS xlsx 또는 title/abstract를 가진 csv·xlsx",
                              type=["xlsx", "xls", "csv"])
        pool_df, report, fmt, id_col = None, [], None, ""
        if up is not None:
            df = _read_upload(up.name, up.getvalue())
            fmt = pool_convert.sniff_format(df)
            if fmt == "wips":
                dedup = st.checkbox("패밀리 중복 제거 (WIPS패밀리 ID당 최선출원 1건)",
                                    value=True)
                pool_df, report = pool_convert.convert_wips(df, family_dedup=dedup)
                id_col = pool_convert.WIPS_ID
            elif fmt == "ready":
                pool_df, report = pool_convert.convert_ready(df)
                id_col = next((c for c in ("record_id", "family_id", "patent_id")
                               if c in df.columns), "record_id")
            else:
                st.warning("컬럼을 자동 인식하지 못했습니다 — 직접 지정해 주세요.")
                cols = list(df.columns)
                tcol = st.selectbox("제목 컬럼", cols)
                acol = st.selectbox("초록 컬럼", cols)
                icol = st.selectbox("ID 컬럼 (선택)", ["(없음)"] + cols)
                icol = None if icol == "(없음)" else icol
                pool_df, report = pool_convert.convert_mapped(df, tcol, acol, icol)
                id_col = icol or ""
            for line in report:
                st.caption("· " + line)
            st.dataframe(pool_df[["record_id", "title", "abstract"]].head(5),
                         width="stretch", height=200)

        st.subheader("2) 도메인 정의")
        query = st.text_input("도메인 질의 (자연어, 한국어 가능)",
                              placeholder="예: 휴머노이드 로봇 상용화 기술")
        desc = st.text_area("도메인 상세 설명 (선택 — 기준서 작성 근거로 주입됩니다)",
                            height=140,
                            placeholder="포함하고 싶은 범위, 제외하고 싶은 인접 기술, "
                                        "과제 배경 등을 자유롭게 서술")
        refs = st.file_uploader("참고자료 업로드 (선택, pdf/txt/md — 근거 노트로 반영)",
                                type=["pdf", "txt", "md"], accept_multiple_files=True)
        st.caption("⚠️ 도메인 출제문·소유자 정의 문서는 **반드시 여기에 업로드**하세요. "
                   "짧은 문서(≤8KB)는 기준서 작성의 최상위 범위 근거로 원문 주입됩니다.")
        allow_flagged = st.checkbox(
            "유출 차단에 걸려도 참고자료 강행 주입 (--local-doc-allow-flagged)",
            value=False,
            help="벤치마크 누출 스캔이 소유자 문서를 오탐하면 실행이 중단됩니다(fail-loud). "
                 "문서를 검토했고 안전하다고 확신할 때만 체크하세요.")

    with col2:
        st.subheader("3) 실행 옵션")
        mock = st.checkbox("mock 모드 (API 호출 없는 데모/점검)", value=False)
        workers = st.slider("판정 병렬 워커 수", 5, 60, 40, step=5)
        limit = st.number_input("판정 건수 제한 (0 = 전체)", min_value=0, value=0,
                                step=100)
        bloop = st.checkbox("경계 피드백 루프 (판정 후 애매 구간 재질문·재판정)",
                            value=True)
        if pool_df is not None:
            n = int(limit) if limit else len(pool_df)
            st.info(f"판정 대상 **{n:,}건**\n\n"
                    f"예상 비용 ~${n / 1000 * 0.8:.1f} · "
                    f"예상 소요 {max(5, n // 300)}–{max(10, n // 150)}분\n\n"
                    f"(gpt-4o-mini 전수 판정 + gpt-4o 기준서, 10키 병렬 기준)")
        st.markdown("---")
        start = st.button("🚀 실행 시작", type="primary", width="stretch",
                          disabled=(pool_df is None or not query.strip()))

    if start:
        run_dir = runner.create_run(
            query.strip(), len(pool_df), mock=mock, workers=int(workers),
            limit=int(limit) or None, boundary_loop=bool(bloop),
            source_name=up.name, source_format=fmt or "unknown", id_col=id_col)
        # save the original file + converted pool
        src = run_dir / "uploads" / ("source" + Path(up.name).suffix.lower())
        src.write_bytes(up.getvalue())
        pool_df.to_csv(run_dir / "pool.csv", index=False, encoding="utf-8")
        # user description + reference docs -> local evidence documents
        m = runner.load_manifest(run_dir)
        docs = []
        if desc.strip() and len(desc.strip()) >= 40:
            p = run_dir / "uploads" / "도메인_설명_사용자작성.md"
            p.write_text(f"# 사용자 도메인 설명 — {query.strip()}\n\n{desc.strip()}\n",
                         encoding="utf-8")
            docs.append(str(p))
        for rf in refs or []:
            p = run_dir / "uploads" / rf.name
            p.write_bytes(rf.getvalue())
            docs.append(str(p))
        m["local_docs"] = docs
        m["description"] = desc.strip()
        m["allow_flagged"] = bool(allow_flagged)
        runner.save_manifest(run_dir, m)
        runner.launch(run_dir)
        _go(run_dir)


# ================================================================ run page
@st.fragment(run_every=2.0)
def live_panel(run_dir: Path):
    status = runner.get_status(run_dir)
    prev = st.session_state.get("last_status")
    st.session_state["last_status"] = status
    if prev is not None and prev != status:
        st.rerun(scope="app")     # stage boundary -> refresh the whole page

    icon, desc = STATUS_LABEL[status]
    st.markdown(f"### {icon}")
    st.caption(desc)

    # stage progress
    stage_idx = runner.current_stage(run_dir)
    n = len(runner.STAGES)
    st.progress((stage_idx + 1) / n if status != "done" else 1.0)
    done_l = [lab for _, lab in runner.STAGES[:stage_idx + 1]]
    todo_l = [lab for _, lab in runner.STAGES[stage_idx + 1:]]
    st.markdown(" → ".join([f"**{x}**" for x in done_l] + todo_l) or "시작 대기")

    # judge-stage progress bar
    ws = runner.find_workspace(run_dir)
    m = runner.load_manifest(run_dir)
    if ws is not None:
        total = m.get("limit") or m.get("pool_rows") or 0
        judged = artifacts.judge_progress(ws)
        if judged and total:
            st.progress(min(1.0, judged / total),
                        text=f"⑥ 판정 진행: {judged:,} / {total:,}건")

    with st.expander("실시간 로그", expanded=(status in ("running", "error"))):
        st.code(runner.read_log(run_dir) or "(로그 없음)", language="text")


def render_hitl(run_dir: Path):
    qp = runner.pending_questions(run_dir)
    st.warning("**시스템이 도메인 범위에 대한 인간의 결정을 요청했습니다.** "
               "답변을 제출하면 즉시 이어서 실행됩니다.", icon="🙋")
    if qp is None:
        st.info("질문 파일을 찾는 중입니다. 워크스페이스가 아직 없으면 재시작하세요.")
        if st.button("▶️ 재시작"):
            runner.launch(run_dir)
            st.rerun()
        return
    stage = {"criteria": "기준서 작성", "judge": "판정 감사",
             "boundary-loop": "경계 루프"}.get(qp.get("stage", ""), qp.get("stage", ""))
    if qp.get("context"):
        st.caption(f"단계: {stage} · 맥락: {qp['context']}")
    # Rich decision cards: join pending questions to decisions.json by id.
    _ws = runner.find_workspace(run_dir)
    cards = {d["id"]: d for d in artifacts.decisions(_ws)} if _ws else {}
    pool_lk = artifacts.pool_lookup(run_dir) if cards else {}

    def _example_patents(ids: list[str]):
        for pid in ids:
            title, abstract = pool_lk.get(str(pid), ("", ""))
            with st.expander(f"📄 {pid}" + (f" — {title[:70]}" if title else "")):
                if title:
                    st.markdown(f"**{title}**")
                st.caption(abstract[:600] if abstract else "(초록 없음 — 풀에서 조회 실패)")

    with st.form("hitl_form"):
        answers: dict[str, str] = {}
        for q in qp.get("questions", []):
            card = q.get("card") or cards.get(q["id"])   # prefer the self-contained card
            if card:
                st.markdown(f"**🧭 {card['stake']}**")
                cc1, cc2 = st.columns(2)
                with cc1:
                    st.markdown("**✅ 포함 논리**")
                    st.caption(card.get("include_argument", ""))
                    if card.get("include_examples"):
                        st.markdown("**예시 특허 (포함):**")
                        _example_patents(card["include_examples"])
                with cc2:
                    st.markdown("**⛔ 제외 논리**")
                    st.caption(card.get("exclude_argument", ""))
                    if card.get("exclude_examples"):
                        st.markdown("**예시 특허 (제외):**")
                        _example_patents(card["exclude_examples"])
                flips, n = card.get("impact_flips", 0), card.get("impact_sample_n", 0)
                st.progress(min(1.0, flips / n) if n else 0.0,
                            text=f"영향 규모: 표본 {n}건 중 {flips}건 판정이 갈림")
                st.info(f"💡 권고: {card.get('recommendation', '')}")
            else:
                st.markdown(f"**{q['id']}. {q['question']}**")
                if q.get("why_needed"):
                    st.caption(f"왜 필요한가: {q['why_needed']}")
            opts = q.get("options") or []
            if opts:
                choice = st.radio("선택", opts + ["직접 입력"], key=f"r_{q['id']}",
                                  horizontal=True, label_visibility="collapsed")
                free = st.text_input("직접 입력", key=f"t_{q['id']}",
                                     label_visibility="collapsed",
                                     placeholder="직접 입력 시 여기에 작성")
                answers[q["id"]] = free.strip() if (choice == "직접 입력") else choice
                if choice == "직접 입력" and free.strip():
                    answers[q["id"]] = free.strip()
            else:
                answers[q["id"]] = st.text_input("답변", key=f"t_{q['id']}")
            st.markdown("---")
        if st.form_submit_button("✅ 답변 제출 → 이어서 실행", type="primary"):
            missing = [k for k, v in answers.items() if not str(v).strip()]
            if missing:
                st.error(f"답변이 비어 있습니다: {', '.join(missing)}")
            else:
                runner.submit_answers(run_dir, answers)
                runner.launch(run_dir)
                st.session_state["last_status"] = "running"
                st.rerun()


def render_blocked(run_dir: Path, ws: Path | None):
    st.error("**기준서 검증이 통과하지 못해 판정을 시작하지 않았습니다** (fail-loud). "
             "결함 있는 기준으로 특허를 판정하지 않기 위한 의도된 중단입니다.", icon="🛑")
    rep = artifacts.blocked_report(ws) if ws is not None else None
    if rep is None:
        st.info("차단 보고서(criteria_blocked.json)를 찾지 못했습니다 — 로그를 확인하세요.")
        return
    st.caption(f"사유: {rep.get('reason','?')} · 최선 버전: v{rep.get('best_version','?')} "
               f"· 라운드별 critical: {rep.get('critical_counts', {})}")
    quality = rep.get("quality_critical_issues", rep.get("critical_issues", []))
    pending = rep.get("human_pending_issues", [])
    if quality:
        st.markdown("**품질 결함 (시스템이 고쳐야 함)**")
        for i in quality:
            st.markdown(f"- 🔴 `{i.get('issue_code','')}` {i.get('problem','')}")
            if i.get("suggestion"):
                st.caption(f"  제안: {i['suggestion']}")
    if pending:
        st.markdown("**미결 소유자 결정 (사람이 답해야 함)**")
        for i in pending:
            st.markdown(f"- 🙋 `{i.get('issue_code','')}` {i.get('problem','')}")
    st.info("🔁 **재시작**하면 기준서 루프를 다시 돌며, 범위 질문은 이 화면에서 답변할 수 "
            "있습니다. 이미 답한 질문(동일 문구)은 자동으로 재사용됩니다.")
    if st.button("▶️ 기준서 루프 재시작", type="primary"):
        runner.launch(run_dir)
        st.session_state["last_status"] = "running"
        st.rerun()


def render_results(run_dir: Path, ws: Path):
    df = artifacts.ranked(ws)
    if df.empty:
        st.info("ranked.csv가 아직 없습니다.")
        return
    st.subheader("판정 결과 · 유효특허 선별")
    c1, c2, c3 = st.columns(3)
    c1.metric("판정 특허 수", f"{len(df):,}")
    c2.metric("C/E 기준 충족 유효특허", f"{int(df['included'].sum()):,}")
    c3.metric("판정 유형", ", ".join(f"{k}:{v}" for k, v in
                                   df["candidate_type"].value_counts().items())[:60])

    hist = (df["relevance_score"].clip(0, 1) // 0.05 * 0.05).round(2).value_counts().sort_index()
    st.bar_chart(hist, x_label="관련도 점수 구간(순위용)", y_label="특허 수", height=180)

    mode = st.radio("유효특허 출력 범위", ["전체 유효특허", "유효특허 중 상위 N건"],
                    horizontal=True)
    if mode == "전체 유효특허":
        sel = artifacts.selected_slice(df, "all_positive", 0.0, 0)
    else:
        n_positive = max(1, int(df["included"].sum()))
        topn = st.number_input("유효특허 내 상위 N건", 1, n_positive,
                               min(1000, n_positive), step=min(50, n_positive))
        sel = artifacts.selected_slice(df, "top_n", 0.0, int(topn))
    st.metric("선별된 유효특허", f"{len(sel):,}건")
    display_cols = [c for c in ["rank", "relevance_score", "decision_confidence",
                                "record_id", "patent_id", "title", "candidate_type"]
                    if c in sel.columns]
    st.dataframe(sel[display_cols].head(30),
                 width="stretch", height=300)

    crit_md = None
    final = ws / "criteria_final.md"
    if final.exists():
        crit_md = final.read_text(encoding="utf-8")
    xlsx = artifacts.build_result_xlsx(run_dir, sel, crit_md)
    d1, d2, d3 = st.columns(3)
    d1.download_button("📥 선별 유효특허 xlsx", xlsx, "유효특허_선별결과.xlsx",
                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                       type="primary", width="stretch")
    d2.download_button("📄 전체 판정 ranked.csv",
                       (ws / "judge" / "ranked.csv").read_bytes(), "ranked_all.csv",
                       "text/csv", width="stretch")
    if crit_md:
        d3.download_button("📜 판단 기준서 (md)", crit_md.encode("utf-8"),
                           "판단기준서.md", "text/markdown", width="stretch")


def render_diagnosis_tab(ws: Path):
    prof = artifacts.pool_profile(ws)
    diag = artifacts.diagnosis(ws)
    if not prof and not diag:
        st.info("정합 진단이 아직 생성되지 않았습니다 (③⁺ 단계 이후 표시).")
        return
    if prof:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("총 특허", f"{prof.get('n_total', 0):,}")
        c2.metric("패밀리 대표", f"{prof.get('n_family_dedup', 0):,}",
                  f"-{prof.get('family_dup_rows', 0)} 중복")
        c3.metric("직접 도메인 언급",
                  f"{prof.get('direct_domain_mention', 0):,}",
                  f"{prof.get('direct_domain_pct', 0) * 100:.1f}%")
        c4.metric("상위10 출원인 집중도", f"{prof.get('top10_assignee_share', 0) * 100:.0f}%")
        if prof.get("direct_domain_terms"):
            st.caption("직접 도메인 용어: " + ", ".join(prof["direct_domain_terms"]))
        cc1, cc2 = st.columns(2)
        with cc1:
            st.markdown("**상위 출원인**")
            st.dataframe(pd.DataFrame(prof.get("top_assignees", []))
                         .rename(columns={"name": "출원인", "count": "건수"}),
                         width="stretch", height=240, hide_index=True)
        with cc2:
            st.markdown("**국적 분포**")
            st.dataframe(pd.DataFrame(prof.get("nationality_dist", []))
                         .rename(columns={"name": "국적", "count": "건수"}),
                         width="stretch", height=240, hide_index=True)
        if prof.get("reference_player_coverage"):
            st.markdown("**참고자료 등장 기업의 풀 내 존재**")
            st.dataframe(pd.DataFrame(prof["reference_player_coverage"])
                         .rename(columns={"name": "기업", "in_pool": "풀 내 특허"}),
                         width="stretch", hide_index=True)
    if diag:
        badge = "✅ 자료 충분" if diag.get("sufficiency") == "sufficient" else "🔎 웹 검색 필요"
        st.markdown(f"### {badge}")
        st.markdown(f"**① 문제 파악**  \n{diag.get('problem_understanding', '')}")
        st.markdown(f"**② 참고자료 파악**  \n{diag.get('reference_understanding', '')}")
        if diag.get("alignment_notes"):
            st.markdown("**③ 정합 진단**")
            for n in diag["alignment_notes"]:
                st.markdown(f"- {n}")
        if diag.get("gaps"):
            st.caption("웹 검색 대상 갭: " + "; ".join(diag["gaps"]))


def _case_table(rows: list[dict], kind: str):
    if not rows:
        st.caption("(해당 없음)")
        return
    cols = {"confirmed": ["patent_id", "assignee", "gist", "tier", "basis"],
            "boundary": ["patent_id", "assignee", "gist", "basis", "recommendation"],
            "false_positive": ["patent_id", "assignee", "gist", "basis"]}[kind]
    df = pd.DataFrame(rows)
    df = df[[c for c in cols if c in df.columns]]
    hdr = {"patent_id": "등록번호", "assignee": "출원인", "gist": "제목 요지",
           "tier": "귀속", "basis": "근거/애매점/오탐사유", "recommendation": "권고"}
    st.dataframe(df.rename(columns=hdr), width="stretch", hide_index=True,
                 height=min(360, 40 + 34 * len(df)))


def render_casemap_tab(ws: Path):
    cats = artifacts.casemap_categories(ws)
    if not cats:
        st.info("사례 매핑이 아직 생성되지 않았습니다 (④b 단계 이후 표시).")
        return
    names = [c.get("category", "?") for c in cats]
    pick = st.selectbox("카테고리", names,
                        format_func=lambda n: f"{n} "
                        f"(확정 {len(next(c for c in cats if c['category']==n)['confirmed'])}/"
                        f"경계 {len(next(c for c in cats if c['category']==n)['boundary'])}/"
                        f"오탐 {len(next(c for c in cats if c['category']==n)['false_positive'])})")
    cat = next(c for c in cats if c["category"] == pick)
    st.markdown(f"#### 확정 사례 ({len(cat['confirmed'])})")
    _case_table(cat["confirmed"], "confirmed")
    st.markdown(f"#### 경계 사례 ({len(cat['boundary'])}) — 판정을 가르는 인사이트")
    _case_table(cat["boundary"], "boundary")
    st.markdown(f"#### 오탐 ({len(cat['false_positive'])})")
    _case_table(cat["false_positive"], "false_positive")
    if cat.get("false_positive_cues"):
        st.caption("오탐 사전: " + " · ".join(cat["false_positive_cues"]))
    revs = artifacts.casemap_revisions(ws, pick)
    if revs:
        st.markdown("#### 🔁 자기수정 이력 (스스로 재분류한 과정)")
        for i, r in enumerate(revs, 1):
            with st.expander(f"라운드 {i}: {len(r.get('changed', []))}건 재분류 — "
                             f"{r.get('rationale', '')[:70]}"):
                for ch in r.get("changed", []):
                    st.markdown(f"- `{ch.get('patent_id')}` → **{ch.get('verdict')}**"
                                f"/{ch.get('tier', '?')} : {ch.get('basis', '')}")


def render_insights_tab(ws: Path):
    summ = artifacts.casemap_summary(ws)
    if not summ:
        st.info("핵심 인사이트가 아직 생성되지 않았습니다 (④b 집계 이후 표시).")
        return
    st.markdown("### 💡 핵심 인사이트")
    for ins in summ.get("insights", []):
        st.markdown(f"**{ins.get('title', '')}**")
        st.markdown(ins.get("detail", ""))
        if ins.get("evidence_ids"):
            st.caption("근거: " + ", ".join(ins["evidence_ids"]))
        st.markdown("---")
    if summ.get("false_positive_cues"):
        st.markdown("**오탐 사전 (전 카테고리 병합)**")
        st.caption(" · ".join(summ["false_positive_cues"]))
    reps = summ.get("representative_confirmed", [])
    if reps:
        st.markdown("**대표 확정 사례**")
        _case_table(reps, "confirmed")


def render_artifact_tabs(run_dir: Path, ws: Path | None):
    tabs = st.tabs(["📜 기준서", "📊 정합 진단", "🗂️ 사례 매핑", "💡 인사이트",
                    "🙋 HITL Q&A", "🔎 리서치·코퍼스", "⚖️ 경계 검증", "🧾 검증 이력"])
    if ws is None:
        for t in tabs:
            with t:
                st.info("워크스페이스 생성 전입니다 (스코핑 단계 이후 표시).")
        return
    with tabs[1]:
        render_diagnosis_tab(ws)
    with tabs[2]:
        render_casemap_tab(ws)
    with tabs[3]:
        render_insights_tab(ws)

    with tabs[0]:
        vers = artifacts.criteria_versions(ws)
        if not vers:
            st.info("기준서가 아직 작성되지 않았습니다.")
        else:
            labels = [v[0] for v in vers]
            pick = st.selectbox("버전", labels, index=len(labels) - 1)
            st.markdown(dict(vers)[pick])
        ax = artifacts.axis_md(ws)
        if ax:
            with st.expander("🧭 기술축 합성 (axis synthesis — 기준서의 골격·출처)"):
                st.markdown(ax)

    with tabs[4]:
        qa = artifacts.human_qa(ws)
        if not qa:
            st.info("아직 질문/답변이 없습니다.")
        for e in qa:
            who = {"human": "🧑 인간 답변", "human_batch": "🧑 인간 답변(UI)",
                   "human_prior": "🧑 인간 답변(같은 실행에서 재사용)",
                   "auto": "🤖 자동 가정 (소유자 결정 아님)"}.get(
                       e.get("answered_by"), e.get("answered_by"))
            st.markdown(f"**[{e.get('stage','')}] Q ({e.get('id','')}):** "
                        f"{e.get('question','')}")
            if e.get("why_needed"):
                st.caption(f"이유: {e['why_needed']}")
            st.markdown(f"> {who}: {e.get('answer','')}")
            st.markdown("---")

    with tabs[5]:
        _render_research_sources(ws)
        _render_alignment(ws)
        st.markdown("---")
        notes = artifacts.research_notes(ws)
        if notes.empty:
            st.info("리서치 노트가 아직 없습니다.")
        else:
            st.markdown(f"**근거 노트 {len(notes)}건** (유형별)")
            st.dataframe(notes.groupby("intent_type").size().rename("노트 수"),
                         width="stretch")
            src = notes["source_url"].value_counts().head(15).rename("노트 수")
            st.markdown("**출처 상위**")
            st.dataframe(src, width="stretch")
            blocked = artifacts.blocked_pages(ws)
            if blocked:
                st.caption(f"벤치마크 누출 차단: {len(blocked)}건")
        dg = artifacts.corpus_digest(ws)
        if dg:
            st.markdown("**특허 풀 통독 요약 (corpus digest)**")
            for cl in dg.get("main_clusters", []):
                st.markdown(f"- {cl}")
            if dg.get("suspected_boundary_cases"):
                st.markdown("**경계 의심 사례**")
                for b in dg["suspected_boundary_cases"]:
                    st.markdown(f"- ⚠️ {b}")

    with tabs[6]:
        probe = artifacts.boundary_probe(ws)
        if not probe:
            st.info("경계 검증(broad/narrow 판정 diff) 기록이 없습니다.")
        else:
            st.caption("범위 질문마다 넓은 규칙 vs 좁은 규칙으로 표본을 실제 판정해 "
                       "라벨이 뒤집히는(flip) 특허 수를 측정한 기록입니다.")
            for e in probe:
                if "summary" in e:
                    for s in e["summary"]:
                        st.markdown(f"- **{s.get('id')}**: 표본 {s.get('n')}건 중 "
                                    f"flip {s.get('flip')}건")

    with tabs[7]:
        ledger = artifacts.issue_ledger(ws)
        if ledger:
            st.markdown("**이슈 원장 (critical 추적)** — 같은 결함은 라운드가 바뀌어도 "
                        "같은 코드로 추적됩니다.")
            st.dataframe(pd.DataFrame([{
                "상태": "🟠 open" if r.get("status") == "open" else "✅ resolved",
                "코드": r.get("issue_code", ""), "분류": r.get("category", ""),
                "등장": f"r{r.get('first_round','?')}→r{r.get('last_round','?')}",
                "지속 라운드": r.get("rounds_open", ""),
                "내용": (r.get("problem", "") or "")[:90],
            } for r in ledger]), width="stretch", height=200)
        repairs = artifacts.provenance_repairs(ws)
        if repairs:
            with st.expander(f"🔧 출처 자동수리·패치 감사 로그 ({len(repairs)}건)"):
                for r in repairs:
                    st.caption(f"[{r.get('stage','')}] {r.get('op', r.get('patched',''))} "
                               f"· {r.get('context','')} "
                               f"{('· ' + str(r.get('from',''))[:60] + ' → ' + str(r.get('to',''))[:60]) if r.get('from') else ''}")
        for c in artifacts.critiques(ws):
            issues = c.get("issues", [])
            ncrit = sum(1 for i in issues if i.get("severity") == "critical")
            st.markdown(f"**기준서 v{c.get('_version')}** — 검증 액션: "
                        f"`{c.get('action', c.get('warning', c.get('status', '?')))}` · "
                        f"지적 {len(issues)}건 (critical {ncrit})")
            for i in issues:
                sev = "🔴" if i.get("severity") == "critical" else "🟡"
                code = f"`{i['issue_code']}` " if i.get("issue_code") else ""
                body = i.get("problem", i.get("issue", "")) or str(i)
                st.caption(f"{sev} {code}{body}")
                if i.get("suggestion"):
                    st.caption(f"    ↳ 제안: {i['suggestion']}")
            st.markdown("---")


def render_run(run_dir: Path):
    m = runner.load_manifest(run_dir)
    status = runner.get_status(run_dir)
    st.header(f"『{m.get('query','')}』")
    meta = (f"run `{m.get('run_id')}` · 풀 {m.get('pool_rows', 0):,}건"
            + (f" · 제한 {m['limit']:,}건" if m.get("limit") else "")
            + (" · **MOCK 모드**" if m.get("mock") else "")
            + (f" · 참고자료 {len(m.get('local_docs', []))}건" if m.get("local_docs") else ""))
    st.caption(meta)

    bc1, bc2, _ = st.columns([1, 1, 4])
    if status in ("running", "waiting_human"):
        if bc1.button("⏹️ 중단"):
            runner.stop(run_dir)
            st.rerun()
    if status in ("stopped", "error", "new"):
        if bc1.button("▶️ 시작/재개", type="primary"):
            runner.launch(run_dir)
            st.session_state["last_status"] = "running"
            st.rerun()

    ws = runner.find_workspace(run_dir)

    if status == "waiting_human":
        render_hitl(run_dir)
    if status == "blocked":
        render_blocked(run_dir, ws)

    if status in ("running", "waiting_human"):
        live_panel(run_dir)
    else:
        icon, desc = STATUS_LABEL[status]
        st.markdown(f"### {icon}")
        st.caption(desc)
        with st.expander("전체 로그", expanded=(status == "error")):
            st.code(runner.read_log(run_dir) or "(로그 없음)", language="text")

    if status == "done" and ws is not None:
        render_results(run_dir, ws)

    st.markdown("---")
    render_artifact_tabs(run_dir, ws)
    if ws is not None:
        st.caption(f"워크스페이스: `{ws}`")


# ================================================================ router
rd = st.session_state.get("run_dir")
if rd and Path(rd).exists():
    render_run(Path(rd))
else:
    render_setup()
