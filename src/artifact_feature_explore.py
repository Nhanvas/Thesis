#!/usr/bin/env python
"""
artifact_feature_explore.py -- can any amplitude-free feature separate ICTAL windows from windows
flagged by the +-5 SD peak rule?  (diagnostic on TRAINING patients only; no model, no scoring)

Save as  F:\\Study\\Thesis\\Code\\src\\artifact_feature_explore.py  and run from the repo root:
    python src/artifact_feature_explore.py

Why training patients: validation and test labels are not used to design anything. Seizure labels are
used here ONLY to measure separability (AUROC) -- no threshold is fitted or saved by this script.

Definitions (same as continuous_eval.compute_artifact_flags, but on the whole-file-filtered signal, so
a few borderline windows may differ): a window is "flagged" if any sample on any of the 18 channels
exceeds that channel's artifact threshold (stats.json artifact_thresh_uV). Ictal and post-seizure-buffer
windows are never counted as flagged background.

Groups: ictal | flagged (non-ictal, non-buffer) | background (unflagged, non-ictal, non-buffer).
Features (per window; per-channel values aggregated across the 18 channels):
  crest_max, crest_med   peak / RMS
  kurt_max, kurt_med     kurtosis
  mob_med, cx_med        Hjorth mobility, complexity
  sent_med               spectral entropy 0.5-60 Hz
  frac_rms2              share of channels with RMS > 2 x the channel's background SD
  rms_med_sd             median channel RMS in background-SD units
  coh_mean               mean |correlation| between channels
Outputs: results/continuous_eval/artifact_feature_explore/{features.csv, summary.md}
"""
import json
import sys
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.signal import welch
from scipy.stats import kurtosis
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import continuous_eval as CE   # noqa: E402

P = CE.P
SUBJS = ["chb12", "chb08", "chb20", "chb05"]      # training patients: 58 seizures, ~110 h
OUT = CE.OUT_DIR / "artifact_feature_explore"
FEATS = ["crest_max", "crest_med", "kurt_max", "kurt_med", "mob_med", "cx_med", "sent_med",
         "frac_rms2", "rms_med_sd", "coh_mean"]
CH = 200


def feats(x, ch_std):
    """x: [n,18,T] float64 in volts."""
    n = x.shape[0]
    rms = np.sqrt((x ** 2).mean(axis=2)) + 1e-18
    crest = np.abs(x).max(axis=2) / rms
    kur = kurtosis(x, axis=2, fisher=True)
    dx = np.diff(x, axis=2)
    ddx = np.diff(dx, axis=2)
    v0, v1, v2 = x.var(axis=2) + 1e-30, dx.var(axis=2) + 1e-30, ddx.var(axis=2) + 1e-30
    mob = np.sqrt(v1 / v0)
    cx = np.sqrt(v2 / v1) / mob
    fr, psd = welch(x, fs=256, nperseg=256, axis=2)
    sel = (fr >= 0.5) & (fr <= 60)
    p = psd[:, :, sel]
    p = p / (p.sum(axis=2, keepdims=True) + 1e-30)
    sent = -(p * np.log(p + 1e-30)).sum(axis=2) / np.log(p.shape[2])
    xc = x - x.mean(axis=2, keepdims=True)
    xn = xc / (np.sqrt((xc ** 2).sum(axis=2, keepdims=True)) + 1e-30)
    C = np.einsum("nct,ndt->ncd", xn, xn)
    off = ~np.eye(18, dtype=bool)
    coh = np.abs(C[:, off]).mean(axis=1)
    rs = rms / ch_std[None, :]
    return np.column_stack([crest.max(axis=1), np.median(crest, axis=1), kur.max(axis=1), np.median(kur, axis=1),
                            np.median(mob, axis=1), np.median(cx, axis=1), np.median(sent, axis=1),
                            (rs > 2).mean(axis=1), np.median(rs, axis=1), coh])


def process(subj):
    stats = json.loads((CE.PROCESSED_DIR / f"{subj}_stats.json").read_text())
    thr = np.asarray(stats["artifact_thresh_uV"], dtype=np.float64) * 1e-6
    ch_std = np.asarray(stats["ch_std_uV"], dtype=np.float64) * 1e-6
    rows = []
    for edf in CE.list_files(subj):
        t0 = time.time()
        try:
            filtered, nw = CE.filter_file(CE.edf_path(subj, edf["fname"]))
        except RuntimeError as err:
            print(f"SKIP {subj}/{edf['fname']}: {err}", flush=True)
            continue
        secs = nw * CE.WIN_SEC
        labels = P.build_labels(secs, edf["seizures"])
        buf = P.build_buffer_mask(secs, edf["seizures"])
        wl = labels.reshape(nw, CE.WIN_SEC).max(axis=1) == 1
        wb = buf.reshape(nw, CE.WIN_SEC).any(axis=1)
        for s in range(0, nw, CH):
            e = min(s + CH, nw)
            x = filtered[s:e].astype(np.float64)
            flag = np.any(np.abs(x).max(axis=2) > thr[None, :], axis=1)
            f = feats(x, ch_std)
            d = pd.DataFrame(f, columns=FEATS)
            d["subject"], d["file"], d["flag_rule"] = subj, edf["fname"], flag
            d["ictal"], d["buffer"] = wl[s:e], wb[s:e] & ~wl[s:e]
            rows.append(d)
        del filtered
        print(f"{subj}/{edf['fname']} {nw} windows {time.time() - t0:.0f}s", flush=True)
    return pd.concat(rows, ignore_index=True)


def auc(y, s):
    return float(roc_auc_score(y, s)) if 0 < y.sum() < len(y) else float("nan")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    parts = []
    for s in SUBJS:
        sp = OUT / f"features_{s}.csv"
        if sp.exists():
            parts.append(pd.read_csv(sp))
        else:
            d = process(s)
            d.to_csv(sp, index=False)
            parts.append(d)
    df = pd.concat(parts, ignore_index=True)
    df.to_csv(OUT / "features.csv", index=False)
    df["group"] = np.where(df.ictal, "ictal", np.where(df.buffer, "buffer",
                           np.where(df.flag_rule, "flagged", "background")))
    L = ["# Ictal vs flagged windows -- training patients " + ", ".join(SUBJS), "",
         "## Windows per group", "", df.groupby(["subject", "group"]).size().unstack(fill_value=0).to_string(), ""]
    ic = df[df.group == "ictal"]
    L += [f"Share of ictal windows that the +-5 SD peak rule would flag: "
          f"{ic.flag_rule.mean():.3f} (per subject: "
          + ", ".join(f"{s} {g.flag_rule.mean():.2f}" for s, g in ic.groupby('subject')) + ")", ""]
    L += ["## AUROC, ictal (positive) vs flagged non-ictal windows. 0.5 = no separation; "
          "'sign ok' = same side of 0.5 in every subject", "",
          "| feature | " + " | ".join(SUBJS) + " | pooled | sign ok | pooled vs background |",
          "|---|" + "---|" * (len(SUBJS) + 3)]
    for f in FEATS:
        per, sg = [], []
        for s in SUBJS:
            d = df[(df.subject == s) & df.group.isin(["ictal", "flagged"])]
            a = auc((d.group == "ictal").astype(int).values, d[f].values)
            per.append(a)
            sg.append(a > 0.5)
        d = df[df.group.isin(["ictal", "flagged"])]
        pa = auc((d.group == "ictal").astype(int).values, d[f].values)
        db = df[df.group.isin(["ictal", "background"])]
        pb = auc((db.group == "ictal").astype(int).values, db[f].values)
        ok = "yes" if (all(sg) or not any(sg)) else "no"
        L.append(f"| {f} | " + " | ".join(f"{a:.3f}" for a in per) + f" | {pa:.3f} | {ok} | {pb:.3f} |")
    L += ["", "## Leave-one-subject-out logistic regression on all 10 features (diagnostic upper bound for a "
              "supervised combination; any rule would do no better)", "",
          "| held-out subject | AUROC ictal vs flagged | AUROC ictal vs flagged+background |", "|---|---|---|"]
    res = []
    for s in SUBJS:
        tr = df[(df.subject != s) & df.group.isin(["ictal", "flagged"])]
        te = df[(df.subject == s) & df.group.isin(["ictal", "flagged"])]
        te2 = df[(df.subject == s) & df.group.isin(["ictal", "flagged", "background"])]
        sc = StandardScaler().fit(tr[FEATS])
        clf = LogisticRegression(class_weight="balanced", max_iter=2000).fit(sc.transform(tr[FEATS]),
                                                                           (tr.group == "ictal").astype(int))
        a1 = auc((te.group == "ictal").astype(int).values, clf.decision_function(sc.transform(te[FEATS])))
        a2 = auc((te2.group == "ictal").astype(int).values, clf.decision_function(sc.transform(te2[FEATS])))
        res.append(a1)
        L.append(f"| {s} | {a1:.3f} | {a2:.3f} |")
    L += ["", f"Mean LOSO AUROC ictal vs flagged: {np.nanmean(res):.3f}.", "",
          "Pre-set reading: a usable veto needs LOSO AUROC >= 0.80 AND at least one single feature with "
          "pooled AUROC >= 0.75 or <= 0.25 and 'sign ok' = yes. Otherwise the artifact-filtering lever is "
          "closed with this evidence. No threshold is derived here."]
    (OUT / "summary.md").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()