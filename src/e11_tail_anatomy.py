#!/usr/bin/env python
"""
e11_tail_anatomy.py -- stage P2, step 1: WHICH readout owns the false-alarm tail?
Cache only (results/e8_gae_v2/scores + data/trainset_v2 flags). 15 non-test subjects. No training,
no detector change, no test data. Descriptive: it has no gate; its reading rules (below) decide what
the adaptation experiment E12 must cover. Written before any number of this script was read.

Why. P1 diagnosis (PERF_PHASE_RECORD.md section 4): on test, removing the patient's own flagged
(high-amplitude) non-seizure windows drops the share of same-length non-ictal spans that out-rank a
seizure peak from 20-50 % to 0.1-1 %. v2 lifted seizures but left flagged windows where they were.
The ensemble = mean of three robust-z readouts (recon, latent, gamma). Patient-specific adaptation of
the GAE changes recon and latent, NOT gamma (a fixed gamma-AEC feature). A per-patient GMM on the v2
latent (E8 V2_GMM) did not raise event sensitivity (0.484 vs 0.489). So before E12 we must know which
readout puts flagged windows in the tail.

Scores rebuilt exactly as E8/E10 (per-patient robust-z on non-signal-loss windows; ER rlg ensemble):
  models: V1 (locked), clean_seed42, clean_seed1
  branches: r = recon, l = LedoitWolf Mahalanobis of mean latent, g = gamma,
            E = ensemble(r, l, g)                       (the E8-frozen V2_LW score)
            lg = per-patient GMM(k=8) NLL on [mean, std] latent (E8 V2_GMM readout), Eg = ensemble(r, lg, g)
  smoothing: per file, centred rolling mean of 15 windows over non-signal-loss windows (= D1)
Measures, per subject, model, branch:
  M1 window AUROC seizure vs flagged non-ictal, seizure vs clean non-ictal (smoothed score)
  M2 tail: T = top 2 % of the smoothed E (the frozen D1 cell); among non-ictal windows in T: share
     flagged, and the mean smoothed robust-z of each branch; the branch with the largest mean = owner
  M3 exceedance (Part-B style): per seizure of length L windows, peak of the smoothed branch score;
     non-ictal, non-buffer blocks of L consecutive windows inside a file; share of blocks whose peak
     exceeds the seizure peak (all blocks, and blocks with no flagged window = "oracle")
READING RULES (fixed now), v2 clean, both seeds agreeing:
  R1 owner of the tail = branch that is owner in >= 8 of 15 subjects (M2).
  R2 if R1 = recon or latent  -> E12 = adaptation of the GAE (covers recon and latent), as planned.
  R3 if R1 = gamma            -> E12 must also make gamma patient-relative (design revised first);
                                  adaptation of the GAE alone is not expected to help.
  R4 no branch reaches 8/15   -> the tail is shared; E12 adapts the GAE and refits every readout
                                  per patient; M3 per branch is reported as the mechanism baseline.
  M3 'oracle' vs 'all' per branch is the baseline that E12's mechanism check is compared against.
TEST GUARD: E8.SUBJS only; any test subject raises.
Run:  python src/e11_tail_anatomy.py [--smoke]          (estimated 5-15 min CPU, not measured)
"""
import argparse
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import rankdata
from sklearn.covariance import LedoitWolf
from sklearn.mixture import GaussianMixture

ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT / "src", ROOT / "src" / "retrain", ROOT / "src" / "dataprep",
          ROOT / "src" / "phaseB", ROOT / "src" / "phaseC"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
import e8_gae_v2_eval as E8      # noqa: E402
import ensemble_recipe as ER     # noqa: E402

TEST = {"chb03", "chb06", "chb13", "chb14", "chb15", "chb16", "chb17", "chb18"}
OUT = ROOT / "results" / "e11_tail_anatomy"
MODELS = ["V1", "clean_seed42", "clean_seed1"]
TOP, SMOOTH, FIT_MAX = 0.02, 15, 20000


def rz(x, ok):
    m = np.median(x[ok]); s = np.median(np.abs(x[ok] - m)) + 1e-9
    return (x - m) / s


def auc(s, pos, neg):
    a, b = s[pos], s[neg]
    a, b = a[np.isfinite(a)], b[np.isfinite(b)]
    if len(a) == 0 or len(b) == 0:
        return np.nan
    r = rankdata(np.concatenate([a, b]))
    return (r[:len(a)].sum() - len(a) * (len(a) + 1) / 2) / (len(a) * len(b))


def smooth(x, ok, fidx):
    out = np.full(len(x), np.nan)
    for f in np.unique(fidx):
        m = fidx == f
        out[m] = (pd.Series(np.where(ok[m], x[m], np.nan))
                  .rolling(SMOOTH, min_periods=1, center=True).mean().values)
    return out


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


def block_peaks(sm, nonict, flag, fidx, L):
    """peaks of non-overlapping L-window blocks fully inside non-ictal runs of each file."""
    peaks, clean = [], []
    for f in np.unique(fidx):
        m = np.flatnonzero(fidx == f)
        for a, b in runs(nonict[m]):
            k = (b - a) // L
            if k == 0:
                continue
            seg = sm[m[a:a + k * L]].reshape(k, L)
            fl = flag[m[a:a + k * L]].reshape(k, L)
            pk = np.nanmax(np.where(np.isfinite(seg), seg, -np.inf), axis=1)
            peaks.append(pk); clean.append(~fl.any(axis=1))
    if not peaks:
        return np.array([]), np.array([], bool)
    return np.concatenate(peaks), np.concatenate(clean)


def branches(z, c, model, ok, n, rng):
    idx = c["idx"]

    def full(v):
        o = np.full(n, np.nan); o[idx] = v; o[~ok] = np.nanmedian(v); return o

    g = rz(full(z["zgamma_raw"][idx].astype(float)), ok)
    key = "v1" if model == "V1" else model
    r = rz(full(c[f"{key}_recon"]), ok)
    lat = c[f"{key}_lat"]
    l = rz(full(LedoitWolf().fit(lat).mahalanobis(lat)), ok)

    def ens(a, b, cc):
        return np.asarray(ER.build_ensemble_subset({"zrecon": a, "zlatent": b, "zgamma": cc},
                                                   ER.CANDIDATES["rlg"]), float)
    out = dict(r=r, l=l, g=g, E=ens(r, l, g))
    plain = np.nanmean(np.vstack([r, l, g]), axis=0)
    out["_ens_vs_mean_maxdiff"] = float(np.nanmax(np.abs(out["E"] - plain)))
    if model != "V1":
        V = np.hstack([lat, c[f"{key}_latstd"]])
        ce = np.median(V, axis=0); q = np.subtract(*np.percentile(V, [75, 25], axis=0)); q[q < 1e-9] = 1
        V = np.clip((V - ce) / q, -10, 10)
        fit = rng.choice(len(V), min(FIT_MAX, len(V)), replace=False)
        gm = GaussianMixture(8, covariance_type="full", reg_covar=1e-3, max_iter=300,
                             random_state=0).fit(V[fit])
        out["lg"] = rz(full(-gm.score_samples(V)), ok)
        out["Eg"] = ens(r, out["lg"], g)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true", help="first two subjects only")
    a = ap.parse_args()
    subs = E8.SUBJS[:2] if a.smoke else E8.SUBJS
    if set(subs) & TEST:
        raise SystemExit("TEST GUARD")
    OUT.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(0)
    t0 = time.time()
    rows, ex_rows = [], []
    for s in subs:
        z = np.load(E8.DATA / f"{s}.npz", allow_pickle=True)
        c = np.load(E8.OUT / "scores" / f"{s}.npz")
        n = len(z["is_ictal"])
        ok = ~z["is_signal_loss"].astype(bool)
        ict = z["is_ictal"].astype(bool) & ok
        buf = z["is_buffer"].astype(bool)
        fl5 = z["is_flag5sd"].astype(bool)
        fidx = z["file_idx"].astype(int)
        nonict = ~z["is_ictal"].astype(bool) & ~buf & ok
        flag, bg = nonict & fl5, nonict & ~fl5
        sz_events = []
        for f in np.unique(fidx):
            m = np.flatnonzero(fidx == f)
            sz_events += [m[a_:b_] for a_, b_ in runs(ict[m])]
        for model in MODELS:
            if model != "V1" and f"{model}_recon" not in c.files:
                raise SystemExit(f"{s}: {model} missing in the E8 cache")
            br = branches(z, c, model, ok, n, rng)
            chk = br.pop("_ens_vs_mean_maxdiff")
            sm = {k: smooth(v, ok, fidx) for k, v in br.items()}
            thr = np.nanquantile(sm["E"][ok], 1 - TOP)
            T = (sm["E"] > thr) & nonict
            row = dict(subject=s, model=model, n_sz=len(sz_events), n_sz_windows=int(ict.sum()),
                       frac_ictal=float(ict.sum() / ok.sum()), frac_flag_nonict=float(flag.sum() / nonict.sum()),
                       ens_minus_plain_mean=chk, tail_n=int(T.sum()),
                       tail_share_flagged=float(fl5[T].mean()) if T.any() else np.nan)
            means = {}
            for k in ("r", "l", "g"):
                means[k] = float(np.nanmean(sm[k][T])) if T.any() else np.nan
                row[f"tail_mean_{k}"] = means[k]
                row[f"sz_mean_{k}"] = float(np.nanmean(sm[k][ict])) if ict.any() else np.nan
            row["tail_owner"] = max(means, key=lambda k: -np.inf if np.isnan(means[k]) else means[k])
            for k, v in sm.items():
                row[f"auc_szflag_{k}"] = auc(v, ict, flag)
                row[f"auc_szbg_{k}"] = auc(v, ict, bg)
            rows.append(row)
            cache = {}
            for e_i, ev in enumerate(sz_events):
                L = len(ev)
                for k, v in sm.items():
                    if (L, k) not in cache:
                        cache[(L, k)] = block_peaks(v, nonict, fl5, fidx, L)
                    pk, cl = cache[(L, k)]
                    peak = np.nanmax(v[ev])
                    ex_rows.append(dict(subject=s, model=model, branch=k, seizure=e_i, L_win=L,
                                        n_blocks=len(pk), exceed_all=float((pk > peak).mean()) if len(pk) else np.nan,
                                        exceed_oracle=float((pk[cl] > peak).mean()) if cl.any() else np.nan))
        print(f"{s}: done ({time.time()-t0:.0f}s)", flush=True)

    R = pd.DataFrame(rows); X = pd.DataFrame(ex_rows)
    R.to_csv(OUT / "per_subject.csv", index=False); X.to_csv(OUT / "exceedance_per_seizure.csv", index=False)

    lines = ["# E11 -- tail anatomy by readout, 15 non-test subjects (cache only)\n",
             f"subjects {len(subs)}; smoothing {SMOOTH} windows; tail = top {TOP:.0%} of the smoothed ensemble; "
             f"max |ER ensemble - plain mean| = {R.ens_minus_plain_mean.max():.2e}\n",
             "## M2 tail owner (count of subjects) and tail composition (median over subjects)\n", "```"]
    for m in MODELS:
        q = R[R.model == m]
        own = q.tail_owner.value_counts().to_dict()
        lines.append(f"{m:13s} owner {own} | flagged share in tail {q.tail_share_flagged.median():.2f} | "
                     f"tail mean z r/l/g {q.tail_mean_r.median():.2f}/{q.tail_mean_l.median():.2f}/"
                     f"{q.tail_mean_g.median():.2f} | seizure mean z r/l/g {q.sz_mean_r.median():.2f}/"
                     f"{q.sz_mean_l.median():.2f}/{q.sz_mean_g.median():.2f}")
    lines += ["```", "\n## M1 window AUROC (median over subjects): seizure vs flagged | seizure vs clean\n", "```"]
    for m in MODELS:
        q = R[R.model == m]
        ks = [k for k in ("r", "l", "lg", "g", "E", "Eg") if f"auc_szflag_{k}" in q and q[f"auc_szflag_{k}"].notna().any()]
        lines.append(f"{m:13s} " + "  ".join(f"{k} {q[f'auc_szflag_{k}'].median():.3f}|{q[f'auc_szbg_{k}'].median():.3f}"
                                             for k in ks))
    lines += ["```", "\n## M3 exceedance (median over seizures): share of same-length non-ictal blocks above the "
              "seizure peak, all blocks | blocks without a flagged window\n", "```"]
    for m in MODELS:
        q = X[X.model == m]
        lines.append(f"{m:13s} " + "  ".join(
            f"{k} {g.exceed_all.median():.3f}|{g.exceed_oracle.median():.3f}" for k, g in q.groupby("branch")))
    lines += ["```", "\n## Reading rules (fixed before the run)\n"]
    for m in ("clean_seed42", "clean_seed1"):
        own = R[R.model == m].tail_owner.value_counts()
        top = own.idxmax() if len(own) else None
        lines.append(f"- {m}: owner in >= 8/15 -> {top if len(own) and own.max() >= 8 else 'none (R4)'} "
                     f"({own.to_dict()})")
    lines.append(f"\nElapsed {time.time()-t0:.0f} s.")
    (OUT / "SUMMARY.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
