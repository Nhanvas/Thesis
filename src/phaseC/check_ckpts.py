"""
check_ckpts.py — READ-ONLY inventory of available per-seed checkpoints. No writes,
no GPU. Run where the checkpoints are mounted (Kaggle: /kaggle/input; or local ckpt dir).

Tells us the ONLY thing that decides the multi-seed path:
  - how many distinct seeds have a GAE checkpoint (gae_joint_seed*) -> rlg re-encode
  - how many have an LSTM checkpoint (lstm_temporal_seed*)          -> (rlg doesn't need it)

USAGE
  # Kaggle notebook (datasets mounted under /kaggle/input):
  python check_ckpts.py --ckpt_root /kaggle/input
  # local:
  python check_ckpts.py --ckpt_root F:/Study/Thesis/Code/ckpts
"""
import os as _os, sys as _sys
_here = _os.path.dirname(_os.path.abspath(__file__))
for _p in (_here, _os.path.dirname(_here),
           _os.path.join(_os.path.dirname(_here), "retrain")):
    if _os.path.isdir(_p) and _p not in _sys.path:
        _sys.path.insert(0, _p)

import argparse
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ckpt_root", default="/kaggle/input")
    a = ap.parse_args()
    import retrain_io as IO

    root = Path(a.ckpt_root)
    print(f"ckpt_root = {root}  (exists={root.exists()})\n")

    for prefix, label in (("gae_joint_seed", "GAE"), ("lstm_temporal_seed", "LSTM")):
        try:
            ck = IO.find_ckpts(a.ckpt_root, prefix)
            seeds = sorted(ck)
            print(f"[{label}] prefix '{prefix}*' -> seeds {seeds}  (n={len(seeds)})")
            for sd in seeds:
                kind, p = ck[sd]
                print(f"    seed {sd:>4}: {kind:4}  {p}")
        except FileNotFoundError as e:
            print(f"[{label}] NONE found for '{prefix}*'")
            print(f"    {str(e)[:300]}")
        print()

    # also list any raw .pt names, to catch a different naming convention
    pts = [c.name for c in root.rglob("*.pt")][:30] if root.exists() else []
    if pts:
        print(f"[raw .pt files seen] {len(pts)} shown (max 30):")
        for n in pts:
            print(f"    {n}")
    else:
        print("[raw .pt files seen] none (checkpoints may be unpacked into data.pkl dirs)")


if __name__ == "__main__":
    main()
