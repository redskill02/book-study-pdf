# -*- coding: utf-8 -*-
"""트랙 1 — 구조화용 300dpi 사본을 만든다.

원본이 600dpi라 MinerU에 그대로 넣으면 느리고 실패 위험이 크다.
텍스트·레이아웃·bbox만 뽑으면 되므로 300dpi면 충분하다.
도판 크롭은 원본(600dpi)에서 따로 뜬다 — crop.py 참조.

    python downsample.py            # _src/src*.pdf -> _src300/src*.pdf
"""
import fitz, os, sys, io, glob

SRC = "_src"
OUT = "_src300"
DPI = 300

os.makedirs(OUT, exist_ok=True)
rows = []
for p in sorted(glob.glob(os.path.join(SRC, "*.pdf"))):
    name = os.path.basename(p)
    out = os.path.join(OUT, name)
    src = fitz.open(p)
    dst = fitz.open()
    for i in range(len(src)):
        pg = src[i]
        pix = pg.get_pixmap(dpi=DPI)
        w, h = pg.rect.width, pg.rect.height
        new = dst.new_page(width=w, height=h)
        new.insert_image(fitz.Rect(0, 0, w, h), pixmap=pix)
    dst.save(out, deflate=True, garbage=4)
    a, b = os.path.getsize(p), os.path.getsize(out)
    rows.append("%-12s %5d쪽  %7.1fMB -> %6.1fMB  (%.0f%%)"
                % (name, len(src), a / 1048576, b / 1048576, b * 100.0 / a))
    dst.close()
    src.close()

io.open("_downsample.txt", "w", encoding="utf-8").write("\n".join(rows))
