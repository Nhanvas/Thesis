"""
Fig 2.12 - Architecture of the review application, and why it recomputes.

Two panels.

(a) The application's components, and the three paths it must never take. The
    application is label-free at runtime: it never reads the seizure annotations,
    never rebuilds a timeline from them, and never loads the pre-split background
    and seizure arrays, because both were split using the annotations.

(b) The measurement that forces (a). Artifact rejection removes background
    windows without recording their positions, so the stored score array is
    ordered by segment. Rebuilding a timeline from it shifts the surviving
    scores and, once the array runs out, fills the remainder by resampling.

Every proportion in panel (b) is read from results/diagnostics/timeline_composition.csv
and drawn to scale. Nothing in this figure is estimated: if the file is missing or
a column is absent, the script stops rather than drawing an illustration of a
measurement it does not have.

Source: results/diagnostics/timeline_composition.csv
Output: figures/fig2_12_application_architecture.png
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrowPatch

ROOT = Path(__file__).resolve().parents[2]
for p in (ROOT / "src", ROOT / "src" / "figures"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from palette import INTERICTAL, ICTAL, DETECTED, CHANCE, HEADLINE, apply_rc  # noqa: E402

CSV = ROOT / "results" / "diagnostics" / "timeline_composition.csv"
EXAMPLE = "chb13"

if not CSV.exists():
    sys.exit(f"FAIL: {CSV} not found. Panel (b) is a measurement and must not "
             "be drawn from typed-in values.")

df = pd.read_csv(CSV)
need = {"subject", "eligible_windows", "committed_inter_windows",
        "exhaustion_point_fraction", "substituted_fraction"}
missing = need - set(df.columns)
if missing:
    sys.exit(f"FAIL: {CSV} lacks {sorted(missing)}. Fix the emitting script; "
             "do not hard-code the values here.")

row = df.loc[df["subject"] == EXAMPLE]
if row.empty:
    sys.exit(f"FAIL: {EXAMPLE} not present in {CSV}.")
row = row.iloc[0]

ELIGIBLE = int(row["eligible_windows"])
STORED = int(row["committed_inter_windows"])
EXHAUST = float(row["exhaustion_point_fraction"])
SUB_MEAN = float(df["substituted_fraction"].mean())
SUB_MIN = float(df["substituted_fraction"].min())
SUB_MAX = float(df["substituted_fraction"].max())
N_SUBJ = len(df)

print(f"read {CSV}")
print(f"  example subject        : {EXAMPLE}")
print(f"  eligible positions     : {ELIGIBLE:,}")
print(f"  stored scores          : {STORED:,}")
print(f"  exhaustion point       : {EXHAUST:.3f} of the timeline")
print(f"  substituted, {N_SUBJ} subjects: mean {SUB_MEAN:.3f}, "
      f"range {SUB_MIN:.3f} to {SUB_MAX:.3f}")

assert 0.0 < EXHAUST < 1.0, "exhaustion point should be a fraction"
assert STORED < ELIGIBLE, "stored scores should be fewer than eligible positions"

# ---------------------------------------------------------------------------
apply_rc()
fig = plt.figure(figsize=(10.4, 9.6))
gs = fig.add_gridspec(2, 1, height_ratios=[1.15, 1.0], hspace=0.16,
                      left=0.06, right=0.97, top=0.96, bottom=0.06)

# === panel (a) — architecture ==============================================
axa = fig.add_subplot(gs[0])
axa.set_xlim(0, 100)
axa.set_ylim(-8, 100)
axa.axis("off")

BANDS = [
    ("Browser", INTERICTAL, 80,
     ["Recording selector", "Signal viewer with\ndetected intervals",
      "Channel-level\nanomaly panel"]),
    ("Application server", CHANCE, 58,
     ["Upload and\nfile handling", "Job queue", "Results interface"]),
    ("Scoring", HEADLINE, 32,
     ["Preprocess,\nevery window kept", "Graph construction",
      "Trained encoder,\nsame checkpoint",
      "Three readouts\nand fusion", "Change-point\ndetection"]),
    ("Storage", CHANCE, 6,
     ["Uploaded recordings", "Computed scores\nand intervals"]),
]

X0, X1 = 3.0, 66.0
BOX_H = 13.0

for name, colour, y, items in BANDS:
    axa.add_patch(Rectangle((X0 - 1.6, y - 2.4), (X1 - X0) + 3.2, BOX_H + 6.0,
                            facecolor="none", edgecolor=colour, linewidth=1.0,
                            linestyle=(0, (3, 3)), zorder=1))
    axa.text(X0 - 0.6, y + BOX_H + 1.2, name, fontsize=9.5, fontweight="bold",
             color=colour, va="bottom", zorder=5,
             bbox=dict(boxstyle="square,pad=0.12", facecolor="white",
                       edgecolor="none"))
    n = len(items)
    w = ((X1 - X0) - 1.6 * (n - 1)) / n
    for i, label in enumerate(items):
        x = X0 + i * (w + 1.6)
        axa.add_patch(Rectangle((x, y), w, BOX_H, facecolor="white",
                                edgecolor=colour, linewidth=1.3, zorder=3))
        axa.text(x + w / 2, y + BOX_H / 2, label, ha="center", va="center",
                 fontsize=7.6, color="0.15", zorder=4)

for y_from, y_to in ((80, 58 + BOX_H), (58, 32 + BOX_H), (32, 6 + BOX_H)):
    axa.add_patch(FancyArrowPatch(((X0 + X1) / 2, y_from),
                                  ((X0 + X1) / 2, y_to), arrowstyle="<|-|>",
                                  mutation_scale=8, color=CHANCE,
                                  linewidth=1.0, zorder=2))

# the forbidden inputs
FX, FW = 71.0, 26.0
axa.add_patch(Rectangle((FX, 6), FW, 67, facecolor="white", edgecolor=ICTAL,
                        linewidth=1.4, zorder=3))
axa.text(FX + FW / 2, 66, "Never read at runtime", ha="center", va="center",
         fontsize=9.5, fontweight="bold", color=ICTAL, zorder=4)
for i, txt in enumerate(["Seizure onset and\noffset annotations",
                         "Any timeline rebuilt\nfrom annotations",
                         "Pre-split background\nand seizure arrays"]):
    axa.text(FX + FW / 2, 54 - i * 14, txt, ha="center", va="center",
             fontsize=8.2, color=ICTAL, zorder=4)

for y in (32 + BOX_H / 2, 6 + BOX_H / 2):
    axa.add_patch(FancyArrowPatch((FX, y), (X1 + 1.6, y), arrowstyle="-[",
                                  mutation_scale=7, color=ICTAL,
                                  linewidth=1.3, zorder=4))
axa.text((X1 + FX) / 2, 25, "blocked", ha="center", va="center", fontsize=8,
         style="italic", color=ICTAL, rotation=90, zorder=4)

axa.text(X0 - 1.6, -5.0,
         "(a)  The application recomputes anomaly scores on the continuous "
         "recording. It does not replay stored scores.",
         fontsize=9.5, va="center", color="0.15")

# === panel (b) — why replay is impossible ==================================
axb = fig.add_subplot(gs[1])
axb.set_xlim(-0.30, 1.06)
axb.set_ylim(-0.55, 4.05)
axb.axis("off")

BAR_H = 0.40
LEFT = 0.0
RNG = np.random.default_rng(7)

# row 1 — the recording as it exists
y = 2.50
axb.add_patch(Rectangle((LEFT, y), 1.0, BAR_H, facecolor="white",
                        edgecolor=INTERICTAL, linewidth=1.2))
rejected = np.sort(RNG.uniform(0.02, 0.98, 34))
for r in rejected:
    axb.add_patch(Rectangle((r, y), 0.006, BAR_H, facecolor=ICTAL,
                            edgecolor="none", alpha=0.85))
for s in (0.30, 0.72):
    axb.add_patch(Rectangle((s, y), 0.022, BAR_H, facecolor=HEADLINE,
                            edgecolor="none"))
axb.text(-0.02, y + BAR_H / 2, "The recording\nas it exists", ha="right",
         va="center", fontsize=8.5)
axb.text(1.02, y + BAR_H / 2,
         "every window has a position in time\n"
         "narrow marks: windows removed by artifact rejection\n"
         "wide marks: annotated seizures",
         ha="left", va="center", fontsize=8, style="italic", color="0.35")

# row 2 — the stored array
y = 1.45
frac_stored = STORED / ELIGIBLE
axb.add_patch(Rectangle((LEFT, y), frac_stored, BAR_H, facecolor="white",
                        edgecolor=INTERICTAL, linewidth=1.2))
axb.text(-0.02, y + BAR_H / 2, "The stored\nscore array", ha="right",
         va="center", fontsize=8.5)
axb.text(frac_stored + 0.02, y + BAR_H / 2,
         f"{STORED:,} scores for {ELIGIBLE:,} positions\n"
         f"ordered by segment; the removed windows are gone,\n"
         f"and nothing records where they were",
         ha="left", va="center", fontsize=8, style="italic", color="0.35")
axb.add_patch(FancyArrowPatch((0.5, 2.50 - 0.06), (0.5, y + BAR_H + 0.06),
                              arrowstyle="-|>", mutation_scale=8,
                              color=CHANCE, linewidth=1.0))
axb.text(0.515, (2.50 + y + BAR_H) / 2, "artifact rejection removes windows",
         fontsize=8, style="italic", color=CHANCE, va="center")

# row 3 — the reconstructed timeline
y = 0.40
axb.add_patch(Rectangle((LEFT, y), EXHAUST, BAR_H, facecolor=INTERICTAL,
                        alpha=0.30, edgecolor=INTERICTAL, linewidth=1.2))
axb.add_patch(Rectangle((EXHAUST, y), 1.0 - EXHAUST, BAR_H, facecolor="white",
                        edgecolor=ICTAL, linewidth=1.2, hatch="////"))
axb.text(-0.02, y + BAR_H / 2, "The reconstructed\ntimeline", ha="right",
         va="center", fontsize=8.5)
axb.text(EXHAUST / 2, y - 0.10, "real scores, shifted from\ntheir original positions",
         ha="center", va="top", fontsize=8, style="italic", color=INTERICTAL)
axb.text((1.0 + EXHAUST) / 2, y - 0.10,
         "bootstrap-resampled:\nthe stored array has run out",
         ha="center", va="top", fontsize=8, style="italic", color=ICTAL)
axb.add_patch(FancyArrowPatch((0.5, 1.45 - 0.06), (0.5, y + BAR_H + 0.06),
                              arrowstyle="-|>", mutation_scale=8,
                              color=CHANCE, linewidth=1.0))
axb.text(0.515, (1.45 + y + BAR_H) / 2, "rebuilt using the annotation file",
         fontsize=8, style="italic", color=CHANCE, va="center")

axb.text(-0.30, 4.00,
         f"(b)  Why a stored score array cannot be replayed on a time axis "
         f"({EXAMPLE}).  Across the {N_SUBJ} held-out patients, "
         f"{SUB_MEAN * 100:.1f} % of each reconstructed timeline carries a "
         f"resampled score on average,\n      ranging from {SUB_MIN * 100:.1f} "
         f"% to {SUB_MAX * 100:.1f} %. The false-alarm rate is measured on "
         f"these timelines, and the direction of the resulting bias is not "
         f"established.",
         fontsize=9.5, va="top", color="0.15")

OUT = ROOT / "figures" / "fig2_12_application_architecture.png"
OUT.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(OUT, dpi=300, bbox_inches="tight", facecolor="white")
print(f"\nwrote {OUT}")

print("\ncaption text:")
print(f"  Architecture of the review application. (a) The application "
      f"recomputes anomaly scores on the continuous recording, retaining every "
      f"window, and never reads the seizure annotations, any timeline rebuilt "
      f"from them, or the pre-split background and seizure arrays. (b) The "
      f"measurement that forces this design: artifact rejection removes "
      f"background windows without recording their positions, so the stored "
      f"array holds {STORED:,} scores for {ELIGIBLE:,} timeline positions in "
      f"{EXAMPLE}, and a reconstructed timeline shifts the surviving scores "
      f"and resamples the remainder. Across the {N_SUBJ} held-out patients "
      f"{SUB_MEAN * 100:.1f} % of each reconstructed timeline is resampled on "
      f"average, ranging from {SUB_MIN * 100:.1f} % to {SUB_MAX * 100:.1f} %. "
      f"The false-alarm rate is measured on these timelines, and the direction "
      f"of the resulting bias is not established.")
