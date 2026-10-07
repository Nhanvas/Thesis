#!/usr/bin/env python
"""
e15_patient_adaptation.py -- stage P2, step 5. Patient-specific, label-free adaptation of the v2 GAE,
tested as intended (E13 was only a diluted proxy). 15 non-test subjects. Design approved by the
author on 2026-10-07 with the review corrections (a)-(f).

Hypothesis. Fine-tuning v2 on the patient's own complete recording (no labels) makes that patient's
frequent high-amplitude states ordinary for the encoder, so the per-channel latent anomaly (S9) of
those states falls while seizures (rare, ~0.2-1 % of windows) stay anomalous.

Arm (one, fixed now). Per patient and seed (v2 clean 42 and 1):
  data      every non-signal-loss window of the patient (the windows that are scored); no is_ictal,
            no is_buffer, no flag is read; f7 scaled with the training constants in the checkpoint json
  model     all 3,964 parameters; loss = train_gae_v2.batch_loss (joint, LAMBDA 0.1), unchanged
  budget    Adam lr 1e-4 (1/10 of the base initial lr), batch 32, 2,000 steps, windows drawn uniformly
            with replacement (fixed per step, not per data volume: ~3.5 passes for chb08, ~0.46 for
            chb04); torch/numpy seeds fixed per (subject, seed)
  readout   S9 recomputed from the adapted encoder exactly as E14 (per-channel LedoitWolf on the node
            latent, per-patient per-channel robust-z, 9th largest of 18, robust-z)
  detector  E8/E14 D1 grid (e1_normal_definition.event_grid), seed mean, best pooled cell at FA/day <= 25
Reference: S9 base = E14 dump (results/e14_spatial_recruitment/pernode), recomputed here.
Characterisation only (never used to choose): latents after 500 and 1,000 steps.

ADOPTION (all; cells chosen by the pooled rule for both arms, every other figure read at those cells):
  G1 seed-mean pooled best (<= 25 FA/day) >= S9 + 0.05, AND each seed's best >= that seed's S9 best
  G2 official SzCORE subject-mean sensitivity at the chosen cell >= S9's at its chosen cell
  G3 pooled sensitivity without chb12 at the chosen cell >= S9's without chb12 at its cell
  G4 validation-only (chb10, chb11, chb22) best >= S9's validation-only best
  G5 per subject seed-mean TP >= S9's in >= 9 of 15
  M  (hard, contamination) median over subjects of the median S9 robust-z of seizure windows >= 0.90 x
     the S9 base value (i.e. not more than 10 % lower)
  Descriptive only: median z of flagged non-ictal windows, tail flagged share (flag != artifact).
A negative result reads "negative at this budget", not "adaptation does not work".
FREEZE RULE (fixed now, before any number): if adopted -> the candidate score for the next steps is
S9-adapted (2,000 steps); otherwise S9 base. The next steps (ensemble form restoring the thesis shape,
CPD as onset/offset localizer) are gated for non-inferiority against that candidate, then the whole
system is frozen for ONE disclosed test look.
Not added (decision 2026-10-07): an arm fine-tuned only on the first N windows of the patient. DynaSD
fits a short baseline (iEEG: -120 to -60 s before an annotated onset, i.e. chosen with the seizure time;
ICU scalp: first 10 or 20 min, the paper is inconsistent; SzCORE CHB-MIT: the start of EACH recording).
For a 3,964-parameter GAE, 150 windows (10 min) x 2,000 steps is ~430 passes over one brain state
across 20-40 h recordings; the faithful CHB-MIT analogue is a per-recording baseline, which is a
readout-level lever (baseline drift) and is tested separately on the saved latents (Z below).
Saved for that next step: full node latents (float16) of the base model (s0) and after 2,000 steps.
Analysis only (not in the method): seizures inside the first 150 windows of each patient and each file.
TEST GUARD: E8.SUBJS only.
Run:
  python src/e15_patient_adaptation.py adapt --smoke     (chb01, 2,048 windows, 50 steps; ~1-2 min)
  python src/e15_patient_adaptation.py adapt             (estimated 1.75-3.5 h CPU, not measured; ~1.4 GB of latents)
  python src/e15_patient_adaptation.py eval              (estimated 10-30 min CPU, not measured)
  E21 (4-seed rule): python src/e15_patient_adaptation.py adapt --tags clean_seed2 clean_seed3 --suffix _s23 --no-z
     (same arm, seeds 2 and 3; reproduction gate against results/p2_seeds; estimated 1.5-3 h, not measured)
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
OUT = ROOT / "results" / "e15_patient_adaptation"
DUMP = OUT / "pernode"
BASE_DUMP = ROOT / "results" / "e14_spatial_recruitment" / "pernode"
CKPT = ROOT / "data" / "models_v2"
TAGS = ["clean_seed42", "clean_seed1"]
KEEP_Z = True
STEPS, SAVE_AT, LR, BATCH, K = 2000, (500, 1000, 2000), 1e-4, 32, 9


def guard(subs):
    if set(subs) & TEST or not set(subs) <= set(E8.SUBJS):
        raise SystemExit("TEST GUARD")


# ----------------------------------------------------------------------------- adapt
def per_channel_d(model, adj, xn, fa, ox, G, T2):
    import torch
    from torch_geometric.data import Batch
    n = len(adj)
    Z = np.empty((n, G.N_CH, G.LATENT_DIM), np.float32)
    model.eval()
    with torch.no_grad():
        for s in range(0, n, E8.CHUNK):
            e = min(s + E8.CHUNK, n)
            b = Batch.from_data_list([T2.window_data(adj[i], xn[i], fa[i]) for i in range(s, e)])
            Z[s:e] = model.encoder(b.x, b.edge_index, b.edge_attr).view(b.num_graphs, G.N_CH, G.LATENT_DIM).numpy()
    D = np.empty((n, G.N_CH), np.float32)
    for c in range(G.N_CH):
        Zc = Z[:, c, :].astype(np.float64)
        D[:, c] = LedoitWolf().fit(Zc).mahalanobis(Zc)
    return D, Z.mean(axis=1), Z


def adapt_subject(subj, smoke=False):
    import torch
    from torch_geometric.data import Batch
    import gae_joint as G
    import train_gae_v2 as T2
    out = DUMP / f"{subj}{'_SMOKE' if smoke else ''}.npz"
    if out.exists() and not smoke:
        print(f"{subj}: exists, skip"); return
    t0 = time.time()
    z = np.load(E8.DATA / f"{subj}.npz", allow_pickle=True)
    cache = np.load(E8.OUT / "scores" / f"{subj}.npz")
    idx = cache["idx"]
    if not np.array_equal(idx, np.flatnonzero(~z["is_signal_loss"])):
        raise SystemExit(f"{subj}: window index differs from the E8 cache")
    steps, save_at = (50, (25, 50)) if smoke else (STEPS, SAVE_AT)
    if smoke:
        idx = idx[:2048]
    adj = z["adj"][idx].astype(np.float32); adj[~np.isfinite(adj).all(axis=(1, 2))] = 0.0
    bp5 = z["bp5"][idx].astype(np.float32); bp5[~np.isfinite(bp5)] = 0.0
    xn = T2.bp_minmax(bp5)
    f7 = z["f7"][idx].astype(np.float64)
    res = {"idx": idx}
    snum = int(subj[3:])
    for tag in TAGS:
        ck = CKPT / f"gae_v2_{tag}.pt"
        meta = json.loads(ck.with_suffix(".json").read_text())
        mu, sd, clip = np.array(meta["add_mean"]), np.array(meta["add_std"]), meta["clip"]
        fa = ((np.clip((f7 - mu) / sd, -clip, clip) + clip) / (2 * clip)).astype(np.float32)
        model = G.GAEModel(in_dim=meta["in_dim"], bands=meta["out_x"])
        model.load_state_dict(torch.load(str(ck), map_location="cpu"), strict=True)
        # base pass over every window: reproduction gates (E8 mean latent, E14 per-channel distances)
        D0, lat0, Z0 = per_channel_d(model, adj, xn, fa, meta["out_x"], G, T2)
        lat_src = cache if tag in ("clean_seed42", "clean_seed1") else np.load(ROOT / "results" / "p2_seeds" / f"{subj}.npz")
        err = float(np.abs(lat0 - lat_src[f"{tag}_lat"][:len(idx)]).max())
        if err > 1e-4:
            raise SystemExit(f"STOP {subj} {tag}: base latent differs from E8 cache by {err:.2e}")
        if not smoke:
            base_src = BASE_DUMP / f"{subj}.npz" if tag in ("clean_seed42", "clean_seed1") \
                else ROOT / "results" / "p2_seeds" / f"{subj}.npz"
            e14 = np.load(base_src)[f"{tag}_d"]
            rel = float(np.abs(D0 - e14).max() / (np.abs(e14).max() + 1e-9))
            if rel > 1e-3:
                raise SystemExit(f"STOP {subj} {tag}: base per-channel distances differ from E14 by {rel:.2e}")
        if KEEP_Z:
            res[f"{tag}_s0_Z"] = Z0.astype(np.float16)
        seed = 10_000 + 100 * snum + int(tag.split("seed")[1])
        T2.set_seed(seed)
        rng = np.random.default_rng(seed)
        opt = torch.optim.Adam(model.parameters(), lr=LR)
        losses = []
        for step in range(1, steps + 1):
            model.train()
            pick = rng.integers(0, len(idx), BATCH)
            b = Batch.from_data_list([T2.window_data(adj[i], xn[i], fa[i]) for i in pick])
            opt.zero_grad()
            loss = T2.batch_loss(model, b, "cpu").mean()
            loss.backward(); opt.step()
            losses.append(loss.item())
            if step in save_at:
                D, _, Zs = per_channel_d(model, adj, xn, fa, meta["out_x"], G, T2)
                res[f"{tag}_s{step}_d"] = D
                if step == save_at[-1] and KEEP_Z:
                    res[f"{tag}_s{step}_Z"] = Zs.astype(np.float16)
                print(f"  {subj} {tag}: step {step}, mean loss last 100 {np.mean(losses[-100:]):.5f} "
                      f"({time.time()-t0:.0f}s)", flush=True)
        res[f"{tag}_loss"] = np.array(losses, np.float32)
    DUMP.mkdir(parents=True, exist_ok=True)
    np.savez(out, **res)
    print(f"{subj}: {len(idx)} windows adapted, {time.time()-t0:.0f}s", flush=True)


# ----------------------------------------------------------------------------- eval
def rz(x, ok):
    m = np.median(x[ok]); s = np.median(np.abs(x[ok] - m)) + 1e-9
    return (x - m) / s


def s_k(D, k=K):
    okk = np.ones(len(D), bool)
    Zc = np.column_stack([rz(D[:, j].astype(np.float64), okk) for j in range(D.shape[1])])
    return -np.sort(-Zc, axis=1)[:, k - 1]


def evaluate():
    import e1_normal_definition as E1
    import e11_tail_anatomy as E11
    t0 = time.time()
    rows, mech = [], []
    arms = {"S9base": None, "S9a500": 500, "S9a1000": 1000, "S9a2000": 2000}
    for s in E8.SUBJS:
        z = np.load(E8.DATA / f"{s}.npz", allow_pickle=True)
        base = np.load(BASE_DUMP / f"{s}.npz"); ad = np.load(DUMP / f"{s}.npz")
        d = E8.d_for_grid(z)
        n = len(d["is_ictal"]); ok = ~d["is_signal_loss"]; idx = base["idx"]
        if not np.array_equal(idx, ad["idx"]):
            raise SystemExit(f"{s}: adapted dump index differs from the E14 dump")
        fidx = z["file_idx"].astype(int); fl5 = z["is_flag5sd"].astype(bool)
        ict = z["is_ictal"].astype(bool) & ok
        nonict = ~z["is_ictal"].astype(bool) & ~z["is_buffer"].astype(bool) & ok
        nh = float((~d["is_ictal"] & ok).sum()) * E8.WIN / 3600

        def full(v):
            o = np.full(n, np.nan); o[idx] = v; o[~ok] = np.nanmedian(v); return o

        for tag in TAGS:
            for arm, st in arms.items():
                D = base[f"{tag}_d"] if st is None else ad[f"{tag}_s{st}_d"]
                v = rz(full(s_k(D)), ok)
                name = f"{tag}|{arm}"
                for r_ in E1.event_grid(d, v):
                    r_.update(subject=s, score=name, nonict_h=nh); rows.append(r_)
                sm = E11.smooth(v, ok, fidx)
                T = (sm > np.nanquantile(sm[ok], 0.98)) & nonict
                mech.append(dict(subject=s, seed=tag, kind=arm, sz_median_z=float(np.nanmedian(v[ict])),
                                 flag_median_z=float(np.nanmedian(v[nonict & fl5])),
                                 tail_flag_share=float(fl5[T].mean()) if T.any() else np.nan,
                                 auc_szflag=E11.auc(sm, ict, nonict & fl5)))
        print(f"{s}: done ({time.time()-t0:.0f}s)", flush=True)

    gr = pd.DataFrame(rows); gr.to_csv(OUT / "grid_per_subject.csv", index=False)
    M = pd.DataFrame(mech); M.to_csv(OUT / "mechanism.csv", index=False)
    gr["kind"] = gr.score.str.split("|").str[1]; gr["seed"] = gr.score.str.split("|").str[0]

    def per_seed(df):
        p = df.groupby(["kind", "seed", "smooth", "top"])[["tp", "fp", "n_ref", "nonict_h", "tp_short",
                                                           "n_ref_short"]].sum().reset_index()
        p["sens"] = p.tp / p.n_ref; p["fa_day"] = p.fp / p.nonict_h * 24
        return p

    def seed_mean(p):
        return p.groupby(["kind", "smooth", "top"]).agg(sens=("sens", "mean"), fa_day=("fa_day", "mean"),
                                                        tp_short=("tp_short", "mean"),
                                                        n_short=("n_ref_short", "max")).reset_index()

    P = per_seed(gr); A = seed_mean(P)
    Av = seed_mean(per_seed(gr[gr.subject.isin(E8.VAL)]))
    Ax = seed_mean(per_seed(gr[gr.subject != "chb12"]))
    A.to_csv(OUT / "grid_seed_mean.csv", index=False)

    def best(T, kind, cap=25.0):
        q = T[(T.kind == kind) & (T.fa_day <= cap)]
        if not len(q):
            return 0.0, None
        r = q.loc[q.sens.idxmax()]
        return float(r.sens), (int(r.smooth), float(r.top), round(float(r.fa_day), 2))

    def at(T, kind, cell):
        q = T[(T.kind == kind) & (T.smooth == cell[0]) & (T.top == cell[1])]
        return float(q.sens.iloc[0]) if len(q) else np.nan

    def subj_mean(kind, cell):
        q = gr[(gr.kind == kind) & (gr.smooth == cell[0]) & (gr.top == cell[1])]
        q = q.groupby(["seed", "subject"])[["tp", "fp", "n_ref", "nonict_h"]].sum().reset_index()
        q["sens"] = q.tp / q.n_ref; q["prec"] = q.tp / (q.tp + q.fp).where(q.tp + q.fp > 0)
        q["f1"] = 2 * q.tp / (2 * q.tp + q.fp + (q.n_ref - q.tp)); q["fa_day"] = q.fp / q.nonict_h * 24
        return q.groupby("seed")[["sens", "prec", "f1", "fa_day"]].mean().mean()

    lines = ["# E15 -- patient-specific adaptation of v2 (2,000 steps) + S9, 15 non-test subjects\n",
             "## Pooled seed mean: best <= 25 | <= 15 | <= 10 | validation-only | without chb12 at the cell | "
             "subject-mean sens/FP-day at the cell\n", "```"]
    info = {}
    for k in arms:
        b, c = best(A, k); bv, _ = best(Av, k)
        sm_ = subj_mean(k, c) if c else None
        info[k] = dict(best=b, cell=c, val=bv, x12=at(Ax, k, c) if c else np.nan,
                       subj=float(sm_.sens) if c else np.nan, subj_fa=float(sm_.fa_day) if c else np.nan,
                       seeds={t: best(P[P.seed == t].assign(), k)[0] for t in TAGS})
        role = "<- PRIMARY" if k == "S9a2000" else "(reference)" if k == "S9base" else "(characterisation)"
        lines.append(f"{k:8s} {b:.3f} {c} | {best(A, k, 15)[0]:.3f} | {best(A, k, 10)[0]:.3f} | val {bv:.3f} | "
                     f"no-chb12 {info[k]['x12']:.3f} | subj {info[k]['subj']:.3f} @ {info[k]['subj_fa']:.1f} | "
                     f"per seed {', '.join(f'{v:.3f}' for v in info[k]['seeds'].values())}  {role}")
    lines.append("```")
    B, Ad = info["S9base"], info["S9a2000"]
    gm = M.groupby(["kind", "subject"])[["sz_median_z", "flag_median_z", "tail_flag_share", "auc_szflag"]].mean()
    med = gm.groupby("kind").median()
    lines += ["\n## Mechanism (median over subjects of seed means)\n", "```",
              "kind      seizure z  flagged z  tail flagged  AUC sz-flag"]
    lines += [f"{k:8s}  {med.loc[k, 'sz_median_z']:9.2f}  {med.loc[k, 'flag_median_z']:9.2f}  "
              f"{med.loc[k, 'tail_flag_share']:12.2f}  {med.loc[k, 'auc_szflag']:.3f}" for k in arms]
    lines.append("```")
    adopted = False
    if Ad["cell"] is None:
        lines.append("S9a2000 never reaches FA/day <= 25 -> NOT adopted")
    else:
        tpA = gr[(gr.kind == "S9a2000") & (gr.smooth == Ad["cell"][0]) & (gr.top == Ad["cell"][1])].groupby("subject").tp.mean()
        tpB = gr[(gr.kind == "S9base") & (gr.smooth == B["cell"][0]) & (gr.top == B["cell"][1])].groupby("subject").tp.mean()
        nref = gr[(gr.kind == "S9base") & (gr.smooth == B["cell"][0]) & (gr.top == B["cell"][1])].groupby("subject").n_ref.max()
        n_ok = int((tpA >= tpB).sum())
        g1 = Ad["best"] >= B["best"] + 0.05 and all(Ad["seeds"][t] >= B["seeds"][t] for t in TAGS)
        g2 = Ad["subj"] >= B["subj"]
        g3 = Ad["x12"] >= B["x12"]
        g4 = Ad["val"] >= B["val"]
        g5 = n_ok >= 9
        zb = med.loc["S9base", "sz_median_z"]
        mm = med.loc["S9a2000", "sz_median_z"] >= zb - 0.10 * abs(zb)
        adopted = g1 and g2 and g3 and g4 and g5 and mm
        f = lambda x: "pass" if x else "FAIL"
        lines += [f"\n- G1 {Ad['best']:.3f} vs S9 {B['best']:.3f} + 0.05; per seed "
                  f"{[round(v, 3) for v in Ad['seeds'].values()]} vs {[round(v, 3) for v in B['seeds'].values()]} -> {f(g1)}",
                  f"- G2 subject-mean {Ad['subj']:.3f} vs {B['subj']:.3f} -> {f(g2)}",
                  f"- G3 without chb12 {Ad['x12']:.3f} vs {B['x12']:.3f} -> {f(g3)}",
                  f"- G4 validation-only {Ad['val']:.3f} vs {B['val']:.3f} -> {f(g4)}",
                  f"- G5 subjects TP >= S9: {n_ok}/15 -> {f(g5)}",
                  f"- M  seizure z {med.loc['S9a2000', 'sz_median_z']:.2f} vs base {zb:.2f} - 10 % -> {f(mm)}",
                  "\n## Per subject, seed-mean TP (adapted at its cell | S9 base at its cell) / n_ref\n", "```"]
        lines += [f"{s}  {tpA.get(s, np.nan):4.1f} | {tpB[s]:4.1f} / {int(nref[s])}" for s in tpB.index]
        lines.append("```")
    first = []
    for s_ in E8.SUBJS:
        z_ = np.load(E8.DATA / f"{s_}.npz", allow_pickle=True)
        ic, fi = z_["is_ictal"].astype(bool), z_["file_idx"].astype(int)
        nf = len(np.unique(fi))
        hit_f = sum(ic[np.flatnonzero(fi == f)[:150]].any() for f in np.unique(fi))
        first.append((s_, bool(ic[:150].any()), int(hit_f), nf))
    lines += ["\n## Analysis only: seizure windows inside the first 150 windows (10 min)\n",
              f"patients whose first 10 min contain a seizure: {sum(x[1] for x in first)}/15; "
              f"files whose first 10 min contain a seizure: {sum(x[2] for x in first)}/{sum(x[3] for x in first)}"]
    lines.append(f"\n**{'ADOPTED: candidate = S9-adapted (2,000 steps)' if adopted else 'NOT adopted at this budget: candidate = S9 base'}**")
    lines.append(f"\nElapsed {time.time()-t0:.0f} s.")
    (OUT / "SUMMARY.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


def main():
    global TAGS, DUMP
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s1 = sub.add_parser("adapt"); s1.add_argument("--smoke", action="store_true")
    s1.add_argument("--subjects", nargs="+", default=E8.SUBJS)
    s1.add_argument("--tags", nargs="+", default=None, help="e.g. clean_seed2 clean_seed3 (E21, 4-seed rule)")
    s1.add_argument("--suffix", default="", help="dump folder suffix, e.g. _s23")
    s1.add_argument("--no-z", action="store_true", help="do not keep node latents")
    sub.add_parser("eval")
    a = ap.parse_args()
    if a.cmd == "adapt":
        if a.tags:
            TAGS = a.tags
        if a.suffix:
            DUMP = OUT / f"pernode{a.suffix}"
        if a.no_z:
            globals()["KEEP_Z"] = False
        subs = ["chb01"] if a.smoke else a.subjects
        guard(subs)
        for s in subs:
            adapt_subject(s, smoke=a.smoke)
    else:
        guard(E8.SUBJS)
        evaluate()


if __name__ == "__main__":
    main()
