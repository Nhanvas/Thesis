import sys, os
from PIL import Image, ImageDraw
ids = sys.argv[2].split(","); out = sys.argv[1]
W, H = 960, 540
sh = Image.new("RGB", (W * 2 + 10, H * ((len(ids) + 1) // 2) + 10 * ((len(ids) + 1) // 2)), "#888")
for j, k in enumerate(ids):
    im = Image.open(f"preview/{k}.png").convert("RGB").resize((W, H))
    d = ImageDraw.Draw(im); d.rectangle([0, 0, 50, 18], fill="yellow"); d.text((3, 3), k, fill="black")
    sh.paste(im, ((j % 2) * (W + 10), (j // 2) * (H + 10)))
sh.save(out)
