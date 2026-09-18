# -*- coding: utf-8 -*-
"""fitz 텍스트 레이어 추출 (권별 집필 입력): python _extf.py NN a b [--off K] [--src _src/src1.pdf]
   책 a~b 쪽 -> _chNNf.txt.   책 = pdf - K  (기본 K=1: pdf 21 = 책 20).  긴 줄은 150자로 접는다."""
import fitz, io, sys, textwrap
if len(__import__("sys").argv) < 4: print('usage: python _extf.py NN a b [--off K] [--src _src/src1.pdf]'); raise SystemExit(2)
NN, a, b = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
K = int(sys.argv[sys.argv.index("--off") + 1]) if "--off" in sys.argv else 1
SRC = sys.argv[sys.argv.index("--src") + 1] if "--src" in sys.argv else "_src/src1.pdf"
d = fitz.open(SRC)
out = []
for bp in range(a, b + 1):
    pi = bp + K - 1            # 0-based pdf index
    if pi < 0 or pi >= len(d): break
    out.append("----- book %d (pdf %d) -----" % (bp, pi + 1))
    for line in d[pi].get_text().split("\n"):
        out += textwrap.wrap(line, 150) or [""]
io.open("_ch%sf.txt" % NN, "w", encoding="utf-8").write("\n".join(out))
print(len(out), "lines ->", "_ch%sf.txt" % NN)
