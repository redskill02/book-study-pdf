# -*- coding: utf-8 -*-
"""0단계 — 원본 PDF의 텍스트 레이어를 믿을 수 있는지 판정한다.

**집필은커녕 변환을 시작하기 전에 반드시 돌린다.**

『프로그램은 어떻게 작동하는가』에서 원본 PDF에는 이미 OCR 텍스트가 들어 있었다.
그런데 그 텍스트가 "프로그램"을 "ㅍ무ㅋ램"으로, "뺄셈"을 "빨셈"으로 뭉개고 있었다.
그대로 썼다면 82쪽 전체가 오염된 채 나왔을 것이고, **읽기 전에는 아무도 몰랐을 것이다.**

가장 강력한 지표는 **고아 자모**다. 정상적인 한국어 텍스트에는 완성되지 않은
자모(ㅍ, ㅁ, ㅋ 같은 낱자)가 거의 나오지 않는다. 이것이 많으면 OCR이 글자를
조합하지 못하고 부서뜨렸다는 뜻이다.

사용법:
  python probe.py "<PDF 폴더 또는 파일>"                  # 원본 검사
  python probe.py "<PDF 폴더>" --compare "<재OCR md 폴더>"  # before/after 대조

출력: _probe.txt  (콘솔은 cp949라 한글이 깨진다. 반드시 cat으로 읽는다)
"""
import io, os, re, sys, glob

# 완성형이 아닌 한글 낱자 — 정상 텍스트에는 거의 없다
JAMO = re.compile(r"[ㄱ-ㆎ]")
# OCR이 글자를 못 만들었을 때 나오는 대체 문자
# □(체크박스)·●(불릿)은 정상 본문에서 쓰인다 — 넣지 마라.
# 넣었다가 박영훈 4권을 전부 "재 OCR 필수"로 오판했다.
# 실제로는 "□ Target: 누구에게 쓰는가?" 같은 체크리스트였다.
JUNK = re.compile(r"[�￼░-▓]")
# 한글 완성형
HANGUL = re.compile(r"[가-힣]")


def scan_text(t):
    """텍스트 한 덩어리의 손상 지표를 잰다."""
    han = len(HANGUL.findall(t))
    jamo = len(JAMO.findall(t))
    junk = len(JUNK.findall(t))
    return {
        "chars": len(t),
        "hangul": han,
        "jamo": jamo,
        "junk": junk,
        # 한글 1만 자당 고아 자모 개수 — 책 길이와 무관하게 비교된다
        "jamo_rate": (jamo * 10000.0 / han) if han else 0.0,
    }


def verdict(s, empty_ratio):
    """재OCR이 필요한지 판정한다."""
    reasons = []
    if s["jamo_rate"] >= 20:
        reasons.append("고아 자모 %.0f개/만자" % s["jamo_rate"])
    if s["junk"] >= 20:
        reasons.append("대체문자 %d개" % s["junk"])
    if empty_ratio >= 0.30:
        reasons.append("텍스트 없는 쪽 %.0f%%" % (empty_ratio * 100))
    if s["hangul"] == 0 and s["chars"] < 200:
        reasons.append("텍스트 레이어가 사실상 없음")

    if reasons:
        return "재OCR 필수", reasons
    if s["jamo_rate"] >= 5:
        return "재OCR 권장", ["고아 자모 %.1f개/만자 — 표본을 눈으로 확인할 것" % s["jamo_rate"]]
    return "레이어 양호", ["다만 MinerU의 구조화·이미지 추출은 여전히 필요하다"]


def probe_pdfs(target):
    import fitz
    pdfs = ([target] if target.lower().endswith(".pdf")
            else sorted(glob.glob(os.path.join(target, "*.pdf"))))
    rows, whole = [], ""
    total_pages = 0
    for p in pdfs:
        d = fitz.open(p)
        t = "\n".join(d.load_page(i).get_text() for i in range(d.page_count))
        imgs = sum(len(d.load_page(i).get_images(full=True)) for i in range(d.page_count))
        empty = sum(1 for i in range(d.page_count)
                    if len(d.load_page(i).get_text().strip()) < 20)
        s = scan_text(t)
        s.update(name=os.path.basename(p), pages=d.page_count,
                 mb=os.path.getsize(p) / 1048576.0, imgs=imgs, empty=empty,
                 sample=next((x.strip() for x in t.split("\n") if len(x.strip()) > 60), ""))
        rows.append(s)
        whole += t
        total_pages += d.page_count
        d.close()
    return rows, whole, total_pages


def probe_md(folder):
    """재OCR 결과(MinerU md)를 같은 지표로 잰다."""
    t = ""
    for f in glob.glob(os.path.join(folder, "**", "*.md"), recursive=True):
        t += io.open(f, encoding="utf-8").read()
    return scan_text(t), t


def main():
    target = sys.argv[1]
    cmp_dir = None
    if "--compare" in sys.argv:
        cmp_dir = sys.argv[sys.argv.index("--compare") + 1]

    rows, whole, total_pages = probe_pdfs(target)
    o = io.open("_probe.txt", "w", encoding="utf-8")

    o.write("0단계 — 원본 텍스트 레이어 품질 검사\n")
    o.write("=" * 72 + "\n\n")
    for r in rows:
        o.write("%s\n" % r["name"])
        o.write("  크기 %.0f MB · %d쪽 · 이미지 객체 %d개\n" % (r["mb"], r["pages"], r["imgs"]))
        o.write("  텍스트 %d자 (쪽당 %.0f자) · 한글 %d자 · 텍스트 없는 쪽 %d\n"
                % (r["chars"], r["chars"] / max(r["pages"], 1), r["hangul"], r["empty"]))
        o.write("  고아 자모 %d개 (%.1f개/만자) · 대체문자 %d개\n"
                % (r["jamo"], r["jamo_rate"], r["junk"]))
        if r["sample"]:
            o.write("  표본: %s\n" % r["sample"][:100])
        o.write("\n")

    tot = scan_text(whole)
    empty_ratio = sum(r["empty"] for r in rows) / float(max(total_pages, 1))
    v, reasons = verdict(tot, empty_ratio)

    o.write("=" * 72 + "\n")
    o.write("합계  %d쪽 · 한글 %d자 · 고아 자모 %d개 (%.1f개/만자)\n"
            % (total_pages, tot["hangul"], tot["jamo"], tot["jamo_rate"]))
    o.write("판정  >>> %s <<<\n" % v)
    for x in reasons:
        o.write("      - %s\n" % x)

    if v.startswith("재OCR"):
        o.write("\n  이 레이어를 그대로 쓰면 안 된다. MinerU로 재OCR한 뒤\n")
        o.write("  --compare 로 다시 돌려 before/after를 확인한다.\n")

    if cmp_dir:
        after, atext = probe_md(cmp_dir)
        o.write("\n" + "=" * 72 + "\n")
        o.write("재OCR 전후 대조\n")
        o.write("%-18s %14s %14s\n" % ("항목", "원본 레이어", "재OCR"))
        o.write("-" * 50 + "\n")
        o.write("%-18s %14d %14d\n" % ("한글 글자수", tot["hangul"], after["hangul"]))
        o.write("%-18s %14d %14d\n" % ("고아 자모", tot["jamo"], after["jamo"]))
        o.write("%-18s %14.1f %14.1f\n" % ("자모/만자", tot["jamo_rate"], after["jamo_rate"]))
        o.write("%-18s %14d %14d\n" % ("대체문자", tot["junk"], after["junk"]))
        o.write("-" * 50 + "\n")
        # 원본이 이미 깨끗하면 자모율로는 아무것도 못 가린다.
        # 이 지표는 '조합 실패'만 잡고 '다른 글자로 잘못 읽은 것'은 못 잡는다.
        # 『무조건 통하는 카피 법칙』 원본은 자모 0개였는데
        # '통하는'을 '토하느'로, '파악'을 '가악'으로 읽고 있었다.
        if tot["jamo_rate"] < 2.0:
            o.write("?? 원본 자모율이 이미 0에 가깝다(%.1f). 이 대조로는 판정할 수 없다.\n"
                    % tot["jamo_rate"])
            o.write("   고아 자모는 '조합 실패'만 잡는다. 멀쩡한 다른 글자로 잘못 읽은 것은\n")
            o.write("   어떤 자모 지표로도 안 잡힌다.\n")
            o.write("   할 일 — 원본 레이어를 눈으로 훑어 오인식 낱말 2~3개를 뽑고,\n")
            o.write("   재OCR 결과에서 그 낱말이 몇 번 남았는지 직접 센다.\n")
        elif after["jamo_rate"] < tot["jamo_rate"] * 0.5 or after["jamo"] == 0:
            o.write("→ 재OCR이 유효하다. 재OCR 결과로 집필한다.\n")
        else:
            o.write("!! 재OCR이 개선을 못 만들었다. 원본 스캔 품질 자체를 의심하고\n")
            o.write("   집필 전에 사용자에게 알린다.\n")

        # 원본에서만 깨져 있던 대표 어휘가 실제로 복구됐는지 표본 확인
        o.write("\n[표본 대조] 원본에서 자모가 섞였던 어절이 재OCR에서 복구됐는지\n")
        broken = sorted(set(re.findall(r"[가-힣]*[ㄱ-ㆎ][가-힣ㄱ-ㆎ]*", whole)),
                        key=lambda s: -len(s))[:12]
        if not broken:
            o.write("  (원본에 깨진 어절이 없다)\n")
        for b in broken:
            o.write("  %-14s 원본 %3d회 → 재OCR %d회\n" % (b, whole.count(b), atext.count(b)))

    o.close()
    print("[OK] probed -> read _probe.txt with cat")


main()
