# -*- coding: utf-8 -*-
"""원본 크롭(C·D 유형)을 지면에 넣을 때만 필요한 검사기 4종.

기존 8종(stats·blocks·headings·svgfit·svgbox·linegap·comicfit·tags)에 더한다.

    python imgcheck.py imgfit     모든 <img>가 <figure> 안 + <figcaption> 있는가
    python imgcheck.py imgres     삽입 크롭이 가로 900px 이상인가
    python imgcheck.py imgcite    크롭마다 '원본 N권 M쪽' 출처가 있는가
    python imgcheck.py size       합본/권별 PDF가 용량 한도 이내인가
    python imgcheck.py all        넷 다

결과는 _img*.txt 로 쓴다 (콘솔이 cp949라 한글을 직접 찍지 않는다).
"""
import io, os, re, sys, glob

MINW = 900              # imgres 최소 가로 픽셀
MAX_CH_MB = 40.0        # 권별 PDF 상한
MAX_ALL_MB = 400.0      # 합본 상한

FIG = re.compile(r"<figure\b.*?</figure>", re.S)
IMG = re.compile(r"<img\b[^>]*>")
SRC = re.compile(r'src\s*=\s*"([^"]+)"')
CAP = re.compile(r"<figcaption\b.*?</figcaption>", re.S)
CITE = re.compile(r"원본\s*\d+\s*권\s*\d+\s*쪽")


def htmls():
    return sorted(glob.glob("ch*.html")) + sorted(glob.glob("_front.html"))


def imgfit():
    out, bad = [], 0
    for f in htmls():
        h = io.open(f, encoding="utf-8").read()
        total = len(IMG.findall(h))
        inside = 0
        nocap = []
        for fig in FIG.findall(h):
            ims = IMG.findall(fig)
            inside += len(ims)
            if ims and not CAP.search(fig):
                nocap.append(SRC.search(ims[0]).group(1) if SRC.search(ims[0]) else "?")
        loose = total - inside
        if loose or nocap:
            bad += 1
            out.append("!! %-12s img %d개 중 figure 밖 %d개 · 캡션없음 %d개"
                       % (f, total, loose, len(nocap)))
            for c in nocap:
                out.append("     캡션 없는 도판: %s" % c)
        else:
            out.append("   %-12s 이상 없음 (img %d개)" % (f, total))
    out.insert(0, "[imgfit] 모든 도판이 figure 안 + 캡션 보유 — 문제 %d개 파일\n" % bad)
    io.open("_imgfit.txt", "w", encoding="utf-8").write("\n".join(out))
    return bad


def imgres():
    try:
        from PIL import Image
    except ImportError:
        io.open("_imgres.txt", "w", encoding="utf-8").write("Pillow 없음 — 건너뜀")
        return 0
    out, bad = [], 0
    seen = set()
    for f in htmls():
        h = io.open(f, encoding="utf-8").read()
        for im in IMG.findall(h):
            m = SRC.search(im)
            if not m:
                continue
            p = m.group(1)
            if p in seen:
                continue
            seen.add(p)
            if not os.path.exists(p):
                out.append("!! %-12s 파일 없음: %s" % (f, p))
                bad += 1
                continue
            w, hh = Image.open(p).size
            if w < MINW:
                out.append("!! %-12s %s  %dx%d  (가로 %d 미만)" % (f, p, w, hh, MINW))
                bad += 1
            else:
                out.append("   %-12s %s  %dx%d" % (f, p, w, hh))
    out.insert(0, "[imgres] 삽입 크롭 가로 %dpx 이상 — 미달 %d개\n" % (MINW, bad))
    io.open("_imgres.txt", "w", encoding="utf-8").write("\n".join(out))
    return bad


def imgcite():
    out, bad = [], 0
    for f in htmls():
        h = io.open(f, encoding="utf-8").read()
        for fig in FIG.findall(h):
            ims = IMG.findall(fig)
            if not ims:
                continue
            cap = CAP.search(fig)
            capt = cap.group(0) if cap else ""
            src = SRC.search(ims[0]).group(1) if SRC.search(ims[0]) else "?"
            if not CITE.search(capt):
                out.append("!! %-12s 출처 없음: %s" % (f, src))
                bad += 1
            else:
                out.append("   %-12s %s  <- %s" % (f, src, CITE.search(capt).group(0)))
    out.insert(0, "[imgcite] 크롭마다 '원본 N권 M쪽' 출처 — 누락 %d개\n" % bad)
    io.open("_imgcite.txt", "w", encoding="utf-8").write("\n".join(out))
    return bad


def size():
    out, bad = [], 0
    for p in sorted(glob.glob(os.path.join("pdf", "*.pdf"))):
        mb = os.path.getsize(p) / 1048576.0
        f = "!!" if mb > MAX_CH_MB else "  "
        if mb > MAX_CH_MB:
            bad += 1
        out.append("%s %-40s %7.1f MB" % (f, os.path.basename(p), mb))
    for p in glob.glob("*.pdf"):
        mb = os.path.getsize(p) / 1048576.0
        f = "!!" if mb > MAX_ALL_MB else "  "
        if mb > MAX_ALL_MB:
            bad += 1
        out.append("%s %-40s %7.1f MB  (합본)" % (f, os.path.basename(p), mb))
    out.insert(0, "[size] 권별 %.0fMB · 합본 %.0fMB 한도 — 초과 %d개\n"
               % (MAX_CH_MB, MAX_ALL_MB, bad))
    io.open("_imgsize.txt", "w", encoding="utf-8").write("\n".join(out))
    return bad


CMD = {"imgfit": imgfit, "imgres": imgres, "imgcite": imgcite, "size": size}

if __name__ == "__main__":
    a = sys.argv[1] if len(sys.argv) > 1 else "all"
    names = list(CMD) if a == "all" else [a]
    total = 0
    for n in names:
        total += CMD[n]()
        print("[OK] %s -> read _%s.txt" % (n, "imgsize" if n == "size" else n))
    sys.exit(1 if total else 0)
