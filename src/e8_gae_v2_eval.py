#!/usr/bin/env python
"""
e8_gae_v2_eval.py -- decide option C on the FULL recordings of the 15 non-test subjects
(data/trainset_v2, every file except those missing a common channel), with the rules fixed
on 2026-10-06 BEFORE any v2 model existed.

Stage 1 (score; CPU; resumable; can run in parallel by --subjects):
  for every window: readouts of the locked v1 GAE and of every v2 checkpoint found in --ckpt_dir
  -> results/e8_gae_v2/scores/{subj}.npz
Stage 2 (eval):
  scores, all fitted per patient on that patient's own non-signal-loss windows (no label):
    V1      locked rlg: robust-z(recon), robust-z(LedoitWolf Mahalanobis of mean latent),
            robust-z(gamma), equal weights                      (= G0 of E6/E7)
    V2_LW   same three readouts from a v2 model
    V2_GMM  v2 recon + v2 latent readout = GaussianMixture(k=8) NLL on [mean, std] of node
            latents (32-d, robust-standardised) + gamma, equal weights
  detector D1 (= E1 grid): per-file moving average 1/3/5/15 windows, threshold = patient's own
  (1 - p) quantile, p in {5, 2, 1, 0.5, 0.2, 0.1} %, merge 90 s, SzCORE.
  Seeds of one variant are combined cell by cell (mean sensitivity, mean FA/day).
RULES (fixed before training):
  V   variant: 'all' is chosen only if its best pooled sensitivity at FA/day <= 25 is higher
      than 'clean' (best over its two scores) AND its validation-only value is not lower.
  C   option C is adopted if the chosen variant's best score reaches
      best(V1) + 0.10 at FA/day <= 25 on the 15 subjects AND its validation-only value
      (chb10, chb11, chb22) is not below V1's validation-only value.
  The adopted (variant, score, smooth, top) is printed as FROZEN for the one-shot test.
TEST GUARD: refuses every test subject.

  python src/e8_gae_v2_eval.py score --subjects chb04 chb08 ...     (stage 1)
  python src/e8_gae_v2_eval.py eval                                   (stage 2)
"""
import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT / "src", ROOT / "src" / "dataprep", ROOT / "src" / "retrain",
          ROOT / "src" / "phaseB", ROOT / "src" / "phaseC"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

SUBJS = ["chb01", "chb02", "chb04", "chb05", "chb07", "chb08", "chb09", "chb12",
         "chb19", "chb20", "chb21", "chb23", "chb10", "chb11", "chb22"]
VAL = ["chb10", "chb11", "chb22"]
TEST = {"chb03", "chb06", "chb13", "chb14", "chb15", "chb16", "chb17", "chb18"}
assert not (set(SUBJS) & TEST), "TEST GUARD"
DATA = ROOT / "data" / "trainset_v2"
V1_CKPT = ROOT / "data" / "models_retrain" / "gae_joint_seed42.pt"
OUT = ROOT / "results" / "e8_gae_v2"
WIN = 4
FIT_MAX = 20000
CHUNK = 1024


# ----------------------------------------------------------------------------- stage 1
def score_subject(subj, ckpt_dir):
    import torch
    from torch_geometric.data import Data, Batch
    from torch_geometric.utils import dense_to_sparse
    import gae_joint as G
    if subj in TEST:
        raise SystemExit(f"TEST GUARD: {subj}")
    out = OUT / "scores" / f"{subj}.npz"
    if out.exists():
        print(f"{subj}: exists, skip"); return
    t0 = time.time()
    z = np.load(DATA / f"{subj}.npz", allow_pickle=True)
    ok = ~z["is_signal_loss"]
    idx = np.flatnonzero(ok)
    adj = z["adj"][idx].astype(np.float32)
    bad = ~np.isfinite(adj).all(axis=(1, 2))
    adj[bad] = 0.0
    bp5 = z["bp5"][idx].astype(np.float32)
    bp5[~np.isfinite(bp5)] = 0.0
    f7 = z["f7"][idx].astype(np.float64)
    res = {"idx": idx, "n_nonfinite_adj": int(bad.sum())}

    # v1 (locked) -- hash-identified by the bias fingerprint
    m1 = G.load_checkpoint(V1_CKPT, "cpu")
    bfp = m1.encoder.conv1.bias.abs().max().item()
    if abs(bfp - G.BIAS_FP_CANONICAL) > 0.01:
        raise SystemExit(f"v1 checkpoint fingerprint {bfp:.4f} is not canonical {G.BIAS_FP_CANONICAL}")
    rec, lat = [], []
    with torch.no_grad():
        for s in range(0, len(idx), CHUNK):
            e = min(s + CHUNK, len(idx))
            pg, A, Xn, B = G.build_batch(torch.tensor(adj[s:e]), torch.tensor(bp5[s:e]), "cpu")
            zz = m1.encoder(pg.x, pg.edge_index, pg.edge_attr).view(B, G.N_CH, G.LATENT_DIM)
            lat.append(zz.mean(dim=1).numpy())
            rec.append(G.joint_score(m1, pg, A, Xn, B).numpy())
    res["v1_recon"] = np.concatenate(rec); res["v1_lat"] = np.vstack(lat)

    # v2 checkpoints
    Xn_all = (bp5 - bp5.min(axis=1, keepdims=True)) / (bp5.max(axis=1, keepdims=True)
                                                      - bp5.min(axis=1, keepdims=True) + 1e-8)
    for ck in sorted(Path(ckpt_dir).glob("gae_v2_*_seed*.pt")):
        if "SMOKE" in ck.name:
            continue
        meta = json.loads(ck.with_suffix(".json").read_text())
        mu, sd, clip = np.array(meta["add_mean"]), np.array(meta["add_std"]), meta["clip"]
        fa = ((np.clip((f7 - mu) / sd, -clip, clip) + clip) / (2 * clip)).astype(np.float32)
        model = G.GAEModel(in_dim=meta["in_dim"], bands=meta["out_x"])
        model.load_state_dict(torch.load(str(ck), map_location="cpu"), strict=True)
        model.eval()
        ox = meta["out_x"]
        rec, lmean, lstd = [], [], []
        with torch.no_grad():
            for s in range(0, len(idx), CHUNK):
                e = min(s + CHUNK, len(idx))
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
                sc = ((A_ - Ah) ** 2).mean(dim=(1, 2)) + G.LAMBDA * ((X_ - Xh) ** 2).mean(dim=(1, 2))
                rec.append(sc.numpy()); lmean.append(zp.mean(dim=1).numpy()); lstd.append(zp.std(dim=1).numpy())
        tag = ck.stem.replace("gae_v2_", "")            # e.g. clean_seed42
        res[f"{tag}_recon"] = np.concatenate(rec)
        res[f"{tag}_lat"] = np.vstack(lmean)
        res[f"{tag}_latstd"] = np.vstack(lstd)
        print(f"  {subj}: {tag} scored ({time.time()-t0:.0f}s)", flush=True)
    (OUT / "scores").mkdir(parents=True, exist_ok=True)
    np.savez(out, **res)
    print(f"{subj}: {len(idx)} windows scored, non-finite adj {int(bad.sum())}, {time.time()-t0:.0f}s", flush=True)


# ----------------------------------------------------------------------------- stage 2
def d_for_grid(z):
    """dict in the format e1_normal_definition.event_grid expects."""
    ict = z["is_ictal"].astype(bool)
    dur = np.zeros(len(ict), dtype=np.int32)
    i = 0
    while i < len(ict):                                   # seizure duration per ictal window
        if ict[i]:
            j = i
            while j < len(ict) and ict[j] and z["file_idx"][j] == z["file_idx"][i]:
                j += 1
            dur[i:j] = (j - i) * WIN; i = j
        else:
            i += 1
    fidx = z["file_idx"].astype(int)
    win = np.zeros(len(ict), dtype=np.int64)
    for f in np.unique(fidx):
        m = fidx == f; win[m] = np.arange(m.sum())
    return dict(is_ictal=ict, is_signal_loss=z["is_signal_loss"].astype(bool),
                is_buffer=z["is_buffer"].astype(bool), is_artifact=z["is_flag5sd"].astype(bool),
                sz_dur=dur, file_idx=fidx, win_idx=win)


def evaluate():
    from scipy.stats import rankdata  # noqa: F401
    from sklearn.covariance import LedoitWolf
    from sklearn.mixture import GaussianMixture
    import e1_normal_definition as E1
    import ensemble_recipe as ER
    rng = np.random.default_rng(0)

    def rz(x, ok):
        m = np.median(x[ok]); s = np.median(np.abs(x[ok] - m)) + 1e-9
        return (x - m) / s

    def ens(r, l, g):
        return np.asarray(ER.build_ensemble_subset({"zrecon": r, "zlatent": l, "zgamma": g},
                                                   ER.CANDIDATES["rlg"]), dtype=float)

    rows, per = [], []
    for s in SUBJS:
        z = np.load(DATA / f"{s}.npz", allow_pickle=True)
        sc = np.load(OUT / "scores" / f"{s}.npz")
        d = d_for_grid(z)
        n = len(d["is_ictal"]); ok = ~d["is_signal_loss"]; idx = sc["idx"]

        def full(v):
            o = np.full(n, np.nan); o[idx] = v
            o[~ok] = np.nanmedian(v); return o

        zg = rz(full(z["zgamma_raw"][idx].astype(float)), ok)
        scores = {}
        r1 = rz(full(sc["v1_recon"]), ok)
        lat1 = sc["v1_lat"]
        l1 = rz(full(LedoitWolf().fit(lat1).mahalanobis(lat1)), ok)
        scores["V1"] = ens(r1, l1, zg)
        tags = sorted({k[:-6] for k in sc.files if k.endswith("_recon") and k != "v1_recon"})
        for tag in tags:
            r2 = rz(full(sc[f"{tag}_recon"]), ok)
            lat = sc[f"{tag}_lat"]
            scores[f"{tag}|V2_LW"] = ens(r2, rz(full(LedoitWolf().fit(lat).mahalanobis(lat)), ok), zg)
            V = np.hstack([lat, sc[f"{tag}_latstd"]])
            c = np.median(V, axis=0); q = np.subtract(*np.percentile(V, [75, 25], axis=0)); q[q < 1e-9] = 1
            V = np.clip((V - c) / q, -10, 10)
            fit = rng.choice(len(V), min(FIT_MAX, len(V)), replace=False)
            gm = GaussianMixture(8, covariance_type="full", reg_covar=1e-3, max_iter=300,
                                 random_state=0).fit(V[fit])
            scores[f"{tag}|V2_GMM"] = ens(r2, rz(full(-gm.score_samples(V)), ok), zg)
        ict = d["is_ictal"] & ok
        base = ~d["is_ictal"] & ~d["is_buffer"] & ok
        flag, bg = base & d["is_artifact"], base & ~d["is_artifact"]
        nh = float((~d["is_ictal"] & ok).sum()) * WIN / 3600
        row = dict(subject=s, n_seizure_windows=int(ict.sum()))
        for name, v in scores.items():
            row[f"{name}|sz_flag"] = E1.auc(v, ict, flag); row[f"{name}|sz_bg"] = E1.auc(v, ict, bg)
            for r in E1.event_grid(d, v):
                r.update(subject=s, score=name, nonict_h=nh); rows.append(r)
        per.append(row)
        print(f"{s}: " + " ".join(f"{k}={row[k + '|sz_flag']:.3f}" for k in scores), flush=True)

    gr = pd.DataFrame(rows)
    gr.to_csv(OUT / "grid_per_subject.csv", index=False)
    pd.DataFrame(per).to_csv(OUT / "per_subject_auroc.csv", index=False)

    def pooled(df):
        p = df.groupby(["score", "smooth", "top"])[["tp", "fp", "n_ref", "nonict_h", "tp_short",
                                                    "n_ref_short"]].sum().reset_index()
        p["sens"] = p.tp / p.n_ref; p["fa_day"] = p.fp / p.nonict_h * 24
        p["variant"] = p.score.map(lambda x: "V1" if x == "V1" else x.split("_seed")[0])
        p["kind"] = p.score.map(lambda x: "V1" if x == "V1" else x.split("|")[1])
        p["seed"] = p.score.map(lambda x: None if x == "V1" else x.split("seed")[1].split("|")[0])
        return p

    P_all, P_val = pooled(gr), pooled(gr[gr.subject.isin(VAL)])
    P_all.to_csv(OUT / "grid_pooled_by_seed.csv", index=False)

    def seed_mean(p):
        return (p.groupby(["variant", "kind", "smooth", "top"])
                  .agg(sens=("sens", "mean"), sens_sd=("sens", "std"), fa_day=("fa_day", "mean"),
                       n_seeds=("sens", "size"), sens_short=("tp_short", "sum"))
                  .reset_index())

    M_all, M_val = seed_mean(P_all), seed_mean(P_val)
    M_all.to_csv(OUT / "grid_seed_mean.csv", index=False)

    def best(M, variant, kind=None, cap=25):
        q = M[(M.variant == variant) & (M.fa_day <= cap)]
        if kind:
            q = q[q.kind == kind]
        if not len(q):
            return 0.0, None
        r = q.loc[q.sens.idxmax()]
        return float(r.sens), dict(kind=r.kind, smooth=int(r.smooth), top=float(r.top),
                                   fa_day=round(float(r.fa_day), 2), sens_sd=r.sens_sd, n_seeds=int(r.n_seeds))

    lines = ["# E8 -- GAE v2 (option C) on full recordings, 15 non-test subjects\n"]
    v1, c1 = best(M_all, "V1"); v1v, _ = best(M_val, "V1")
    lines.append(f"V1 (locked): best sens FA/day<=25 = {v1:.3f} {c1}; validation-only {v1v:.3f}")
    res = {}
    for var in ("clean", "all"):
        if var not in set(M_all.variant):
            lines.append(f"{var}: no checkpoint found"); continue
        b, c = best(M_all, var); bv, cv = best(M_val, var)
        res[var] = (b, c, bv)
        for kind in ("V2_LW", "V2_GMM"):
            bk, ck = best(M_all, var, kind)
            lines.append(f"  {var} {kind}: {bk:.3f} {ck}  (FA/day<=15: {best(M_all, var, kind, 15)[0]:.3f})")
        lines.append(f"{var}: best {b:.3f} {c}; validation-only {bv:.3f}")
    if "all" in res and "clean" in res:
        chosen = "all" if (res["all"][0] > res["clean"][0] and res["all"][2] >= res["clean"][2]) else "clean"
    else:
        chosen = next(iter(res), None)
    if chosen:
        b, c, bv = res[chosen]
        passed = b >= v1 + 0.10 and bv >= v1v
        lines += [f"\n- Rule V: chosen variant = {chosen}",
                  f"- Rule C: {b:.3f} vs V1 {v1:.3f} + 0.10; validation-only {bv:.3f} vs {v1v:.3f} -> "
                  f"{'ADOPTED' if passed else 'NOT adopted'}",
                  f"\n**FROZEN for the one-shot test: "
                  + (f"GAE v2 {chosen}, score {c['kind']}, smooth {c['smooth']}, top {c['top']}**"
                     if passed else f"locked V1 with D1, smooth {c1['smooth']}, top {c1['top']}**")]
    lines += ["\nShort seizures (< 20 s) in this set: n_ref_short = "
              f"{int(P_all[P_all.score == 'V1'].n_ref_short.max())}"]
    (OUT / "SUMMARY.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s1 = sub.add_parser("score")
    s1.add_argument("--subjects", nargs="+", default=SUBJS)
    s1.add_argument("--ckpt_dir", default=str(ROOT / "data" / "models_v2"))
    sub.add_parser("eval")
    a = ap.parse_args()
    if a.cmd == "score":
        bad = set(a.subjects) - set(SUBJS)
        if bad:
            raise SystemExit(f"not allowed: {sorted(bad)}")
        for s in a.subjects:
            score_subject(s, a.ckpt_dir)
    else:
        evaluate()


if __name__ == "__main__":
    main()
