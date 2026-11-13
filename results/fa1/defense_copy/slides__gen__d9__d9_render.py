"""Local preview of slide files: renders each section at 1920x1080 and reports flow content that runs past y = 964
(above the footer). Usage: python -I d9_render.py <artifact_root> <figs_dir> <out_dir> <id> [<id> ...]"""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

root, figs, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
ids = sys.argv[4:]
out.mkdir(parents=True, exist_ok=True)
BLOBS = {
    "b74f4e4f17f65bf292e4f6d3b17be8b5": "d9_model_comparison.png", "72eeee3abcc591b4dae3f03c7ca6ef42": "d9_siena_explained.png",
    "b76825005c7727c1658fa31a2acba7ad": "d9_hard_patients.png", "1c6a3f5a87644c35471994b1856b4daa": "d9_five_representations.png",
    "b8aad6d1173d83c0059bd144d66f07a5": "d9_knn_24_cases.png",
}
CSS = """<style>
@font-face{font-family:'Carlito';src:url('file:///usr/share/fonts/truetype/crosextra/Carlito-Regular.ttf');}
@font-face{font-family:'Carlito';font-weight:700;src:url('file:///usr/share/fonts/truetype/crosextra/Carlito-Bold.ttf');}
@font-face{font-family:'Carlito';font-style:italic;src:url('file:///usr/share/fonts/truetype/crosextra/Carlito-Italic.ttf');}
*{margin:0;box-sizing:border-box} body{width:1920px;height:1080px}
section{position:relative;width:1920px;height:1080px;overflow:hidden}
ul{padding-left:1.2em} table{border-collapse:collapse} td,th{border:1.5px solid #1E2430;padding:4px 8px;text-align:left;vertical-align:top}
aside{display:none} img{background:#eee}
</style>"""
JS = """() => { const s=document.querySelector('section'); let worst=0, who='';
 for (const el of s.querySelectorAll('*')) { const cs=getComputedStyle(el); if (cs.position==='absolute') continue;
   let p=el.parentElement, abs=false; while(p&&p!==s){ if(getComputedStyle(p).position==='absolute'){abs=true;break;} p=p.parentElement;}
   if (abs) continue; const r=el.getBoundingClientRect(); if (r.bottom>worst){worst=r.bottom; who=el.tagName+':'+(el.textContent||'').slice(0,50);} }
 return [Math.round(worst), who]; }"""
with sync_playwright() as pw:
    b = pw.chromium.launch()
    pg = b.new_page(viewport={"width": 1920, "height": 1080})
    for sid in ids:
        html = (root / f"project/slides/{sid}.html").read_text(encoding="utf-8")
        for k, v in BLOBS.items():
            html = html.replace(f"/_blob/{k}", (figs / v).resolve().as_uri())
        pg.set_content(f"<html><head>{CSS}</head><body>{html}</body></html>")
        pg.wait_for_timeout(150)
        worst, who = pg.evaluate(JS)
        flag = "OVERFLOW" if worst > 964 else "ok"
        print(f"{sid:5s} bottom {worst:4d} {flag}  {who if flag != 'ok' else ''}")
        pg.screenshot(path=str(out / f"{sid}.png"))
    b.close()
