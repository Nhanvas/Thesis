"""
Fig 3.6 (formerly emitted as fig3_11_application.png, see the output path note below) -
the application's own screens, composed from raw screenshots captured by
CC_PART2_PART4_PROMPT.md Part D on the frozen build (szscan-frozen-v2).

Screenshots are placed as-is, never redrawn or retouched -- the only edit made here is
cropping away window chrome (the app's own dark footer bar) and the large empty margin
below panel (a)'s Create New panel; the pixel content inside each crop is untouched.

Layout, per CC_PROMPT_FIG3_6.md Part B: panel (b), the detection timeline, is the widest
panel and spans the full width; (a), (c) and (d) sit in a row below it, scaled to a common
height. Panel labels follow the house style read from src/figures/fig2_14_event_scoring.py
(the only generator in this set that already draws lettered multi-panel labels):
"(x)  <one-line caption>", left-aligned, bold, fontsize 10.5 -- serif family and dpi=150
on-screen / 300 on save match src/figures/palette.py's shared RC. No overall figure title;
the caption belongs to the report text (CC_PROMPT_FIG3_6.md Part B).

Inputs (all four required by CC_PART2_PART4_PROMPT.md Part D):
  web_demo/report_handback/fig3_6a_import.png        - throwaway one-file chb13 upload,
                                                          discarded before Process
  web_demo/report_handback/fig3_6b_timeline.png       - chb13_62, Event 2 selected
  web_demo/report_handback/fig3_6c_channel_panel.png  - channel-level reconstruction
                                                          anomaly panel, Event 2
  web_demo/report_handback/fig3_6d_review.png         - Event 2's own review row,
                                                          Accept/Reject/Uncertain, unclicked

Output: figures/fig3_11_application.png (this repo's next free figure slot at the time
this script was written -- 21 figures existed; ls figures/*.png | wc -l must read 22
afterwards, per CC_PROMPT_FIG3_6.md Part B's own check).

Regenerate: python src/figures/make_fig3_6_application.py
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
SCREENSHOT_DIR = ROOT / "web_demo" / "report_handback"
OUT = ROOT / "figures" / "fig3_11_application.png"

RC = {
    "font.family": "serif",
    "font.size": 10,
    "figure.dpi": 150,
}
plt.rcParams.update(RC)

PANEL_LABEL_STYLE = dict(loc="left", fontsize=10.5, fontweight="bold", pad=8)

FIG_WIDTH_IN = 6.3  # CC_PROMPT_FIG3_6.md: "about 6 inches" printed text width
GAP_IN = 0.12
ROW_GAP_IN = 0.30
LABEL_BAND_IN = 0.30  # vertical room reserved for each row's "(x)  caption" title


def _crop_to_content(arr: np.ndarray, std_threshold: float = 5.0) -> np.ndarray:
    """Crop away the app's own dark footer bar, then any further blank margin above it.
    Two stages, in this order, because both the footer (white text on a dark bar) and
    real content have nonzero row-std -- a single bottom-up std scan finds the footer
    first and stops there, never reaching the real content boundary above it:

    1. Footer: scan the last 200 rows for the sharp brightness drop into the dark bar
       (window chrome, per CC_PROMPT_FIG3_6.md's composition rule) and cut there.
    2. Empty margin: within what is left, trim trailing rows with no real content
       (row-std <= threshold) back to the last row that still has it -- (a)'s Create New
       panel leaves a large blank gap above where the footer used to be.
    """
    mean_b = arr.reshape(arr.shape[0], -1).mean(axis=1)
    tail_start = max(0, arr.shape[0] - 200)
    footer_start = arr.shape[0]
    for r in range(arr.shape[0] - 1, tail_start, -1):
        if mean_b[r - 1] - mean_b[r] > 80:  # sharp light-to-dark drop = top edge of the footer
            footer_start = r
            break
    arr = arr[:footer_start]

    row_std = arr.reshape(arr.shape[0], -1).std(axis=1)
    last_content = 0
    for r in range(arr.shape[0] - 1, -1, -1):
        if row_std[r] > std_threshold:
            last_content = r
            break
    pad = 12
    end = min(arr.shape[0], last_content + pad)
    return arr[:end]


def load_panel(name: str, crop: bool) -> np.ndarray:
    path = SCREENSHOT_DIR / name
    if not path.exists():
        raise SystemExit(f"missing required screenshot: {path}")
    arr = np.asarray(Image.open(path).convert("RGB"))
    if crop:
        arr = _crop_to_content(arr)
    return arr


def main():
    img_a = load_panel("fig3_6a_import.png", crop=True)
    img_b = load_panel("fig3_6b_timeline.png", crop=True)
    img_c = load_panel("fig3_6c_channel_panel.png", crop=False)
    img_d = load_panel("fig3_6d_review.png", crop=True)

    # --- geometry: (b) full width on top; (a),(c),(d) in a row below, common height ---
    ratio_b = img_b.shape[1] / img_b.shape[0]
    top_h_in = FIG_WIDTH_IN / ratio_b

    ratios = [img_a.shape[1] / img_a.shape[0], img_c.shape[1] / img_c.shape[0], img_d.shape[1] / img_d.shape[0]]
    n_gaps = 2
    bottom_h_in = (FIG_WIDTH_IN - n_gaps * GAP_IN) / sum(ratios)
    bottom_widths_in = [bottom_h_in * r for r in ratios]

    fig_h_in = LABEL_BAND_IN + top_h_in + ROW_GAP_IN + LABEL_BAND_IN + bottom_h_in
    fig = plt.figure(figsize=(FIG_WIDTH_IN, fig_h_in))

    def add_axes(x_in, y_in, w_in, h_in):
        return fig.add_axes([x_in / FIG_WIDTH_IN, y_in / fig_h_in, w_in / FIG_WIDTH_IN, h_in / fig_h_in])

    # Matplotlib figure coords have y=0 at the BOTTOM, so lay out bottom-up.
    y_bottom_row = 0.0
    y_top_row = bottom_h_in + LABEL_BAND_IN + ROW_GAP_IN

    ax_b = add_axes(0.0, y_top_row, FIG_WIDTH_IN, top_h_in)
    ax_b.imshow(img_b)
    ax_b.set_title("(b)  Detection timeline: Event 2 selected and highlighted", **PANEL_LABEL_STYLE, clip_on=True)
    ax_b.axis("off")

    # The bottom row's three panels are much narrower than (b) (1.1-3.7in vs 6.3in) --
    # matplotlib's set_title() does not wrap or clip to the axes width by default, so a
    # caption sized for (b) overlaps its neighbours here. Short, per-panel captions plus
    # clip_on=True (belt and braces: truncate rather than overlap if a caption is ever
    # widened later) keep each row's three titles inside their own column.
    x = 0.0
    labels_bottom = ["(a)  Import in progress", "(c)  Channel panel", "(d)  Event review"]
    for img, w_in, label in zip([img_a, img_c, img_d], bottom_widths_in, labels_bottom):
        ax = add_axes(x, y_bottom_row, w_in, bottom_h_in)
        ax.imshow(img)
        ax.set_title(label, loc="left", fontsize=9, fontweight="bold", pad=6, clip_on=True)
        ax.axis("off")
        x += w_in + GAP_IN

    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)

    saved = Image.open(OUT)
    print(f"wrote {OUT}  size={saved.size[0]}x{saved.size[1]} px")

    # Effective resolution of each source panel at its printed size in this composition.
    print("\nEffective pixel density (source px / printed inch) per panel:")
    print(f"  (a) source {img_a.shape[1]}x{img_a.shape[0]} px -> printed {bottom_widths_in[0]:.2f}in wide "
          f"-> {img_a.shape[1] / bottom_widths_in[0]:.0f} px/in")
    print(f"  (b) source {img_b.shape[1]}x{img_b.shape[0]} px -> printed {FIG_WIDTH_IN:.2f}in wide "
          f"-> {img_b.shape[1] / FIG_WIDTH_IN:.0f} px/in")
    print(f"  (c) source {img_c.shape[1]}x{img_c.shape[0]} px -> printed {bottom_widths_in[1]:.2f}in wide "
          f"-> {img_c.shape[1] / bottom_widths_in[1]:.0f} px/in")
    print(f"  (d) source {img_d.shape[1]}x{img_d.shape[0]} px -> printed {bottom_widths_in[2]:.2f}in wide "
          f"-> {img_d.shape[1] / bottom_widths_in[2]:.0f} px/in")


if __name__ == "__main__":
    main()
