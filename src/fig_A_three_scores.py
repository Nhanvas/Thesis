#!/usr/bin/env python3
"""
fig_A_three_scores.py
Three-Signal Anomaly Score Decomposition — All 8 Test Subjects

Shows z_recon, z_temporal, |z_gamma| per 4-second window for each subject.
Seizure periods shaded. PELT TP change points (pen=0.3) marked.
Layout: 4x2 grid. No FCP/h reported.

Usage: python src/fig_A_three_scores.py
"""

import re
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import ruptures as rpt

# ── Config ───────────────────────────────────────────────────────────────────
DATA_DIR    = Path("data/processed")
TEMP_DIR    = Path("data/processed/temporal_zscores")
SCORES_DIR  = Path("results/cpd/scores")
OUT_DIR     = Path("results/cpd/figures")
SUMMARY_DIR = Path(r"F:\Study\Thesis\Dataset\CHB-MIT\CHB info\summary")
OUT_DIR.mkdir(parents=True, exist_ok=True)

WIN_SEC  = 4
BUFFER_H = 4
PEN      = 0.3
TOL_S    = 30
W_R, W_T, W_G = 0.35, 0.30, 0.35

TEST_SUBJS = ["chb03", "chb06", "chb13", "chb14", "chb15", "chb16", "chb17", "chb18"]

AUROC_MAP = {
    "chb03": 0.9579, "chb06": 0.4401, "chb13": 0.8163, "chb14": 0.7301,
    "chb15": 0.8192, "chb16": 0.9095, "chb17": 0.7729, "chb18": 0.9194,
}
DR_MAP = {
    "chb03": "7/7", "chb06": "6/10", "chb13": "11/12", "chb14": "5/8",
    "chb15": "19/20", "chb16": "8/10", "chb17": "2/3", "chb18": "6/6",
}

# ── Helpers ──────────────────────────────────────────────────────────────────
def rznorm(a, b):
    s = np.concatenate([a, b])
    med = np.median(s)
    mad = np.median(np.abs(s - med)) + 1e-9
    return (a - med) / mad, (b - med) / mad


def parse_time_hms(t):
    p = t.strip().split(":")
    return int(p[0]) * 3600 + int(p[1]) * 60 + int(p[2])


def parse_summary(path):
    text = Path(path).read_text()
    pat = re.compile(
        r"File Name:\s*(\S+\.edf)\s+File Start Time:\s*(\S+)\s+"
        r"File End Time:\s*(\S+)\s+Number of Seizures in File:\s*(\d+)(.*?)(?=File Name:|$)",
        re.DOTALL,
    )
    edfs = []
    for m in pat.finditer(text):
        fn, t0, t1, nsz, rest = m.groups()
        dur = parse_time_hms(t1) - parse_time_hms(t0)
        if dur <= 0:
            dur += 86400
        szs = []
        if int(nsz) > 0:
            ons = [int(x) for x in re.findall(r"Seizure.*?Start Time.*?:\s*(\d+)", rest, re.I)]
            ofs = [int(x) for x in re.findall(r"Seizure.*?End Time.*?:\s*(\d+)",   rest, re.I)]
            szs = list(zip(ons, ofs))
        edfs.append({"fname": fn, "duration_s": dur, "seizures": szs})
    edfs.sort(key=lambda x: x["fname"])
    return edfs


def build_timeline_indexed(subj, inter_scores, ictal_scores):
    """Timeline reconstruction; also returns idx_map for EEG window lookup."""
    np.random.seed(42)
    edfs = parse_summary(SUMMARY_DIR / f"{subj}-summary.txt")
    tl, is_ic, idx_map = [], [], []
    ip = icp = 0
    total_is = 0.0
    pool = np.random.choice(inter_scores, size=250_000, replace=True)
    bp = 0

    for edf in edfs:
        dur = edf["duration_s"]
        nw  = dur // WIN_SEC
        lab = np.zeros(dur, dtype=np.int8)
        buf = np.zeros(dur, dtype=bool)
        for on, off in edf["seizures"]:
            on = min(on, dur); off = min(off, dur)
            lab[on:off] = 1
            buf[off : min(dur, off + BUFFER_H * 3600)] = True
        tlen = nw * WIN_SEC
        wl = lab[:tlen].reshape(nw, WIN_SEC).max(axis=1)
        wb = buf[:tlen].reshape(nw, WIN_SEC).any(axis=1)

        for w in range(nw):
            if wl[w] == 1:
                tl.append(float(ictal_scores[icp]) if icp < len(ictal_scores) else 0.0)
                idx_map.append(("ictal", icp if icp < len(ictal_scores) else -1))
                if icp < len(ictal_scores):
                    icp += 1
                is_ic.append(True)
            elif wb[w]:
                tl.append(float(pool[bp])); idx_map.append(("buffer", -1))
                bp = (bp + 1) % len(pool)
                is_ic.append(False); total_is += WIN_SEC
            else:
                if ip < len(inter_scores):
                    tl.append(float(inter_scores[ip])); idx_map.append(("inter", ip))
                    ip += 1
                else:
                    tl.append(float(pool[bp])); idx_map.append(("buffer", -1))
                    bp = (bp + 1) % len(pool)
                is_ic.append(False); total_is += WIN_SEC

    if ip < len(inter_scores):
        for i in range(ip, len(inter_scores)):
            tl.append(float(inter_scores[i])); idx_map.append(("inter", i))
            is_ic.append(False); total_is += WIN_SEC

    tl_arr = np.array(tl, dtype=np.float32)
    ic_arr = np.array(is_ic, dtype=bool)
    sz_ranges = []
    in_s = False; ss = 0
    for i, ic in enumerate(ic_arr):
        if ic and not in_s:  ss = i; in_s = True
        elif not ic and in_s: sz_ranges.append((ss, i)); in_s = False
    if in_s: sz_ranges.append((ss, len(ic_arr)))

    return tl_arr, sz_ranges, total_is / 3600.0, idx_map


def apply_map(comp_i, comp_c, idx_map):
    """Apply a pre-built index map to a different component array."""
    out = []
    for src, ptr in idx_map:
        if src == "inter" and 0 <= ptr < len(comp_i):
            out.append(float(comp_i[ptr]))
        elif src == "ictal" and 0 <= ptr < len(comp_c):
            out.append(float(comp_c[ptr]))
        else:
            out.append(0.0)
    return np.array(out, dtype=np.float32)


def run_pelt(sig, pen):
    n = len(sig)
    if n < 10: return []
    med = np.median(sig); mad = np.median(np.abs(sig - med)) + 1e-9
    s2 = (1.4826 * mad) ** 2
    if s2 < 1e-10: s2 = 1.0
    algo = rpt.Pelt(model="l2", min_size=3, jump=5).fit(sig.reshape(-1, 1))
    return [c for c in algo.predict(pen=pen * s2 * np.log(n)) if c < n]


def find_tp_cps(cps, sz_ranges, tol_win):
    tp = []
    for ss, _ in sz_ranges:
        hits = [c for c in cps if abs(c - ss) <= tol_win]
        if hits:
            tp.append(min(hits, key=lambda c: abs(c - ss)))
    return sorted(set(tp))


# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    np.random.seed(42)
    print("Generating Figure A: Three-signal score decomposition")

    fig, axes = plt.subplots(4, 2, figsize=(16, 14))
    axes = axes.flatten()
    tol_win = TOL_S // WIN_SEC

    for idx, subj in enumerate(TEST_SUBJS):
        ax = axes[idx]
        print(f"  {subj} ...", end="", flush=True)

        # Load and normalise component scores
        ens_i   = np.load(SCORES_DIR / f"{subj}_ens_inter.npy")
        ens_c   = np.load(SCORES_DIR / f"{subj}_ens_ictal.npy")
        z_t_i, z_t_c = rznorm(
            np.load(TEMP_DIR / f"temporal_{subj}_zinter.npy"),
            np.load(TEMP_DIR / f"temporal_{subj}_zictal.npy"),
        )
        gai, gac = (lambda a, b: (np.abs(a), np.abs(b)))(
            *rznorm(
                np.load(DATA_DIR / f"gamma_aec_{subj}_inter.npy"),
                np.load(DATA_DIR / f"gamma_aec_{subj}_ictal.npy"),
            )
        )

        ni = min(len(ens_i), len(z_t_i), len(gai))
        nc = min(len(ens_c), len(z_t_c), len(gac))

        # Derive z_recon from the cached ensemble
        z_r_i = (ens_i[:ni] - W_T * z_t_i[:ni] - W_G * gai[:ni]) / W_R
        z_r_c = (ens_c[:nc] - W_T * z_t_c[:nc] - W_G * gac[:nc]) / W_R

        # Build timeline (ensemble gives the window ordering)
        tl_ens, sz_ranges, _, idx_map = build_timeline_indexed(
            subj, ens_i[:ni], ens_c[:nc]
        )

        # Project each component onto the same timeline structure
        tl_r = apply_map(z_r_i, z_r_c, idx_map)
        tl_t = apply_map(z_t_i[:ni], z_t_c[:nc], idx_map)
        tl_g = apply_map(gai, gac, idx_map)

        def sm(arr, w=7):
            return pd.Series(arr).rolling(w, min_periods=1, center=True).mean().values

        # PELT on 1-min smoothed ensemble
        ens_sm = pd.Series(tl_ens).rolling(15, min_periods=1, center=True).mean().values
        cps     = sorted(run_pelt(ens_sm, PEN))
        tp_cps  = find_tp_cps(cps, sz_ranges, tol_win)

        # Time axis (hours) with downsampling for display
        t_h  = np.arange(len(tl_ens)) * WIN_SEC / 3600.0
        step = max(1, len(tl_ens) // 5000)

        ax.plot(t_h[::step], sm(tl_r)[::step],
                color="#1565C0", lw=0.9, alpha=0.85, label=r"$z_{recon}$ (Reconstruction)")
        ax.plot(t_h[::step], sm(tl_t)[::step],
                color="#E65100", lw=0.9, alpha=0.85, label=r"$z_{temporal}$ (LSTM)")
        ax.plot(t_h[::step], sm(tl_g)[::step],
                color="#2E7D32", lw=0.9, alpha=0.85, label=r"$|z_{gamma}|$ (Gamma AEC)")

        for k, (ss, se) in enumerate(sz_ranges):
            ax.axvspan(t_h[ss], t_h[min(se, len(t_h) - 1)],
                       color="#EF5350", alpha=0.22,
                       label="Seizure period" if k == 0 else None)

        shown = False
        for cp in tp_cps:
            ax.axvline(t_h[cp], color="#1A237E", lw=1.6, ls="--", alpha=0.80,
                       label="PELT CP  (pen=0.3)" if not shown else None)
            shown = True

        ax.axhline(0, color="gray", lw=0.5, ls=":")

        if subj == "chb17":
            ax.set_ylim(-3, 12)
            ax.text(0.01, 0.96, "y clipped — multi-session baseline drift",
                    transform=ax.transAxes, fontsize=7, style="italic",
                    color="#B71C1C", va="top")
        else:
            vals = np.concatenate([sm(tl_r), sm(tl_t), sm(tl_g)])
            lo, hi = np.percentile(vals, 1), np.percentile(vals, 99)
            ax.set_ylim(lo - 0.5, hi + 0.5)

        ax.set_title(
            f"{subj}  |  AUROC = {AUROC_MAP[subj]:.4f}  |  "
            f"Event DR = {DR_MAP[subj]}  (pen = 0.3)",
            fontsize=9.5, fontweight="bold",
        )
        ax.set_xlabel("Recording time (hours)", fontsize=8)
        ax.set_ylabel("z-score", fontsize=8)
        ax.tick_params(labelsize=7)
        ax.grid(True, alpha=0.18, lw=0.5)
        if idx == 0:
            ax.legend(fontsize=7.5, loc="upper right", ncol=2, framealpha=0.85)
        print(" done")

    fig.suptitle(
        "Three-Signal Anomaly Score Decomposition — All 8 Test Subjects\n"
        "Blue: GAE reconstruction  ·  Orange: LSTM temporal transition  ·  Green: Gamma AEC",
        fontsize=11, fontweight="bold", y=0.999,
    )
    plt.tight_layout(rect=[0, 0, 1, 0.975])
    out = OUT_DIR / "figA_three_scores_8subjects.png"
    plt.savefig(out, dpi=250, bbox_inches="tight")
    plt.close()
    print(f"\n→ Saved: {out}")


if __name__ == "__main__":
    main()