# book-study-pdf

**책 PDF(스캔본 · OCR본) → 읽고 시험까지 볼 수 있는 한국어 학습노트 PDF.**
AI 에이전트가 그대로 따라 하도록 만든 *스킬*(지침 + 스크립트 + 템플릿)이다. Claude Code 스킬 형식(`SKILL.md`)이지만 Codex · Cursor · Gemini CLI 등 어떤 에이전트든 `AGENTS.md` 부터 읽으면 쓸 수 있다.

> **What it is (EN).** A drop-in agent skill that converts a scanned/OCR'd book PDF into a verified Korean study-note PDF:
> per-chapter digests, figures redrawn as Korean SVG (or, for stock/chart books, original chart crops with Korean
> annotation overlays), 4-panel comics, localized examples, recall pages, exams + answer keys + pass thresholds,
> a per-chapter tutor prompt, a study plan with spaced review, a final mixed exam — merged into one PDF and
> checked by 12 automated checkers. English books are translated into Korean while being digested.

---

## 무엇이 나오나

한 권의 책이 **N권 + 총정리**의 합본 PDF 하나가 된다. 권마다 같은 순서로 들어 있다.

| 순서 | 요소 | 근거(학습과학) |
|---|---|---|
| 1 | **본문 정리** — 한국어 책은 더 쉬운 말로, 영어 원서는 번역하며 | |
| 2 | **도표** — 일반 도서: 한글 SVG 재작도 / 주식·차트 도서: 원본 크롭 + 한글 주석 | 이중부호화 |
| 3 | **4컷 만화** 2편 — 저자의 일화·실패담 | 이중부호화 · 서사 |
| 4 | **쉬운 예시** 3개 — 영어 원서는 한국 사례로 대체, 숫자 대입 | 정교화 |
| 5 | **덮고 쓰기** — 뼈대와 개수만 인쇄, 내용은 빈칸 | 인출 |
| 6 | **시험** 30~36문항 (객관식·단답·서술·설명형 · 차트 판독형) | 인출 · 재인 |
| 7 | **정답 + 합격선** — 몇 개면 넘어가고 몇 개면 되돌아가는지 숫자로, 급소 3문항 | 메타인지 |
| 8 | **튜터 프롬프트** — 그 권 전용, 복사해 아무 AI 에 붙이면 심문이 시작된다 | AI 협업 |
| 책 전체 | 표지 · 차례 · **1-4-7-14 복습 계획표** · 서지 · **총정리 + 종합시험**(장을 섞은 문항) | 분산 · 인터리빙 |

## 책 유형을 두 축으로 가른다

```
mode     = translate (영어 원서 → 한국어 번역 정리)   |  digest (한국어 책 · 번역서 → 쉬운 재정리)
figures  = redraw    (일반 도서 → 도판 전부 SVG 재작도) |  chart  (주식·차트 도서 → 실제 차트는 원본 크롭 + 한글 주석, 개념도·UI 는 재작도)
```

**주식·차트 도서의 실제 차트는 재작도하면 안 된다** — 저자가 사고판 자리와 실제 차트의 지저분함이 학습 목표라서, 다시 그리면 교과서 속 깔끔한 패턴이 되어 버린다. 판별 기준과 5분류(A~E)는 [`references/book-types.md`](references/book-types.md) · [`references/chart-mode.md`](references/chart-mode.md).
영어 원서의 용어 병기 · 한국 사례 대체 · 대조법은 [`references/translate-mode.md`](references/translate-mode.md).

## 파이프라인

```
0    스캔 완전성 · probe.py(텍스트 레이어 판정 · 재OCR) · rotate.py(뒤집힌 쪽 검출·보정 — MinerU 는 180° 를 못 고친다)
1    MinerU 구조화 (pipeline -m ocr)   · chart 책: 300dpi 사본으로 구조화 → 그 bbox 로 원본 600dpi 크롭 (이중 트랙)
2    대단원 분할 · 권별 원문 추출 (content_list / 텍스트 레이어)
3    컨택트시트로 원본 이미지 전수 확인 → 도판 분류 · 권 구성 (_GATE.md)        ← 여기까지 끝나야 첫 줄을 쓴다
4    권마다 HTML 집필 (templates/chapter.html)
5    권별 체인: _fix → _chain --nobuild → prewidth → _chain → 12 검사기 0건 → 개요 PNG · 만화 100% 눈으로 → _done
6    원문 대조 — 정방향(audit.py) + 역방향(audit_kw: 노트가 주장한 효과 이름·수치가 원문에 있는가)
7    표지 · 총정리 → build.py all → merge → deploy
8    기록 · 새 함정은 references/pitfalls.md 에 번호 붙여 추가
```

검사기 12종: `stats blocks headings svgbox svgfit linegap comicfit tags` + `imgfit imgres imgcite size` — [`references/checkers.md`](references/checkers.md).
지금까지 **50권 가까이**(경영 · 마케팅 · 심리 · 코드 · 지정학 · 주식 30여 권 · 영어 원서 4권)에서 검증했고, 그 과정에서 겪은 함정 100여 건이 [`references/pitfalls.md`](references/pitfalls.md) 에 있다.

## 설치

```bash
git clone https://github.com/redskill02/book-study-pdf.git
cd book-study-pdf && pip install -r requirements.txt
```

| 에이전트 | 방법 |
|---|---|
| **Claude Code** | `./install.ps1`(Windows) 또는 `./install.sh` → `~/.claude/skills/book-study-pdf/` 에 복사. 이후 "책 학습노트 만들어줘" · `/book-study-pdf` 로 발동 |
| **Codex · Cursor · Gemini CLI · OpenCode · 기타** | 저장소를 clone 하고 첫 메시지에 `AGENTS.md 를 읽고 그대로 따라 <책.pdf> 의 학습노트를 만들어라` |
| **원격 참조만** | `https://raw.githubusercontent.com/redskill02/book-study-pdf/main/SKILL.md` 를 읽게 한다. 스크립트는 clone 이 필요하다 |

필요한 것 — Python 3.10+, `pymupdf` `pillow` `numpy` `pypdfium2`, **Chrome/Chromium**(HTML→PDF), **MinerU**(별도 venv 권장, `MINERU_EXE` · `MINERU_PY` 환경변수), 한글 폰트(Malgun Gothic 또는 Nanum). MinerU 설치와 플래그는 [`references/pipeline.md`](references/pipeline.md).

## 빠른 시작

```bash
export SKILL=/path/to/book-study-pdf   MINERU_EXE=mineru   MINERU_PY=/path/to/mineru-venv/bin/python
mkdir book_foo && cd book_foo && mkdir _src && cp "책.pdf" _src/src1.pdf
cp "$SKILL/assets/style.css" "$SKILL/scripts/"*.py "$SKILL/templates/book.json" "$SKILL/templates/_GATE.md" .
python probe.py _src && cat _probe.txt          # 0단계
python _pipeline.py 1                            # rotate scan/fix → MinerU
python contact_sheet.py out1/src1/ocr/images cs  # 전수 확인 → _GATE.md 에 분류
python _extm.py 01 11 30 0                       # 1권 원문 (책 11~30쪽)
# ch01.html 집필 → python _fix.py ch01.html → python _chain.py 01 --nobuild → python prewidth.py 100 → python _chain.py 01 → cat _rep.txt
python build.py all && python build.py merge && python build.py deploy
```

## 저장소 구조

```
SKILL.md                 에이전트 실행 지침 (Claude Code 스킬 본체)
AGENTS.md                에이전트 중립 진입점 · 읽는 순서 · 완료 정의
references/              pitfalls · book-types · chart-mode · translate-mode · writing · checkers · pipeline · audit
scripts/                 probe rotate split contact_sheet build audit … (38개, 작업 폴더에 복사해서 쓴다)
assets/style.css         A4 인쇄용 CSS (차트 오버레이 · 시험 .qa 포함)
templates/               book.json · _GATE.md · chapter.html · chart-figure.html · front.html
prompts/auto-continue.md 여러 권을 묻지 않고 연속 작업시키는 프롬프트
```

## 주의

- 결과물은 **구입자 본인의 개인 학습용**이다. 원문 인용은 이해에 필요한 최소한으로 제한하고, 학습노트를 배포하지 않는다. 판권면에 AI 사용 금지 문구가 있으면 서지에 명시한다.
- 이 저장소에는 **책 내용이 들어 있지 않다.** 지침 · 스크립트 · 빈 템플릿뿐이다.
- 한글을 콘솔에 `print` 하면 Windows cp949 에서 깨진다 — 모든 검사 결과는 `_*.txt` 파일로 나온다.

## License

MIT — `LICENSE`.
