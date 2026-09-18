# -*- coding: utf-8 -*-
"""MinerU 입력용 JPEG 사본을 만든다.

downsample.py는 300dpi 무압축(deflate)으로 저장한다.
book_mujak은 그 결과가 src1 747MB가 되었고, MinerU가 출력 없이 죽었다.
같은 300dpi를 JPEG(q=80)로 다시 넣으면 화질 손실은 OCR에 무의미한 수준인데
파일은 5~10배 작아진다.

    python tojpg.py _src300/src1_정방향.pdf _mineru_in/src1.pdf
"""
import fitz, sys, os, io

src_path, out_path = sys.argv[1], sys.argv[2]
DPI = 300
Q = 80

os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
src = fitz.open(src_path)
dst = fitz.open()
total = len(src)
for i in range(total):
    pg = src[i]
    pix = pg.get_pixmap(dpi=DPI)
    if pix.n > 3:                      # alpha 제거
        pix = fitz.Pixmap(fitz.csRGB, pix)
    jpg = pix.tobytes("jpeg", jpg_quality=Q)
    w, h = pg.rect.width, pg.rect.height
    new = dst.new_page(width=w, height=h)
    new.insert_image(fitz.Rect(0, 0, w, h), stream=jpg)
    pix = None
    if (i + 1) % 25 == 0:
        print("  %d/%d" % (i + 1, total), flush=True)

dst.save(out_path, deflate=True, garbage=4)
a, b = os.path.getsize(src_path), os.path.getsize(out_path)
print("%s  %d쪽  %.0fMB -> %.0fMB (%.0f%%)"
      % (os.path.basename(out_path), total, a / 1048576, b / 1048576, b * 100.0 / a),
      flush=True)
dst.close()
src.close()
