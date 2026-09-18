import os,glob,io,sys
if len(__import__("sys").argv) < 3: print('usage: python _done.py NN "GATE line"'); raise SystemExit(2)
n=sys.argv[1]; line=sys.argv[2]
for f in [f'_ov{n}.png',f'_ch{n}c.txt','_chain.log','_t.txt','_rep.txt']+glob.glob(f'pdf/_fig_ch{n}_*.png'):
    if os.path.exists(f): os.remove(f)
io.open('_GATE.md','a',encoding='utf-8').write(line+'\n')
