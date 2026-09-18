# -*- coding: utf-8 -*-
"""MinerU 산출물 -> 학습용 구조(목차 + 대단원별 파일 + 이미지)"""
import json, io, glob, os, re, shutil

import sys
# 사용법: python split.py <MinerU 출력 루트(out*)> <분할 결과 폴더> ["대단원 정규식"]
#   대단원 정규식 기본값은 영어 원서용 SECTION I/II … 이다. 한국어 책은 예:  "^\s*제\s*(\d+)\s*[장부]"
if len(sys.argv) < 3:
    print(__doc__); print("usage: python split.py <mineru_out_root> <dest_dir> [section_regex]"); sys.exit(2)
W    = sys.argv[1]
DEST = sys.argv[2]
SEC  = re.compile(sys.argv[3] if len(sys.argv) > 3 else r"^\s*SECTION\s+([IVXLCD]+|[A-Z])\b\s*[:\s]", re.I)

UNESC = re.compile(r"\\([$#&_{}%])")           # MinerU 가 이스케이프한 문자 복원
BADCH = re.compile(r'[<>:"/\\|?*]')            # 윈도우 파일명 금지문자


def unesc(s):
    return UNESC.sub(r"\1", s)


def slug(s):
    s = BADCH.sub("", unesc(s)).strip()
    return re.sub(r"\s+", " ", s)[:60].rstrip(". ")


def render(blocks, title_first=False):
    """title_first: 첫 블록(대단원 제목)을 파일 최상위 제목(#)으로 올린다."""
    parts = []
    for n, b in enumerate(blocks):
        t = b.get("type")
        if t == "text":
            lv = b.get("text_level")
            txt = b.get("text", "").strip()
            if not txt:
                continue
            if title_first and n == 0:
                parts.append("# " + txt)
            else:
                parts.append(("#" * min(lv + 1, 6) + " " + txt) if lv else txt)
        elif t == "table":
            cap = " ".join(b.get("table_caption") or [])
            parts.append((cap + "\n" if cap else "") + (b.get("table_body") or ""))
        elif t == "image":
            cap = " ".join(b.get("image_caption") or [])
            parts.append("![{}]({})".format(cap, b.get("img_path", "")))
        elif t == "equation":
            parts.append(b.get("text", ""))
    return "\n\n".join(p for p in parts if p.strip())


log = []
for cl_path in sorted(glob.glob(os.path.join(W, "**", "*_content_list.json"), recursive=True)):
    book = re.sub(r"_(ocr_)?content_list\.json$", "", os.path.basename(cl_path))
    src  = os.path.dirname(cl_path)
    cl   = json.load(open(cl_path, encoding="utf-8"))
    out  = os.path.join(DEST, slug(book))
    os.makedirs(out, exist_ok=True)
    for stale in glob.glob(os.path.join(out, "*.md")):   # 재실행 시 이전 분할 결과 제거
        os.remove(stale)

    if os.path.isdir(os.path.join(src, "images")):
        shutil.copytree(os.path.join(src, "images"), os.path.join(out, "images"), dirs_exist_ok=True)

    body = [b for b in cl if b.get("type") in ("text", "image", "table", "equation")]

    # 대단원 경계 = SECTION <번호> 제목. 같은 번호가 다시 나오면(Conclusion/Outline 등)
    # 새 경계로 보지 않고 최초 출현만 경계로 삼는다.
    bounds, seen = [], set()
    for i, b in enumerate(body):
        if not b.get("text_level"):
            continue
        m = SEC.match(unesc(b.get("text", "")))
        if not m:
            continue
        num = m.group(1).upper()
        if num in seen:
            continue
        seen.add(num)
        bounds.append(i)

    segs = []
    if bounds:
        if bounds[0] > 0:
            segs.append(("00_앞부분", body[:bounds[0]]))
        for n, i in enumerate(bounds, 1):
            j = bounds[n] if n < len(bounds) else len(body)
            segs.append(("{:02d}_{}".format(n, slug(body[i]["text"])), body[i:j]))
    else:
        segs.append(("00_전체", body))

    for fn, blocks in segs:
        is_sec = not fn.startswith("00_")
        io.open(os.path.join(out, fn + ".md"), "w", encoding="utf-8").write(render(blocks, title_first=is_sec))

    total_pg = max((b.get("page_idx", 0) for b in cl), default=0) + 1
    toc = ["# {} 목차".format(unesc(book)), "",
           "- 총 {}페이지 / 본문블록 {}개 / 대단원 {}개".format(total_pg, len(body), len(bounds)), ""]
    for fn, blocks in segs:
        pg = blocks[0].get("page_idx", 0) + 1 if blocks else 0
        toc.append("## [{0}]({0}.md)  (p{1}~, {2}블록)".format(fn, pg, len(blocks)))
        for b in blocks:
            if b.get("text_level") and not SEC.match(unesc(b.get("text", ""))):
                toc.append("  - p{} {}".format(b.get("page_idx", 0) + 1, unesc(b["text"]).strip()[:80]))
        toc.append("")
    io.open(os.path.join(out, "00_목차.md"), "w", encoding="utf-8").write("\n".join(toc))

    log.append("{}: {}페이지 | 대단원 {}개 | 파일 {}개".format(unesc(book), total_pg, len(bounds), len(segs) + 1))

io.open(os.path.join(DEST, "_split_log.txt"), "w", encoding="utf-8").write("\n".join(log))
print("done")
