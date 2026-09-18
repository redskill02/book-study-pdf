# -*- coding: utf-8 -*-
"""0.5단계 + 1단계를 한 번에: rotate scan -> rotate fix -> MinerU ocr.  (오래 걸린다 — detach 로 띄운다)

    python _pipeline.py [권번호 ...]          # 기본 1
환경변수
    MINERU_PY    MinerU venv 의 python (rotate.py 는 MinerU 의 OCR 엔진을 빌려 쓴다)
    MINERU_EXE   mineru 실행 파일
    MINERU_LANG  korean(기본) / en
    SKILL_DIR    이 저장소(스킬) 경로 — rotate.py 위치. 기본은 이 파일의 폴더
진행은 _pipeline_done.txt 에 단계별 시각이 찍힌다.
"""
import subprocess, io, datetime, os, shutil, sys
HERE = os.path.dirname(os.path.abspath(__file__))
V = os.environ.get("MINERU_PY", sys.executable)
R = os.path.join(os.environ.get("SKILL_DIR", HERE), "rotate.py")
if not os.path.exists(R):
    R = os.path.join(os.environ.get("SKILL_DIR", HERE), "scripts", "rotate.py")
M = os.environ.get("MINERU_EXE", "mineru")
lang = os.environ.get("MINERU_LANG", "korean")
vols = [int(a) for a in sys.argv[1:]] or [1]
def stamp(msg):
    io.open("_pipeline_done.txt", "a").write("%s %s\n" % (msg, datetime.datetime.now().strftime("%H:%M:%S")))
os.makedirs("_mineru_in", exist_ok=True)
for v in vols:
    src = "_src/src%d.pdf" % v
    with open("_rotate_scan%d.log" % v, "w") as log:
        subprocess.run([V, R, "scan", src], stdout=log, stderr=subprocess.STDOUT)
    stamp("rotate-scan src%d" % v)
    with open("_rotate_fix%d.log" % v, "w") as log:
        subprocess.run([V, R, "fix", src], stdout=log, stderr=subprocess.STDOUT)
    stamp("rotate-fix src%d" % v)
    fixed = "_src/src%d_정방향.pdf" % v
    use = fixed if os.path.exists(fixed) else src
    shutil.copy(use, "_mineru_in/src%d.pdf" % v)
    stamp("copied " + use)
    cmd = [M, "-b", "pipeline", "-m", "ocr", "-p", "_mineru_in/src%d.pdf" % v, "-o", "out%d" % v]
    if lang and lang not in ("en", "none"):
        cmd += ["-l", lang]
    with open("_mineru%d.log" % v, "w") as log:
        subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT)
    stamp("mineru src%d" % v)
stamp("ALL DONE")
