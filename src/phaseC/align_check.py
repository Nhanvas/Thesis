"""
align_check.py — CURSOR CPU. Verify the build_timeline windowing rule reproduces the committed
feature-array window counts, BEFORE writing the (heavy) TE-branch builder. Reuses the LOCKED parser
evaluation_protocol.parse_summary_edf_list so segmentation matches §0 exactly.

Rule (from evaluation_protocol.build_timeline): files in FILENAME order; 4 s non-overlapping windows
(drop remainder); per window -> ICTAL if it overlaps a seizure; else BUFFER (excluded) if within
BUFFER_H=4 h after a seizure; else INTERICTAL. The feature arrays should contain the ictal windows and
the interictal (non-buffer) windows, in that order.

USAGE
  python align_check.py --summary_root "F:/.../summary" \
    --feat_root  "F:/.../data/processed" \
    --subjects chb10,chb11,chb22,chb06,chb14
"""
import argparse, sys, os
from pathlib import Path
import numpy as np

# import the LOCKED parser + constants
sys.path.insert(0, "src"); sys.path.insert(0, ".")
import evaluation_protocol as EP   # parse_summary_edf_list, WIN_SEC, BUFFER_H


def counts_from_summary(summary_path):
    edfs = EP.parse_summary_edf_list(summary_path)
    n_ictal = n_inter = n_buffer = 0
    for edf in edfs:
        dur = edf["duration_s"]; n_win = dur // EP.WIN_SEC
        labels = np.zeros(dur, dtype=np.int8); buf = np.zeros(dur, dtype=bool)
        for (on, off) in edf["seizures"]:
            on = min(on, dur); off = min(off, dur)
            labels[on:off] = 1
            buf[off:min(dur, off + EP.BUFFER_H * 3600)] = True
        tl = n_win * EP.WIN_SEC
        wl = labels[:tl].reshape(n_win, EP.WIN_SEC).max(1)
        wb = buf[:tl].reshape(n_win, EP.WIN_SEC).any(1)
        for w in range(n_win):
            if wl[w] == 1: n_ictal += 1
            elif wb[w]: n_buffer += 1
            else: n_inter += 1
    return n_inter, n_ictal, n_buffer


def feat_nwin(feat_root, subj, split):
    cands = [f"{subj}_{split}_features.npy", f"{subj}_{split}_adjs_topk20.npy",
             f"{subj}_{split}_adjs.npy"]
    for name in cands:
        p = Path(feat_root) / name
        if p.exists(): return int(np.load(p, mmap_mode="r").shape[0])
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--summary_root", required=True)
    ap.add_argument("--feat_root", required=True)
    ap.add_argument("--subjects", required=True)
    a = ap.parse_args()
    print(f"WIN_SEC={EP.WIN_SEC}  BUFFER_H={EP.BUFFER_H}")
    print(f"{'subj':>6} | {'rule_inter':>10}{'feat_inter':>11} | {'rule_ictal':>10}{'feat_ictal':>11} | buffer | MATCH")
    for s in a.subjects.split(","):
        ni, nc, nb = counts_from_summary(os.path.join(a.summary_root, f"{s}-summary.txt"))
        fi = feat_nwin(a.feat_root, s, "interictal"); fc = feat_nwin(a.feat_root, s, "ictal")
        mi = "" if fi is None else ("OK" if fi == ni else f"Δ{ni-fi:+d}")
        mc = "" if fc is None else ("OK" if fc == nc else f"Δ{nc-fc:+d}")
        match = "✓" if (mi == "OK" and mc == "OK") else "✗"
        print(f"{s:>6} | {ni:>10}{str(fi):>11} | {nc:>10}{str(fc):>11} | {nb:>6} | {match}  inter:{mi} ictal:{mc}")
    print("\n✓ everywhere -> TE branch will align by construction. Any Δ -> feature preprocessing used a "
          "different interictal rule; report the Δ and I adjust the TE builder to match.")


if __name__ == "__main__":
    main()
