# -*- coding: utf-8 -*-
"""트랙 2 — MinerU가 잡은 도판 bbox로 '원본 600dpi'에서 직접 크롭한다.

구조화는 300dpi 사본으로 하고(downsample.py), 크롭만 원본에서 뜬다.
downsample.py가 쪽 크기(pt)를 그대로 보존하므로 좌표가 1:1로 맞는다.

    python crop.py                # out*/  ->  crops/  +  crops/_index.txt
    python crop.py --dpi 400      # 크롭 해상도 지정 (기본 400)

출력
    crops/v1_p041_a.jpg           v=권, p=원본 쪽(1부터), a/b/c=그 쪽의 몇 번째 도판
    crops/_index.txt              집필할 때 보는 목록 (출처·크기·비율)
"""
import fitz, os, io, json, glob, re, sys

DPI = 400
if "--dpi" in sys.argv:
    DPI = int(sys.argv[sys.argv.index("--dpi") + 1])

MAXW = 1600          # 가로 상한 (용량 통제)
JPEGQ = 88
PAD = 4              # bbox 여유 (pt) — 테두리가 잘리는 것 방지
MINW = 900           # 이보다 좁으면 '작음'으로 표시 (imgres 검사 기준)

os.makedirs("crops", exist_ok=True)
rows = []
n = 0

for mid in sorted(glob.glob(os.path.join("out*", "*", "ocr", "*_middle.json"))):
    m = re.search(r"out(\d+)", mid)
    vol = int(m.group(1)) if m else 0
    orig = os.path.join("_src", "src%d_정방향.pdf" % vol)
    if not os.path.exists(orig):
        orig = os.path.join("_src", "src%d.pdf" % vol)
    if not os.path.exists(orig):
        rows.append("!! 원본 없음: %s" % orig)
        continue
    doc = fitz.open(orig)
    info = json.load(io.open(mid, encoding="utf-8")).get("pdf_info", [])

    for pg in info:
        pi = pg.get("page_idx", 0)
        if pi >= len(doc):
            continue
        pw, ph = pg.get("page_size", [0, 0])
        if not pw or not ph:
            continue
        page = doc[pi]
        sx = page.rect.width / float(pw)
        sy = page.rect.height / float(ph)

        boxes = []
        for b in pg.get("para_blocks", []) or []:
            # MinerU는 주가 차트를 'image'가 아니라 'chart'로 분류한다.
            # 이걸 빼면 주식책의 종목 차트가 전부 누락된다 (파일럿에서 11장 놓칠 뻔했다).
            if isinstance(b, dict) and b.get("type") in ("image", "table", "chart"):
                bb = b.get("bbox")
                if bb and len(bb) == 4:
                    boxes.append((b.get("type"), bb))
        boxes.sort(key=lambda t: (t[1][1], t[1][0]))

        for k, (typ, bb) in enumerate(boxes):
            r = fitz.Rect(bb[0] * sx - PAD, bb[1] * sy - PAD,
                          bb[2] * sx + PAD, bb[3] * sy + PAD) & page.rect
            if r.width < 20 or r.height < 20:
                continue
            dpi = DPI
            if r.width / 72.0 * dpi > MAXW:              # 가로 상한 적용
                dpi = int(MAXW / (r.width / 72.0))
            pix = page.get_pixmap(clip=r, dpi=dpi)
            name = "v%d_p%03d_%s.jpg" % (vol, pi + 1, "abcdefgh"[k] if k < 8 else str(k))
            out = os.path.join("crops", name)
            pix.pil_save(out, format="JPEG", quality=JPEGQ, optimize=True)
            kb = os.path.getsize(out) / 1024.0
            flag = "" if pix.width >= MINW else "  <- 작음"
            rows.append("%-18s %-5s %d권 %3d쪽  %4dx%-4d %6.0fKB%s"
                        % (name, typ, vol, pi + 1, pix.width, pix.height, kb, flag))
            n += 1
    doc.close()

hdr = ["도판 크롭 %d개  (원본 %ddpi에서 추출 · 가로 상한 %dpx · JPEG q%d)" % (n, DPI, MAXW, JPEGQ),
       "%-18s %-5s %-9s %-10s %s" % ("파일", "종류", "출처", "크기", "용량"),
       "-" * 74]
io.open(os.path.join("crops", "_index.txt"), "w", encoding="utf-8").write(
    "\n".join(hdr + rows))
