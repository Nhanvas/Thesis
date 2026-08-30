"""
align_check2.py — CURSOR CPU. Try to reverse-engineer the feature preprocessing's INTERICTAL rule
(ictal already matches exactly). Tests standard CHB-MIT interictal definitions against feat_inter.
If one hypothesis matches all subjects -> we can reproduce the interictal set -> align a TE branch.
If none matches -> the preprocessing must be re-owned (controlled EDF->features/adj, committed).

USAGE
  python align_check2.py --summary_root "F:/.../summary" --feat_root "F:/.../data/processed" \
    --subjects chb10,chb11,chb22,chb06,chb14
"""
import argparse, sys, os
from pathlib import Path
import numpy as np
sys.path.insert(0, "src"); sys.path.insert(0, ".")
import evaluation_protocol as EP


def feat_nwin(feat_root, subj, split):
    for name in (f"{subj}_{split}_features.npy", f"{subj}_{split}_adjs_topk20.npy", f"{subj}_{split}_adjs.npy"):
        p = Path(feat_root) / name
        if p.exists(): return int(np.load(p, mmap_mode="r").shape[0])
    return None


def inter_count(edfs, buffer_h=4.0, pre_buffer_h=0.0, seizfree_only=False):
    """Count interictal windows under a hypothesis."""
    n = 0
    for edf in edfs:
        dur = edf["duration_s"]; nw = dur // EP.WIN_SEC
        has_sz = len(edf["seizures"]) > 0
        if seizfree_only and has_sz:
            continue
        labels = np.zeros(dur, dtype=np.int8); buf = np.zeros(dur, dtype=bool)
        for (on, off) in edf["seizures"]:
            on = min(on, dur); off = min(off, dur)
            labels[on:off] = 1
            buf[off:min(dur, int(off + buffer_h*3600))] = True
            if pre_buffer_h > 0: buf[max(0, int(on - pre_buffer_h*3600)):on] = True
        tl = nw * EP.WIN_SEC
        wl = labels[:tl].reshape(nw, EP.WIN_SEC).max(1)
        wb = buf[:tl].reshape(nw, EP.WIN_SEC).any(1)
        n += int(((wl == 0) & (~wb)).sum())
    return n


HYP = [
    ("buf4h (base)",      dict(buffer_h=4)),
    ("buf1h",             dict(buffer_h=1)),
    ("buf2h",             dict(buffer_h=2)),
    ("buf6h",             dict(buffer_h=6)),
    ("buf8h",             dict(buffer_h=8)),
    ("pre+post 1h",       dict(buffer_h=1, pre_buffer_h=1)),
    ("pre+post 4h",       dict(buffer_h=4, pre_buffer_h=4)),
    ("seizfree files",    dict(seizfree_only=True, buffer_h=0)),
    ("seizfree +buf4h",   dict(seizfree_only=True, buffer_h=4)),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--summary_root", required=True)
    ap.add_argument("--feat_root", required=True)
    ap.add_argument("--subjects", required=True)
    a = ap.parse_args()
    subs = a.subjects.split(",")
    edfs = {s: EP.parse_summary_edf_list(os.path.join(a.summary_root, f"{s}-summary.txt")) for s in subs}
    feat = {s: feat_nwin(a.feat_root, s, "interictal") for s in subs}
    print("feat_inter:", {s: feat[s] for s in subs})
    print(f"\n{'hypothesis':>18} | " + " ".join(f"{s:>7}" for s in subs) + " | all-match?")
    for name, kw in HYP:
        row = {s: inter_count(edfs[s], **kw) for s in subs}
        allok = all(feat[s] is not None and row[s] == feat[s] for s in subs)
        cells = " ".join((f"{row[s]:>7}" if feat[s] is None else
                          (f"{'OK':>7}" if row[s] == feat[s] else f"{row[s]-feat[s]:>+7}")) for s in subs)
        print(f"{name:>18} | {cells} | {'*** YES ***' if allok else ''}")
    print("\nOK/±Δ shown vs feat_inter. A row of all-OK -> that rule reproduces the interictal set.")


if __name__ == "__main__":
    main()
