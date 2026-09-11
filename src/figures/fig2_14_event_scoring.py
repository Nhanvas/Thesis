"""
Fig 2.14 - Event-based scoring rules, in three panels.

One rule per panel, drawn to scale on a common time axis, so the 30 s pre-onset
tolerance, the 60 s post-offset tolerance and the 90 s merge gap can be read off
the axis rather than taken on trust.

The five parameters are read from src/szcore_eval.py, not typed in here: the
script imports them and stops if they cannot be found, so the drawing cannot
drift from the scorer that implements the rule.

The waveform is SYNTHETIC and illustrative. It is generated from a fixed seed and
is not a recording. It is drawn so a reader can see what the boxes refer to; no
property of it affects the scoring, which depends only on the interval endpoints.
Drawing a real recording here would invite the question of which recording and
whether this is a result, and this figure is neither.

Source of parameters: src/szcore_eval.py
Output: figures/fig2_14_event_scoring.png
"""
import sys
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrowPatch

ROOT = Path(__file__).resolve().parents[2]
for p in (ROOT / "src", ROOT / "src" / "figures"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from palette import ICTAL, DETECTED, CHANCE, HEADLINE, apply_rc  # noqa: E402

try:
    import szcore_eval as SZ
except Exception as exc:                                     # pragma: no cover
    sys.exit(f"FAIL: cannot import src/szcore_eval.py ({exc}). "
             "This figure must not be drawn with typed-in parameters.")


def _param(*names):
    """Find a scoring parameter wherever szcore_eval keeps it."""
    for n in names:
        if hasattr(SZ, n):
            return getattr(SZ, n), f"szcore_eval.{n}"
    for holder in dir(SZ):
        if holder.startswith("__"):
            continue
        obj = getattr(SZ, holder)
        if isinstance(obj, (str, int, float, list, dict, tuple)):
            continue
        for n in names:
            if hasattr(obj, n):
                return getattr(obj, n), f"szcore_eval.{holder}.{n}"
    sys.exit(f"FAIL: none of {names} found in src/szcore_eval.py, at module "
             "level or on any configuration object. Fix the lookup here; do "
             "not edit szcore_eval.py and do not hard-code the value.")


TOL_START, src_a = _param("toleranceStart", "TOLERANCE_START", "TOL_START")
TOL_END, src_b = _param("toleranceEnd", "TOLERANCE_END", "TOL_END")
MERGE_GAP, src_c = _param("minDurationBetweenEvents",
                          "MIN_DURATION_BETWEEN_EVENTS", "MERGE_GAP")
MAX_EVENT, src_d = _param("maxEventDuration", "MAX_EVENT_DURATION", "MAX_EVENT")
TOL_START, TOL_END = float(TOL_START), float(TOL_END)
MERGE_GAP, MAX_EVENT = float(MERGE_GAP), float(MAX_EVENT)

print("parameters, and where each was read from")
print(f"  tolerance before onset : {TOL_START:g} s   <- {src_a}")
print(f"  tolerance after offset : {TOL_END:g} s   <- {src_b}")
print(f"  merge gap              : {MERGE_GAP:g} s   <- {src_c}")
print(f"  maximum event duration : {MAX_EVENT:g} s   <- {src_d}")

# --- illustrative signal ----------------------------------------------------
T_MAX = 420.0
FS_PLOT = 14.0
RNG = np.random.default_rng(42)
t = np.arange(0, T_MAX, 1.0 / FS_PLOT)


def _trace(seizure=None, spike_at=None):
    """Background activity, optionally with a rhythmic burst and a transient."""
    x = np.convolve(RNG.normal(0, 1.0, t.size), np.ones(5) / 5.0,
                    mode="same") * 0.30
    if seizure is not None:
        s, e = seizure
        m = (t >= s) & (t <= e)
        ramp = np.sin(np.pi * (t[m] - s) / (e - s)) ** 0.5
        x[m] += 1.00 * ramp * np.sin(2 * np.pi * 0.9 * (t[m] - s))
        x[m] += RNG.normal(0, 0.20, m.sum())
    if spike_at is not None:
        m = np.abs(t - spike_at) < 3.0
        x[m] += 2.0 * np.exp(-((t[m] - spike_at) ** 2) / 0.40)
    return x


SEIZURE = (150.0, 250.0)            # the same annotated seizure in all panels

PANELS = [
    dict(
        tag="(a)",
        title="Any overlap inside the tolerance window counts as a match",
        lanes=["Reference", "Hypothesis"],
        detections=[[(265.0, 300.0)]],
        outcomes=[["match"]],
        tolerance=True,
        spike=None,
        note="The detection begins after the annotated seizure has ended. It "
             "still counts, because it falls inside the post-offset tolerance.",
    ),
    dict(
        tag="(b)",
        title=f"Detections closer than {MERGE_GAP:g} s are merged before scoring",
        lanes=["Reference", "Hypothesis,\nas produced",
               "Hypothesis,\nafter merging"],
        detections=[[(140.0, 190.0), (215.0, 265.0)], [(140.0, 265.0)]],
        outcomes=[[None, None], ["match"]],
        tolerance=False,
        spike=None,
        note="Two detections separated by less than the merge gap become one "
             "interval, which is then scored once.",
    ),
    dict(
        tag="(c)",
        title="A detection outside the tolerance window is a false alarm",
        lanes=["Reference", "Hypothesis"],
        detections=[[(160.0, 230.0), (345.0, 375.0)]],
        outcomes=[["match", "false alarm"]],
        tolerance=True,
        spike=360.0,
        note="False alarms are counted per recorded day. Specificity is not "
             "defined at event level, because a true-negative event has no "
             "meaning once a timeline is expressed as events.",
    ),
]

apply_rc()
fig, axes = plt.subplots(3, 1, figsize=(10.2, 10.8),
                         gridspec_kw=dict(height_ratios=[2, 3, 2], hspace=1.05,
                                          bottom=0.11, top=0.96))

LANE_GAP = 1.0
BOX_H = 0.60
SIG_AMP = 0.25

for ax, P in zip(axes, PANELS):
    n = len(P["lanes"])
    ys = [(n - 1 - i) * LANE_GAP for i in range(n)]

    y_ref = ys[0]
    ax.plot(t, y_ref + SIG_AMP * _trace(seizure=SEIZURE), color=CHANCE,
            linewidth=0.55, zorder=2)

    if P["tolerance"]:
        ax.add_patch(Rectangle((SEIZURE[0] - TOL_START, y_ref - BOX_H / 2),
                               (SEIZURE[1] + TOL_END) - (SEIZURE[0] - TOL_START),
                               BOX_H, facecolor="none", edgecolor=ICTAL,
                               linewidth=1.1, linestyle=(0, (5, 4)), zorder=4))
    ax.add_patch(Rectangle((SEIZURE[0], y_ref - BOX_H / 2),
                           SEIZURE[1] - SEIZURE[0], BOX_H, facecolor="none",
                           edgecolor=ICTAL, linewidth=1.6, zorder=5))

    for li, dets in enumerate(P["detections"]):
        y = ys[li + 1]
        ax.plot(t, y + SIG_AMP * _trace(seizure=SEIZURE, spike_at=P["spike"]),
                color=CHANCE, linewidth=0.55, zorder=2)
        for di, (s, e) in enumerate(dets):
            ax.add_patch(Rectangle((s, y - BOX_H / 2), e - s, BOX_H,
                                   facecolor="none", edgecolor=DETECTED,
                                   linewidth=1.6, zorder=5))
            lab = P["outcomes"][li][di]
            if lab:
                ax.text((s + e) / 2, y - BOX_H / 2 - 0.11, lab, ha="center",
                        va="top", fontsize=8.5,
                        color=DETECTED if lab == "match" else HEADLINE,
                        zorder=6)

    if P["tolerance"]:
        y_a = y_ref + BOX_H / 2 + 0.15
        for x0, x1, lab in (
            (SEIZURE[0] - TOL_START, SEIZURE[0], f"{TOL_START:g} s before onset"),
            (SEIZURE[1], SEIZURE[1] + TOL_END, f"{TOL_END:g} s after offset"),
        ):
            ax.add_patch(FancyArrowPatch((x0, y_a), (x1, y_a),
                                         arrowstyle="<->", mutation_scale=7,
                                         color=ICTAL, linewidth=0.9, zorder=6))
            ax.text((x0 + x1) / 2, y_a + 0.04, lab, ha="center", va="bottom",
                    fontsize=8, color=ICTAL, zorder=6)

    if len(P["detections"]) == 2:
        a = P["detections"][0][0][1]
        b = P["detections"][0][1][0]
        y_g = ys[1]
        ax.add_patch(FancyArrowPatch((a, y_g), (b, y_g), arrowstyle="<->",
                                     mutation_scale=6, color=HEADLINE,
                                     linewidth=1.0, zorder=7))
        ax.annotate(f"gap {b - a:.0f} s, under {MERGE_GAP:g} s",
                    xy=((a + b) / 2, y_g + BOX_H / 2 - 0.02),
                    xytext=(b + 45, y_g + BOX_H / 2 + 0.30), ha="left",
                    va="center", fontsize=8, color=HEADLINE, zorder=8,
                    bbox=dict(boxstyle="round,pad=0.18", facecolor="white",
                              edgecolor="none"),
                    arrowprops=dict(arrowstyle="-", color=HEADLINE,
                                    linewidth=0.7, shrinkA=1, shrinkB=2))

    ax.set_title(f"{P['tag']}  {P['title']}", loc="left", fontsize=10.5,
                 fontweight="bold", pad=18)
    ax.annotate(P["note"], xy=(0.5, 0), xycoords="axes fraction",
                xytext=(0, -46), textcoords="offset points", ha="center",
                va="top", fontsize=8.5, style="italic", color="0.30")

    ax.set_yticks(ys)
    ax.set_yticklabels(P["lanes"], fontsize=9)
    ax.tick_params(axis="y", length=0)
    ax.set_xlim(60, T_MAX)
    ax.set_ylim(-LANE_GAP * 0.72, ys[0] + BOX_H / 2 + 0.50)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.grid(axis="x", color=CHANCE, alpha=0.15, linewidth=0.6)
    ax.set_axisbelow(True)
    ax.set_xlabel("Time (s)", fontsize=9, labelpad=2)

OUT = ROOT / "figures" / "fig2_14_event_scoring.png"
OUT.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(OUT, dpi=300, bbox_inches="tight", facecolor="white")
print(f"\nwrote {OUT}")

print("\ncaption text:")
print(f"  Event-based scoring. (a) A detected interval is matched to an "
      f"annotated seizure by any overlap, after the annotation is extended by "
      f"{TOL_START:g} s before onset and {TOL_END:g} s after offset; the "
      f"detection shown begins after the seizure has ended and still counts. "
      f"(b) Detections separated by less than {MERGE_GAP:g} s are merged into "
      f"one interval before scoring. (c) A detection outside the tolerance "
      f"window is a false alarm. Detections longer than {MAX_EVENT / 60:g} "
      f"minutes are split, which is not shown. The signal is synthetic and "
      f"illustrative; the scoring depends only on the interval endpoints. "
      f"Specificity is not defined at event level, because a true-negative "
      f"event has no meaning once a timeline is expressed as events; false "
      f"alarms per day replaces it.")
