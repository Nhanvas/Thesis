import json, re, sys, os
base='/tmp/claude-0/-home-claude/3a874df3-3a87-50a5-adf3-824bd0eda443/scratchpad'
out=base+'/assets'
d=json.load(open(base+'/icons/hi/package/icons.json'))
W=d.get('width',48); H=d.get('height',48)
hi={'neurology':'#3D2A4D','hospitalized':'#3D2A4D','doctor':'#3D2A4D','laptop':'#3D2A4D','medicines':'#146F70',
    'neuro-surgery':'#146F70','medical-search':'#146F70','database':'#3D2A4D','people':'#3D2A4D','globe':'#3D2A4D','calendar':'#3D2A4D','hospital':'#3D2A4D'}
for n,c in hi.items():
    ic=d['icons'][n]; w=ic.get('width',W); h=ic.get('height',H)
    body=ic['body'].replace('currentColor',c)
    open(f'{out}/hi_{n}.svg','w').write(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w*8}" height="{h*8}">{body}</svg>')
si=json.load(open(base+'/icons/si/package/data/simple-icons.json')) if os.path.exists(base+'/icons/si/package/data/simple-icons.json') else None
logos=['react','vite','tailwindcss','python','fastapi','pytorch','pyg','scikitlearn','numpy','sqlite']
hexes={}
if si:
    for e in (si if isinstance(si,list) else si.get('icons',[])):
        hexes[e.get('slug') or e['title'].lower()]=e['hex']
for l in logos:
    s=open(f'{base}/icons/si/package/icons/{l}.svg').read()
    col='#'+hexes.get(l,'3D2A4D')
    s=s.replace('<svg ','<svg width="192" height="192" fill="'+col+'" ',1)
    open(f'{out}/logo_{l}.svg','w').write(s)
    print(l,col)
