"""
build_ens.py — KAGGLE GPU ONLY. The fast half of the pipeline.

For each model seed and each of the 8 TEST subjects, build robust-z components
(GAE recon + LSTM temporal + gamma), form the weighted ensemble, and SAVE the
two ensemble score arrays:
    ens_seed{S}_{subj}_inter.npy , ens_seed{S}_{subj}_ictal.npy
plus per-subject window AUROC in window_auroc_seed{S}.json.

This is the ONLY step that needs a GPU (torch + torch_geometric). It is fast
(~seconds/subject, like derive_weights). The slow CPD grid + SzCORE scoring runs
afterwards on Cursor CPU via score_ens.py — no GPU, no Kaggle timeout, resumable.

USAGE (Kaggle GPU)
  python build_ens.py --input_root /kaggle/input --weights 0.3334,0.3333,0.3333 \
      --out_dir /kaggle/working/ens
Smoke (no torch):
  python build_ens.py --smoke
"""
import os as _os, sys as _sys
_here = _os.path.dirname(_os.path.abspath(__file__))
for _p in (_here, _os.path.dirname(_here)):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

import argparse
import json
from pathlib import Path

import numpy as np

import retrain_io as IO

MODEL_SEEDS = [42, 1, 2, 3, 4]


def save_subject(out, sd, subj, ens_i, ens_c):
    np.save(out / f"ens_seed{sd}_{subj}_inter.npy", ens_i.astype(np.float32))
    np.save(out / f"ens_seed{sd}_{subj}_ictal.npy", ens_c.astype(np.float32))
    return IO.window_auroc(ens_i, ens_c)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input_root", default="/kaggle/input")
    ap.add_argument("--weights", required=False, default="0.3334,0.3333,0.3333")
    ap.add_argument("--suffix", default="_topk20")
    ap.add_argument("--seeds", default=",".join(str(s) for s in MODEL_SEEDS))
    ap.add_argument("--out_dir", default="/kaggle/working/ens")
    ap.add_argument("--subjects", default=None,
                    help="comma list (default = 8 test subjects); e.g. chb10,chb11,chb22 for VAL")
    ap.add_argument("--smoke", action="store_true")
    a = ap.parse_args()
    weights = tuple(float(x) for x in a.weights.split(","))
    assert abs(sum(weights) - 1.0) < 1e-6, "weights must sum to 1"

    if a.smoke:
        out = Path("/tmp/ens_smoke"); out.mkdir(parents=True, exist_ok=True)
        rng = np.random.default_rng(0)
        wa = save_subject(out, 42, "chb03",
                          rng.normal(0, 1, 500), rng.normal(1.5, 1, 40))
        assert (out / "ens_seed42_chb03_inter.npy").exists()
        assert (out / "ens_seed42_chb03_ictal.npy").exists()
        assert 0.0 <= wa <= 1.0
        print(f"[SMOKE] saved arrays, window AUROC={wa:.3f} -> PASS")
        return

    import torch
    import gae_joint as G
    import lstm_temporal as T
    dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"device={dev}  weights={weights}")

    adj_dir = IO.find_data_dir(a.input_root, f"chb13_interictal_adjs{a.suffix}.npy")
    feat_dir = IO.find_data_dir(a.input_root, "chb13_interictal_features.npy")
    gamma_dir = IO.find_gamma_dir(a.input_root)
    gae_ck = IO.find_ckpts(a.input_root, "gae_joint_seed")
    lstm_ck = IO.find_ckpts(a.input_root, "lstm_temporal_seed")
    seeds = [int(s) for s in a.seeds.split(",") if int(s) in gae_ck and int(s) in lstm_ck]
    subjs = a.subjects.split(",") if a.subjects else IO.TEST_SUBJS
    print(f"seeds: {seeds} | subjects: {subjs}")

    out = Path(a.out_dir); out.mkdir(parents=True, exist_ok=True)
    for sd in seeds:
        gae = G.GAEModel().to(dev)
        gsd = IO.load_state(gae_ck[sd]); gae.load_state_dict(gsd.get("state_dict", gsd), strict=True); gae.eval()
        lstm = T.LSTMPredictor(in_dim=18 * 16).to(dev)
        lsd = IO.load_state(lstm_ck[sd]); lstm.load_state_dict(lsd.get("state_dict", lsd), strict=True); lstm.eval()
        wa = {}
        for subj in subjs:
            comp = IO.build_subject_components(gae, lstm, subj, adj_dir, feat_dir,
                                               gamma_dir, a.suffix, dev)
            ens_i, ens_c = IO.ensemble_from_components(comp, weights)
            wa[subj] = round(save_subject(out, sd, subj, ens_i, ens_c), 4)
            print(f"  seed {sd} {subj}: n_inter={len(ens_i)} n_ictal={len(ens_c)} "
                  f"window AUROC={wa[subj]:.4f}", flush=True)
        (out / f"window_auroc_seed{sd}.json").write_text(json.dumps(wa, indent=2))
        print(f"[saved] seed {sd} arrays + window_auroc_seed{sd}.json")
    # record the weights alongside the arrays (provenance)
    (out / "ens_weights.json").write_text(json.dumps(dict(weights=list(weights)), indent=2))
    print(f"\nDone. Download {out}/ to Cursor, then run score_ens.py (CPU).")


if __name__ == "__main__":
    main()
