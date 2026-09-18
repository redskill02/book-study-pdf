# -*- coding: utf-8 -*-
"""MinerU 를 권(volume)마다 순서대로 돌린다. 백그라운드(detach)로 띄우고 _mineru_done.txt 를 지켜본다.

    python run_mineru.py 1 2        # _mineru_in/src1.pdf, src2.pdf -> out1/, out2/
    python run_mineru.py 1 --lang en

환경변수
    MINERU_EXE   mineru 실행 파일 (기본: mineru  — PATH 에 있어야 한다)
    MINERU_LANG  기본 언어 (기본: korean, 영어 원서는 en 또는 생략)
"""
import subprocess, io, datetime, os, sys
M = os.environ.get("MINERU_EXE", "mineru")
lang = os.environ.get("MINERU_LANG", "korean")
vols = []
args = sys.argv[1:]
if "--lang" in args:
    i = args.index("--lang"); lang = args[i + 1]; del args[i:i + 2]
vols = [int(a) for a in args] or [1]
for v in vols:
    src = "_mineru_in/src%d.pdf" % v
    if not os.path.exists(src):
        src = "_src/src%d.pdf" % v
    cmd = [M, "-b", "pipeline", "-m", "ocr", "-p", src, "-o", "out%d" % v]
    if lang and lang not in ("en", "none"):
        cmd += ["-l", lang]
    with open("_mineru%d.log" % v, "w") as log:
        subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT)
    io.open("_mineru_done.txt", "a").write("done src%d %s\n" % (v, datetime.datetime.now().strftime("%H:%M:%S")))
