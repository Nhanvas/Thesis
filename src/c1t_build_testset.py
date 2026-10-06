#!/usr/bin/env python
"""
c1t_build_testset.py -- build the 8 TEST subjects' full recordings with exactly the v2 signal
path of c1b_build_trainset.build() (same features, same skip rule), into data/testset_v2/.
Building scores nothing and selects nothing; the seizure annotation stored in the file is used
only by the one-shot scorer, after the configuration was frozen by E8 (2026-10-06):
GAE v2 clean, score V2_LW, detector D1 smooth 15, top 2 %.

  python src/c1t_build_testset.py --subjects chb03 chb06 ...
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import c1b_build_trainset as C1B  # noqa: E402

TEST = ["chb03", "chb06", "chb13", "chb14", "chb15", "chb16", "chb17", "chb18"]
OUT = ROOT / "data" / "testset_v2"

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--subjects", nargs="+", default=TEST)
    a = ap.parse_args()
    bad = set(a.subjects) - set(TEST)
    if bad:
        raise SystemExit(f"only test subjects here: {sorted(bad)}")
    for s in a.subjects:
        C1B.build(s, out_dir=OUT, allow_test=True)
