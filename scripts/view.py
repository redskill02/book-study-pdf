# -*- coding: utf-8 -*-
"""python view.py v1_p017_a [max]  -> pdf/_v_<name>.png (긴 변 max px, 기본 1000)"""
import sys, fitz, os
os.makedirs('pdf', exist_ok=True)
for n in sys.argv[1:]:
    if n.isdigit(): continue
    mx = int(sys.argv[-1]) if sys.argv[-1].isdigit() else 1000
    p = 'crops/%s.jpg' % n; d = fitz.open(p); pg = d[0]; r = pg.rect; s = mx / max(r.width, r.height)
    pg.get_pixmap(matrix=fitz.Matrix(s, s)).save('pdf/_v_%s.png' % n)
