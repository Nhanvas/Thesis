"""
check_spectral.py
=================
Check whether band power features change during ictal windows
for the subjects with low AUROC: chb14, chb16, chb17.

If ratio ictal/interictal is near 1.0 for all bands
→ spectral signal absent → Ex3a (joint reconstruction) unlikely to help.
If ratio deviates strongly (>1.3 or <0.7) for any band
→ spectral signal exists → Ex3a warranted.
"""
import numpy as np
from pathlib import Path

PROC    = Path("data/processed")
# Subjects with AUROC < 0.65 and not structural failure
TARGETS = ["chb14", "chb16", "chb17"]
BANDS   = ["delta(0.5-4Hz)", "theta(4-8Hz)", "alpha(8-13Hz)",
           "beta(13-30Hz)", "gamma(30-60Hz)"]

print("Band power ratio: mean_ictal / mean_interictal")
print("Threshold: ratio > 1.3 or < 0.7 = detectable spectral change")
print("=" * 70)

for subj in TARGETS:
    inter_f = PROC / f"{subj}_interictal_features.npy"
    ictal_f = PROC / f"{subj}_ictal_features.npy"

    if not inter_f.exists() or not ictal_f.exists():
        print(f"\n{subj}: features not found, skip")
        continue

    inter = np.load(str(inter_f), mmap_mode="r")  # [N, 18, 5]
    ictal = np.load(str(ictal_f), mmap_mode="r")  # [M, 18, 5]

    # Mean across all channels and all windows → per-band scalar
    inter_mean = inter.mean(axis=(0, 1))  # [5]
    ictal_mean = ictal.mean(axis=(0, 1))  # [5]

    ratio = ictal_mean / (inter_mean + 1e-10)

    print(f"\n{subj} — {inter.shape[0]} interictal windows, "
          f"{ictal.shape[0]} ictal windows")
    print(f"  {'Band':<20} {'Inter mean':>12} {'Ictal mean':>12} "
          f"{'Ratio':>8}  {'Signal?':>8}")
    print(f"  {'-'*20} {'-'*12} {'-'*12} {'-'*8}  {'-'*8}")
    any_signal = False
    for b, (bname, im, icm, r) in enumerate(
            zip(BANDS, inter_mean, ictal_mean, ratio)):
        signal = "YES ←" if (r > 1.3 or r < 0.7) else "no"
        if r > 1.3 or r < 0.7:
            any_signal = True
        print(f"  {bname:<20} {im:>12.4f} {icm:>12.4f} "
              f"{r:>8.3f}  {signal:>8}")

    print(f"  → Detectable spectral change: {'YES' if any_signal else 'NO'}")

print("\n" + "=" * 70)
print("Decision rule:")
print("  Any subject with YES → Ex3a (joint reconstruction) is warranted")
print("  All NO → Ex3a will not help, skip")