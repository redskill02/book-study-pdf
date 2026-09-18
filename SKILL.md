---
name: book-study-pdf
description: 책 PDF(스캔본·OCR본)를 MinerU로 구조화해 대단원별 한국어 학습노트를 만들고, 원본 도표를 한글 벡터로 재작도하거나(일반 도서) 원본 차트를 크롭해 한글 주석을 얹고(주식·차트 도서), 영어 원서는 한국어로 번역하며 정리하고, 쉬운 예시·4컷 만화·덮고 쓰기·시험문제·합격선·튜터 프롬프트를 챕터마다 붙여, 12종 자동 검사를 통과한 하나의 합본 PDF로 배포한다. "책 학습노트", "원서 번역 정리", "PDF 쉽게 정리", "챕터별 요약", "시험문제 만들어줘", "OCR 책", "MinerU", "합본 PDF", "주식책 차트 정리" 같은 요청에서 쓴다.
---

# 책 PDF → 한국어 학습노트 PDF

책 한 권을 **읽고 시험까지 볼 수 있는 한국어 학습 자료**로 만드는 전체 파이프라인.
사용자는 이 작업을 반복해서 요청하므로, **매번 지시받지 않아도 아래 규격을 전부 적용한다.**

> 이 문서는 **에이전트가 읽는 실행 지침**이다. 사람용 개요는 `README.md`, 다른 에이전트(Codex · Cursor · Gemini CLI 등)용 진입점은 `AGENTS.md`.
> 문서 안의 `$SKILL` 은 이 저장소(스킬 폴더)의 절대 경로, `$MINERU_PY` / `$MINERU_EXE` 는 MinerU venv 의 python / mineru 실행 파일이다 (`references/pipeline.md`).

## 0. 먼저 책의 유형을 정한다 — 두 축

집필 방식은 **언어 축**과 **도판 축**으로 정해진다. 둘 다 `book.json` 에 적는다. 판별 절차는 `references/book-types.md`.

### 언어 축 — `mode`

| 모드 | 대상 | 핵심 작업 |
|---|---|---|
| `translate` | **영어(외국어) 원서** | 한국어로 **번역**하며 정리. 용어는 한국어 + 괄호 원어. 미국 맥락 사례는 **한국 사례로 대체**. 상세 `references/translate-mode.md` |
| `digest` | **한국어 책** (번역서 포함) | 번역이 필요 없다. 대신 **더 쉬운 말로 재정리**하고 예시로 풀어준다. 번역서는 **그 책의 표기**(인명 · 용어)를 따른다 |

### 도판 축 — `figures`

| 값 | 대상 | 도판 처리 |
|---|---|---|
| `redraw` (일반 도서) | 경영 · 자기계발 · 심리 · 과학 · 코드 책 등 | 원본 도표를 **전부 한글 인라인 SVG로 재작도**. 원본 이미지는 지면에 넣지 않는다 |
| `chart` (주식 · 차트 도서) | 주가 차트 · 매매 기록 · HTS 화면이 실린 책 | **5분류(A~E)**: 개념도 · 패턴 도해 · UI 캡처는 재작도(A · B · D′), **실제 종목 차트 · 기록표는 원본 600dpi 크롭 + 한글 주석 오버레이(C)**, 사진은 크롭(D), 장식은 버림(E). 상세 `references/chart-mode.md` |

**판별 기준 한 줄** — 도판에 **저자의 매매 흔적(사고판 자리 · 기호 · 실제 종목 · 기간)이 인쇄되어 있는가.** 있으면 `chart`. "차트처럼 생겼는가"가 아니다. 캔들을 지운 이평선 도해는 개념도라 재작도한다.

두 축은 독립이다 — 영어 주식책은 `translate` + `chart`, 한국어 코드 책은 `digest` + `redraw`.
**공통 목표는 같다** — 원본보다 읽기 쉽고, 그림으로 이해되고, 시험으로 확인되는 자료. 아래 규칙 · 순서 · 검증은 모든 조합에 동일하다.

## 기본 규칙 (사용자가 말 안 해도 지킨다)

1. **한 챕터(권)씩** 작성하고, 각 챕터마다 **스스로 검증**한 뒤 다음으로 넘어간다.
2. 중간에 **멈추고 물어보지 않는다.** 책 한 권을 끝까지 간 다음 보고한다. 판단이 필요하면 이 문서와 `references/` 의 규칙으로 스스로 정하고 근거를 `_GATE.md` 에 한 줄 남긴다.
3. 모든 챕터가 끝나면 **하나의 합본 PDF**로 합친다.
4. 출력은 전부 **한국어**. 원서 용어는 한국어 뒤 괄호로 병기한다.
5. 완료 시 **파일 경로를 출력**한다.
6. **원본 상태 보정은 묻지 않고 알아서 한다.** 0단계(재OCR 판정)와 0.5단계(뒤집힌 쪽 보정)는 사용자가 "학습노트 만들어줘"라고만 해도 **자동으로 돌린다.** 보정 사실은 최종 보고에 한 줄로 적는다.
7. **원본 PDF · 배포된 완성본을 절대 지우거나 덮어쓰지 않는다.** 작업 폴더를 만들기 전에 같은 이름이 있는지 확인한다(함정 #49).
8. 판권면에 "AI 사용 금지" 문구가 있으면 `_front` 서지에 **"개인 학습용 · 배포하지 않음"** 을 명시하고 계속한다.

## 각 챕터에 반드시 들어가는 7가지

| 요소 | `translate` (영어 원서) | `digest` (한국어 책) |
|---|---|---|
| **본문 정리** | 한국어 **번역**. 원문 구조 유지 | **더 쉬운 말로 재정리.** 전문용어는 풀어 쓰고 괄호로 원어 병기 |
| **원본 도판** | `redraw`: 한글 SVG 재작도 · `chart`: C유형은 크롭+주석, 나머지 재작도 | 동일. 한국어 도표라도 **다시 그린다** (스캔은 흐리고 검색이 안 된다) |
| **만화** | 저자의 일화·실패담을 4컷 SVG로 (권당 2편) | 동일. 추상적 개념은 **비유 상황**을 만화로 |
| **예시** | 미국 사례 → **한국 사례로 대체** (권당 3개) | 원문 예시가 부족하거나 어려우면 **쉬운 예시를 추가** |
| **덮고 쓰기** | 시험지 **앞**. 뼈대와 **개수만** 인쇄하고 내용은 빈칸 | 동일 |
| **시험문제 + 정답** | 챕터 끝. 객관식·단답·서술 혼합, 해설 포함. **설명형 1문항 필수**. `chart` 책은 **차트 판독형 · 패턴 식별형** 추가 | 동일 |
| **합격선 · 튜터 프롬프트** | 정답지 끝에 합격선(숫자 기준 3단 + 급소 3문항), 그 뒤 챕터 전용 튜터 프롬프트 | 동일 |

**순서를 지켜라 — 덮고 쓰기 → 시험 → 채점·합격선 → 튜터.**
먼저 보기 없이 꺼내보고(인출), 그다음 보기를 보고 고르고(재인), 그다음 스스로 판정한다. 이 순서가 뒤집히면 전부 재인 훈련이 된다.

### 책 전체에 한 번만 들어가는 것

| 요소 | 어디에 |
|---|---|
| 표지 · 차례 · 서지 · 사용법 · **학습 계획표의 "오늘 꺼낼 것" 열**(1·4·7·14일 복습 + 예비일 1일) | `_front.html` |
| **총정리** — 책의 지도 · 용어집 · 숫자 · 체크리스트 · **종합시험**(장을 섞은 문항 · 만화 2 · 예시 3 포함) | `ch99.html` |

### 권(챕터) 크기 기준

| | 일반 도서 | 주식 · 차트 도서 |
|---|---|---|
| 권당 원본 범위 | 18~31쪽 · 원서 장 경계를 살려 절 2~5개 묶음 | 동일하되 차트가 많은 장은 더 잘게 |
| 권당 결과 | 14~22쪽 · 도표 8~12 · 만화 2 · 예시 3 · 문항 30~36 | 18~22쪽 · 도표 8~12(크롭+재작도) · 나머지 동일 |

## 왜 이 구조인가 — 근거

| 원칙 | 이 스킬의 어디에 |
|---|---|
| **인출** — 읽기보다 덮고 떠올리기 | 덮고 쓰기 · 설명형 문항 · 튜터 프롬프트 |
| **분산** — 몰아서보다 며칠에 나눠 | 계획표의 "오늘 꺼낼 것" 열 (1-4-7-14) |
| **인터리빙** — 기초는 묶어서, 익숙해지면 섞어서 | 장별 시험(묶음) → 종합시험(섞음). **순서를 바꾸지 마라** |
| **이중부호화** — 글보다 글+그림 | 도표 재작도 · 차트 크롭 · 4컷 만화 |
| **메타인지** — 쉽게 느껴지면 의심하라 | 합격선. "읽은 느낌"과 실력은 자주 반대다 |
| **AI 협업** — 잡일은 AI, 판단은 나 | 튜터 프롬프트(한 번에 한 질문 · 강의 금지) |

**넣지 않는 것도 정해져 있다.** 하루 11시간 몰입, 수면·운동 지침, "기본서 버리고 기출부터" 같은 것은 근거가 일화적이거나 수험 특화라 학습노트가 다룰 자리가 아니다. 학습노트는 **재료를 요리하는 것**까지만 한다.

## 절대 규칙 — 원본 이미지

> "원본에서 꼭 전달하고자 하는 내용이 원본 사진(이미지)에 있을 확률이 높다."

- 원본 도표는 **웬만하면 살린다.** 본문에 없고 **그림에만 존재하는 개념·수치**가 실제로 있다 (`$100M Offers`의 Splinter Stack은 본문 언급 0회; 이탈 이유 10가지의 비율은 그림에만 있었다).
- **일반 도서**는 원본 이미지를 그대로 넣지 않고 **인라인 SVG로 재작도**한다. 스캔 이미지는 인쇄가 흐리고 PDF 안에서 글자 검색이 안 된다.
- **주식·차트 도서의 실제 차트(C유형)는 반대다 — 재작도하면 안 된다.** 저자가 사고판 자리와 실제 차트의 지저분함이 학습 목표라서, 다시 그리면 "교과서 속 깔끔한 패턴"이 되어 버린다. 원본 600dpi 크롭 + 한글 주석 오버레이로 넣는다.
- 이미지가 많아 보여도 **한 장씩 열어본다.** 장식 사이에 헤드라인 골격 14종이 숨어 있었고, 32장뿐인 책의 12장이 각 장 요약 상자였다.
- 누락이 발견되면 **심각도 순**으로 채운다: 프레임워크 > 프로세스 > 사례·팁.

## 작업 순서

**순서를 바꾸지 마라.** 0번과 3번을 건너뛰면 반드시 사고가 난다. 둘 다 실제로 겪었다.

0. **스캔본 완전성 확인 (5분, 무엇보다 먼저)** — 차례 쪽의 마지막 항목 쪽번호와 마지막 권의 끝 쪽번호를 맞춰본다. 빠진 범위가 있으면 표지·1장·마지막 장 세 곳에 명시하고 그 상태로 끝까지 만든다. 인쇄 목차의 쪽번호는 한 칸 밀려 있을 수 있다 — 장 경계는 **본문의 장 표제 쪽**으로 확정한다(함정 #35).

0. **원본 품질 검사 (변환보다 먼저)** — `scripts/probe.py`
   ```bash
   python "$SKILL/scripts/probe.py" "<PDF 폴더 또는 파일>"
   cat _probe.txt
   ```
   스캔본에 이미 들어 있는 OCR 텍스트를 믿어도 되는지 판정한다("프로그램"이 "ㅍ무ㅋ램"인 책이 있었다). `재OCR 필수`면 재OCR 후 `--compare` 로 before/after 를 확인한다. **고아 자모 0개도 안전이 아니다** — 눈에 띄는 오인식 낱말 두세 개를 직접 센다(함정 #29). 파일명이 `_ocr` 이어도 돌린다.

   0.5 **뒤집힌 페이지 검사** — `scripts/rotate.py` (MinerU venv 파이썬으로 실행 · 오래 걸린다 · detach)
   ```bash
   "$MINERU_PY" "$SKILL/scripts/rotate.py" scan "<PDF 또는 폴더>"   # 쪽당 약 4초
   cat _rotate.txt
   "$MINERU_PY" "$SKILL/scripts/rotate.py" fix  "<PDF 또는 폴더>"   # <원본>_정방향.pdf
   "$MINERU_PY" "$SKILL/scripts/rotate.py" peek "<PDF>" 41 88       # 보류 쪽을 눈으로
   ```
   MinerU는 180도를 **구조적으로 못 고친다**(후보각이 0/90/270, 대상도 표뿐). `보류` 는 직접 본다. 챕터 간지의 **세로 장식 글자**는 오탐이다(함정: 판정불가 +1 쌍). 보정 후에는 **`_정방향.pdf` 를 1단계 입력으로 쓴다.**

1. **변환** — MinerU `-b pipeline -m ocr` (한국어 책 `-l korean`, 영어 원서 생략) → `references/pipeline.md`.
   `scripts/_pipeline.py` 가 0.5 + 1 을 한 번에 돌린다. 여러 권이면 **전부 끝날 때까지 집필 금지.**
   **주식·차트 도서는 이중 트랙** — `downsample.py`(300dpi 사본 · 쪽 크기 보존) → MinerU 구조화 → `crop.py` 가 그 bbox 로 **원본에서** `image · table · chart` 세 타입을 전부 크롭. 원본이 수백 MB 면 `tojpg.py` 로 JPEG 사본을 MinerU 에 넣는다.
2. **분할 · 추출** — `scripts/split.py` 로 대단원별 md. 집필 입력은 책 유형에 따라 다르다:
   `_extm.py NN a b OFF` (MinerU content_list — `text`+`list_items`+`aside_text` 를 다 읽는다, 함정: `type:"list"`) /
   `_extf.py` · `srcpdf.py` (원본 텍스트 레이어 — probe 가 양호하거나 **차트 책**일 때. MinerU md 는 띄어쓰기를 지운다, 함정 #98).
   분권 책은 **권마다 오프셋(책쪽 = pdf쪽 + K)을 인쇄 쪽번호로 다시 재서 `_GATE.md` 에 적는다.**
3. **컨택트시트 (집필 전 필수)** — `scripts/contact_sheet.py` 로 원본 이미지를 **전수 확인**하고, `_GATE.md` 에 재작도 대상을 심각도(⭐⭐⭐/⭐⭐/⭐) 또는 5분류(A~E)로 적은 계획표와 권 구성표를 쓴다.
   > **게이트 — PDF가 여러 권으로 쪼개져 있으면, 마지막 권 변환이 끝나고 모든 권의 컨택트시트를 확인하기 전까지 `ch01` 의 첫 줄도 쓰지 않는다.** 기다리는 비용보다 되돌리는 비용이 크다.
   `chart` 책은 크롭 `crops/_index.txt` 와 `_cs.py` 시트로 분류하고, 캡션을 쓰기 전에 `idsheet.py` 로 **파일명 ↔ 차트를 눈으로 확정**한다(파일명만 믿으면 한 칸씩 밀린다).
4. **집필** — 챕터당 HTML 하나. 규격은 `references/writing.md`, 골격은 `templates/chapter.html`. 원문은 **`wc -l` 로 길이를 보고 끝까지 읽는다**(함정 #20). 긴 장은 `chNN.html` + `_chNN_b.html` 두 파일로 쓰고 `_asm.py` 로 잇는다.
5. **빌드 · 자동 검사 · 시각 검증** — 권마다 아래 체인. 상세와 통과 기준은 `references/checkers.md`.
   ```bash
   python _fix.py chNN.html              # 자작 오타 정규식 (text-anchor 오타 · 잘못된 태그)
   python _chain.py NN --nobuild         # 조립 · esctitle/strip/flatg/pushg · 사전검사 → _rep.txt
   python prewidth.py 100                # <pre> 줄 폭 (한글 2 · ASCII 1)
   python _chain.py NN                   # fixbottom · autofit · build · 12 검사기 · 쪽 목록 · _ovNN.png
   cat _rep.txt                          # 비어 있어야 통과. 남으면 고치고 다시
   ```
   `_chain.py` 는 `build.py` 8종(`stats blocks headings svgbox svgfit linegap comicfit tags`) + `imgcheck.py` 4종(`imgfit imgres imgcite size`)을 돌린다. **12종 전부 0건이어야 다음 권으로 간다.**
   그리고 눈으로 본다 — `_ovNN.png`(첫 8쪽 개요)와 `build.py render` 결과에서 **만화는 100%, 도표 쪽은 5장 이상** Read 로 확인한다. 검사기가 0건이라고 통과가 아니다(함정 #28 · #32).
   끝나면 `python _done.py NN "<GATE 한 줄>"` 로 임시 파일을 지우고 `_GATE.md` 에 기록한다.
6. **원문 대조 (별도 패스 필수)** — `scripts/audit.py`(정방향: 원문 → 노트) + `audit_kw_template.py`(역방향: 노트 → 원문, CLAIMS 교체) → `references/audit.md`. `--mode` 는 `book.json` 에서 읽는다. **대상 수 0 · 전부 오탐 · 0건 통과는 검사기 고장을 먼저 의심한다.**
7. **표지 · 총정리 · 합본 · 배포** — `_front.html` · `ch99.html` → `build.py all` → `merge` → `imgcheck.py all` → `deploy`. 배포 폴더의 합본 1 + 권별 PDF 수를 센다.
8. **기록** — 진도표 · `_GATE.md` 갱신, 새로 겪은 함정은 `references/pitfalls.md` 에 번호를 붙여 추가한다.

## 빠른 시작

```bash
mkdir book_<약칭> && cd book_<약칭>              # 이름 중복 확인 먼저 (함정 #49)
mkdir _src && cp "<원본>.pdf" _src/src1.pdf      # 분권이면 src1, src2 …
cp "$SKILL/assets/style.css" .  &&  cp "$SKILL/scripts/"*.py .     # 스킬 스크립트 세트 복사
cp "$SKILL/templates/book.json" "$SKILL/templates/_GATE.md" .      # 책마다 채운다
python probe.py _src && cat _probe.txt
python _pipeline.py 1                            # rotate scan/fix → MinerU (detach 권장)
python contact_sheet.py out1/src1/ocr/images cs  # 전수 확인 → _GATE.md
# (chart 책) python downsample.py && python crop.py && python _cs.py 1 400 _cs1.png
python _extm.py 01 11 30 0                       # 또는 _extf.py / srcpdf.py
# ch01.html 집필 → 5번 체인 → _done.py → ch02 …
python build.py all && python build.py merge && python build.py deploy
```

`book.json` (경로는 슬래시로 쓴다, 함정 #44):

```json
{
  "book": "돈의 속성", "mode": "digest", "figures": "redraw",
  "output": "돈의 속성_학습노트_전권합본.pdf",
  "deploy": "<배포 루트>/_학습노트/돈의 속성",
  "titles":        { "_front": "표지 · 차례 · 사용법", "ch01": "1권 — …", "ch99": "총정리 · 종합시험" },
  "chapter_files": { "_front": "00_표지_차례.pdf", "ch01": "01_1권_….pdf", "ch99": "99_총정리.pdf" }
}
```

## 참조 문서

| 파일 | 언제 읽나 |
|---|---|
| `references/pitfalls.md` | **먼저 읽어라.** 실제로 겪은 함정 100여 건 |
| `references/book-types.md` | 책 유형 판별 트리 — 일반/주식·차트/코드/에세이·인터뷰/번역서, 유형별 집필 차이 |
| `references/chart-mode.md` | **주식·차트 도서** — 5분류 · 이중 트랙 · 주석 오버레이 · 검사기 4종 · 함정 |
| `references/translate-mode.md` | **영어 원서** — 번역 규격 · 용어 병기 · 한국 사례 대체 · 대조법 |
| `references/writing.md` | HTML 챕터 작성 규격 · 모드별 집필법 · SVG 작도법 · 시험문제 규격 |
| `references/checkers.md` | 12종 검사기와 권별 체인 · 출력 파일 · 통과 기준 · 오탐 판별 |
| `references/pipeline.md` | MinerU 변환 · 환경 · 실행 플래그 · 회전 검사 |
| `references/audit.md` | 원문 대조 패스 · 심각도 분류 |
| `prompts/auto-continue.md` | 여러 권을 묻지 않고 연속 작업시키는 프롬프트 |

## 자산

- `assets/style.css` — A4 인쇄용 공통 CSS (작업 폴더에 복사). 차트 크롭 오버레이 · 시험 `.qa` 포함
- `templates/` — `book.json` · `_GATE.md` · `chapter.html`(권 골격, 12 검사기 통과 확인) · `chart-figure.html`(크롭 도표 골격) · `front.html`(표지 골격)
- `scripts/` — 아래 표. 전부 작업 폴더에 복사해서 그 안에서 돌린다(`build.py` 는 자기 폴더의 `book.json` 을 읽는다)

| 단계 | 스크립트 |
|---|---|
| 0 · 0.5 | `probe.py`(텍스트 레이어 판정) · `rotate.py`(회전 scan/fix/peek, MinerU venv) |
| 1 변환 | `_pipeline.py`(rotate+MinerU) · `run_mineru.py` · `downsample.py`(300dpi 사본) · `tojpg.py`(JPEG 사본) |
| 2 추출 | `split.py`(대단원 md) · `_extm.py`(content_list) · `_extf.py` · `srcpdf.py` · `src.py`(텍스트 레이어) |
| 3 도판 | `contact_sheet.py`(원본 이미지 시트) · `crop.py`(bbox 크롭) · `_cs.py`(크롭 시트) · `idsheet.py`(ID 확정) · `view.py`(크롭 확대) · `anno.py`(주석 오버레이 생성기) |
| 5 검사 | `build.py`(빌드·합본·배포·검사 8종·render) · `imgcheck.py`(4종) · `checkall.py`(12종 일괄) · `_chain.py`(권별 체인) · `prewidth.py` · `_fix.py` · `_asm.py` · `esctitle.py` · `strip.py` · `flatg.py` · `pushg.py` · `fixbottom.py` · `autofit.py` · `_shrink.py` · `qawrap.py` · `_done.py` |
| 6 대조 | `audit.py`(정방향) · `audit_kw_template.py`(역방향, CLAIMS 교체) · `audit_kw_example_*.py` |
