#!/usr/bin/env python
"""
e3_supervised_loso.py -- how far does a patient-independent SUPERVISED classifier on the same
27 label-free window features get, under exactly the protocol of E1 (LOSO over the 15 non-test
subjects, same cache, same threshold detector, same SzCORE scoring)?

Purpose: decide whether separating seizures from high-amplitude non-seizure windows needs
seizure knowledge (labels of the training patients), after E1 showed that redefining "normal"
does not do it in an unsupervised model.

One configuration, fixed before the run (no tuning):
  HistGradientBoostingClassifier(max_iter=300, learning_rate=0.05, class_weight="balanced",
  random_state=0); training windows per fold = every ictal window of the 14 training subjects
  + up to 5,000 non-ictal, non-buffer, non-signal-loss windows per subject (flagged included).
GATE (fixed before the run), against E1's unsupervised reference (k=8 clean, best 0.340 / all 0.372):
  H1  best pooled event sensitivity with FA/day <= 25  >= 0.52
  H2  mean over subjects of AUROC(seizure vs flagged)  >= 0.85
  H3  AUROC(seizure vs flagged) above E1 k=8 clean in >= 10 of 15 subjects
  E3 PASSES only if H1, H2 and H3 all pass.
TEST GUARD inherited from e1_normal_definition (refuses every test subject).
Writes only results/e3_supervised_loso/.
"""
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import e1_normal_definition as E1  # noqa: E402  (load, auc, event_grid, SUBJS, TEST guard)

OUT = ROOT / "results" / "e3_supervised_loso"
OUT.mkdir(parents=True, exist_ok=True)
E1_PS = ROOT / "results" / "e1_normal_definition" / "per_subject_auroc.csv"
RNG = np.random.default_rng(0)


def main():
    t0 = time.time()
    ref = pd.read_csv(E1_PS)
    ref = ref[(ref.k == 8) & (ref.variant == "clean")].set_index("subject")
    data = {s: E1.load(s) for s in E1.SUBJS}
    per_subj, grid_rows = [], []
    for s in E1.SUBJS:
        Xs, ys = [], []
        for t in E1.SUBJS:
            if t == s:
                continue
            d = data[t]
            pos = np.flatnonzero(d["is_ictal"] & ~d["is_signal_loss"])
            neg = np.flatnonzero(~d["is_ictal"] & ~d["is_buffer"] & ~d["is_signal_loss"])
            if len(neg) > E1.PER_SUBJ_TRAIN:
                neg = RNG.choice(neg, E1.PER_SUBJ_TRAIN, replace=False)
            Xs += [d["X"][pos], d["X"][neg]]
            ys += [np.ones(len(pos)), np.zeros(len(neg))]
        clf = HistGradientBoostingClassifier(max_iter=300, learning_rate=0.05,
                                             class_weight="balanced", random_state=0)
        clf.fit(np.vstack(Xs), np.concatenate(ys))
        d = data[s]
        score = clf.predict_proba(d["X"])[:, 1]
        ict = d["is_ictal"] & ~d["is_signal_loss"]
        base = ~d["is_ictal"] & ~d["is_buffer"] & ~d["is_signal_loss"]
        flag, bg = base & d["is_artifact"], base & ~d["is_artifact"]
        ok = ~d["is_signal_loss"]
        perm = RNG.permutation(ict[ok])
        per_subj.append(dict(subject=s, auc_sz_vs_flagged=E1.auc(score, ict, flag),
                             auc_sz_vs_bg=E1.auc(score, ict, bg),
                             auc_flagged_vs_bg=E1.auc(score, flag, bg),
                             auc_null_perm=E1.auc(score[ok], perm, ~perm),
                             e1_clean_sz_vs_flagged=float(ref.loc[s, "auc_sz_vs_flagged"])))
        for r in E1.event_grid(d, score):
            r.update(subject=s,
                     nonict_h=float((~d["is_ictal"] & ~d["is_signal_loss"]).sum()) * E1.WIN / 3600)
            grid_rows.append(r)
        print(f"{s}: sz_vs_flag={per_subj[-1]['auc_sz_vs_flagged']:.3f} "
              f"(E1 {per_subj[-1]['e1_clean_sz_vs_flagged']:.3f})  ({time.time()-t0:.0f}s)", flush=True)

    ps = pd.DataFrame(per_subj).set_index("subject")
    gr = pd.DataFrame(grid_rows)
    ps.to_csv(OUT / "per_subject_auroc.csv")
    gr.to_csv(OUT / "event_grid_per_subject.csv", index=False)
    pooled = (gr.groupby(["smooth", "top"])
                [["tp", "fp", "n_ref", "tp_short", "n_ref_short", "nonict_h"]].sum().reset_index())
    pooled["sens"] = pooled.tp / pooled.n_ref
    pooled["fa_day"] = pooled.fp / pooled.nonict_h * 24
    pooled.to_csv(OUT / "event_grid_pooled.csv", index=False)

    def best(cap):
        q = pooled[pooled.fa_day <= cap]
        return (float(q.sens.max()), q.loc[q.sens.idxmax()].to_dict()) if len(q) else (0.0, None)

    b25, r25 = best(25); b15, r15 = best(15); b10, _ = best(10)
    h1 = b25 >= 0.52
    h2 = ps.auc_sz_vs_flagged.mean() >= 0.85
    nimp = int((ps.auc_sz_vs_flagged > ps.e1_clean_sz_vs_flagged).sum())
    h3 = nimp >= 10
    lines = ["# E3 -- supervised feature classifier, LOSO over 15 non-test subjects\n",
             "## Per subject\n", "```", ps.round(4).to_string(), "```",
             f"\nMean: sz_vs_flagged {ps.auc_sz_vs_flagged.mean():.4f}, sz_vs_bg {ps.auc_sz_vs_bg.mean():.4f}, "
             f"null {ps.auc_null_perm.mean():.4f}\n",
             f"- H1: best sens at FA/day <= 25 = {b25:.3f} ({r25}) -> {'PASS' if h1 else 'FAIL'}",
             f"- H2: mean AUROC seizure vs flagged = {ps.auc_sz_vs_flagged.mean():.4f} -> {'PASS' if h2 else 'FAIL'}",
             f"- H3: subjects above E1 clean = {nimp}/15 -> {'PASS' if h3 else 'FAIL'}",
             f"- (info) best sens at FA/day <= 15 = {b15:.3f} ({r15}); <= 10 = {b10:.3f}",
             f"\n**E3 VERDICT: {'PASS' if (h1 and h2 and h3) else 'FAIL'}**\n",
             "## Pooled event grid\n", "```", pooled.round(4).to_string(index=False), "```",
             f"\nElapsed {time.time()-t0:.0f} s."]
    (OUT / "SUMMARY.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines[:30]))


if __name__ == "__main__":
    main()
