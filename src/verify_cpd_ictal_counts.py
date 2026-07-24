# src/verify_cpd_ictal_counts.py
import re, numpy as np
from pathlib import Path

DATA_DIR    = Path("data/processed")
SUMMARY_DIR = Path("path/to/chb-mit-summary")  # adjust
TEST_SUBJS  = ["chb03","chb06","chb13","chb14","chb15","chb16","chb17","chb18"]
WIN_S = 4

def parse_seizure_windows(summary_path):
    text = Path(summary_path).read_text()
    total = 0
    for m in re.finditer(
        r'Number of Seizures in File:\s*(\d+)(.*?)(?=File Name:|$)',
        text, re.DOTALL):
        n = int(m.group(1))
        if n == 0: continue
        starts = [int(x) for x in re.findall(r'Seizure.*?Start.*?(\d+)\s*second', m.group(2), re.I)]
        ends   = [int(x) for x in re.findall(r'Seizure.*?End.*?(\d+)\s*second',   m.group(2), re.I)]
        for s, e in zip(starts, ends):
            total += max(1, (e - s) // WIN_S)
    return total

print(f"{'Subj':<6} {'Expected_ictal':>15} {'Actual_ictal':>12} {'Match':>6}")
print("-" * 42)
for subj in TEST_SUBJS:
    expected = parse_seizure_windows(str(SUMMARY_DIR / f"{subj}-summary.txt"))
    actual   = len(np.load(str(DATA_DIR / f"{subj}_ictal_adjs_topk20.npy")))
    match    = "OK" if abs(expected - actual) <= max(2, int(actual * 0.05)) else "MISMATCH"
    print(f"{subj:<6} {expected:>15} {actual:>12} {match:>6}")