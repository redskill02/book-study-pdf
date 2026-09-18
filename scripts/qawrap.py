# -*- coding: utf-8 -*-
"""시험 문항과 답안줄을 한 덩어리로 묶는다.

빈 페이지의 원인 — <div class="q">문항</div> 다음의 <div class="line"></div> 들이
문항과 떨어져 다음 장으로 넘어가면, 그 장은 '줄만 있는 빈 페이지'처럼 보인다.
page-break-before: avoid 는 Chrome 인쇄에서 형제 요소 연속에 잘 안 걸린다.
확실한 방법은 둘을 한 컨테이너에 넣고 break-inside: avoid 를 거는 것이다.

    python qawrap.py            # ch*.html 전부 처리 (이미 묶인 것은 건너뛴다)

CSS 에 다음이 있어야 한다:
    .exam .qa { page-break-inside: avoid; break-inside: avoid; }
"""
import io, re, glob, sys

PAT = re.compile(
    r'(<div class="q">.*?</div>)'          # 문항
    r'((?:\s*<div class="line"></div>)+)',  # 뒤따르는 답안줄 1개 이상
    re.S)

n_files = 0
n_wrap = 0
for f in sorted(glob.glob("ch*.html")) + ["_front.html"]:
    try:
        s = io.open(f, encoding="utf-8").read()
    except IOError:
        continue
    if '<div class="qa">' in s:
        continue
    out, cnt = PAT.subn(lambda m: '<div class="qa">%s%s\n</div>' % (m.group(1), m.group(2)), s)
    if cnt:
        io.open(f, "w", encoding="utf-8").write(out)
        n_files += 1
        n_wrap += cnt

io.open("_qawrap.txt", "w", encoding="utf-8").write(
    "문항+답안줄 묶기 — 파일 %d개 / 문항 %d개\n" % (n_files, n_wrap))
print("files=%d wrapped=%d" % (n_files, n_wrap))
