# -*- coding: utf-8 -*-
"""검사기 8종 + 이미지 4종을 한 번에. 셸 변수 확장 없이 돌리기 위한 래퍼."""
import subprocess, sys
names = ["stats","blocks","headings","svgbox","svgfit","linegap","comicfit","tags"]
for n in names:
    r = subprocess.run([sys.executable, "build.py", n], capture_output=True, text=True)
    print((r.stdout or r.stderr).strip().splitlines()[-1])
r = subprocess.run([sys.executable, "imgcheck.py", "all"], capture_output=True, text=True)
print((r.stdout or "").strip())
