import sys,glob,re
from PIL import Image, ImageDraw
a,b,out=int(sys.argv[1]),int(sys.argv[2]),sys.argv[3]
cols=int(sys.argv[4]) if len(sys.argv)>4 else 4
V=sys.argv[5] if len(sys.argv)>5 else 'v1'
files=[]
for f in sorted(glob.glob('crops/%s_p*.jpg'%V)):
    p=int(re.search(r'p(\d{3})',f).group(1))
    if a<=p<=b: files.append(f)
W=420; thumbs=[]
for f in files:
    im=Image.open(f); w,h=im.size; t=im.resize((W,int(h*W/w)))
    d=ImageDraw.Draw(t); d.rectangle((0,0,110,18),fill='yellow'); d.text((3,3),f[6:-4],fill='black')
    thumbs.append(t)
rowh=max(t.size[1] for t in thumbs)
rows=(len(thumbs)+cols-1)//cols
m=Image.new('RGB',(W*cols,rowh*rows),'white')
for i,t in enumerate(thumbs): m.paste(t,((i%cols)*W,(i//cols)*rowh))
m.save(out); print(len(thumbs),m.size)
