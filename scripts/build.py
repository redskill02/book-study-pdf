# -*- coding: utf-8 -*-
"""챕터 HTML -> PDF 변환 · 합본 · 검증 · 배포.

작업 폴더(이 스크립트와 같은 위치)에 book.json 이 있어야 한다:
{
  "book":   "$100M Leads",
  "output": "$100M Leads_한국어_학습노트_전권합본.pdf",
  "deploy": "C:\\\\Users\\\\...\\\\_학습노트\\\\$100M Leads",
  "titles": {
    "_front": "표지 · 목차",
    "ch01":   "SECTION I — 여기서 시작",
    ...
  },
  "chapter_files": {
    "ch01": "01_SECTION1_여기서 시작.pdf",
    ...
  }
}

사용법:
  python build.py ch01     # 특정 챕터만
  python build.py all      # 전체 챕터 (_front 포함)
  python build.py merge    # 합본 생성 + 검증
  python build.py deploy   # 배포 폴더로 복사 (정식 파일명)
  python build.py page 47  # 합본 47페이지를 PNG로 렌더 (시각 검증용)
"""
import os, sys, glob, json, io, shutil, subprocess

BOOK   = os.path.dirname(os.path.abspath(__file__))
PDFDIR = os.path.join(BOOK, "pdf")
def _find_chrome():
    """Chrome/Chromium 실행 파일. 환경변수 CHROME_PATH 가 최우선."""
    env = os.environ.get("CHROME_PATH")
    if env and os.path.exists(env):
        return env
    cands = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/usr/bin/google-chrome", "/usr/bin/google-chrome-stable",
        "/usr/bin/chromium", "/usr/bin/chromium-browser",
    ]
    for c in cands:
        if os.path.exists(c):
            return c
    return "chrome"   # PATH 에 있기를 기대한다
CHROME = _find_chrome()
os.makedirs(PDFDIR, exist_ok=True)

CFG = json.load(io.open(os.path.join(BOOK, "book.json"), encoding="utf-8"))
TITLES = CFG.get("titles", {})


def to_pdf(html_path):
    name = os.path.splitext(os.path.basename(html_path))[0]
    out = os.path.join(PDFDIR, name + ".pdf")
    if os.path.exists(out):
        os.remove(out)
    url = "file:///" + html_path.replace("\\", "/")
    subprocess.run([CHROME, "--headless", "--disable-gpu", "--no-sandbox",
                    "--no-pdf-header-footer", "--print-to-pdf=" + out, url],
                   capture_output=True, timeout=180)
    if not os.path.exists(out):
        raise RuntimeError("PDF build failed: " + name)
    return out


def verify(pdf_path):
    """페이지 수 · 폰트 임베딩 · 텍스트 추출 · 빈 페이지 검사."""
    import fitz
    d = fitz.open(pdf_path)
    fonts, empty, chars = set(), [], 0
    for i in range(d.page_count):
        pg = d.load_page(i)
        for f in pg.get_fonts():
            fonts.add(f[3].split("+")[-1])
        t = pg.get_text().strip()
        chars += len(t)
        if len(t) < 25 and not pg.get_images():
            empty.append(i + 1)
    ok_font = any("Malgun" in f or "Nanum" in f for f in fonts)
    return {"file": os.path.basename(pdf_path), "pages": d.page_count,
            "chars": chars, "fonts": sorted(fonts),
            "korean_font_embedded": ok_font, "empty_pages": empty}


def merge():
    import fitz
    order = sorted(glob.glob(os.path.join(PDFDIR, "ch*.pdf")))
    front = os.path.join(PDFDIR, "_front.pdf")
    parts = ([front] if os.path.exists(front) else []) + order

    doc, marks, page_at = fitz.open(), [], 0
    for p in parts:
        src = fitz.open(p)
        key = os.path.splitext(os.path.basename(p))[0]
        marks.append([1, TITLES.get(key, key), page_at + 1])
        doc.insert_pdf(src)
        page_at += src.page_count
        src.close()
    doc.set_toc(marks)

    # 페이지 번호 (표지 · 각 챕터 첫 장 제외)
    covers = {m[2] for m in marks} | {1}
    fpath = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts", "malgun.ttf")
    for i in range(doc.page_count):
        if (i + 1) in covers:
            continue
        pg = doc.load_page(i)
        r = pg.rect
        pg.insert_text((r.width / 2 - 12, r.height - 26), str(i + 1),
                       fontsize=8.5, fontfile=fpath, fontname="MG",
                       color=(0.45, 0.45, 0.45))

    out = os.path.join(PDFDIR, CFG["output"])
    doc.save(out, garbage=4, deflate=True)
    doc.close()
    return out


def deploy():
    """정식 파일명으로 배포. 챕터 파일명은 book.json의 chapter_files 기준."""
    dst = CFG["deploy"]
    ch = os.path.join(dst, "챕터별PDF")
    os.makedirs(ch, exist_ok=True)
    log = []
    shutil.copy2(os.path.join(PDFDIR, CFG["output"]), os.path.join(dst, CFG["output"]))
    log.append(CFG["output"])
    for key, name in CFG.get("chapter_files", {}).items():
        src = os.path.join(PDFDIR, key + ".pdf")
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(ch, name))
            log.append("챕터별PDF/" + name)
    # 배포 폴더에 남은 임시 파일(ch01.pdf 등) 정리
    for f in os.listdir(ch):
        if f.startswith("ch") and f.endswith(".pdf") and len(f) <= 9:
            os.remove(os.path.join(ch, f))
        if f == "_front.pdf":
            os.remove(os.path.join(ch, f))
    return dst, log


def render_page(n):
    """합본의 n페이지를 PNG로 저장. 도표 겹침 등 시각 검증용."""
    import fitz
    d = fitz.open(os.path.join(PDFDIR, CFG["output"]))
    out = os.path.join(PDFDIR, "_page%d.png" % n)
    d[n - 1].get_pixmap(dpi=105).save(out)
    return out


def find_page(keyword):
    """합본에서 키워드가 처음 나오는 페이지 번호."""
    import fitz
    d = fitz.open(os.path.join(PDFDIR, CFG["output"]))
    for i, pg in enumerate(d):
        if keyword in pg.get_text():
            return i + 1
    return None



# ---------------------------------------------------------------- 자동 검사

def CLS(name):
    """class 속성 안에 해당 토큰이 있는 태그를 찾는 정규식.

    class="exam" 을 문자열로 찾으면 class="exam pagebreak" 를 놓친다.
    브랜드설계자 1장에서 실제로 '시험문제 없음'이 뗴다.
    """
    return r'class="[^"]*(?<![-\w])' + name + r'(?![-\w])[^"]*"'


def _chapters():
    return sorted(glob.glob(os.path.join(BOOK, "ch*.html")))


def stats():
    """챕터별 실제 개수를 세어 표지 .meta 문구와 대조한다.

    표지 수치를 눈대중으로 적으면 거의 매번 틀린다.
    도표를 하나 추가·삭제할 때마다 다시 어긋나므로 사람이 셀 일이 아니다.
    """
    import re
    rows, warn = [], []
    tot = dict(fig=0, comic=0, case=0, q=0, tbl=0)
    for f in _chapters():
        h = io.open(f, encoding="utf-8").read()
        comic = len(re.findall(r"4컷 만화로 재구성", h))
        n = dict(
            fig=len(re.findall(r"<figure", h)) - comic,   # 만화는 도표에서 뺀다
            comic=comic,
            case=len(re.findall(r'class="kr-case"', h)),
            q=len(re.findall(r'class="q"', h)),
            tbl=len(re.findall(r"<table", h)),
        )
        for k in tot:
            tot[k] += n[k]

        m = re.search(r'class="meta">(.*?)</div>', h, re.S)
        meta = re.sub(r"\s+", " ", m.group(1)).strip() if m else "(없음)"
        want = "도표 %d · 만화 4컷 %d편 · 예시 %d · 시험문제 %d" % (
            n["fig"], n["comic"], n["case"], n["q"])
        ok = (meta == want)
        if not ok:
            warn.append((os.path.basename(f), meta, want))
        rows.append("%s%-11s 도표 %2d · 만화 %d · 예시 %d · 문항 %2d · 표 %2d"
                    % ("   " if ok else "!! ", os.path.basename(f),
                       n["fig"], n["comic"], n["case"], n["q"], n["tbl"]))

    out = ["챕터별 실제 개수 (표지 .meta 문구와 대조)", "=" * 62] + rows
    out.append("=" * 62)
    out.append("   합계        도표 %d · 만화 %d · 예시 %d · 문항 %d · 표 %d"
               % (tot["fig"], tot["comic"], tot["case"], tot["q"], tot["tbl"]))
    if warn:
        out.append("")
        out.append("!! 표지 문구가 실제와 다르다 — 고쳐야 한다")
        for name, meta, want in warn:
            out.append("   %s" % name)
            out.append("     현재: %s" % meta)
            out.append("     실제: %s" % want)
    else:
        out.append("")
        out.append("   표지 문구 전부 일치")
    return "\n".join(out), len(warn)


PAD = 4.0        # 상자 안쪽 여백. 글자가 테두리에 닿으면 이미 보기 나쁘다


try:                       # py3
    from html import unescape as _unescape
except ImportError:        # py2
    from HTMLParser import HTMLParser as _HP
    _unescape = _HP().unescape


def _text_width(s, size, bold=False):
    """한글은 정폭에 가깝고 ASCII는 절반쯤이다. 실측 기반 근사.

    굵은 글씨는 같은 크기라도 넓다. 이 계수를 빼먹었더니
    2장 만화의 실제 넘침(98.1 vs 상자 98)을 '간신히 들어감'으로 판정했다.
    """
    w = 0.0
    for ch in s:
        o = ord(ch)
        if o < 128:
            w += 0.52 if ch not in "iljI.,'\"()[] " else 0.30
        elif 0x3131 <= o <= 0xD7A3:      # 한글
            w += 1.02
        else:
            w += 0.95
    return w * size * (1.05 if bold else 1.0)


def tags():
    """짝 없는 태그 검사.

    `<div class="warn">...</p></div>` 처럼 **열린 적 없는 닫는 태그**가 섞이면
    브라우저는 조용히 무시하고 렌더링한다. 눈으로는 절대 안 잡힌다.
    실제로 두 권 연속 같은 자리(.warn / .note)에서 났다.

    **검사한 태그 수를 함께 찍는다.** 0건 통과는 통과가 아니다(함정 #28).
    """
    import re
    TAG = re.compile(r'<\s*(/?)(div|p|figure|table|tr|td|ol|ul|li|svg)\b[^>]*?(/?)\s*>',
                     re.I)
    out, bad, scanned = [], [], 0
    for f in _chapters() + [os.path.join(BOOK, "_front.html")]:
        if not os.path.exists(f):
            continue
        h = io.open(f, encoding="utf-8").read()
        stack, errs = [], []
        for m in TAG.finditer(h):
            closing, name, selfclose = m.group(1), m.group(2).lower(), m.group(3)
            if selfclose:
                continue
            scanned += 1
            line = h.count("\n", 0, m.start()) + 1
            if not closing:
                stack.append((name, line))
            else:
                if not stack:
                    errs.append(u"%d행: </%s> 가 열린 적 없다" % (line, name))
                elif stack[-1][0] != name:
                    errs.append(u"%d행: </%s> 인데 열려 있는 것은 <%s> (%d행)"
                                % (line, name, stack[-1][0], stack[-1][1]))
                    stack.pop()
                else:
                    stack.pop()
        for name, line in stack:
            errs.append(u"%d행: <%s> 가 닫히지 않았다" % (line, name))
        base = os.path.basename(f)
        if errs:
            bad.append(base)
            out.append(u"!! %-12s %d건" % (base, len(errs)))
            for e in errs[:6]:
                out.append(u"      " + e)
        else:
            out.append(u"   %-12s 이상 없음" % base)

    head = [u"짝 없는 태그 검사", u"=" * 62,
            u"태그 %d개 검사" % scanned, u""]
    if scanned == 0:
        return u"\n".join(head + [u"!! 검사한 태그가 0개다. '이상 없음'이 아니라 검사기 고장이다."]), 1
    tail = [u"", u"   전부 짝이 맞는다"] if not bad else [u"", u"!! 고쳐야 한다: " + ", ".join(bad)]
    return u"\n".join(head + out + tail), len(bad)


def comicfit():
    """만화 칸의 **세로** 넘침 검사. svgfit 은 가로만 본다(함정 #25).

    칸 테두리는 y=16 에서 시작해 높이 220 → **아래 테두리가 y=236**.
    칸 안 글자는 y<=230, 칸 밖 꼬리말은 y=256 이다.
    그 사이(231~250)에 글자가 있으면 테두리를 뚫는다.

    **빈손으로 통과시키지 않는다.** 검사한 글자가 0개면 그건 '이상 없음'이 아니라
    검사기가 고장 난 것이다. 정규식이 하나도 안 맞아 0건을 '이상 없음'으로
    출력하는 바람에 실제 넘침 2건을 놓칠 뻔했다(함정 #28).
    """
    import re
    TEXT = re.compile(r'<text[^>]*\by="([0-9.]+)"[^>]*>([^<]*)<')
    SVGB = re.compile(r'<svg[^>]*>(.*?)</svg>', re.S)
    bad, comics, scanned = [], 0, 0
    for f in sorted(glob.glob(os.path.join(BOOK, "ch*.html"))):
        h = io.open(f, encoding="utf-8").read()
        for body in SVGB.findall(h):
            if "4컷 만화로 재구성" not in body:
                continue
            comics += 1
            ttl = re.search("4컷 만화로 재구성 — ([^<]*)", body)
            for m in TEXT.finditer(body):
                scanned += 1
                y = float(m.group(1))
                if 231 <= y <= 250:
                    bad.append("  %s  y=%.0f  \"%s\"   [%s]"
                               % (os.path.basename(f), y, m.group(2)[:24],
                                  ttl.group(1)[:22] if ttl else ""))
    out = ["만화 칸 세로 넘침 검사 (아래 테두리 y=236)", "=" * 56,
           "만화 %d편 / 글자 %d개 검사" % (comics, scanned), ""]
    if comics == 0 or scanned == 0:
        out.append("!! 검사한 것이 없다. '이상 없음'이 아니라 검사기 고장이다.")
        return "\n".join(out), 1
    if bad:
        out.append("!! 테두리를 뚫는 글자 %d건" % len(bad))
        out.extend(bad)
        out.append("")
        out.append("  y 를 230 이하로 내리거나 위 요소를 끌어올린다.")
        return "\n".join(out), len(bad)
    out.append("전부 칸 안에 들어간다")
    return "\n".join(out), 0


def svgfit():
    """SVG <text>가 자기를 담은 <rect> 밖으로 넘치는지 검사한다.

    말풍선·라벨 상자가 글자보다 좁으면 글자가 상자를 뚫고 나온다.
    렌더해서 눈으로 봐야만 보이던 종류인데, 폭을 근사해서 미리 잡을 수 있다.
    실측 — 2장 만화 3컷의 '아뇨, 그리스 사람이에요'가 이 방식으로 재현됐다.
    """
    import re
    SVG = re.compile(r"<svg\b.*?</svg>", re.S)
    RECT = re.compile(r'<rect\b([^>]*)/?>', re.S)
    TEXT = re.compile(r'<text\b([^>]*)>(.*?)</text>', re.S)
    ATTR = re.compile(r'([a-zA-Z-]+)\s*=\s*"([^"]*)"')

    def at(s):
        return dict(ATTR.findall(s))

    def num(d, k, dv=0.0):
        try:
            return float(d.get(k, dv))
        except ValueError:
            return dv

    HARD = 2.0       # 이 이상 넘치면 실패. 그 미만은 근사 오차일 수 있어 알리기만 한다
    # <g> 에서 물려받는 속성. text-anchor 를 빼면 가운데정렬 글자를
    # 왼쪽정렬로 계산해 폭의 절반만큼 오른쪽으로 밀리고, 오탐이 쌓인다.
    INHERIT = ("font-size", "font-weight", "text-anchor")
    rows, hits, tight = [], [], []
    for f in _chapters():
        h = io.open(f, encoding="utf-8").read()
        n_over = 0
        for si, svg in enumerate(SVG.findall(h), 1):
            rects = []
            for m in RECT.finditer(svg):
                d = at(m.group(1))
                if "x" not in d or "width" not in d:
                    continue
                rects.append((num(d, "x"), num(d, "y"),
                              num(d, "width"), num(d, "height")))
            # <g>에 걸린 font-size / font-weight 를 상속해야 한다.
            # 처음엔 이걸 빼먹어서 8.2pt 글자를 12pt로 계산했고,
            # 8장에서 오탐 4건이 났다.
            # 주의 - 이 정규식을 힙독으로 써넣었다가 워드경계가
            # 백스페이스로 바뀌어 아무것도 매칭되지 않은 적이 있다.
            # 그때 검사기는 조용히 '전부 이상 없음'을 냈다.
            GTOK = re.compile(r"<g\b([^>]*)>|</g>|<text\b([^>]*)>(.*?)</text>", re.S)
            stack = []
            for m in GTOK.finditer(svg):
                whole = m.group(0)
                if whole.startswith("</g"):
                    if stack:
                        stack.pop()
                    continue
                if whole.startswith("<g"):
                    g = at(m.group(1) or "")
                    inh = dict(stack[-1]) if stack else {}
                    for k in INHERIT:
                        if k in g:
                            inh[k] = g[k]
                    stack.append(inh)
                    continue

                d = at(m.group(2) or "")
                inh = stack[-1] if stack else {}
                for k in INHERIT:
                    if k not in d and k in inh:
                        d[k] = inh[k]

                raw = re.sub(r"<[^>]+>", "", m.group(3) or "")
                # HTML 엔티티를 풀지 않으면 &lsquo; 하나가 6글자로 계산된다.
                # 따옴표가 많은 대사 한 줄이 실제 폭의 두 배로 잡혀
                # 멀쩡한 도표가 '넘침'으로 올라온다. 실제로 겪었다.
                raw = _unescape(raw)
                s = re.sub(r"\s+", " ", raw).strip()
                if not s:
                    continue
                size = num(d, "font-size", 12)
                x, y = num(d, "x"), num(d, "y")
                bold = num(d, "font-weight", 400) >= 600
                w = _text_width(s, size, bold)
                anc = d.get("text-anchor", "start")
                x0 = x - w / 2 if anc == "middle" else (x - w if anc == "end" else x)
                x1 = x0 + w
                # 이 글자를 담고 있다고 볼 수 있는 가장 작은 사각형
                host = None
                for (rx, ry, rw, rh) in rects:
                    if rx <= x <= rx + rw and ry <= y <= ry + rh:
                        if host is None or rw < host[2]:
                            host = (rx, ry, rw, rh)
                if host is None:
                    continue
                rx, _ry, rw, _rh = host
                # 테두리에 딱 붙는 것도 넘침으로 본다 (안쪽 여백 PAD 확보)
                over = max((rx + PAD) - x0, x1 - (rx + rw - PAD))
                if over >= HARD:
                    n_over += 1
                    hits.append("     %-11s svg#%-2d %+5.1f pt  \"%s\""
                                % (os.path.basename(f), si, over, s[:32]))
                elif over > 0:
                    tight.append("     %-11s svg#%-2d %+5.1f pt  \"%s\""
                                 % (os.path.basename(f), si, over, s[:32]))
        rows.append("%s%-11s %s" % ("   " if not n_over else "!! ",
                                    os.path.basename(f),
                                    "이상 없음" if not n_over else "넘침 %d건" % n_over))
    out = ["SVG 글자 넘침 검사 (상자보다 글자가 넓은 곳)", "=" * 62] + rows
    if hits:
        out += ["", "!! 상자를 넘어간 글자 — 고쳐야 한다"] + hits
        out.append("")
        out.append("  글자를 줄이거나 rect의 width를 키운다.")
    if tight:
        out += ["", "(참고) 여백이 빠듯한 곳 — %.1fpt 미만이라 근사 오차일 수 있다" % HARD] + tight
    if not hits and not tight:
        out.append("")
        out.append("   전부 여유 있게 들어간다")
    out.append("=" * 62)
    return "\n".join(out), len(hits)


def linegap():
    """같은 SVG 안에서 <text> 두 줄이 세로로 포개지는지 검사한다.

    svgfit 은 **가로만** 본다. 줄 간격(baseline 차이)을 글자 크기보다 좁게 잡으면
    렌더에서 두 줄이 겹쳐 읽을 수 없게 되는데, 가로 검사로는 절대 안 잡힌다.
    실측 - 『설득의 심리학 1』 ch06 혁명 곡선에서 10.5pt 글자를 baseline 간격 10 으로
    두어 마지막 두 줄이 겹쳤다. **렌더 이미지를 눈으로 보고서야** 발견했다.
    """
    import re
    SVG = re.compile(r"<svg\b.*?</svg>", re.S)
    TEXT = re.compile(r'<text\b([^>]*)>(.*?)</text>', re.S)
    ATTR = re.compile(r'([a-zA-Z-]+)\s*=\s*"([^"]*)"')
    HARD = 1.02         # baseline 간격 / 글자 크기. 이보다 좁으면 실제로 겹친다
    SOFT = 1.20         # 이보다 좁으면 빡빡하다 — 알리기만 한다
    #  큰 숫자(20pt 이상)은 실제 글자 높이가 font-size 보다 훨씬 낮아
    #  1.12 로 잡으면 멀짬한 막대그래프 라벨이 전부 오탄으로 뜼었다.
    WIN = 46.0          # 이보다 멀면 볼 필요가 없다

    rows, bad, tight = [], [], []
    for f in _chapters():
        h = io.open(f, encoding="utf-8").read()
        hits = []
        for si, m in enumerate(SVG.finditer(h), 1):
            items = []
            for a, body in TEXT.findall(m.group(0)):
                d = dict(ATTR.findall(a))
                try:
                    x = float(d.get("x", 0)); y = float(d.get("y", 0))
                    fs = float(d.get("font-size", 12))
                except ValueError:
                    continue
                txt = _unescape(re.sub(r"<[^>]+>", "", body)).strip()
                if not txt:
                    continue
                w = _text_width(txt, fs, "800" in a)
                anc = d.get("text-anchor", "start")
                x0 = x - w / 2 if anc == "middle" else (x - w if anc == "end" else x)
                items.append((y, x0, x0 + w, fs, txt))
            items.sort()
            for i in range(len(items)):
                for j in range(i + 1, len(items)):
                    y1, a1, b1, f1, t1 = items[i]
                    y2, a2, b2, f2, t2 = items[j]
                    gap = y2 - y1
                    if gap > WIN:
                        break
                    base = max(f1, f2)
                    if gap >= base * SOFT:
                        continue
                    if b1 <= a2 or b2 <= a1:      # 가로로 안 겹치면 상관없다
                        continue
                    line = ("     svg#%-2d  간격 %.1f (글자 %.1f)   \"%s\" / \"%s\""
                            % (si, gap, base, t1[:20], t2[:20]))
                    (hits if gap < base * HARD else tight).append(line)
        rows.append("%s%-11s %s" % ("   " if not hits else "!! ", os.path.basename(f),
                                    "이상 없음" if not hits else "겹침 %d건" % len(hits)))
        bad += hits

    out = ["SVG 줄 간격 검사 (세로로 포개진 글자)", "=" * 62] + rows
    out.append("=" * 62)
    if bad:
        out += ["", "!! 두 줄이 겹친다 - y 를 벌리거나 글자를 줄여야 한다"] + bad
        out += ["", "  상자 안이라면 rect 의 height 와 viewBox 높이도 함께 키운다."]
    else:
        out += ["", "   전부 여유 있다"]
    return "\n".join(out), len(bad)


def blocks():
    """챕터마다 있어야 할 블록이 실제로 들어갔는지 검사한다.

    시험지·정답지는 눈에 띄어 빠뜨리기 어렵지만, 튜터 프롬프트는
    정답지 뒤에 붙는 작은 블록이라 한 챕터만 빠져도 모르고 넘어간다.
    """
    import re
    rows, miss = [], []
    for f in _chapters():
        h = io.open(f, encoding="utf-8").read()
        n = {
            "회상지면": len(re.findall(CLS("recall"), h)),
            "시험문제": len(re.findall(CLS("exam"), h)),
            "정답지": len(re.findall(CLS("answers"), h)),
            "합격선": len(re.findall(CLS("cut"), h)),
            "튜터": len(re.findall(CLS("tutor"), h)),
        }
        # 종합시험(ch99)은 '덮고 쓰기'가 없는 것이 정상이다.
        # 시험 자체가 인출인데 그 앞에 회상 지면을 또 두면 같은 일을 두 번 시킨다.
        # 예외는 두되 **조용히 빠지지 않게** 이름을 찍는다.
        final = os.path.basename(f).startswith("ch99")
        bad = [k for k, v in n.items() if v < 1 and not (final and k == "회상지면")]
        rows.append("%s%-11s 회상 %d · 시험 %d · 정답 %d · 합격선 %d · 튜터 %d%s"
                    % ("   " if not bad else "!! ", os.path.basename(f),
                       n["회상지면"], n["시험문제"], n["정답지"],
                       n["합격선"], n["튜터"],
                       "" if not bad else "   <- 빠짐: " + ", ".join(bad)))
        if bad:
            miss.append((os.path.basename(f), bad))

    out = ["챕터별 필수 블록 검사", "=" * 62] + rows + ["=" * 62]
    if miss:
        out.append("")
        out.append("!! 빠진 블록이 있다 — 채워야 한다")
        for name, b in miss:
            out.append("   %s -> %s" % (name, ", ".join(b)))
    else:
        out.append("   전부 있음")
    return "\n".join(out), len(miss)


def headings():
    """<h3>N. 번호가 연속인지 검사한다.

    절을 중간에 끼워 넣으면 뒤 번호가 밀리는데 눈으로는 잘 안 보인다.
    """
    import re
    out, bad = ["절 번호 연속성 검사", "=" * 62], 0
    for f in _chapters():
        h = io.open(f, encoding="utf-8").read()
        # <h2>가 나오면 번호가 1부터 다시 시작한다 (원서의 장이 바뀌는 지점)
        # h3는 두 표기를 모두 허용한다:
        #   "1."  단독      -> h2 안에서 1, 2, 3 …
        #   "2.1" 부모붙임  -> 앞자리가 부모 h2 번호와 같아야 하고 뒷자리가 1, 2, 3 …
        seq, expect, h2no = [], 1, None
        for m in re.finditer(r"<(h2|h3)\b[^>]*>(.*?)</\1>", h, re.S):
            title = re.sub(r"<[^>]+>", "", m.group(2)).strip()
            if m.group(1) == "h2":
                expect = 1
                p = re.match(r"(\d+)\.", title)
                h2no = int(p.group(1)) if p else None
                continue
            n = re.match(r"(\d+)\.(\d+)?", title)
            if not n:
                continue
            if n.group(2) is not None:
                parent, got = int(n.group(1)), int(n.group(2))
                if h2no is not None and parent != h2no:
                    seq.append("     부모 절이 %d인데 %d.%d 로 적혀 있다 — %s"
                               % (h2no, parent, got, title[:38]))
                    bad += 1
            else:
                got = int(n.group(1))
            if got != expect:
                seq.append("     %d 이어야 하는데 %d — %s" % (expect, got, title[:44]))
                bad += 1
                expect = got
            expect += 1
        out.append("%s%-11s %s" % ("   " if not seq else "!! ",
                                   os.path.basename(f),
                                   "연속" if not seq else "어긋남 %d곳" % len(seq)))
        out += seq
    out.append("=" * 62)
    out.append("   어긋난 곳 %d" % bad)
    return "\n".join(out), bad


def render_figures():
    """도표가 있는 페이지를 전부 PNG로 렌더하고, 복잡한 순으로 줄을 세운다.

    겹침은 샘플링으로 못 잡는다. 실제로 82쪽 중 6쪽만 봤을 때
    그 6쪽에서만 4건이 나왔고, 도표가 있는 쪽은 사실 63쪽이었다.

    다만 63쪽을 전부 눈으로 보는 것도 비현실적이라
    **요소가 많은 순**으로 정렬해 우선순위를 준다.
    만화가 있는 쪽은 무조건 맨 앞이다 — 겹침 4건 중 2건이 만화였다.
    """
    import fitz
    src = os.path.join(PDFDIR, CFG["output"])
    srcs = [src] if os.path.exists(src) else sorted(glob.glob(os.path.join(PDFDIR, "ch*.pdf")))

    items = []
    for s in srcs:
        d = fitz.open(s)
        tag = os.path.splitext(os.path.basename(s))[0][:12]
        for i in range(d.page_count):
            pg = d.load_page(i)
            n = len(pg.get_drawings())
            txt = pg.get_text()
            # 요소 수만으로 가르면 글자 위주 도표를 놓친다.
            # 곡선 하나에 라벨이 잔뜿 붙은 도표는 요소가 9개뿐이었고,
            # 라벨 충돌은 정확히 그런 도표에서 난다.
            if n < 12 and "재작도" not in txt:
                continue
            # <title>4컷 만화로 재구성</title>은 SVG 메타데이터라
            # 렌더된 PDF의 텍스트에 절대 나오지 않는다. 눈에 보이는
            # 캡션 문구로도 찾아야 한다 — 안 그러면 "만화 0장"이 뜬다.
            comic = ("만화로 재구성" in txt) or ("4컷으로 옮겨 그림" in txt)
            out = os.path.join(PDFDIR, "_fig_%s_p%02d.png" % (tag, i + 1))
            pg.get_pixmap(dpi=105).save(out)
            items.append((comic, n, i + 1, out))
        d.close()

    items.sort(key=lambda x: (not x[0], -x[1]))
    lines = ["도표 페이지 렌더 — 위에서부터 확인한다 (만화 먼저, 그다음 요소 많은 순)",
             "=" * 70]
    for comic, n, pno, out in items:
        lines.append("%s p%-4d 요소 %4d   %s" % ("[만화] " if comic else "       ", pno, n, out))
    lines.append("=" * 70)
    lines.append("총 %d장 (만화 %d장)" % (len(items), sum(1 for x in items if x[0])))
    lines.append("")
    lines.append("최소 기준 — 만화는 100%, 나머지는 요소 많은 순으로 상위 10장 이상을 Read로 확인한다.")
    return [x[3] for x in items], "\n".join(lines)

def svgbox():
    """SVG 콘텐츠가 viewBox 높이를 넘는지 검사한다 (함정 #60).

    svgfit 은 **가로**만, linegap 은 **줄 간격**만, comicfit 은 **만화 칸**만 본다.
    세로로 viewBox 를 넘어가는 것은 아무도 보지 않는다.
    1px만 넘어도 표의 마지막 행이 통째로 잘려 나간다 —
    『장문정의 마케털이』에서 한 권에 3건(300/301, 196/204, 244/247) 나왔다.
    """
    import re
    rows, bad = [], []
    for f in _chapters() + [os.path.join(BOOK, "_front.html")]:
        if not os.path.exists(f):
            continue
        t = io.open(f, encoding="utf-8").read()
        hits = []
        for i, m in enumerate(re.finditer(
                r'<svg viewBox="0 0 (\d+) (\d+)"(.*?)</svg>', t, re.S), 1):
            H, body = int(m.group(2)), m.group(3)
            mx = 0.0
            for r in re.finditer(
                    r'<rect[^>]*y="([0-9.]+)"[^>]*height="([0-9.]+)"', body):
                mx = max(mx, float(r.group(1)) + float(r.group(2)))
            for r in re.finditer(r'<text[^>]*\sy="([0-9.]+)"', body):
                mx = max(mx, float(r.group(1)) + 2)   # baseline 아래 여유
            if mx > H:
                hits.append((i, H, mx))
        name = os.path.basename(f)
        if hits:
            bad += [(name, i, H, mx) for i, H, mx in hits]
            rows.append("!! %-11s viewBox 넘침 %d건" % (name, len(hits)))
        else:
            rows.append("   %-11s 이상 없음" % name)

    out = ["SVG viewBox 세로 넘침 검사 (표 마지막 행이 잘린다)", "=" * 56] + rows
    out.append("=" * 56)
    if bad:
        out += ["", "!! viewBox 높이를 늘려야 한다"]
        out += ["     %-11s svg#%-3d viewBox H=%d  콘텐츠 바닥=%.0f  (+%.0f)"
                % (n, i, H, mx, mx - H) for n, i, H, mx in bad]
    else:
        out += ["", "   전부 viewBox 안에 들어간다"]
    return chr(10).join(out), len(bad)


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "all"
    results = []

    if arg == "merge":
        results.append(verify(merge()))
    elif arg == "deploy":
        dst, log = deploy()
        lines = ["deploy -> " + dst] + ["  " + x for x in log]
        io.open(os.path.join(BOOK, "_deploy.txt"), "w", encoding="utf-8").write("\n".join(lines))
        print("[OK] deployed -> read _deploy.txt with cat")
        sys.exit(0)
    elif arg == "stats":
        txt, n = stats()
        io.open(os.path.join(BOOK, "_stats.txt"), "w", encoding="utf-8").write(txt)
        print("[%s] stats -> read _stats.txt with cat" % ("OK" if n == 0 else "!!"))
        sys.exit(1 if n else 0)
    elif arg == "svgbox":
        txt, n = svgbox()
        io.open(os.path.join(BOOK, "_svgbox.txt"), "w", encoding="utf-8").write(txt)
        print("[%s] svgbox -> read _svgbox.txt with cat" % ("OK" if n == 0 else "!!"))
        sys.exit(1 if n else 0)
    elif arg == "svgfit":
        txt, n = svgfit()
        io.open(os.path.join(BOOK, "_svgfit.txt"), "w", encoding="utf-8").write(txt)
        print("[%s] svgfit -> read _svgfit.txt with cat" % ("OK" if n == 0 else "!!"))
        sys.exit(1 if n else 0)
    elif arg == "tags":
        txt, n = tags()
        io.open(os.path.join(BOOK, "_tags.txt"), "w", encoding="utf-8").write(txt)
        print("[%s] tags -> read _tags.txt with cat" % ("OK" if n == 0 else "!!"))
        sys.exit(1 if n else 0)
    elif arg == "linegap":
        txt, n = linegap()
        io.open(os.path.join(BOOK, "_linegap.txt"), "w", encoding="utf-8").write(txt)
        print("[%s] linegap -> read _linegap.txt with cat" % ("OK" if n == 0 else "!!"))
        sys.exit(1 if n else 0)
    elif arg == "comicfit":
        txt, n = comicfit()
        io.open(os.path.join(BOOK, "_comicfit.txt"), "w", encoding="utf-8").write(txt)
        print("[%s] comicfit -> read _comicfit.txt with cat" % ("OK" if n == 0 else "!!"))
        sys.exit(1 if n else 0)
    elif arg == "blocks":
        txt, n = blocks()
        io.open(os.path.join(BOOK, "_blocks.txt"), "w", encoding="utf-8").write(txt)
        print("[%s] blocks -> read _blocks.txt with cat" % ("OK" if n == 0 else "!!"))
        sys.exit(1 if n else 0)
    elif arg == "headings":
        txt, n = headings()
        io.open(os.path.join(BOOK, "_headings.txt"), "w", encoding="utf-8").write(txt)
        print("[%s] headings -> read _headings.txt with cat" % ("OK" if n == 0 else "!!"))
        sys.exit(1 if n else 0)
    elif arg == "render":
        made, report = render_figures()
        io.open(os.path.join(BOOK, "_render.txt"), "w", encoding="utf-8").write(report)
        print("[OK] rendered %d pages -> read _render.txt (sorted by priority)" % len(made))
        sys.exit(0)
    elif arg == "page":
        print(render_page(int(sys.argv[2])))
        sys.exit(0)
    elif arg == "find":
        print(find_page(sys.argv[2]))
        sys.exit(0)
    else:
        if arg == "all":
            targets = sorted(glob.glob(os.path.join(BOOK, "ch*.html")))
            fr = os.path.join(BOOK, "_front.html")
            if os.path.exists(fr):
                targets.append(fr)
        else:
            targets = [os.path.join(BOOK, arg + ".html")]
        for h in targets:
            results.append(verify(to_pdf(h)))

    io.open(os.path.join(BOOK, "_verify.json"), "w", encoding="utf-8").write(
        json.dumps(results, ensure_ascii=False, indent=2))
    # 콘솔 cp949 깨짐 방지 — 결과는 파일로도 남긴다
    lines = ["%-44s %3d p | %6d자 | 한글폰트 %s | 빈페이지 %s"
             % (r["file"], r["pages"], r["chars"],
                "OK" if r["korean_font_embedded"] else "실패",
                r["empty_pages"] or "없음") for r in results]
    io.open(os.path.join(BOOK, "_verify.txt"), "w", encoding="utf-8").write("\n".join(lines))
    print("[OK] built -> read _verify.txt with cat (console is cp949, Korean will look broken)")
