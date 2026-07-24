"""
fig_raw_eeg_pelt_8subj.py
4 rows x 2 columns  (8 test subjects)
Each panel: 18-channel preprocessed EEG around seizure 1.
Red dashed  = annotated seizure onset
Red shading = annotated seizure period
Blue dotted = PELT change point  (pen = 0.3)
Δ  in title = detection latency relative to annotation
"""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import ruptures as rpt
import re
from pathlib import Path

DATA_DIR    = Path("data/processed")
SCORES_DIR  = Path("results/cpd/scores")
OUT_DIR     = Path("results/cpd/figures")
SUMMARY_DIR = Path(r"F:\Study\Thesis\Dataset\CHB-MIT\CHB info\summary")
OUT_DIR.mkdir(parents=True, exist_ok=True)

WIN_SEC  = 4
FS       = 256
WIN_SAMP = FS * WIN_SEC   # 1024 samples / window
N_PRE    = 10             # interictal windows shown before seizure  (40 s)
PEN      = 0.3

TEST_SUBJS = ["chb03","chb06","chb13","chb14","chb15","chb16","chb17","chb18"]
AUROC_MAP  = {
    "chb03":0.9518,"chb06":0.4093,"chb13":0.8191,"chb14":0.8624,
    "chb15":0.7915,"chb16":0.8973,"chb17":0.7455,"chb18":0.9253,
}
CHANNEL_NAMES = [
    "FP1-F7","F7-T7","T7-P7","P7-O1",
    "FP1-F3","F3-C3","C3-P3","P3-O1",
    "FP2-F4","F4-C4","C4-P4","P4-O2",
    "FP2-F8","F8-T8","T8-P8","P8-O2",
    "FZ-CZ","CZ-PZ",
]
N_CH = 18


def parse_time_hms(t):
    p = t.strip().split(":")
    return int(p[0]) * 3600 + int(p[1]) * 60 + int(p[2])


def get_seizure1_windows(subj):
    """
    Return (onset_s, n_windows) of the FIRST annotated seizure.
    Parses the subject's summary file in chronological file order.
    """
    text = (SUMMARY_DIR / f"{subj}-summary.txt").read_text()
    pat  = re.compile(
        r"File Name:\s*(\S+\.edf)\s+File Start Time:\s*(\S+)\s+"
        r"File End Time:\s*(\S+)\s+Number of Seizures in File:\s*(\d+)(.*?)(?=File Name:|$)",
        re.DOTALL,
    )
    for m in pat.finditer(text):
        _, _, _, nsz, rest = m.groups()
        if int(nsz) == 0:
            continue
        ons = [int(x) for x in re.findall(r"Seizure.*?Start Time.*?:\s*(\d+)", rest, re.I)]
        ofs = [int(x) for x in re.findall(r"Seizure.*?End Time.*?:\s*(\d+)",   rest, re.I)]
        if ons and ofs:
            dur = max(ofs[0] - ons[0], WIN_SEC)
            return ons[0], max(1, dur // WIN_SEC)
    return None, 0


def run_pelt_segment(scores_1d, pen):
    """Run PELT on a short 1-D segment.  Returns list of CP window indices."""
    n = len(scores_1d)
    if n < 4:
        return []
    med = np.median(scores_1d)
    mad = np.median(np.abs(scores_1d - med)) + 1e-9
    s2  = max((1.4826 * mad) ** 2, 1e-10)
    algo = rpt.Pelt(model="l2", min_size=2, jump=1).fit(scores_1d.reshape(-1, 1))
    cps  = algo.predict(pen=pen * s2 * np.log(n))
    return [c for c in cps if c < n]


def main():
    print("Generating fig_raw_eeg_pelt_8subj ...")

    fig, axes = plt.subplots(4, 2, figsize=(22, 30))
    plt.subplots_adjust(hspace=0.20, wspace=0.07)
    axes_flat = axes.flatten()

    for idx, subj in enumerate(TEST_SUBJS):
        ax = axes_flat[idx]
        print(f"  {subj} ...", end=" ", flush=True)

        # ── Seizure 1 info ──────────────────────────────────────────────────
        onset_s, n_ictal_1 = get_seizure1_windows(subj)
        if onset_s is None:
            ax.set_title(f"{subj} — seizure annotation not found", fontsize=10)
            print("skipped"); continue

        # ── Load preprocessed EEG slices  (mmap → copy only what we need) ──
        inter_raw = np.load(DATA_DIR / f"{subj}_interictal.npy", mmap_mode="r")
        ictal_raw = np.load(DATA_DIR / f"{subj}_ictal.npy",      mmap_mode="r")

        n_pre_use   = min(N_PRE,      len(inter_raw))
        n_ictal_use = min(n_ictal_1,  len(ictal_raw))

        inter_seg = np.array(inter_raw[-n_pre_use:])    # [N_pre,   18, 1024]
        ictal_seg = np.array(ictal_raw[:n_ictal_use])   # [N_ictal, 18, 1024]
        del inter_raw, ictal_raw

        # Stitch windows into continuous [18, total_samples] array
        eeg_win  = np.concatenate([inter_seg, ictal_seg], axis=0)  # [T, 18, 1024]
        N_total  = len(eeg_win)
        eeg_all  = eeg_win.transpose(1, 0, 2).reshape(N_CH, -1)   # [18, T*1024]

        # ── Ensemble score segment (already z-normalised) ───────────────────
        ens_i = np.load(SCORES_DIR / f"{subj}_ens_inter.npy")
        ens_c = np.load(SCORES_DIR / f"{subj}_ens_ictal.npy")

        scores_seg = np.concatenate([
            ens_i[-n_pre_use:],
            ens_c[:n_ictal_use],
        ])

        # ── PELT on score segment ───────────────────────────────────────────
        cps = run_pelt_segment(scores_seg, PEN)
        # Pick the CP closest to the true onset boundary (index = n_pre_use)
        best_cp   = min(cps, key=lambda c: abs(c - n_pre_use)) if cps else None
        latency_s = (best_cp - n_pre_use) * WIN_SEC if best_cp is not None else None

        # ── Plot 18 EEG channels ────────────────────────────────────────────
        OFFSET = 4.5
        t_sec  = np.arange(eeg_all.shape[1]) / FS

        for ch in range(N_CH):
            trace = eeg_all[ch].copy().astype(np.float32)
            pp    = np.ptp(trace) + 1e-9
            trace = (trace - trace.mean()) / pp * 2.0   # scale to ±2 for display
            y_pos = (N_CH - 1 - ch) * OFFSET
            ax.plot(t_sec, trace + y_pos,
                    color="#37474F", lw=0.35, alpha=0.80)

        # ── Seizure annotation ──────────────────────────────────────────────
        onset_t  = n_pre_use   * WIN_SEC
        end_sz_t = onset_t + n_ictal_use * WIN_SEC

        ax.axvspan(onset_t, end_sz_t, color="#EF5350", alpha=0.12,
                   label="Annotated seizure")
        ax.axvline(onset_t, color="#C62828", lw=1.8, ls="--",
                   label="Seizure onset")

        # ── PELT change point ───────────────────────────────────────────────
        if best_cp is not None:
            cp_t_abs = best_cp * WIN_SEC
            lat_lbl  = f"PELT CP  (Δ = {latency_s:+.0f} s)"
            ax.axvline(cp_t_abs, color="#1565C0", lw=1.8, ls=":",
                       label=lat_lbl)

        # ── Axis formatting ─────────────────────────────────────────────────
        ax.set_yticks([(N_CH - 1 - ch) * OFFSET for ch in range(N_CH)])
        ax.set_yticklabels(CHANNEL_NAMES, fontsize=6.5)
        ax.set_xlim(0, N_total * WIN_SEC)
        ax.set_xlabel("Time (s from segment start)", fontsize=8.5)
        ax.tick_params(axis="x", labelsize=8)
        ax.grid(axis="x", alpha=0.22)

        lat_disp = f"Δ = {latency_s:+.0f} s" if latency_s is not None else "No CP detected"
        ax.set_title(
            f"{subj}  |  AUROC = {AUROC_MAP[subj]:.3f}  |  {lat_disp}",
            fontsize=10, fontweight="bold",
        )
        ax.legend(loc="upper right", fontsize=7.5, framealpha=0.88)
        print("done")

    fig.suptitle(
        "Preprocessed EEG with PELT Change Point Detection (pen = 0.3) — All 8 Test Subjects\n"
        "Red shading: annotated seizure   |   Blue dotted line: PELT-detected onset   |   "
        "Δ = detection latency relative to annotation",
        fontsize=11, fontweight="bold", y=1.002,
    )

    out = OUT_DIR / "fig_raw_eeg_pelt_8subj.png"
    plt.savefig(out, dpi=180, bbox_inches="tight")
    plt.close()
    print(f"\nSaved → {out}")


if __name__ == "__main__":
    main()