"""Detached cross-platform pipeline wrapper for the Streamlit runner.

Usage: python -m app._run_wrapper <log> <exit_file> <cmd...>

Runs <cmd...> appending stdout+stderr to <log>, then writes the exit code to
<exit_file>. Replaces the POSIX-only `bash -c "... ; echo $? > exit_code"`
wrapper so the UI works on Windows (cp949 console, no bash/killpg) and macOS.
"""
from __future__ import annotations

import subprocess
import sys


def main() -> None:
    log_path, exit_path, *cmd = sys.argv[1:]
    with open(log_path, "a", encoding="utf-8") as log:
        rc = subprocess.call(cmd, stdout=log, stderr=subprocess.STDOUT)
    with open(exit_path, "w", encoding="utf-8") as f:
        f.write(str(rc))


if __name__ == "__main__":
    main()
