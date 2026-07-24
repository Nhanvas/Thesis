"""
================================================================================
 fig_cpd_eeg_single.py  —  ONE subject/seizure: show that PELT localizes BOTH
 the START (onset) and END (offset) of the seizure, on the real EEG.
================================================================================

The thesis claim is temporal localization of onset AND offset. So this figure
marks, from the LOCKED pipeline, the change point nearest the seizure START and
the one nearest the seizure END, and shades the detected interval between them --
compared against the true (clinical) onset/offset.

WHY chb15 (long seizure) BY DEFAULT
-----------------------------------
The score is smoothed with a 60 s window. On a SHORT seizure (e.g. chb03's 52 s)
that smoothing blurs onset and offset into one bump, so only ONE change point
survives -> you cannot see start vs end. On a LONG seizure (chb15 ~190 s) the
smoothed score has a clear plateau with a distinct rising edge (onset) and
falling edge (offset), so PELT places a change point at EACH -> start and end are
both visible. That is why the default is a long chb15 seizure.

Panels: (A) real preprocessed EEG (line) with PELT onset/offset lines + detected
span; (B) the ensemble score PELT actually cuts, same markers. SHOW_SCORE=False
-> EEG only.

ANNOTATION LAYOUT (this version)
---------------------------------
- The "PELT onset" / "PELT offset" text labels are placed in the MARGIN ABOVE
  panel A (using a blended data-x / axes-fraction-y transform), never on top of
  the EEG traces, and never behind the legend.
- ALL legend entries (from both panels) are merged into ONE horizontal legend
  row placed BELOW the entire figure (fig.legend, not per-axes legend), so
  nothing overlaps the plotted data or the annotation text.
- A footnote below the legend states the detection config (weight/pen/mag/seed)
  and the EEG display caveat (per-channel gain+clip, not a true uV scale).

FAITHFULNESS: EEG is the real filtered EDF (bandpass 0.5-60 Hz + notch 60 Hz);
only a per-channel gain + clip is applied so 18 channels stack (not true uV).
Detection is the locked pipeline (weight 0.40/0.35/0.25, v14). Nothing hand-drawn.
Run from the project code dir. Needs mne OR pyedflib.
================================================================================
"""

import os
import numpy as np
from scipy.signal import butter, sosfiltfilt, iirnotch, filtfilt
from sklearn.metrics import roc_auc_score

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.transforms as mtransforms
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.ticker import MultipleLocator

import evaluation_protocol as EP
import ensemble_recipe as ER
import szcore_eval as SE
import cpd_pipeline_v14 as V14

# ============================================================================
# CONFIG
# ============================================================================
COMP_DIR    = r"data\processed\components"
SUMMARY_DIR = r"F:\Study\Thesis\Dataset\CHB-MIT\CHB info\summary"
EDF_DIR     = r"F:\Study\Thesis\Dataset\CHB-MIT\chb15"   # <-- folder of the SUBJECT's edf
OUT_DIR     = r"F:\Study\Thesis\Code\results\figures"

SUBJECT     = "chb15"
TARGET_EDF  = "chb15_28.edf"     # single long seizure 876-1066 s (~190 s) -> onset+offset both detectable
TARGET_ONSET = None              # None -> read from summary
TARGET_OFFSET = None

PEN_MULT    = 1.0                # locked balanced OP. If only ONE CP shows (start=end),
MIN_MAG_PCT = 60                 #   drop PEN_MULT to 0.5 or 0.3 to resolve both boundaries.
CANON_SEED  = 0

SHOW_SCORE  = True               # True = EEG + score; False = EEG only
PRE_S       = 30                 # seconds shown before onset
POST_PAD_S  = 30                 # seconds shown after offset
DECIMATE    = 0                  # 0 = auto (~3500 pts/channel)
SEP         = 1.0
DISP_GAIN_SD = 0.16              # 1 interictal SD -> this * SEP (interictal readable)
DISP_CLIP   = 0.5                # clip EEG display to +/- this * SEP (raise to 0.6-0.7 for taller ictal)

CHANS = ["FP1-F7", "F7-T7", "T7-P7", "P7-O1", "FP1-F3", "F3-C3", "C3-P3", "P3-O1",
         "FP2-F4", "F4-C4", "C4-P4", "P4-O2", "FP2-F8", "F8-T8", "T8-P8", "P8-O2",
         "FZ-CZ", "CZ-PZ"]

WIN_SEC = EP.WIN_SEC
FS = 256


# ============================================================================
def _bandpass_notch(x, fs=FS, lo=0.5, hi=60.0, notch_hz=60.0, q=30.0):
    sos = butter(4, [lo, hi], btype="band", fs=fs, output="sos")
    x = sosfiltfilt(sos, x)
    b, a = iirnotch(notch_hz, q, fs)
    return filtfilt(b, a, x)


def load_edf(edf_path, chans, fs=FS):
    names, sigs = [], []
    try:
        import mne
        raw = mne.io.read_raw_edf(edf_path, preload=True, verbose="ERROR")
        avail = {c.strip().upper(): c for c in raw.ch_names}
        sr = raw.info["sfreq"]
        for c in chans:
            k = c.strip().upper()
            if k in avail:
                sigs.append(raw.get_data(picks=[avail[k]])[0]); names.append(c)
    except Exception:
        import pyedflib
        f = pyedflib.EdfReader(edf_path)
        labels = [l.strip().upper() for l in f.getSignalLabels()]
        sr = f.getSampleFrequency(0)
        for c in chans:
            k = c.strip().upper()
            if k in labels:
                sigs.append(f.readSignal(labels.index(k))); names.append(c)
        f._close()
    if not sigs:
        raise RuntimeError(f"none of the requested channels found in {edf_path}")
    data = np.vstack(sigs).astype(float)
    if abs(sr - fs) > 1e-6:
        from scipy.signal import resample
        data = resample(data, int(round(data.shape[1] * fs / sr)), axis=1)
    for i in range(data.shape[0]):
        data[i] = _bandpass_notch(data[i], fs=fs)
    return data, names


def resolve_comp_dir(comp_dir, subject):
    import glob
    probe = f"zrecon_{subject}_inter.npy"
    if os.path.exists(os.path.join(comp_dir, probe)):
        print(f"[diag] components dir: {os.path.abspath(comp_dir)}"); return comp_dir
    hits = glob.glob(os.path.join(".", "**", probe), recursive=True)
    if hits:
        found = os.path.dirname(hits[0])
        print(f"[diag] components not at default; using {os.path.abspath(found)}"); return found
    raise FileNotFoundError(
        f"{probe} not found under {os.path.abspath(comp_dir)} or below {os.path.abspath('.')}.\n"
        f"       Point COMP_DIR at the folder with zrecon_/ztemp_/zgamma_*.npy.")


def approx_global_onset_window(summary_dir, subject, target_edf, onset_s):
    edfs = EP.parse_summary_edf_list(os.path.join(summary_dir, f"{subject}-summary.txt"))
    cum = 0
    for e in edfs:
        if e["fname"] == target_edf:
            return cum + onset_s // WIN_SEC
        cum += e["duration_s"] // WIN_SEC
    raise RuntimeError(f"{target_edf} not found in summary")


def match_seizure(sz_ranges, approx_w_on, dur_s, tol_win=8):
    cand = min(sz_ranges, key=lambda r: abs(r[0] - approx_w_on))
    if abs((cand[1] - cand[0]) * WIN_SEC - dur_s) > tol_win * WIN_SEC:
        cand = min(sz_ranges, key=lambda r: abs((r[1] - r[0]) * WIN_SEC - dur_s))
    return cand


# ============================================================================
def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    edfs = EP.parse_summary_edf_list(os.path.join(SUMMARY_DIR, f"{SUBJECT}-summary.txt"))
    tgt = next((e for e in edfs if e["fname"] == TARGET_EDF), None)
    if tgt is None:
        raise RuntimeError(f"{TARGET_EDF} not in summary")
    onset_s, offset_s = (TARGET_ONSET, TARGET_OFFSET)
    if onset_s is None:
        onset_s, offset_s = tgt["seizures"][0]
    dur_s = offset_s - onset_s
    print(f"[cfg] {SUBJECT} {TARGET_EDF}  seizure {onset_s}-{offset_s}s ({dur_s}s)")

    comp_dir = resolve_comp_dir(COMP_DIR, SUBJECT)
    ens_inter, ens_ictal = ER.ensemble_for_subject(comp_dir, SUBJECT)
    y = np.concatenate([np.zeros(len(ens_inter)), np.ones(len(ens_ictal))])
    auroc = roc_auc_score(y, np.concatenate([ens_inter, ens_ictal]))
    print(f"[ens] weights={ER.ENS_WEIGHTS}  window AUROC={auroc:.4f}")

    np.random.seed(CANON_SEED)
    signal, is_ictal, is_buffer, real_inter, sz_ranges, n_inter_h = \
        SE.build_timeline_masked(SUBJECT, ens_inter, ens_ictal, SUMMARY_DIR)
    cps, smoothed = V14.detect_changepoints(signal, PEN_MULT, min_mag_pct=MIN_MAG_PCT,
                                            inter_mask=real_inter)
    cps = sorted(cps)

    w_on = approx_global_onset_window(SUMMARY_DIR, SUBJECT, TARGET_EDF, onset_s)
    (w_on, w_off) = match_seizure(sz_ranges, w_on, dur_s)
    rel_cps = [(c - w_on) * WIN_SEC for c in cps]                # 0 == clinical onset

    # CPs within SzCORE tolerance of THIS seizure -> detected boundaries
    near = sorted(rc for rc in rel_cps if -30 <= rc <= dur_s + 60)
    det_on  = min(near, key=lambda r: abs(r - 0))     if near else None   # nearest START
    det_off = min(near, key=lambda r: abs(r - dur_s)) if near else None   # nearest END
    if det_on is not None:
        print(f"[detect] PELT onset  @ {det_on:+.0f}s (true 0)   -> latency {det_on:+.0f}s")
        print(f"[detect] PELT offset @ {det_off:+.0f}s (true {dur_s}) -> error {det_off-dur_s:+.0f}s")
        if det_on == det_off:
            print("[detect] NOTE: only ONE change point near this seizure "
                  "(start=end). Lower PEN_MULT (0.5 or 0.3) to resolve both edges.")

    # --- EEG segment ---------------------------------------------------------
    data, names = load_edf(os.path.join(EDF_DIR, TARGET_EDF), CHANS)
    t_lo, t_hi = -PRE_S, dur_s + POST_PAD_S
    s0 = max(0, int((onset_s + t_lo) * FS)); s1 = min(data.shape[1], int((onset_s + t_hi) * FS))
    seg = data[:, s0:s1]; t = np.arange(seg.shape[1]) / FS + t_lo
    pre_n = int(PRE_S * FS); disp = np.empty_like(seg)
    for i in range(seg.shape[0]):
        base = seg[i, :pre_n] if pre_n > 5 else seg[i]
        med = np.median(base); mad = np.median(np.abs(base - med)) + 1e-9
        z = (seg[i] - med) / (1.4826 * mad)
        disp[i] = np.clip(z * DISP_GAIN_SD, -DISP_CLIP, DISP_CLIP)

    # --- score segment -------------------------------------------------------
    g0 = max(0, w_on + int(np.floor(t_lo / WIN_SEC)))
    g1 = min(len(smoothed), w_on + int(np.ceil(t_hi / WIN_SEC)))
    tsc = (np.arange(g0, g1) - w_on) * WIN_SEC; ysc = smoothed[g0:g1]

    # ========================= PLOT =========================================
    plt.rcParams.update({"font.family": "serif", "font.size": 9,
                         "axes.spines.top": False, "axes.spines.right": False})
    n_ch = seg.shape[0]
    span = t_hi - t_lo

    # Wide figure spanning the full canvas width. A thin dedicated legend ROW
    # sits BETWEEN panel A and panel B (its own gridspec row, no axes/spines),
    # evenly spaced from both -- replacing the old fig.legend() placed far
    # below everything at a negative y-offset.
    FIG_W = 16.0
    if SHOW_SCORE:
        fig = plt.figure(figsize=(FIG_W, 9.6))
        gs = fig.add_gridspec(3, 1, height_ratios=[2.6, 0.30, 1.0], hspace=0.07)
        axE = fig.add_subplot(gs[0, 0])
        axL = fig.add_subplot(gs[1, 0]); axL.axis("off")   # legend strip
        axS = fig.add_subplot(gs[2, 0], sharex=axE)
    else:
        fig = plt.figure(figsize=(FIG_W, 7.6))
        gs = fig.add_gridspec(2, 1, height_ratios=[2.6, 0.30], hspace=0.07)
        axE = fig.add_subplot(gs[0, 0])
        axL = fig.add_subplot(gs[1, 0]); axL.axis("off")   # legend strip
        axS = None

    # Fixed margins instead of bbox_inches="tight" combined with off-canvas
    # (negative-y) legend/footnote coordinates -- that combination was what
    # forced matplotlib to expand the canvas and left the plotted panels
    # looking shrunk inside a lot of surrounding white space.
    fig.subplots_adjust(left=0.045, right=0.995, top=0.90, bottom=0.135)

    # blended transform: x in DATA coords, y in AXES-FRACTION coords (0..1 =
    # bottom..top of the axes box). Used to place onset/offset labels in the
    # margin ABOVE panel A, regardless of the EEG y-scaling, so they never
    # overlap the traces.
    trans_top = mtransforms.blended_transform_factory(axE.transData, axE.transAxes)

    def mark_boundaries(ax):
        ax.axvline(0, color="#cc0000", lw=1.3, ls="--", alpha=0.9, zorder=5)
        ax.axvline(dur_s, color="#cc0000", lw=1.3, ls="--", alpha=0.5, zorder=5)
        if det_on is not None:
            ax.axvspan(det_on, det_off, color="#1f4e79", alpha=0.10, lw=0, zorder=1)
            ax.axvline(det_on,  color="#1f4e79", lw=1.6, ls="-",  alpha=0.9, zorder=5)
            ax.axvline(det_off, color="#1f4e79", lw=1.6, ls=(0, (1, 1)), alpha=0.9, zorder=5)

    def _ha_for(x):
        """Keep text away from clipping at the left/right edge of the axes."""
        if x < t_lo + 0.12 * span:
            return "left"
        if x > t_hi - 0.12 * span:
            return "right"
        return "center"

    # ---- Panel A: EEG ----
    for ax in ([axE, axS] if SHOW_SCORE else [axE]):
        ax.xaxis.set_major_locator(MultipleLocator(20))
        ax.grid(axis="x", color="#e3e3e3", lw=0.5, alpha=0.6, zorder=0)

    axE.axvspan(t_lo, 0, color="#cfe0f2", alpha=0.5, lw=0, zorder=0)
    axE.axvspan(0, dur_s, color="#f2d0d0", alpha=0.55, lw=0, zorder=0)
    axE.axvspan(dur_s, t_hi, color="#cfe0f2", alpha=0.5, lw=0, zorder=0)
    step = DECIMATE if DECIMATE and DECIMATE > 0 else max(1, seg.shape[1] // 3500)
    tt = t[::step]
    for i, name in enumerate(names):
        yoff = (n_ch - 1 - i) * SEP
        axE.plot(tt, disp[i, ::step] + yoff, lw=0.3, color="#222222", zorder=3)
        axE.text(t_lo - span * 0.006, yoff, name, ha="right", va="center",
                 fontsize=7, color="#444444")
    mark_boundaries(axE)

    # panel letter, top-left, well clear of the onset/offset labels below
    axE.text(-0.025, 1.22, "(A)", transform=axE.transAxes, ha="left", va="bottom",
             fontsize=10, fontweight="bold")

    # onset/offset labels: placed in the margin ABOVE the EEG stack (axes
    # fraction y > 1), never on top of a trace and never behind the legend
    # (the legend now lives below the whole figure, see below).
    if det_on is not None:
        close = (det_off is not None) and (abs(det_off - det_on) < 0.10 * span)
        axE.text(det_on, 1.05, f"PELT onset\n({det_on:+.0f}s vs true onset)",
                 transform=trans_top, ha=_ha_for(det_on), va="bottom",
                 fontsize=7.5, color="#1f4e79", clip_on=False,
                 bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.75))
        if det_off is not None and det_off != det_on:
            y_off = 1.22 if close else 1.05
            axE.text(det_off, y_off, f"PELT offset\n({det_off - dur_s:+.0f}s vs true end)",
                     transform=trans_top, ha=_ha_for(det_off), va="bottom",
                     fontsize=7.5, color="#1f4e79", clip_on=False,
                     bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.75))

    axE.set_ylim(-SEP, n_ch * SEP + 0.4); axE.set_yticks([])
    axE.set_ylabel("Preprocessed EEG\n(18-ch, scaled per channel)")

    fig.suptitle(f"{SUBJECT} / {TARGET_EDF}   |   window AUROC = {auroc:.3f}   |   "
                 f"PELT localizes seizure onset & offset (EEG bandpass 0.5\u201360 Hz)",
                 fontsize=11.5, y=0.975)

    # ---- Panel B: score ----
    if SHOW_SCORE:
        axS.axvspan(0, dur_s, color="#f2d0d0", alpha=0.4, lw=0, zorder=0)
        axS.plot(tsc, ysc, lw=0.9, color="#1f1f1f", zorder=3)
        mark_boundaries(axS)
        for rc in rel_cps:
            if t_lo <= rc <= t_hi and rc not in (det_on, det_off):
                axS.axvline(rc, color="#8aa9c9", lw=0.7, ls=":", alpha=0.7, zorder=2)
        axS.set_ylabel("Ensemble\nanomaly score")
        axS.text(-0.025, 1.05, "(B)", transform=axS.transAxes, ha="left", va="bottom",
                 fontsize=10, fontweight="bold")

    (axS if SHOW_SCORE else axE).set_xlabel("Time relative to clinical seizure onset (s)")
    axE.set_xlim(t_lo, t_hi)
    fig.align_ylabels()

    # ---- ONE combined legend, single horizontal row, IN ITS OWN STRIP ----
    # Placed in the dedicated legend row (axL) between panel A and panel B
    # (or directly under panel A when SHOW_SCORE=False), so it sits evenly
    # spaced from both panels instead of far below the whole figure.
    legend_handles = [
        Patch(facecolor="#f2d0d0", alpha=0.55, label="True seizure (clinical annotation)"),
        Line2D([0], [0], color="#cc0000", ls="--", lw=1.3, label="True onset / offset"),
        Line2D([0], [0], color="#1f4e79", ls="-",  lw=1.6, label="PELT detected onset"),
        Line2D([0], [0], color="#1f4e79", ls=":",  lw=1.6, label="PELT detected offset"),
        Patch(facecolor="#1f4e79", alpha=0.10, label="PELT detected interval"),
    ]
    if SHOW_SCORE:
        legend_handles.append(
            Line2D([0], [0], color="#8aa9c9", ls=":", lw=0.9,
                   label="Other change point (this recording, not matched here)"))

    axL.legend(handles=legend_handles, loc="center",
               bbox_to_anchor=(0.5, 0.5), ncol=len(legend_handles),
               fontsize=8.3, frameon=True, framealpha=0.95,
               columnspacing=1.4, handletextpad=0.55, borderaxespad=0.3)

    # ---- footnote: provenance + display caveat, in the fixed bottom margin ----
    footnote = (
        f"EEG: real preprocessed signal from the raw EDF (bandpass 0.5\u201360 Hz + 60 Hz notch); "
        f"per-channel gain and clipping are applied ONLY so all 18 channels stack legibly \u2014 "
        f"this is NOT a true \u00b5V amplitude scale.  "
        f"Detection: locked pipeline v14 \u2014 ensemble weight (recon, temporal, gamma) = "
        f"{ER.ENS_WEIGHTS}, pen_mult = {PEN_MULT}, magnitude filter = {MIN_MAG_PCT}th pct, "
        f"seed = {CANON_SEED}."
    )
    fig.text(0.5, 0.012, footnote, ha="center", va="bottom",
              fontsize=7.2, color="#555555", wrap=True)

    base = os.path.join(OUT_DIR, f"fig_eeg_cpd_{SUBJECT}_{TARGET_EDF.replace('.edf','')}")
    # NOTE: bbox_inches="tight" deliberately NOT used here. Combined with the
    # off-canvas legend/footnote coordinates from the previous version, it was
    # what forced matplotlib to expand the saved canvas and made the plotted
    # panels look shrunk inside a lot of surrounding white space. Margins are
    # now fixed via subplots_adjust() above, so a plain save keeps the layout
    # (full-width panels, evenly spaced legend strip) exactly as laid out.
    fig.savefig(base + ".pdf")
    fig.savefig(base + ".png", dpi=200)
    print(f"[ok] wrote {base}.pdf / .png")


if __name__ == "__main__":
    main()