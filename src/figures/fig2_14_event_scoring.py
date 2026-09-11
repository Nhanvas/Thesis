"""
Fig 2.14 - Event-based scoring rules.

Drawn to scale on a real time axis, so the 30 s pre-onset tolerance and the 60 s
post-offset tolerance are visibly different lengths and the 90 s merge gap can be
read off the axis.

The five parameters are read from src/szcore_eval.py, not typed in here: the script
imports them and stops if they are missing, so the drawing cannot drift from the
scorer.

The scenario is illustrative. It is constructed to show, in one picture, every
outcome the scoring rule can produce: a detection matched by direct overlap, a
detection matched only because it falls inside the post-offset tolerance, two
detections merged because they are closer than the merge gap, a false positive,
and a missed seizure. No number in this figure is a result.

Source of parameters: src/szcore_eval.py
Output: figures/fig2_14_event_scoring.png
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrowPatch

# --- repo imports -----------------------------------------------------------
ROOT = Path(__file__).resolve().parents[2]
for p in (ROOT / "src", ROOT / "src" / "figures"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from palette import ICTAL, DETECTED, CHANCE, HEADLINE, apply_rc  # noqa: E402

# --- parameters, read from the scorer ---------------------------------------
try:
    import szcore_eval as SZ
except Exception as exc:                                    # pragma: no cover
    sys.exit(f"FAIL: cannot import src/szcore_eval.py ({exc}). "
             "This figure must not be drawn with typed-in parameters.")


def _param(*names):
    """Return the first attribute found, else stop."""
    for n in names:
        if hasattr(SZ, n):
            return getattr(SZ, n)
    sys.exit(f"FAIL: none of {names} found in src/szcore_eval.py. "
             "Do not hard-code the value; fix the lookup.")


TOL_START = float(_param("TOLERANCE_START", "toleranceStart", "TOL_START"))
TOL_END = float(_param("TOLERANCE_END", "toleranceEnd", "TOL_END"))
MERGE_GAP = float(_param("MIN_DURATION_BETWEEN_EVENTS",
                         "minDurationBetweenEvents", "MERGE_GAP"))
MAX_EVENT = float(_param("MAX_EVENT_DURATION", "maxEventDuration", "MAX_EVENT"))

print("parameters read from src/szcore_eval.py")
print(f"  tolerance before onset : {TOL_START:g} s")
print(f"  tolerance after offset : {TOL_END:g} s")
print(f"  merge gap              : {MERGE_GAP:g} s")
print(f"  maximum event duration : {MAX_EVENT:g} s")

assert TOL_END > TOL_START, "post-offset tolerance should exceed the pre-onset one"

# --- illustrative scenario --------------------------------------------------
T_MAX = 700.0

# annotated seizures (start, end)
SEIZURES = [(100.0, 160.0), (300.0, 330.0), (480.0, 510.0)]

# raw detected intervals, before merging
RAW = [(130.0, 150.0), (175.0, 195.0), (350.0, 375.0), (600.0, 630.0)]


def merge(intervals, gap):
    out = []
    for s, e in sorted(intervals):
        if out and s - out[-1][1] < gap:
            out[-1] = (out[-1][0], e)
        else:
            out.append((s, e))
    return out


MERGED = merge(RAW, MERGE_GAP)


def matches(det, seiz):
    s, e = seiz
    return det[1] > s - TOL_START and det[0] < e + TOL_END


# outcome per merged detection, and per seizure
det_outcome, used = [], set()
for d in MERGED:
    hit = next((i for i, z in enumerate(SEIZURES) if matches(d, z)), None)
    det_outcome.append(("true positive", hit) if hit is not None
                       else ("false positive", None))
    if hit is not None:
        used.add(hit)
missed = [i for i in range(len(SEIZURES)) if i not in used]

print(f"\nscenario: {len(SEIZURES)} annotated seizures, "
      f"{len(RAW)} raw detections merged into {len(MERGED)}")
for d, (lab, hit) in zip(MERGED, det_outcome):
    print(f"  [{d[0]:6.0f}, {d[1]:6.0f}] s -> {lab}"
          + (f" (seizure {hit + 1})" if hit is not None else ""))
for i in missed:
    print(f"  seizure {i + 1} at [{SEIZURES[i][0]:.0f}, "
          f"{SEIZURES[i][1]:.0f}] s -> missed")

# --- drawing ----------------------------------------------------------------
apply_rc()
fig, ax = plt.subplots(figsize=(11.0, 4.3))

LANE = {"ref": 2.55, "raw": 1.55, "merged": 0.55}
H = 0.34

# tolerance margins, drawn first so the seizure bars sit on top
for s, e in SEIZURES:
    ax.add_patch(Rectangle((s - TOL_START, LANE["ref"] - H / 2), TOL_START, H,
                           facecolor=ICTAL, alpha=0.13, edgecolor="none",
                           zorder=1))
    ax.add_patch(Rectangle((e, LANE["ref"] - H / 2), TOL_END, H,
                           facecolor=ICTAL, alpha=0.13, edgecolor="none",
                           zorder=1))

for i, (s, e) in enumerate(SEIZURES):
    ax.add_patch(Rectangle((s, LANE["ref"] - H / 2), e - s, H,
                           facecolor=ICTAL, alpha=0.85, edgecolor=ICTAL,
                           linewidth=1.0, zorder=3))
    if i in missed:
        ax.text((s + e) / 2, LANE["ref"] - H / 2 - 0.17, "missed",
                ha="center", va="top", fontsize=8, color=ICTAL)

for s, e in RAW:
    ax.add_patch(Rectangle((s, LANE["raw"] - H / 2), e - s, H,
                           facecolor=DETECTED, alpha=0.85, edgecolor=DETECTED,
                           linewidth=1.0, zorder=3))

for d, (lab, hit) in zip(MERGED, det_outcome):
    ax.add_patch(Rectangle((d[0], LANE["merged"] - H / 2), d[1] - d[0], H,
                           facecolor=DETECTED, alpha=0.85, edgecolor=DETECTED,
                           linewidth=1.0, zorder=3))
    ax.text((d[0] + d[1]) / 2, LANE["merged"] - H / 2 - 0.17, lab,
            ha="center", va="top", fontsize=8,
            color=DETECTED if lab == "true positive" else CHANCE)

# the merge that happened, marked between the raw and merged lanes
m_a, m_b = RAW[0], RAW[1]
ax.annotate("", xy=((m_a[1] + m_b[0]) / 2, LANE["merged"] + H / 2 + 0.06),
            xytext=((m_a[1] + m_b[0]) / 2, LANE["raw"] - H / 2 - 0.06),
            arrowprops=dict(arrowstyle="-|>", color=CHANCE, linewidth=0.9,
                            shrinkA=0, shrinkB=0))
ax.text((m_a[1] + m_b[0]) / 2 + 8, (LANE["raw"] + LANE["merged"]) / 2,
        f"gap {m_b[0] - m_a[1]:.0f} s < {MERGE_GAP:g} s, joined",
        fontsize=8, style="italic", color=CHANCE, va="center")

# tolerance call-outs on the first seizure
s0, e0 = SEIZURES[0]
y_tol = LANE["ref"] + H / 2 + 0.20
ax.add_patch(FancyArrowPatch((s0 - TOL_START, y_tol), (s0, y_tol),
                             arrowstyle="<->", mutation_scale=8,
                             color=ICTAL, linewidth=0.9))
ax.text(s0 - TOL_START / 2, y_tol + 0.07, f"{TOL_START:g} s before onset",
        ha="center", va="bottom", fontsize=8, color=ICTAL)
ax.add_patch(FancyArrowPatch((e0, y_tol), (e0 + TOL_END, y_tol),
                             arrowstyle="<->", mutation_scale=8,
                             color=ICTAL, linewidth=0.9))
ax.text(e0 + TOL_END / 2, y_tol + 0.07, f"{TOL_END:g} s after offset",
        ha="center", va="bottom", fontsize=8, color=ICTAL)

# the tolerance-only match, called out on the second seizure
d_tol = MERGED[1]
ax.annotate("matched by the post-offset tolerance,\nno overlap of the annotation itself",
            xy=(d_tol[1], LANE["merged"] + H / 2 - 0.05),
            xytext=(d_tol[1] + 30, (LANE["raw"] + LANE["merged"]) / 2 + 0.08),
            ha="left", va="center", fontsize=8, color=HEADLINE,
            arrowprops=dict(arrowstyle="-", color=HEADLINE, linewidth=0.8,
                            shrinkA=2, shrinkB=2,
                            connectionstyle="angle,angleA=0,angleB=90,rad=0"))

ax.set_yticks([LANE["merged"], LANE["raw"], LANE["ref"]])
ax.set_yticklabels(["Detected intervals,\nafter merging",
                    "Detected intervals,\nas produced",
                    "Annotated seizures,\nwith tolerance"])
ax.tick_params(axis="y", length=0)
ax.set_xlim(0, T_MAX)
ax.set_ylim(-0.15, LANE["ref"] + 1.25)
ax.set_xlabel("Time (s)")
for side in ("top", "right", "left"):
    ax.spines[side].set_visible(False)
ax.grid(axis="x", color=CHANCE, alpha=0.18, linewidth=0.6)
ax.set_axisbelow(True)

fig.tight_layout()
OUT = ROOT / "figures" / "fig2_14_event_scoring.png"
OUT.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(OUT, dpi=300, bbox_inches="tight", facecolor="white")
print(f"\nwrote {OUT}")

print("\ncaption text:")
print(f"  Event-based scoring. A detected interval is matched to an annotated "
      f"seizure by any overlap after a {TOL_START:g} s tolerance before onset "
      f"and {TOL_END:g} s after offset; detections separated by less than "
      f"{MERGE_GAP:g} s are merged, and detections longer than "
      f"{MAX_EVENT / 60:g} minutes are split. The scenario shown is "
      f"illustrative and reports no result. Specificity is not defined at "
      f"event level, because a true-negative event has no meaning once a "
      f"timeline is expressed as events; false alarms per day replaces it.")
