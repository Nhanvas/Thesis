"""Reference slides (not final art): Comparison, Contribution, Conclusion in the author's deck style. Numbers = locks."""
import sys, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyBboxPatch
import numpy as np
OUT = sys.argv[1]; BLUE, RED, INK, YEL = "#1F6FB2", "#DC433A", "#222222", "#FFF27A"
plt.rcParams["font.family"] = "DejaVu Sans"
def slide(title, active, page):
    fig = plt.figure(figsize=(19.2, 10.8), dpi=100); ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 1920); ax.set_ylim(1080, 0); ax.axis("off")
    grad = np.linspace(0, 1, 512)[None, :]
    from matplotlib.colors import LinearSegmentedColormap
    ax.imshow(grad, extent=[0, 1920, 1080, 1010], cmap=LinearSegmentedColormap.from_list("g", ["#D8E6F3", "#2C67AE"]), aspect="auto")
    x = 40
    for s in ["Introduction", "Methodology", "Results", "Discussion", "Conclusion"]:
        w = 18 * len(s) * 0.68 + 36
        if s == active: ax.add_patch(FancyBboxPatch((x - 10, 1022), w, 46, boxstyle="round,pad=0,rounding_size=20", color=BLUE))
        ax.text(x + 5, 1046, s, fontsize=18, va="center", color="white" if s == active else INK); x += w + 20
    ax.text(1880, 1046, str(page), fontsize=16, color="white", va="center", ha="right")
    ax.text(40, 70, title, fontsize=34, color=BLUE, va="center")
    return fig, ax
def bullets(ax, items, x, y, dy=62, fs=22):
    for head, body in items:
        ax.text(x, y, "•", fontsize=fs, va="top")
        ax.text(x + 28, y, head, fontsize=fs, va="top", weight="bold", color=BLUE)
        ax.text(x + 28, y + 36, body, fontsize=fs - 3, va="top", color=INK, linespacing=1.35)
        y += dy + 36 * (body.count("\n") + 1)
    return y

# Comparison
fig, ax = slide("Comparison on Siena (SzCORE)", "Discussion", "x")
cols = ["Method", "Seizure labels", "Sensitivity", "Precision", "FA/day"]; cx = [60, 560, 1060, 1340, 1610]
rows = [["EventNet 2024", "supervised (TUH)", "0.587", "0.578", "8.2"],
        ["Zhu Transformer 2023", "supervised (TUH)", "0.674", "0.484", "15.3"],
        ["This work (GAE, 4 seeds)", "none (trained on CHB-MIT)", "0.633", "0.160", "41.0"],
        ["DynaSD", "none (threshold: iEEG)†", "0.664", "0.126", "77.7"]]
y0 = 170; ax.add_patch(Rectangle((40, y0), 1840, 70, color=BLUE))
for c, x in zip(cols, cx): ax.text(x, y0 + 35, c, fontsize=22, color="white", va="center", weight="bold")
for i, r in enumerate(rows):
    y = y0 + 70 + i * 90
    ax.add_patch(Rectangle((40, y), 1840, 90, facecolor=YEL if i == 2 else "white", edgecolor="#BBBBBB"))
    for v, x in zip(r, cx): ax.text(x, y + 45, v, fontsize=22, va="center", color=INK, weight="bold" if i == 2 else "normal")
ax.text(60, 690, "Similar sensitivity to the only other label-free method, at about half the false alarms.", fontsize=24, color=INK)
ax.text(60, 745, "Supervised methods raise far fewer false alarms → the gap to close.", fontsize=24, color=INK)
ax.text(60, 940, "Siena: 14 adults, 47 seizures; per-patient mean; methods not trained on Siena. † threshold set on labelled intracranial EEG. Full table and CHB-MIT studies → backup.",
        fontsize=16, color="#666", style="italic")
fig.savefig(f"{OUT}/REF_comparison.png"); plt.close(fig)

# Contribution
fig, ax = slide("Contributions", "Conclusion", "x")
bullets(ax, [
 ("Label-free seizure events with onset and offset", "GAE score on the patient's own recording + kernel change points · onset error 32 → 12 s (median, 4 seeds)"),
 ("Strict, comparable evaluation", "continuous recordings, unseen patients, SzCORE · adults without retraining: 0.633 at 41.0 FA/day\n(only other label-free method: 0.664 at 77.7)"),
 ("Channel-level evidence", "blind annotation of 76 test seizures, 282 channel labels (supervisor-approved) · ranking above chance (0.547)\nbut not better than a simple anatomical prior (0.739)"),
 ("Measured lessons", "artifact removal (ASR) cuts seizure contrast 2.09 → 1.41* · file drift drives most false alarms before correction ·\nmissed seizures are low-amplitude and short*"),
 ("SzScan review tool", "local, label-free, ≈ 22 s per hour of EEG on a laptop CPU")], 60, 150)
ax.text(60, 960, "per-patient mean · *after the review", fontsize=16, color="#666", style="italic")
fig.savefig(f"{OUT}/REF_contribution.png"); plt.close(fig)

# Conclusion
fig, ax = slide("Conclusion", "Conclusion", "x")
ax.text(60, 140, "Can we localize seizures in a new patient without his seizure labels?", fontsize=24, style="italic", color=INK)
y = bullets(ax, [
 ("Achieved", "held-out unseen patients: 0.508 at 21.8 FA/day · onset error 12 s (median, 4 seeds)"),
 ("Evaluated", "adults without retraining: 0.633 at 41.0 FA/day · label-free application: 0.528 at 26.9 FA/day"),
 ("Delivered", "SzScan, a local review tool")], 60, 210)
ax.text(60, y + 10, "Limits  →  Next", fontsize=24, weight="bold", color=RED)
lim = [("Low-amplitude, short seizures missed", "rhythm / morphology features"),
       ("≈ 1 false alarm per hour", "supervised artifact detector"),
       ("Offset error 24 s", "run rule for the offset"),
       ("Hospital EEG has no labels", "expert reading, prospective study")]
for i, (l, n) in enumerate(lim):
    yy = y + 70 + i * 52
    ax.text(90, yy, l, fontsize=20, color=INK); ax.text(900, yy, "→  " + n, fontsize=20, color=INK)
ax.text(60, 960, "per-patient mean", fontsize=16, color="#666", style="italic")
fig.savefig(f"{OUT}/REF_conclusion.png"); plt.close(fig)
print("ok")
