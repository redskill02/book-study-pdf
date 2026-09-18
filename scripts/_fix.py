import re,io,sys
for f in sys.argv[1:]:
    s=io.open(f,encoding='utf-8').read()
    s=s.replace(' text-antml-anchor="middle"','').replace(' text-anchor="antml-middle"','')
    s=s.replace(' fill="#1f2937" fill="#1f2937"',' fill="#1f2937"').replace(' font:size=',' font-size=')
    s=re.sub(r'<text name="[a-z]" ','<text ',s)
    s=s.replace('</div>\n<parameter>\n<figcaption>','</div>\n<figcaption>')
    io.open(f,'w',encoding='utf-8').write(s)
