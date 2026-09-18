# -*- coding: utf-8 -*-
"""
0.5단계 — 뒤집힌 페이지 검출과 보정.

스캔본 PDF에는 한두 장씩 거꾸로(180도) 또는 옆으로(90/270도) 들어간 쪽이 섞인다.
MinerU는 이걸 고쳐주지 못한다. MinerU의 방향 분류기는 표(table)만 대상으로 하고
후보각이 ("0", "90", "270") 뿐이라 180도는 아예 고려 대상이 아니다.
(mineru/model/table/cls/mineru_table_ori_cls.py 의 ORIENTATION_SCORE_LABELS)

그래서 변환 전에 이 단계를 따로 돌린다.

  실행은 MinerU venv 파이썬으로 한다:
    $MINERU_PY rotate.py scan "<PDF 또는 폴더>"
    cat _rotate.txt
    $MINERU_PY rotate.py fix  "<PDF 또는 폴더>"

  판정이 애매한 쪽은 사람이 직접 본다:
    ... rotate.py peek "<PDF>" 41 88

판정 방법 — 회전 후보별로 OCR을 돌려 인식 신뢰도를 비교한다.
축을 먼저 정하고, 축 안에서만 겨루는 2단 구조다. 이유는 실측 때문이다:

  40쪽 정방향   가설 0 = 283.7점 / 가설 90 = 282.8점  <- 거의 동점
                가설 180 =  20.0점 / 가설 270 = 14.1점

  OCR이 세로로 긴 박스를 자동으로 눕혀 인식하기 때문에 0도와 90도는 점수가 갈리지 않는다.
  반대로 0도 대 180도는 14배까지 벌어진다.
  따라서 0/90 판별은 점수가 아니라 '박스가 세로로 긴 비율'로 하고,
  180도 판별만 점수로 한다.
"""
import io
import json
import os
import sys
import time

import numpy as np

TALL = 0.8          # w/h 가 이보다 작으면 세로로 긴 박스
TALL_RATIO = 0.50   # 세로 박스가 이 비율을 넘으면 90/270 축
CONF_MIN = 0.85     # 평균 신뢰도가 이보다 낮으면 의심
MIN_CHARS = 15      # 글자가 이보다 적으면 판정 불가(그림/빈 쪽)
MARGIN_MIN = 1.30   # 승자/패자 점수비가 이보다 낮으면 판정 보류
DPI = 100

_ENGINE = None


def engine(lang):
    global _ENGINE
    if _ENGINE is None:
        from mineru.backend.pipeline.model_init import ocr_model_init
        _ENGINE = ocr_model_init(lang=lang)
    return _ENGINE


def rot(img, deg):
    """화면상 시계방향 deg 회전."""
    return np.ascontiguousarray(np.rot90(img, {0: 0, 90: 3, 180: 2, 270: 1}[deg % 360]))


def measure(img, lang):
    """(평균신뢰도, 글자수, 가중합계, 세로박스비율)"""
    res = engine(lang).ocr(img, det=True, rec=True)[0]
    if not res:
        return 0.0, 0, 0.0, 0.0
    chars, acc, tall, nbox = 0, 0.0, 0, 0
    for box, (txt, sc) in res:
        n = len(txt.strip())
        p = np.asarray(box, dtype=np.float32)
        w, h = float(p[2][0] - p[0][0]), float(p[2][1] - p[0][1])
        nbox += 1
        if h > 0 and (w / h) < TALL:
            tall += 1
        if n:
            chars += n
            acc += sc * n
    mean = acc / chars if chars else 0.0
    return mean, chars, acc, (tall / nbox if nbox else 0.0)


def pdf_pages(path):
    import pypdfium2 as pdfium
    return pdfium.PdfDocument(path)


# --- 사전필터 (--fast) ------------------------------------------------------
#
# 1차 통과는 모든 쪽에 OCR을 돌리기 때문에 시간의 대부분을 여기서 쓴다.
# 그런데 검사가 필요한 쪽은 원본 텍스트 레이어만 봐도 상당히 좁혀진다.
#
# 실측 3권 (브랜드설계자 · 인생을 운에 맡기지 마라 · 트래픽설계자)
#   (쪽별 고아 자모율 상위 10%) ∪ (한글 150자 미만)  ->  대상 9/9 전부 포함
#
# 두 조건이 **둘 다** 필요하다. 자모율만 쓰면 놓친다:
#   트래픽설계자 1권 138쪽(빈 쪽)  자모율 235위 / 한글 1자
#   인생을 운에... 1권 표지(뒤집힘) 자모율 206위 / 한글 9자
# 글자가 적은 쪽은 자모도 적어서 자모율 순위가 올라가지 않는다.
#
# 텍스트 레이어가 없는 PDF에서는 이 필터를 쓸 수 없다. 그때는 전수로 되돌린다.
FAST_TOP_RATIO = 0.10     # 자모율 상위 몇 %를 후보로 볼 것인가
FAST_MIN_HANGUL = 150     # 한글이 이보다 적으면 무조건 후보

_JAMO = None
_HAN = None


def _page_text_stats(path):
    """쪽마다 (한글 수, 고아 자모 수). 텍스트 레이어가 없거나 못 읽으면 None.

    pypdfium2 를 쓴다. MinerU venv 에 PyMuPDF(fitz)가 없기 때문이다 —
    이걸 모르고 fitz 로 짰다가 ModuleNotFoundError 로 죽었다.
    실패하면 무조건 None 을 돌려 **전수 검사로 되돌린다.** 안전한 방향은 그쪽이다.
    """
    global _JAMO, _HAN
    import re
    if _JAMO is None:
        _JAMO = re.compile(u"[ㄱ-ㆎ]")
        _HAN = re.compile(u"[가-힣]")
    try:
        doc = pdf_pages(path)
        out = []
        for i in range(len(doc)):
            tp = doc[i].get_textpage()
            t = tp.get_text_range()
            out.append((len(_HAN.findall(t)), len(_JAMO.findall(t))))
    except Exception:
        return None
    return out if sum(h for h, _ in out) > 0 else None


def prefilter(path, n, out_log):
    """검사할 쪽 번호(1-based) 집합. 필터를 쓸 수 없으면 None."""
    stats = _page_text_stats(path)
    if stats is None or len(stats) != n:
        out_log("  [사전필터] 텍스트 레이어가 없어 쓸 수 없다 -> 전수 검사로 되돌린다")
        return None

    rate = []
    for i, (h, j) in enumerate(stats):
        rate.append((99999.0 if h == 0 else j * 10000.0 / h, i + 1))
    rate.sort(reverse=True)
    top = set(p for _, p in rate[:max(1, int(n * FAST_TOP_RATIO))])
    few = set(i + 1 for i, (h, _) in enumerate(stats) if h < FAST_MIN_HANGUL)
    cand = top | few
    out_log("  [사전필터] 자모율 상위 %d쪽 ∪ 한글 %d자 미만 %d쪽 = 후보 %d쪽 (%.0f%%)"
            % (len(top), FAST_MIN_HANGUL, len(few), len(cand), 100.0 * len(cand) / n))
    out_log("  [사전필터] 나머지 %d쪽은 검사하지 않는다. 놓칠 수 있다는 뜻이다."
            % (n - len(cand)))
    return cand


def render(doc, pno, dpi):
    pil = doc[pno].render(scale=dpi / 72.0).to_pil().convert("RGB")
    return np.asarray(pil)


def scan_pdf(path, lang, dpi, out_log, fast=False):
    doc = pdf_pages(path)
    n = len(doc)
    name = os.path.basename(path)
    rows = []
    out_log("")
    out_log("=" * 78)
    out_log("%s  (%d쪽)" % (name, n))
    out_log("=" * 78)

    only = prefilter(path, n, out_log) if fast else None

    t0 = time.time()
    done = 0
    for i in range(n):
        if only is not None and (i + 1) not in only:
            # 사전필터에서 빠진 쪽. OCR을 돌리지 않으므로 2차 후보에도 오르지 않는다.
            rows.append({"page": i + 1, "mean": 1.0, "chars": 9999,
                         "acc": 0.0, "tall": 0.0, "need": 0,
                         "margin": None, "state": "미검사"})
            continue
        img = render(doc, i, dpi)
        mean, chars, acc, tall = measure(img, lang)
        rows.append({"page": i + 1, "mean": mean, "chars": chars,
                     "acc": acc, "tall": tall, "need": 0,
                     "margin": None, "state": "정상"})
        done += 1
        if done % 25 == 0:
            out_log("  ... %d쪽 1차 통과 (%.0f초)" % (done, time.time() - t0))

    # 2차 — 의심되는 쪽을 정밀 검사한다.
    #
    # 글자가 적은 쪽(chars < MIN_CHARS)을 여기서 곧바로 '판정불가'로 빼면 안 된다.
    # 뒤집힌 쪽은 0도에서 글자가 거의 안 읽히므로 바로 그 조건에 걸린다.
    # 실제로 『인생을 운에 맡기지 마라』 1권 표지와 2권 195쪽이 그렇게 새어 나갔다.
    # 빈 쪽인지 뒤집힌 쪽인지는 **돌려보기 전에는 구분할 수 없다.**
    sus = []
    for r in rows:
        if (r["chars"] < MIN_CHARS
                or r["tall"] > TALL_RATIO
                or r["mean"] < CONF_MIN):
            r["state"] = "의심"
            sus.append(r)

    for r in sus:
        i = r["page"] - 1
        img = render(doc, i, dpi)
        thin = r["chars"] < MIN_CHARS
        if thin:
            cands = (0, 90, 180, 270)   # 글자가 없으면 축을 정할 수 없다. 전부 본다
        elif r["tall"] > TALL_RATIO:
            cands = (90, 270)
        else:
            cands = (0, 180)

        sc, tl, best_chars = {}, {}, 0
        for a in cands:
            _m, nch, tot, t = measure(rot(img, a), lang)
            sc[a] = tot
            tl[a] = t
            best_chars = max(best_chars, nch)

        r["scores"] = {str(k): round(float(v), 1) for k, v in sc.items()}
        r["talls"] = {str(k): round(float(v), 2) for k, v in tl.items()}
        if best_chars < MIN_CHARS:
            # 어느 방향으로 돌려도 글자가 없다 = 진짜 그림/빈 쪽
            r["state"] = "판정불가"
            continue

        # **점수만으로는 180 과 270 을 못 가른다.**
        # PaddleOCR 은 세로로 긴 박스를 인식 전에 자기가 90도 돌린다. 그래서
        # 옆으로 누운 렌더링도 글자가 거의 그대로 읽히고 점수가 같이 올라간다.
        # 『콘텐츠 설계자』 3권 48쪽 — 눈으로 보면 180도인데 점수는
        #   180=118.0 / 270=120.0 으로 **270이 1등**이었다.
        # 가른 것은 점수가 아니라 박스 모양이다. 같은 쪽의 세로박스 비율이
        #   180 -> 0.00 (가로 줄)   270 -> 1.00 (전부 세로)
        # 바로 선 쪽은 글줄이 가로다. 가로 줄이 보이는 후보가 있으면 그쪽만 남긴다.
        flat = [a for a in sc if tl[a] < TALL_RATIO]
        if flat and len(flat) < len(sc):
            r["dropped"] = sorted(a for a in sc if a not in flat)
            sc = dict((a, sc[a]) for a in flat)

        # 점수차는 반드시 **2위**와 비교한다. 최하위와 비교하면
        # 180 vs 270 이 43.0 대 44.4(=1.03배)로 사실상 동점인데도
        # 최하위 1.8 과 견주어 24.2배로 찍혀 '확실한 판정'처럼 보인다.
        # 『스토리 설계자』 1권 108쪽이 그렇게 180도를 270도로 오판했다.
        order = sorted(sc, key=sc.get, reverse=True)
        win = order[0]
        second = order[1] if len(order) > 1 else win
        margin = (sc[win] / sc[second]) if sc[second] > 0 else 999.0
        r["need"] = win
        r["margin"] = round(margin, 2)
        if win == 0:
            r["state"] = "정상"
        elif margin < MARGIN_MIN:
            r["state"] = "보류"
        else:
            r["state"] = "뒤집힘"

    bad = [r for r in rows if r["state"] == "뒤집힘"]
    hold = [r for r in rows if r["state"] == "보류"]
    unk = [r for r in rows if r["state"] == "판정불가"]

    skipped = [r for r in rows if r["state"] == "미검사"]

    out_log("")
    out_log("1차 통과 %d쪽 / 2차 정밀 %d쪽 / 총 %.0f초"
            % (n - len(skipped), len(sus), time.time() - t0))
    if skipped:
        out_log("  ** 사전필터로 %d쪽을 건너뛰었다. 전수 검사가 아니다. **" % len(skipped))
    out_log("")
    out_log("  뒤집힘   %3d쪽   <- fix 로 보정된다" % len(bad))
    out_log("  보류     %3d쪽   <- 점수차가 작다. peek 로 직접 볼 것" % len(hold))
    out_log("  판정불가 %3d쪽   <- 4방향 전부 글자 없음(그림/빈 쪽)" % len(unk))
    out_log("")

    if bad:
        out_log("[뒤집힌 쪽]")
        for r in bad:
            out_log("  %4d쪽  %3d도 회전 필요  (점수차 %.1f배  %s)"
                    % (r["page"], r["need"], r["margin"], r.get("scores")))
            if r.get("dropped"):
                out_log("          세로박스라 제외한 후보 %s  (세로비율 %s)"
                        % (r["dropped"], r.get("talls")))
    if hold:
        out_log("[보류 — 사람이 확인]")
        for r in hold:
            out_log("  %4d쪽  후보 %3d도  점수차 %.2f배만  %s"
                    % (r["page"], r["need"], r["margin"], r.get("scores")))
    if unk:
        out_log("[판정불가]")
        out_log("  " + ", ".join(str(r["page"]) for r in unk[:40])
                + (" ..." if len(unk) > 40 else ""))

    # 참고용 분포 — 임계값이 이 책에 맞는지 사람이 판단할 수 있게
    ms = sorted(r["mean"] for r in rows if r["chars"] >= MIN_CHARS)
    if ms:
        q = lambda p: ms[min(len(ms) - 1, int(len(ms) * p))]
        out_log("")
        out_log("평균 신뢰도 분포  최저 %.3f / 25%% %.3f / 중앙 %.3f / 최고 %.3f  (기준 %.2f)"
                % (ms[0], q(.25), q(.5), ms[-1], CONF_MIN))

    return {"pdf": path, "pages": n,
            "fix": [{"page": r["page"], "need": r["need"]} for r in bad],
            "hold": [r["page"] for r in hold],
            "unknown": [r["page"] for r in unk]}


def targets(arg):
    if os.path.isdir(arg):
        return sorted(os.path.join(arg, f) for f in os.listdir(arg)
                      if f.lower().endswith(".pdf"))
    return [arg]


def cmd_scan(args):
    lang = "korean"
    dpi = DPI
    fast = "--fast" in args
    if "--lang" in args:
        lang = args[args.index("--lang") + 1]
    if "--dpi" in args:
        dpi = int(args[args.index("--dpi") + 1])
    src = args[0]
    log = []

    def out_log(s):
        log.append(str(s))
        io.open("_rotate.txt", "w", encoding="utf-8").write("\n".join(log))

    out_log("뒤집힌 페이지 검사   dpi=%d  lang=%s%s"
            % (dpi, lang, "  [--fast 사전필터]" if fast else ""))
    plans = [scan_pdf(p, lang, dpi, out_log, fast) for p in targets(src)]
    io.open("_rotate.json", "w", encoding="utf-8").write(
        json.dumps(plans, ensure_ascii=False, indent=1))
    total = sum(len(p["fix"]) for p in plans)
    out_log("")
    out_log("_rotate.json 에 보정 계획을 썼다. 보정할 쪽 %d개." % total)
    out_log("확인 후:  rotate.py fix \"%s\"" % src)
    print("scan done. see _rotate.txt (fix targets: %d)" % total)
    return 0


def cmd_fix(args):
    import pypdfium2 as pdfium
    plans = json.loads(io.open("_rotate.json", encoding="utf-8").read())
    done = 0
    for pl in plans:
        if not pl["fix"]:
            continue
        src = pl["pdf"]
        doc = pdfium.PdfDocument(src, autoclose=True)
        for item in pl["fix"]:
            pg = doc[item["page"] - 1]
            pg.set_rotation((pg.get_rotation() + item["need"]) % 360)
        stem, ext = os.path.splitext(src)
        dst = stem + "_정방향" + ext
        with open(dst, "wb") as f:
            doc.save(f)
        print("fixed %d page(s) -> %s" % (len(pl["fix"]), os.path.basename(dst)))
        done += len(pl["fix"])
    if not done:
        print("nothing to fix.")
    return 0


def cmd_peek(args):
    """판정이 애매한 쪽을 PNG로 뽑는다. Read 도구로 눈으로 본다."""
    src = args[0]
    doc = pdf_pages(src)
    for s in args[1:]:
        if s.startswith("--"):
            break
        i = int(s) - 1
        doc[i].render(scale=2).to_pil().save("_peek_%04d.png" % (i + 1))
        print("_peek_%04d.png" % (i + 1))
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    cmd, rest = sys.argv[1], sys.argv[2:]
    sys.exit({"scan": cmd_scan, "fix": cmd_fix, "peek": cmd_peek}[cmd](rest))
