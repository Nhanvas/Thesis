"""Write slide files (deploy, with /_blob/ ids) and a local preview; render PNGs and report overflow."""
import sys, os, json, re, asyncio, importlib
sys.path.insert(0, os.path.dirname(__file__))
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
IMG = {  # name -> local file
 "eeg_cap": "img/p4-000.png", "eeg_onset": "img/p4-001.png",
 "fig7_cd": "img/fig7_cd.png", "fig7_b": "img/fig7_b.png", "fig10": "../in_figs/Fig10.png",
 "fig14": "img/fig14_grid.png", "fig15": "../in_figs/Fig15.png", "cpd_fig": "img/b07_cpd.png",
 "F1map": "figs/F1_annotation_map.png", "A2dur": "figs/A2_durations.png",
}
for f in os.listdir(os.path.join(ROOT, "eq")):
    IMG[f[:-4]] = "eq/" + f
BLOBS = json.load(open(os.path.join(ROOT, "blobs.json"))) if os.path.exists(os.path.join(ROOT, "blobs.json")) else {}

def collect(mods):
    S = {}
    for m in mods:
        S.update(importlib.import_module(m).S)
    return S

def fill(html, local):
    def rep(m):
        k = m.group(1)
        if local:
            return "file://" + os.path.join(ROOT, IMG[k])
        if k not in BLOBS:
            raise SystemExit(f"no blob for {k}")
        return BLOBS[k]
    return re.sub(r"\{\{(\w+)\}\}", rep, html)

CSS = """*{margin:0;padding:0;box-sizing:border-box}body{background:#888}
section{position:relative;width:1920px;height:1080px;overflow:hidden;margin:0 0 20px 0}
p{font-size:32px;line-height:1.4}h2{font-size:64px}h3{font-size:44px}
ul{padding-left:1.1em}table{border-collapse:collapse}td,th{border:1px solid #D5DCE4;padding:.35em .6em;text-align:left;vertical-align:top}
th{font-weight:700}aside{display:none}
@font-face{font-family:'Cabin';font-weight:400;src:url(FONT/cabin-latin-400-normal.woff2)}
@font-face{font-family:'Cabin';font-weight:500;src:url(FONT/cabin-latin-500-normal.woff2)}
@font-face{font-family:'Cabin';font-weight:600;src:url(FONT/cabin-latin-600-normal.woff2)}
@font-face{font-family:'Cabin';font-weight:700;src:url(FONT/cabin-latin-700-normal.woff2)}
"""

async def shoot(order, S, outdir):
    from playwright.async_api import async_playwright
    font = "file://" + os.path.join(ROOT, "fonts/node_modules/@fontsource/cabin/files")
    page_html = "<html><head><meta charset=\"utf-8\"><style>" + CSS.replace("FONT", font) + "</style></head><body>" + \
        "\n".join(fill(S[k], True) for k in order) + "</body></html>"
    open(os.path.join(ROOT, "preview/all.html"), "w").write(page_html)
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport={"width": 1920, "height": 1080})
        await pg.goto("file://" + os.path.join(ROOT, "preview/all.html"))
        await pg.wait_for_timeout(800)
        for k in order:
            el = await pg.query_selector(f"section#{k}")
            await el.screenshot(path=os.path.join(outdir, f"{k}.png"))
            # overflow check: flow descendants below y=962 or beyond x=1880; text boxes with clipped content
            issues = await pg.evaluate("""(id)=>{const s=document.getElementById(id);const r0=s.getBoundingClientRect();const out=[];
              for(const el of s.querySelectorAll('*')){const cs=getComputedStyle(el);if(cs.position==='absolute')continue;
                let anc=el.parentElement,pinned=false;while(anc&&anc!==s){if(getComputedStyle(anc).position==='absolute'){pinned=true;break}anc=anc.parentElement}
                if(pinned)continue;const r=el.getBoundingClientRect();if(r.width===0)continue;
                if(r.bottom-r0.top>962||r.right-r0.left>1884)out.push(el.tagName+':'+(el.textContent||el.alt||'').slice(0,40)+' b='+Math.round(r.bottom-r0.top)+' r='+Math.round(r.right-r0.left));
                if((el.tagName==='P'||el.tagName==='TD'||el.tagName==='TH')&&el.scrollWidth>el.clientWidth+2)out.push('WIDE '+el.tagName+':'+el.textContent.slice(0,40));}
              return out.slice(0,6)}""", k)
            print(k, "OK" if not issues else issues)
        await b.close()

if __name__ == "__main__":
    mods = sys.argv[1].split(",")
    S = collect(mods)
    order = [k for k in (sys.argv[2].split(",") if len(sys.argv) > 2 else S.keys())]
    os.makedirs(os.path.join(ROOT, "preview"), exist_ok=True)
    asyncio.run(shoot(order, S, os.path.join(ROOT, "preview")))
