#!/usr/bin/env python
"""
e13_recon_seen_artifacts.py -- stage P2, step 3. Cache only (E8 scores), 15 non-test subjects.
Descriptive with a pre-registered decision rule; no gate, no adoption, no test data.

Question. Patient-specific adaptation (fine-tuning the GAE on the patient's whole recording) is only
worth a Kaggle night if the RECONSTRUCTION readout becomes able to separate seizures from the patient's
own high-amplitude windows once the model has been trained on such windows. Today it cannot:
E11, v2 clean recon, seizure-vs-flagged AUROC 0.527-0.534, exceedance 0.34.

Natural experiment already in the cache. The 'all' variant of v2 was trained on the flagged windows of
the 12 TRAINING subjects (their own artifacts, seizures and 4 h buffers excluded); the 'clean' variant
never saw flagged windows. On those 12 subjects, all-vs-clean is a diluted proxy of "the model has seen
this patient's own artifacts" (diluted: 11 other patients share the capacity; conservative: their
seizures were excluded, so it says nothing about contamination). On the 3 validation subjects it is a
cross-patient effect only.

Measures per subject and model (clean_seed42, clean_seed1, all_seed42, all_seed1), branches
r = recon and l = latent LW (both per-patient robust-z), smoothed as D1 (15 windows):
  window AUROC seizure vs flagged, seizure vs clean; share flagged among non-ictal windows in the top
  2 % of the branch's own smoothed score; exceedance (E11 M3) all blocks | blocks without a flag.
DECISION RULE (fixed now). Seed-mean per subject, the 12 training subjects:
  A  median Delta AUROC(seizure vs flagged) of recon, all - clean  >= +0.10, and positive in >= 8/12
     -> adaptation has a measured mechanism on the recon readout -> build the adaptation experiment.
  B  otherwise -> adaptation of the GAE is not supported by evidence; the next lever is a readout
     that uses spatial recruitment (per-node outputs), not adaptation.
  The 3 validation subjects are reported separately and do not enter the rule.
TEST GUARD: E8.SUBJS only.
Run:  python src/e13_recon_seen_artifacts.py      (estimated 3-10 min CPU, not measured)
"""
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.covariance import LedoitWolf

ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT / "src", ROOT / "src" / "retrain"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
import e8_gae_v2_eval as E8            # noqa: E402
import e11_tail_anatomy as E11         # noqa: E402

TEST = {"chb03", "chb06", "chb13", "chb14", "chb15", "chb16", "chb17", "chb18"}
OUT = ROOT / "results" / "e13_recon_seen_artifacts"
MODELS = ["clean_seed42", "clean_seed1", "all_seed42", "all_seed1"]
TRAIN12 = [s for s in E8.SUBJS if s not in E8.VAL]


def main():
    if set(E8.SUBJS) & TEST:
        raise SystemExit("TEST GUARD")
    OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    rows = []
    for s in E8.SUBJS:
        z = np.load(E8.DATA / f"{s}.npz", allow_pickle=True)
        c = np.load(E8.OUT / "scores" / f"{s}.npz")
        n = len(z["is_ictal"]); ok = ~z["is_signal_loss"].astype(bool); idx = c["idx"]
        ict = z["is_ictal"].astype(bool) & ok
        fl5 = z["is_flag5sd"].astype(bool); fidx = z["file_idx"].astype(int)
        nonict = ~z["is_ictal"].astype(bool) & ~z["is_buffer"].astype(bool) & ok
        flag, bg = nonict & fl5, nonict & ~fl5
        events = []
        for f in np.unique(fidx):
            m = np.flatnonzero(fidx == f)
            events += [m[a:b] for a, b in E11.runs(ict[m])]

        def full(v):
            o = np.full(n, np.nan); o[idx] = v; o[~ok] = np.nanmedian(v); return o

        for model in MODELS:
            if f"{model}_recon" not in c.files:
                raise SystemExit(f"{s}: {model} missing in the E8 cache")
            lat = c[f"{model}_lat"]
            br = {"r": E11.rz(full(c[f"{model}_recon"]), ok),
                  "l": E11.rz(full(LedoitWolf().fit(lat).mahalanobis(lat)), ok)}
            for k, v in br.items():
                sm = E11.smooth(v, ok, fidx)
                thr = np.nanquantile(sm[ok], 0.98)
                T = (sm > thr) & nonict
                ex_all, ex_or, cache = [], [], {}
                for ev in events:
                    L = len(ev)
                    if L not in cache:
                        cache[L] = E11.block_peaks(sm, nonict, fl5, fidx, L)
                    pk, cl = cache[L]; peak = np.nanmax(sm[ev])
                    if len(pk):
                        ex_all.append((pk > peak).mean())
                    if cl.any():
                        ex_or.append((pk[cl] > peak).mean())
                rows.append(dict(subject=s, set="val" if s in E8.VAL else "train",
                                 variant=model.split("_seed")[0], seed=model.split("seed")[1], branch=k,
                                 auc_szflag=E11.auc(sm, ict, flag), auc_szbg=E11.auc(sm, ict, bg),
                                 tail_flag_share=float(fl5[T].mean()) if T.any() else np.nan,
                                 exceed_all=float(np.median(ex_all)) if ex_all else np.nan,
                                 exceed_oracle=float(np.median(ex_or)) if ex_or else np.nan))
        print(f"{s}: done ({time.time()-t0:.0f}s)", flush=True)

    R = pd.DataFrame(rows); R.to_csv(OUT / "per_subject_seed.csv", index=False)
    S = R.groupby(["subject", "set", "variant", "branch"])[["auc_szflag", "auc_szbg", "tail_flag_share",
                                                           "exceed_all", "exceed_oracle"]].mean().reset_index()
    S.to_csv(OUT / "per_subject_seedmean.csv", index=False)

    lines = ["# E13 -- does training on artifacts make the recon readout discriminative? (cache only)\n",
             "Median over subjects of the seed-mean values.\n", "```",
             "set    variant branch  AUC sz-flag  AUC sz-clean  tail flagged  exceed all|no-flag"]
    for st in ("train", "val"):
        for var in ("clean", "all"):
            for br in ("r", "l"):
                q = S[(S.set == st) & (S.variant == var) & (S.branch == br)]
                lines.append(f"{st:6s} {var:7s} {br:6s}  {q.auc_szflag.median():11.3f}  {q.auc_szbg.median():12.3f}"
                             f"  {q.tail_flag_share.median():12.2f}  {q.exceed_all.median():.3f}|{q.exceed_oracle.median():.3f}")
    lines.append("```")
    r = S[S.branch == "r"].pivot_table(index=["subject", "set"], columns="variant", values="auc_szflag").reset_index()
    r["delta"] = r["all"] - r["clean"]
    tr = r[r.set == "train"]
    med, npos = float(tr.delta.median()), int((tr.delta > 0).sum())
    lines += ["\n## Recon, seizure-vs-flagged AUROC, all - clean, per subject (seed mean)\n", "```"]
    lines += [f"{x.subject} ({x.set:5s})  clean {x['clean']:.3f}  all {x['all']:.3f}  delta {x.delta:+.3f}"
              for _, x in r.iterrows()]
    lines.append("```")
    dec = "A" if (med >= 0.10 and npos >= 8) else "B"
    lines.append(f"\nDecision rule (12 training subjects): median delta {med:+.3f}, positive in {npos}/12 -> "
                 f"**{dec}** " + ("(build the adaptation experiment)" if dec == "A"
                                  else "(adaptation not supported; next lever = spatial-recruitment readout)"))
    lines.append(f"\nElapsed {time.time()-t0:.0f} s.")
    (OUT / "SUMMARY.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
