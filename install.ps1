# Claude Code 스킬로 설치 — ~/.claude/skills/book-study-pdf 에 복사한다.
$dst = Join-Path $env:USERPROFILE ".claude/skills/book-study-pdf"
$src = Split-Path -Parent $MyInvocation.MyCommand.Path
if (Test-Path $dst) { Write-Host "이미 있음: $dst  (덮어쓰려면 폴더를 먼저 지우세요)"; exit 1 }
New-Item -ItemType Directory -Force -Path $dst | Out-Null
foreach ($d in @("SKILL.md","AGENTS.md","README.md","references","scripts","assets","templates","prompts","requirements.txt")) {
  Copy-Item -Recurse -Force (Join-Path $src $d) $dst
}
Get-ChildItem -Recurse -Directory -Filter "__pycache__" $dst | Remove-Item -Recurse -Force
Write-Host "설치됨: $dst"
Write-Host "다음: pip install -r `"$dst/requirements.txt`" ; 환경변수 MINERU_EXE · MINERU_PY · (선택) CHROME_PATH 설정"
