import sys,io,re
p=sys.argv[1]; s=io.open(p,encoding='utf-8').read()
s=s.replace('text-anchor="antml:middle" ','').replace('&mbox;','').replace('<parameter>','')
s=re.sub(r'<invoke (?:name|class)="(\w+)">', lambda m: '<div class="%s">' % m.group(1), s)
io.open(p,'w',encoding='utf-8').write(s)
print('invoke' in s, len(re.findall(r'<div class="qa">',s)), s.count('<div class="">'))
