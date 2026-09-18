# -*- coding: utf-8 -*-
"""MinerU가 추출한 원본 이미지를 컨택트시트로 묶어 전수 확인한다.

집필 '전에' 반드시 돌린다. 본문에 없고 그림에만 존재하는 개념이 있기 때문이다.
($100M Offers의 Splinter Stack은 본문 언급 0회, 오직 그림에만 있었다.)

사용법:
  python contact_sheet.py "<images 폴더>" [출력경로prefix] [칸수]
출력:
  prefix_1.png, prefix_2.png ... (시트당 최대 40장)
  + prefix_index.txt (칸 번호 -> 파일명 매핑)
"""
import os, sys, io, math
from PIL import Image

src = sys.argv[1]
prefix = sys.argv[2] if len(sys.argv) > 2 else "contact"
COLS = int(sys.argv[3]) if len(sys.argv) > 3 else 5
PER = 40
CELL = 300
PAD = 26  # 번호 라벨 자리

files = sorted(f for f in os.listdir(src)
               if f.lower().endswith((".jpg", ".jpeg", ".png")))
idx = []
for s in range(0, len(files), PER):
    chunk = files[s:s + PER]
    rows = math.ceil(len(chunk) / COLS)
    sheet = Image.new("RGB", (COLS * CELL, rows * (CELL + PAD)), "white")
    for i, f in enumerate(chunk):
        n = s + i + 1
        idx.append("%3d  %s" % (n, f))
        try:
            im = Image.open(os.path.join(src, f))
            im.thumbnail((CELL - 10, CELL - 10))
        except Exception:
            continue
        x = (i % COLS) * CELL + (CELL - im.width) // 2
        y = (i // COLS) * (CELL + PAD) + PAD + (CELL - im.height) // 2
        sheet.paste(im, (x, y))
        # 번호는 그림 위에 텍스트로 (PIL 기본 폰트, 숫자만이라 충분)
        from PIL import ImageDraw
        ImageDraw.Draw(sheet).text(
            ((i % COLS) * CELL + 8, (i // COLS) * (CELL + PAD) + 6),
            str(n), fill="red")
    out = "%s_%d.png" % (prefix, s // PER + 1)
    sheet.save(out)
    print(out)

io.open(prefix + "_index.txt", "w", encoding="utf-8").write("\n".join(idx))
print("총 %d장 / 시트 %d개" % (len(files), math.ceil(len(files) / PER)))
