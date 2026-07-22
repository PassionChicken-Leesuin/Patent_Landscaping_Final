#!/usr/bin/env bash
# Snapshot the agentic MAS system (code + docs, no data) into the dedicated repo
#   https://github.com/PassionChicken-Leesuin/Patent_Landscaping_MAS
# keeping its history: clone -> rsync whitelist -> commit -> push.
#
#   bash scripts/push_mas_repo.sh "commit message"
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REMOTE="https://github.com/PassionChicken-Leesuin/Patent_Landscaping_MAS.git"
STAGE="${TMPDIR:-/tmp}/patent_landscaping_mas_stage"
MSG="${1:-sync MAS system}"

rm -rf "$STAGE"
git clone "$REMOTE" "$STAGE" 2>/dev/null || { mkdir -p "$STAGE"; git -C "$STAGE" init -q; }
cd "$STAGE"
git checkout -q main 2>/dev/null || git checkout -qb main

RS="rsync -a --delete --exclude=__pycache__ --exclude=.pytest_cache --exclude=.DS_Store"
$RS "$ROOT/app/"     app/
$RS "$ROOT/src/"     src/
$RS "$ROOT/scripts/" scripts/
mkdir -p experiments
rsync -a --exclude=.DS_Store "$ROOT/experiments/"*.md experiments/ 2>/dev/null || true
cp "$ROOT/requirements.txt" .
cp "$ROOT/README_MAS.md" README.md
cp "$ROOT/MAS_implementation_v2.md" . 2>/dev/null || true
cp "$ROOT/MAS_LangGraph_구현스펙_v1.md" . 2>/dev/null || true
cat > .gitignore <<'EOF'
__pycache__/
*.py[cod]
.venv*/
.env
*.key
.DS_Store
DataSet/
outputs/
EOF

git add -A
if git diff --cached --quiet; then
    echo "nothing to push (stage identical to remote)"
    exit 0
fi
git commit -q -m "$MSG"
git remote add origin "$REMOTE" 2>/dev/null || git remote set-url origin "$REMOTE"
git push -u origin main
echo "pushed -> $REMOTE"
