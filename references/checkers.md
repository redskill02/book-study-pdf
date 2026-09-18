# 검사기 12종과 권별 체인

**수치와 번호를 손으로 세지 마라.** 6개 챕터 중 5개가 틀렸던 적이 있고, 도표를 하나 추가하자 또 어긋났다.
**장을 하나 쓸 때마다 전부 돌린다.** 하나라도 빼면 사고가 났다(`.exam` 이 8장 내내 안 닫힌 채 나갔다, 함정 #37).

결과는 전부 **`_<이름>.txt` 파일**로 쓴다 — 콘솔이 cp949 라 한글을 직접 찍지 않는다. `cat` 으로 읽는다.
검사기를 `> _stats.txt` 처럼 리다이렉트하면 build.py 가 쓰는 결과 파일을 덮어써 `autofit` 이 깨진다 — **리다이렉트 없이** 돌린다.

---

## 1. `build.py` 8종

| 명령 | 검사 | 통과 기준 | 결과 파일 |
|---|---|---|---|
| `stats` | 커버 `.meta` 문자열 `도표 N · 만화 4컷 N편 · 예시 N · 시험문제 N` 이 실제 개수와 **글자 단위로** 일치하는가. 도표 = `<figure>` − 만화(`4컷 만화로 재구성` 문자열 수), 예시 = `.kr-case`, 문항 = `class="q"` | 불일치 0 · rc 0 | `_stats.txt` |
| `blocks` | 챕터마다 `.recall`(덮고 쓰기) · `.exam` · `.answers` · `.cut`(합격선) · `.tutor` 가 각 1개인가. `ch99` 는 회상 0 예외(로그에 찍힘) | `회상 1 · 시험 1 · 정답 1 · 합격선 1 · 튜터 1` | `_blocks.txt` |
| `headings` | `<h2>` 절 번호가 연속인가 (§1 → §2 …) | `연속` | `_headings.txt` |
| `svgbox` | SVG 콘텐츠의 최대 y 가 `viewBox` 높이를 넘는가 (표 마지막 행 잘림) | 넘침 0 | `_svgbox.txt` |
| `svgfit` | `<text>` 의 추정 폭이 그 앵커를 품은 `<rect>` 를 **가로로** 넘는가. HTML 엔티티를 풀고 `<g>` 의 `text-anchor` 를 상속해 계산 | 넘침 0 | `_svgfit.txt` |
| `linegap` | 같은 SVG 안에서 두 `<text>` 가 **세로로 포개지는가** (svgfit 이 못 보는 방향). 같은 y 다른 x 의 "간격 0.0" 은 가로 겹침 | 겹침 0 | `_linegap.txt` |
| `comicfit` | 만화 칸(`rect`) 바닥을 캡션 baseline 이 뚫는가. **검사 대상 수를 함께 찍고 0이면 rc 1** | `만화 N편 / 글자 M개 검사` · 넘침 0 | `_comicfit.txt` |
| `tags` | 짝 없는 `<div>` · `<figure>` · `<svg>` | 0 | `_tags.txt` |

폭 추정 모델(`_text_width`): ASCII 0.52(`iljI.,'"()[] ` 는 0.30) · 한글 1.02 · 기타 0.95 × font-size. `<text>` 마다 `font-size` 가 있어야 한다 — `<g>` 상속은 `linegap` 이 12pt 로 읽어 89건 오탐을 냈다(함정 #71). `pushg.py` 가 `<g>` 속성을 `<text>` 로 내려 준다.

그 외 `build.py` 명령 — `chNN`(권 빌드) · `all` · `merge`(합본 + 빈 쪽 · 폰트 · 북마크 검증 → `_verify.txt`) · `deploy` · `render`(도표 쪽 전수 렌더 · 만화 우선 → `_render.txt`) · `page N`(합본 N쪽 PNG) · `find "키워드"`.

## 2. `imgcheck.py` 4종 (`figures: chart` 일 때 필수, 아니어도 돌려서 0 확인)

| 명령 | 검사 | 통과 기준 | 결과 파일 |
|---|---|---|---|
| `imgfit` | 모든 `<img>` 가 `<figure>` 안 + `<figcaption>` | 0 | `_imgfit.txt` |
| `imgres` | 크롭 가로 ≥ 900px | 0 | `_imgres.txt` |
| `imgcite` | 캡션에 `원본\s*\d+\s*권\s*\d+\s*쪽` | 0 (`원본 3권 4쪽 · 5쪽` 형식, `4~5쪽` 은 실패) | `_imgcite.txt` |
| `size` | 권별 ≤ 40MB · 합본 ≤ 400MB | 0 (`pdf/` 안 합본 오판은 무시) | `_imgsize.txt` |

## 3. 집필 직후 세 가지 — 검사기가 못 잡는 것

```bash
grep -n "^<text.*<[biu]>" ch*.html _front.html   # SVG <text> 안의 <b> — 조용히 상자 밖으로 나간다(함정 #36)
python fixbottom.py .                            # rect 바닥에 잘리는 글자 → rect 높이만 키운다(함정 #38)
python autofit.py .                              # svgfit/linegap 지적분을 글자 크기로 해소(함정 #40, MIN 7pt)
python _shrink.py chNN.html 3.8                  # 4점대 작은 글자는 autofit 이 무력 → 비례 축소(floor 3.8)
```

`autofit` · `_shrink` 는 **`svgfit` · `linegap` 을 먼저 돌린 뒤** 결과 파일을 읽어 동작한다. 두세 번 돌려도 남으면 그때 문장을 줄인다(`_retext` 방식: prefix → 새 문장 표).

## 4. 권별 체인 — `_chain.py`

권 하나를 쓸 때마다 이 순서다. 토큰과 실수를 절반으로 줄인다.

```bash
python _fix.py chNN.html                # ① 자작 오타 정규식: text-antml-anchor · antml-middle · <text name="x"> · font:size · 잘못 섞인 <parameter>
python _chain.py NN --nobuild           # ② _chNN_b.html 이 있으면 이어 붙임 → <class ' · <table · <parameter · </invoke 검출
                                        #    → esctitle · strip · flatg · pushg → checkall 사전 → svgfit · linegap · svgbox · tags → prewidth 100
                                        #    → _rep.txt  (비어 있으면 "pre-checks clean")
python prewidth.py 100                  # ③ <pre> 줄 폭 (한글 2 · ASCII 1 단위). 표는 손으로 열 축소 — 자동 줄바꿈은 표를 망가뜨린다
python _chain.py NN                     # ④ fixbottom · autofit · pushg · build chNN · render · stats · checkall 2차 · svgfit/linegap 2차
                                        #    · svgbox/comicfit/tags/blocks/headings 2차 · 쪽별 첫 줄 목록 · _ovNN.png (첫 8쪽 개요)
cat _rep.txt                            # ⑤ 남은 지적을 고치고 ②~④ 반복. 비어야 통과
# ⑥ 눈으로: _ovNN.png 첫 타일(커버 .meta 가 1쪽에 있나 · h1 ≤ 600자) · 만화 쪽 100% · 도표 쪽 5장+ Read
python _done.py NN "chNN 14p · 도표 10(크롭 1 · 재작도 9) · 만화 2 · 예시 3 · 문항 32 · 12 checkers 0"   # ⑦ 임시 파일 정리 + _GATE.md 기록
```

`_chain.py` 가 검출하는 것(`!!`) — `<parameter>` · `</invoke` · `<class '` 같은 **도구 출력이 HTML 에 섞여 들어간 흔적**(함정 #84 · #93), `<html` 이 2개(잘린 파일을 이어 붙인 흔적), `<text>` 안 `<b>`.

## 5. 예방 규칙 — 처음부터 이렇게 쓰면 수정이 거의 없다

| 대상 | 한계 | 근거 |
|---|---|---|
| 커버 `<h1>` | ≤ 600자 | 넘으면 `.meta` 가 2쪽으로 밀려 `stats` 는 통과하는데 커버가 깨진다. `_asm.py` 가 `len(h1)` 을 찍는다 |
| `<pre>` 한 줄 | ≤ 100 단위(한글 2) | 106 이 아니라 100 — `.kr-case` 안에서는 100 (함정 #88). 표는 `east_asian_width` 패딩으로 **생성**한다(함정 #97 · #100). 4열 이내 · 판정 열 ≤ 18~22자 |
| 3-box 도표(690×150) 4.3pt 줄 | ≤ 55자 | 세 칸 폭 216 |
| SVG 표 4.3pt 셀 | ≤ 110자 | |
| 인터뷰 · 인용 4.3pt 줄 | ≤ 80자 | 85~95자면 `_shrink` 3회 + 문장 축약 |
| 만화 캡션 baseline | 칸 바닥 − 8pt | `svgfit` 은 가로만 본다(함정 #25) |
| SVG 라벨용 투명 rect | 글자보다 좌우 4pt 넓게 | 함정 #70 |
| 얇은 강조 바 `height 8~12` | 위에 글자 두지 않기 | 검사기가 못 잡고 렌더에서만 보인다(함정 #52) |
| 덮고 쓰기 항목 | 한 줄 · ≤ 45자 · 12항목 | 두 줄로 감기면 마지막 `.line` 이 다음 쪽으로(함정 #102) |
| 시험 마크업 | `div.qa > (div.q > span.qtype) + div.line` · 문항마다 `div.qa` 하나 | 한 qa 에 몰면 페이지 분할이 안 되고, 다르게 쓰면 `stats` 가 문항 0 |
| 합격선 | `div.cut` 3단 + `div.warn2` **급소 3문항** | `blocks` 가 `.cut` 을 센다 |
| SVG `<title>` · `<pre>` 안 꺾쇠 | `&lt;` 로 | `<class 'int'>` 가 문서를 그 자리에서 잘라 먹는다(함정 #93) — `esctitle.py` |
| `overflow: hidden` | 쓰지 않는다 | 긴 줄을 조용히 자른다(함정 #32) |

## 6. 검사기를 믿는 법

- **0건은 통과가 아니라 "검출식을 의심할 신호"다.** `svgfit` 의 `\b` 가 백스페이스로 바뀌어 아무것도 못 잡은 채 "전부 이상 없음"을 낸 적이 있다. 검사기는 **검사 대상 수를 함께 찍고, 0이면 rc 1** 을 내야 한다(함정 #28). 개수를 **다른 경로로 한 번 더 센다** — `render` 의 만화 수 ↔ `stats` 의 만화 수.
- **뜬 것 중 서너 개를 손으로 확인해 오탐률을 먼저 잰다**(함정 #21 · #59). `svgfit` 이 `text-anchor` 를 상속 안 해 10건 중 9건이 오탐이었고, `probe` 가 `□` 를 손상문자로 세어 멀쩡한 4권을 재OCR 필수로 오판했다. 오탐이 쌓이면 진짜 1건이 묻힌다.
- **`linegap` 의 "간격 0.0" 은 절반이 오탐** — `svgfit` 과 함께 읽어야 판별된다(함정 #56). 작은 장식 `<rect>` 옆 라벨의 svgfit 오탐은 라벨을 `figcaption` 으로 옮기거나 헤더 바에 맡긴다(함정 #75 · #81).
- **검사기를 고친 뒤에는 결함을 일부러 되돌려 재검증한다**(함정 #19). 양방향 — 없으면 rc 1, 넣으면 rc 0.
- `_front.html` 은 checker 가 검사하지 않는다(함정 #47) — 렌더로 본다.
- 빈 쪽이 뜨면 "쪽 수"가 아니라 **"내용"** 을 본다 — Chrome 헤드리스가 답안 뒷부분을 통째로 삭제한 적이 있다(함정 #50).

## 7. 전권 끝 — 합본 검증

```bash
python build.py all && python build.py merge && cat _verify.txt   # 빈 쪽 0 · 한글 폰트 임베딩 OK · 북마크 = 챕터 수 + 1
python checkall.py                                                # 12종 0
python audit.py "<out 폴더>" . && cat _audit.txt                  # 정방향
python audit_kw.py && cat _audit_kw.txt                           # 역방향 (CLAIMS 교체한 사본)
python build.py deploy && cat _deploy.txt                         # 배포 폴더의 합본 1 + 권별 PDF 수를 센다. 임시명(ch01.pdf) 이 남지 않았는지
```
