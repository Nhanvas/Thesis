"""
dump_components.py — Kaggle GPU, SHORT. Reuse the seed-42 GAE + v3 LSTM checkpoints to write the
per-subject robust-z components (zrecon/ztemp/zgamma) for the 8 TEST subjects to disk, using the
EXACT §16 recipe (retrain_io.build_subject_components). No training. No CPD here.

Output names match ensemble_recipe.load_components: {key}_{subj}_{inter,ictal}.npy
  -> download out_dir to  F:\Study\Thesis\Code\data\processed\components_retrain\  (NEW dir; do NOT
     overwrite the July `components/`), then run eval_local.py on CPU (full grid, no timeout).

Attach: gae-seed-checkpoints + the train-output version (lstm_temporal_seed42.pt) +
        chbmit-topk20 + chbmit-processed + gamma-aec-scores.  Do NOT attach the old lstm.temporal.
    !python dump_components.py --input_root /kaggle/input --seed 42 --out_dir /kaggle/working/components_retrain
"""
import argparse
from pathlib import Path

import numpy as np

import retrain_io as IO


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input_root", default="/kaggle/input")
    ap.add_argument("--suffix", default="_topk20")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out_dir", default="/kaggle/working/components_retrain")
    a = ap.parse_args()

    import torch
    import gae_joint as G
    import lstm_temporal as T
    dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    adj_dir = IO.find_data_dir(a.input_root, f"chb13_interictal_adjs{a.suffix}.npy")
    feat_dir = IO.find_data_dir(a.input_root, "chb13_interictal_features.npy")
    gamma_dir = IO.find_gamma_dir(a.input_root)
    gae_ck = IO.find_ckpts(a.input_root, "gae_joint_seed")
    lstm_ck = IO.find_ckpts(a.input_root, "lstm_temporal_seed")
    assert a.seed in gae_ck and a.seed in lstm_ck, f"seed {a.seed} checkpoints missing"
    print(f"device={dev} | GAE={gae_ck[a.seed][0]} | LSTM={lstm_ck[a.seed][0]}")

    gae = G.GAEModel().to(dev)
    gsd = IO.load_state(gae_ck[a.seed]); gae.load_state_dict(gsd.get("state_dict", gsd), strict=True); gae.eval()
    lstm = T.LSTMPredictor(in_dim=18 * 16).to(dev)
    lsd = IO.load_state(lstm_ck[a.seed]); lstm.load_state_dict(lsd.get("state_dict", lsd), strict=True); lstm.eval()

    out = Path(a.out_dir); out.mkdir(parents=True, exist_ok=True)
    for s in IO.TEST_SUBJS:
        comp = IO.build_subject_components(gae, lstm, s, adj_dir, feat_dir, gamma_dir, a.suffix, dev)
        for key in ("zrecon", "ztemp", "zgamma"):
            zi, zc = comp[key]
            np.save(out / f"{key}_{s}_inter.npy", np.asarray(zi, np.float32))
            np.save(out / f"{key}_{s}_ictal.npy", np.asarray(zc, np.float32))
        print(f"  {s}: saved zrecon/ztemp/zgamma (inter+ictal)")
    print(f"\nDONE -> {out}  (download to data/processed/components_retrain/)")


if __name__ == "__main__":
    main()
