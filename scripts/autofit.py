# -*- coding: utf-8 -*-
"""svgfit / linegap 지적사항을 글자 크기만 줄여서 자동으로 해소한다.

  왜 필요한가 — 도표 하나에 지적이 대여섯 개씩 나오는데, 그때마다
  긴 문자열을 손으로 찾아 바꾸면 따옴표·엔대시 한 글자 차이로 계속 빗나간다
  (실제로 &mdash; 와 — 가 섞여 세 번 연속 실패했다).
  이 스크립트는 **좌표를 열쇠로** 쓰기 때문에 본문 표기와 무관하게 맞는다.

  글자만 줄인다 — rect 나 y 는 건드리지 않으므로 레이아웃이 틀어지지 않는다.
  (rect 바닥에 붙은 글자는 fixbottom.py 가 따로 맡는다.)

사용:
    python build.py svgfit ; python build.py linegap
    python autofit.py .          # 지적된 곳의 font-size 를 줄인다
    python build.py svgfit ; python build.py linegap   # 다시 확인

한 번에 다 못 잡으면 (줄여도 여전히 넘치면) 두세 번 돌린다.
그래도 남으면 글자 자체가 너무 길다는 뜻이니 그때 손으로 문장을 줄인다.
"""
import io, os, re, sys, glob
try:
    from html import unescape
except ImportError:
    from HTMLParser import HTMLParser
    unescape = HTMLParser().unescape

MIN_FS = 7.0          # 이보다 작아지면 인쇄해서 읽기 힘들다

def text_width(s, size, bold=False):
    """build.py 의 _text_width 와 같은 모델. 한글은 정폭에 가깝다(1.02)."""
    w = 0.0
    for ch in s:
        o = ord(ch)
        if o < 128:
            w += 0.52 if ch not in "iljI.,'\"()[] " else 0.30
        elif 0x3131 <= o <= 0xD7A3:
            w += 1.02
        else:
            w += 0.95
    return w * size * (1.05 if bold else 1.0)
SVG = re.compile(r'<svg[^>]*>.*?</svg>', re.S)
TEXT = re.compile(r'<text([^>]*)>')

def fs_of(attrs):
    m = re.search(r'\sfont-size="([\d.]+)"', attrs)
    return float(m.group(1)) if m else 10.0

def y_of(attrs):
    m = re.search(r'\sy="([\d.]+)"', attrs)
    return float(m.group(1)) if m else None

def set_fs(attrs, v):
    v = "%g" % round(v, 1)
    if re.search(r'\sfont-size="', attrs):
        return re.sub(r'(\sfont-size=")[\d.]+(")', lambda m: m.group(1)+v+m.group(2), attrs, count=1)
    return attrs + ' font-size="%s"' % v

def parse_svgfit(path):
    """{(파일, svg번호): [(넘침pt, 글자앞부분), ...]}"""
    out = {}
    if not os.path.exists(path): return out
    for ln in io.open(path, encoding="utf-8"):
        m = re.match(r'\s+(\S+\.html)\s+svg#(\d+)\s+\+([\d.]+) pt\s+"(.*)"\s*$', ln)
        if m and "여백이 빠듯" not in ln:
            out.setdefault((m.group(1), int(m.group(2))), []).append((float(m.group(3)), m.group(4)))
    return out

def parse_linegap(path):
    """{파일: [(svg번호, 간격, 글자크기), ...]}  — 파일명은 헤더에서 따온다"""
    out, cur = {}, None
    if not os.path.exists(path): return out
    for ln in io.open(path, encoding="utf-8"):
        h = re.match(r'!!\s+(\S+\.html)\s+겹침', ln)
        if h: cur = h.group(1); continue
        m = re.match(r'\s+svg#(\d+)\s+간격\s+([\d.]+)\s+\(글자\s+([\d.]+)\)', ln)
        if m and cur:
            out.setdefault(cur, []).append((int(m.group(1)), float(m.group(2)), float(m.group(3))))
    return out

def strip_tags(s):
    return re.sub(r'<[^>]+>', '', s)

# 함정 #42 — 지적 보고서에는 &mdash; 가 — 로 찍혀 나오는데
# HTML 원문에는 &mdash; 로 들어 있다. 그대로 비교하면 앞 12글자가 어긋나
# 자동 수정이 통째로 빗나간다. 양쪽을 다 풀어서(unescape) 문장부호를 지우고 맞춘다.
def norm(s):
    s = unescape(strip_tags(s))
    return re.sub(r"[\s‘’“”–—'\"·.,!?()\[\]{}<>:;…\-]+", "", s)

def run(book):
    fit = parse_svgfit(os.path.join(book, "_svgfit.txt"))
    gap = parse_linegap(os.path.join(book, "_linegap.txt"))
    report, total = [], 0

    files = sorted(set([f for f, _ in fit] + list(gap)))
    for fname in files:
        path = os.path.join(book, fname)
        if not os.path.exists(path): continue
        html = io.open(path, encoding="utf-8").read()
        blocks = list(SVG.finditer(html))
        newhtml, last, changed = [], 0, 0

        for si, m in enumerate(blocks, 1):
            blk = m.group(0)
            hits = fit.get((fname, si), [])
            gaps = [g for g in gap.get(fname, []) if g[0] == si]
            if not hits and not gaps:
                continue

            def fix_text(tm, _blk=blk):
                nonlocal changed
                attrs = tm.group(1)
                # 이 <text> 의 실제 글자
                tail = _blk[tm.end():]
                body = strip_tags(tail.split("</text>", 1)[0]).strip()
                fs = fs_of(attrs)
                bold = float(re.search(r'font-weight="(\d+)"', attrs).group(1)) >= 600                        if re.search(r'font-weight="(\d+)"', attrs) else False
                new = fs
                nbody = norm(body)
                for over, frag in hits:
                    key = norm(frag)
                    if key and nbody and (key[:10] in nbody or nbody[:10] in key):
                        # 함정 #45 — 폭 모델을 build.py 와 똑같이 써야 한다.
                        # 예전엔 len*fs*0.55 로 근사했는데, 한글은 실제로 1.02 다.
                        # 그래서 줄여야 할 양의 절반만 줄이고 '고쳤다'고 보고했다.
                        width = max(text_width(unescape(body), fs, bold), 1.0)
                        new = min(new, fs * width / (width + over) * 0.97)
                for _, g, gfs in gaps:
                    if abs(gfs - fs) < 0.01:
                        new = min(new, g / 1.28)
                new = max(new, MIN_FS)
                if new < fs - 0.05:
                    changed += 1
                    return "<text" + set_fs(attrs, new) + ">"
                return tm.group(0)

            fixed = TEXT.sub(fix_text, blk)
            newhtml.append(html[last:m.start()]); newhtml.append(fixed); last = m.end()

        if changed:
            newhtml.append(html[last:])
            io.open(path, "w", encoding="utf-8").write("".join(newhtml))
            report.append("  %-12s  글자 %d개 축소" % (fname, changed))
            total += changed

    io.open(os.path.join(book, "_autofit.txt"), "w", encoding="utf-8").write(
        "\n".join(["글자 크기 자동 축소 (svgfit / linegap 지적분)", "=" * 50] + report
                  + ["=" * 50, "총 %d개" % total,
                     "", "다시 확인: python build.py svgfit ; python build.py linegap"]))
    print(total)

if __name__ == "__main__":
    run(sys.argv[1] if len(sys.argv) > 1 else ".")
