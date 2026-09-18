# -*- coding: utf-8 -*-
"""<g font-size=...> 의 텍스트 속성을 각 <text> 로 내린다 (linegap/svgfit 이 <text> 속성만 읽음)."""
import io,re,sys
p=sys.argv[1]; s=io.open(p,encoding='utf-8').read()
G=re.compile(r'<g([^>]*)>(.*?)</g>', re.S)
KEYS=('font-size','font-weight','fill','text-anchor')
def fix(m):
    attrs, body = m.group(1), m.group(2)
    vals={k:re.search(r'\b%s="([^"]+)"'%k,attrs) for k in KEYS}
    if not vals['font-size'] and not vals['text-anchor'] and not vals['font-weight']:
        return m.group(0)   # 도형용 g (fill/stroke) 는 건드리지 않는다
    def tf(t):
        a=t.group(1)
        for k in KEYS:
            if vals[k] and ('%s='%k) not in a: a+=' %s="%s"'%(k,vals[k].group(1))
        return '<text'+a+'>'
    body=re.sub(r'<text([^>]*)>',tf,body)
    for k in KEYS:
        attrs=re.sub(r'\s*\b%s="[^"]+"'%k,'',attrs)
    return '<g'+attrs+'>'+body+'</g>'
s2=G.sub(fix,s); io.open(p,'w',encoding='utf-8').write(s2); print(len(s),'->',len(s2))
