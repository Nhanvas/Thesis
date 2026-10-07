#!/usr/bin/env python
"""
p3b_diag.py -- stage P3-B diagnostics D1-D3 (record 9.6). DESCRIPTIVE, NO GATE, NO SELECTION. Cache only,
frozen final scalar (E17b, e22_test_oneshot.final_scalar), 4 seeds. Written 2026-10-07 before any result.

D1 smoothing scale (H9: a bursty seizure anomaly is diluted by the 20-s smoothing).
   (a) per seizure, p_need at smoothing {1, 2, 3, 5, 9} windows (share of the patient's smoothed values >=
       the seizure's peak over its SzCORE tolerance span); non-test, and test with --include-test (tier T-B,
       reachability only);
   (b) non-test operating curve: e1_normal_definition.event_grid on SMOOTH {1, 2, 3, 5, 9} x the fine top-p
       grid; best pooled sensitivity at FA/day <= 25 and <= 40 per smoothing (4-seed mean); FA/day at 5/0.02;
       reproduction: smoothing 5 / top 0.005 equals results/e17b_latent_family/grid_per_subject.csv;
   (c) short-seizure proxy (non-test only): each seizure's first 3 windows, peak of the smoothed score
       INSIDE those windows (no tolerance span, which would reach the rest of the seizure), p_need per
       smoothing. Conservative proxy: centred smoothing still borrows later seizure windows.
D2 where the top non-ictal windows lie (seed 42): for each patient, non-ictal windows of the smoothed (5)
   score in the top 0.5 % and in 0.5-2 %: flagged share, share in files that hold a seizure, share within
   10 min of a seizure in the same file but outside its tolerance span (peri-ictal), median distance to the
   nearest seizure (same file). chb12 (non-test analogue) and chb15 (test, tier T-B) are printed in full.
D3 tail-owning channel (label-free, tier T-A on test): per patient, seed 42, the histogram over the 18
   channel indices of the argmax per-channel robust-z in the top-0.5 % smoothed windows; top 3 indices with
   shares; per-channel median robust-z over all windows. Index -> name: read the montage order from code
   (the command greps it); this script does not guess names.
Run:  python src/p3b_diag.py --smoke                    (chb01, seed 42; ~1 min, estimated)
      python src/p3b_diag.py --include-test             (estimated 5-15 min CPU, not measured)
"""
import argparse
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT / "src", ROOT / "src" / "retrain", ROOT / "src" / "phaseB", ROOT / "src" / "phaseC",
          ROOT / "src" / "dataprep"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
import p2_scalars as PS                # noqa: E402
import e16_recording_baseline as E16   # noqa: E402
import e8_gae_v2_eval as E8            # noqa: E402
import e22_test_oneshot as E22         # noqa: E402

OUT = ROOT / "results" / "p3b_diag"
TAGS = list(E16.TAGS)
SMOOTHS = [1, 2, 3, 5, 9]
FINE = [0.05, 0.03, 0.02, 0.015, 0.01, 0.0075, 0.005, 0.002, 0.001]
WIN, PRE_W, POST_W, PERI_W = 4, 8, 15, 150      # 30 s, 60 s tolerances; 10 min peri-ictal


def pneed_fn(sm):
    v = np.sort(sm[np.isfinite(sm)])
    return lambda pk: (1.0 - np.searchsorted(v, pk, side="left") / len(v)) if np.isfinite(pk) and len(v) else np.nan


def peak(v, idx):
    seg = v[idx]
    return np.nanmax(seg) if np.isfinite(seg).any() else np.nan


def seizure_runs(ctx):
    for f in np.unique(ctx["fidx"]):
        m = np.flatnonzero(ctx["fidx"] == f)
        for a, b in PS._runs(ctx["ict"][m]):
            yield f, m, a, b


def d1_seizures(ctx, s, sset, tag, x, rows):
    sms = {w: PS.smoothed(ctx, x, w) for w in SMOOTHS}
    pns = {w: pneed_fn(sms[w]) for w in SMOOTHS}
    for f, m, a, b in seizure_runs(ctx):
        ge = m[max(0, a - PRE_W):min(len(m), b + POST_W)]
        r = dict(subject=s, set=sset, seed=tag, file=int(f), onset_s=a * WIN, dur_s=(b - a) * WIN)
        for w in SMOOTHS:
            r[f"pn_s{w}"] = pns[w](peak(sms[w], ge))
            if sset == "non-test":
                r[f"proxy_s{w}"] = pns[w](peak(sms[w], m[a:min(b, a + 3)]))
        rows.append(r)


def d2_tail(ctx, s, sset, x, rows):
    sm = PS.smoothed(ctx, x, 5)
    q995, q98 = np.nanquantile(sm, 0.995), np.nanquantile(sm, 0.98)
    n = ctx["n"]; dist = np.full(n, np.inf); intol = np.zeros(n, bool); sz_file = np.zeros(n, bool)
    for f, m, a, b in seizure_runs(ctx):
        pos = np.arange(len(m))
        d = np.where(pos < a, a - pos, np.where(pos >= b, pos - b + 1, 0))
        dist[m] = np.minimum(dist[m], d)
        intol[m[max(0, a - PRE_W):min(len(m), b + POST_W)]] = True
        sz_file[m] = True
    has_flag = "is_flag5sd" in ctx["z"].files
    fl = ctx["z"]["is_flag5sd"].astype(bool) if has_flag else np.zeros(n, bool)
    nonict = ~ctx["ict"] & ctx["ok"]
    for tier, mask in (("top0.5%", sm > q995), ("0.5-2%", (sm > q98) & (sm <= q995))):
        T = mask & nonict
        k = int(T.sum())
        rows.append(dict(subject=s, set=sset, tier=tier, n_nonictal=k,
                         frac_nonictal=float(T.sum() / max((mask & ctx["ok"]).sum(), 1)),
                         flagged=float(fl[T].mean()) if (k and has_flag) else np.nan,
                         in_seizure_files=float(sz_file[T].mean()) if k else np.nan,
                         peri_10min=float(((dist[T] <= PERI_W) & ~intol[T]).mean()) if k else np.nan,
                         in_tolerance=float(intol[T].mean()) if k else np.nan,
                         median_dist_min=float(np.median(np.where(np.isfinite(dist[T]), dist[T] * WIN / 60, np.nan)))
                         if k and np.isfinite(dist[T]).any() else np.nan))


def d3_channels(ctx, s, sset, x, D, rows):
    okk = np.ones(len(D), bool)
    Zc = np.column_stack([E16.rz(D[:, j], okk) for j in range(D.shape[1])])
    Zf = np.full((ctx["n"], Zc.shape[1]), np.nan); Zf[ctx["idx"]] = Zc
    sm = PS.smoothed(ctx, x, 5)
    T = (sm > np.nanquantile(sm, 0.995)) & ctx["ok"]
    cnt = np.bincount(np.nanargmax(Zf[T], axis=1), minlength=Zc.shape[1]) / max(T.sum(), 1)
    med = np.median(Zc, axis=0)
    r = dict(subject=s, set=sset, n_tail=int(T.sum()))
    r.update({f"own_{j}": float(cnt[j]) for j in range(Zc.shape[1])})
    r.update({f"medz_{j}": float(med[j]) for j in range(Zc.shape[1])})
    rows.append(r)


def main():
    import e1_normal_definition as E1
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--include-test", action="store_true")
    a = ap.parse_args()
    t0 = time.time()
    nontest = ["chb01"] if a.smoke else list(E8.SUBJS)
    test = (["chb03"] if a.smoke else list(E22.TEST)) if a.include_test else []
    tags = ["clean_seed42"] if a.smoke else TAGS
    if set(nontest) & set(E22.TEST):
        raise SystemExit("TEST GUARD")
    E1.SMOOTH, E1.TOPS = SMOOTHS, FINE
    g17 = pd.read_csv(ROOT / "results" / "e17b_latent_family" / "grid_per_subject.csv")
    sz, grid, tail, ch = [], [], [], []
    for sset, subs in (("non-test", nontest), ("test", test)):
        for s in subs:
            ctx = PS.subject_context(s) if sset == "non-test" else E22.test_context(s)
            for tag in tags:
                x = E22.final_scalar(ctx, tag)
                d1_seizures(ctx, s, sset, tag, x, sz)
                if sset == "non-test":
                    for r_ in E1.event_grid(E8.d_for_grid(ctx["z"]), x):
                        if r_["smooth"] == 5 and np.isclose(r_["top"], 0.005):
                            w = g17[(g17.subject == s) & (g17.score == f"{tag}|E17b") & (g17.smooth == 5)
                                    & np.isclose(g17.top, 0.005)].iloc[0]
                            if (r_["tp"], r_["fp"]) != (int(w.tp), int(w.fp)):
                                raise SystemExit(f"STOP {s} {tag}: grid 5/0.005 {(r_['tp'], r_['fp'])} vs E17b {(int(w.tp), int(w.fp))}")
                        r_.update(subject=s, seed=tag, nonict_h=ctx["nh"]); grid.append(r_)
                if tag == "clean_seed42":
                    d2_tail(ctx, s, sset, x, tail)
                    d3_channels(ctx, s, sset, x, ctx["D"][tag], ch)
            print(f"{s}: done ({time.time()-t0:.0f}s)", flush=True)
    SZ, G, TL, CH = pd.DataFrame(sz), pd.DataFrame(grid), pd.DataFrame(tail), pd.DataFrame(ch)
    od = OUT / "smoke" if a.smoke else OUT
    od.mkdir(parents=True, exist_ok=True)
    for name, df in (("seizures", SZ), ("grid", G), ("tail", TL), ("channels", CH)):
        df.to_csv(od / f"{name}.csv", index=False)

    L = ["# P3-B diagnostics D1-D3 (descriptive, no gate), frozen final scalar, 4 seeds\n",
         "Reproduction: the non-test grid at 5/0.005 equals the E17b grid for every subject and seed.\n" if not a.smoke else "SMOKE.\n",
         "## D1a -- seizures with p_need <= 0.005 / 0.01 / 0.02 by smoothing (4-seed mean)\n", "```"]
    for sset in ("non-test", "test"):
        q = SZ[SZ.set == sset]
        if not len(q):
            continue
        for p in (0.005, 0.01, 0.02):
            cnt = {w: q.groupby("seed")[f"pn_s{w}"].apply(lambda v: (v <= p).sum()).mean() for w in SMOOTHS}
            L.append(f"{sset:8s} p<={p:<6} " + "  ".join(f"s{w}: {c:6.2f}" for w, c in cnt.items()) + f"   (n = {q.groupby('seed').size().mean():.0f})")
    L.append("```")
    L += ["\nPer subject, median p_need by smoothing (4-seed mean):\n", "```",
          SZ.groupby(["set", "subject", "seed"])[[f"pn_s{w}" for w in SMOOTHS]].median()
            .groupby(["set", "subject"]).mean().round(4).to_string(), "```"]
    if len(G):
        P_ = G.groupby(["seed", "smooth", "top"])[["tp", "fp", "n_ref", "nonict_h"]].sum().reset_index()
        P_["sens"] = P_.tp / P_.n_ref; P_["fa_day"] = P_.fp / P_.nonict_h * 24
        M = P_.groupby(["smooth", "top"])[["sens", "fa_day"]].mean().reset_index()
        L += ["\n## D1b -- non-test operating curve (pooled, 4-seed mean): best at FA/day <= 25 and <= 40\n", "```"]
        for w in SMOOTHS:
            out = []
            for cap in (25, 40):
                q = M[(M.smooth == w) & (M.fa_day <= cap)]
                out.append(f"<= {cap}: {q.sens.max():.3f} (top {q.loc[q.sens.idxmax(), 'top']}, {q.loc[q.sens.idxmax(), 'fa_day']:.1f})" if len(q) else f"<= {cap}: none")
            L.append(f"smooth {w}  " + " | ".join(out))
        r = M[(M.smooth == 5) & np.isclose(M.top, 0.02)]
        if len(r):
            L.append(f"FA/day at 5/0.02: {float(r.fa_day.iloc[0]):.1f}, sensitivity {float(r.sens.iloc[0]):.3f}")
        L += ["```", "\nFull curve (smoothing x top):\n", "```",
              M.pivot(index="top", columns="smooth", values="sens").round(3).to_string(), "",
              M.pivot(index="top", columns="smooth", values="fa_day").round(1).to_string(), "```"]
        L += ["\n## D1c -- short-seizure proxy (non-test, first 3 windows, no tolerance): count with p_need <= p\n", "```"]
        q = SZ[SZ.set == "non-test"]
        for p in (0.005, 0.01, 0.02):
            L.append(f"p<={p:<6} " + "  ".join(f"s{w}: {q.groupby('seed')[f'proxy_s{w}'].apply(lambda v: (v <= p).sum()).mean():6.2f}" for w in SMOOTHS))
        L.append("```")
    if len(TL):
        L += ["\n## D2 -- where the top non-ictal windows lie (seed 42, smoothing 5)\n", "```",
              TL.round(3).to_string(index=False), "```"]
    if len(CH):
        own = CH.set_index(["set", "subject"])[[f"own_{j}" for j in range(18)]]
        top3 = own.apply(lambda r: ", ".join(f"{int(c.split('_')[1])}:{v:.2f}" for c, v in r.sort_values(ascending=False).head(3).items()), axis=1)
        L += ["\n## D3 -- tail-owning channel index (top 3 with shares; seed 42, top 0.5 % windows)\n", "```",
              top3.to_string(), "```",
              "\nPer-channel median robust-z over all windows (should be ~0 by construction):\n", "```",
              CH.set_index(["set", "subject"])[[f"medz_{j}" for j in range(18)]].round(2).to_string(), "```"]
    L.append(f"\nElapsed {time.time()-t0:.0f} s.")
    (od / "SUMMARY.md").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
