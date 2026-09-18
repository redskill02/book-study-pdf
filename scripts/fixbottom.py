# -*- coding: utf-8 -*-
"""rect 아래로 글자가 잘리는 곳을 찾아 rect 높이(그리고 필요하면 viewBox)를 키운다.

  좌우 넘침은 svgfit이, 세로 겹침은 linegap이 잡지만
  '상자 바닥에 baseline이 붙어 descender가 잘리는' 경우는 아무도 안 잡는다.
  실제로 4권 전체에서 41건이 나왔다.
아래 rect가 바로 이어지면 건드리지 않고 건너뛴다(SKIP).
"""
import io,re,sys,glob,os
RECT=re.compile(r'<rect[^>]*/>')
SVG=re.compile(r'<svg[^>]*>.*?</svg>',re.S)
TEXT=re.compile(r'<text([^>]*)>(.*?)</text>',re.S)
def at(s,n,d=None):
    m=re.search(r'\s%s="([\d.]+)"'%n,s); return float(m.group(1)) if m else d
def setattr_(s,n,v):
    v=("%g"%v)
    return re.sub(r'(\s%s=")[\d.]+(")'%n, lambda m:m.group(1)+v+m.group(2), s, count=1)

def fix(path, report):
    h=io.open(path,encoding="utf-8").read(); changed=0
    def do_svg(m):
        nonlocal changed
        blk=m.group(0); vb=re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"',blk)
        vh=float(vb.group(2)) if vb else None
        rects=[(r.start(),r.group(0)) for r in RECT.finditer(blk)]
        info=[(at(r,"x"),at(r,"y"),at(r,"width"),at(r,"height"),pos,r) for pos,r in rects]
        info=[i for i in info if None not in i[:4]]
        grow={}
        for t in TEXT.finditer(blk):
            a=t.group(1); tx=at(a,"x"); ty=at(a,"y"); fs=at(a,"font-size",10)
            if tx is None or ty is None: continue
            cand=[i for i in info if i[0]-3<=tx<=i[0]+i[2]+3 and i[1]<ty<=i[1]+i[3]+fs]
            if not cand: continue
            rx,ry,rw,rh,pos,raw=min(cand,key=lambda i:i[2]*i[3])
            need=fs*0.38-(ry+rh-ty)
            if need<=0.5: continue
            d=max(grow.get(pos,(0,))[0], round(need+1.5))
            grow[pos]=(d,rx,ry,rw,rh,raw)
        if not grow: return blk
        # 아래 rect와 부딪히는지 확인
        out=blk
        for pos,(d,rx,ry,rw,rh,raw) in sorted(grow.items(), reverse=True):
            clash=[i for i in info if i[4]!=pos and i[1]>=ry+rh and i[1]<ry+rh+d
                   and not(i[0]+i[2]<rx or i[0]>rx+rw)]
            if clash:
                report.append("SKIP %s  rect y=%g (+%g 하면 아래 상자와 겹침)"%(path,ry,d)); continue
            out=out[:pos]+setattr_(raw,"height",rh+d)+out[pos+len(raw):]
            changed+=1
            report.append("  +%g  %s  rect y=%g h=%g->%g"%(d,os.path.basename(path),ry,rh,rh+d))
            if vh is not None and ry+rh+d > vh-4:
                out=re.sub(r'(viewBox="0 0 [\d.]+ )[\d.]+(")',
                           lambda mm:mm.group(1)+("%g"%(ry+rh+d+8))+mm.group(2), out, count=1)
        return out
    h2=SVG.sub(do_svg,h)
    if changed: io.open(path,"w",encoding="utf-8").write(h2)
    return changed

rep=[]; tot=0
for d in sys.argv[1:]:
    for f in sorted(glob.glob(os.path.join(d,"ch*.html")))+[os.path.join(d,"_front.html")]:
        if os.path.exists(f): tot+=fix(f,rep)
io.open("_fixbottom.txt","w",encoding="utf-8").write("\n".join(rep)+"\n총 %d건 보정\n"%tot)
print(tot)
