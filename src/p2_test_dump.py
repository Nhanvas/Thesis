#!/usr/bin/env python
"""
p2_test_dump.py -- prepares the single P2 test look (#6). Label-free model outputs for the 8 TEST
subjects, v2 clean seeds 42, 1, 2, 3, computed exactly as for the non-test subjects
(p2_dump_seeds23.run_model): joint recon score, graph-mean latent, and the per-channel LedoitWolf
distance of the node latent (fitted on all non-signal-loss windows of the patient, no labels).
No label is read and nothing is scored here; scoring is done once by e22_test_oneshot.py.

Reproduction gate (per subject and seed, before anything is written): recon and graph-mean latent of
the first 1,024 windows must equal the E9 cache (results/e9_test_oneshot/scores/{s}__{tag}.npz)
within 1e-5 / 1e-4, and the window index must be identical.
Output: results/p2_test/{subj}.npz with idx, {tag}_recon, {tag}_lat, {tag}_d (n x 18 float32).
Run:  python src/p2_test_dump.py --smoke     (chb03, 2,048 windows, seed 42 only; ~1 min)
      python src/p2_test_dump.py             (estimated 15-45 min CPU, not measured)
"""
import argparse
import sys
import time
from pathlib import Path

import numpy as np
from sklearn.covariance import LedoitWolf

ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT / "src", ROOT / "src" / "dataprep", ROOT / "src" / "retrain",
          ROOT / "src" / "phaseB", ROOT / "src" / "phaseC"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
import p2_dump_seeds23 as PD           # noqa: E402

TEST = ["chb03", "chb06", "chb13", "chb14", "chb15", "chb16", "chb17", "chb18"]
DATA = ROOT / "data" / "testset_v2"
E9 = ROOT / "results" / "e9_test_oneshot" / "scores"
OUT = ROOT / "results" / "p2_test"
TAGS = ["clean_seed42", "clean_seed1", "clean_seed2", "clean_seed3"]


def dump(subj, smoke=False):
    out = OUT / f"{subj}{'_SMOKE' if smoke else ''}.npz"
    if out.exists() and not smoke:
        print(f"{subj}: exists, skip"); return
    t0 = time.time()
    z = np.load(DATA / f"{subj}.npz", allow_pickle=True)
    idx = np.flatnonzero(~z["is_signal_loss"].astype(bool))
    tags = TAGS[:1] if smoke else TAGS
    for tag in tags:
        if not np.array_equal(np.load(E9 / f"{subj}__{tag}.npz")["idx"], idx):
            raise SystemExit(f"STOP {subj} {tag}: window index differs from the E9 cache")
    if smoke:
        idx = idx[:2048]
    adj = z["adj"][idx].astype(np.float32); adj[~np.isfinite(adj).all(axis=(1, 2))] = 0.0
    bp5 = z["bp5"][idx].astype(np.float32); bp5[~np.isfinite(bp5)] = 0.0
    f7 = z["f7"][idx].astype(np.float64)
    xn = (bp5 - bp5.min(axis=1, keepdims=True)) / (bp5.max(axis=1, keepdims=True)
                                                  - bp5.min(axis=1, keepdims=True) + 1e-8)
    res = {"idx": idx}
    for tag in tags:
        rec, Z = PD.run_model(tag, adj, xn, f7)
        ref = np.load(E9 / f"{subj}__{tag}.npz")
        e_r = float(np.abs(rec[:1024] - ref["recon"][:1024]).max())
        e_l = float(np.abs(Z[:1024].mean(axis=1) - ref["lat"][:1024]).max())
        if e_r > 1e-5 or e_l > 1e-4:
            raise SystemExit(f"STOP {subj} {tag}: reproduction of the E9 cache failed (recon {e_r:.1e}, lat {e_l:.1e})")
        D = np.empty((len(idx), Z.shape[1]), np.float32)
        for c in range(Z.shape[1]):
            Zc = Z[:, c, :].astype(np.float64)
            D[:, c] = LedoitWolf().fit(Zc).mahalanobis(Zc)
        res[f"{tag}_recon"] = rec; res[f"{tag}_lat"] = Z.mean(axis=1); res[f"{tag}_d"] = D
        print(f"  {subj} {tag}: reproduction recon {e_r:.1e} lat {e_l:.1e} ({time.time()-t0:.0f}s)", flush=True)
    OUT.mkdir(parents=True, exist_ok=True)
    np.savez(out, **res)
    print(f"{subj}: {len(idx)} windows, {time.time()-t0:.0f}s", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--subjects", nargs="+", default=TEST)
    a = ap.parse_args()
    subs = ["chb03"] if a.smoke else a.subjects
    if set(subs) - set(TEST):
        raise SystemExit(f"test subjects only: {sorted(set(subs) - set(TEST))}")
    for s in subs:
        dump(s, smoke=a.smoke)


if __name__ == "__main__":
    main()
