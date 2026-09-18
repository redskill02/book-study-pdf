# -*- coding: utf-8 -*-
"""원문 대조 패스 — 집필이 끝난 뒤 '별도 패스'로 반드시 돌린다.

**모드에 따라 방법이 완전히 다르다.**

  translate : 원문 영어 / 노트 한국어 → 단어 매칭이 성립하지 않는다.
              자동 판정하지 않고 **사람이 볼 체크리스트**를 만들어준다.

  digest    : 원문 한국어 / 노트 한국어 → 매칭이 될 것 같지만 **안 된다.**
              digest는 제목을 의역하는 것이 목적이기 때문이다.
              "함수 호출의 구조" → "함수 호출 — 점프만으로는 안 되는 이유"
              『프로그램은 어떻게 작동하는가』에서 제목 문자열로 대조했더니
              **18건이 뜨고 전부 오탐**이었다. 오탐이 쌓이면 진짜 누락 1건이 묻힌다.
              그래서 제목이 아니라 **내용어(명사) 단위**로 대조한다.

사용법:
  python audit.py "<원문 md 폴더>" "<학습노트 html 폴더>" [--mode digest|translate]
  (--mode 생략 시 학습노트 폴더의 book.json에서 mode를 읽는다)

출력: <학습노트 폴더>/_audit.txt
"""
import os, sys, io, re, glob, json

args = [a for a in sys.argv[1:] if not a.startswith("--")]
src_dir, html_dir = args[0], args[1]

mode = None
if "--mode" in sys.argv:
    mode = sys.argv[sys.argv.index("--mode") + 1]
if mode is None:
    cfg = os.path.join(html_dir, "book.json")
    if os.path.exists(cfg):
        mode = json.load(io.open(cfg, encoding="utf-8")).get("mode")
mode = mode or "translate"

html = "\n".join(io.open(f, encoding="utf-8").read()
                 for f in sorted(glob.glob(os.path.join(html_dir, "ch*.html"))))
fr = os.path.join(html_dir, "_front.html")
if os.path.exists(fr):
    html += io.open(fr, encoding="utf-8").read()
# SVG의 <text>도 남긴다 — 도표 라벨에만 존재하는 개념이 실제로 있다
text = re.sub(r"<[^>]+>", " ", html)
text = re.sub(r"\s+", " ", text)
svg_count = html.count("<svg")

HEAD = re.compile(r"^(#{1,4})\s+(.+?)\s*$")
ENUM = re.compile(r"\b(\w+)\s+(ways?|steps?|reasons?|types?|things?|elements?|rules?|parts?|levels?)\b", re.I)
KOR = re.compile(r"([가-힣\d]+)\s*(가지|단계)")
ANCHOR = re.compile(r"\b[A-Z]{2,6}\b|\$[\d,]+(?:[KMB])?|\b\d{2,}%")
STOP = set("""A AN THE AND OR BUT IF SO TO OF IN ON AT BY FOR IT IS ARE WAS BE DO
YOU YOUR I ME MY WE US THEY THEM NOT NO YES ALL ONE TWO NEW OLD FREE GIFT LOW HIGH
BONUS MORE LESS BEST GOOD BAD BIG WHY HOW WHAT WHO WHEN NOW THEN HERE THERE
STEP PRO TIP QR PDF OK VS PS DM CTA""".split())
SKIP_FILE = re.compile(r"^00_")
SKIP_HEAD = re.compile(
    r"Table of Contents|Thank You|To \w+:|Acknowledg|워밍업|위밍업|위임업|워임업|퀴즈|^정답$|^해설$|^COLUMN$",
    re.I)
# 장 표시("제1장")는 내용이 아니다. OCR이 뭉개서 제1정·제2점·제8광처럼 나오므로
# 글자까지 맞추려 하지 말고 패턴으로 통째로 버린다.
CHAP_MARK = re.compile(r"^제\s*\d+\s*[가-힣]?\s*$")
# 명령줄·코드 조각도 헤딩으로 잡히지만 대조 대상이 아니다
CODE_HEAD = re.compile(r"^(#include|>>>|[a-z0-9_.]+\s+-{1,2}[a-zA-Z]|List\s|BB#)")

# digest 대조에서 버릴 기능어 — 이게 걸리면 아무 데나 다 매칭된다
KSTOP = set("""것 수 때 등 및 그 이 저 하는 되는 있는 없는 위한 대한 통해 보자 하기 한다
방법 구조 이유 관계 경우 내용 부분 사용 이용 확인 설명 시작 실행 처리 기능 정보 데이터
무엇 어떻게 어떤 이란 인가 살펴 알아 만들 해보 넘어 우리 여러분 필자 이번 다음 지금""".split())


def content_words(title):
    """제목에서 '내용어'만 뽑는다. 의역해도 이건 대체로 살아남는다."""
    t = re.sub(r"[^\w가-힣]+", " ", title)
    out = []
    for w in t.split():
        if w in KSTOP or len(w) < 2:
            continue
        out.append(w)
    return list(dict.fromkeys(out))


def found(w):
    """한국어는 조사가 붙고, 원문 OCR은 띄어쓰기를 자주 먹는다.

    "2진수와16진수" 같은 덩어리를 그대로 찾으면 당연히 없다.
    노트에는 "2진수와 16진수"로 띄어 썼기 때문이다.
    그래서 조사 절단 → 덩어리 분해 순으로 찾아본다.
    """
    if w in text:
        return w
    if re.match(r"^[가-힣]+$", w) and len(w) >= 3:
        stem = w[:-1]
        if len(stem) >= 2 and stem in text:
            return stem
    # 띄어쓰기가 먹힌 덩어리 — 숫자/한글 경계와 조사로 쪼개 조각을 찾는다
    if len(w) >= 5:
        parts = re.split(r"(?<=\d)(?=[가-힣])|(?<=[가-힣])(?=\d)|와|과|의|를|을|은|는", w)
        for p in parts:
            if len(p) >= 2 and p not in KSTOP and p in text:
                return p
    return None


heads, enums, anchors, digest_rows = [], [], {}, []
n_head = 0
for md in sorted(glob.glob(os.path.join(src_dir, "**", "*.md"), recursive=True)):
    name = os.path.basename(md)
    if SKIP_FILE.match(name):
        continue
    heads.append("")
    heads.append("=== " + name + " ===")
    for i, ln in enumerate(io.open(md, encoding="utf-8"), 1):
        m = HEAD.match(ln)
        if m and not SKIP_HEAD.search(m.group(2)):
            lvl, title = m.group(1), m.group(2).strip()
            if CHAP_MARK.match(title) or CODE_HEAD.match(title):
                continue
            n_head += 1
            heads.append("  [ ] L%-5d %-4s %s" % (i, lvl, title))
            if mode == "digest":
                ws = content_words(title)
                hit = [x for x in (found(w) for w in ws) if x]
                digest_rows.append((len(hit), title, ws, hit, name, i))
        for m2 in ENUM.finditer(ln):
            enums.append("  %-30s L%-5d %s" % (name, i, m2.group(0)))
        for m3 in KOR.finditer(ln):
            enums.append("  %-30s L%-5d %s" % (name, i, m3.group(0)))
        for a in ANCHOR.findall(ln):
            anchors.setdefault(a, [0, name, i])
            anchors[a][0] += 1

missing = sorted((v[0], k, v[1], v[2]) for k, v in anchors.items()
                 if v[0] >= 3 and k not in text and k not in STOP)

out = ["원문 대조 — mode: %s" % mode, "=" * 70, ""]

if mode == "digest":
    zero = [r for r in digest_rows if r[0] == 0 and r[2]]
    weak = [r for r in digest_rows if r[0] == 1 and len(r[2]) >= 3]
    ok_n = len(digest_rows) - len(zero) - len(weak)
    out.append("[A] 개념 대조 — 제목이 아니라 '내용어'가 노트에 있는지 본다")
    out.append("    digest는 제목을 의역하는 것이 목적이라 문자열 일치로는 판정할 수 없다.")
    out.append("    (제목 문자열로 대조했다가 18건이 뜨고 전부 오탐이었던 적이 있다.)")
    out.append("")
    out.append("  원문 헤딩 %d개 중" % len(digest_rows))
    out.append("    내용어 0개   %3d개   <- 진짜 누락 후보. 반드시 원문을 열어 확인한다" % len(zero))
    out.append("    내용어 1개만 %3d개   <- 약하게 다뤘을 수 있다. 훑어본다" % len(weak))
    out.append("    나머지       %3d개   <- 다뤄진 것으로 본다" % ok_n)
    out.append("")
    if zero:
        out.append("  == 내용어 0개 — 진짜 누락 후보 ==")
        for _, title, ws, _h, name, i in zero:
            out.append("  !! %-44s  %s L%d" % (title[:44], name, i))
            out.append("       내용어: %s" % " / ".join(ws))
    else:
        out.append("  == 내용어 0개 — 없음 ==")
    if weak:
        out.append("")
        out.append("  == 내용어 1개만 — 약하게 다뤄졌을 수 있음 ==")
        for _, title, ws, hit, name, i in weak:
            out.append("   ? %-44s  ('%s' 만 확인됨)" % (title[:44], hit[0]))
    out.append("")
    out.append("[A-2] 전체 헤딩 목록 — 위 판정이 미심쩍으면 여기서 직접 본다")
    out += heads
else:
    out.append("[A] 원문 헤딩 체크리스트 — 노트에 대응 항목이 있는지 하나씩 확인한다")
    out.append("    원문이 영어라 단어 매칭이 성립하지 않는다. 자동 판정하지 않는다.")
    out += heads

out.append("")
out.append("[B] 열거형 표현 — 'N가지'라면 N개 항목이 각각 '본문'을 갖고 있는지 센다")
out.append("    표 한 줄로 요약하고 내용을 빠뜨리는 것이 가장 흔한 누락 유형이다.")
out += sorted(set(enums))
out.append("")
out.append("[C] 앵커 누락 후보 — 원문에 3회 이상 나오는데 노트에 없는 약어·금액·비율")
out.append("    오탐이 있다. 한국어로 풀어 쓴 경우가 많으므로 반드시 원문을 열어 확인한다.")
for cnt, k, name, i in sorted(missing, reverse=True)[:40]:
    out.append("  %-12s 원문 %2d회   최초 %s L%d" % (k, cnt, name, i))
out.append("")
out.append("[D] 참고 — 학습노트 SVG %d개 / 원문 헤딩 %d개" % (svg_count, n_head))
out.append("    컨택트시트 계획표의 재작도 대상 수와 비교한다. 모자라면 그만큼 누락이다.")

io.open(os.path.join(html_dir, "_audit.txt"), "w", encoding="utf-8").write("\n".join(out))
print("[OK] _audit.txt written (mode=%s) -> read it with cat" % mode)
