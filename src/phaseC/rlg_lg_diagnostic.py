"""
rlg_lg_diagnostic.py — Phase C-final REPORT diagnostic (NOT a decision gate).
torch + PyG. KILL is already locked; this only sharpens the write-up.

QUESTION: is C4-full's 2-branch macro (0.926) driven by GAMMA (i.e. any latent+gamma
lands ~0.926, even WITHOUT the directed relation), or does C4-full's directed latent
contribute something real that just isn't enough to beat rlg-full (0.928)?

METHOD: compute rlg's OWN 2-branch (rlg-latent + gamma), using the single-relation
rlg checkpoint gae_joint_seed42.pt — the FAIR matched ablation the committee would ask
for. Mirrors stage0_lg_variant EXACTLY (robust_z each branch -> equal-avg -> window AUROC),
so rlg-lg and C4-full-lg are apples-to-apples.

READ-OUT:
  * rlg-lg  <<  0.926  -> C4-full's directed latent DID contribute (rlg's plain latent+gamma
                          is weaker); C4-full just couldn't overcome the chb10 capacity loss.
                          => nuanced, stronger negative ("mechanism real, insufficient").
  * rlg-lg  ~=  0.926  -> the 0.926 is a GAMMA effect; directed latent adds ~nothing at the
                          2-branch macro. => plain, clean negative.
Either way KILL stands (C4-full 2-branch 0.926 < rlg-full 0.928).

Built-in fidelity gate: rlg latent-only AUROC must reproduce E2_latent_val.csv
(chb10 0.816 / chb11 0.641 / chb22 0.736, +-0.01) or the encode path is untrusted -> STOP.

Usage (local):
  python src/phaseC/rlg_lg_diagnostic.py --ckpt data/models_retrain/gae_joint_seed42.pt \
    --a1_dir data/processed --feat_dir data/processed --gamma_dir data/processed \
    --out_dir results/phaseC/c4full
"""
import os as _os, sys as _sys
_here = _os.path.dirname(_os.path.abspath(__file__))
_src = _os.path.dirname(_here)
for _p in (_src, _here, _os.path.join(_src, "retrain"),
           _os.path.join(_src, "dataprep"), _os.path.join(_src, "phaseB")):
    if _os.path.isdir(_p) and _p not in _sys.path:
        _sys.path.insert(0, _p)

import argparse, glob, json
from pathlib import Path

import numpy as np
import torch
from sklearn.covariance import LedoitWolf

import gae_joint as G
import latent_anomaly as LA          # latent_pool (validated rlg latent readout)
import retrain_io as IO

VAL = ["chb10", "chb11", "chb22"]
TEST = {"chb03", "chb06", "chb13", "chb14", "chb15", "chb16", "chb17", "chb18"}
E2_LATENT = {"chb10": 0.816, "chb11": 0.641, "chb22": 0.736}   # fidelity anchor
C4FULL_LG = 0.926
RLG_FULL = 0.928


def load_gamma_strict(gdir, subj, split):
    want_inter = split.startswith("inter")
    for c in sorted(glob.glob(f"{gdir}/*gamma*{subj}*.npy")):
        b = _os.path.basename(c).lower(); is_inter = "inter" in b
        if (want_inter and is_inter) or ((not want_inter) and "ictal" in b and not is_inter):
            return np.load(c).astype(np.float32)
    raise FileNotFoundError(f"strict gamma {subj}/{split} in {gdir}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ckpt", default="data/models_retrain/gae_joint_seed42.pt",
                    help="rlg single-relation checkpoint")
    ap.add_argument("--a1_dir", default="data/processed")
    ap.add_argument("--feat_dir", default="data/processed")
    ap.add_argument("--gamma_dir", default="data/processed")
    ap.add_argument("--suffix", default="_topk20")
    ap.add_argument("--out_dir", default="results/phaseC/c4full")
    a = ap.parse_args()

    dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = G.load_checkpoint(a.ckpt, dev)
    print(f"rlg ckpt={a.ckpt} device={dev}\n")
    print(f"{'subj':7s} {'latent':>7s} {'(E2)':>6s} {'gamma':>7s} {'rlg-lg':>7s}")

    res = {}; fidelity_ok = True
    for subj in VAL:
        assert subj not in TEST
        ai = Path(a.a1_dir) / f"{subj}_interictal_adjs{a.suffix}.npy"
        ac = Path(a.a1_dir) / f"{subj}_ictal_adjs{a.suffix}.npy"
        fi = Path(a.feat_dir) / f"{subj}_interictal_features.npy"
        fc = Path(a.feat_dir) / f"{subj}_ictal_features.npy"
        Zi = LA.latent_pool(model, ai, fi, dev)
        Zc = LA.latent_pool(model, ac, fc, dev)
        cov = LedoitWolf().fit(Zi)
        di, dc = cov.mahalanobis(Zi), cov.mahalanobis(Zc)
        zl_i, zl_c = IO.robust_z(di, dc)
        lat = IO.window_auroc(zl_i, zl_c)
        gi = load_gamma_strict(a.gamma_dir, subj, "inter")
        gc = load_gamma_strict(a.gamma_dir, subj, "ictal")
        zg_i, zg_c = IO.robust_z(gi, gc)
        gam = IO.window_auroc(zg_i, zg_c)
        lg = IO.window_auroc((zl_i + zg_i) / 2.0, (zl_c + zg_c) / 2.0)
        res[subj] = dict(latent=round(lat, 4), gamma=round(gam, 4), lg=round(lg, 4))
        dev_e2 = abs(lat - E2_LATENT[subj])
        if dev_e2 > 0.01:
            fidelity_ok = False
        print(f"{subj:7s} {lat:7.3f} {E2_LATENT[subj]:6.3f} {gam:7.3f} {lg:7.3f}"
              f"{'  <-- E2 mismatch!' if dev_e2 > 0.01 else ''}")

    macro_lg = float(np.mean([res[s]["lg"] for s in VAL]))
    print(f"\n[fidelity] rlg latent-only reproduces E2: {'PASS' if fidelity_ok else 'FAIL — path untrusted, STOP'}")
    print(f"\n[macro] rlg-lg (latent+gamma)        = {macro_lg:.4f}")
    print(f"        C4-full-lg (latent-mr+gamma) = {C4FULL_LG}")
    print(f"        rlg-full 3-branch (incumbent)= {RLG_FULL}")
    gap = C4FULL_LG - macro_lg
    if abs(gap) < 0.005:
        story = ("rlg-lg ~= C4-full-lg -> the 0.926 is a GAMMA effect; directed latent adds "
                 "~nothing at 2-branch macro. Plain clean negative.")
    elif gap > 0:
        story = (f"C4-full-lg > rlg-lg by {gap:.3f} -> directed latent DID contribute real "
                 "signal; C4-full still lost only because the shared encoder hurt chb10. "
                 "Nuanced negative: mechanism real, insufficient to beat rlg-full.")
    else:
        story = (f"rlg-lg > C4-full-lg by {-gap:.3f} -> plain latent+gamma already beats the "
                 "directed variant; directed relation is net-negative at 2-branch. Clean negative.")
    print(f"\n[story] {story}")
    print(f"\nKILL stands regardless (C4-full 2-branch {C4FULL_LG} < rlg-full {RLG_FULL}).")

    out = Path(a.out_dir); out.mkdir(parents=True, exist_ok=True)
    (out / "rlg_lg_diagnostic_seed42.json").write_text(json.dumps(
        dict(per_subject=res, rlg_lg_macro=round(macro_lg, 4), c4full_lg=C4FULL_LG,
             rlg_full=RLG_FULL, fidelity_ok=fidelity_ok, story=story), indent=2))
    print(f"[saved] {out}/rlg_lg_diagnostic_seed42.json")


if __name__ == "__main__":
    main()
