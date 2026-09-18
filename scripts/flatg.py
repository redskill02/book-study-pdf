import sys,io,re
# Flatten nested <g> inside <g>: push inner g attrs onto its <text> children (if absent), drop inner g tags.
p=sys.argv[1]; s=io.open(p,encoding='utf-8').read()
tokens=re.split(r'(<g\b[^>]*>|</g>)',s)
res=[];stack=[];n=0
for t in tokens:
    if t.startswith('<g'):
        if stack:
            attrs=dict(re.findall(r'(\S+?)="([^"]*)"',t)); stack.append(attrs); n+=1; continue
        stack.append(None); res.append(t)
    elif t=='</g>':
        a=stack.pop() if stack else None
        if a is None: res.append(t)
    else:
        if stack and stack[-1] is not None:
            attrs=stack[-1]
            def fix(m):
                tag=m.group(0)
                for k,v in attrs.items():
                    if k+'=' not in tag:
                        if tag.endswith('/>'): tag=tag[:-2]+' %s="%s"/>'%(k,v)
                        else: tag=tag[:-1]+' %s="%s">'%(k,v)
                return tag
            t=re.sub(r'<(?:text|rect|circle|line|path|polygon|ellipse)\b[^>]*>',fix,t)
        res.append(t)
io.open(p,'w',encoding='utf-8').write(''.join(res)); print('flattened',n)
