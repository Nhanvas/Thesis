"""
Shared palette and rcParams for the rebuilt detection figures (Fig 2.8, 2.9, 3.1,
3.2, 3.3, 3.5, 3.6, 3.7, 3.9).

One colour for interictal, one for ictal, one for detected intervals -- brief rule 7.
Chance level / noise bands are drawn explicitly wherever they apply, never implied.
No confidence intervals appear on any detection figure (brief rule 4).
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

INTERICTAL = "#4C72B0"   # blue
ICTAL = "#C44E52"        # red
DETECTED = "#55A868"     # green
CHANCE = "#8C8C8C"       # grey, dashed
HEADLINE = "#B8860B"     # dark goldenrod -- the one operating point every figure marks
BEST_ACHIEVABLE = "#6A3D9A"  # purple -- the post-hoc best point, never a result

# One sequential colormap for every adjacency / band-power heatmap in the report
# (docs/FIGURE_FIXES_R3.md §1, Fig 2.4): Fig 1.2, Fig 2.4 panels (b)/(c), Fig 2.5.
SEQUENTIAL_CMAP = "viridis"

RC = {
    "font.family": "serif",
    "font.size": 10,
    "axes.titlesize": 11,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "figure.dpi": 150,
}


def apply_rc():
    plt.rcParams.update(RC)
