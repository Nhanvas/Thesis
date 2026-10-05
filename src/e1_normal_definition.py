#!/usr/bin/env python
"""
e1_normal_definition.py -- does defining "normal" as ALL non-seizure EEG (instead of windows
that pass the +-5 SD rule) make an unsupervised anomaly model separate seizures from the
high-amplitude non-seizure windows?

Approved 2026-10-05 (gate fixed before any number was read):
  primary model  GaussianMixture, k = 8 components, full covariance
  variants       (a) clean : trained on non-ictal, non-buffer, non-flagged, non-signal-loss windows
                 (b) all   : trained on non-ictal, non-buffer, non-signal-loss windows (flagged included)
  protocol       leave-one-subject-out over the 15 non-test subjects (12 training + 3 validation),
                 features from results/raw_eeg_view/cache (no model output used anywhere)
  GATE (k = 8)   G1  mean over subjects of AUROC(seizure vs flagged non-seizure): (b) - (a) >= +0.10,
                     and (b) > (a) in >= 10 of 15 subjects
                 G2  mean AUROC(seizure vs clean background): (b) >= (a) - 0.03
                 G3  best pooled event sensitivity with FA/day <= 25 on the threshold-detector grid:
                     (b) - (a) >= +0.10
                 E1 PASSES only if G1, G2 and G3 all pass.
  descriptive    k = 32 (capacity), a label-permutation null, seizures shorter than 20 s.

TEST GUARD: refuses every test subject. Labels (is_ictal) are used only to train-exclude seizures
of the training folds and to score the held-out subject. Thresholds are label-free quantiles of the
held-out subject's own score.
Writes only results/e1_normal_definition/.
"""
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score
from sklearn.mixture import GaussianMixture

ROOT = Path(__file__).resolve().parents[1]
for _p in (ROOT / "src",):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))
import szcore_eval as SE  # noqa: E402

WIN = 4
SUBJS = ["chb01", "chb02", "chb04", "chb05", "chb07", "chb08", "chb09", "chb12",
         "chb19", "chb20", "chb21", "chb23", "chb10", "chb11", "chb22"]
TEST = set(SE.TEST_SUBJS)
assert not (set(SUBJS) & TEST), "TEST GUARD"

CACHE = ROOT / "results" / "raw_eeg_view" / "cache"
OUT = ROOT / "results" / "e1_normal_definition"
OUT.mkdir(parents=True, exist_ok=True)

STORED = ["mobility", "complexity", "linelen_sd", "rel_d05_4", "rel_4_8", "rel_8_13",
          "rel_13_30", "rel_30_60", "muscle_20_60", "slow_05_2", "spec_entropy",
          "rhythmicity", "kurtosis"]
FEATS = [f"{n}_{a}" for n in STORED for a in ("med", "max")] + ["frac_ch_sd_gt3med"]
LOG_FEATS = {"linelen_sd_med", "linelen_sd_max", "complexity_med", "complexity_max"}
SIGNED_LOG = {"kurtosis_med", "kurtosis_max"}
PER_SUBJ_TRAIN = 5000
KS = [8, 32]
PRIMARY_K = 8
SMOOTH = [1, 3, 5, 15]
TOPS = [0.05, 0.02, 0.01, 0.005, 0.002, 0.001]
RNG = np.random.default_rng(0)


def load(subj):
    if subj in TEST:
        raise SystemExit(f"TEST GUARD: {subj}")
    z = np.load(CACHE / f"{subj}.npz", allow_pickle=True)
    d = {k: z[k] for k in ("is_ictal", "is_buffer", "is_artifact", "is_signal_loss",
                           "sz_dur", "file_idx", "win_idx")}
    X = []
    for f in FEATS[:-1]:
        v = z[f].astype(np.float64)
        if f in LOG_FEATS:
            v = np.log(np.maximum(v, 1e-12))
        elif f in SIGNED_LOG:
            v = np.sign(v) * np.log1p(np.abs(v))
        X.append(v)
    sd = z["sd_uV"].astype(np.float64)                       # label-free, as in raw_eeg_view
    med = np.median(sd, axis=0)
    X.append((sd > 3.0 * med[None, :]).mean(axis=1))
    X = np.column_stack(X)
    ok = ~d["is_signal_loss"]
    # per-subject robust standardisation over all of this subject's windows (label-free)
    c = np.median(X[ok], axis=0)
    s = np.subtract(*np.percentile(X[ok], [75, 25], axis=0))
    s[s < 1e-9] = 1.0
    d["X"] = np.clip((X - c) / s, -10, 10)
    d["subj"] = subj
    # contiguity check: windows of one file must be consecutive and in order
    for f in np.unique(d["file_idx"]):
        w = d["win_idx"][d["file_idx"] == f]
        if not np.all(np.diff(w) == 1):
            raise SystemExit(f"{subj}: file {f} windows are not contiguous; event scoring would be wrong")
    return d


def train_mask(d, variant):
    m = ~d["is_ictal"] & ~d["is_buffer"] & ~d["is_signal_loss"]
    if variant == "clean":
        m &= ~d["is_artifact"]
    return m


def fit(train, variant, k):
    parts = []
    for d in train:
        idx = np.flatnonzero(train_mask(d, variant))
        if len(idx) > PER_SUBJ_TRAIN:
            idx = RNG.choice(idx, PER_SUBJ_TRAIN, replace=False)
        parts.append(d["X"][idx])
    Xt = np.vstack(parts)
    g = GaussianMixture(n_components=k, covariance_type="full", reg_covar=1e-3,
                        max_iter=300, random_state=0).fit(Xt)
    return g, len(Xt)


def auc(score, pos, neg):
    if pos.sum() == 0 or neg.sum() == 0:
        return np.nan
    y = np.r_[np.ones(pos.sum()), np.zeros(neg.sum())]
    return roc_auc_score(y, np.r_[score[pos], score[neg]])


def events_for_file(sm, above, merge_s=90):
    ev, i, n = [], 0, len(above)
    while i < n:
        if above[i]:
            j = i
            while j < n and above[j]:
                j += 1
            ev.append((i * WIN, j * WIN)); i = j
        else:
            i += 1
    out = []
    for a, b in ev:
        if out and a - out[-1][1] <= merge_s:
            out[-1] = (out[-1][0], b)
        else:
            out.append((a, b))
    return out


def ref_for_file(ictal):
    ref, i, n = [], 0, len(ictal)
    while i < n:
        if ictal[i]:
            j = i
            while j < n and ictal[j]:
                j += 1
            ref.append((i * WIN, j * WIN)); i = j
        else:
            i += 1
    return ref


def event_grid(d, score):
    """threshold detector, per-file smoothing, label-free per-subject quantile threshold."""
    rows = []
    sc = score.copy()
    sc[d["is_signal_loss"]] = np.nan
    files = np.unique(d["file_idx"])
    for w in SMOOTH:
        sm = np.full_like(sc, np.nan)
        for f in files:
            m = d["file_idx"] == f
            sm[m] = pd.Series(sc[m]).rolling(w, min_periods=1, center=True).mean().values
        valid = ~np.isnan(sm)
        for p in TOPS:
            thr = np.quantile(sm[valid], 1 - p)
            # files laid end to end with a 600 s gap so no event or merge crosses a file
            ref_all, hyp_all, off, tp_short, nref_short = [], [], 0, 0, 0
            for f in files:
                m = d["file_idx"] == f
                ictal = d["is_ictal"][m]
                above = np.nan_to_num(sm[m], nan=-np.inf) > thr
                hyp = events_for_file(sm[m], above)
                ref = ref_for_file(ictal)
                durs = d["sz_dur"][m]
                for (a, b) in ref:                      # short seizures, overlap rule, descriptive
                    if durs[a // WIN] < 20:
                        nref_short += 1
                        tp_short += any(hb >= a - 30 and ha <= b + 60 for ha, hb in hyp)
                ref_all += [(a + off, b + off) for a, b in ref]
                hyp_all += [(a + off, b + off) for a, b in hyp]
                off += int(m.sum()) * WIN + 600
            nonict_h = float((~d["is_ictal"] & ~d["is_signal_loss"]).sum()) * WIN / 3600
            r = SE.score_szcore(ref_all, hyp_all, off, nonict_h)
            tp, fp, nref = int(r["tp"]), int(r["fp"]), int(r["n_ref"])
            rows.append(dict(smooth=w, top=p, tp=tp, fp=fp, n_ref=nref,
                             tp_short=tp_short, n_ref_short=nref_short))
    return rows


def main():
    t0 = time.time()
    data = {s: load(s) for s in SUBJS}
    for s, d in data.items():
        print(f"{s}: windows {len(d['X'])}, ictal {d['is_ictal'].sum()}, "
              f"flagged {d['is_artifact'].sum()}, files {len(np.unique(d['file_idx']))}", flush=True)
    per_subj, grid_rows = [], []
    for k in KS:
        for variant in ("clean", "all"):
            for s in SUBJS:
                train = [data[t] for t in SUBJS if t != s]
                g, n_train = fit(train, variant, k)
                d = data[s]
                score = -g.score_samples(d["X"])
                ict = d["is_ictal"] & ~d["is_signal_loss"]
                base = ~d["is_ictal"] & ~d["is_buffer"] & ~d["is_signal_loss"]
                flag = base & d["is_artifact"]
                bg = base & ~d["is_artifact"]
                perm = RNG.permutation(ict[~d["is_signal_loss"]])
                null = auc(score[~d["is_signal_loss"]], perm, ~perm)
                per_subj.append(dict(k=k, variant=variant, subject=s, n_train=n_train,
                                     auc_sz_vs_flagged=auc(score, ict, flag),
                                     auc_sz_vs_bg=auc(score, ict, bg),
                                     auc_flagged_vs_bg=auc(score, flag, bg),
                                     auc_null_perm=null))
                for r in event_grid(d, score):
                    r.update(k=k, variant=variant, subject=s,
                             nonict_h=float((~d["is_ictal"] & ~d["is_signal_loss"]).sum()) * WIN / 3600)
                    grid_rows.append(r)
                print(f"k={k} {variant:5s} {s}: sz_vs_flag={per_subj[-1]['auc_sz_vs_flagged']:.3f} "
                      f"sz_vs_bg={per_subj[-1]['auc_sz_vs_bg']:.3f} ({time.time()-t0:.0f}s)", flush=True)

    ps = pd.DataFrame(per_subj)
    gr = pd.DataFrame(grid_rows)
    ps.to_csv(OUT / "per_subject_auroc.csv", index=False)
    gr.to_csv(OUT / "event_grid_per_subject.csv", index=False)
    pooled = (gr.groupby(["k", "variant", "smooth", "top"])
                [["tp", "fp", "n_ref", "tp_short", "n_ref_short", "nonict_h"]].sum().reset_index())
    pooled["sens"] = pooled.tp / pooled.n_ref
    pooled["fa_day"] = pooled.fp / pooled.nonict_h * 24
    pooled["sens_short"] = pooled.tp_short / pooled.n_ref_short.replace(0, np.nan)
    pooled.to_csv(OUT / "event_grid_pooled.csv", index=False)

    def best(k, v, cap):
        q = pooled[(pooled.k == k) & (pooled.variant == v) & (pooled.fa_day <= cap)]
        return (float(q.sens.max()), q.loc[q.sens.idxmax()].to_dict()) if len(q) else (0.0, None)

    lines = ["# E1 -- normal definition test (LOSO, 15 non-test subjects)\n"]
    summ = ps.groupby(["k", "variant"])[["auc_sz_vs_flagged", "auc_sz_vs_bg",
                                         "auc_flagged_vs_bg", "auc_null_perm"]].mean().round(4)
    lines += ["## Mean AUROC over subjects\n", "```", summ.to_string(), "```\n"]
    for k in KS:
        a = ps[(ps.k == k) & (ps.variant == "clean")].set_index("subject")
        b = ps[(ps.k == k) & (ps.variant == "all")].set_index("subject")
        dflag = (b.auc_sz_vs_flagged - a.auc_sz_vs_flagged)
        dbg = (b.auc_sz_vs_bg - a.auc_sz_vs_bg)
        s_a25, r_a25 = best(k, "clean", 25); s_b25, r_b25 = best(k, "all", 25)
        s_a15, _ = best(k, "clean", 15); s_b15, _ = best(k, "all", 15)
        g1 = dflag.mean() >= 0.10 and (dflag > 0).sum() >= 10
        g2 = dbg.mean() >= -0.03
        g3 = (s_b25 - s_a25) >= 0.10
        tag = "PRIMARY (gated)" if k == PRIMARY_K else "descriptive"
        lines += [f"## k = {k} -- {tag}\n",
                  "Per subject, AUROC seizure vs flagged: clean / all / difference\n", "```",
                  pd.DataFrame({"clean": a.auc_sz_vs_flagged, "all": b.auc_sz_vs_flagged,
                                "diff": dflag, "sz_vs_bg_clean": a.auc_sz_vs_bg,
                                "sz_vs_bg_all": b.auc_sz_vs_bg}).round(4).to_string(), "```",
                  f"- G1: mean diff {dflag.mean():+.4f}, subjects improved {(dflag > 0).sum()}/15 -> "
                  f"{'PASS' if g1 else 'FAIL'}",
                  f"- G2: mean diff seizure vs background {dbg.mean():+.4f} -> {'PASS' if g2 else 'FAIL'}",
                  f"- G3: best sens at FA/day <= 25: clean {s_a25:.3f} ({r_a25}), all {s_b25:.3f} ({r_b25}) "
                  f"-> {'PASS' if g3 else 'FAIL'}",
                  f"- (info) best sens at FA/day <= 15: clean {s_a15:.3f}, all {s_b15:.3f}"]
        if k == PRIMARY_K:
            lines.append(f"\n**E1 VERDICT: {'PASS' if (g1 and g2 and g3) else 'FAIL'}**\n")
    lines += ["## Pooled event grid (all k, both variants)\n", "```",
              pooled.round(4).to_string(index=False), "```",
              f"\nElapsed {time.time()-t0:.0f} s."]
    (OUT / "SUMMARY.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines[:60]))


if __name__ == "__main__":
    main()
