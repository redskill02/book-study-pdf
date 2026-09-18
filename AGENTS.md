# AGENTS.md — 에이전트 진입점 (Claude Code · Codex · Cursor · Gemini CLI · OpenCode · 기타)

> **English summary.** This repository is a self-contained *skill* that turns a scanned/OCR'd book PDF into a
> verified Korean study-note PDF (chapter digests, redrawn Korean SVG figures — or, for stock/chart books,
> original chart crops with Korean annotations — 4-panel comics, easy examples, recall pages, exams with answer keys,
> pass thresholds and tutor prompts, merged into one PDF). English books are translated into Korean as they are digested.
> **Read `SKILL.md` first and follow it literally.** Everything below is the reading order and the definition of done.
> All output to the reader is Korean.

이 저장소는 **책 PDF → 한국어 학습노트 PDF** 파이프라인을 스킬 하나로 묶은 것이다. 어떤 에이전트든 아래 순서로 읽고 그대로 따르면 같은 결과가 나온다.

## 1. 읽는 순서 (건너뛰지 마라)

| 순서 | 파일 | 왜 |
|---|---|---|
| 1 | `SKILL.md` | 실행 지침 전체. 책 유형 두 축(`mode` · `figures`) · 필수 요소 7가지 · 작업 순서 0~8 |
| 2 | `references/pitfalls.md` | 실제로 겪은 함정 100여 건. **이걸 안 읽으면 같은 사고를 반복한다** |
| 3 | `references/book-types.md` | 일반 도서 / 주식·차트 도서 / 영어 원서 / 코드·에세이·인터뷰 판별 트리 |
| 4 | 유형에 따라 `references/chart-mode.md`(주식·차트) · `references/translate-mode.md`(영어 원서) | 유형별로 완전히 다른 부분 |
| 5 | `references/writing.md` | HTML 챕터 규격 · SVG 작도 · 만화 · 예시 · 덮고 쓰기 · 시험 · 합격선 · 튜터 · 표지 · 계획표 |
| 6 | `references/checkers.md` | 검사기 12종 · 권별 체인 `_chain.py` · 예방 규칙 · 검사기를 믿는 법 |
| 7 | `references/pipeline.md` · `references/audit.md` | MinerU 변환 · 회전 검사 · 원문 대조 |
| — | `templates/` | `book.json` · `_GATE.md` · `chapter.html` · `front.html` 골격 |
| — | `prompts/auto-continue.md` | 여러 권을 묻지 않고 연속 작업할 때 첫 메시지로 쓰는 프롬프트 |

## 2. 환경 (한 번만)

```
python 3.10+   pip install -r requirements.txt        # pymupdf pillow numpy pypdfium2
Chrome/Chromium (HTML → PDF 인쇄)                        # CHROME_PATH 로 지정 가능
MinerU (별도 venv 권장)                                   # MINERU_EXE=<mineru 실행 파일>  MINERU_PY=<그 venv 의 python>
한글 폰트: Malgun Gothic(Windows) 또는 Nanum 계열          # build.py merge 가 임베딩을 검사한다
SKILL=<이 저장소의 절대 경로>
```

Claude Code 라면 `~/.claude/skills/book-study-pdf/` 에 두면 `/book-study-pdf` 로 자동 발동된다(`install.ps1` / `install.sh`).
다른 에이전트는 이 저장소를 clone 한 뒤 **작업 폴더에 `scripts/*.py` 와 `assets/style.css` 를 복사**해서 그 안에서 돌린다(`build.py` 는 자기 폴더의 `book.json` 을 읽는다).

## 3. 한 권의 흐름 (요약 — 상세는 SKILL.md "작업 순서")

```
0   스캔 완전성 · probe.py (재OCR 판정) · rotate.py scan/fix (뒤집힌 쪽)          ← 묻지 않고 자동
1   MinerU 변환 (_pipeline.py)   · chart 책은 downsample → MinerU → crop.py 이중 트랙
2   split.py 분할 · _extm.py / _extf.py / srcpdf.py 로 권별 원문 추출 (오프셋은 권마다)
3   contact_sheet.py 전수 확인 → _GATE.md 에 도판 분류 + 권 구성 (분권이면 마지막 권까지 보고 집필)
4   권마다 chNN.html 집필 (templates/chapter.html)
5   _fix.py → _chain.py NN --nobuild → prewidth.py 100 → _chain.py NN → _rep.txt 비면 통과
    → _ovNN.png · 만화 100% · 도표 쪽 5장+ 눈으로 → _done.py NN "GATE 한 줄"
6   audit.py (정방향) + audit_kw (역방향, CLAIMS 교체) → 누락 보완
7   _front.html · ch99.html → build.py all → merge → imgcheck.py all → deploy
8   기록 (진도표 · _GATE.md · 새 함정은 pitfalls.md 에 번호 붙여 추가)
```

## 4. 완료 정의 (Definition of Done)

- [ ] `checkall.py` 12종 전부 0건 (`stats blocks headings svgbox svgfit linegap comicfit tags imgfit imgres imgcite size`)
- [ ] 권마다 덮고 쓰기 → 시험 → 정답 + 합격선(급소 3문항) → 튜터 순서, 만화 2 · 예시 3 · 문항 30~36
- [ ] `_front.html`(차례 · 1-4-7-14 계획표 · 서지 · 개인 학습용 문구) + `ch99.html`(총정리 · 종합시험 · 만화 2 · 예시 3)
- [ ] `build.py merge` → `_verify.txt` 빈 쪽 0 · 한글 폰트 임베딩 OK · 북마크 = 권 수 + 1
- [ ] `audit.py` · `audit_kw` 결과의 진짜 누락을 심각도 순으로 보완, 오탐은 근거와 함께 기록
- [ ] 만화 100% · 도표 쪽 상위 10장 이상을 렌더로 눈으로 확인 (검사기 0건은 통과가 아니다)
- [ ] `build.py deploy` 후 배포 폴더에 합본 1 + 권별 PDF, 임시 파일명 없음
- [ ] 원본 PDF · 기존 완성본을 지우거나 덮어쓰지 않았음 · 판권면 AI 금지 문구 확인 · 결과 경로 출력

## 5. 절대 규칙

1. 한 권(챕터)씩 쓰고 검증한 뒤 다음으로. **중간에 사용자에게 묻지 않는다** — 규칙으로 정하고 `_GATE.md` 에 근거를 남긴다.
2. 출력은 전부 한국어. 원어는 괄호 병기. 번역서는 그 책의 표기를 따른다.
3. 일반 도서의 도판은 전부 한글 SVG 재작도. **주식·차트 도서의 실제 차트는 재작도 금지** — 원본 크롭 + 한글 주석.
4. 한글을 콘솔에 `print` 하지 않는다(cp949 깨짐). 파일로 쓰고 읽는다. 긴 스크립트 · HTML 은 heredoc 대신 파일 쓰기 도구로.
5. 검사기가 0건 · 전부 오탐 · 대상 0 을 내면 **검사기부터 의심**한다.
6. 원본을 끝까지 읽는다(`wc -l`). 그림에만 있는 개념 · 수치를 찾는다. 부록은 별도 권.
