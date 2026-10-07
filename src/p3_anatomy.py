#!/usr/bin/env python
"""
p3_anatomy.py -- stage P3, step P3-A: anatomy of the failures. DESCRIPTIVE, NO GATE, NO SELECTION.
Written 2026-10-07 before any P3 result (PERF_PHASE_RECORD section 9). Cache only, 4 seeds.

Part A  label-free (tier T-A), all 23 subjects:
  * input domain shift of the GAE v2 node features f7 (log band power x5, log line length, signed-log
    kurtosis): constants recomputed exactly as retrain/train_gae_v2.norm_constants (mean/std over the
    clean windows of the 12 training subjects); per subject and feature, share of values the model's
    standardisation clips at +-4, and the median in training-SD units (every 4th non-signal-loss window);
  * flagged (+-5 SD) share of all windows, hours, files;
  * frozen final scalar (E17b): file drift (IQR of per-file medians / patient MAD) before and after the
    +-15 min correction; share of the top-0.5 % smoothed windows lying in the patient's top-quartile
    files (files ranked before the correction); the channel owning that tail (argmax of the per-channel
    robust-z) and its share; (file, channel) pairs whose median per-channel robust-z over the file > 3.
Part B  annotation-guided (tier T-B; on the test subjects this is test-informed and is logged in record
  section 3). Per reference seizure (run of ictal windows inside a file), per seed:
  p_need(series) = share of the patient's smoothed (5 windows, = frozen D1) values >= the series' peak
  over the seizure's SzCORE tolerance span [onset - 30 s, offset + 60 s] = the top-p a threshold must
  reach to touch the seizure. Series: the frozen final scalar; the same without the +-15 min correction;
  each family member alone (S6e, S9e, S12e, Smean_e); focal-scale members (characterisation) S1e (max of
  18) and S3e (3rd largest). Also: channels with robust-z > 3 at the in-seizure peak; channels whose
  median robust-z over the seizure > 2; flagged share; gap to the nearest seizure in the same file;
  distance to the file's start and end; caught by the frozen detector (E1 overlap rule).
Part C  contamination of the per-patient fit (H2), non-test only (test node latents are not cached):
  per channel, LedoitWolf refitted on the node latent after dropping its 5 % most distant windows (one
  refit); final scalar rebuilt; p_need_trim vs p_need_refit0 (the untrimmed refit, same float16 latents).
Reproduction gates (STOP before anything is written):
  R0 the final scalar built here equals e22_test_oneshot.final_scalar (every subject, seed 42);
  R2 non-test: frozen detector tp/fp at cell 5/0.005 = results/e17b_latent_family/grid_per_subject.csv,
     every subject and seed;
  R3 test (only with --include-test): detector tp/fp = results/e22_test_oneshot/per_subject_seed.csv
     (stage detector), every subject and seed;
  R4 Part C: the untrimmed refit reproduces the cached distances (Spearman >= 0.999 on every channel).
NOT computed (record 9.2): no sensitivity-vs-FA curve on test; operating points are chosen on non-test.
TEST GUARD: test subjects are read only with --include-test.
Run:  python src/p3_anatomy.py --smoke --include-test (chb01 + chb03, seed 42; ~1-2 min, estimated)
      python src/p3_anatomy.py --include-test         (estimated 10-25 min CPU, not measured)
"""
import argparse
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import rankdata
from sklearn.covariance import LedoitWolf

ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT / "src", ROOT / "src" / "retrain", ROOT / "src" / "phaseB", ROOT / "src" / "phaseC",
          ROOT / "src" / "dataprep"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
import p2_scalars as PS                # noqa: E402
import e16_recording_baseline as E16   # noqa: E402
import e8_gae_v2_eval as E8            # noqa: E402
import e22_test_oneshot as E22         # noqa: E402

OUT = ROOT / "results" / "p3_anatomy"
TAGS = list(E16.TAGS)
TRAIN = ["chb01", "chb02", "chb04", "chb05", "chb07", "chb08", "chb09", "chb12",
         "chb19", "chb20", "chb21", "chb23"]
TEST = list(E22.TEST)
CELL = tuple(E22.CELL)                 # (5, 0.005), the frozen D1 cell
WIN = 4
PRE_W, POST_W = 8, 15                  # 30 s (7.5 windows, rounded up) and 60 s SzCORE tolerances
FAM = ("S6", "S9", "S12", "Smean_")   # "Smean_" + "e" -> Smean_e     # frozen family (E17b)
F7_NAMES = ["lbp_delta", "lbp_theta", "lbp_alpha", "lbp_beta", "lbp_gamma", "log_ll", "slog_kurt"]
TRIM = 0.05


# ----------------------------------------------------------------------------- builders
def norm_constants(subjects):
    """exactly retrain/train_gae_v2.norm_constants(variant='clean')."""
    n, s1, s2 = 0, np.zeros(7), np.zeros(7)
    for s in subjects:
        z = np.load(E8.DATA / f"{s}.npz", allow_pickle=True)
        m = ~z["is_ictal"] & ~z["is_buffer"] & ~z["is_signal_loss"] & ~z["is_flag5sd"]
        F = z["f7"][m].reshape(-1, 7).astype(np.float64)
        if not np.isfinite(F).all():
            raise SystemExit(f"STOP: {s} non-finite f7 inside the training mask")
        n += len(F); s1 += F.sum(0); s2 += (F * F).sum(0)
    mu = s1 / n
    return mu, np.sqrt(np.maximum(s2 / n - mu * mu, 1e-12))


def f7_shift(z, ok, mu, sd):
    if "f7" not in z.files:
        return {}
    w = np.flatnonzero(ok)[::4]
    X = (z["f7"][w].reshape(-1, 7).astype(np.float64) - mu) / sd
    X = np.where(np.isfinite(X), X, np.nan)
    clip = np.nanmean(np.abs(X) > 4, axis=0)
    med = np.nanmedian(X, axis=0)
    out = dict(f7_clip_max=float(np.nanmax(clip)), f7_clip_feat=F7_NAMES[int(np.nanargmax(clip))],
               f7_shift_maxabs=float(np.nanmax(np.abs(med))), f7_shift_feat=F7_NAMES[int(np.nanargmax(np.abs(med)))])
    out.update({f"clip_{k}": float(clip[i]) for i, k in enumerate(F7_NAMES)})
    out.update({f"shift_{k}": float(med[i]) for i, k in enumerate(F7_NAMES)})
    return out


def zc_of(D):
    okk = np.ones(len(D), bool)
    return np.column_stack([E16.rz(D[:, j], okk) for j in range(D.shape[1])])


def detr(v, wf):
    out = v.copy()
    for f in np.unique(wf):                       # identical to e17b_latent_family.member / E16.c_scalar("e")
        w = np.flatnonzero(wf == f)
        out[w] = v[w] - pd.Series(v[w]).rolling(451, min_periods=1, center=True).median().values
    return out


def build(ctx, D, focal=True):
    """percentile series on the full window axis + per-channel robust-z (n x 18, NaN off the dump)."""
    Zc = zc_of(D)
    S = -np.sort(-Zc, axis=1)
    raw = {"S6": S[:, 5], "S9": S[:, 8], "S12": S[:, 11], "Smean_": Zc.mean(axis=1)}
    if focal:
        raw.update({"S1": S[:, 0], "S3": S[:, 2]})
    P = {}
    for k, v in raw.items():
        P[k + "e"] = PS.pct(PS._full(ctx, detr(v, ctx["wf"])), ctx["ok"])
        if k in FAM:
            P[k + "_nodt"] = PS.pct(PS._full(ctx, v), ctx["ok"])
    out = {"final": np.mean([P[k + "e"] for k in FAM], axis=0),
           "final_nodt": np.mean([P[k + "_nodt"] for k in FAM], axis=0)}
    if focal:
        out.update({k + "e": P[k + "e"] for k in raw})
    Zf = np.full((ctx["n"], Zc.shape[1]), np.nan)
    Zf[ctx["idx"]] = Zc
    return out, Zf


def pneed_fn(sm):
    v = np.sort(sm[np.isfinite(sm)])

    def f(pk):
        if not np.isfinite(pk) or not len(v):
            return np.nan
        return 1.0 - np.searchsorted(v, pk, side="left") / len(v)
    return f


def trimmed_distances(Z, D):
    """per channel: untrimmed LW refit (reproduction R4) and one refit without the 5 % most distant."""
    D0, Dt = np.empty_like(D), np.empty_like(D)
    for j in range(D.shape[1]):
        X = Z[:, j, :].astype(np.float64)
        d0 = LedoitWolf().fit(X).mahalanobis(X)
        rho = np.corrcoef(rankdata(d0), rankdata(D[:, j]))[0, 1]
        if rho < 0.999:
            raise SystemExit(f"STOP R4: channel {j} untrimmed refit vs cached distances Spearman {rho:.5f}")
        keep = d0 <= np.quantile(d0, 1 - TRIM)
        D0[:, j] = d0
        Dt[:, j] = LedoitWolf().fit(X[keep]).mahalanobis(X)
    return D0, Dt


# ----------------------------------------------------------------------------- per subject
def analyse(ctx, s, sset, tags, mu, sd, ref_det, part_c, out):
    n, ok, fidx = ctx["n"], ctx["ok"], ctx["fidx"]
    z = ctx["z"]
    has_flag = "is_flag5sd" in z.files
    fl = z["is_flag5sd"].astype(bool) if has_flag else None
    base = dict(subject=s, set=sset, hours=n * WIN / 3600, files=int(len(np.unique(fidx))),
                flag_share=float(fl[ok].mean()) if has_flag else np.nan, **f7_shift(z, ok, mu, sd))
    for tag in tags:
        D = ctx["D"][tag]
        series, Zf = build(ctx, D)
        if tag == "clean_seed42":                                           # R0
            ref = E22.final_scalar(ctx, tag)
            if not np.allclose(series["final"], ref, atol=1e-12, equal_nan=True):
                raise SystemExit(f"STOP R0 {s}: final scalar differs from e22_test_oneshot.final_scalar")
        if part_c:
            D0, Dt = trimmed_distances(ctx["Z"][tag], D)
            series["refit0"] = build(ctx, D0, focal=False)[0]["final"]
            series["trim"] = build(ctx, Dt, focal=False)[0]["final"]
        sm = {k: PS.smoothed(ctx, v, CELL[0]) for k, v in series.items()}
        pn = {k: pneed_fn(v) for k, v in sm.items()}
        det = PS.d1_events(ctx, series["final"], CELL[0], CELL[1])
        tp, fp, nr, h = PS.score(ctx, det)
        want = ref_det(s, tag)                                              # R2 / R3
        if (int(tp), int(fp)) != want:
            raise SystemExit(f"STOP {'R3' if sset == 'test' else 'R2'} {s} {tag}: detector {(int(tp), int(fp))}, stored {want}")
        out["det"].append(dict(subject=s, set=sset, seed=tag, tp=int(tp), fp=int(fp), n_ref=int(nr), nonict_h=h))

        # ---- Part A, seed-dependent, label-free
        x, xr = series["final"], series["final_nodt"]
        mad = lambda v: np.median(np.abs(v[ok] - np.median(v[ok]))) + 1e-9          # noqa: E731
        mr = pd.Series(xr[ok]).groupby(fidx[ok]).median()
        mf = pd.Series(x[ok]).groupby(fidx[ok]).median()
        topf = mr[mr >= mr.quantile(0.75)].index
        T_after = (sm["final"] > np.nanquantile(sm["final"], 1 - CELL[1])) & ok
        T_before = (sm["final_nodt"] > np.nanquantile(sm["final_nodt"], 1 - CELL[1])) & ok
        cnt = np.bincount(np.nanargmax(Zf[T_after], axis=1), minlength=Zf.shape[1]) if T_after.any() else np.zeros(18, int)
        odd_pairs, odd_files = 0, 0
        for f in np.unique(fidx):
            mm = (fidx == f) & ok
            if mm.sum() < 10:
                continue
            k_ = int((np.nanmedian(Zf[mm], axis=0) > 3).sum()); odd_pairs += k_; odd_files += k_ > 0
        out["A"].append(dict(base, seed=tag,
                             drift_before=float((mr.quantile(.75) - mr.quantile(.25)) / mad(xr)),
                             drift_after=float((mf.quantile(.75) - mf.quantile(.25)) / mad(x)),
                             tail_topfiles_before=float(np.isin(fidx[T_before], topf).mean()) if T_before.any() else np.nan,
                             tail_topfiles_after=float(np.isin(fidx[T_after], topf).mean()) if T_after.any() else np.nan,
                             tail_top_ch=int(cnt.argmax()), tail_top_ch_share=float(cnt.max() / max(cnt.sum(), 1)),
                             odd_ch_file_pairs=odd_pairs, files_with_odd_ch=odd_files))

        # ---- Part B, per seizure
        for f in np.unique(fidx):
            m = np.flatnonzero(fidx == f); L = len(m)
            runs = PS._runs(ctx["ict"][m])
            for i, (a, b) in enumerate(runs):
                g, ge = m[a:b], m[max(0, a - PRE_W):min(L, b + POST_W)]
                r = dict(subject=s, set=sset, seed=tag, file=int(f), onset_s=a * WIN, dur_s=(b - a) * WIN,
                         from_start_s=a * WIN, to_end_s=(L - b) * WIN)
                for k, v in sm.items():
                    seg = v[ge]
                    r[f"pn_{k}"] = pn[k](np.nanmax(seg)) if np.isfinite(seg).any() else np.nan
                seg = sm["final"][g]
                r["pn_final_in"] = pn["final"](np.nanmax(seg)) if np.isfinite(seg).any() else np.nan
                okg = g[ok[g]]
                if len(okg):
                    gpk = okg[np.argmax(x[okg])]
                    r.update(ch_gt3_peak=int((Zf[gpk] > 3).sum()), top_ch_peak=int(np.nanargmax(Zf[gpk])),
                             n_ch_med_gt2=int((np.nanmedian(Zf[okg], axis=0) > 2).sum()))
                else:
                    r.update(ch_gt3_peak=np.nan, top_ch_peak=np.nan, n_ch_med_gt2=np.nan)
                r["flag_share"] = float(fl[g].mean()) if has_flag else np.nan
                others = [(c, d) for j, (c, d) in enumerate(runs) if j != i]
                r["gap_s"] = min(max(c - b, a - d) for c, d in others) * WIN if others else np.nan
                a_s, b_s = a * WIN, b * WIN
                r["caught"] = bool(any(h1 >= a_s - 30 and h0 <= b_s + 60 for h0, h1 in det.get(f, [])))
                out["B"].append(r)


# ----------------------------------------------------------------------------- summary
def summary(A, B, Dt, include_test, elapsed):
    L = ["# P3-A -- failure anatomy (descriptive, no gate), 4 seeds\n",
         "Reproduction gates R0 (final scalar = e22), R2 (non-test detector = E17b grid)"
         + (", R3 (test detector = look #6)" if include_test else "") + ", R4 (untrimmed refit) passed.\n",
         "Test rows (tier T-B) are test-informed and are logged in PERF_PHASE_RECORD section 3.\n"]
    det = Dt.groupby(["set", "seed"])[["tp", "fp", "n_ref", "nonict_h"]].sum()
    det["sens"] = det.tp / det.n_ref; det["fa_day"] = det.fp / det.nonict_h * 24
    L += ["## Frozen detector (reproduced)\n", "```", det.round(3).to_string(), "```"]

    num = A.drop(columns=["seed"]).groupby(["set", "subject"]).agg(
        lambda v: v.mean() if pd.api.types.is_numeric_dtype(v) else v.iloc[0])
    cols = ["hours", "files", "flag_share", "f7_clip_max", "f7_clip_feat", "f7_shift_maxabs", "f7_shift_feat",
            "drift_before", "drift_after", "tail_topfiles_before", "tail_topfiles_after", "tail_top_ch",
            "tail_top_ch_share", "files_with_odd_ch"]
    L += ["\n## Part A -- label-free, per subject (seed-dependent columns: 4-seed mean)\n", "```",
          num[[c for c in cols if c in num.columns]].round(3).to_string(), "```"]
    fcols = [c for c in num.columns if c.startswith("clip_") or c.startswith("shift_")]
    L += ["\nPer-feature clip share and median shift (training-SD units):\n", "```",
          num[fcols].round(3).to_string(), "```"]

    B = B.copy()
    for k in ("S1e", "S3e", "final_nodt"):
        B[f"resc_{k}"] = (B.pn_final > CELL[1]) & (B[f"pn_{k}"] <= CELL[1])
        B[f"loss_{k}"] = (B.pn_final <= CELL[1]) & (B[f"pn_{k}"] > CELL[1])
    if "pn_trim" in B.columns:
        B["resc_trim"] = (B.pn_refit0 > CELL[1]) & (B.pn_trim <= CELL[1])
        B["loss_trim"] = (B.pn_refit0 <= CELL[1]) & (B.pn_trim > CELL[1])
    agg = dict(n=("caught", "size"), caught=("caught", "sum"), dur=("dur_s", "median"),
               pn_med=("pn_final", "median"), pn_in_med=("pn_final_in", "median"))
    for p in (0.005, 0.01, 0.02, 0.05, 0.10):
        agg[f"le{p:g}"] = ("pn_final", lambda v, p=p: (v <= p).sum())
    for k in ("S1e", "S3e", "S6e", "S9e", "S12e", "Smean_e", "final_nodt"):
        agg[f"{k}_le.005"] = (f"pn_{k}", lambda v: (v <= CELL[1]).sum())
    for c in [c for c in B.columns if c.startswith("resc_") or c.startswith("loss_")]:
        agg[c] = (c, "sum")
    agg.update(ch_gt3=("ch_gt3_peak", "median"), ch_med2=("n_ch_med_gt2", "median"),
               flag=("flag_share", "median"), gap=("gap_s", "median"))
    per = B.groupby(["set", "subject", "seed"]).agg(**agg).groupby(["set", "subject"]).mean()
    tot = per.groupby("set").sum()
    show1 = ["n", "caught", "dur", "pn_med", "pn_in_med"] + [c for c in per.columns if c.startswith("le")]
    show2 = [c for c in per.columns if c.endswith("_le.005")]
    show3 = [c for c in per.columns if c.startswith("resc_") or c.startswith("loss_")] + ["ch_gt3", "ch_med2", "flag", "gap"]
    L += ["\n## Part B -- per seizure, aggregated per subject (4-seed mean; p_need = top-p needed, frozen = 0.005)\n",
          "Reachability (seizures with p_need <= p) ignores false alarms and merging: an upper bound, not a curve.\n",
          "```", per[show1].round(3).to_string(), "", "set totals:", tot[[c for c in show1 if c not in
                                                                         ("dur", "pn_med", "pn_in_med")]].round(2).to_string(), "```",
          "\nMembers alone and without the +-15 min correction (seizures with p_need <= 0.005):\n", "```",
          per[show2].round(2).to_string(), "", "set totals:", tot[show2].round(2).to_string(), "```",
          "\nRescued / lost vs the frozen scalar at top 0.5 % (trim: vs the untrimmed refit, non-test only; 0 on test = not computed), spatial extent, "
          "flagged share, gap to the nearest seizure (s):\n", "```", per[show3].round(2).to_string(), "",
          "set totals:", tot[[c for c in show3 if c.startswith("resc_") or c.startswith("loss_")]].round(2).to_string(), "```"]
    if include_test:
        m42 = B[(B.set == "test") & (B.seed == "clean_seed42") & ~B.caught]
        cls = pd.cut(m42.pn_final, [-1, CELL[1], 0.02, 0.10, 1.0],
                     labels=["<=0.005 (scoring/merge)", "0.005-0.02 (near)", "0.02-0.10 (mid)", ">0.10 (deep)"])
        L += ["\n## Missed test seizures, seed 42, by p_need class\n", "```",
              pd.crosstab(m42.subject, cls).to_string(), "```"]
    L.append(f"\nElapsed {elapsed:.0f} s.")
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--include-test", action="store_true")
    ap.add_argument("--smoke", action="store_true")
    a = ap.parse_args()
    t0 = time.time()
    nontest = ["chb01"] if a.smoke else list(E8.SUBJS)
    test = (["chb03"] if a.smoke else TEST) if a.include_test else []
    tags = ["clean_seed42"] if a.smoke else TAGS
    if set(nontest) & set(TEST):
        raise SystemExit("TEST GUARD")
    if test:
        print("This run reads test annotations (tier T-B): log it in PERF_PHASE_RECORD section 3.", flush=True)
    mu, sd = norm_constants(TRAIN[:2] if a.smoke else TRAIN)
    g17 = pd.read_csv(ROOT / "results" / "e17b_latent_family" / "grid_per_subject.csv")
    look6 = pd.read_csv(ROOT / "results" / "e22_test_oneshot" / "per_subject_seed.csv") if test else None

    def ref_nontest(s, tag):
        r = g17[(g17.subject == s) & (g17.score == f"{tag}|E17b") & (g17.smooth == CELL[0]) & np.isclose(g17.top, CELL[1])]
        if len(r) != 1:
            raise SystemExit(f"STOP R2 {s} {tag}: {len(r)} rows in the E17b grid")
        return int(r.tp.iloc[0]), int(r.fp.iloc[0])

    def ref_test(s, tag):
        r = look6[(look6.subject == s) & (look6.seed == tag) & (look6.stage == "detector")]
        if len(r) != 1:
            raise SystemExit(f"STOP R3 {s} {tag}: {len(r)} rows in look #6")
        return int(r.tp.iloc[0]), int(r.fp.iloc[0])

    out = dict(A=[], B=[], det=[])
    for s in nontest:
        analyse(PS.subject_context(s), s, "non-test", tags, mu, sd, ref_nontest, True, out)
        print(f"{s}: done ({time.time()-t0:.0f}s)", flush=True)
    for s in test:
        analyse(E22.test_context(s), s, "test", tags, mu, sd, ref_test, False, out)
        print(f"{s}: done ({time.time()-t0:.0f}s)", flush=True)
    A, B, Dt = pd.DataFrame(out["A"]), pd.DataFrame(out["B"]), pd.DataFrame(out["det"])
    od = OUT / "smoke" if a.smoke else OUT
    od.mkdir(parents=True, exist_ok=True)
    A.to_csv(od / "labelfree.csv", index=False); B.to_csv(od / "seizures.csv", index=False)
    Dt.to_csv(od / "detector_check.csv", index=False)
    text = summary(A, B, Dt, bool(test), time.time() - t0)
    (od / "SUMMARY.md").write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
