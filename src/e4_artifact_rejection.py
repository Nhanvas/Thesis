#!/usr/bin/env python
"""
e4_artifact_rejection.py -- two-stage design that keeps seizure detection unsupervised:
stage 1 an anomaly score learned from non-seizure data (E1 'clean' GMM, k = 8, the stand-in
for the GAE); stage 2 an ARTIFACT model trained only on NON-SEIZURE windows of the training
patients (positive = window flagged by the +-5 SD rule, negative = clean window). No seizure
window is ever used to train either stage; the label usage is the same as the GAE's own
training (seizures and the 4 h post-seizure buffer of the training patients are excluded).

Fixed before the run (one configuration, no tuning):
  artifact model  HistGradientBoostingClassifier(max_iter=300, learning_rate=0.05,
                  class_weight="balanced", random_state=0), 27 features, up to 5,000
                  non-ictal non-buffer windows per training subject
  combination     S = r_a * (1 - p_art), r_a = within-subject percentile rank of the anomaly
                  score (label-free), p_art = artifact probability
  protocol        LOSO over the 15 non-test subjects, E1 cache, E1 threshold detector, SzCORE
GATE (A0 = anomaly score alone, recomputed in this run):
  J1  best pooled sensitivity with FA/day <= 25:  S >= A0 + 0.10
  J2  mean AUROC(seizure vs flagged): S >= A0 + 0.08, and S > A0 in >= 10 of 15 subjects
  J3  mean AUROC(seizure vs clean background): S >= A0 - 0.03
  E4 PASSES only if J1, J2 and J3 all pass.
Descriptive: hard veto (p_art > 0.5 -> lowest score), artifact-model quality, the share of
seizure windows the artifact model calls artifact.
TEST GUARD inherited from e1_normal_definition. Writes only results/e4_artifact_rejection/.
"""
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import rankdata
from sklearn.ensemble import HistGradientBoostingClassifier

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import e1_normal_definition as E1  # noqa: E402

OUT = ROOT / "results" / "e4_artifact_rejection"
OUT.mkdir(parents=True, exist_ok=True)
RNG = np.random.default_rng(0)


def pct_rank(x, ok):
    r = np.zeros_like(x, dtype=float)
    r[ok] = (rankdata(x[ok]) - 1) / max(ok.sum() - 1, 1)
    return r


def main():
    t0 = time.time()
    data = {s: E1.load(s) for s in E1.SUBJS}
    per, grid = [], []
    for s in E1.SUBJS:
        train = [data[t] for t in E1.SUBJS if t != s]
        gmm, _ = E1.fit(train, "clean", 8)
        Xs, ys = [], []
        for d in train:
            idx = np.flatnonzero(~d["is_ictal"] & ~d["is_buffer"] & ~d["is_signal_loss"])
            if len(idx) > E1.PER_SUBJ_TRAIN:
                idx = RNG.choice(idx, E1.PER_SUBJ_TRAIN, replace=False)
            Xs.append(d["X"][idx]); ys.append(d["is_artifact"][idx].astype(int))
        art = HistGradientBoostingClassifier(max_iter=300, learning_rate=0.05,
                                             class_weight="balanced", random_state=0)
        art.fit(np.vstack(Xs), np.concatenate(ys))

        d = data[s]
        ok = ~d["is_signal_loss"]
        a0 = -gmm.score_samples(d["X"])
        p = art.predict_proba(d["X"])[:, 1]
        ra = pct_rank(a0, ok)
        S = ra * (1.0 - p)
        V = ra.copy(); V[p > 0.5] = 0.0
        ict = d["is_ictal"] & ok
        base = ~d["is_ictal"] & ~d["is_buffer"] & ok
        flag, bg = base & d["is_artifact"], base & ~d["is_artifact"]
        row = dict(subject=s,
                   A0_sz_flag=E1.auc(a0, ict, flag), A0_sz_bg=E1.auc(a0, ict, bg),
                   S_sz_flag=E1.auc(S, ict, flag), S_sz_bg=E1.auc(S, ict, bg),
                   V_sz_flag=E1.auc(V, ict, flag), V_sz_bg=E1.auc(V, ict, bg),
                   art_auc_flag_vs_bg=E1.auc(p, flag, bg),
                   art_auc_flag_vs_sz=E1.auc(p, flag, ict),
                   sz_windows_called_artifact=float((p[ict] > 0.5).mean()) if ict.any() else np.nan,
                   flagged_called_artifact=float((p[flag] > 0.5).mean()) if flag.any() else np.nan)
        per.append(row)
        nh = float((~d["is_ictal"] & ok).sum()) * E1.WIN / 3600
        for name, sc in (("A0", a0), ("S", S), ("V", V)):
            for r in E1.event_grid(d, sc):
                r.update(subject=s, score=name, nonict_h=nh); grid.append(r)
        print(f"{s}: A0 {row['A0_sz_flag']:.3f} -> S {row['S_sz_flag']:.3f} | sz called artifact "
              f"{row['sz_windows_called_artifact']:.2f} ({time.time()-t0:.0f}s)", flush=True)

    ps = pd.DataFrame(per).set_index("subject")
    gr = pd.DataFrame(grid)
    ps.to_csv(OUT / "per_subject.csv")
    gr.to_csv(OUT / "event_grid_per_subject.csv", index=False)
    pooled = (gr.groupby(["score", "smooth", "top"])
                [["tp", "fp", "n_ref", "nonict_h"]].sum().reset_index())
    pooled["sens"] = pooled.tp / pooled.n_ref
    pooled["fa_day"] = pooled.fp / pooled.nonict_h * 24
    pooled.to_csv(OUT / "event_grid_pooled.csv", index=False)

    def best(name, cap):
        q = pooled[(pooled.score == name) & (pooled.fa_day <= cap)]
        return (float(q.sens.max()), q.loc[q.sens.idxmax()][["smooth", "top", "tp", "fp", "fa_day"]].to_dict()) \
            if len(q) else (0.0, None)

    bA, rA = best("A0", 25); bS, rS = best("S", 25); bV, rV = best("V", 25)
    j1 = bS >= bA + 0.10
    d_flag = ps.S_sz_flag - ps.A0_sz_flag
    j2 = d_flag.mean() >= 0.08 and (d_flag > 0).sum() >= 10
    j3 = ps.S_sz_bg.mean() >= ps.A0_sz_bg.mean() - 0.03
    lines = ["# E4 -- anomaly score + artifact model trained on non-seizure windows only (LOSO)\n",
             "```", ps.round(4).to_string(), "```",
             f"\nMeans: A0 sz/flag {ps.A0_sz_flag.mean():.4f}, S sz/flag {ps.S_sz_flag.mean():.4f}, "
             f"V sz/flag {ps.V_sz_flag.mean():.4f}; A0 sz/bg {ps.A0_sz_bg.mean():.4f}, S sz/bg {ps.S_sz_bg.mean():.4f}",
             f"Artifact model: flagged vs bg {ps.art_auc_flag_vs_bg.mean():.4f}; flagged vs seizure "
             f"{ps.art_auc_flag_vs_sz.mean():.4f}; seizure windows called artifact {ps.sz_windows_called_artifact.mean():.3f}\n",
             f"- J1: best sens at FA/day <= 25: A0 {bA:.3f} {rA} | S {bS:.3f} {rS} -> {'PASS' if j1 else 'FAIL'}",
             f"- J2: mean diff sz/flag {d_flag.mean():+.4f}, improved {(d_flag > 0).sum()}/15 -> {'PASS' if j2 else 'FAIL'}",
             f"- J3: sz/bg A0 {ps.A0_sz_bg.mean():.4f} vs S {ps.S_sz_bg.mean():.4f} -> {'PASS' if j3 else 'FAIL'}",
             f"- (descriptive) hard veto V: best sens at FA/day <= 25 = {bV:.3f} {rV}",
             f"- (info) best at <= 15: A0 {best('A0', 15)[0]:.3f}, S {best('S', 15)[0]:.3f}, V {best('V', 15)[0]:.3f}",
             f"\n**E4 VERDICT: {'PASS' if (j1 and j2 and j3) else 'FAIL'}**\n",
             "## Pooled event grid\n", "```", pooled.round(4).to_string(index=False), "```",
             f"\nElapsed {time.time()-t0:.0f} s."]
    (OUT / "SUMMARY.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines[:35]))


if __name__ == "__main__":
    main()
