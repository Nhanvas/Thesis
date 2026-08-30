"""
build_ens_tier2.py — KAGGLE GPU ONLY (Phase B / Tier-2). Sibling of build_ens.py.

Builds the robust-z components INCLUDING the first-class latent-Mahalanobis branch
(zlatent), then for each PRE-REGISTERED candidate subset forms the equal-weight
ensemble and saves the two score arrays in the EXACT format score_ens.py consumes:
    <out_dir>/<candidate_tag>/ens_seed{S}_{subj}_{inter,ictal}.npy
So the downstream event harness (score_ens -> cpd_pipeline_v14 -> szcore_eval ->
fp_budget_operating_point) is byte-identical to the §0 baseline — only the ensemble
INPUT changes. That is what makes "beats §0" a clean claim.

Components:
  zrecon,ztemp,zgamma  <- retrain_io.build_subject_components (unchanged, pinned recipe)
  zlatent              <- graph-mean-pooled GAE latent Z (16-d); LedoitWolf covariance
                          fit on that subject's INTERICTAL only (label-free, valid on
                          TEST); Mahalanobis distance -> robust_z (same recipe as others).

Candidates (ensemble_recipe.CANDIDATES): baseline_rtg (=§0, the G2 baseline),
rltg (PRIMARY), ltg (SECONDARY), rlg (EXPLORATORY, VAL only).

INTEGRITY: default subjects = VAL (chb10/11/22). TEST subjects are refused unless
--allow_test is passed (the single one-shot pass at the very end). Seed 42 canonical.

USAGE (Kaggle GPU)
  python build_ens_tier2.py --input_root /kaggle/input --out_dir /kaggle/working/ens_tier2
  # one-shot TEST at the very end (only after VAL guardrail G2 passes):
  python build_ens_tier2.py --input_root /kaggle/input --out_dir /kaggle/working/ens_tier2 \
      --subjects chb03,chb06,chb13,chb14,chb15,chb16,chb17,chb18 --allow_test
Smoke (no torch/sklearn):
  python build_ens_tier2.py --smoke
"""
import os as _os, sys as _sys
_here = _os.path.dirname(_os.path.abspath(__file__))
for _p in (_here, _os.path.dirname(_here)):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

import argparse
import json
import os as _os, sys as _sys
from pathlib import Path

# build_ens_tier2 runs on Kaggle (all .py cp'd flat to /kaggle/working) OR locally
# from src/phaseB (modules scattered in sibling src/ subdirs). Add both so imports
# resolve either way.
_here = _os.path.dirname(_os.path.abspath(__file__))
_src = _os.path.dirname(_here)
for _p in (_here, _src, _os.path.join(_src, "retrain"), _os.path.join(_src, "dataprep"),
           _os.path.join(_src, "phaseB")):
    if _os.path.isdir(_p) and _p not in _sys.path:
        _sys.path.insert(0, _p)

import numpy as np

import retrain_io as IO
import ensemble_recipe as ER

VAL = ["chb10", "chb11", "chb22"]
TEST = {"chb03", "chb06", "chb13", "chb14", "chb15", "chb16", "chb17", "chb18"}


def rlg_components(gae, subj, adj_dir, feat_dir, gamma_dir, suffix, device):
    """recon + gamma robust-z components WITHOUT lstm/ztemp — identical computation to
    the zrecon/zgamma branches of retrain_io.build_subject_components. For GAE-only
    (new-seed) rlg builds where no LSTM checkpoint exists."""
    import gae_joint as G
    import glob as _glob
    ai = Path(adj_dir) / f"{subj}_interictal_adjs{suffix}.npy"
    ac = Path(adj_dir) / f"{subj}_ictal_adjs{suffix}.npy"
    fi = Path(feat_dir) / f"{subj}_interictal_features.npy"
    fc = Path(feat_dir) / f"{subj}_ictal_features.npy"
    rri = G.score_windows(gae, ai, fi, device); rrc = G.score_windows(gae, ac, fc, device)
    zri, zrc = IO.robust_z(rri, rrc)

    # gamma: require 'gamma' in the filename. IO.load_gamma globs *{subj}* which, when
    # gamma files share a dir with raw windows (local data/processed), can grab
    # {subj}_interictal.npy [N,18,1024] instead of gamma_aec_{subj}_inter.npy. This
    # stricter glob is byte-identical to IO.load_gamma on a clean gamma dir (Kaggle).
    def _gamma(split):
        want_inter = (split == "inter")
        for c in sorted(_glob.glob(f"{gamma_dir}/*gamma*{subj}*.npy")):
            b = _os.path.basename(c).lower()
            is_inter = "inter" in b
            is_ictal = ("ictal" in b) and not is_inter
            if (want_inter and is_inter) or ((not want_inter) and is_ictal):
                return np.load(c).astype(np.float32)
        raise FileNotFoundError(f"gamma {subj}/{split} (with 'gamma' in name) not in {gamma_dir}")
    gi, gc = _gamma("inter"), _gamma("ictal")
    zgi, zgc = IO.robust_z(gi, gc)
    return {"zrecon": (zri, zrc), "zgamma": (zgi, zgc)}


def latent_component(gae, subj, adj_dir, feat_dir, suffix, device):
    """zlatent for one subject: fit LedoitWolf on interictal pooled Z, Mahalanobis
    on both splits, robust_z (pinned recipe, inter+ictal pooled). Returns (zi, zc)."""
    import gae_joint as G
    from sklearn.covariance import LedoitWolf

    def pool(split):
        A = Path(adj_dir) / f"{subj}_{split}_adjs{suffix}.npy"
        F = Path(feat_dir) / f"{subj}_{split}_features.npy"
        adjs = np.load(A, mmap_mode="r"); feats = np.load(F, mmap_mode="r")
        Z = []
        import torch
        gae.eval()
        with torch.no_grad():
            for s in range(0, len(adjs), 512):
                e = min(s + 512, len(adjs))
                At = torch.tensor(adjs[s:e].astype(np.float32))
                Xt = torch.tensor(feats[s:e].astype(np.float32))
                pg, _, _, B = G.build_batch(At, Xt, device)
                z = gae.encoder(pg.x, pg.edge_index, pg.edge_attr).view(B, G.N_CH, G.LATENT_DIM)
                Z.append(z.mean(dim=1).cpu().numpy().astype(np.float32))  # [B,16]
        return np.concatenate(Z, 0)

    Zi, Zc = pool("interictal"), pool("ictal")
    cov = LedoitWolf().fit(Zi)                       # interictal manifold ONLY (label-free)
    di, dc = cov.mahalanobis(Zi), cov.mahalanobis(Zc)
    return IO.robust_z(di, dc)                        # same recipe as zrecon/ztemp/zgamma


def save_ens(out, tag, sd, subj, comp_i, comp_c, subset):
    d = out / tag; d.mkdir(parents=True, exist_ok=True)
    ei = ER.build_ensemble_subset(comp_i, subset)
    ec = ER.build_ensemble_subset(comp_c, subset)
    np.save(d / f"ens_seed{sd}_{subj}_inter.npy", ei.astype(np.float32))
    np.save(d / f"ens_seed{sd}_{subj}_ictal.npy", ec.astype(np.float32))
    return IO.window_auroc(ei, ec)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input_root", default="/kaggle/input")
    ap.add_argument("--ckpt_root", default=None,
                    help="dir to DISCOVER checkpoints (default=input_root). Point at the "
                         "CANONICAL committed dataset to PIN provenance (data/models_retrain).")
    ap.add_argument("--suffix", default="_topk20")
    ap.add_argument("--seed", type=int, default=42)          # canonical single seed
    ap.add_argument("--subjects", default=None, help="comma list; default = VAL (chb10,11,22)")
    ap.add_argument("--out_dir", default="/kaggle/working/ens_tier2")
    ap.add_argument("--allow_test", action="store_true", help="required to touch TEST (one-shot)")
    ap.add_argument("--dump_components", action="store_true",
                    help="also save per-branch robust-z components for provenance diffs.")
    ap.add_argument("--only", default=None,
                    help="comma list of candidate tags to build (default=all). "
                         "e.g. --only baseline_rtg reproduces §0 with NO latent (one-shot preserved).")
    ap.add_argument("--smoke", action="store_true")
    a = ap.parse_args()

    if a.smoke:
        out = Path("/tmp/ens_tier2_smoke")
        rng = np.random.default_rng(0)
        ci = {k: rng.normal(size=300) for k in ER.COMPONENT_KEYS_EXT}
        cc = {k: rng.normal(1.2, 1, 40) for k in ER.COMPONENT_KEYS_EXT}
        for tag, subset in ER.CANDIDATES.items():
            wa = save_ens(out, tag, 42, "chb10", ci, cc, subset)
            assert (out / tag / "ens_seed42_chb10_inter.npy").exists()
            assert 0.0 <= wa <= 1.0
            print(f"[SMOKE] {tag:12s} subset={subset} window AUROC={wa:.3f}")
        print("[SMOKE] PASS")
        return

    subjs = a.subjects.split(",") if a.subjects else VAL
    leak = [s for s in subjs if s in TEST]
    if leak and not a.allow_test:
        raise SystemExit(f"INTEGRITY ABORT: TEST subject(s) {leak}. Pass --allow_test "
                         f"ONLY for the final one-shot pass after VAL guardrail G2 passes.")
    if leak:
        print(f"*** ONE-SHOT TEST PASS on {leak} — this is the single allowed TEST exposure. ***")

    import torch
    import gae_joint as G
    dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    sd = a.seed

    adj_dir = IO.find_data_dir(a.input_root, f"chb13_interictal_adjs{a.suffix}.npy")
    feat_dir = IO.find_data_dir(a.input_root, "chb13_interictal_features.npy")
    gamma_dir = IO.find_gamma_dir(a.input_root)
    ckpt_root = a.ckpt_root or a.input_root
    gae_ck = IO.find_ckpts(ckpt_root, "gae_joint_seed")
    print(f"ckpt_root={ckpt_root}")
    print(f"device={dev} seed={sd} subjects={subjs}")

    active = [t.strip() for t in a.only.split(",")] if a.only else list(ER.CANDIDATES)
    bad = [t for t in active if t not in ER.CANDIDATES]
    if bad: raise SystemExit(f"unknown --only tags {bad}; valid={list(ER.CANDIDATES)}")
    need_latent = any("zlatent" in ER.CANDIDATES[t] for t in active)
    need_temp = any("ztemp" in ER.CANDIDATES[t] for t in active)

    gae = G.GAEModel().to(dev)
    gsd = IO.load_state(gae_ck[sd]); gae.load_state_dict(gsd.get("state_dict", gsd), strict=True); gae.eval()

    # LSTM is only needed for temporal candidates. rlg (recon+latent+gamma) is
    # temporal-free, so a GAE-only new seed (no lstm_temporal_seed{S}.pt) can still
    # build rlg. Only DISCOVER + load LSTM when a temporal candidate is active —
    # find_ckpts raises if none exist, so calling it unconditionally would crash
    # a legitimate rlg-only build on a GAE-only ckpt_root.
    lstm = None
    if need_temp:
        lstm_ck = IO.find_ckpts(ckpt_root, "lstm_temporal_seed")
        if sd not in lstm_ck:
            raise SystemExit(f"temporal candidate active but no lstm_temporal_seed{sd} ckpt; "
                             f"rlg-only build does not need it (drop ztemp candidates).")
        import lstm_temporal as T
        lstm = T.LSTMPredictor(in_dim=18 * 16).to(dev)
        lsd = IO.load_state(lstm_ck[sd]); lstm.load_state_dict(lsd.get("state_dict", lsd), strict=True); lstm.eval()
    print(f"building candidates: {active}  (latent computed: {need_latent})")
    out = Path(a.out_dir)
    wa_all = {tag: {} for tag in active}
    for subj in subjs:
        if lstm is None:
            comp = rlg_components(gae, subj, adj_dir, feat_dir, gamma_dir, a.suffix, dev)
        else:
            comp = IO.build_subject_components(gae, lstm, subj, adj_dir, feat_dir, gamma_dir, a.suffix, dev)
        if need_latent:
            zli, zlc = latent_component(gae, subj, adj_dir, feat_dir, a.suffix, dev)
            comp["zlatent"] = (zli, zlc)
        keys = [k for k in ER.COMPONENT_KEYS_EXT if k in comp]
        comp_i = {k: comp[k][0] for k in keys}
        comp_c = {k: comp[k][1] for k in keys}
        if a.dump_components:
            cd = out / "components"; cd.mkdir(parents=True, exist_ok=True)
            for k in comp:
                np.save(cd / f"{k}_{subj}_inter.npy", np.asarray(comp[k][0], dtype=np.float32))
                np.save(cd / f"{k}_{subj}_ictal.npy", np.asarray(comp[k][1], dtype=np.float32))
        for tag in active:
            wa_all[tag][subj] = round(save_ens(out, tag, sd, subj, comp_i, comp_c, ER.CANDIDATES[tag]), 4)
        print(f"  {subj}: " + " ".join(f"{t}={wa_all[t][subj]:.3f}" for t in active), flush=True)

    for tag in active:
        (out / tag / f"window_auroc_seed{sd}.json").write_text(json.dumps(wa_all[tag], indent=2))
        (out / tag / "ens_weights.json").write_text(json.dumps(
            dict(subset=list(ER.CANDIDATES[tag]), weights="equal"), indent=2))
    macro = {t: round(float(np.mean(list(v.values()))), 4) for t, v in wa_all.items()}
    print(f"\n[macro window AUROC] {macro}")
    print(f"Done. Download {out}/ to Cursor, then per candidate run score_ens.py "
          f"(--ens_dir <out>/<tag> --only_subjects {','.join(subjs)}).")


if __name__ == "__main__":
    main()
