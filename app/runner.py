"""Run manager for the Streamlit UI.

Each UI run lives under DataSet/agentic_ui/<run_id>/ :
  manifest.json   query / variant / flags / pid / launch history
  pool.csv        converted judge pool (record_id/patent_id/title/abstract [+meta])
  uploads/        the original uploaded file + reference documents
  run.log         combined stdout+stderr of every launch
  exit_code       written when a launch ends (0 done, 2 waiting for human answers)

The pipeline itself is scripts.run_agentic with --hitl batch: on a human question it
writes questions_pending.json into its workspace and exits with code 2; we surface
the questions in the UI, write answers.json, and relaunch — every finished stage is
cached in the workspace, so the run resumes exactly where it stopped. Exit code 3 =
fail-loud block (criteria/axis validation): criteria_blocked.json holds the report.

Cross-platform: launching goes through app/_run_wrapper.py (no bash), stopping uses
taskkill on Windows / killpg on POSIX.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UI_DIR = ROOT / "DataSet" / "agentic_ui"
AGENTIC_DIR = ROOT / "DataSet" / "agentic"
IS_WINDOWS = os.name == "nt"

STAGES = [
    ("[1] scoping", "① 질의 스코핑"),
    ("[2] research", "② 웹 자료수집"),
    ("[2b] local docs", "②b 사용자 자료 반영"),
    ("[3] corpus", "③ 특허 풀 통독"),
    ("[3.5] alignment diagnosis", "③⁺ 정합 진단"),
    ("technology-axis synthesis", "④a 기술축 합성"),
    ("[4a+] design plan", "④a⁺ 설계안(Tier)"),
    ("[4b-map] category case-mapping", "④b 사례 매핑·자기수정"),
    ("[4c] scope decisions", "④c 범위 결정(HITL)"),
    ("criteria drafting + validator loop", "④⑤ 기준서 작성·검증(HITL)"),
    ("[6] judge", "⑥ 특허 판정"),
    ("[7] judgment validator", "⑦ 판정 감사"),
    ("[3-loop]", "⑧ 경계 피드백 루프"),
    ("ranked CSV", "완료: 랭킹 산출"),
]


# ------------------------------------------------------------------ manifest
def manifest_path(run_dir: Path) -> Path:
    return run_dir / "manifest.json"


def load_manifest(run_dir: Path) -> dict:
    p = manifest_path(run_dir)
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def save_manifest(run_dir: Path, m: dict) -> None:
    manifest_path(run_dir).write_text(
        json.dumps(m, ensure_ascii=False, indent=2), encoding="utf-8")


def list_runs() -> list[Path]:
    if not UI_DIR.exists():
        return []
    runs = [p for p in UI_DIR.iterdir() if (p / "manifest.json").exists()]
    return sorted(runs, key=lambda p: p.name, reverse=True)


def create_run(query: str, pool_csv_rows: int, *, mock: bool, workers: int,
               limit: int | None, boundary_loop: bool, source_name: str,
               source_format: str, id_col: str) -> Path:
    run_id = time.strftime("%Y%m%d-%H%M%S")
    run_dir = UI_DIR / run_id
    (run_dir / "uploads").mkdir(parents=True, exist_ok=True)
    save_manifest(run_dir, {
        "run_id": run_id,
        "created": time.strftime("%Y-%m-%d %H:%M:%S"),
        "query": query,
        "variant": f"ui{run_id.replace('-', '')}",
        "mock": mock,
        "workers": workers,
        "limit": limit,
        "boundary_loop": boundary_loop,
        "pool_rows": pool_csv_rows,
        "source_name": source_name,
        "source_format": source_format,
        "id_col": id_col,
        "local_docs": [],
        "pid": None,
        "launches": [],
    })
    return run_dir


# ------------------------------------------------------------------ launch
def build_command(run_dir: Path, m: dict) -> list[str]:
    args = [sys.executable, "-u", "-m", "scripts.run_agentic",
            "--query", m["query"],
            "--input", str(run_dir / "pool.csv"),
            "--hitl", "batch",
            "--resume",
            "--workers", str(m.get("workers", 40)),
            "--variant", m["variant"]]
    if m.get("mock"):
        args.append("--mock")
    if m.get("limit"):
        args += ["--limit", str(m["limit"])]
    if m.get("boundary_loop"):
        args.append("--boundary-loop")
    for doc in m.get("local_docs", []):
        args += ["--local-doc", doc]
    if m.get("allow_flagged"):
        args.append("--local-doc-allow-flagged")
    return args


def launch(run_dir: Path) -> int:
    """Start (or resume) the pipeline detached; returns the wrapper pid."""
    m = load_manifest(run_dir)
    log = run_dir / "run.log"
    exit_file = run_dir / "exit_code"
    exit_file.unlink(missing_ok=True)

    cmd = build_command(run_dir, m)
    stamp = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(log, "a", encoding="utf-8") as f:
        f.write(f"\n===== launch {stamp} =====\n$ {' '.join(cmd)}\n\n")

    env = {**os.environ, "PYTHONUNBUFFERED": "1", "PYTHONPATH": str(ROOT),
           "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}
    wrapper = [sys.executable, "-m", "app._run_wrapper",
               str(log), str(exit_file)] + cmd
    if IS_WINDOWS:
        flags = (subprocess.CREATE_NEW_PROCESS_GROUP
                 | getattr(subprocess, "CREATE_NO_WINDOW", 0))
        p = subprocess.Popen(wrapper, cwd=str(ROOT), env=env, creationflags=flags,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        p = subprocess.Popen(wrapper, cwd=str(ROOT), env=env,
                             start_new_session=True,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    m["pid"] = p.pid
    m.setdefault("launches", []).append({"time": stamp, "pid": p.pid})
    save_manifest(run_dir, m)
    return p.pid


def stop(run_dir: Path) -> None:
    m = load_manifest(run_dir)
    pid = m.get("pid")
    if not pid or not _pid_alive(pid):
        return
    if IS_WINDOWS:
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)],
                       capture_output=True)
        # a force-killed wrapper never writes exit_code — record the stop here
        (run_dir / "exit_code").write_text("130", encoding="utf-8")
    else:
        import signal
        try:
            os.killpg(os.getpgid(pid), signal.SIGTERM)
        except (ProcessLookupError, PermissionError):
            pass


def _pid_alive(pid: int) -> bool:
    if IS_WINDOWS:
        out = subprocess.run(
            ["tasklist", "/FI", f"PID eq {pid}", "/NH", "/FO", "CSV"],
            capture_output=True, text=True)
        return str(pid) in (out.stdout or "")
    try:
        os.kill(pid, 0)
    except (ProcessLookupError, PermissionError):
        return False
    return True


# ------------------------------------------------------------------ status
def get_status(run_dir: Path) -> str:
    """new | running | waiting_human | blocked | done | stopped | error"""
    m = load_manifest(run_dir)
    exit_file = run_dir / "exit_code"
    if exit_file.exists():
        try:
            code = int(exit_file.read_text().strip() or "-1")
        except ValueError:
            code = -1
        if code == 0:
            return "done"
        if code == 2:
            return "waiting_human"
        if code == 3:
            return "blocked"
        if code in (-15, 143, 130):
            return "stopped"
        return "error"
    pid = m.get("pid")
    if pid is None:
        return "new"
    if _pid_alive(pid):
        return "running"
    # a just-issued launch may not have forked yet
    launches = m.get("launches", [])
    if launches:
        try:
            last = time.mktime(time.strptime(launches[-1]["time"], "%Y-%m-%d %H:%M:%S"))
            if time.time() - last < 10:
                return "running"
        except (ValueError, KeyError):
            pass
    return "error"


def read_log(run_dir: Path, tail_chars: int = 30000) -> str:
    log = run_dir / "run.log"
    if not log.exists():
        return ""
    text = log.read_text(encoding="utf-8", errors="replace")
    return text[-tail_chars:]


def current_stage(run_dir: Path) -> int:
    """Index into STAGES of the furthest stage marker seen in the log (-1 = none)."""
    text = read_log(run_dir, tail_chars=200000)
    idx = -1
    for i, (marker, _label) in enumerate(STAGES):
        if marker in text:
            idx = max(idx, i)
    return idx


# ------------------------------------------------------------------ workspace
def find_workspace(run_dir: Path) -> Path | None:
    """The pipeline names its workspace from the LLM-scoped canonical name; find it
    by matching query/variant/mock in each workspace's query.json."""
    m = load_manifest(run_dir)
    if m.get("workspace"):
        ws = AGENTIC_DIR / m["workspace"]
        if ws.exists():
            return ws
    if not AGENTIC_DIR.exists():
        return None
    for qj in AGENTIC_DIR.glob("*/query.json"):
        try:
            d = json.loads(qj.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if (d.get("query_original") == m.get("query")
                and str(d.get("variant", "")) == m.get("variant")
                and bool(d.get("mock")) == bool(m.get("mock"))):
            m["workspace"] = qj.parent.name
            save_manifest(run_dir, m)
            return qj.parent
    return None


def pending_questions(run_dir: Path) -> dict | None:
    ws = find_workspace(run_dir)
    if ws is None:
        return None
    qp = ws / "questions_pending.json"
    if not qp.exists():
        return None
    try:
        return json.loads(qp.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def submit_answers(run_dir: Path, answers: dict[str, str]) -> None:
    """Merge answers into the workspace answers.json (batch-HITL contract)."""
    ws = find_workspace(run_dir)
    if ws is None:
        raise RuntimeError("workspace not found — 파이프라인이 아직 스코핑 전입니다")
    ap = ws / "answers.json"
    existing = {}
    if ap.exists():
        try:
            existing = json.loads(ap.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            existing = {}
    existing.update({k: v for k, v in answers.items() if str(v).strip()})
    ap.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8")
