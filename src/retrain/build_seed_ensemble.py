"""
build_seed_ensemble.py — CURSOR CPU. Deep seed-ensemble (variance reduction).

Averages the per-seed ensemble score arrays (ens_seed{k}_{subj}_{split}.npy) over
all training seeds into a single, more stable production signal, saved under a new
seed tag (default 99). Then score_ens.py --seed 99 runs the normal CPD grid on it
and aggregate_final.py produces its headline exactly like any seed.

Rationale: single-seed event-level sensitivity was unstable (SD ~0.18). A deep
ensemble (mean over seeds) is the standard variance-reduction estimator; it is
reported transparently ALONGSIDE the single-seed mean±SD, not instead of it.

Needs only numpy + scikit-learn. NO torch.

USAGE (Cursor)
  python build_seed_ensemble.py --ens_dir results/retrain/ens \
      --seeds 42,1,2,3,4 --out_tag 99
Smoke:
  python build_seed_ensemble.py --smoke
"""
import argparse
import json
from pathlib import Path

import numpy as np
from sklearn.metrics import roc_auc_score

TEST_SUBJS = ["chb03", "chb06", "chb13", "chb14", "chb15", "chb16", "chb17", "chb18"]


def window_auroc(ei, ec):
    ei = np.asarray(ei, float); ec = np.asarray(ec, float)
    ei = ei[~np.isnan(ei)]; ec = ec[~np.isnan(ec)]
    if len(ei) == 0 or len(ec) == 0:
        return float("nan")
    y = np.r_[np.zeros(len(ei)), np.ones(len(ec))]
    return float(roc_auc_score(y, np.r_[ei, ec]))


def build(ens_dir, seeds, tag, subjs=None):
    subjs = subjs or TEST_SUBJS
    ens_dir = Path(ens_dir)
    wa = {}
    for subj in subjs:
        arrs_i, arrs_c = [], []
        for k in seeds:
            fi = ens_dir / f"ens_seed{k}_{subj}_inter.npy"
            fc = ens_dir / f"ens_seed{k}_{subj}_ictal.npy"
            if not (fi.exists() and fc.exists()):
                raise SystemExit(f"missing {fi.name} or {fc.name}")
            arrs_i.append(np.load(fi)); arrs_c.append(np.load(fc))
        # all seeds share the window count per subject -> element-wise mean
        n_i = min(len(a) for a in arrs_i); n_c = min(len(a) for a in arrs_c)
        mi = np.mean([a[:n_i] for a in arrs_i], axis=0).astype(np.float32)
        mc = np.mean([a[:n_c] for a in arrs_c], axis=0).astype(np.float32)
        np.save(ens_dir / f"ens_seed{tag}_{subj}_inter.npy", mi)
        np.save(ens_dir / f"ens_seed{tag}_{subj}_ictal.npy", mc)
        wa[subj] = round(window_auroc(mi, mc), 4)
        print(f"  {subj}: n_inter={n_i} n_ictal={n_c} window AUROC={wa[subj]:.4f}")
    (ens_dir / f"window_auroc_seed{tag}.json").write_text(json.dumps(wa, indent=2))
    macro = float(np.nanmean(list(wa.values())))
    print(f"deep-ensemble (seed {tag}) macro window AUROC = {macro:.4f}")
    print(f"[saved] ens_seed{tag}_* + window_auroc_seed{tag}.json in {ens_dir}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ens_dir", default="results/retrain/ens")
    ap.add_argument("--seeds", default="42,1,2,3,4")
    ap.add_argument("--out_tag", default="99")
    ap.add_argument("--subjects", default=None, help="comma list; default = 8 test subjects")
    ap.add_argument("--smoke", action="store_true")
    a = ap.parse_args()

    if a.smoke:
        d = Path("/tmp/ens_seed_smoke"); d.mkdir(parents=True, exist_ok=True)
        rng = np.random.default_rng(0)
        for k in [42, 1, 2]:
            for s in TEST_SUBJS:
                np.save(d / f"ens_seed{k}_{s}_inter.npy", rng.normal(0, 1, 300))
                np.save(d / f"ens_seed{k}_{s}_ictal.npy", rng.normal(1.5, 1, 40))
        build(d, [42, 1, 2], "99")
        assert (d / "ens_seed99_chb03_inter.npy").exists()
        assert (d / "window_auroc_seed99.json").exists()
        print("\n[SMOKE] PASS")
        return

    seeds = [int(x) for x in a.seeds.split(",")]
    subjs = a.subjects.split(",") if a.subjects else None
    build(a.ens_dir, seeds, a.out_tag, subjs)


if __name__ == "__main__":
    main()
