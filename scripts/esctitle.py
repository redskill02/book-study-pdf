# -*- coding: utf-8 -*-
"""SVG <title> 안의 꺾쇠(<class 'int'>, <table …> 등)를 이스케이프한다 (pitfalls #93). python esctitle.py chNN.html"""
import io, re, sys
p = sys.argv[1]; s = io.open(p, encoding='utf-8').read()
head, sep, rest = s.partition('<svg')
def f(m):
    b = m.group(1)
    if '<' not in b: return m.group(0)
    return '<title>' + b.replace('<', '&lt;').replace('>', '&gt;') + '</title>'
rest2, n = re.subn(r'<title>(.*?)</title>', f, rest, flags=re.S)
io.open(p, 'w', encoding='utf-8').write(head + sep + rest2)
print('esctitle', n)
