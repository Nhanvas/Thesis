"""
encode_multirel_val.py — Phase C-final / C4-full Stage-0 VAL window-check. torch + PyG.

Encodes the 3 VAL subjects with a trained multi-relational GAE and evaluates the
PRE-REGISTERED (Boti-approved 2026-08) GO/KILL criteria vs the LOCKED rlg baseline.
NO CPD, NO ensemble weighting search, NO TEST — a cheap Day-1 kill gate.

rlg reference (LOCKED — docs/RESULTS_OF_RECORD_phaseB.md / E2_latent_val.csv, seed42 VAL):
  latent AUROC : chb10 0.816 | chb11 0.641 | chb22 0.736 | macro 0.731
  recon  AUROC : chb10 0.268 | chb11 0.852 | chb22 0.656 | macro 0.592
  ensemble (recon+latent+gamma) window macro AUROC = 0.928 (seed42)

PRE-REGISTERED GO (proceed to Stage 1) — ALL must hold on seed42:
  1. C4-full ensemble (recon-mr + latent-mr + gamma, equal-3) window macro >= 0.928
  2. latent-mr(chb22) > 0.736                              (inverted-subject mechanism)
  3. latent-mr(chb_i) >= rlg_latent(chb_i) - delta_i        (delta_i = bootstrap-CI half-width,
       chb10 0.816, chb11 0.641; NO drop beyond the run's own AUROC sampling noise)
  4. R2 alive: (a) chb22 zTE window AUROC in [0.78,0.88]   (input fidelity vs C0 0.83)
               (b) R2-only recon AUROC(chb22) - null >= 0.10, null in [0.40,0.60],
                   and chb22 is the max-R2 VAL subject
               (c) no relation-collapse (latent-mr - latent-mr[no R2] > 0)

KILL if: ensemble < 0.928 AND chb22 not improved; OR R2-collapse (4b/4c fail);
         OR input-fidelity (4a) out of band -> investigate (eval-bug) before any verdict.

Usage (GPU):
  python src/phaseC/encode_multirel_val.py --ckpt data/models_retrain/gae_multirel_seed42.pt \
    --a1_dir <adjs_topk20> --a2_dir data/processed --feat_dir data/processed \
    --raw_dir data/processed --gamma_dir data/processed --out_dir results/phaseC/c4full
"""
import os as _os, sys as _sys
_here = _os.path.dirname(_os.path.abspath(__file__))
_src = _os.path.dirname(_here)
for _p in (_src, _here, _os.path.join(_src, "retrain"),
           _os.path.join(_src, "dataprep"), _os.path.join(_src, "phaseB")):
    if _os.path.isdir(_p) and _p not in _sys.path:
        _sys.path.insert(0, _p)

import argparse
import glob
import json
from pathlib import Path

import numpy as np
import torch
from sklearn.covariance import LedoitWolf
from sklearn.metrics import roc_auc_score

import gae_joint_multirel as M
import retrain_io as IO                       # robust_z, window_auroc
import build_te_branch as TEB                 # te_vectors, latent_te_readout (input fidelity)

VAL = ["chb10", "chb11", "chb22"]
TEST = {"chb03", "chb06", "chb13", "chb14", "chb15", "chb16", "chb17", "chb18"}

# LOCKED rlg reference (seed42 VAL)
RLG_LATENT = {"chb10": 0.816, "chb11": 0.641, "chb22": 0.736}
RLG_ENS_MACRO = 0.928
FIDELITY_BAND = (0.78, 0.88)      # chb22 zTE vs C0 0.83 +-0.05
R2_MARGIN_MIN = 0.10
NULL_BAND = (0.40, 0.60)


# ----------------------------------------------------------------------------
def load_gamma_strict(gdir, subj, split):
    """Strict: filename MUST contain 'gamma' (avoids grabbing raw {subj}_interictal.npy
    in a shared data/processed dir — the build_ens_tier2 bug, handoff §5)."""
    want_inter = split.startswith("inter")
    for c in sorted(glob.glob(f"{gdir}/*gamma*{subj}*.npy")):
        b = _os.path.basename(c).lower()
        is_inter = "inter" in b
        is_ictal = ("ictal" in b) and not is_inter
        if (want_inter and is_inter) or ((not want_inter) and is_ictal):
            return np.load(c).astype(np.float32)
    raise FileNotFoundError(f"strict gamma {subj}/{split} not in {gdir}")


def bootstrap_ci(si, sc, n_boot=1000, seed=0):
    """Half-width of the 95% percentile CI of window AUROC (paired resample)."""
    rng = np.random.default_rng(seed)
    si = np.asarray(si, float); sc = np.asarray(sc, float)
    base = IO.window_auroc(si, sc)
    aucs = np.empty(n_boot)
    for b in range(n_boot):
        i = rng.integers(0, len(si), len(si)); c = rng.integers(0, len(sc), len(sc))
        aucs[b] = IO.window_auroc(si[i], sc[c])
    lo, hi = np.percentile(aucs, [2.5, 97.5])
    return base, float((hi - lo) / 2.0)


def null_auroc(scores_inter, n_rep=50, seed=0):
    """Interictal-vs-interictal random-label AUROC (~0.5) — the run's noise floor."""
    rng = np.random.default_rng(seed)
    s = np.asarray(scores_inter, float)
    vals = []
    for _ in range(n_rep):
        y = rng.integers(0, 2, len(s))
        if 0 < y.sum() < len(y):
            vals.append(roc_auc_score(y, s))
    return float(np.mean(vals)) if vals else 0.5


def latent_mr(oi, oc):
    """Mahalanobis on graph-level mean latent (fit interictal manifold)."""
    Zi, Zc = oi["Z"], oc["Z"]
    cov = LedoitWolf().fit(Zi)
    return cov.mahalanobis(Zi), cov.mahalanobis(Zc)


# ----------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ckpt", default="data/models_retrain/gae_multirel_seed42.pt")
    ap.add_argument("--a1_dir", default="/kaggle/input/datasets/nhn2mm/chbmit-topk20")
    ap.add_argument("--a2_dir", default="data/processed")
    ap.add_argument("--feat_dir", default="/kaggle/input/datasets/nhn2mm/chbmit-processed")
    ap.add_argument("--raw_dir", default="data/processed",
                    help="raw windows for the input-fidelity zTE check")
    ap.add_argument("--gamma_dir", default="data/processed")
    ap.add_argument("--suffix", default="_topk20")
    ap.add_argument("--out_dir", default="results/phaseC/c4full")
    ap.add_argument("--subjects", default=None)
    ap.add_argument("--skip_fidelity", action="store_true",
                    help="skip the CPU zTE recompute (only if already verified this session)")
    a = ap.parse_args()

    subjs = a.subjects.split(",") if a.subjects else VAL
    leak = [s for s in subjs if s in TEST]
    if leak:
        raise SystemExit(f"INTEGRITY ABORT: TEST subject(s) {leak} — Stage 0 is VAL only.")

    dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = M.load_checkpoint(a.ckpt, dev)
    print(f"ckpt={a.ckpt} device={dev}\n")

    def paths(subj, split):
        return (str(Path(a.a1_dir) / f"{subj}_{split}_adjs{a.suffix}.npy"),
                str(Path(a.a2_dir) / f"{subj}_{split}_te_topk20.npy"),
                str(Path(a.feat_dir) / f"{subj}_{split}_features.npy"))

    res = {}
    ens_i_all, ens_c_all = {}, {}
    print(f"{'subj':7s} {'recon-mr':>9s} {'latent-mr':>10s} {'R2-only':>8s} "
          f"{'R2null':>7s} {'R2marg':>7s} {'ens':>6s} {'δ_lat':>6s}")
    for subj in subjs:
        oi = M.score_windows_mr(model, *paths(subj, "interictal"), dev)
        oc = M.score_windows_mr(model, *paths(subj, "ictal"), dev)

        # recon-mr (total joint recon)
        zr_i, zr_c = IO.robust_z(oi["total"], oc["total"]); recon_au = IO.window_auroc(zr_i, zr_c)
        # latent-mr
        li, lc = latent_mr(oi, oc); zl_i, zl_c = IO.robust_z(li, lc)
        lat_au, dlt = bootstrap_ci(zl_i, zl_c)
        # R2-only recon
        z2_i, z2_c = IO.robust_z(oi["r2"], oc["r2"]); r2_au = IO.window_auroc(z2_i, z2_c)
        r2_null = null_auroc(z2_i); r2_marg = r2_au - r2_null
        # gamma + equal-3 ensemble (recon-mr + latent-mr + gamma)
        gi = load_gamma_strict(a.gamma_dir, subj, "inter")
        gc = load_gamma_strict(a.gamma_dir, subj, "ictal")
        zg_i, zg_c = IO.robust_z(gi, gc)
        ens_i = (zr_i + zl_i + zg_i) / 3.0; ens_c = (zr_c + zl_c + zg_c) / 3.0
        ens_au = IO.window_auroc(ens_i, ens_c)
        ens_i_all[subj], ens_c_all[subj] = ens_i, ens_c

        print(f"{subj:7s} {recon_au:9.3f} {lat_au:10.3f} {r2_au:8.3f} "
              f"{r2_null:7.2f} {r2_marg:7.3f} {ens_au:6.3f} {dlt:6.3f}")
        res[subj] = dict(recon_mr=round(recon_au, 4), latent_mr=round(lat_au, 4),
                         latent_delta=round(dlt, 4), r2_only=round(r2_au, 4),
                         r2_null=round(r2_null, 4), r2_margin=round(r2_marg, 4),
                         ens=round(ens_au, 4), n_inter=len(oi["total"]), n_ictal=len(oc["total"]))

    macro_ens = float(np.mean([res[s]["ens"] for s in subjs]))
    macro_lat = float(np.mean([res[s]["latent_mr"] for s in subjs]))
    print(f"\n[macro] ensemble={macro_ens:.3f} (rlg {RLG_ENS_MACRO})  "
          f"latent-mr={macro_lat:.3f} (rlg 0.731)")

    # ---- relation-collapse ablation (latent-mr with R2 messages zeroed) ----
    print("\n[collapse-ablation] latent-mr full vs no-R2:")
    for subj in subjs:
        oi0 = M.score_windows_mr(model, *paths(subj, "interictal"), dev, use_r2=False)
        oc0 = M.score_windows_mr(model, *paths(subj, "ictal"), dev, use_r2=False)
        li0, lc0 = latent_mr(oi0, oc0); z0i, z0c = IO.robust_z(li0, lc0)
        au0 = IO.window_auroc(z0i, z0c)
        d = res[subj]["latent_mr"] - au0
        res[subj]["latent_noR2"] = round(au0, 4); res[subj]["latent_dAUROC_R2"] = round(d, 4)
        print(f"  {subj}: {res[subj]['latent_mr']:.3f} -> {au0:.3f}  ΔR2={d:+.3f}")

    # ---- input fidelity: reproduce C0 zTE on raw windows (chb22 vs 0.83) ----
    fid = {}
    if not a.skip_fidelity:
        print("\n[input-fidelity] zTE window AUROC on raw TE (reproduce C0):")
        for subj in subjs:
            wi = np.load(Path(a.raw_dir) / f"{subj}_interictal.npy", mmap_mode="r")
            wc = np.load(Path(a.raw_dir) / f"{subj}_ictal.npy", mmap_mode="r")
            Xi, Xc = TEB.te_vectors(wi), TEB.te_vectors(wc)
            raw_i, raw_c, diag = TEB.latent_te_readout(Xi, Xc)
            zi, zc = IO.robust_z(raw_i, raw_c)
            zte_au = IO.window_auroc(zi, zc)
            fid[subj] = dict(zTE_auroc=round(zte_au, 4), null=diag["null"])
            print(f"  {subj}: zTE={zte_au:.3f} null={diag['null']:.2f}")
        res_fidelity = fid
    else:
        res_fidelity = {"skipped": True}

    # ---- pre-registered verdict ----
    print("\n" + "=" * 60 + "\nGO/KILL VERDICT (pre-registered)\n" + "=" * 60)
    checks = {}
    checks["1_ensemble>=0.928"] = macro_ens >= RLG_ENS_MACRO
    checks["2_latent_chb22>0.736"] = res["chb22"]["latent_mr"] > RLG_LATENT["chb22"]
    checks["3_no_harm_chb10"] = res["chb10"]["latent_mr"] >= RLG_LATENT["chb10"] - res["chb10"]["latent_delta"]
    checks["3_no_harm_chb11"] = res["chb11"]["latent_mr"] >= RLG_LATENT["chb11"] - res["chb11"]["latent_delta"]
    if not a.skip_fidelity:
        z22 = fid["chb22"]["zTE_auroc"]
        checks["4a_fidelity_chb22_in_band"] = FIDELITY_BAND[0] <= z22 <= FIDELITY_BAND[1]
    checks["4b_R2_margin_chb22>=0.10"] = res["chb22"]["r2_margin"] >= R2_MARGIN_MIN
    checks["4b_R2_null_in_band"] = NULL_BAND[0] <= res["chb22"]["r2_null"] <= NULL_BAND[1]
    checks["4b_chb22_is_maxR2"] = res["chb22"]["r2_only"] == max(res[s]["r2_only"] for s in subjs)
    checks["4c_no_collapse_chb22"] = res["chb22"]["latent_dAUROC_R2"] > 0

    for k, v in checks.items():
        print(f"  [{'PASS' if v else 'FAIL'}] {k}")
    go = all(checks.values())
    verdict = "GO -> Stage 1 (multi-seed event gate)" if go else "KILL / investigate — rlg stands"
    print(f"\nVERDICT: {'GO' if go else 'NO-GO'}  ({verdict})")
    if not a.skip_fidelity and not checks.get("4a_fidelity_chb22_in_band", True):
        print("  NOTE: 4a failed -> R2 INPUT suspect. Investigate as an eval-bug "
              "BEFORE reading this as a model verdict.")

    out = Path(a.out_dir); out.mkdir(parents=True, exist_ok=True)
    payload = dict(ckpt=a.ckpt, per_subject=res, macro_ensemble=round(macro_ens, 4),
                   macro_latent=round(macro_lat, 4), fidelity=res_fidelity,
                   checks={k: bool(v) for k, v in checks.items()}, go=bool(go))
    (out / "stage0_verdict_seed42.json").write_text(json.dumps(payload, indent=2))
    print(f"\n[saved] {out}/stage0_verdict_seed42.json")


if __name__ == "__main__":
    main()
