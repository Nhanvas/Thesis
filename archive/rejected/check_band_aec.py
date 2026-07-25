# src/check_band_aec.py
"""
Pre-check: Does delta/gamma AEC increase during chb06 seizures?
If yes → band-specific AEC could fix chb06 inverted detection.
Runs on existing raw windows (no adjacency files needed).
"""
import numpy as np
from scipy.signal import butter, filtfilt, hilbert
from pathlib import Path

DATA_DIR   = Path("data/processed")
TEST_SUBJS = ["chb03", "chb06", "chb13", "chb14", "chb15",
              "chb16", "chb17", "chb18"]
FS         = 256

BANDS = {
    "delta":  (0.5,  4.0),
    "theta":  (4.0,  8.0),
    "alpha":  (8.0, 13.0),
    "gamma":  (30.0, 60.0),
}


def butter_bandpass(low, high, fs=FS, order=4):
    nyq = fs / 2.0
    b, a = butter(order, [low / nyq, high / nyq], btype="band")
    return b, a


def mean_aec_batch(windows, low, high, keep_ratio=0.20):
    """
    windows: [N, 18, 1024]
    Returns: [N] — mean of top-20% AEC values per window.
    """
    b_coef, a_coef = butter_bandpass(low, high)
    N, n_ch, _ = windows.shape
    scores = np.zeros(N, dtype=np.float32)

    for i in range(N):
        w = windows[i]                              # [18, 1024]
        filt = filtfilt(b_coef, a_coef, w, axis=1) # [18, 1024]
        env  = np.abs(hilbert(filt, axis=1))        # [18, 1024]
        env  = np.log(env + 1e-10)

        triu = np.triu_indices(n_ch, k=1)
        corrs = np.array([
            float(np.corrcoef(env[r], env[c])[0, 1])
            for r, c in zip(triu[0], triu[1])
        ])
        corrs = np.nan_to_num(corrs, nan=0.0)
        k = max(1, int(len(corrs) * keep_ratio))
        scores[i] = float(np.mean(np.sort(corrs)[-k:]))

    return scores


# ── Sample check on test subjects ────────────────────────────────────────────
print(f"{'Subj':<6} " +
      " ".join(f"{'inter_'+b:>12} {'ictal_'+b:>11}" for b in BANDS) +
      f"  {'wPLI_dir':>10}")
print("-" * 110)

for subj in TEST_SUBJS:
    inter_path = DATA_DIR / f"{subj}_interictal.npy"
    ictal_path  = DATA_DIR / f"{subj}_ictal.npy"
    if not inter_path.exists() or not ictal_path.exists():
        print(f"{subj:<6}  raw windows not found — skip")
        continue

    # Subsample to keep computation fast
    inter_raw = np.load(str(inter_path), mmap_mode="r")
    ictal_raw  = np.load(str(ictal_path),  mmap_mode="r")
    n_inter = min(500, len(inter_raw))
    n_ictal  = min(len(ictal_raw), len(ictal_raw))   # all ictal
    idx = np.random.choice(len(inter_raw), n_inter, replace=False)
    W_inter = inter_raw[idx].astype(np.float32)
    W_ictal  = ictal_raw[:n_ictal].astype(np.float32)

    row = f"{subj:<6}"
    for band_name, (lo, hi) in BANDS.items():
        s_i = mean_aec_batch(W_inter, lo, hi)
        s_c = mean_aec_batch(W_ictal,  lo, hi)
        m_i, m_c = s_i.mean(), s_c.mean()
        direction = "↑" if m_c > m_i else "↓"
        row += f"  {m_i:>7.4f}→{m_c:>7.4f}{direction}"
    print(row)