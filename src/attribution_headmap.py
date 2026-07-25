"""
================================================================================
 attribution_headmap.py — DISPLAY-ONLY visualisation of per-channel attribution
================================================================================
Renders the per-node GAE reconstruction attribution on a 10-20 head schematic.

READ THIS BEFORE USING THE OUTPUT ANYWHERE
------------------------------------------
Under pre-registration v3.1 both pre-registered validity tests returned NEGATIVE:
  * Test A -> criterion A3: ictal attribution concentration is statistically
    indistinguishable from length-matched interictal baseline fluctuation.
  * Test D -> D1 and D2 both FAIL: concentration does not discriminate true-positive
    from false-positive detections and adds nothing over anomaly score + duration.
Therefore this figure is an UNVALIDATED DISPLAY. It is evidence surfacing for human
EEG review. It is NOT localization, NOT seizure-onset-zone identification, and NOT
triage. CHB-MIT provides seizure onset/offset times only — there is no per-channel
ground truth against which any channel ranking could be checked, even in principle.
The warning is rendered ON the figure itself, deliberately, so it cannot be
separated from the image. Do not remove it.

WHY BIPOLAR DERIVATIONS ARE DRAWN AS EDGES, NOT DOTS
----------------------------------------------------
Every channel here is a DIFFERENCE between two electrodes (F7-T7 is not a location).
Painting a blob at the midpoint invents a spatial position the signal does not have,
and is exactly the rendering that makes a viewer infer a focus. Each derivation is
therefore drawn as a line segment joining its two electrodes. Adjacent derivations
share a physical electrode (FP1-F7 and F7-T7 share F7) and are inherently correlated
— which is also why attainable concentration is capped (pre-registration §1.4).

STATISTIC (identical to Stage 1 — imported, never re-defined)
  z_i = (mean_event r_i - median_interictal r_i) / MAD_interictal r_i ; ranking uses |z|

USAGE
  # one subject, median over its seizures + one panel per seizure
  python attribution_headmap.py --pernode_root data/pernode \
      --summary_dir "F:\\Study\\Thesis\\Dataset\\CHB-MIT\\CHB info\\summary" \
      --subject chb13 --summary_csv results/attribution_v3/attribution_v3_summary.csv \
      --outdir results/attribution_v3/headmaps

  # all 8 test subjects, median map each
  python attribution_headmap.py --pernode_root data/pernode --summary_dir "..." \
      --subject all --outdir results/attribution_v3/headmaps

  python attribution_headmap.py --selftest
================================================================================
"""
import argparse
import os
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection

from attribution_v3 import (abs_z, gini, find_pernode, seizure_window_blocks,
                            MAD_EPS, CH_NAMES, TOPK, TEST_SUBJS)

# ---- 10-20 scalp positions, unit head, nose up (x right, y anterior) --------
POS = {
    "FP1": (-0.31, 0.95), "FP2": (0.31, 0.95),
    "F7": (-0.81, 0.59), "F3": (-0.40, 0.45), "FZ": (0.00, 0.50),
    "F4": (0.40, 0.45), "F8": (0.81, 0.59),
    "T7": (-1.00, 0.00), "C3": (-0.50, 0.00), "CZ": (0.00, 0.00),
    "C4": (0.50, 0.00), "T8": (1.00, 0.00),
    "P7": (-0.81, -0.59), "P3": (-0.40, -0.45), "PZ": (0.00, -0.50),
    "P4": (0.40, -0.45), "P8": (0.81, -0.59),
    "O1": (-0.31, -0.95), "O2": (0.31, -0.95),
}
WARNING = ("UNVALIDATED DISPLAY — CHB-MIT has no per-channel ground truth.\n"
           "Not localization · not SOZ · not triage. Tests A and D both negative.")


def draw_head(ax):
    th = np.linspace(0, 2 * np.pi, 361)
    ax.plot(np.cos(th), np.sin(th), color="#333333", lw=1.6, zorder=1)
    ax.plot([-0.13, 0, 0.13], [0.985, 1.14, 0.985], color="#333333", lw=1.6, zorder=1)
    for s in (-1, 1):
        e = np.linspace(-np.pi / 4, np.pi / 4, 60)
        ax.plot(s * (1.0 + 0.09 * np.cos(e)), 0.09 * 3 * np.sin(e),
                color="#333333", lw=1.4, zorder=1)
    for name, (x, y) in POS.items():
        ax.scatter([x], [y], s=13, color="#888888", zorder=3)
        ax.annotate(name, (x, y), textcoords="offset points", xytext=(0, 7),
                    ha="center", fontsize=6, color="#444444", zorder=6,
                    bbox=dict(boxstyle="round,pad=0.12", fc="white", ec="none",
                              alpha=0.85))
    ax.set_xlim(-1.35, 1.35); ax.set_ylim(-1.30, 1.32)
    ax.set_aspect("equal")
    ax.set_xticks([]); ax.set_yticks([])
    for sp in ax.spines.values():
        sp.set_visible(False)


def draw_attribution(ax, az, title, subtitle=None, top_k=TOPK):
    """az: |z| vector, one value per entry of CH_NAMES (18 bipolar derivations)."""
    draw_head(ax)
    segs, vals, missing = [], [], []
    for ch, v in zip(CH_NAMES, az):
        a, b = ch.split("-")
        if a not in POS or b not in POS:
            missing.append(ch); continue
        segs.append([POS[a], POS[b]]); vals.append(v)
    if missing:
        raise KeyError(f"unknown electrode(s) in {missing}")
    vals = np.asarray(vals, dtype=float)
    vmax = float(np.nanmax(vals)) if np.isfinite(vals).any() else 1.0
    lc = LineCollection(segs, cmap="magma_r", linewidths=3.4, zorder=2,
                        norm=plt.Normalize(0, vmax if vmax > 0 else 1.0))
    lc.set_array(vals)
    ax.add_collection(lc)

    # top-k halo: a WIDER line drawn UNDERNEATH the coloured line (zorder < lc).
    # Must use `colors=`; `edgecolors=` is ignored by LineCollection, which is why
    # an earlier version rendered no highlight at all.
    order = np.argsort(vals)[::-1][:top_k]
    hi = [segs[i] for i in order]
    ax.add_collection(LineCollection(hi, colors=["#1f77b4"] * len(hi),
                                     linewidths=8.0, alpha=0.40, zorder=1.7,
                                     capstyle="round"))
    ax.set_title(title, fontsize=10, pad=6)
    if subtitle:
        ax.set_xlabel(subtitle, fontsize=7.5, color="#444444", labelpad=6, wrap=True)
        ax.xaxis.set_visible(True)
        ax.set_xticks([])
        for sp in ax.spines.values():
            sp.set_visible(False)
    return lc, [CH_NAMES[i] for i in order]


def subject_maps(subj, pernode_root, summary_dir, outdir, parse_fn, win_sec,
                 per_seizure=True, ctx=None):
    p_int = find_pernode(pernode_root, subj, "inter")
    p_ict = find_pernode(pernode_root, subj, "ictal")
    if p_int is None or p_ict is None:
        raise FileNotFoundError(f"{subj}: per-node arrays not found under {pernode_root}")
    inter = np.load(p_int).astype(float)
    ictal = np.load(p_ict).astype(float)
    med = np.median(inter, axis=0)
    mad = np.median(np.abs(inter - med), axis=0) + MAD_EPS

    blocks, _ = seizure_window_blocks(subj, summary_dir, win_sec, parse_fn)
    azs, ginis = [], []
    for blk in blocks:
        blk = blk[blk < ictal.shape[0]]
        if blk.size == 0:
            continue
        a = abs_z(ictal[blk], med, mad)
        azs.append(a); ginis.append(gini(a))
    if not azs:
        raise RuntimeError(f"{subj}: no usable seizure blocks")

    os.makedirs(outdir, exist_ok=True)
    med_az = np.median(np.vstack(azs), axis=0)

    # ---- subject-level median map ------------------------------------------
    fig, ax = plt.subplots(figsize=(6.6, 7.0))
    sub = f"median over {len(azs)} seizures  ·  Gini {np.median(ginis):.3f}"
    if ctx and subj in ctx:
        c = ctx[subj]
        sub += (f"\nnull median {c['null']:.3f}  ·  deviation {c['dev']:+.3f}"
                f"  ·  p = {c['p']:.3f}  →  indistinguishable from baseline")
    else:
        sub += "\n[no --summary_csv: null / p context missing]"
    lc, top = draw_attribution(ax, med_az, f"{subj} — per-node attribution |z|", sub)
    cb = fig.colorbar(lc, ax=ax, fraction=.042, pad=.02,
                      label="|z| (robust, vs interictal)")
    cb.ax.tick_params(labelsize=8)
    cb.set_label("|z| (robust, vs interictal)", fontsize=8.5)
    fig.text(.5, .105, "colour scale is PER SUBJECT — do not compare intensity "
             "between subjects", ha="center", fontsize=7, color="#555555",
             style="italic")
    fig.text(.5, .035, WARNING, ha="center", fontsize=8, color="#b00020")
    # right margin must leave room for the colorbar TICK LABELS *and* its axis
    # label; .97 clipped both in an earlier version.
    fig.subplots_adjust(left=.03, right=.855, top=.94, bottom=.20)
    out = os.path.join(outdir, f"headmap_{subj}_median.png")
    fig.savefig(out, dpi=170); plt.close(fig)
    print(f"  {subj}: top-{TOPK} = {', '.join(top)}  -> {out}")

    # ---- per-seizure grid ---------------------------------------------------
    if per_seizure and len(azs) > 1:
        n = len(azs); cols = min(4, n); rows = int(np.ceil(n / cols))
        fig, axes = plt.subplots(rows, cols, figsize=(3.5 * cols, 4.2 * rows))
        axes = np.atleast_1d(axes).ravel()
        for i, (a, g) in enumerate(zip(azs, ginis)):
            draw_attribution(axes[i], a, f"seizure {i+1}  ·  Gini {g:.3f}")
        for j in range(len(azs), len(axes)):
            axes[j].set_visible(False)
        fig.suptitle(f"{subj} — per-seizure attribution (display only) · "
                     "colour scale is per panel", fontsize=11)
        fig.text(.5, .012, WARNING, ha="center", fontsize=8, color="#b00020")
        fig.tight_layout(rect=[0, .05, 1, .965])
        fig.subplots_adjust(hspace=.30)
        out2 = os.path.join(outdir, f"headmap_{subj}_perseizure.png")
        fig.savefig(out2, dpi=150); plt.close(fig)
        print(f"          per-seizure grid -> {out2}")
    return top


def load_context(path):
    """Optional: pull each subject's Gini / null median / p from Stage 1 output so
    the figure carries its own falsification context instead of a bare ranking."""
    if not path or not os.path.exists(path):
        return None
    import csv
    ctx = {}
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            ctx[r["subject"]] = dict(null=float(r["gini_null_median"]),
                                     dev=float(r["signed_deviation"]),
                                     p=float(r["p_raw"]))
    return ctx


def selftest():
    print("=== SELF-TEST (synthetic) ===")
    ok = True
    for ch in CH_NAMES:
        a, b = ch.split("-")
        ok &= a in POS and b in POS
    print(f" all 18 derivations map to 10-20 positions: {ok}")

    root = "/home/claude/fake3"
    pdir, sdir = f"{root}/pernode", f"{root}/summary"
    os.makedirs(pdir, exist_ok=True); os.makedirs(sdir, exist_ok=True)
    rng = np.random.default_rng(5)
    np.save(f"{pdir}/chbXX_interictal_pernode.npy", rng.normal(0, 1, (3000, 18)))
    ic = rng.normal(0, 1, (60, 18)); ic[:, [1, 2]] += 6.0     # F7-T7, T7-P7
    np.save(f"{pdir}/chbXX_ictal_pernode.npy", ic)
    with open(f"{sdir}/chbXX-summary.txt", "w") as f:
        for h, (a, b) in enumerate([(100, 220), (300, 420)]):
            f.write(f"File Name: x{h}.edf\nFile Start Time: 0{h}:00:00\n"
                    f"File End Time: 0{h+1}:00:00\nNumber of Seizures in File: 1\n"
                    f"Seizure Start Time: {a} seconds\n"
                    f"Seizure End Time: {b} seconds\n\n")
    from evaluation_protocol import parse_summary_edf_list as pf
    top = subject_maps("chbXX", pdir, sdir, f"{root}/out", pf, 4)
    print(f" injected F7-T7/T7-P7 recovered in top-5: "
          f"{'F7-T7' in top and 'T7-P7' in top}")
    ok &= "F7-T7" in top and "T7-P7" in top
    for fn in ["headmap_chbXX_median.png", "headmap_chbXX_perseizure.png"]:
        e = os.path.exists(f"{root}/out/{fn}"); ok &= e
        print(f" output {fn}: {'OK' if e else 'MISSING'}")
    print("\n=== SELF-TEST", "PASSED" if ok else "FAILED", "===")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(description="Attribution head map (display only)")
    ap.add_argument("--pernode_root"); ap.add_argument("--summary_dir")
    ap.add_argument("--subject", default="all")
    ap.add_argument("--summary_csv", default=None,
                    help="attribution_v3_summary.csv — adds null/p context to the figure")
    ap.add_argument("--outdir", default="results/attribution_v3/headmaps")
    ap.add_argument("--no_per_seizure", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(selftest())
    if not (a.pernode_root and a.summary_dir):
        ap.error("--pernode_root and --summary_dir are required")
    import evaluation_protocol as E
    subs = TEST_SUBJS if a.subject == "all" else [a.subject]

    # ---- fail fast, with a readable message, before any per-subject work ----
    if not os.path.isdir(a.summary_dir):
        sys.exit(f"ERROR: --summary_dir is not a directory:\n  "
                 f"{os.path.abspath(a.summary_dir)}\n"
                 "If you copied a placeholder from the usage example, replace it "
                 "with the real path, e.g.\n"
                 '  --summary_dir "F:\\Study\\Thesis\\Dataset\\CHB-MIT\\CHB info\\summary"')
    if not os.path.isdir(a.pernode_root):
        sys.exit(f"ERROR: --pernode_root is not a directory:\n  "
                 f"{os.path.abspath(a.pernode_root)}")
    missing = [s for s in subs
               if not os.path.exists(os.path.join(a.summary_dir, f"{s}-summary.txt"))]
    if missing:
        seen = sorted(f for f in os.listdir(a.summary_dir) if f.endswith(".txt"))
        sys.exit(f"ERROR: summary file(s) missing for {', '.join(missing)} in\n  "
                 f"{os.path.abspath(a.summary_dir)}\n"
                 f"  {len(seen)} .txt file(s) there"
                 + (":\n    " + "\n    ".join(seen[:12]) if seen else ""))
    if a.summary_csv and not os.path.exists(a.summary_csv):
        print(f"  [warn] --summary_csv not found ({a.summary_csv}); figures will "
              "show the ranking WITHOUT its null/p context. Strongly discouraged.\n")

    ctx = load_context(a.summary_csv)
    print("DISPLAY ONLY — attribution is unvalidated (Tests A and D negative).\n")
    for s in subs:
        subject_maps(s, a.pernode_root, a.summary_dir, a.outdir,
                     E.parse_summary_edf_list, E.WIN_SEC,
                     per_seizure=not a.no_per_seizure, ctx=ctx)


if __name__ == "__main__":
    main()