# MinerU 변환 파이프라인

## 환경

MinerU 는 **전용 venv** 에 설치한다 (검증 버전: MinerU 3.x + CUDA torch. Windows 는 `mineru[core]` 만, vllm/lmdeploy 미설치).
이 스킬의 스크립트는 세 환경변수로 위치를 받는다 —

```
MINERU_EXE = <venv>/Scripts/mineru.exe  (또는 <venv>/bin/mineru)   ← run_mineru.py · _pipeline.py
MINERU_PY  = <venv>/Scripts/python.exe  (또는 <venv>/bin/python)    ← rotate.py 는 MinerU 의 OCR 엔진을 빌려 쓴다
SKILL      = 이 저장소 경로                                           ← 문서의 $SKILL
CHROME_PATH= (선택) Chrome 실행 파일                                   ← build.py, 없으면 표준 위치를 찾는다
```

설치 함정 — PyPI 기본 torch 는 Windows 에서 CPU 빌드다. `--index-url https://download.pytorch.org/whl/cu1xx` 와 `torch==x.y.z+cu1xx` 처럼 로컬 버전까지 명시해 강제 재설치한다(uv 는 버전 숫자만 같으면 건너뛴다). 모델(약 4.6GB)은 첫 실행 때 내려받는다.
MinerU venv 에는 PyMuPDF 가 없을 수 있다 — `rotate.py` 는 그래서 `pypdfium2` 를 쓴다(함정 #24). 스킬 스크립트의 나머지는 일반 python(`requirements.txt`)으로 돈다(함정 #63: 파이썬이 두 개다).

긴 작업(MinerU · rotate)은 셸 시간 한도에 걸린다 — Windows 는 `Start-Process` 로 detach, Linux/mac 은 `nohup … &` 로 띄우고 `_pipeline_done.txt` / `_mineru_done.txt` 를 지켜본다.

## 백엔드 선택 — `pipeline -m ocr`을 쓴다

| 백엔드 | 판단 |
|---|---|
| `pipeline` | **권장.** 안정적이고 언어 지정이 된다 |
| `vlm-engine` | 무거운데 이 용도에서 이득이 없다 |
| `hybrid-engine` | 마찬가지 |

모드는 `-m ocr`을 쓴다. `-m txt`는 기존 텍스트 레이어를 신뢰하는데,
**이런 스캔본 PDF의 텍스트 레이어는 그 자체가 불완전한 OCR 결과물**이라 신뢰할 수 없다.

언어는 한국어 책이면 `-l korean`, 영어 책이면 기본값(`ch`)이 잘 동작한다.

```bash
"$MINERU_EXE" -b pipeline -m ocr \
  -p "<원서.pdf>" -o "<출력폴더>"
```

## 변환 전에 — 0단계를 먼저 돌린다

```bash
python "$SKILL/scripts/probe.py" "<PDF 폴더>"
cat _probe.txt
```

원본에 **이미 OCR 텍스트가 들어 있는 경우**가 있다. 그게 쓸 만한지 먼저 판정한다.
판정이 `재OCR 필수`면 변환 후 반드시 `--compare`로 before/after를 확인한다.

```bash
python ".../probe.py" "<PDF 폴더>" --compare "<MinerU 출력 폴더>"
```

실측 — 『프로그램은 어떻게 작동하는가』는 원본 레이어의 고아 자모가 **1,729개**였고
재OCR 후 **5개**가 됐다. 재OCR이 유효했다.

## 뒤집힌 페이지 — MinerU는 못 고친다

스캔본에는 한두 장씩 거꾸로(180도) 또는 옆으로(90/270도) 들어간 쪽이 섞인다.
**MinerU에 기대면 안 된다.** 소스를 확인한 결과다.

```python
# mineru/model/table/cls/mineru_table_ori_cls.py
ORIENTATION_SCORE_LABELS = ("0", "90", "270")
```

- **180도가 후보에 없다.** 거꾸로 된 쪽은 구조적으로 검출 불가다
- 그나마도 대상이 **표(table) 크롭**이지 페이지 전체가 아니다

그래서 `scripts/rotate.py`를 변환 **전에** 돌린다.

```bash
V="$MINERU_PY"
R="$SKILL/scripts/rotate.py"
"$V" "$R" scan "<PDF 또는 폴더>"    # 백그라운드 권장. 쪽당 약 4초
cat _rotate.txt
"$V" "$R" fix  "<PDF 또는 폴더>"    # <원본>_정방향.pdf 생성
"$V" "$R" scan "<PDF>" --fast     # 사전필터. 아래 조건을 읽고 쓸 것
```

**보정본을 변환 입력으로 쓴다.** 원본을 넣으면 아무 의미가 없다.

### 판정 방법 — 축을 먼저 정하고, 축 안에서 겨룬다

회전 후보마다 OCR을 돌려 `신뢰도 × 글자수` 합계를 비교한다. 다만 **한 번에 4방향을 겨루면 안 된다.**

```
40쪽 정방향   가설   0 = 283.7점   가설  90 = 282.8점   <- 거의 동점
              가설 180 =  20.0점   가설 270 =  14.1점
```

OCR이 세로로 긴 박스를 **자동으로 눕혀서** 인식하기 때문에 0도와 90도가 갈리지 않는다.
반면 0도 대 180도는 **14배**까지 벌어진다. 그래서 2단으로 나눈다.

1. **축 결정** — 검출된 박스 중 세로로 긴 것(`w/h < 0.8`)의 비율. 절반을 넘으면 90/270 축
2. **축 안에서만 점수 비교** — `0 vs 180` 또는 `90 vs 270`

점수차가 1.3배 미만이면 판정하지 않고 **`보류`로 남겨 사람에게 넘긴다.**

```bash
"$V" "$R" peek "<PDF>" 41 88     # _peek_0041.png 로 뽑아 눈으로 본다
```

### 실측

30쪽짜리 시험용 PDF에 `{6:180, 12:180, 19:90, 25:270}`을 심어놓고 돌렸다.

| 쪽 | 심은 왜곡 | 판정 보정각 | 점수차 |
|---|---|---|---|
| 6 | 180도 | 180도 ✅ | 15.4배 |
| 12 | 180도 | 180도 ✅ | 11.0배 |
| 19 | 90도 | 270도 ✅ | 37.7배 |
| 25 | 270도 | 90도 ✅ | 4.6배 |

**4/4 정확, 나머지 26쪽 오탐 0.** `판정불가`로 빠진 1쪽은 실제로 백지였다.

## 이 변환의 진짜 가치

재OCR은 일부 오류를 고치지만 **새 오류도 만든다.** 텍스트 정확도가 목적이 아니다.
진짜 이득은 **구조화 + 노이즈 제거**다.

> 다만 위 실측처럼 **원본 레이어가 심하게 망가진 경우에는 텍스트 정확도 자체가 목적이 된다.**
> 0단계 판정이 그 둘을 갈라준다.

- 머리말·꼬리말·페이지 번호 블록 제거 (4권에서 2,176개 제거됨)
- 차트 축 눈금 라벨 같은 쓰레기 텍스트를 이미지 참조로 대체
- 헤딩 레벨(`text_level`)이 붙어 대단원 분할이 가능해진다
- 이미지가 `images/` 로 전부 추출된다 ← **이게 핵심이다**

## 대단원 분할

`scripts/split.py`가 `content_list.json`을 읽어 `SECTION I`, `SECTION II` … 로 자른다.

핵심 로직 — **각 섹션 번호의 최초 출현만 경계로 삼는다.**
목차나 상호참조에 같은 문자열이 다시 나와서 과분할되는 것을 막는다.

```python
SEC = re.compile(r"^\s*SECTION\s+([IVXLCD]+|[A-Z])\b\s*[:\s]", re.I)
bounds, seen = [], set()
for i, b in enumerate(body):
    if not b.get("text_level"): continue
    m = SEC.match(unesc(b.get("text", "")))
    if not m: continue
    num = m.group(1).upper()
    if num in seen: continue      # 최초 출현만
    seen.add(num); bounds.append(i)
```

책마다 섹션 표기가 다르면(`Chapter`, `Part` 등) 이 정규식만 바꾼다.
분할 후 **파일 수와 원서 목차의 대단원 수가 일치하는지 반드시 확인**한다.

## 분량이 큰 대단원은 둘로 나눈다

`$100M Leads`의 Section III는 202KB였다. 한 챕터 HTML로 만들면 너무 길어진다.
`ch03`(III-1) / `ch04`(III-2)로 나누고 `book.json`의 `titles`에 그렇게 적는다.
합본 북마크에는 `SECTION III-1`, `SECTION III-2`로 나온다.

### `--fast` — 언제 써도 되나

1차 통과가 모든 쪽에 OCR 을 돌리기 때문에 시간의 대부분을 거기서 쓴다.
`--fast` 는 **원본 텍스트 레이어**만 보고 검사 대상을 좁힌다.

    (쪽별 고아 자모율 상위 10%) ∪ (한글 150자 미만)

실측 — 브랜드설계자 2·3권에서 **246쪽 → 35쪽 / 9분 → 130초**,
알려진 뒤집힌 쪽 3개를 **전부 재검출**했다. 트래픽설계자에서도 3/3이었다.

**두 조건이 둘 다 필요하다.** 글자가 적은 쪽은 자모도 적어서 자모율 순위가 안 올라간다 —
트래픽설계자 1권 138쪽(한글 1자)은 자모율 235위였고,
『인생을 운에 맡기지 마라』 1권 표지(한글 9자)는 206위였다.

**쓰지 말아야 할 때**
- 원본에 **텍스트 레이어가 아예 없을 때** — 자동으로 전수로 되돌아가지만, 그러면 이득도 없다
- **처음 다루는 종류의 책**(세로쓰기·만화·사진집 등) — 근거가 된 실측은 전부 일반 단행본이다
- 시간이 급하지 않을 때. **기본값(전수)이 여전히 옳다**
