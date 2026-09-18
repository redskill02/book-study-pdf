# -*- coding: utf-8 -*-
"""책 쪽번호로 원문을 뽑는다.

MinerU가 장 제목을 본문에 섞어 버려서 md 줄 번호로는 장 경계를 잡기 어렵다.
대신 content_list.json 의 page_idx 로 '책 쪽번호 -> 원문'을 만든다.

    python src.py 199 213        # 책 199~213쪽 (5장 매매 구역 JH ZONE)
    python src.py 65 82 --raw    # 표/이미지 표시 없이 본문만

쪽 대응 (책 7쪽 = src1 p5 '머리말'로 확인)
    src1  책쪽 = PDF쪽 + 2      (책   3~138)
    src2  책쪽 = PDF쪽 + 138    (책 139~214)
    src3  책쪽 = PDF쪽 + 214    (책 215~288)
"""
import json, io, os, sys, glob

# 권별 오프셋(책쪽 = PDF쪽 + OFF). 책마다 다르다 — 인쇄 쪽번호(footer)로 권마다 다시 재서 _GATE.md 에 적는다.
#   환경변수 BOOK_OFF="1:2,2:150,3:260"  또는  --off 1:2,2:150 으로 준다.
import os
def _parse_off(txt):
    d = {}
    for kv in txt.split(","):
        if ":" in kv:
            k, v = kv.split(":"); d[int(k)] = int(v)
    return d
OFF = _parse_off(os.environ.get("BOOK_OFF", "1:0"))
if "--off" in sys.argv:
    OFF = _parse_off(sys.argv[sys.argv.index("--off") + 1])
# src1 책쪽 = PDF쪽 + 2   (책   3~150)
# src2 책쪽 = PDF쪽 + 150 (책 151~260)
# src3 책쪽 = PDF쪽 + 260 (책 261~346)
# src4 책쪽 = PDF쪽 + 346 (책 347~440)


def load():
    pages = {}
    for v in sorted(OFF):
        f = "out%d/src%d/ocr/src%d_content_list.json" % (v, v, v)
        if not os.path.exists(f):
            continue
        for it in json.load(io.open(f, encoding="utf-8")):
            bp = it.get("page_idx", 0) + 1 + OFF[v]
            pages.setdefault(bp, []).append((v, it))
    return pages


def dump(a, b, raw=False):
    pages = load()
    out = []
    for bp in range(a, b + 1):
        items = pages.get(bp)
        if not items:
            continue
        out.append("\n----- 책 %d쪽 (원본 %d권 %d쪽) -----" % (bp, items[0][0], bp - OFF[items[0][0]]))
        for v, it in items:
            t = it.get("type")
            if t in ("text", "aside_text"):
                s = (it.get("text") or "").strip()
                if s:
                    out.append(s)
            elif t == "list":
                for s in (it.get("list_items") or []):
                    s = (s or "").strip()
                    if s:
                        out.append(s)
            elif t in ("image", "table", "chart") and not raw:
                cap = " ".join(it.get("img_caption") or it.get("table_caption") or [])
                out.append("[%s%s]" % (t, (" — " + cap) if cap else ""))
            elif t == "equation" and not raw:
                out.append("[수식] " + (it.get("text") or "")[:80])
    return "\n".join(out)


if __name__ == "__main__":
    a, b = int(sys.argv[1]), int(sys.argv[2])
    raw = "--raw" in sys.argv
    io.open("_읽기.txt", "w", encoding="utf-8").write(dump(a, b, raw))
    print("[OK] 책 %d~%d쪽 -> _읽기.txt" % (a, b))
