#!/usr/bin/env python
"""
v9_x3_cv_eval.py -- V9-X3 (docs/prompts/V9_X3_CV_PREP.md), step 4: dump + score. For a fold's own
trained GAE checkpoint (gae_fold{k}_seed{seed}.pt, written by v9_x3_train_fold.py on Kaggle), dump
the per-channel LedoitWolf distance D of the GAE node latent on a case's valid windows, then run
the FROZEN downstream chain unchanged: e17b_latent_family.member() (order statistics 6/9/12 +
channel mean, each with the E16e +-15 min running-median correction inside each file) ->
percentile-mean final scalar / robust-z-mean member signal (v9_e1_baselines.final_scalar_from_D /
member_mean_z_from_D) -> D1 smoothing 5 -> per-patient budget clip(q_i(k), 0.005, 0.02), k
calibrated ONCE PER FOLD on that fold's own TRAINING cases (p3_levers.calibrate(), label-free,
median q_i(k) = 0.005, exactly v9_e1b_calibrate.calibrate()'s construction) -> merge 90 s ->
kernel-CPD localizer (p3_levers.localize, mode "cpd") -> SzCORE scorer (p2_scalars.score).
Read-only reuse, no frozen file edited: p2_scalars.py, e16_recording_baseline.py,
e17b_latent_family.py, e18_cpd_localizer.py, p3_levers.py, v9_e1_baselines.py (subject_ctx,
final_scalar_from_D, member_mean_z_from_D, evaluate_arm), p2_dump_seeds23.py (run_model's own
per-window GAE forward pass, generalised here to an explicit checkpoint path instead of a
module-global tag/directory).

GATE (--gate; run before anything else is trusted; no GPU, no new extraction -- reads only
already-committed dumps and code): with the ORIGINAL thesis checkpoint
(data/models_v2/gae_v2_clean_seed42.pt, loaded by tag "clean_seed42" exactly as every other V9
script) and the original 15/8 split, chb03's "balanced" point (results/e23_test_look7/
per_subject_seed.csv, results/p3c_freeze/freeze.json's k = 4.067744298524509, floor 0.005, cap
0.02) must reproduce EXACTLY: detector tp=7 fp=23, localized (cpd) tp=7 fp=22. STOP if not --
this is the one gate this script's own evaluate_arm() call must pass before a fold's dump/score
numbers (which reuse the identical call) can be trusted.

chb24 (fold 3 only; never in the original 15/8 split): its own window array
(results/v9_x3/chb24.npz, built by v9_x3_build_chb24.py -- NOT results/v9_anatomy/xcache/
chb24.npz, different z-scoring, see that script's docstring) is read directly here (chb24_ctx()),
bypassing v9_e1_baselines.subject_ctx's EXT path (xcache + label-free stats, a different,
deliberately-external-deployment condition used by V9-T3/E1/E4, not the within-split convention
V9-X3 needs).

Per-fold k calibration (--calibrate) and per-case dump+score (--score) both need a trained
checkpoint and are therefore NOT run as part of V9-X3 preparation -- they are written and gated
here so they are ready the moment a fold's Kaggle run returns gae_fold{k}_seed42.pt.

Run:  python src/v9_x3_cv_eval.py --gate
      python src/v9_x3_cv_eval.py --calibrate --fold 1 --ckpt_dir <dir with gae_fold1_seed42.pt>
      python src/v9_x3_cv_eval.py --score --fold 1 --ckpt_dir <dir> --seed 42
"""
import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.covariance import LedoitWolf

ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT / "src", ROOT / "src" / "retrain", ROOT / "src" / "phaseB", ROOT / "src" / "phaseC",
          ROOT / "src" / "dataprep"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
import p2_scalars as PS                # noqa: E402
import e18_cpd_localizer as E18        # noqa: E402
import p3_levers as P3L                # noqa: E402
import v9_e1_baselines as V9E1         # noqa: E402
import train_gae_v2 as TGV2            # noqa: E402

OUT = ROOT / "results" / "v9_x3"
WIN, SMOOTH, FLOOR, CAP = 4, 5, 0.005, 0.02
GATE_K = 4.067744298524509          # results/p3c_freeze/freeze.json, == v9_e1b calibration.json k_G
GATE_REF = dict(detector=(7, 23), localized=(7, 22))   # chb03, seed42, "balanced" point


# ------------------------------------------------------------------------------------- context
def chb24_ctx():
    """Same dict shape as p2_scalars.subject_context, sourced from results/v9_x3/chb24.npz. No
    D/Z/c8/p2 fields: V9-X3 always supplies its OWN fold-trained D explicitly (dump_D below), never
    a frozen dump."""
    z = np.load(OUT / "chb24.npz", allow_pickle=True)
    ok = ~z["is_signal_loss"].astype(bool)
    idx = np.flatnonzero(ok)
    ict = z["is_ictal"].astype(bool)
    fidx = z["file_idx"].astype(int)
    return dict(s="chb24", z=z, idx=idx, n=len(ict), ok=ok, fidx=fidx, wf=fidx[idx], ict=ict,
                ict_ok=ict & ok, fl5=z["is_flag5sd"].astype(bool),
                nonict=~ict & ~z["is_buffer"].astype(bool) & ok,
                nh=float((~ict & ok).sum()) * WIN / 3600)


def case_ctx(subj):
    """ctx for any of the 24 CHB-MIT cases. The 23 thesis-split subjects reuse
    v9_e1_baselines.subject_ctx (works unmodified: its DEV/TEST dispatch already covers them via
    data/trainset_v2|testset_v2; its D/Z fields are present but IGNORED by this script -- we never
    read ctx["D"], only the window-bookkeeping fields idx/ok/fidx/wf/ict/n/z). chb24 uses
    chb24_ctx() instead of subject_ctx's EXT path (see module docstring)."""
    return chb24_ctx() if subj == "chb24" else V9E1.subject_ctx(subj)


# ------------------------------------------------------------------------------------- GAE forward + D
def run_model_ckpt(ckpt, meta, adj, Xn_all, f7):
    """p2_dump_seeds23.run_model, generalised to an explicit checkpoint + meta path instead of a
    module-global tag resolved under data/models_v2/ -- the only change; the forward pass itself
    (encoder, reconstruction, latent) is byte-identical."""
    import torch
    from torch_geometric.data import Data, Batch
    from torch_geometric.utils import dense_to_sparse
    import gae_joint as G
    mu, sd, clip = np.array(meta["add_mean"]), np.array(meta["add_std"]), meta["clip"]
    fa = ((np.clip((f7 - mu) / sd, -clip, clip) + clip) / (2 * clip)).astype(np.float32)
    model = G.GAEModel(in_dim=meta["in_dim"], bands=meta["out_x"])
    model.load_state_dict(torch.load(str(ckpt), map_location="cpu"), strict=True)
    model.eval()
    ox = meta["out_x"]; n = len(adj)
    rec = np.empty(n, np.float32)
    Z = np.empty((n, G.N_CH, G.LATENT_DIM), np.float32)
    CHUNK = 1024
    with torch.no_grad():
        for s in range(0, n, CHUNK):
            e = min(s + CHUNK, n)
            dl = []
            for i in range(s, e):
                A = torch.tensor(adj[i]); An = A / (A.amax() + 1e-8)
                xt = torch.cat([torch.tensor(Xn_all[i].astype(np.float32)), torch.tensor(fa[i])], dim=1)
                ei, ew = dense_to_sparse(A)
                dl.append(Data(x=torch.cat([An, xt], dim=1), edge_index=ei, edge_attr=ew, A=A, Xt=xt))
            b = Batch.from_data_list(dl); B = b.num_graphs
            zz = model.encoder(b.x, b.edge_index, b.edge_attr)
            zp = zz.view(B, G.N_CH, G.LATENT_DIM)
            Ah = torch.clamp(torch.bmm(zp, zp.transpose(1, 2)), 0.0, 1.0)
            Xh = model.x_decoder(zz).view(B, G.N_CH, ox)
            A_ = b.A.view(B, G.N_CH, G.N_CH); X_ = b.Xt.view(B, G.N_CH, ox)
            rec[s:e] = (((A_ - Ah) ** 2).mean(dim=(1, 2)) + G.LAMBDA * ((X_ - Xh) ** 2).mean(dim=(1, 2))).numpy()
            Z[s:e] = zp.numpy()
    return rec, Z


def dump_D(ctx, ckpt, meta, cache_key=None):
    """cache_key, when given (e.g. "fold1_seed42/chb12"), persists D under results/v9_x3/dumps/
    so a restarted --calibrate/--score does not redo the GAE forward pass; keyed only by fold+
    seed+case, which is safe because dump_D's inputs (ctx's window set, the checkpoint) are
    otherwise fixed for a given (fold, seed, case) triple."""
    if cache_key is not None:
        fp = OUT / "dumps" / f"{cache_key}_D.npy"
        if fp.exists():
            D = np.load(fp)
            if len(D) == len(ctx["idx"]):
                return D
    z = ctx["z"]; idx = ctx["idx"]
    adj = z["adj"][idx].astype(np.float32); adj[~np.isfinite(adj).all(axis=(1, 2))] = 0.0
    bp5 = z["bp5"][idx].astype(np.float32); bp5[~np.isfinite(bp5)] = 0.0
    f7 = z["f7"][idx].astype(np.float64)
    xn = TGV2.bp_minmax(bp5)
    _, Z = run_model_ckpt(ckpt, meta, adj, xn, f7)
    D = np.empty((len(idx), Z.shape[1]), np.float32)
    for c in range(Z.shape[1]):
        Zc = Z[:, c, :].astype(np.float64)
        D[:, c] = LedoitWolf().fit(Zc).mahalanobis(Zc)
    if cache_key is not None:
        fp = OUT / "dumps" / f"{cache_key}_D.npy"
        fp.parent.mkdir(parents=True, exist_ok=True)
        np.save(fp, D)
    return D


def evaluate_full(ctx, x, m, k):
    """evaluate_arm's own construction, PLUS matched onset/offset error rows and duration-bin
    hits (P3L.refs_of / E18.match_errors / V9E1.duration_bins) -- the extra pieces the prompt's
    step 5 reporting needs (onset/offset error, duration bins) that evaluate_arm's return value
    alone does not carry (it drops P3L.localize's `pair` mapping)."""
    q = P3L.q_of(PS.smoothed(ctx, m, SMOOTH), k)
    top = float(np.clip(q, FLOOR, max(CAP, FLOOR)))
    det = PS.d1_events(ctx, x, SMOOTH, top)
    thr = np.nanquantile(PS.smoothed(ctx, x, SMOOTH), 1 - top)
    loc, pair = P3L.localize(ctx, x, det, thr, "cpd")
    out = {}
    for name, ev in (("detector", det), ("localized", loc)):
        tp, fp, nr, h = PS.score(ctx, ev)
        kk, ns = PS.caught(PS.short_refs(ctx), ev)
        out[name] = dict(tp=tp, fp=fp, n_ref=nr, nonict_h=h, short_tp=kk, short_n=ns, top=top, q_raw=q)
    refs = P3L.refs_of(ctx)
    errs = [dict(ref_dur=rb - ra, ev_dur=h1 - h0, onset_err=pair[(f_, h0, h1)][0] - ra,
                 offset_err=pair[(f_, h0, h1)][1] - rb)
            for f_, ra, rb, h0, h1 in E18.match_errors(refs, det)]
    bins = V9E1.duration_bins(ctx, loc)
    return out, errs, bins


def load_fold_ckpt(ckpt_dir, fold, seed):
    ck = Path(ckpt_dir) / f"gae_fold{fold}_seed{seed}.pt"
    meta = json.loads(ck.with_suffix(".json").read_text())
    return ck, meta


# ------------------------------------------------------------------------------------- gate
def gate_chb03():
    """No new compute beyond one evaluate_arm() call: reuses the already-committed clean_seed42
    dump (results/p2_test/chb03.npz) via v9_e1_baselines.subject_ctx -> e22_test_oneshot.test_context."""
    ctx = V9E1.subject_ctx("chb03")
    D = ctx["D"]["clean_seed42"]
    x = V9E1.final_scalar_from_D(ctx, D)
    m = V9E1.member_mean_z_from_D(ctx, D)
    out, _, _ = V9E1.evaluate_arm(ctx, x, GATE_K, FLOOR, CAP, SMOOTH, m=m)
    bad = []
    for stage, (tp_ref, fp_ref) in GATE_REF.items():
        got = (out[stage]["tp"], out[stage]["fp"])
        if got != (tp_ref, fp_ref):
            bad.append((stage, got, (tp_ref, fp_ref)))
    if bad:
        raise SystemExit(f"STOP GATE: chb03 reproduction failed: {bad}")
    print(f"GATE OK: chb03 reproduces the frozen balanced point exactly -- "
          f"detector {out['detector']['tp']}/{out['detector']['fp']}, "
          f"localized {out['localized']['tp']}/{out['localized']['fp']} "
          f"(k={GATE_K}, floor={FLOOR}, cap={CAP})")


# ------------------------------------------------------------------------------------- per-fold
def fold_manifest(fold):
    return json.loads((OUT / "fold_manifests.json").read_text())[str(fold)]


def calibrate_fold_k(fold, ckpt_dir, seed=42):
    """k such that median q_i(k) = 0.005 over the fold's OWN training cases, label-free -- exactly
    p3_levers.calibrate() / v9_e1b_calibrate.calibrate()'s construction, on this fold's D."""
    man = fold_manifest(fold)
    ck, meta = load_fold_ckpt(ckpt_dir, fold, seed)
    t0 = time.time()
    sms = []
    for s in man["train_cases"]:
        ctx = case_ctx(s)
        D = dump_D(ctx, ck, meta, cache_key=f"fold{fold}_seed{seed}/{s}")
        m = V9E1.member_mean_z_from_D(ctx, D)
        sms.append(PS.smoothed(ctx, m, SMOOTH))
        print(f"  {s}: dumped + smoothed ({time.time()-t0:.0f}s)", flush=True)
    k = P3L.calibrate(sms)
    (OUT / f"fold{fold}_seed{seed}_calibration.json").write_text(
        json.dumps(dict(fold=fold, seed=seed, k=k, floor=FLOOR, cap=CAP, smooth=SMOOTH,
                         train_cases=man["train_cases"], elapsed_s=round(time.time() - t0)), indent=1))
    print(f"fold {fold} seed {seed}: k = {k:.6f} (median q_i = 0.005 over "
          f"{len(man['train_cases'])} training cases), {time.time()-t0:.0f}s", flush=True)
    return k


def score_fold(fold, ckpt_dir, seed=42):
    man = fold_manifest(fold)
    ck, meta = load_fold_ckpt(ckpt_dir, fold, seed)
    kfile = OUT / f"fold{fold}_seed{seed}_calibration.json"
    if not kfile.exists():
        raise SystemExit(f"run --calibrate --fold {fold} first ({kfile} missing)")
    k = json.loads(kfile.read_text())["k"]
    rows, errs, dur_rows = [], [], []
    t0 = time.time()
    for s in man["held_out_cases"]:
        ctx = case_ctx(s)
        D = dump_D(ctx, ck, meta, cache_key=f"fold{fold}_seed{seed}/{s}")
        x = V9E1.final_scalar_from_D(ctx, D)
        m = V9E1.member_mean_z_from_D(ctx, D)
        out, ev, bins = evaluate_full(ctx, x, m, k)
        for stage, v in out.items():
            rows.append(dict(fold=fold, seed=seed, subject=s, stage=stage, **v))
        errs += [dict(fold=fold, seed=seed, subject=s, **e) for e in ev]
        for (lo, hi), (caught, n) in bins.items():
            dur_rows.append(dict(fold=fold, seed=seed, subject=s, lo=lo, hi=hi, caught=caught, n=n))
        print(f"  {s}: scored (detector tp={out['detector']['tp']} fp={out['detector']['fp']}, "
              f"localized tp={out['localized']['tp']} fp={out['localized']['fp']}) "
              f"({time.time()-t0:.0f}s)", flush=True)
    R = pd.DataFrame(rows)
    R.to_csv(OUT / f"fold{fold}_seed{seed}_per_subject.csv", index=False)
    pd.DataFrame(errs).to_csv(OUT / f"fold{fold}_seed{seed}_errors.csv", index=False)
    pd.DataFrame(dur_rows).to_csv(OUT / f"fold{fold}_seed{seed}_duration_bins.csv", index=False)
    print(f"wrote {OUT / f'fold{fold}_seed{seed}_per_subject.csv'} (+ errors.csv, duration_bins.csv)")
    return R


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gate", action="store_true")
    ap.add_argument("--calibrate", action="store_true")
    ap.add_argument("--score", action="store_true")
    ap.add_argument("--fold", type=int, choices=[1, 2, 3, 4])
    ap.add_argument("--ckpt_dir")
    ap.add_argument("--seed", type=int, default=42)
    a = ap.parse_args()
    gate_chb03()
    if a.calibrate:
        if not (a.fold and a.ckpt_dir):
            raise SystemExit("--calibrate needs --fold and --ckpt_dir")
        calibrate_fold_k(a.fold, a.ckpt_dir, a.seed)
    if a.score:
        if not (a.fold and a.ckpt_dir):
            raise SystemExit("--score needs --fold and --ckpt_dir")
        score_fold(a.fold, a.ckpt_dir, a.seed)


if __name__ == "__main__":
    main()
