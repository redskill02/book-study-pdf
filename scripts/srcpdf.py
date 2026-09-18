# -*- coding: utf-8 -*-
"""원본 PDF 텍스트 레이어로 책 쪽 범위를 뽑는다 — MinerU md 는 띄어쓰기를 지우므로 차트 책 · 레이어 양호한 책의 집필용은 이쪽.
    python srcpdf.py 4 38              -> _읽기.txt   (책 4~38쪽)
    python srcpdf.py 4 38 --off 2      -> 책 N = pdf N+2  (기본 0 = 책 N = pdf N)
    python srcpdf.py 4 38 --off 2 --src _src/src2.pdf
책 = pdf + OFF 관계는 책마다 · 권마다 다르다. 인쇄 쪽번호로 확인해 _GATE.md 에 적어 둔다.
"""
import fitz, io, sys
if len(__import__("sys").argv) < 3: print('usage: python srcpdf.py <a> <b> [--off K] [--src _src/src1.pdf]'); raise SystemExit(2)
a, b = int(sys.argv[1]), int(sys.argv[2])
OFF = int(sys.argv[sys.argv.index("--off") + 1]) if "--off" in sys.argv else 0
SRC = sys.argv[sys.argv.index("--src") + 1] if "--src" in sys.argv else "_src/src1.pdf"
d = fitz.open(SRC)
out = []
for bp in range(a, b + 1):
    p = bp + OFF - 1
    if p < 0 or p >= len(d): break
    t = d[p].get_text().replace("\u00ad", "")
    lines = [l.rstrip() for l in t.split("\n") if l.strip()]
    out.append("----- 책 %d쪽 (pdf %d) -----" % (bp, p + 1))
    out.append("\n".join(lines)); out.append("")
io.open("_읽기.txt", "w", encoding="utf-8").write("\n".join(out))
print("ok", a, b, "->", "_읽기.txt")
