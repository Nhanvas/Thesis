#!/usr/bin/env python
"""
e9_test_oneshot.py -- ONE-SHOT TEST of the configuration frozen by E8 (2026-10-06):
  GAE v2 'clean', score V2_LW (robust-z recon + robust-z LedoitWolf latent + robust-z gamma,
  equal weights, every statistic fitted per patient on its own non-signal-loss windows),
  detector D1: per-file moving average of 15 windows (60 s), threshold = patient's own
  98th percentile (top 2 %), events merged within 90 s, SzCORE scoring.
Nothing here is selected on the test patients. Reported alongside, on the same windows and with
the same detector cell: the locked v1 GAE (V1). Headline model = seed 42; the other 'clean'
seeds give the spread (seed 1 now, seeds 2 and 3 when trained; re-run 'score' then 'eval').
Characterisation only (not selection): sensitivity/FA curve over the top-p grid at smooth 15.
Only 'clean' checkpoints are scored on test; the 'all' variant is never looked at here.

  python src/e9_test_oneshot.py score --subjects chb03 chb06 ...   (resumable per checkpoint)
  python src/e9_test_oneshot.py eval
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

TEST = ["chb03", "chb06", "chb13", "chb14", "chb15", "chb16", "chb17", "chb18"]
DATA = ROOT / "data" / "testset_v2"
CKD = ROOT / "data" / "models_v2"
V1_CKPT = ROOT / "data" / "models_retrain" / "gae_joint_seed42.pt"
OUT = ROOT / "results" / "e9_test_oneshot"
WIN, CHUNK = 4, 1024
SMOOTH, TOP, MERGE_S = 15, 0.02, 90
TOPS = [0.05, 0.02, 0.01, 0.005, 0.002, 0.001]


def load_inputs(subj):
    z = np.load(DATA / f"{subj}.npz", allow_pickle=True)
    ok = ~z["is_signal_loss"].astype(bool)
    idx = np.flatnonzero(ok)
    adj = z["adj"][idx].astype(np.float32)
    bad = ~np.isfinite(adj).all(axis=(1, 2)); adj[bad] = 0.0
    bp5 = z["bp5"][idx].astype(np.float32); bp5[~np.isfinite(bp5)] = 0.0
    return z, idx, adj, bp5, z["f7"][idx].astype(np.float64), int(bad.sum())


def score_v1(adj, bp5):
    import torch
    import gae_joint as G
    m = G.load_checkpoint(V1_CKPT, "cpu")
    if abs(m.encoder.conv1.bias.abs().max().item() - G.BIAS_FP_CANONICAL) > 0.01:
        raise SystemExit("v1 checkpoint is not the canonical one")
    rec, lat = [], []
    with torch.no_grad():
        for s in range(0, len(adj), CHUNK):
            e = min(s + CHUNK, len(adj))
            pg, A, Xn, B = G.build_batch(torch.tensor(adj[s:e]), torch.tensor(bp5[s:e]), "cpu")
            zz = m.encoder(pg.x, pg.edge_index, pg.edge_attr).view(B, G.N_CH, G.LATENT_DIM)
            lat.append(zz.mean(dim=1).numpy()); rec.append(G.joint_score(m, pg, A, Xn, B).numpy())
    return np.concatenate(rec), np.vstack(lat)


def score_v2(ck, adj, bp5, f7):
    import torch
    from torch_geometric.data import Data, Batch
    from torch_geometric.utils import dense_to_sparse
    import gae_joint as G
    meta = json.loads(ck.with_suffix(".json").read_text())
    assert meta["variant"] == "clean", "only the frozen 'clean' variant is scored on test"
    mu, sd, clip, ox = np.array(meta["add_mean"]), np.array(meta["add_std"]), meta["clip"], meta["out_x"]
    fa = ((np.clip((f7 - mu) / sd, -clip, clip) + clip) / (2 * clip)).astype(np.float32)
    xn = (bp5 - bp5.min(axis=1, keepdims=True)) / (bp5.max(axis=1, keepdims=True)
                                                  - bp5.min(axis=1, keepdims=True) + 1e-8)
    model = G.GAEModel(in_dim=meta["in_dim"], bands=ox)
    model.load_state_dict(torch.load(str(ck), map_location="cpu"), strict=True); model.eval()
    rec, lat = [], []
    with torch.no_grad():
        for s in range(0, len(adj), CHUNK):
            e = min(s + CHUNK, len(adj)); dl = []
            for i in range(s, e):
                A = torch.tensor(adj[i]); An = A / (A.amax() + 1e-8)
                xt = torch.cat([torch.tensor(xn[i].astype(np.float32)), torch.tensor(fa[i])], dim=1)
                ei, ew = dense_to_sparse(A)
                dl.append(Data(x=torch.cat([An, xt], dim=1), edge_index=ei, edge_attr=ew, A=A, Xt=xt))
            b = Batch.from_data_list(dl); B = b.num_graphs
            zz = model.encoder(b.x, b.edge_index, b.edge_attr); zp = zz.view(B, G.N_CH, G.LATENT_DIM)
            Ah = torch.clamp(torch.bmm(zp, zp.transpose(1, 2)), 0.0, 1.0)
            Xh = model.x_decoder(zz).view(B, G.N_CH, ox)
            sc = (((b.A.view(B, G.N_CH, G.N_CH) - Ah) ** 2).mean(dim=(1, 2))
                  + G.LAMBDA * ((b.Xt.view(B, G.N_CH, ox) - Xh) ** 2).mean(dim=(1, 2)))
            rec.append(sc.numpy()); lat.append(zp.mean(dim=1).numpy())
    return np.concatenate(rec), np.vstack(lat)


def cmd_score(subjects):
    (OUT / "scores").mkdir(parents=True, exist_ok=True)
    cks = sorted(CKD.glob("gae_v2_clean_seed*.pt"))
    cks = [c for c in cks if "SMOKE" not in c.name]
    print("clean checkpoints:", [c.name for c in cks])
    for s in subjects:
        t0 = time.time()
        z, idx, adj, bp5, f7, nbad = load_inputs(s)
        f = OUT / "scores" / f"{s}__v1.npz"
        if not f.exists():
            r, l = score_v1(adj, bp5); np.savez(f, idx=idx, recon=r, lat=l, n_nonfinite_adj=nbad)
        for ck in cks:
            tag = ck.stem.replace("gae_v2_", "")
            f = OUT / "scores" / f"{s}__{tag}.npz"
            if f.exists():
                continue
            r, l = score_v2(ck, adj, bp5, f7); np.savez(f, idx=idx, recon=r, lat=l)
        print(f"{s}: scored ({time.time()-t0:.0f}s)", flush=True)


def runs(mask):
    out, i, n = [], 0, len(mask)
    while i < n:
        if mask[i]:
            j = i
            while j < n and mask[j]:
                j += 1
            out.append((i, j)); i = j
        else:
            i += 1
    return out


def detect_and_score(z, score, top, smooth=SMOOTH):
    import szcore_eval as SE
    ok = ~z["is_signal_loss"].astype(bool); ict = z["is_ictal"].astype(bool); fidx = z["file_idx"].astype(int)
    sm = np.full(len(score), np.nan)
    for f in np.unique(fidx):
        m = fidx == f
        sm[m] = pd.Series(np.where(ok[m], score[m], np.nan)).rolling(smooth, min_periods=1, center=True).mean().values
    thr = np.nanquantile(sm[ok], 1 - top)
    ref_all, hyp_all, off, short = [], [], 0, []
    for f in np.unique(fidx):
        m = np.flatnonzero(fidx == f)
        above = np.nan_to_num(sm[m], nan=-np.inf) > thr
        ev = []
        for a, b in runs(above):
            a_s, b_s = a * WIN, b * WIN
            if ev and a_s - ev[-1][1] <= MERGE_S:
                ev[-1] = (ev[-1][0], b_s)
            else:
                ev.append((a_s, b_s))
        ref = [(a * WIN, b * WIN) for a, b in runs(ict[m])]
        for a, b in ref:
            if b - a < 20:
                short.append(any(hb >= a - 30 and ha <= b + 60 for ha, hb in ev))
        ref_all += [(a + off, b + off) for a, b in ref]; hyp_all += [(a + off, b + off) for a, b in ev]
        off += len(m) * WIN + 600
    nonict_h = float((~ict & ok).sum()) * WIN / 3600
    r = SE.score_szcore(ref_all, hyp_all, off, nonict_h)
    r = {k: (float(v) if np.isscalar(v) else v) for k, v in r.items()}
    r.update(n_hyp=len(hyp_all), nonict_h=nonict_h, n_short=len(short), tp_short=int(sum(short)))
    return r


def cmd_eval():
    from sklearn.covariance import LedoitWolf
    from sklearn.metrics import roc_auc_score
    import ensemble_recipe as ER

    def rz(x, ok):
        m = np.median(x[ok]); s = np.median(np.abs(x[ok] - m)) + 1e-9; return (x - m) / s

    tags = sorted({p.stem.split("__")[1] for p in (OUT / "scores").glob("*__clean_seed*.npz")})
    rows, curve = [], []
    for s in TEST:
        z = np.load(DATA / f"{s}.npz", allow_pickle=True)
        n = len(z["is_ictal"]); ok = ~z["is_signal_loss"].astype(bool); ict = z["is_ictal"].astype(bool)
        buf = z["is_buffer"].astype(bool)
        v1 = np.load(OUT / "scores" / f"{s}__v1.npz"); idx = v1["idx"]

        def full(v):
            o = np.full(n, np.nan); o[idx] = v; o[~ok] = np.nanmedian(v); return o
        zg = rz(full(z["zgamma_raw"][idx].astype(float)), ok)

        def ens(rec, lat):
            l = rz(full(LedoitWolf().fit(lat).mahalanobis(lat)), ok)
            return np.asarray(ER.build_ensemble_subset({"zrecon": rz(full(rec), ok), "zlatent": l, "zgamma": zg},
                                                       ER.CANDIDATES["rlg"]), float)
        models = {"V1": ens(v1["recon"], v1["lat"])}
        for t in tags:
            q = np.load(OUT / "scores" / f"{s}__{t}.npz"); models[t] = ens(q["recon"], q["lat"])
        win_mask = ok & ~buf
        for name, sc in models.items():
            r = detect_and_score(z, sc, TOP)
            auc = roc_auc_score(ict[win_mask], sc[win_mask]) if ict[win_mask].any() else np.nan
            rows.append(dict(subject=s, model=name, window_auroc=auc, **r))
            for p in TOPS:
                c = detect_and_score(z, sc, p)
                curve.append(dict(subject=s, model=name, top=p, tp=c["tp"], fp=c["fp"], n_ref=c["n_ref"],
                                  nonict_h=c["nonict_h"]))
        print(f"{s}: done", flush=True)

    df = pd.DataFrame(rows); df.to_csv(OUT / "per_subject.csv", index=False)
    cv = pd.DataFrame(curve); cv.to_csv(OUT / "curve_per_subject.csv", index=False)

    def pooled(g):
        tp, fp, nr, h, nh = g.tp.sum(), g.fp.sum(), g.n_ref.sum(), g.nonict_h.sum(), g.n_hyp.sum()
        sens = tp / nr; prec = (nh - fp) / nh if nh else np.nan
        return pd.Series(dict(tp=tp, n_ref=nr, fp=fp, sens=sens, precision=prec,
                              f1=2 * sens * prec / (sens + prec) if (sens + prec) else 0.0,
                              fa_day=fp / h * 24, window_auroc_macro=g.window_auroc.mean(),
                              short_tp=g.tp_short.sum(), short_n=g.n_short.sum(), nonict_h=h))
    P = df.groupby("model").apply(pooled)
    seeds = P.loc[[t for t in tags]]
    lines = ["# E9 -- ONE-SHOT TEST of the E8-frozen configuration (8 test patients)\n",
             f"Frozen: GAE v2 clean, V2_LW, D1 smooth {SMOOTH} windows, top {TOP:.0%}, merge {MERGE_S} s, SzCORE.",
             f"FA denominator = non-ictal recorded hours of the processed files ({P.nonict_h.iloc[0]:.1f} h).",
             "Precision (approx.) = (hypothesised events - SzCORE false positives) / hypothesised events.\n",
             "## Pooled\n", "```", P.drop(columns="nonict_h").round(4).to_string(), "```",
             f"\nHeadline (seed 42): see row clean_seed42. Spread over {len(tags)} clean seed(s): "
             f"sens {seeds.sens.mean():.3f} +- {seeds.sens.std(ddof=1) if len(tags) > 1 else float('nan'):.3f}, "
             f"FA/day {seeds.fa_day.mean():.1f} +- {seeds.fa_day.std(ddof=1) if len(tags) > 1 else float('nan'):.1f}, "
             f"F1 {seeds.f1.mean():.3f}",
             "\n## Per patient (frozen cell)\n", "```",
             df[["subject", "model", "tp", "n_ref", "fp", "window_auroc", "tp_short", "n_short"]]
             .assign(fa_day=(df.fp / df.nonict_h * 24).round(1)).round(4).to_string(index=False), "```"]
    C = cv.groupby(["model", "top"])[["tp", "fp", "n_ref", "nonict_h"]].sum().reset_index()
    C["sens"] = C.tp / C.n_ref; C["fa_day"] = C.fp / C.nonict_h * 24
    lines += ["\n## Characterisation (not selection): smooth 15, top-p grid\n", "```",
              C[["model", "top", "tp", "n_ref", "fp", "sens", "fa_day"]].round(3).to_string(index=False), "```"]
    (OUT / "SUMMARY.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s1 = sub.add_parser("score"); s1.add_argument("--subjects", nargs="+", default=TEST)
    sub.add_parser("eval")
    a = ap.parse_args()
    if a.cmd == "score":
        bad = set(a.subjects) - set(TEST)
        if bad:
            raise SystemExit(f"test subjects only: {sorted(bad)}")
        cmd_score(a.subjects)
    else:
        cmd_eval()
