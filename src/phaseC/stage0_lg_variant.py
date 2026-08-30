"""
stage0_lg_variant.py — Phase C-final / C4-full, PRE-REGISTERED 2-branch variant test.
torch + PyG. NO retrain — reuses the existing gae_multirel_seed42.pt.

WHY (locked BEFORE computing the deciding number):
  The 3-branch GO gate failed for TWO INDEPENDENT reasons:
    (1) recon-mr collapsed because R2 reconstruction is ANTI-discriminative
        (macro 0.439 < 0.5; a priori: seizure -> more synchronized connectivity
        -> easier to reconstruct -> lower ictal recon error -> anti-discriminative).
        An <0.5 branch DRAGS the equal-weight ensemble toward random.
    (2) chb10 latent harm from sharing encoder capacity across 2 relations
        (NOT caused by R2 — ablation ΔR2(chb10)=+0.040). This is NOT fixed here.
  This variant fixes only (1): drop recon-mr, keep latent-mr + gamma (2-branch).
  It is a DIFFERENT front-end architecture, not a re-weighting to fit seen numbers.

PRE-REGISTERED verdict (deciding number = 2-branch window macro, UNSEEN until run):
  GO (earn Stage-1 multi-seed + EVENT gate): macro(latent-mr + gamma) >= 0.928
      (rlg-full incumbent) AND chb22 latent-mr stays > 0.736.
  KILL (close Phase C): macro < 0.928 -> representation gain does not survive to a
      full-pipeline win -> net-wash confirmed at the pipeline level. NO further variants.

Reads locally (all inputs present): ckpt + R1 adjs + te + features + gamma.

Usage (local):
  python src/phaseC/stage0_lg_variant.py --ckpt data/models_retrain/gae_multirel_seed42.pt \
    --a1_dir data/processed --a2_dir data/processed --feat_dir data/processed \
    --gamma_dir data/processed --out_dir results/phaseC/c4full
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

import gae_joint_multirel as M
import retrain_io as IO

VAL = ["chb10", "chb11", "chb22"]
TEST = {"chb03", "chb06", "chb13", "chb14", "chb15", "chb16", "chb17", "chb18"}
RLG_FULL_MACRO = 0.928           # incumbent (recon+latent+gamma) — the bar to beat
C4FULL_3BRANCH = 0.909           # for context (with the anti-discriminative recon)
RLG_LATENT = {"chb10": 0.816, "chb11": 0.641, "chb22": 0.736}


def load_gamma_strict(gdir, subj, split):
    want_inter = split.startswith("inter")
    for c in sorted(glob.glob(f"{gdir}/*gamma*{subj}*.npy")):
        b = _os.path.basename(c).lower(); is_inter = "inter" in b
        if (want_inter and is_inter) or ((not want_inter) and "ictal" in b and not is_inter):
            return np.load(c).astype(np.float32)
    raise FileNotFoundError(f"strict gamma {subj}/{split} in {gdir}")


def latent_mr(oi, oc):
    cov = LedoitWolf().fit(oi["Z"])
    return cov.mahalanobis(oi["Z"]), cov.mahalanobis(oc["Z"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ckpt", default="data/models_retrain/gae_multirel_seed42.pt")
    ap.add_argument("--a1_dir", default="data/processed")
    ap.add_argument("--a2_dir", default="data/processed")
    ap.add_argument("--feat_dir", default="data/processed")
    ap.add_argument("--gamma_dir", default="data/processed")
    ap.add_argument("--suffix", default="_topk20")
    ap.add_argument("--out_dir", default="results/phaseC/c4full")
    a = ap.parse_args()

    dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = M.load_checkpoint(a.ckpt, dev)
    print(f"ckpt={a.ckpt} device={dev}\n")
    print(f"{'subj':7s} {'latent':>7s} {'gamma':>7s} {'lat+gam':>8s}  (rlg-latent)")

    res = {}
    for subj in VAL:
        assert subj not in TEST
        def p(split):
            return (str(Path(a.a1_dir) / f"{subj}_{split}_adjs{a.suffix}.npy"),
                    str(Path(a.a2_dir) / f"{subj}_{split}_te_topk20.npy"),
                    str(Path(a.feat_dir) / f"{subj}_{split}_features.npy"))
        oi = M.score_windows_mr(model, *p("interictal"), dev)
        oc = M.score_windows_mr(model, *p("ictal"), dev)
        li, lc = latent_mr(oi, oc); zl_i, zl_c = IO.robust_z(li, lc)
        gi = load_gamma_strict(a.gamma_dir, subj, "inter")
        gc = load_gamma_strict(a.gamma_dir, subj, "ictal")
        zg_i, zg_c = IO.robust_z(gi, gc)
        lat = IO.window_auroc(zl_i, zl_c); gam = IO.window_auroc(zg_i, zg_c)
        lg_i = (zl_i + zg_i) / 2.0; lg_c = (zl_c + zg_c) / 2.0
        lg = IO.window_auroc(lg_i, lg_c)
        res[subj] = dict(latent=round(lat, 4), gamma=round(gam, 4), lg=round(lg, 4))
        print(f"{subj:7s} {lat:7.3f} {gam:7.3f} {lg:8.3f}  ({RLG_LATENT[subj]:.3f})")

    macro_lg = float(np.mean([res[s]["lg"] for s in VAL]))
    print(f"\n[macro] latent-mr+gamma (2-branch) = {macro_lg:.4f}")
    print(f"        vs rlg-full 3-branch (incumbent) = {RLG_FULL_MACRO}")
    print(f"        vs C4-full 3-branch (with recon)  = {C4FULL_3BRANCH}")

    go = (macro_lg >= RLG_FULL_MACRO) and (res["chb22"]["latent"] > RLG_LATENT["chb22"])
    print("\n" + "=" * 56)
    print(f"  [{'PASS' if macro_lg >= RLG_FULL_MACRO else 'FAIL'}] 2-branch macro >= 0.928")
    print(f"  [{'PASS' if res['chb22']['latent'] > RLG_LATENT['chb22'] else 'FAIL'}] chb22 latent-mr > 0.736")
    print(f"\n  PRE-REGISTERED: {'GO -> Stage-1 multi-seed + EVENT gate' if go else 'KILL -> close Phase C (net-wash confirmed at pipeline level)'}")
    print("=" * 56)

    out = Path(a.out_dir); out.mkdir(parents=True, exist_ok=True)
    (out / "stage0_lg_variant_seed42.json").write_text(json.dumps(
        dict(per_subject=res, macro_lg=round(macro_lg, 4),
             rlg_full=RLG_FULL_MACRO, c4full_3branch=C4FULL_3BRANCH, go=bool(go)), indent=2))
    print(f"[saved] {out}/stage0_lg_variant_seed42.json")


if __name__ == "__main__":
    main()
