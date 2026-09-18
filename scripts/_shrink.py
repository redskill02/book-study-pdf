# -*- coding: utf-8 -*-
"""svgfit 지적분을 font-size 축소로 해소 (autofit 는 MIN 7.0 이라 작은 글자엔 무력)."""
import re, sys
from html import unescape
fn=sys.argv[1]
FLOOR=float(sys.argv[2]) if len(sys.argv)>2 else 3.8
hits=[]
for ln in open('_svgfit.txt',encoding='utf-8'):
    if fn in ln and 'pt' in ln and '"' in ln:
        m=re.search(r'\+([\d.]+) pt\s+"(.*)"',ln)
        if m: hits.append((float(m.group(1)),m.group(2)))
s=open(fn,encoding='utf-8').read()
n=0
for over,pre in hits:
    pre=pre.rstrip()
    for m in re.finditer(r'<text([^>]*)>(.*?)</text>',s):
        txt=unescape(re.sub(r'<[^>]+>','',m.group(2)))
        if txt.startswith(pre[:18]):
            attrs=m.group(1)
            fm=re.search(r'font-size="([\d.]+)"',attrs)
            if not fm: break
            fs=float(fm.group(1))
            # 대략 박스 폭 210 기준으로 비례 축소, 여유 2%
            new=max(FLOOR, round(fs*(200.0/(200.0+over))-0.05,1))
            if new<fs:
                s=s[:m.start(1)]+attrs.replace(fm.group(0),f'font-size="{new}"')+s[m.end(1):]
                n+=1
            break
open(fn,'w',encoding='utf-8').write(s)
print('shrunk',n)
