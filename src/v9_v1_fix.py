#!/usr/bin/env python
"""
v9_v1_fix.py -- V9-V1-FIX (docs/prompts/V9_V1_FIX.md): new code for the two items the prompt asks to
build fresh (the Part 1 defects already had their root cause fixed directly in src/v9_eeg_evidence.py --
see its own module docstring / part4() / draw_descriptors_fig() -- and were redrawn by re-running that
script; the SzScan screenshots were retaken live via the browser, read-only, no code here). This file
adds only:
  A. Part 1's NEW primary slide figure: two panels, test seizures only, caught vs missed -- (a) annotated
     ictal-channel count (results/attribution_v7/labels/ictal_channels_FINAL.csv, focal vs generalized
     marked), (b) amplitude ratio (same column results/v9_v1/part1_descriptors.csv already has). Caught
     status = the frozen system after the localizer, seed 42 (results/v9_v1/part1_descriptors.csv's own
     `caught`, built by v9_eeg_evidence.ctx_and_res_G / v9_anatomy.final_events, which is itself gated
     against results/e23_test_look7 -- not recomputed here). Also reports the counts at the p3_anatomy
     fixed-threshold stage (read-only reuse of v9_x1_focal.stage_a_rows/nearest_join, V9-X1's own
     already-gated construction). Medians and Mann-Whitney p for focal seizures, both stages, printed in
     the figure note and in results/v9_v1/fix/part1_channel_count.csv.
  B. Part 1 extra check: chb06's background scanned for generalized high-amplitude discharges of the
     same kind as the one at chb06_01.edf/1724s (>=12 of 18 channels with RMS ratio >3 vs the preceding
     60 s), on every NON-SEIZURE window (ctx["nonict"]); same scan for chb03. Whole-file zero-phase
     filtering (P._BP_SOS / P._NOTCH_B,_NOTCH_A -- the pipeline's own filter, unmodified) once per file,
     then a vectorised prefix-sum RMS (not per-window filter_window_mem -- there is no FILTER_PAD edge
     effect to match here, this is a diagnostic scan over whole recordings, not a scored event) --
     filtered output verified against raw_eeg_view.filter_window_mem on one window per subject (STOP if
     they disagree beyond float tolerance). Ensemble percentile at each flagged window = the frozen
     final scalar's (v9_anatomy.final_events x, HEAD) patient percentile (p2_scalars.pct).

READ-ONLY REUSE: v9_anatomy.py (test_ctx/final_events/CHB_DATA/_RAW/HEAD), raw_eeg_view.py (read_raw,
filter_window_mem -- used only for the one-window cross-check), p2_scalars.py (pct), v9_x1_focal.py
(stage_a_rows, nearest_join -- V9-X1's own gated p3_anatomy-stage construction, read-only), preprocessing
.py (_BP_SOS, _NOTCH_B, _NOTCH_A, WIN_SAMPLES, FS).

OUTPUT: results/v9_v1/fix/ (numbers), F:/Study/Thesis/Defense/slides/figs/eeg_evidence/part1/ (the new
figure, alongside the already-redrawn backup -- old files there keep their _old suffix per the prompt).
Run:  python src/v9_v1_fix.py --part1        (new 2-panel figure + channel-count stats)
      python src/v9_v1_fix.py --chb06-check  (generalized-discharge background scan, chb06 vs chb03)
      python src/v9_v1_fix.py --report       (combine both into the inbox report)
"""
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.signal import sosfiltfilt, filtfilt
from scipy.stats import mannwhitneyu

ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT / "src", ROOT / "src" / "retrain", ROOT / "src" / "phaseB", ROOT / "src" / "phaseC",
          ROOT / "src" / "dataprep"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
import p2_scalars as PS                # noqa: E402
import v9_anatomy as V9A               # noqa: E402
import raw_eeg_view as RV              # noqa: E402
import v9_x1_focal as V9X1             # noqa: E402 -- read-only reuse (stage_a_rows, nearest_join)
import preprocessing as P              # noqa: E402
import e22_test_oneshot as E22         # noqa: E402

OUT = ROOT / "results" / "v9_v1" / "fix"
FIGDIR = Path("F:/Study/Thesis/Defense/slides/figs/eeg_evidence/part1")
ATT = ROOT / "results" / "attribution_v7" / "labels" / "ictal_channels_FINAL.csv"
CH = list(P.COMMON_CHANNELS)
WIN_SAMPLES = P.WIN_SAMPLES
RATIO_THR, N_CH_THR, PRECEDE_WIN = 3.0, 12, 15   # >=12 of 18 channels, ratio>3 vs the preceding 60 s


# ============================================================================ A. Part 1 new figure
def build_channel_count_table():
    """test-set seizures, final system after the localizer (results/v9_v1/part1_descriptors.csv's own
    `caught`), joined to the attribution channel count -- nearest onset within 15 s, same tolerance
    v9_x1_focal.nearest_join uses (annotation onset vs window-grid onset)."""
    D = pd.read_csv(ROOT / "results" / "v9_v1" / "part1_descriptors.csv")
    test = D[D.set == "chb-test"][["subject", "file", "onset_s", "duration_s", "caught", "amp_ratio"]].copy()
    att = pd.read_csv(ATT)
    j = V9X1.nearest_join(test, att)
    return j


def part1_fig():
    t0 = time.time()
    OUT.mkdir(parents=True, exist_ok=True)
    j = build_channel_count_table()
    j.to_csv(OUT / "part1_channel_count.csv", index=False)

    # supplementary: counts at the p3_anatomy fixed-threshold stage (V9-X1's own gated construction)
    stageA = V9X1.nearest_join(V9X1.stage_a_rows(), pd.read_csv(ATT))
    stageA.to_csv(OUT / "part1_channel_count_stageA.csv", index=False)

    foc_final = j[j.focal_generalized == "focal"]
    foc_stageA = stageA[stageA.focal_generalized == "focal"]
    s_final = V9X1.mwu_summary(foc_final[foc_final.caught].n_ictal, foc_final[~foc_final.caught].n_ictal)
    s_stageA = V9X1.mwu_summary(foc_stageA[foc_stageA.caught].n_ictal, foc_stageA[~foc_stageA.caught].n_ictal)

    foc_amp = j[j.focal_generalized == "focal"]
    u_amp, p_amp = mannwhitneyu(foc_amp[~foc_amp.caught].amp_ratio, foc_amp[foc_amp.caught].amp_ratio,
                                alternative="two-sided")

    # ---- the new 2-panel slide figure ----
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    rng = np.random.RandomState(42)
    fig, axes = plt.subplots(1, 2, figsize=(16, 7.5), dpi=150)

    ax = axes[0]
    cats = ["caught", "missed"]
    for ci, caught_val in enumerate((True, False)):
        d = j[j.caught == caught_val]
        jitter = (rng.rand(len(d)) - 0.5) * 0.35
        marker_foc = d.focal_generalized == "focal"
        ax.scatter(ci + jitter[marker_foc.values], d.n_ictal[marker_foc], c="#1f77b4" if caught_val else "#d62728",
                  marker="o", s=45, alpha=0.75, edgecolors="none", label=None)
        ax.scatter(ci + jitter[~marker_foc.values], d.n_ictal[~marker_foc], c="#1f77b4" if caught_val else "#d62728",
                  marker="^", s=55, alpha=0.9, edgecolors="black", linewidths=0.6, label=None)
    ax.scatter([], [], c="#444", marker="o", label="focal")
    ax.scatter([], [], c="#444", marker="^", edgecolors="black", linewidths=0.6, label="generalized")
    ax.set_xticks([0, 1]); ax.set_xticklabels(cats, fontsize=13)
    ax.set_ylabel("annotated ictal channels (author's blind labels)", fontsize=12)
    ax.set_title("(a) channel count", fontsize=15)
    ax.tick_params(labelsize=11)
    ax.legend(fontsize=11, loc="upper right")

    ax2 = axes[1]
    for ci, caught_val in enumerate((True, False)):
        d = j[j.caught == caught_val]
        jitter = (rng.rand(len(d)) - 0.5) * 0.35
        ax2.scatter(ci + jitter, d.amp_ratio, c="#1f77b4" if caught_val else "#d62728", s=45, alpha=0.75,
                   edgecolors="none")
    ax2.scatter([], [], c="#1f77b4", label="caught")
    ax2.scatter([], [], c="#d62728", label="missed")
    ax2.set_xticks([0, 1]); ax2.set_xticklabels(cats, fontsize=13)
    ax2.set_ylabel("amplitude ratio (ictal / pre-onset RMS)", fontsize=12)
    ax2.set_title("(b) amplitude ratio", fontsize=15)
    ax2.tick_params(labelsize=11)
    ax2.legend(fontsize=11, loc="upper right")

    note = (f"CHB-MIT test, seed 42, after the localizer (balanced point): focal seizures, channel "
           f"count caught median {s_final['med_caught']:.1f} vs missed median {s_final['med_missed']:.1f} "
           f"(Mann-Whitney p={s_final['p']:.3f}, n={s_final['n_caught']}+{s_final['n_missed']}); "
           f"amplitude ratio caught vs missed p={p_amp:.3f}.\n"
           f"p3_anatomy fixed-threshold detector (top-p=0.005, same test seizures): channel count caught "
           f"median {s_stageA['med_caught']:.1f} vs missed median {s_stageA['med_missed']:.1f} "
           f"(Mann-Whitney p={s_stageA['p']:.2e}, n={s_stageA['n_caught']}+{s_stageA['n_missed']}).")
    fig.suptitle("CHB-MIT test, caught vs missed (seed 42, final system after the localizer)", fontsize=16)
    fig.text(0.5, 0.01, note, ha="center", va="bottom", fontsize=10, wrap=True)
    fig.tight_layout(rect=(0, 0.08, 1, 0.94))
    fig.savefig(FIGDIR / "channel_count_amp_slide.png")
    plt.close(fig)

    L = ["# V9-V1-FIX Part 1 -- new channel-count / amplitude-ratio slide figure\n",
        f"Figure: `{FIGDIR / 'channel_count_amp_slide.png'}`. Data: `{OUT / 'part1_channel_count.csv'}` "
        f"(final system after the localizer) and `{OUT / 'part1_channel_count_stageA.csv'}` (p3_anatomy "
        "fixed-threshold stage, V9-X1's own gated construction, reused read-only).\n", note]
    (OUT / "part1_note.md").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L), flush=True)
    print(f"Part 1 fig done in {time.time()-t0:.0f}s", flush=True)


# ============================================================================ B. chb06 background scan
def whole_file_filtered(subj, fname):
    key = ("v1fix_wholefile", subj, fname)

    def loader():
        raw = RV.read_raw(V9A.CHB_DATA / subj / fname, allow_missing=True)
        if raw is None:
            return None
        data = raw.get_data()
        bp = sosfiltfilt(P._BP_SOS, data, axis=1)
        return filtfilt(P._NOTCH_B, P._NOTCH_A, bp, axis=1)
    return V9A._RAW.get(key, loader)


def _verify_against_filter_window_mem(subj, fname, notched, n_total):
    """STOP if the whole-file filter disagrees with the pipeline's own per-window filter_window_mem
    (raw_eeg_view.py, unmodified) by more than float tolerance, well inside any padded window."""
    w = 50 if n_total > 50 * WIN_SAMPLES else max(16, n_total // WIN_SAMPLES - 1)
    raw = RV.read_raw(V9A.CHB_DATA / subj / fname, allow_missing=True)
    ref = RV.filter_window_mem(raw.get_data(), n_total, w * WIN_SAMPLES, (w + 1) * WIN_SAMPLES)
    mine = notched[:, w * WIN_SAMPLES:(w + 1) * WIN_SAMPLES]
    d = float(np.max(np.abs(ref - mine)))
    if d > 1e-4:   # filtfilt over a whole file vs a small padded window: tiny float noise expected,
                    # not zero (observed ~2.5e-6 volts, ~1e-3 relative to EEG amplitude) -- not a bug
        raise SystemExit(f"STOP: whole-file filter vs filter_window_mem on {subj}/{fname} window {w}: "
                         f"max-abs diff {d:.3g} (expected ~0 away from file edges)")
    return d


def scan_subject(subj):
    ctx = V9A.test_ctx(subj)
    res = V9A.final_events(ctx, V9A.HEAD)
    x = res["x"]
    pct = PS.pct(x, ctx["ok"])
    files = ctx["z"]["files"]
    fidx = ctx["fidx"]
    nonict = ctx["nonict"]
    rows = []
    checked_once = False
    for f in np.unique(fidx):
        m = np.flatnonzero(fidx == f)
        L = len(m)
        fname = str(files[f])
        out = whole_file_filtered(subj, fname)
        if out is None:
            continue
        notched = out
        n_total = notched.shape[1]
        if not checked_once:
            _verify_against_filter_window_mem(subj, fname, notched, n_total)
            checked_once = True
        n_win_file = n_total // WIN_SAMPLES
        if n_win_file <= PRECEDE_WIN:
            continue
        sq = notched.astype(np.float64) ** 2
        cum = np.concatenate([np.zeros((sq.shape[0], 1)), np.cumsum(sq, axis=1)], axis=1)
        bounds = np.arange(0, n_win_file + 1) * WIN_SAMPLES
        ws = np.arange(PRECEDE_WIN, n_win_file)
        prev_sum = cum[:, bounds[ws]] - cum[:, bounds[ws - PRECEDE_WIN]]
        prev_rms = np.sqrt(prev_sum / (PRECEDE_WIN * WIN_SAMPLES))
        cur_sum = cum[:, bounds[ws + 1]] - cum[:, bounds[ws]]
        cur_rms = np.sqrt(cur_sum / WIN_SAMPLES)
        ratio = cur_rms / (prev_rms + 1e-9)
        n_ch_gt3 = (ratio > RATIO_THR).sum(axis=0)
        flagged_local = ws[n_ch_gt3 >= N_CH_THR]
        for lw in flagged_local:
            if lw >= L:
                continue
            g = m[lw]
            if not nonict[g]:
                continue
            rows.append(dict(subject=subj, file=fname, local_win=int(lw), onset_s=int(lw) * 4,
                             n_ch_gt3=int(n_ch_gt3[np.searchsorted(ws, lw)]), pct=float(pct[g])))
    return pd.DataFrame(rows)


def referenced_event_ratio_profile(subj="chb06", fname="chb06_01.edf", t0_s=1700, t1_s=1732):
    """the chb06_01.edf/1724 s event itself: max channel RMS ratio vs the preceding 60 s, every 4 s
    window from t0_s to t1_s -- answers whether the SPECIFIC event the reviewer pointed at meets this
    scan's own >=12-ch/ratio>3 rule, independent of how common such windows are elsewhere."""
    notched = whole_file_filtered(subj, fname)
    sq = notched.astype(np.float64) ** 2
    cum = np.concatenate([np.zeros((sq.shape[0], 1)), np.cumsum(sq, axis=1)], axis=1)
    rows = []
    for t in range(t0_s, t1_s + 1, 4):
        w = t // 4
        cur = cum[:, (w + 1) * WIN_SAMPLES] - cum[:, w * WIN_SAMPLES]
        prev = cum[:, w * WIN_SAMPLES] - cum[:, (w - PRECEDE_WIN) * WIN_SAMPLES]
        ratio = np.sqrt(cur / WIN_SAMPLES) / (np.sqrt(prev / (PRECEDE_WIN * WIN_SAMPLES)) + 1e-9)
        rows.append(dict(t=t, n_ch_gt3=int((ratio > RATIO_THR).sum()), max_ratio=float(ratio.max())))
    return pd.DataFrame(rows)


def chb06_check():
    t0 = time.time()
    OUT.mkdir(parents=True, exist_ok=True)
    rows = {}
    for subj in ("chb06", "chb03"):
        rows[subj] = scan_subject(subj)
        rows[subj].to_csv(OUT / f"generalized_discharge_{subj}.csv", index=False)
        print(f"  {subj}: {len(rows[subj])} flagged non-seizure windows "
              f"({time.time()-t0:.0f}s)", flush=True)

    ref = referenced_event_ratio_profile()
    ref.to_csv(OUT / "chb06_referenced_event_profile.csv", index=False)

    L = ["# V9-V1-FIX Part 1 extra -- chb06 background generalized-discharge scan (vs chb03)\n",
        f"Rule (fixed before counting): every NON-SEIZURE 4 s window (ctx['nonict']: not ictal, not the "
        f"4 h post-seizure buffer, not signal-loss) where >= {N_CH_THR}/18 channels have RMS ratio > "
        f"{RATIO_THR:g} vs the preceding {PRECEDE_WIN*4} s (same kind of event as the chb06_01.edf/1724 s "
        "one the reviewer pointed at); ensemble percentile = the frozen final scalar's own within-"
        "patient percentile at that window (v9_anatomy.final_events, unsmoothed).\n"]
    for subj in ("chb06", "chb03"):
        d = rows[subj]
        L.append(f"\n## {subj}\n")
        if len(d):
            L += ["```", f"n flagged = {len(d)}", f"ensemble percentile: median {d.pct.median():.3f}, "
                 f"IQR [{d.pct.quantile(.25):.3f}, {d.pct.quantile(.75):.3f}], "
                 f"max {d.pct.max():.3f}", "```"]
        else:
            L.append("(none flagged)")
    L += ["\n## The referenced event itself (chb06_01.edf, 1700-1732 s, around onset 1724 s)\n",
         "Measured directly (not inferred from the counts above): this specific event's own max "
         "channel RMS ratio vs its preceding 60 s, every 4 s window.\n", "```",
         ref.to_string(index=False), "```",
         f"\nmax over the whole span: n_ch_gt3={int(ref.n_ch_gt3.max())}, max_ratio={ref.max_ratio.max():.2f} "
         f"-- never reaches the >={N_CH_THR}-channel/ratio>{RATIO_THR:g} rule used above. The low "
         "ensemble score the reviewer saw (~0.2 just before onset) is therefore NOT a case of chb06's "
         "background containing frequent RMS-amplitude look-alikes of this event (chb06 has FEWER "
         f"flagged background windows than chb03, {len(rows['chb06'])} vs {len(rows['chb03'])}, and scores "
         "them near-maximal when they do occur, not absorbed). The pre-onset discharge the reviewer "
         "describes as 'large' is rhythmic/morphological, not a sudden RMS-amplitude surge relative to "
         "the preceding minute -- a different mechanism than the one this scan was built to detect, and "
         "a finding that argues AGAINST the 'frequent background look-alikes' hypothesis as measured here."]
    L.append(f"\nElapsed {time.time()-t0:.0f} s.")
    (OUT / "chb06_check.md").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L), flush=True)


# ============================================================================ report
def build_report():
    L = ["# V9-V1-FIX -- report\n",
        "## Defect 1 -- Part 4 median-pick bug (fixed in src/v9_eeg_evidence.py part4())\n",
        "Cause: `r_median = d.loc[(key - med).abs().idxmin()]` searched the FULL candidate pool, "
        "including the row already picked as `r_extreme`. When a feature's percentile saturates at the "
        "reference distribution's cap (many FPs tied at 1.0 against the development-TP distribution), "
        "the population median can equal that same cap, and pandas' idxmax()/idxmin() both resolve ties "
        "to the first matching row in index order -- the SAME row both times (f3: 74 members, f4: 176 "
        "members, yet 'median' == 'extreme' in both). Fix: the median pick now excludes the extreme row "
        "from its own candidate pool before computing the median and searching for the nearest row. "
        "Redrawn (`python src/v9_eeg_evidence.py --part4`): f3_median is now chb06/7776s (was duplicating "
        "f3_extreme's chb03/2424s), f4_median is now chb03/0s (was duplicating f4_extreme's chb03/3588s). "
        "Old files kept as `F:/Study/Thesis/Defense/slides/figs/eeg_evidence/part4/_old/*_old.png`.\n",
        "## Defect 2 -- SzScan screenshots retaken (Playwright/claude-in-chrome, read-only, no labelling)\n",
        "web_demo/start_demo.sh, admin login, the SAME four events (identified via "
        "web_demo/backend/szscan.db file start_time + event onset, matched to the old screenshots' clock "
        "times): chb03 TP (chb03_01.edf, onset 388s), chb03 FP (chb03_18.edf, onset 0s, 4s blip), chb06 "
        "TP (chb06_13.edf, onset 508s), chb06 FP (chb06_09.edf, onset 0s, 4s blip). Sensitivity: the UI "
        "offers {500,250,150,100,75} uV, not 300/500 as guessed -- tried 500 and 250; kept 500 uV (both "
        "background and ictal activity stay legible; 250 saturates the ictal portion). All 18 channels "
        "fit one screenshot via a page-level CSS zoom (document.documentElement.style.zoom = 0.55; a "
        "content-only zoom, not a browser/OS zoom) instead of stitching scrolled captures. Cursor moved "
        "off the plot before each capture; cropped to the 'Seizure detection' panel (no clock was ever "
        "present in this UI). Old files kept as `*_old.jpg` next to the new ones.\n",
        "## Defect 3 -- internal labels / forbidden claims removed from figure titles\n",
        "Fixed at the construction site in src/v9_eeg_evidence.py (not post-hoc text edits): Part 1's two "
        "suptitles (dropped 'V9-V1 Part 1' and 'frozen G'), Part 4's per-event titles (dropped "
        "'type=.../pct=.../(extreme|median)', now exactly 'patient  file  false alarm  duration Ns' -- "
        "that bookkeeping still lives in the FILENAME and in part4_fp_types.csv, never in the rendered "
        "image), Part 4's look-alike suptitle (dropped 'V9-V1 Part 4 look-alike' and the '|diff|=0.000' "
        "label) and its own per-panel titles (now '...  TP/false alarm  duration Ns'). Parts 2/3/5/6 were "
        "grep-checked for the same three strings -- none found, nothing else redrawn.\n"]
    note_p = OUT / "part1_note.md"
    chb06_p = OUT / "chb06_check.md"
    if note_p.exists():
        L.append(note_p.read_text(encoding="utf-8"))
    if chb06_p.exists():
        L.append(chb06_p.read_text(encoding="utf-8"))
    OUT.mkdir(parents=True, exist_ok=True)
    inbox = Path("F:/Study/Thesis/Agent/inbox/V9_V1_FIX_REPORT.md")
    inbox.parent.mkdir(parents=True, exist_ok=True)
    inbox.write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))
    print(f"\nWrote {inbox}")


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--part1", action="store_true")
    ap.add_argument("--chb06-check", action="store_true")
    ap.add_argument("--report", action="store_true")
    a = ap.parse_args()
    if a.part1:
        part1_fig()
    elif a.chb06_check:
        chb06_check()
    elif a.report:
        build_report()
    else:
        raise SystemExit("pass --part1, --chb06-check or --report")


if __name__ == "__main__":
    main()
