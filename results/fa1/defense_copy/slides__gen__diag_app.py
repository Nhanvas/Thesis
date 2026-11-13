#!/usr/bin/env python
"""D13 -- SzScan architecture (report Section 2.9.2, Fig. 10; facts from web_demo/ via APP_FACTS.md sections 1-3).
Logos: Simple Icons 13.21.0 (CC0), brand colours from its metadata. Run: python diag_app.py out/D13_app.png"""
import sys
from diag_lib import *

TL = "/home/claude/slidegen/assets/tools/"
d = D(9.4, 6.9)


NAME = {"react": "React", "vite": "Vite", "tailwindcss": "Tailwind", "python": "Python", "fastapi": "FastAPI",
        "pytorch": "PyTorch", "pyg": "PyG", "scikitlearn": "scikit-learn", "numpy": "NumPy", "sqlite": "SQLite"}


def logos(names, x0, y, s=0.42, gap=0.1, lab=True):
    for i, n in enumerate(names):
        x = x0 + i * (s + gap)
        d.image(TL + n + ".png", x, y - s / 2 + 0.08, x + s, y + s / 2 + 0.08, frame=False)
        if lab:
            d.txt(x + s / 2, y - s / 2 - 0.06, NAME[n], 10.5, color=GREY)


# whole machine
d.group(0.08, 0.08, 9.32, 6.82, "One hospital workstation: nothing leaves the machine", c="#FFFFFF", ec="#1F6FB2")

# browser
d.box(4.7, 5.85, 8.9, 0.95, "", c="#E8F1FA")
d.txt(0.4, 6.14, "Browser", 16, ha="left", fontweight="bold")
logos(["react", "vite", "tailwindcss"], 0.42, 5.69, s=0.32, gap=0.34)
d.txt(2.25, 5.85, "Review screens: score timeline, EEG around each event,\nchannel panel; Accept / Reject / Uncertain", 14, ha="left")
d.arrow([(4.7, 5.36), (4.7, 5.02)]); d.arrow([(5.0, 5.02), (5.0, 5.36)])
d.txt(5.15, 5.19, "/api", 12.5, ha="left", color=GREY)

# server
d.box(4.7, 3.42, 8.9, 3.15, "", c="#FFF6DD")
d.txt(0.4, 4.78, "Server", 16, ha="left", fontweight="bold")
logos(["python", "fastapi"], 1.4, 4.78, s=0.36, gap=0.2, lab=False)
d.txt(2.45, 4.82, "Python + FastAPI: upload, jobs, review state", 14, ha="left")
st = [("A · each file", "read EDF, filter,\n4 s windows"), ("B · each patient", "graphs, GAE,\nanomaly score"),
      ("Process", "alarm budget,\ndetector, change points")]
for i, (t, s) in enumerate(st):
    x = 1.75 + i * 2.95
    d.box(x, 3.72, 2.55, 1.05, "", c=W)
    d.txt(x, 3.98, t, 14.5, fontweight="bold")
    d.txt(x, 3.58, s, 13.5)
    if i:
        d.arrow([(x - 2.95 + 1.28, 3.72), (x - 1.28, 3.72)])
d.txt(0.4, 2.62, "Frozen thesis code, CPU:", 14, ha="left")
logos(["pytorch", "pyg", "scikitlearn", "numpy"], 2.75, 2.62, s=0.36, gap=0.36)
d.txt(5.75, 2.62, "+ MNE (EDF), ruptures\n(change points)", 13.5, ha="left")
d.txt(0.4, 2.12, "GAE checkpoint checked by hash; settings read from the frozen file", 13, ha="left", style="italic", color=GREY)

# storage
d.arrow([(4.7, 1.84), (4.7, 1.52)]); d.arrow([(5.0, 1.52), (5.0, 1.84)])
d.box(2.45, 0.95, 4.4, 1.05, "", c="#F2F6FB")
logos(["sqlite"], 0.42, 0.95, s=0.42, lab=False)
d.txt(1.05, 0.95, "SQLite: events, reviews,\ncomments", 14, ha="left")
d.box(6.95, 0.95, 4.4, 1.05, "", c="#F2F6FB")
logos(["numpy"], 4.92, 0.95, s=0.42, lab=False)
d.txt(5.55, 0.95, "Cache on disk: signals,\nscores, channel arrays", 14, ha="left")
d.save(sys.argv[1])
print("saved")
