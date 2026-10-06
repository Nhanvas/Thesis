#!/usr/bin/env python
"""
e14_spatial_recruitment.py -- stage P2, step 4 (decided by E13 rule B). 15 non-test subjects.

Mechanism. E11-E13: the best readout (v2 latent, graph-mean node latent, per-patient LedoitWolf) still
has a top-2 % non-ictal tail that is 84-88 % flagged high-amplitude windows of the patient (E12: 0.87);
training the reconstruction objective on artifacts does not help (E13, delta -0.007). A rarity score
cannot tell a rare artifact from a rare seizure. A label-free physiological prior can: a seizure
recruits a large part of the montage, while most high-amplitude artifacts are focal (eye: frontal-polar
pair; muscle: temporal chain; electrode pop: one electrode). Graph-MEAN pooling lets one or two extreme
channels dominate the window score. DynaSD (SzCORE benchmark, unsupervised) requires >= 9 of 18
channels; the raw-EEG view found spatial spread among the separators of seizure vs flagged windows.
Hypothesis: a window score that requires at least half of the 18 channels to be anomalous in the GAE
latent space ranks seizures above the patient's own high-amplitude windows better than the graph mean.

PRIMARY readout S (one, fixed now, k from DynaSD, not tuned):
  per patient p and channel c: d_c = LedoitWolf Mahalanobis of the v2 node latent Z_c (16-d), fitted on
  all non-signal-loss windows of p (label-free, whole recording, as the latent readout of E8);
  z_c = per-patient per-channel robust-z of d_c;  S = the 9th largest of the 18 z_c ("at least half
  of the montage"), then robust-z per patient.
Detector and selection procedure IDENTICAL to E8/E12 (e1_normal_definition.event_grid, seed mean,
best cell at FA/day <= 25). Seeds: v2 clean 42 and 1.
REPRODUCTION GATE (dump stage): the mean over channels of the dumped Z must equal the E8 cached
{tag}_lat within 1e-4 on every subject, else STOP (the dump is not the E8 model).
ADOPTION GATE (vs the adopted system E = E8 V2_LW; all three):
  G1 best seed-mean pooled sensitivity of S at FA/day <= 25 >= 0.489 + 0.10
  G2 validation-only value of S >= 0.733
  G3 per subject seed-mean TP of S at its cell >= E at the frozen cell in >= 9 of 15
Mechanism check (required to read a pass as a pass): flagged share in the top-2 % non-ictal tail
falls below L's (E12: 0.87).
Characterisation only (never used to choose): k = 1 (max), 3, 6, 12, the channel mean, and L.
Official SzCORE aggregation (mean over subjects) is printed beside the pooled values.
TEST GUARD: E8.SUBJS only.
Run:
  python src/e14_spatial_recruitment.py dump --smoke      (chb01, first 2,048 windows, ~1 min)
  python src/e14_spatial_recruitment.py dump              (estimated 30-90 min CPU, not measured)
  python src/e14_spatial_recruitment.py eval              (estimated 15-45 min CPU, not measured)
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
for p in (ROOT / "src", ROOT / "src" / "dataprep", ROOT / "src" / "retrain",
          ROOT / "src" / "phaseB", ROOT / "src" / "phaseC"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
import e8_gae_v2_eval as E8            # noqa: E402

TEST = {"chb03", "chb06", "chb13", "chb14", "chb15", "chb16", "chb17", "chb18"}
OUT = ROOT / "results" / "e14_spatial_recruitment"
DUMP = OUT / "pernode"
TAGS = ["clean_seed42", "clean_seed1"]
CKPT = ROOT / "data" / "models_v2"
K_PRIMARY = 9
K_CHAR = [1, 3, 6, 12]
FROZEN = (15, 0.02)


def guard(subs):
    if set(subs) & TEST or not set(subs) <= set(E8.SUBJS):
        raise SystemExit("TEST GUARD")


# ----------------------------------------------------------------------------- dump
def dump_subject(subj, smoke=False):
    import torch
    from torch_geometric.data import Data, Batch
    from torch_geometric.utils import dense_to_sparse
    import gae_joint as G
    out = DUMP / f"{subj}{'_SMOKE' if smoke else ''}.npz"
    if out.exists() and not smoke:
        print(f"{subj}: exists, skip"); return
    t0 = time.time()
    z = np.load(E8.DATA / f"{subj}.npz", allow_pickle=True)
    cache = np.load(E8.OUT / "scores" / f"{subj}.npz")
    idx = cache["idx"]
    if not np.array_equal(idx, np.flatnonzero(~z["is_signal_loss"])):
        raise SystemExit(f"{subj}: window index differs from the E8 cache")
    if smoke:
        idx = idx[:2048]
    adj = z["adj"][idx].astype(np.float32); adj[~np.isfinite(adj).all(axis=(1, 2))] = 0.0
    bp5 = z["bp5"][idx].astype(np.float32); bp5[~np.isfinite(bp5)] = 0.0
    f7 = z["f7"][idx].astype(np.float64)
    Xn_all = (bp5 - bp5.min(axis=1, keepdims=True)) / (bp5.max(axis=1, keepdims=True)
                                                      - bp5.min(axis=1, keepdims=True) + 1e-8)
    res = {"idx": idx}
    for tag in TAGS:
        ck = CKPT / f"gae_v2_{tag}.pt"
        meta = json.loads(ck.with_suffix(".json").read_text())
        mu, sd, clip = np.array(meta["add_mean"]), np.array(meta["add_std"]), meta["clip"]
        fa = ((np.clip((f7 - mu) / sd, -clip, clip) + clip) / (2 * clip)).astype(np.float32)
        model = G.GAEModel(in_dim=meta["in_dim"], bands=meta["out_x"])
        model.load_state_dict(torch.load(str(ck), map_location="cpu"), strict=True)
        model.eval()
        ox = meta["out_x"]
        Z = np.empty((len(idx), G.N_CH, G.LATENT_DIM), np.float32)
        ex = np.empty((len(idx), G.N_CH), np.float32)
        ea = np.empty((len(idx), G.N_CH), np.float32)
        with torch.no_grad():
            for s in range(0, len(idx), E8.CHUNK):
                e = min(s + E8.CHUNK, len(idx))
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
                Z[s:e] = zp.numpy()
                ea[s:e] = ((A_ - Ah) ** 2).mean(dim=2).numpy()
                ex[s:e] = ((X_ - Xh) ** 2).mean(dim=2).numpy()
        # reproduction gate against the E8 cache
        ref = cache[f"{tag}_lat"][:len(idx)]
        err = float(np.abs(Z.mean(axis=1) - ref).max())
        if err > 1e-4:
            raise SystemExit(f"STOP {subj} {tag}: mean latent differs from E8 cache by {err:.2e}")
        D = np.empty((len(idx), G.N_CH), np.float32)
        for c in range(G.N_CH):
            Zc = Z[:, c, :].astype(np.float64)
            D[:, c] = LedoitWolf().fit(Zc).mahalanobis(Zc)
        res[f"{tag}_d"] = D; res[f"{tag}_ex"] = ex; res[f"{tag}_ea"] = ea
        print(f"  {subj} {tag}: dumped, reproduction max err {err:.1e} ({time.time()-t0:.0f}s)", flush=True)
    DUMP.mkdir(parents=True, exist_ok=True)
    np.savez(out, **res)
    print(f"{subj}: {len(idx)} windows, {time.time()-t0:.0f}s", flush=True)


# ----------------------------------------------------------------------------- eval
def rz(x, ok):
    m = np.median(x[ok]); s = np.median(np.abs(x[ok] - m)) + 1e-9
    return (x - m) / s


def evaluate():
    import e1_normal_definition as E1
    import ensemble_recipe as ER
    import e11_tail_anatomy as E11
    t0 = time.time()
    rows, mech = [], []
    for s in E8.SUBJS:
        z = np.load(E8.DATA / f"{s}.npz", allow_pickle=True)
        c = np.load(E8.OUT / "scores" / f"{s}.npz")
        pn = np.load(DUMP / f"{s}.npz")
        d = E8.d_for_grid(z)
        n = len(d["is_ictal"]); ok = ~d["is_signal_loss"]; idx = c["idx"]
        if not np.array_equal(idx, pn["idx"]):
            raise SystemExit(f"{s}: dump index differs from the E8 cache")
        fidx = z["file_idx"].astype(int)
        nonict = ~z["is_ictal"].astype(bool) & ~z["is_buffer"].astype(bool) & ok
        fl5 = z["is_flag5sd"].astype(bool)

        def full(v):
            o = np.full(n, np.nan); o[idx] = v; o[~ok] = np.nanmedian(v); return o

        g = rz(full(z["zgamma_raw"][idx].astype(float)), ok)
        nh = float((~d["is_ictal"] & ok).sum()) * E8.WIN / 3600
        scores = {}
        for tag in TAGS:
            r = rz(full(c[f"{tag}_recon"]), ok)
            lat = c[f"{tag}_lat"]
            l = rz(full(LedoitWolf().fit(lat).mahalanobis(lat)), ok)
            scores[f"{tag}|E"] = np.asarray(ER.build_ensemble_subset(
                {"zrecon": r, "zlatent": l, "zgamma": g}, ER.CANDIDATES["rlg"]), float)
            scores[f"{tag}|L"] = l
            D = pn[f"{tag}_d"].astype(np.float64)
            okk = np.ones(len(D), bool)
            Zc = np.column_stack([rz(D[:, j], okk) for j in range(D.shape[1])])
            Zs = -np.sort(-Zc, axis=1)                      # descending per window
            for k in [K_PRIMARY] + K_CHAR:
                scores[f"{tag}|S{k}"] = rz(full(Zs[:, k - 1]), ok)
            scores[f"{tag}|Smean"] = rz(full(Zc.mean(axis=1)), ok)
        for name, v in scores.items():
            for r_ in E1.event_grid(d, v):
                r_.update(subject=s, score=name, nonict_h=nh); rows.append(r_)
            sm = E11.smooth(v, ok, fidx)
            T = (sm > np.nanquantile(sm[ok], 0.98)) & nonict
            mech.append(dict(subject=s, score=name, tail_flag_share=float(fl5[T].mean()) if T.any() else np.nan,
                             auc_szflag=E11.auc(sm, z["is_ictal"].astype(bool) & ok, nonict & fl5)))
        print(f"{s}: done ({time.time()-t0:.0f}s)", flush=True)

    gr = pd.DataFrame(rows); gr.to_csv(OUT / "grid_per_subject.csv", index=False)
    M = pd.DataFrame(mech); M.to_csv(OUT / "mechanism.csv", index=False)
    gr["kind"] = gr.score.str.split("|").str[1]; gr["seed"] = gr.score.str.split("|").str[0]
    M["kind"] = M.score.str.split("|").str[1]

    def pooled(df):
        p = df.groupby(["kind", "seed", "smooth", "top"])[["tp", "fp", "n_ref", "nonict_h", "tp_short",
                                                           "n_ref_short"]].sum().reset_index()
        p["sens"] = p.tp / p.n_ref; p["fa_day"] = p.fp / p.nonict_h * 24
        return (p.groupby(["kind", "smooth", "top"]).agg(sens=("sens", "mean"), fa_day=("fa_day", "mean"),
                tp_short=("tp_short", "mean"), n_short=("n_ref_short", "max")).reset_index())

    A, V = pooled(gr), pooled(gr[gr.subject.isin(E8.VAL)])
    A.to_csv(OUT / "grid_seed_mean.csv", index=False)

    def best(T, kind, cap=25.0):
        q = T[(T.kind == kind) & (T.fa_day <= cap)]
        if not len(q):
            return 0.0, None
        r = q.loc[q.sens.idxmax()]
        return float(r.sens), (int(r.smooth), float(r.top), round(float(r.fa_day), 2))

    def official(kind, sm, top):
        q = gr[(gr.kind == kind) & (gr.smooth == sm) & (gr.top == top)]
        q = q.groupby(["seed", "subject"])[["tp", "fp", "n_ref", "nonict_h"]].sum().reset_index()
        q["sens"] = q.tp / q.n_ref
        q["prec"] = q.tp / (q.tp + q.fp).where(q.tp + q.fp > 0)
        q["f1"] = 2 * q.tp / (2 * q.tp + q.fp + (q.n_ref - q.tp))
        q["fa_day"] = q.fp / q.nonict_h * 24
        return q.groupby("seed")[["sens", "prec", "f1", "fa_day"]].mean().mean()

    e_cell = A[(A.kind == "E") & (A.smooth == FROZEN[0]) & (A.top == FROZEN[1])]
    lines = ["# E14 -- spatial-recruitment readout (k-th largest per-channel latent anomaly), 15 non-test\n",
             f"Reproduction of E8 frozen cell: E {float(e_cell.sens.iloc[0]):.3f} @ {float(e_cell.fa_day.iloc[0]):.2f}"
             " (E8: 0.489 @ 19.78)\n",
             "## Best cell at FA/day <= 25 | <= 15 | <= 10 | validation-only <= 25 | mechanism (median over subjects)\n",
             "```"]
    kinds = ["E", "L", f"S{K_PRIMARY}"] + [f"S{k}" for k in K_CHAR] + ["Smean"]
    res = {}
    for k in kinds:
        b, cfg = best(A, k); bv, _ = best(V, k); res[k] = (b, cfg, bv)
        mm = M[M.kind == k]
        role = "<- PRIMARY" if k == f"S{K_PRIMARY}" else "(reference)" if k in ("E", "L") else "(characterisation)"
        lines.append(f"{k:6s} {b:.3f} {cfg} | {best(A, k, 15)[0]:.3f} | {best(A, k, 10)[0]:.3f} | val {bv:.3f} | "
                     f"tail flagged {mm.tail_flag_share.median():.2f} AUC sz-flag {mm.auc_szflag.median():.3f}  {role}")
    lines.append("```")
    kp = f"S{K_PRIMARY}"
    bS, cS, bvS = res[kp]
    adopted = False
    if cS is None:
        lines.append(f"{kp} never reaches FA/day <= 25 -> NOT adopted")
    else:
        tpS = gr[(gr.kind == kp) & (gr.smooth == cS[0]) & (gr.top == cS[1])].groupby("subject").tp.mean()
        tpE = gr[(gr.kind == "E") & (gr.smooth == FROZEN[0]) & (gr.top == FROZEN[1])].groupby("subject").tp.mean()
        nref = gr[(gr.kind == "E") & (gr.smooth == FROZEN[0]) & (gr.top == FROZEN[1])].groupby("subject").n_ref.max()
        n_ok = int((tpS >= tpE).sum())
        g1, g2, g3 = bS >= 0.489 + 0.10, bvS >= 0.733, n_ok >= 9
        mS = M[M.kind == kp].tail_flag_share.median()
        adopted = g1 and g2 and g3
        lines += [f"\n- G1 {bS:.3f} vs 0.589 -> {'pass' if g1 else 'FAIL'}",
                  f"- G2 validation-only {bvS:.3f} vs 0.733 -> {'pass' if g2 else 'FAIL'}",
                  f"- G3 subjects TP({kp}) >= TP(E): {n_ok}/15 -> {'pass' if g3 else 'FAIL'}",
                  f"- mechanism: tail flagged share {kp} {mS:.2f} vs L (E12) 0.87 -> "
                  f"{'lower' if mS < 0.87 else 'NOT lower'}"]
        oE, oS = official("E", *FROZEN), official(kp, cS[0], cS[1])
        lines += ["\n## Official SzCORE aggregation (mean over subjects)\n", "```"]
        for k, o, cfg in (("E", oE, FROZEN), (kp, oS, cS[:2])):
            lines.append(f"{k} {cfg}: sens {o.sens:.3f} prec {o.prec:.3f} F1 {o.f1:.3f} FP/day {o.fa_day:.1f}")
        lines += ["```", f"\n## Per subject, seed-mean TP ({kp} at its cell | E frozen) / n_ref\n", "```"]
        lines += [f"{s}  {tpS.get(s, np.nan):4.1f} | {tpE[s]:4.1f} / {int(nref[s])}" for s in tpE.index]
        lines.append("```")
        sh = A[(A.kind == kp) & (A.smooth == cS[0]) & (A.top == cS[1])]
        lines.append(f"\nShort seizures (< 20 s) detected by {kp}: {float(sh.tp_short.iloc[0]):.1f} of {int(sh.n_short.iloc[0])}")
    lines.append(f"\n**{'ADOPTED' if adopted else 'NOT adopted'}**"
                 + (f" -> FROZEN for one disclosed test look: v2 clean, {kp}, D1 smooth {cS[0]}, top {cS[1]}"
                    if adopted else ""))
    lines.append(f"\nElapsed {time.time()-t0:.0f} s.")
    (OUT / "SUMMARY.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s1 = sub.add_parser("dump"); s1.add_argument("--smoke", action="store_true")
    s1.add_argument("--subjects", nargs="+", default=E8.SUBJS)
    sub.add_parser("eval")
    a = ap.parse_args()
    if a.cmd == "dump":
        subs = ["chb01"] if a.smoke else a.subjects
        guard(subs)
        for s in subs:
            dump_subject(s, smoke=a.smoke)
    else:
        guard(E8.SUBJS)
        evaluate()


if __name__ == "__main__":
    main()
