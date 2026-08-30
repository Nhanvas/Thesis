"""
build_te_branch.py — Phase C / C4-lite. CPU ONLY (numpy/sklearn; NO GPU, NO torch).

Builds the directed-connectivity ANOMALY BRANCH (zTE) as a first-class robust-z
component, ALIGNED BY CONSTRUCTION to the canonical windows, then forms the
candidate ensemble rltg_te = recon+latent+gamma+TE (equal 1/4) for the SAME event
harness that scored rlg (score_ens -> cpd_pipeline_v14 -> szcore_eval -> OP). Only
the ensemble INPUT changes vs rlg -> "beats rlg" stays a clean claim.

WHY THIS IS ALIGNED (no rebuild, no GPU)
  preprocessing.py writes z-scored artifact-clean raw windows
      data/processed/{subj}_{interictal,ictal}.npy  [N,18,1024]
  in the SAME file/window order that graph_construction/feature_extraction read to
  build adj/features. So reading those arrays and computing TE per window IN ORDER
  yields a component with the SAME window SET and ORDER as features/adj. The
  alignment gate below ASSERTS len(zTE) == len(rlg ensemble) per subject/split.

TE READOUT (matches the VALIDATED C0 probe — NOT a naive zlatent copy)
  Per window: connectivity_probe.conn_matrix(W,"te") -> directed 18x18 TE (i->j),
  bins=6,k=1, per-channel z-score inside conn_matrix (amplitude-invariant regime).
  The TE vector is 306-d (18x18 minus diagonal) -> dim>>n Mahalanobis is degenerate
  (the "all-1.0 AUROC" artifact flagged in the handoff). The C0 probe avoided this
  with PCA(12) BEFORE LedoitWolf; we carry that pinned recipe forward:
      PCA(n_pca=12, fit on interictal only) -> LedoitWolf(interictal) ->
      Mahalanobis(all windows) -> retrain_io.robust_z  (label-free, valid on TEST).
  Subject-z (already applied by preprocessing) does NOT change per-window-z inputs,
  so the TE math is faithful to the probe; the only intended difference is the
  (canonical) window set. CAR is NOT re-applied by default: the C0 evidence was
  generated without it; --car exposes it as a cheap pre-registered ablation.

rltg_te BUILD (exact algebraic identity — no component dumps, no 2nd GPU run)
  rlg ensemble = (zrecon+zlatent+zgamma)/3  (equal-3, committed).
  rltg_te      = (zrecon+zlatent+zgamma+zTE)/4 = 0.75*rlg + 0.25*zTE.
  We build rltg_te from the COMMITTED rlg arrays + zTE. Auditable, reproducible.

INTEGRITY: default subjects = VAL (chb10/11/22). TEST refused unless --allow_test.
Seed 42 canonical. Reproduce-before-trust: prints held-out zTE AUROC (probe-style)
+ interictal-vs-interictal NULL (must be ~0.5) per subject as an eval-bug guard.

USAGE (Cursor CPU)
  python build_te_branch.py --smoke
  python build_te_branch.py \
      --raw_dir data/processed \
      --rlg_dir results/phaseB/tier2/ens_tier2/rlg \
      --out_dir results/phaseC/c4lite
  # one-shot TEST only after VAL gate G2' passes:
  #   ... --subjects chb03,chb06,chb13,chb14,chb15,chb16,chb17,chb18 --allow_test
"""
import os as _os, sys as _sys
# build_te_branch.py lives in src/phaseC/; repo modules are in sibling src/ subdirs
# (retrain_io->src/retrain, graph_construction->src/dataprep, ensemble_recipe->src,
#  connectivity_probe->src/phaseC). Add them all so flat imports resolve locally.
_here = _os.path.dirname(_os.path.abspath(__file__))          # .../src/phaseC
_src  = _os.path.dirname(_here)                               # .../src
for _p in (_src, _here,
           _os.path.join(_src, "retrain"),
           _os.path.join(_src, "dataprep"),
           _os.path.join(_src, "phaseB")):
    if _os.path.isdir(_p) and _p not in _sys.path:
        _sys.path.insert(0, _p)

import argparse
import json
from pathlib import Path

import numpy as np

import retrain_io as IO
import ensemble_recipe as ER
import connectivity_probe as CP
import graph_construction as GC

VAL = ["chb10", "chb11", "chb22"]
TEST = {"chb03", "chb06", "chb13", "chb14", "chb15", "chb16", "chb17", "chb18"}

N_PCA_PINNED = 12   # C0 PREREG pinned value (validated on held-out probe)


# ----------------------------------------------------------------------------
# TE feature matrix per window -> stacked [N, 324] (306 informative off-diagonal)
# ----------------------------------------------------------------------------
def _disc(a, bins):
    a = (a - a.min()) / (np.ptp(a) + 1e-12)
    return np.clip((a * bins).astype(int), 0, bins - 1)


def _H(codes):
    cnt = np.bincount(codes); cnt = cnt[cnt > 0]
    p = cnt / cnt.sum()
    return -np.sum(p * np.log(p))


def te_matrix(W, bins=6, k=1):
    """Vectorized directed binned-TE 18x18 — EXACT replica (max|Δ|~1e-15) of looping
    connectivity_probe.transfer_entropy inside conn_matrix('te'). ~33x faster via
    bincount entropy. Fidelity point: disc() is applied PER SLICE (target[k:],
    target[:-k], source[:-k]) exactly as CP does, and W is z-scored per channel first
    (conn_matrix's amplitude-invariant regime). Verify with --verify_fidelity."""
    W = (W - W.mean(1, keepdims=True)) / (W.std(1, keepdims=True) + 1e-9)
    C = W.shape[0]; b = bins
    fut  = [_disc(W[c][k:],  bins) for c in range(C)]     # disc(target[k:])
    past = [_disc(W[c][:-k], bins) for c in range(C)]     # disc(x[:-k]) target-past & source-past
    M = np.zeros((C, C))
    for j in range(C):
        fj, pj = fut[j], past[j]
        H_xp, H_xfxp = _H(pj), _H(fj * b + pj)
        for i in range(C):
            if i == j: continue
            sp = past[i]
            M[i, j] = max(0.0, H_xfxp + _H(pj * b + sp) - H_xp - _H((fj * b + pj) * b + sp))
    return M


def te_vectors(windows, use_car=False, bins=6, k=1):
    """windows: [N,18,1024] -> [N,324] flattened directed-TE matrices."""
    out = np.empty((len(windows), 18 * 18), dtype=np.float32)
    for n, W in enumerate(windows):
        W = np.asarray(W, dtype=np.float64)
        if use_car:
            W = GC.apply_car(W)              # optional; OFF by default (match C0 probe)
        out[n] = te_matrix(W, bins=bins, k=k).ravel().astype(np.float32)
    return out


def latent_te_readout(Xi, Xc, n_pca=N_PCA_PINNED, seed=0):
    """Interictal-fit PCA + LedoitWolf Mahalanobis (label-free) on the TE vectors.
    Returns (raw_i, raw_c, diag) where diag has held-out AUROC + null for sanity."""
    from sklearn.covariance import LedoitWolf
    from sklearn.decomposition import PCA
    from sklearn.metrics import roc_auc_score

    Xi = np.nan_to_num(Xi); Xc = np.nan_to_num(Xc)
    keep = Xi.std(0) > 1e-9                  # drop 18 constant-zero diagonal dims -> 306
    Xi, Xc = Xi[:, keep], Xc[:, keep]
    n_dim = Xi.shape[1]
    k = int(min(n_pca, len(Xi) - 1, n_dim))
    if k < 2:
        raise RuntimeError(f"too few interictal windows for PCA (n={len(Xi)})")

    # ---- component score: fit on ALL interictal (label-free), score ALL windows
    pca = PCA(n_components=k).fit(Xi)
    cov = LedoitWolf().fit(pca.transform(Xi))
    raw_i = cov.mahalanobis(pca.transform(Xi))
    raw_c = cov.mahalanobis(pca.transform(Xc))

    # ---- diagnostics (do NOT feed the pipeline): held-out separation + null ~0.5
    # fit on interictal TRAIN half; score held-out interictal + ictal (probe-style).
    rng = np.random.default_rng(seed); perm = rng.permutation(len(Xi)); h = len(Xi) // 2
    tr, teh = perm[:h], perm[h:]
    kk = int(min(n_pca, h - 1, n_dim))
    p2 = PCA(n_components=kk).fit(Xi[tr]); c2 = LedoitWolf().fit(p2.transform(Xi[tr]))
    die = c2.mahalanobis(p2.transform(Xi[teh]))   # held-out interictal
    dce = c2.mahalanobis(p2.transform(Xc))        # ictal
    au = float(roc_auc_score(np.r_[np.zeros(len(die)), np.ones(len(dce))], np.r_[die, dce]))
    # null: random labels on the homogeneous held-out interictal -> must be ~0.5
    yr = rng.integers(0, 2, len(die))
    null = float(roc_auc_score(yr, die)) if 0 < yr.sum() < len(yr) else 0.5
    return raw_i, raw_c, dict(auroc_heldout=round(au, 4), null=round(null, 4),
                              n_pca=k, n_dim=int(n_dim))


def load_rlg(rlg_dir, seed, subj):
    d = Path(rlg_dir)
    ei = np.load(d / f"ens_seed{seed}_{subj}_inter.npy").astype(np.float64)
    ec = np.load(d / f"ens_seed{seed}_{subj}_ictal.npy").astype(np.float64)
    return ei, ec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw_dir", default="data/processed",
                    help="dir with {subj}_{interictal,ictal}.npy [N,18,1024]")
    ap.add_argument("--rlg_dir", default="results/phaseB/tier2/ens_tier2/rlg",
                    help="committed rlg ensemble arrays (equal-3) for rltg_te identity + alignment gate")
    ap.add_argument("--out_dir", default="results/phaseC/c4lite")
    ap.add_argument("--subjects", default=None, help="comma list; default = VAL (chb10,11,22)")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--n_pca", type=int, default=N_PCA_PINNED)
    ap.add_argument("--car", action="store_true", help="apply CAR before TE (OFF by default; matches C0 probe)")
    ap.add_argument("--allow_test", action="store_true", help="required to touch TEST (one-shot)")
    ap.add_argument("--verify_fidelity", action="store_true",
                    help="assert vectorized te_matrix == connectivity_probe.conn_matrix, then exit")
    ap.add_argument("--smoke", action="store_true")
    a = ap.parse_args()

    if a.verify_fidelity:
        rng = np.random.default_rng(3); md = 0.0
        for _ in range(8):
            W = rng.standard_normal((18, 1024))
            md = max(md, float(np.abs(CP.conn_matrix(W, "te") - te_matrix(W)).max()))
        print(f"max|Δ| te_matrix vs validated conn_matrix('te'): {md:.2e}")
        assert md < 1e-9, "TE fidelity broken — DO NOT trust the branch"
        print("[FIDELITY PASS] vectorized TE is numerically identical to C0 probe.")
        return

    if a.smoke:
        out = Path("/tmp/te_smoke"); (out / "components").mkdir(parents=True, exist_ok=True)
        rng = np.random.default_rng(0)
        # fidelity: vectorized TE == validated C0 conn_matrix('te')
        Wf = rng.standard_normal((18, 1024))
        dmax = float(np.abs(CP.conn_matrix(Wf, "te") - te_matrix(Wf)).max())
        assert dmax < 1e-9, f"TE fidelity broken: {dmax}"
        print(f"[SMOKE] TE fidelity vs C0 conn_matrix: max|Δ|={dmax:.1e}  PASS")
        # 60 interictal + 12 ictal random 4s windows; ictal given mild extra coupling
        wi = rng.standard_normal((60, 18, 1024))
        wc = rng.standard_normal((12, 18, 1024)); wc[:, 1] += 0.3 * wc[:, 0]  # 0->1 driver
        Xi, Xc = te_vectors(wi, a.car), te_vectors(wc, a.car)
        raw_i, raw_c, diag = latent_te_readout(Xi, Xc, n_pca=a.n_pca)
        zi, zc = IO.robust_z(raw_i, raw_c)
        assert len(zi) == 60 and len(zc) == 12, "length mismatch"
        # identity check: rltg_te == 0.75*rlg + 0.25*zTE, and == build_ensemble_subset
        rlg_i = rng.standard_normal(60); rlg_c = rng.standard_normal(12)
        ident_i = 0.75 * rlg_i + 0.25 * zi
        # cross-check vs build_ensemble_subset on 4 fake components summing to same
        comp = {"zrecon": rng.standard_normal(60), "zlatent": rng.standard_normal(60),
                "zgamma": rng.standard_normal(60), "zTE": zi}
        rlg_from_comp = ER.build_ensemble_subset(comp, ("zrecon", "zlatent", "zgamma"))
        rltg_from_comp = ER.build_ensemble_subset(comp, ("zrecon", "zlatent", "zgamma", "zTE"))
        assert np.allclose(0.75 * rlg_from_comp + 0.25 * zi, rltg_from_comp), "identity broken"
        print(f"[SMOKE] TE vectors {Xi.shape} -> zTE ok; diag={diag}")
        print(f"[SMOKE] identity 0.75*rlg+0.25*zTE == build_ensemble_subset(4) : PASS")
        print("[SMOKE] PASS")
        return

    subjs = a.subjects.split(",") if a.subjects else VAL
    leak = [s for s in subjs if s in TEST]
    if leak and not a.allow_test:
        raise SystemExit(f"INTEGRITY ABORT: TEST subject(s) {leak}. Pass --allow_test ONLY "
                         f"for the final one-shot pass after VAL gate G2' passes.")
    if leak:
        print(f"*** ONE-SHOT TEST PASS on {leak} — the single allowed TEST exposure. ***")

    raw = Path(a.raw_dir); out = Path(a.out_dir)
    cdir = out / "components"; cdir.mkdir(parents=True, exist_ok=True)
    tdir = out / "rltg_te"; tdir.mkdir(parents=True, exist_ok=True)
    sd = a.seed
    print(f"seed={sd} n_pca={a.n_pca} car={a.car} subjects={subjs}")
    print(f"{'subj':7s} {'n_inter':>7s} {'n_ict':>5s} {'zTE_AUC':>7s} {'null':>5s} "
          f"{'rlg_AUC':>7s} {'rltg_te_AUC':>11s}")

    summ = {}
    for subj in subjs:
        wi = np.load(raw / f"{subj}_interictal.npy", mmap_mode="r")
        wc = np.load(raw / f"{subj}_ictal.npy", mmap_mode="r")
        Xi, Xc = te_vectors(wi, a.car), te_vectors(wc, a.car)
        raw_i, raw_c, diag = latent_te_readout(Xi, Xc, n_pca=a.n_pca)
        zi, zc = IO.robust_z(raw_i, raw_c)
        np.save(cdir / f"zTE_{subj}_inter.npy", zi.astype(np.float32))
        np.save(cdir / f"zTE_{subj}_ictal.npy", zc.astype(np.float32))

        # ---- ALIGNMENT GATE + rltg_te via identity from committed rlg
        rlg_i, rlg_c = load_rlg(a.rlg_dir, sd, subj)
        assert len(zi) == len(rlg_i), f"{subj} inter align {len(zi)}!={len(rlg_i)}"
        assert len(zc) == len(rlg_c), f"{subj} ictal align {len(zc)}!={len(rlg_c)}"
        rt_i = 0.75 * rlg_i + 0.25 * zi
        rt_c = 0.75 * rlg_c + 0.25 * zc
        np.save(tdir / f"ens_seed{sd}_{subj}_inter.npy", rt_i.astype(np.float32))
        np.save(tdir / f"ens_seed{sd}_{subj}_ictal.npy", rt_c.astype(np.float32))

        te_auc = IO.window_auroc(zi, zc)
        rlg_auc = IO.window_auroc(rlg_i, rlg_c)
        rt_auc = IO.window_auroc(rt_i, rt_c)
        flag = "" if 0.40 <= diag["null"] <= 0.60 else "  <-- NULL NOT ~0.5: eval suspect!"
        print(f"{subj:7s} {len(zi):7d} {len(zc):5d} {te_auc:7.3f} {diag['null']:5.2f} "
              f"{rlg_auc:7.3f} {rt_auc:11.3f}{flag}")
        summ[subj] = dict(n_inter=len(zi), n_ictal=len(zc),
                          zTE_auroc_insample=round(te_auc, 4),
                          zTE_auroc_heldout=diag["auroc_heldout"], null=diag["null"],
                          rlg_auroc=round(rlg_auc, 4), rltg_te_auroc=round(rt_auc, 4))

    (tdir / "ens_weights.json").write_text(json.dumps(
        dict(subset=["zrecon", "zlatent", "zgamma", "zTE"], weights="equal",
             built_as="0.75*rlg + 0.25*zTE (identity)"), indent=2))
    (out / f"te_branch_diag_seed{sd}.json").write_text(json.dumps(summ, indent=2))
    macro = round(float(np.mean([v["rltg_te_auroc"] for v in summ.values()])), 4)
    macro_rlg = round(float(np.mean([v["rlg_auroc"] for v in summ.values()])), 4)
    print(f"\n[macro window AUROC] rlg={macro_rlg}  rltg_te={macro}")
    print(f"Next: score_ens.py --ens_dir {tdir} --seed {sd} "
          f"--only_subjects {','.join(subjs)}  then g2_val_gate vs rlg.")


if __name__ == "__main__":
    main()