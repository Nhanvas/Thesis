#!/usr/bin/env python3
"""results_scan.py -- READ-ONLY. Inventory results/ (every CSV: bytes, lines, header, +first row for
key files) + list loose files at repo root, so results/ can be classified CITED / SUPERSEDED / UNCLEAR
against RESULTS_OF_RECORD.md. Writes nothing."""
import os, glob

KEY = ("locked", "event_level", "window_level", "stat_tests", "component_auroc", "ablation",
       "duration", "reproducibility", "multiseed", "fp_filter", "attribution", "auroc_verification")

print("RESULTS_SCAN v1 (read-only)\ncwd =", os.path.abspath("."))

# --- results/ subdir summary ---
print("\n" + "=" * 74 + "\nresults/ SUBDIR SUMMARY (file counts by ext)\n" + "=" * 74)
from collections import defaultdict
bydir = defaultdict(lambda: defaultdict(int))
for dp, dns, fns in os.walk("results"):
    for f in fns:
        bydir[dp][os.path.splitext(f)[1].lower() or "<none>"] += 1
for d in sorted(bydir):
    print(f"  {d}  ::  " + ", ".join(f"{e}:{c}" for e, c in sorted(bydir[d].items())))

# --- every CSV under results/: signature ---
print("\n" + "=" * 74 + "\nresults/ CSVs  [bytes | lines | path] (+header; +1 row if key)\n" + "=" * 74)
for p in sorted(glob.glob("results/**/*.csv", recursive=True)):
    try:
        b = os.path.getsize(p)
        with open(p, encoding="utf-8", errors="replace") as f:
            lines = f.read().splitlines()
    except OSError as e:
        print(f"  <err {e}> {p}"); continue
    flag = "  <<<EMPTY" if b < 40 else ""
    print(f"\n{b:>7}B | {len(lines):>4}L | {p}{flag}")
    key = any(k in os.path.basename(p).lower() for k in KEY)
    for r in lines[:(2 if key else 1)]:
        print("   " + r[:190])

# --- loose files at repo root (non-dir) ---
print("\n" + "=" * 74 + "\nLOOSE FILES AT REPO ROOT (non-folder)\n" + "=" * 74)
for f in sorted(os.listdir(".")):
    if os.path.isfile(f):
        print(f"  {os.path.getsize(f):>8}B  {f}")

# --- non-CSV result artifacts worth noting (npy/npz/pt/png/pdf/json big) ---
print("\n" + "=" * 74 + "\nresults/ NON-CSV artifacts (npz/pt/json/png/pdf)\n" + "=" * 74)
for p in sorted(glob.glob("results/**/*", recursive=True)):
    if os.path.isfile(p) and os.path.splitext(p)[1].lower() in (".npz", ".pt", ".json", ".png", ".pdf"):
        print(f"  {os.path.getsize(p)//1024:>6}KB  {p}")

print("\n[done] read-only.")