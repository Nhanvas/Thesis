#!/usr/bin/env python
"""
e17_rank_ensemble.py -- stage P2, E17 (design approved 2026-10-07, PERF_PHASE_RECORD 6.3/6.4).
"Ensemble anomaly score" (registration form) = ONE scalar series combining readouts (author decision).
15 non-test subjects, v2 clean seeds 42, 1, 2, 3. Cache only.

C = candidate after E16 (passed with --c; S9base unless an E16 arm was adopted).
Per patient, every readout is converted to its percentile over the patient's non-signal-loss windows
(signal-loss windows get 0.5), and the ensemble is the equal mean of percentiles. Ranking removes the
heavy upper tail that let gamma own the top 2 % of the old z-score ensemble (E11).
Combinations (all three scored, listed before the run; not a sweep):
  Ea = C + recon + gamma      Eb = C + L + gamma      Ec = C + L
  (recon = v2 joint reconstruction score, L = per-patient LedoitWolf Mahalanobis of the graph-mean
   latent, gamma = gamma-AEC; same seed as C for recon and L)
Detector cell re-selected per score by the 4-seed-mean pooled rule (FA/day <= 25).
NON-INFERIORITY vs C (each combination): pooled best >= C - 0.02, subject-mean sensitivity at the cell
>= C's - 0.02, validation-only best >= C's - 0.067 (one validation seizure).
CHOICE: the passing combination with the highest pooled best; a tie within 0.02 goes to a combination
containing gamma. If none passes: run with --latent-family (E17b: percentiles of S6, S9, S12, channel
mean, L, same gate); if that fails too, the author decides (record 6.4: C alone = channel ensemble).
Always reported: per component, percentile AUROC seizure-vs-flagged and mean percentile in the
combination's top-2 % non-ictal tail.
Every combination appends one row to results/p2_ledger.csv.
TEST GUARD: E8.SUBJS only.
Run:  python src/e17_rank_ensemble.py --c S9base            (estimated 10-30 min CPU, not measured)
      python src/e17_rank_ensemble.py --c S9base --latent-family   (only if none passes; 10-20 min)
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
for p in (ROOT / "src", ROOT / "src" / "retrain", ROOT / "src" / "phaseB", ROOT / "src" / "phaseC"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
import e8_gae_v2_eval as E8            # noqa: E402
import e16_recording_baseline as E16   # noqa: E402

TEST = {"chb03", "chb06", "chb13", "chb14", "chb15", "chb16", "chb17", "chb18"}
OUT = ROOT / "results" / "e17_rank_ensemble"
TAGS = E16.TAGS
COMBOS = {"Ea": ("C", "recon", "gamma"), "Eb": ("C", "L", "gamma"), "Ec": ("C", "L")}
FAMILY = {"E17b": ("S6", "S9", "S12", "Smean", "L")}


def pct(v, ok):
    out = np.full(len(v), 0.5)
    out[ok] = (rankdata(v[ok]) - 0.5) / ok.sum()
    return out


def k_scalar(D, k):
    okk = np.ones(len(D), bool)
    Zc = np.column_stack([E16.rz(D[:, j], okk) for j in range(D.shape[1])])
    return Zc.mean(axis=1) if k == "mean" else -np.sort(-Zc, axis=1)[:, k - 1]


def main():
    import e1_normal_definition as E1
    import e11_tail_anatomy as E11
    ap = argparse.ArgumentParser()
    ap.add_argument("--c", default="S9base", choices=["S9base", "a", "b", "c", "d", "e", "f"])
    ap.add_argument("--latent-family", action="store_true")
    a = ap.parse_args()
    if set(E8.SUBJS) & TEST:
        raise SystemExit("TEST GUARD")
    OUT.mkdir(parents=True, exist_ok=True)
    tagrun = "E17b" if a.latent_family else "E17"
    t0 = time.time()
    rows, comp, mech = [], [], []
    for s in E8.SUBJS:
        z = np.load(E8.DATA / f"{s}.npz", allow_pickle=True)
        d = E8.d_for_grid(z)
        idx, D, Z = E16.load_subject(s)
        c8 = np.load(E8.OUT / "scores" / f"{s}.npz"); p2 = np.load(ROOT / "results" / "p2_seeds" / f"{s}.npz")
        n = len(d["is_ictal"]); ok = ~d["is_signal_loss"]
        fidx = z["file_idx"].astype(int); wf = fidx[idx]
        fl5 = z["is_flag5sd"].astype(bool); ict = z["is_ictal"].astype(bool) & ok
        nonict = ~z["is_ictal"].astype(bool) & ~z["is_buffer"].astype(bool) & ok
        nh = float((~d["is_ictal"] & ok).sum()) * E8.WIN / 3600

        def full(v):
            o = np.full(n, np.nan); o[idx] = v; o[~ok] = np.nanmedian(v); return o

        g = full(z["zgamma_raw"][idx].astype(float))
        for tag in TAGS:
            src = c8 if tag in ("clean_seed42", "clean_seed1") else p2
            lat = src[f"{tag}_lat"].astype(np.float64)
            raw = {"recon": full(src[f"{tag}_recon"].astype(float)),
                   "L": full(LedoitWolf().fit(lat).mahalanobis(lat)), "gamma": g}
            cv, _ = E16.c_scalar(a.c, D[tag], Z[tag], wf)
            raw["C"] = full(cv)
            if a.latent_family:
                for k, kk in (("S6", 6), ("S9", 9), ("S12", 12), ("Smean", "mean")):
                    raw[k] = full(k_scalar(D[tag], kk))
            P = {k: pct(v, ok) for k, v in raw.items()}
            scores = {"C": E16.rz(raw["C"], ok)}
            combos = FAMILY if a.latent_family else COMBOS
            for name, parts in combos.items():
                scores[name] = np.mean([P[x] for x in parts], axis=0)
            for name, v in scores.items():
                for r_ in E1.event_grid(d, v):
                    r_.update(subject=s, score=f"{tag}|{name}", nonict_h=nh); rows.append(r_)
                mech.append(dict(subject=s, seed=tag, kind=name, sz_median=float(np.nanmedian(v[ict]))))
                if name == "C":
                    continue
                sm = E11.smooth(v, ok, fidx)
                T = (sm > np.nanquantile(sm[ok], 0.98)) & nonict
                for x in combos[name]:
                    comp.append(dict(subject=s, seed=tag, combo=name, component=x,
                                     auc_szflag=E11.auc(P[x], ict, nonict & fl5),
                                     tail_mean_pct=float(P[x][T].mean()) if T.any() else np.nan,
                                     sz_mean_pct=float(P[x][ict].mean()) if ict.any() else np.nan))
        print(f"{s}: done ({time.time()-t0:.0f}s)", flush=True)

    gr = pd.DataFrame(rows)
    gr["kind"] = gr.score.str.split("|").str[1]; gr["seed"] = gr.score.str.split("|").str[0]
    sfx = f"{tagrun}_C{a.c}"
    gr.to_csv(OUT / f"grid_per_subject_{sfx}.csv", index=False)
    Cp = pd.DataFrame(comp); Cp.to_csv(OUT / f"components_{sfx}.csv", index=False)
    pd.DataFrame(mech).to_csv(OUT / f"mechanism_{sfx}.csv", index=False)

    RC = E16.summarise(gr, "C")
    lines = [f"# {tagrun} -- rank ensemble to one scalar, C = {a.c}, 4 seeds, 15 non-test subjects\n",
             "## Best <= 25 | <= 15 | <= 10 | val | no-chb12 | subject-mean sens @ FP/day | per seed | short\n", "```"]
    res = {"C": RC}
    combos = FAMILY if a.latent_family else COMBOS
    for k in ["C"] + list(combos):
        R = RC if k == "C" else E16.summarise(gr, k)
        res[k] = R
        if R["cell"] is None:
            lines.append(f"{k:5s} never reaches FA/day <= 25"); continue
        lines.append(f"{k:5s} {R['best']:.3f} {R['cell']} | {R['le15']:.3f} | {R['le10']:.3f} | val {R['val']:.3f} | "
                     f"{R['x12']:.3f} | {R['subj']:.3f} @ {R['subj_fa']:.1f} | "
                     f"{', '.join(f'{v:.3f}' for v in R['seeds'].values())} | {R['short']}"
                     + ("   (reference C)" if k == "C" else f"   {'+'.join(combos[k])}"))
    lines += ["```", "\n## Components (median over subjects of seed means): AUROC seizure-vs-flagged | mean "
              "percentile in the combination's top-2 % non-ictal tail | in seizures\n", "```"]
    for (cb, x), gq in Cp.groupby(["combo", "component"]):
        m = gq.drop(columns=["seed", "combo", "component"]).groupby("subject").mean().median()
        lines.append(f"{cb:5s} {x:6s} {m.auc_szflag:.3f} | {m.tail_mean_pct:.3f} | {m.sz_mean_pct:.3f}")
    lines.append("```")
    passing = []
    for k in combos:
        R = res[k]
        if R["cell"] is None:
            E16.ledger(tagrun, k, dict(best=0.0, cell=None), {}, "not non-inferior (no cell)"); continue
        n1 = R["best"] >= RC["best"] - 0.02; n2 = R["subj"] >= RC["subj"] - 0.02; n3 = R["val"] >= RC["val"] - 0.067
        ok_ = n1 and n2 and n3
        E16.ledger(tagrun, k, R, dict(NI_pooled=n1, NI_subj=n2, NI_val=n3), "non-inferior" if ok_ else "inferior")
        lines.append(f"- {k}: pooled {'pass' if n1 else 'FAIL'}, subject-mean {'pass' if n2 else 'FAIL'}, "
                     f"validation {'pass' if n3 else 'FAIL'} -> {'non-inferior' if ok_ else 'inferior'}")
        if ok_:
            passing.append(k)
    if passing:
        top = max(passing, key=lambda k: res[k]["best"])
        tie = [k for k in passing if res[top]["best"] - res[k]["best"] <= 0.02 and "gamma" in combos[k]]
        chosen = max(tie, key=lambda k: res[k]["best"]) if tie and "gamma" not in combos[top] else top
        lines.append(f"\n**Chosen ensemble: {chosen} ({'+'.join(combos[chosen])})**")
    else:
        lines.append("\n**No combination is non-inferior** -> "
                     + ("author decides (record 6.4)" if a.latent_family else "run --latent-family (E17b)"))
    lines.append(f"\nElapsed {time.time()-t0:.0f} s.")
    (OUT / f"SUMMARY_{sfx}.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
