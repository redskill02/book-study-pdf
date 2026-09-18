# -*- coding: utf-8 -*-
"""차트 크롭 위에 얹을 한글 주석 SVG를 만든다.

크롭마다 손으로 좌표를 잡되, 흰 깔개(rect) 폭 계산과 태그 조립은 여기서 한다.
40장 넘게 반복하는 작업이라 규격을 고정해 둔다.

    from anno import overlay, L
    print(overlay(1598, 2320, [
        L(566,1962, 626,1938, "거래량 급증 — 여기서 주목"),      # 화살표 + 라벨
        L(None,None, 850,1397, "24.5달러 500주 매수", arrow=(791,1383,838,1383)),
    ]))

규칙
    - 원본에 이미 A~D 같은 마커가 있으면 링을 그리지 않는다. 화살표만 붙인다.
    - 마커는 한 크롭에 3~4개까지. 그 이상은 캡션으로 넘긴다.
    - 라벨은 반드시 흰 깔개 위에 올린다. 격자선 위에서도 읽혀야 한다.
"""


def width_of(s, fs):
    """한글 1.0 · 영숫자 0.56 · 공백 0.35 기준의 대략 폭(px)."""
    u = 0.0
    for c in s:
        if c == " ":
            u += 0.35
        elif "가" <= c <= "힣" or "ㄱ" <= c <= "ㆎ":
            u += 1.0
        elif c in "—–…·":
            u += 0.9
        else:
            u += 0.56
    return u * fs


class L(object):
    """라벨 하나. arrow=(x1,y1,x2,y2) 를 주면 화살표를 함께 그린다."""
    def __init__(self, tx, ty, text, fs=44, arrow=None, anchor="start", box=None):
        self.tx, self.ty, self.text, self.fs = tx, ty, text, fs
        self.arrow, self.anchor, self.box = arrow, anchor, box


def overlay(vw, vh, items, pad=10):
    o = ['<svg class="anno" viewBox="0 0 %d %d" preserveAspectRatio="none">' % (vw, vh),
         '<defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" '
         'markerWidth="5" markerHeight="5" orient="auto-start-reverse">'
         '<path d="M0,0 L10,5 L0,10 z" fill="#b91c1c"/></marker></defs>']
    for it in items:
        if it.box:                                   # 구간을 네모로 감쌀 때
            x, y, w, h = it.box
            o.append('<rect x="%d" y="%d" width="%d" height="%d" rx="8" class="bx"/>'
                     % (x, y, w, h))
        if it.arrow:
            x1, y1, x2, y2 = it.arrow
            o.append('<line x1="%d" y1="%d" x2="%d" y2="%d" class="ar"/>' % (x1, y1, x2, y2))
        if it.text:
            w = width_of(it.text, it.fs)
            x0 = it.tx - pad if it.anchor == "start" else it.tx - w - pad
            if it.anchor == "middle":
                x0 = it.tx - w / 2 - pad
            o.append('<rect x="%.0f" y="%.0f" width="%.0f" height="%.0f" rx="5" class="lbbg"/>'
                     % (x0, it.ty - it.fs * 0.84, w + pad * 2, it.fs * 1.18))
            o.append('<text x="%d" y="%d" font-size="%s" class="lb"%s>%s</text>'
                     % (it.tx, it.ty, it.fs,
                        '' if it.anchor == "start" else ' text-anchor="%s"' % it.anchor,
                        it.text))
    o.append('</svg>')
    return "\n".join(o)
