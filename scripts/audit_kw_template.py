# -*- coding: utf-8 -*-
"""역방향 대조 템플릿 — 책마다 CLAIMS 만 바꿔서 작업 폴더에 복사해 쓴다.
   (원본: 설득의 법칙. 아래 CLAIMS 는 예시이므로 그 책의 것으로 교체한다.)
   자세한 이유는 references/pitfalls.md 함정 #33.

audit.py [A]는 '원문 → 노트' 방향이라 내가 지어낸 말은 못 잡는다.
이 검사는 반대 방향이다.

주의 — 대상을 <b> 강조 전체로 잡으면 안 된다. 한 번 그렇게 했다가
      "Q1 →", "10개 이상", "(9장·10장)" 같은 내 글이 전부 검사 대상이 되어
      413건 중 343건이 '없음'으로 떴고 전부 오탐이었다.
      검사 대상은 '원문의 것이라고 내가 주장한 말'뿐이다 —
      효과 이름과 수치. 둘 다 틀리면 학습자가 그대로 외운다.
"""
import io, glob, os, re

W = os.path.dirname(os.path.abspath(__file__))

# 노트가 "원문에 있다"고 주장하는 것들. 표기가 다를 수 있는 것은 (표시어, 원문표기).
CLAIMS = [
    # ── 1~3장
    "태도", "확증 편향", "공정한 세상", "소유 효과", "이해당사자",
    "자기중심", "스포트라이트", "공감", "거울 뉴런",
    # ── 4~6장
    "환심 사기", "휴리스틱", "벤저민 프랭클린", "상호성의 원리",
    "처리 유창성", "유사성의 원칙", "인사이데",          # 원문 OCR 표기
    "단순 노출 효과", "상호적 애착", "동기", "음식심리학",
    "매력 자본", "캐서린 하킴", "소크라테스 방식", "유령 칭찬",
    "역설적 개입", "로젠탈", "우월함 망상", "워비곤", "이름 효과",
    "보상의 숨겨진 대가", "채팀하우스",                   # 원문 OCR 표기
    # ── 7~8장
    "세네카", "최근 효과", "첫머리 효과", "부정적 상태",
    "후광 효과", "손다이크", "올포트", "뇌섬엽",
    # ── 9장
    "정박 효과", "점화 효과", "책임감 분산", "리액턴스",
    "인지부조화", "외적 합리화", "문간에 발", "머리부터",
    "조건형성", "간헐적 강화", "소거",
    # ── 10장
    "청중 관리", "명령적 규범", "집단 압력", "정교화 가능성",
    "중심 경로", "주변 경로", "밀그램", "폭스 박사", "바벨라스",
    "예일", "가용성", "진리 효과", "페피노",
    # ── 수치 (틀리면 학습자가 그대로 외운다)
    # 오답 보기(distractor)의 수치는 CLAIMS 에 넣지 않는다 —
    # 원문에 없는 것이 정상이라 넣으면 반드시 오탐이 된다. 실제로 겪었다.
    "250억", "95퍼센트", "20페이지", "24페이지",
    "일흔 명", "620", "1000", "1만", "10만", "17유로",
    "400볼트", "53개국", "20배", "10센트", "5센티미터",
    "월 요금이 17유로", "여덟 번", "열다섯 번", "스물다섯",
]

# 원문 md + 삼켜졌다 복원한 원본 텍스트 레이어까지 합쳐서 본다
PUNCT = r"[\s,.·’‘“”'\"\-–—/()（）\[\]:;?!~%]"

def norm(s):
    """구두점·공백만 지운다. 태그 제거는 하지 않는다."""
    return re.sub(PUNCT, "", s)

def norm_html(s):
    """노트(HTML)에만 쓴다 — 태그가 낱말을 가르기 때문.
       원문(OCR)에 이걸 쓰면 안 된다: OCR이 만들어낸 깨진 '<'와 '>' 사이의
       실제 본문이 통째로 삭제되어, 원문에 있는 말이 '없음'으로 뜬다.
       (설득의 심리학 3에서 4,029자가 삼켜져 '피크엔드 효과'가 오탐으로 떴다.)"""
    s = re.sub(r"<[^>]+>", "", s)
    s = re.sub(r"&[a-z]+;", "", s)
    return norm(s)


src = "\n".join(io.open(f, encoding="utf-8").read()
                for f in sorted(glob.glob(os.path.join(W, "out", "src", "ocr", "*.md"))))
for extra in ("_raw.txt", "_holetext.txt"):
    p = os.path.join(W, extra)
    if os.path.exists(p):
        src += io.open(p, encoding="utf-8").read()
src = norm(src)

if len(src) < 20000:
    raise SystemExit(
        u"!! 원문을 제대로 못 읽었다 (%d자). "
        u"out/src/ocr/*.md 경로를 확인해라. "
        u"이 상태로 돌리면 '전부 원문에 없음'이라는 "
        u"거짓 경보가 쌀아진다 (함정 #41)." % len(src))

notes = "".join(io.open(f, encoding="utf-8").read()
                for f in sorted(glob.glob(os.path.join(W, "*.html"))))
notes_n = norm_html(notes)

missing, unused = [], []
for c in CLAIMS:
    k = norm(c)
    if k not in notes_n:
        unused.append(c)          # 노트에 안 쓴 말은 검사 의미가 없다
    elif k not in src:
        missing.append(c)

out = ["역방향 대조 — 노트가 '원문의 것'이라 주장한 말이 원문에 있는가", "=" * 66,
       "   검사 대상 %d개 (효과 이름 + 수치)" % len(CLAIMS),
       "   노트에 실제로 쓰인 것 %d개" % (len(CLAIMS) - len(unused)),
       "=" * 66]
if missing:
    out += ["", "!! 원문에서 못 찾음 — 지어냈거나 표기가 다르다"] + \
           ["   %s" % m for m in missing]
else:
    out += ["", "   원문에 전부 있다"]
if unused:
    out += ["", "(참고) 노트에서 안 쓴 항목 — 검사 대상에서 빠졌다"] + \
           ["   %s" % u for u in unused]
io.open(os.path.join(W, "_audit_kw.txt"), "w", encoding="utf-8").write("\n".join(out))
print("[%s] audit_kw -> read _audit_kw.txt" % ("OK" if not missing else "!!"))
