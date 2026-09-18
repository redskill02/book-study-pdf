# -*- coding: utf-8 -*-
"""권별 체인: python _chain.py NN [--nobuild] -> concat _chNN_b, pre-checks, build, full checks, page list, overview PNG. Report: _rep.txt"""
import io, os, re, sys, subprocess
if len(__import__("sys").argv) < 2: print('usage: python _chain.py NN [--nobuild]'); raise SystemExit(2)
PY = '"%s"' % sys.executable
n = sys.argv[1]
ch = "ch%s.html" % n
rep = []
def run(cmd):
    p = subprocess.run(cmd, shell=True, capture_output=True)
    return (p.stdout + p.stderr).decode("utf-8", "replace")
def rd(f):
    return io.open(f, encoding="utf-8", errors="replace").read() if os.path.exists(f) else ""
OKWORDS = ["이상 없음", "회상 1 · 시험 1 · 정답 1 · 합격선 1 · 튜터 1"]
def chk(c, tag):
    run(PY + " build.py " + c)
    for l in rd("_%s.txt" % c).split("\n"):
        ls = l.strip()
        if "!!" in l or (ch in l and not any(k in l for k in OKWORDS) and not ls.endswith("연속")):
            rep.append(tag + ": " + ls)
b = "_ch%s_b.html" % n
if os.path.exists(b):
    a = io.open(ch, encoding="utf-8").read()
    if a.rfind("<parameter>") > 0: rep.append("!! TRUNC in part a")
    io.open(ch, "w", encoding="utf-8").write(a.rstrip("\n") + "\n" + io.open(b, encoding="utf-8").read())
    os.remove(b)
s = io.open(ch, encoding="utf-8").read()
for pat in ["<class '", "<table", "<parameter", "</invoke"]:
    if pat in s: rep.append("!! found " + pat)
if s.count("<html") != 1: rep.append("!! html count %d" % s.count("<html"))
for m in re.finditer(r"^<text.*<[biu]>", s, re.M): rep.append("!! b in text: " + m.group(0)[:80])
run(PY + " esctitle.py " + ch); run(PY + " strip.py " + ch); run(PY + " flatg.py " + ch); run(PY + " pushg.py " + ch)
o = run(PY + " checkall.py " + ch); rep += ["checkall: " + l for l in o.split("\n") if l.strip() and not l.startswith("[OK]")]
run(PY + " build.py svgfit >nul"); run(PY + " build.py linegap >nul")
for f in ["_svgfit.txt", "_linegap.txt"]:
    for l in rd(f).split("\n"):
        if ch in l and "svg#" in l: rep.append(f + ": " + l.strip())
chk("svgbox", "svgbox"); chk("tags", "tags")
run(PY + " prewidth.py 100 >nul")
rep += ["prewidth: " + l.strip() for l in rd("_prewidth.txt").split("\n") if ch in l and "  - " not in l]
if "--nobuild" in sys.argv or any(r.startswith(("!!", "checkall", "_svgfit", "_linegap", "svgbox", "tags", "prewidth")) for r in rep):
    io.open("_rep.txt", "w", encoding="utf-8").write("\n".join(rep) or "pre-checks clean"); sys.exit()
o = run(PY + " fixbottom.py ."); rep += ["fixbottom: " + l.strip() for l in o.split("\n") if ch in l]
o = run(PY + " autofit.py ."); rep += ["autofit: " + l.strip() for l in o.split("\n") if ch in l]
run(PY + " pushg.py " + ch); run(PY + " build.py ch" + n); run(PY + " build.py render >nul")
run(PY + " build.py stats")
rep += ["stats: " + l.strip() for l in rd("_stats.txt").split("\n") if ch in l or "불일치" in l or "전부" in l]
o = run(PY + " checkall.py " + ch); rep += ["checkall2: " + l for l in o.split("\n") if l.strip() and not l.startswith("[OK]")]
run(PY + " build.py svgfit >nul"); run(PY + " build.py linegap >nul")
for f in ["_svgfit.txt", "_linegap.txt"]:
    for l in rd(f).split("\n"):
        if ch in l and "svg#" in l: rep.append(f + "2: " + l.strip())
for c in ["svgbox", "comicfit", "tags", "blocks", "headings"]: chk(c, c + "2")
rep.append("comicfit: " + rd("_comicfit.txt").strip().split("\n")[-1])
import fitz
from PIL import Image
d = fitz.open("pdf/ch%s.pdf" % n)
rep.append("pages %d" % len(d))
for i, p in enumerate(d): rep.append("%d: %s" % (i + 1, p.get_text()[:48].replace("\n", " ")))
ims = []
for i in range(1, min(9, len(d))):
    pix = d[i].get_pixmap(dpi=40); ims.append(Image.frombytes("RGB", (pix.width, pix.height), pix.samples))
w, h = ims[0].size; sheet = Image.new("RGB", (w * 4, h * 2), "white")
for k, im in enumerate(ims): sheet.paste(im, ((k % 4) * w, (k // 4) * h))
sheet.save("_ov%s.png" % n)
io.open("_rep.txt", "w", encoding="utf-8").write("\n".join(rep))
