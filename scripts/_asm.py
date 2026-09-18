import io, re, sys, os
f = sys.argv[1]
h = io.open(f, encoding='utf-8').read()
b = f.replace('ch', '_ch', 1).replace('.html', '_b.html')
if os.path.exists(b):
    h += io.open(b, encoding='utf-8').read(); os.remove(b)
for a, c in [(' text-antml-anchor="middle"', ' text-anchor="middle"'), ('antml:middle', 'middle'),
             (' text-anchor="middle" text-anchor="middle"', ' text-anchor="middle"'),
             ('</text></div>', '</div>'), (' name="x"', '')]:
    h = h.replace(a, c)
io.open(f, 'w', encoding='utf-8').write(h)
h1 = re.search(r'<h1>(.*?)</h1>', h, re.S).group(1)
h1 = re.sub(r'&[a-z]+;', 'x', h1)
print('h1', len(h1), 'figure', h.count('<figure>'), 'qa', h.count('class="qa"'), 'a', h.count('<div class="a">'))
print(re.findall(r'도표 (\d+) &mdash;', h))
