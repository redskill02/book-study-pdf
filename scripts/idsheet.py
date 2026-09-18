# -*- coding: utf-8 -*-
"""크롭 ID 시트 — 후보 크롭을 세로로 이어 붙여 '어느 파일이 어느 차트인지' 눈으로 확정한다.

캡션에 종목명 · 그림 번호를 쓰기 전에 반드시 만든다. 파일명(p312_a)만 믿고 번호를 붙이면 한 칸씩 밀린다.

    python idsheet.py _id14a.png v3_p068_a v3_p069_a v3_p070_a
    python idsheet.py _id14a.png --dir crops v3_p068_a ...      # 크롭 폴더 지정 (기본 crops)
"""
import sys, os
from PIL import Image, ImageDraw
if len(__import__("sys").argv) < 2: print('usage: python idsheet.py <out.png> [--dir crops] <id1> <id2> ...'); raise SystemExit(2)
args = sys.argv[1:]
D = "crops"
if "--dir" in args:
    i = args.index("--dir"); D = args[i + 1]; del args[i:i + 2]
out, ids = args[0], args[1:]
W, BAR = 980, 26
tiles = []
for i in ids:
    p = os.path.join(D, i if i.lower().endswith((".jpg", ".png")) else i + ".jpg")
    im = Image.open(p).convert("RGB")
    h = min(int(im.height * W / im.width), 640)
    tiles.append((os.path.basename(p), im.resize((W, h), Image.LANCZOS)))
H = sum(BAR + t[1].height for t in tiles)
canvas = Image.new("RGB", (W, H), "white")
d = ImageDraw.Draw(canvas); y = 0
for name, im in tiles:
    d.rectangle([0, y, W, y + BAR], fill="black"); d.text((8, y + 7), name, fill="white")
    y += BAR; canvas.paste(im, (0, y)); y += im.height
canvas.save(out); print(out, canvas.size)
