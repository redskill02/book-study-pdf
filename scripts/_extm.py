# -*- coding: utf-8 -*-
# MinerU content_list 기반 추출: python _extm.py NN a b [OFF]  (책 a~b쪽, 책 = pdf + OFF)
import io, json, re, sys
if len(__import__("sys").argv) < 4: print('usage: python _extm.py NN a b [OFF] [V]'); raise SystemExit(2)
n, a, b = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
OFF = int(sys.argv[4]) if len(sys.argv) > 4 else 2
V = sys.argv[5] if len(sys.argv) > 5 else '1'
L = json.load(io.open('out%s/src%s/ocr/src%s_content_list.json' % (V, V, V), encoding='utf-8'))
out = []
for bk in range(a, b + 1):
    pi = bk - OFF - 1  # page_idx 0-based
    out.append('----- 책 %d쪽 (pdf %d) -----' % (bk, pi + 1))
    for x in L:
        if x.get('page_idx') != pi: continue
        t = x.get('type')
        if t in ('text', 'list'):
            s = x.get('text', '')
            if isinstance(s, list): s = ' / '.join(s)
            if t == 'list':
                items = x.get('list_items') or []
                if items: s = ' '.join(i.strip() for i in items)
            s = s.strip()
            if len(re.findall('[가-힣]', s)) == 0 and len(s) < 40: continue
            out.append(s)
        elif t == 'table':
            cap = ' '.join(x.get('table_caption') or [])
            body = x.get('table_body', '')
            body = re.sub(r'<[^>]+>', ' | ', body)
            body = re.sub(r'(\s*\|\s*)+', ' | ', body).strip()
            out.append('[표] ' + cap + ' :: ' + body[:1500])
        elif t in ('image', 'chart'):
            cap = ' '.join(x.get('image_caption') or []) + ' ' + ' '.join(x.get('image_footnote') or [])
            out.append('[그림 %s] %s' % (x.get('img_path', ''), cap.strip()))
        elif t == 'code':
            cap = ' '.join(x.get('code_caption') or [])
            body = x.get('code_body', '').replace('```python', '').replace('```', '').strip()
            out.append('[CODE %s]' % cap); out.append(body[:2500]); out.append('[/CODE]')
        elif t == 'header':
            pass
io.open('_ch%sc.txt' % n, 'w', encoding='utf-8').write('\n'.join(out))
print(len(out))
