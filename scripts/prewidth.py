# -*- coding: utf-8 -*-
"""<pre> 줄 폭 검사. 한글 2 · ASCII 1 로 세어 LIMIT 넘는 줄을 찍는다.  python prewidth.py [limit]"""
import re,io,glob,sys,unicodedata,html
LIMIT=int(sys.argv[1]) if len(sys.argv)>1 else 106
def w(s):
    s=html.unescape(re.sub(r'<[^>]+>','',s))
    return sum(2 if unicodedata.east_asian_width(c) in 'WF' else 1 for c in s)
out=[]
for f in sorted(glob.glob('ch*.html'))+['_front.html']:
    try: h=io.open(f,encoding='utf-8').read()
    except: continue
    for pre in re.findall(r'<pre>(.*?)</pre>',h,re.S):
        for ln in pre.split('\n'):
            if w(ln)>LIMIT: out.append(f"{f} {w(ln):4d}  {ln[:70]}")
io.open('_prewidth.txt','w',encoding='utf-8').write('\n'.join(out))
print(len(out))
