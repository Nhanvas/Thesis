"""
diagnose_gamma_emg.py — EMG Artifact Diagnostic for Gamma AEC
3 checks per subject: channel power ratio, pair spatial distribution, amplitude CV
Usage: python src/diagnose_gamma_emg.py
"""

import numpy as np
from pathlib import Path
from scipy.signal import butter, sosfiltfilt, hilbert

DATA_DIR = Path("data/processed")
FS = 256

CHANNEL_NAMES = [
    "FP1-F7","F7-T7","T7-P7","P7-O1",
    "FP1-F3","F3-C3","C3-P3","P3-O1",
    "FP2-F4","F4-C4","C4-P4","P4-O2",
    "FP2-F8","F8-T8","T8-P8","P8-O2",
    "FZ-CZ","CZ-PZ",
]

FRONTAL  = {0, 4, 8, 12, 16}
TEMPORAL = {1, 2, 13, 14}
CENTRAL  = {5, 6, 9, 10, 17}
POSTERIOR= {3, 7, 11, 15}

def region(ch):
    if ch in FRONTAL:  return "frontal"
    if ch in TEMPORAL: return "temporal"
    if ch in CENTRAL:  return "central"
    return "posterior"

def bandpass_gamma(sig):
    sos = butter(4, [30, 60], btype="band", fs=FS, output="sos")
    return sosfiltfilt(sos, sig, axis=-1)

def gamma_stats(windows, n_sample=300, seed=42):
    np.random.seed(seed)
    idx = np.random.choice(len(windows), min(n_sample, len(windows)), replace=False)
    batch = windows[idx].astype(np.float64)       # [N, 18, 1024]
    N, C, T = batch.shape

    filtered = bandpass_gamma(batch)               # [N, 18, 1024]
    envelope = np.abs(hilbert(filtered, axis=-1))  # [N, 18, 1024]

    channel_power = (filtered ** 2).mean(axis=(0, 2))  # [18]
    channel_cv    = (envelope.std(axis=-1) /
                     (envelope.mean(axis=-1) + 1e-10)).mean(axis=0)  # [18]

    log_env = np.log(envelope + 1e-10)
    log_env -= log_env.mean(axis=-1, keepdims=True)
    std = log_env.std(axis=-1, keepdims=True) + 1e-10
    log_env /= std
    aec_matrix = (log_env @ log_env.transpose(0, 2, 1)).mean(axis=0) / T
    np.fill_diagonal(aec_matrix, 0)

    return channel_power, channel_cv, aec_matrix

def top_k_pairs(mat, k=30):
    triu = [(mat[i, j], i, j) for i in range(18) for j in range(i+1, 18)]
    triu.sort(reverse=True)
    return triu[:k]

TEST_SUBJECTS = ["chb03","chb06","chb13","chb14","chb15","chb16","chb17","chb18"]

print("=" * 68)
print("GAMMA AEC EMG DIAGNOSTIC")
print("=" * 68)

summary = {}

for subj in TEST_SUBJECTS:
    ip = DATA_DIR / f"{subj}_interictal.npy"
    cp = DATA_DIR / f"{subj}_ictal.npy"
    gp_i = DATA_DIR / f"gamma_aec_{subj}_inter.npy"
    gp_c = DATA_DIR / f"gamma_aec_{subj}_ictal.npy"

    if not ip.exists() or not cp.exists():
        print(f"\n[{subj}] raw windows not found — skip")
        continue

    inter = np.load(str(ip), mmap_mode="r")
    ictal = np.load(str(cp), mmap_mode="r")

    print(f"\n{'─'*60}")
    print(f"  {subj}  ({len(inter)} inter, {len(ictal)} ictal windows)")

    pow_i, cv_i, aec_i = gamma_stats(inter)
    pow_c, cv_c, aec_c = gamma_stats(ictal)

    # ── CHECK 1: channel power ratio ictal/interictal ──────────────
    ratio = pow_c / (pow_i + 1e-10)
    frontal_r  = ratio[list(FRONTAL)].mean()
    temporal_r = ratio[list(TEMPORAL)].mean()
    central_r  = ratio[list(CENTRAL)].mean()
    poster_r   = ratio[list(POSTERIOR)].mean()

    print(f"\n  CHECK 1 — Gamma power ratio (ictal / interictal) per region")
    print(f"    frontal   {frontal_r:.3f}  (EMG-prone region)")
    print(f"    temporal  {temporal_r:.3f}")
    print(f"    central   {central_r:.3f}")
    print(f"    posterior {poster_r:.3f}")
    top3 = np.argsort(ratio)[-3:][::-1]
    print(f"    Top-3 channels: "
          f"{[(CHANNEL_NAMES[c], f'{ratio[c]:.2f}') for c in top3]}")

    # ── CHECK 2: spatial distribution of top-30 interictal pairs ───
    pairs = top_k_pairs(aec_i, 30)
    pt_counts = {}
    for _, ci, cj in pairs:
        key = "–".join(sorted([region(ci), region(cj)]))
        pt_counts[key] = pt_counts.get(key, 0) + 1

    frontal_pair_count = sum(v for k, v in pt_counts.items() if "frontal" in k)

    print(f"\n  CHECK 2 — Top-30 interictal gamma AEC pairs by region")
    for pt, cnt in sorted(pt_counts.items(), key=lambda x: -x[1]):
        bar  = "█" * cnt
        flag = "  ← EMG suspect" if "frontal" in pt and cnt >= 8 else ""
        print(f"    {pt:25s}  {cnt:2d}/30  {bar}{flag}")

    # ── CHECK 3: amplitude CV (burstiness) ─────────────────────────
    cv_f_i = cv_i[list(FRONTAL)].mean()
    cv_f_c = cv_c[list(FRONTAL)].mean()
    cv_o_i = cv_i[list(TEMPORAL | CENTRAL | POSTERIOR)].mean()
    cv_o_c = cv_c[list(TEMPORAL | CENTRAL | POSTERIOR)].mean()

    print(f"\n  CHECK 3 — Amplitude CV (higher = more bursty = more EMG-like)")
    print(f"    frontal  CV: inter={cv_f_i:.3f}  ictal={cv_f_c:.3f}  "
          f"delta={cv_f_c-cv_f_i:+.3f}")
    print(f"    other    CV: inter={cv_o_i:.3f}  ictal={cv_o_c:.3f}  "
          f"delta={cv_o_c-cv_o_i:+.3f}")

    # ── CHECK 4: gamma z-score direction (if pre-computed scores exist) ─
    if gp_i.exists() and gp_c.exists():
        gz_i = np.load(str(gp_i))
        gz_c = np.load(str(gp_c))
        sep = np.median(gz_c) - np.median(gz_i)
        direction = "↑ CORRECT" if sep > 0 else "↓ INVERTED"
        print(f"\n  CHECK 4 — Gamma z-score direction")
        print(f"    med_inter={np.median(gz_i):.3f}  "
              f"med_ictal={np.median(gz_c):.3f}  "
              f"sep={sep:+.3f}  {direction}")

    # ── VERDICT ────────────────────────────────────────────────────
    max_non_frontal = max(temporal_r, central_r, poster_r)
    if frontal_r > 1.5 * max_non_frontal or frontal_pair_count > 15:
        risk = "HIGH"
    elif frontal_r > 1.2 * max_non_frontal or frontal_pair_count > 8:
        risk = "MODERATE"
    else:
        risk = "LOW"

    summary[subj] = risk
    print(f"\n  VERDICT: {risk} EMG RISK")

print(f"\n{'='*68}")
print("SUMMARY")
for subj, risk in summary.items():
    flag = "⚠️ " if risk != "LOW" else "✅"
    print(f"  {flag} {subj}: {risk}")