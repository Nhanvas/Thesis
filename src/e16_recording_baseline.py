#!/usr/bin/env python
"""
e16_recording_baseline.py -- stage P2, E16 (design approved 2026-10-07, PERF_PHASE_RECORD rev D/E 6.3).
Readout-level, label-free per-recording baseline ("baseline drifts" in the registration form).
15 non-test subjects, v2 clean seeds 42, 1, 2, 3. Cache only.

Reference: S9 base (per-patient per-channel LedoitWolf on the node latent, 9th largest of 18).
Arms (one construction each, all fixed now; same gate for every arm):
  a  PRIMARY: per file, per channel, LW fitted on the first min(150, n_file // 2) windows of the file
     (10 min); distances for every window of the file; files with < 40 windows use the patient fit.
  b  patient-level LW (as S9) + per-file median/MAD normalisation of each channel's distances.
  c  as a with min(450, n_file // 2) windows (30 min).
  d  causal sliding baseline: inside each file, LW refitted every 225 windows (15 min) on the previous
     450 windows (30 min); the first 450 windows of the file use the patient fit.
  Arms b-d are run only if a is not adopted (author rule: no verdict before evidence-backed fixes).
  Added 2026-10-07 after a-d (mechanism measured under S9 base: 84.5 % of the top-2 % non-ictal
  windows sit in the patient's top-quartile files; drift IQR/MAD 0.85; arm b, location+scale per file,
  better at <= 15 and <= 10 FA/day but seizure z 4.72 -> 4.08), location-only corrections of the S9
  scalar, same gate:
  e  S9 minus its centred running median over 451 windows (+-15 min) inside each file
  f  S9 minus its median inside each file
Common tail: per-channel robust-z over the patient's windows, 9th largest of 18, robust-z per patient.
Detector: D1 grid of e1_normal_definition.event_grid; the cell of every score is re-selected by the
same rule (highest 4-seed-mean pooled sensitivity at FA/day <= 25).
GATE (vs S9 base, fixed for every arm):
  G1 4-seed mean best >= S9 + 0.05 AND >= 3 of 4 seeds with best >= that seed's S9 best
  G2 subject-mean sensitivity at the cell >= S9's at its cell
  G3 pooled sensitivity without chb12 at the cell >= S9's
  G4 validation-only best >= S9's
  G5 >= 9 of 15 subjects with 4-seed-mean TP >= S9's
  M  median seizure-window z not more than 10 % below S9's
Diagnostics (always): (a) drift under S9 base: IQR of per-file medians of non-ictal scores / patient
MAD, and the share of top-2 % non-ictal windows inside the patient's top-quartile files; (b) fit noise
for baseline arms: std of distances inside / outside the baseline; (c) self-scoring: median z of
baseline windows minus median z of the other non-ictal windows.
Every arm appends one row to results/p2_ledger.csv (all arms, adopted or not).
TEST GUARD: E8.SUBJS only.
Run:  python src/e16_recording_baseline.py --arms a          (estimated 10-30 min CPU, not measured)
      python src/e16_recording_baseline.py --arms b c d      (only if a is not adopted; 30-90 min)
"""
import argparse
import sys
import time
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.covariance import LedoitWolf

ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT / "src", ROOT / "src" / "retrain", ROOT / "src" / "phaseB", ROOT / "src" / "phaseC"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
import e8_gae_v2_eval as E8            # noqa: E402

TEST = {"chb03", "chb06", "chb13", "chb14", "chb15", "chb16", "chb17", "chb18"}
OUT = ROOT / "results" / "e16_recording_baseline"
LEDGER = ROOT / "results" / "p2_ledger.csv"
TAGS = ["clean_seed42", "clean_seed1", "clean_seed2", "clean_seed3"]
K = 9


# ----------------------------------------------------------------------------- shared loaders
def load_subject(s):
    """window index, D (patient-level per-channel distances) and Z (node latents) for 4 seeds."""
    c8 = np.load(E8.OUT / "scores" / f"{s}.npz")
    e14 = np.load(ROOT / "results" / "e14_spatial_recruitment" / "pernode" / f"{s}.npz")
    e15 = np.load(ROOT / "results" / "e15_patient_adaptation" / "pernode" / f"{s}.npz")
    p2 = np.load(ROOT / "results" / "p2_seeds" / f"{s}.npz")
    idx = c8["idx"]
    for name, f in (("e14", e14), ("e15", e15), ("p2_seeds", p2)):
        if not np.array_equal(idx, f["idx"]):
            raise SystemExit(f"{s}: window index of {name} differs from the E8 cache")
    D, Z = {}, {}
    for t in ("clean_seed42", "clean_seed1"):
        D[t] = e14[f"{t}_d"].astype(np.float64); Z[t] = e15[f"{t}_s0_Z"]
    for t in ("clean_seed2", "clean_seed3"):
        D[t] = p2[f"{t}_d"].astype(np.float64); Z[t] = p2[f"{t}_Z"]
    return idx, D, Z


def rz(x, ok):
    m = np.median(x[ok]); s = np.median(np.abs(x[ok] - m)) + 1e-9
    return (x - m) / s


def s_from_d(D, k=K):
    okk = np.ones(len(D), bool)
    Zc = np.column_stack([rz(D[:, j], okk) for j in range(D.shape[1])])
    return -np.sort(-Zc, axis=1)[:, k - 1]


def lw_dist(fit, score):
    return LedoitWolf().fit(fit.astype(np.float64)).mahalanobis(score.astype(np.float64))


# ----------------------------------------------------------------------------- arms
def arm_distances(arm, D, Z, wf):
    """per-channel distances for one seed. wf = file id of each dumped window (time order inside a file)."""
    out = D.copy()
    base_mask = np.zeros(len(D), bool)
    for f in np.unique(wf):
        w = np.flatnonzero(wf == f); n = len(w)
        if arm in ("a", "c"):
            nb = min(150 if arm == "a" else 450, n // 2)
            if nb < 40:
                continue
            base_mask[w[:nb]] = True
            for c in range(D.shape[1]):
                out[w, c] = lw_dist(Z[w[:nb], c, :], Z[w, c, :])
        elif arm == "b":
            for c in range(D.shape[1]):
                x = D[w, c]; m = np.median(x); s_ = np.median(np.abs(x - m)) + 1e-9
                out[w, c] = (x - m) / s_
        elif arm == "d":
            for t0 in range(450, n, 225):
                fit, sc = w[t0 - 450:t0], w[t0:t0 + 225]
                for c in range(D.shape[1]):
                    out[sc, c] = lw_dist(Z[fit, c, :], Z[sc, c, :])
        else:
            raise SystemExit(f"unknown arm {arm}")
    return out, base_mask


def c_scalar(arm, D, Z, wf):
    """per-dumped-window scalar of any arm (S9base, a-f)."""
    if arm in ("S9base", "e", "f"):
        v = s_from_d(D)
        if arm == "S9base":
            return v, None
        out = v.copy()
        for f in np.unique(wf):
            w = np.flatnonzero(wf == f)
            if arm == "f":
                out[w] = v[w] - np.median(v[w])
            else:
                out[w] = v[w] - pd.Series(v[w]).rolling(451, min_periods=1, center=True).median().values
        return out, None
    Da, bm = arm_distances(arm, D, Z, wf)
    return s_from_d(Da), (Da, bm)


# ----------------------------------------------------------------------------- evaluation helpers
def pooled_tables(gr):
    p = gr.groupby(["kind", "seed", "smooth", "top"])[["tp", "fp", "n_ref", "nonict_h", "tp_short",
                                                       "n_ref_short"]].sum().reset_index()
    p["sens"] = p.tp / p.n_ref; p["fa_day"] = p.fp / p.nonict_h * 24
    m = p.groupby(["kind", "smooth", "top"]).agg(sens=("sens", "mean"), fa_day=("fa_day", "mean"),
                                                 tp_short=("tp_short", "mean"),
                                                 n_short=("n_ref_short", "max")).reset_index()
    return p, m


def best(T, kind, cap=25.0):
    q = T[(T.kind == kind) & (T.fa_day <= cap)]
    if not len(q):
        return 0.0, None
    r = q.loc[q.sens.idxmax()]
    return float(r.sens), (int(r.smooth), float(r.top), round(float(r.fa_day), 2))


def at(T, kind, cell):
    q = T[(T.kind == kind) & (T.smooth == cell[0]) & (T.top == cell[1])]
    return float(q.sens.iloc[0]) if len(q) else np.nan


def subj_mean(gr, kind, cell):
    q = gr[(gr.kind == kind) & (gr.smooth == cell[0]) & (gr.top == cell[1])]
    q = q.groupby(["seed", "subject"])[["tp", "fp", "n_ref", "nonict_h"]].sum().reset_index()
    q["sens"] = q.tp / q.n_ref; q["fa_day"] = q.fp / q.nonict_h * 24
    q["prec"] = q.tp / (q.tp + q.fp).where(q.tp + q.fp > 0)
    q["f1"] = 2 * q.tp / (2 * q.tp + q.fp + (q.n_ref - q.tp))
    return q.groupby("seed")[["sens", "prec", "f1", "fa_day"]].mean().mean()


def summarise(gr, kind):
    P, A = pooled_tables(gr)
    _, Av = pooled_tables(gr[gr.subject.isin(E8.VAL)])
    _, Ax = pooled_tables(gr[gr.subject != "chb12"])
    b, c = best(A, kind)
    if c is None:
        return dict(best=0.0, cell=None)
    sm = subj_mean(gr, kind, c)
    seeds = {t: best(P[P.seed == t], kind)[0] for t in TAGS}
    tp = gr[(gr.kind == kind) & (gr.smooth == c[0]) & (gr.top == c[1])].groupby("subject").tp.mean()
    sh = A[(A.kind == kind) & (A.smooth == c[0]) & (A.top == c[1])]
    # two validation quantities (record 6.5): `val` = best cell re-selected on the 3 validation subjects
    # alone at THEIR FA/day <= 25 (the definition used by every gate G4 since E12); `val_at_cell` =
    # sensitivity of the 3 validation subjects at the cell selected on all 15 (descriptive only).
    return dict(best=b, cell=c, le15=best(A, kind, 15)[0], le10=best(A, kind, 10)[0],
                val=best(Av, kind)[0], val_at_cell=at(Av, kind, c), x12=at(Ax, kind, c), subj=float(sm.sens), subj_fa=float(sm.fa_day),
                subj_f1=float(sm.f1), seeds=seeds, tp=tp,
                short=f"{float(sh.tp_short.iloc[0]):.1f}/{int(sh.n_short.iloc[0])}")


def gate(R, B, zR, zB):
    g1 = R["best"] >= B["best"] + 0.05 and sum(R["seeds"][t] >= B["seeds"][t] for t in TAGS) >= 3
    g2 = R["subj"] >= B["subj"]; g3 = R["x12"] >= B["x12"]; g4 = R["val"] >= B["val"]
    n_ok = int((R["tp"] >= B["tp"]).sum()); g5 = n_ok >= 9
    m = zR >= zB - 0.10 * abs(zB)
    return dict(G1=g1, G2=g2, G3=g3, G4=g4, G5=g5, M=m, n_ok=n_ok), all([g1, g2, g3, g4, g5, m])


def ledger(step, arm, R, gates, verdict):
    row = dict(date=str(date.today()), step=step, arm=arm, best_le25=round(R["best"], 4), cell=str(R["cell"]),
               le15=round(R.get("le15", np.nan), 4), le10=round(R.get("le10", np.nan), 4),
               val=round(R.get("val", np.nan), 4), no_chb12=round(R.get("x12", np.nan), 4),
               subj_sens=round(R.get("subj", np.nan), 4), subj_fa=round(R.get("subj_fa", np.nan), 2),
               seeds="|".join(f"{v:.3f}" for v in R.get("seeds", {}).values()),
               gates=" ".join(f"{k}={'P' if v else 'F'}" for k, v in gates.items() if k != "n_ok"),
               n_subj_ok=gates.get("n_ok"), verdict=verdict)
    df = pd.DataFrame([row])
    df.to_csv(LEDGER, mode="a", header=not LEDGER.exists(), index=False)


# ----------------------------------------------------------------------------- main
def main():
    import e1_normal_definition as E1
    import e11_tail_anatomy as E11
    ap = argparse.ArgumentParser()
    ap.add_argument("--arms", nargs="+", default=["a"], choices=["a", "b", "c", "d", "e", "f"])
    a = ap.parse_args()
    if set(E8.SUBJS) & TEST:
        raise SystemExit("TEST GUARD")
    OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    rows, mech, diag = [], [], []
    for s in E8.SUBJS:
        z = np.load(E8.DATA / f"{s}.npz", allow_pickle=True)
        d = E8.d_for_grid(z)
        idx, D, Z = load_subject(s)
        n = len(d["is_ictal"]); ok = ~d["is_signal_loss"]
        fidx = z["file_idx"].astype(int); wf = fidx[idx]
        fl5 = z["is_flag5sd"].astype(bool); ict = z["is_ictal"].astype(bool) & ok
        nonict = ~z["is_ictal"].astype(bool) & ~z["is_buffer"].astype(bool) & ok
        nh = float((~d["is_ictal"] & ok).sum()) * E8.WIN / 3600

        def full(v):
            o = np.full(n, np.nan); o[idx] = v; o[~ok] = np.nanmedian(v); return o

        for tag in TAGS:
            scores = {"S9base": (rz(full(s_from_d(D[tag])), ok), None)}
            for arm in a.arms:
                v_, extra_ = c_scalar(arm, D[tag], Z[tag], wf)
                scores[f"E16{arm}"] = (rz(full(v_), ok), extra_)
            for kind, (v, extra) in scores.items():
                for r_ in E1.event_grid(d, v):
                    r_.update(subject=s, score=f"{tag}|{kind}", nonict_h=nh); rows.append(r_)
                mech.append(dict(subject=s, seed=tag, kind=kind, sz_median_z=float(np.nanmedian(v[ict])),
                                 flag_median_z=float(np.nanmedian(v[nonict & fl5]))))
                if kind == "S9base":                     # diagnostic (a): drift under S9 base
                    sm = E11.smooth(v, ok, fidx)
                    T = (sm > np.nanquantile(sm[ok], 0.98)) & nonict
                    meds = pd.Series(v[nonict]).groupby(fidx[nonict]).median()
                    mad = np.median(np.abs(v[nonict] - np.median(v[nonict]))) + 1e-9
                    topf = meds[meds >= meds.quantile(0.75)].index
                    sz_files = np.unique(fidx[ict])
                    in_top = np.isin(fidx, topf)
                    diag.append(dict(subject=s, seed=tag, kind=kind, drift_iqr_over_mad=float(
                        (meds.quantile(0.75) - meds.quantile(0.25)) / mad),
                        tail_share_top_quartile_files=float(np.isin(fidx[T], topf).mean()) if T.any() else np.nan,
                        top_files_with_seizure=float(np.isin(topf, sz_files).mean()) if len(topf) else np.nan,
                        flag_share_top_files=float(fl5[nonict & in_top].mean()) if (nonict & in_top).any() else np.nan,
                        flag_share_other_files=float(fl5[nonict & ~in_top].mean()) if (nonict & ~in_top).any() else np.nan))
                elif extra is not None and extra[1].any():  # diagnostics (b), (c) for baseline arms
                    Da, bm = extra
                    inb, outb = bm, ~bm & nonict[idx]
                    vv = v[idx]
                    diag.append(dict(subject=s, seed=tag, kind=kind,
                                     fit_noise_std_in_over_out=float(np.median(Da[inb].std(axis=0) /
                                                                              (Da[outb].std(axis=0) + 1e-9))),
                                     self_scoring_dz=float(np.median(vv[inb]) - np.median(vv[outb]))))
        print(f"{s}: done ({time.time()-t0:.0f}s)", flush=True)

    gr = pd.DataFrame(rows)
    gr["kind"] = gr.score.str.split("|").str[1]; gr["seed"] = gr.score.str.split("|").str[0]
    gr.to_csv(OUT / f"grid_per_subject_{''.join(a.arms)}.csv", index=False)
    M = pd.DataFrame(mech); M.to_csv(OUT / f"mechanism_{''.join(a.arms)}.csv", index=False)
    Dg = pd.DataFrame(diag); Dg.to_csv(OUT / f"diagnostics_{''.join(a.arms)}.csv", index=False)
    med = M.groupby(["kind", "subject"])[["sz_median_z", "flag_median_z"]].mean().groupby("kind").median()

    B = summarise(gr, "S9base")
    lines = [f"# E16 -- per-recording baseline readout, arms {a.arms}, 4 seeds, 15 non-test subjects\n",
             "## Best <= 25 | <= 15 | <= 10 | val | no-chb12 | subject-mean sens @ FP/day | per seed | short\n", "```"]
    res = {"S9base": B}
    for kind in ["S9base"] + [f"E16{x}" for x in a.arms]:
        R = summarise(gr, kind) if kind != "S9base" else B
        res[kind] = R
        if R["cell"] is None:
            lines.append(f"{kind:7s} never reaches FA/day <= 25"); continue
        lines.append(f"{kind:7s} {R['best']:.3f} {R['cell']} | {R['le15']:.3f} | {R['le10']:.3f} | val {R['val']:.3f} | "
                     f"{R['x12']:.3f} | {R['subj']:.3f} @ {R['subj_fa']:.1f} | "
                     f"{', '.join(f'{v:.3f}' for v in R['seeds'].values())} | {R['short']}")
    lines += ["```", "\n## Mechanism (median over subjects of seed means)\n", "```"]
    lines += [f"{k:7s} seizure z {med.loc[k, 'sz_median_z']:.2f}  flagged z {med.loc[k, 'flag_median_z']:.2f}"
              for k in med.index]
    lines += ["```", "\n## Diagnostics (median over subjects of seed means)\n", "```"]
    for k, g in Dg.groupby("kind"):
        gm = g.drop(columns=["seed"]).groupby("subject").mean(numeric_only=True).median()
        lines.append(f"{k:7s} " + "  ".join(f"{c} {gm[c]:.3f}" for c in gm.index if np.isfinite(gm[c])))
    lines.append("```")
    adopted_any = []
    for arm in a.arms:
        kind = f"E16{arm}"; R = res[kind]
        if R["cell"] is None:
            ledger("E16", arm, dict(best=0.0, cell=None), {}, "NOT adopted (no cell <= 25)"); continue
        g, ok_ = gate(R, B, med.loc[kind, "sz_median_z"], med.loc["S9base", "sz_median_z"])
        verdict = "ADOPTED" if ok_ else "NOT adopted"
        ledger("E16", arm, R, g, verdict)
        if ok_:
            adopted_any.append((R["best"], kind))
        lines.append(f"\n- {kind}: " + " ".join(f"{k} {'pass' if v else 'FAIL'}" for k, v in g.items() if k != "n_ok")
                     + f" (subjects {g['n_ok']}/15) -> **{verdict}**")
        lines += ["  per subject 4-seed-mean TP (arm | S9 base): " +
                  ", ".join(f"{s_} {R['tp'].get(s_, np.nan):.2f}|{B['tp'][s_]:.2f}" for s_ in B["tp"].index)]
    winner = max(adopted_any)[1] if adopted_any else "S9base"
    lines.append(f"\n**Candidate C after this run: {winner}**"
                 + ("" if adopted_any or a.arms != ["a"] else " -- arm a not adopted: run arms b c d (record 6.3)"))
    lines.append(f"\nElapsed {time.time()-t0:.0f} s.")
    (OUT / f"SUMMARY_{''.join(a.arms)}.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
