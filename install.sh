#!/usr/bin/env bash
# Claude Code 스킬로 설치 — ~/.claude/skills/book-study-pdf 에 복사한다.
set -e
src="$(cd "$(dirname "$0")" && pwd)"
dst="$HOME/.claude/skills/book-study-pdf"
if [ -e "$dst" ]; then echo "이미 있음: $dst  (덮어쓰려면 폴더를 먼저 지우세요)"; exit 1; fi
mkdir -p "$dst"
for d in SKILL.md AGENTS.md README.md references scripts assets templates prompts requirements.txt; do
  cp -R "$src/$d" "$dst/"
done
find "$dst" -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null || true
echo "설치됨: $dst"
echo "다음: pip install -r \"$dst/requirements.txt\" ; 환경변수 MINERU_EXE · MINERU_PY · (선택) CHROME_PATH 설정"
