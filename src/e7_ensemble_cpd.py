#!/usr/bin/env python
"""
e7_ensemble_cpd.py -- one run, two decisions, both fixed before the run (approved 2026-10-05).

SCORES (every fit per patient on that patient's own non-signal-loss windows, no label):
  G0  locked GAE readouts as the application builds them: robust-z(recon), robust-z(LedoitWolf
      Mahalanobis of the 16-d latent), robust-z(gamma), equal weights (ensemble_recipe 'rlg').
  F   per-patient GaussianMixture (k = 8, full) NLL on the 27 raw_eeg_view features (= E5).
  B   four branches, equal weights: robust-z of recon, latent, gamma and F.
DETECTORS (per file; events never cross a file; events closer than 90 s merged):
  D1  threshold detector: moving average (1/3/5/15 windows) above the patient's own
      (1 - p) quantile, p in {5, 2, 1, 0.5, 0.2, 0.1} %  (= E1 grid).
  D2  change-point segmentation: PELT (ruptures, l2 cost, min_size 2 windows) on the
      unsmoothed score of each file, penalty = c * sigma^2 * ln(n_file), c in {1, 3, 10},
      sigma = patient noise level (1.4826 * MAD of first differences / sqrt 2); a segment is
      an alarm when its MEAN exceeds the patient's (1 - p) quantile; the event is the segment.
      This keeps change-point detection but uses it to SEGMENT, fixing the two measured
      defects of the locked use (every change point an alarm incl. falling ones; point events).
DECISION RULES (15 non-test subjects pooled, SzCORE, best sensitivity with FA/day <= 25):
  R1  B is adopted if  B >= max(F, G0)  and  B >= G0 + 0.10  (under the better detector).
      If F > B, B is not adopted and the finding is reported (decision goes to the supervisor).
  R2  D2 is adopted over D1 if D2 >= D1 - 0.02 on the adopted score (non-inferiority by at
      most 2 of 94 seizures), because it keeps the change-point method and gives segment
      onsets/offsets; otherwise D1 is adopted.
  The adopted score, detector and its best cell are then frozen for the one-shot test run.
Known biases: GAE saw training subjects' clean windows (favours G0/B); training-subject caches
are seizure-enriched (works against F/B).
TEST GUARD inherited from e1_normal_definition. Writes only results/e7_ensemble_cpd/.
"""
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import ruptures as rpt
from sklearn.covariance import LedoitWolf
from sklearn.mixture import GaussianMixture

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import e1_normal_definition as E1  # noqa: E402
import ensemble_recipe as ER       # noqa: E402
import szcore_eval as SE           # noqa: E402

DUMP = ROOT / "results" / "e6_gae_dump"
OUT = ROOT / "results" / "e7_ensemble_cpd"
OUT.mkdir(parents=True, exist_ok=True)
FIT_MAX = 20000
PENS = [1.0, 3.0, 10.0]
RNG = np.random.default_rng(0)


def med_mad(x):
    m = float(np.median(x)); return m, float(np.median(np.abs(x - m))) + 1e-9


def rz(x, ok):
    m, s = med_mad(x[ok]); return (x - m) / s


def gmm_nll(V, ok):
    idx = np.flatnonzero(ok)
    if len(idx) > FIT_MAX:
        idx = RNG.choice(idx, FIT_MAX, replace=False)
    g = GaussianMixture(n_components=8, covariance_type="full", reg_covar=1e-3,
                        max_iter=300, random_state=0).fit(V[idx])
    return -g.score_samples(V)


def merge(ev, gap=90):
    out = []
    for a, b in sorted(ev):
        if out and a - out[-1][1] <= gap:
            out[-1] = (out[-1][0], max(b, out[-1][1]))
        else:
            out.append((a, b))
    return out


def score_events(d, per_file_events):
    """per_file_events: {file_id: [(a_s, b_s), ...]} in file-relative seconds -> tp, fp, n_ref."""
    ref_all, hyp_all, off = [], [], 0
    for f in np.unique(d["file_idx"]):
        m = d["file_idx"] == f
        ref_all += [(a + off, b + off) for a, b in E1.ref_for_file(d["is_ictal"][m])]
        hyp_all += [(a + off, b + off) for a, b in per_file_events.get(f, [])]
        off += int(m.sum()) * E1.WIN + 600
    nonict_h = float((~d["is_ictal"] & ~d["is_signal_loss"]).sum()) * E1.WIN / 3600
    r = SE.score_szcore(ref_all, hyp_all, off, nonict_h)
    return int(r["tp"]), int(r["fp"]), int(r["n_ref"]), nonict_h


def d2_grid(d, score):
    ok = ~d["is_signal_loss"]
    x_all = score.astype(float).copy()
    x_all[~ok] = np.median(x_all[ok])
    dif = np.diff(x_all[ok])
    sigma = 1.4826 * np.median(np.abs(dif - np.median(dif))) / np.sqrt(2) + 1e-9
    rows = []
    for c in PENS:
        segs = {}
        for f in np.unique(d["file_idx"]):
            m = np.flatnonzero(d["file_idx"] == f)
            x = x_all[m]
            if len(x) < 4:
                segs[f] = [(0, len(x), float(x.mean()))]; continue
            pen = c * sigma ** 2 * np.log(len(x))
            bk = rpt.Pelt(model="l2", min_size=2, jump=1).fit(x.reshape(-1, 1)).predict(pen=pen)
            st = [0] + bk[:-1]
            segs[f] = [(a, b, float(x[a:b].mean())) for a, b in zip(st, bk)]
        for p in E1.TOPS:
            thr = np.quantile(score[ok], 1 - p)
            ev = {f: merge([(a * E1.WIN, b * E1.WIN) for a, b, mu in sg if mu > thr]) for f, sg in segs.items()}
            tp, fp, nr, h = score_events(d, ev)
            rows.append(dict(detector="D2", param=c, top=p, tp=tp, fp=fp, n_ref=nr, nonict_h=h))
    return rows


def main():
    t0 = time.time()
    rows, per = [], []
    for s in E1.SUBJS:
        d = E1.load(s)
        z = np.load(DUMP / f"{s}.npz")
        if len(z["zrecon_raw"]) != len(d["is_ictal"]):
            raise SystemExit(f"{s}: dump/cache length mismatch")
        ok = ~d["is_signal_loss"]
        zr, zg = rz(z["zrecon_raw"], ok), rz(z["zgamma_raw"], ok)
        zl = rz(LedoitWolf().fit(z["graph_z"][ok]).mahalanobis(z["graph_z"]), ok)
        G0 = np.asarray(ER.build_ensemble_subset({"zrecon": zr, "zlatent": zl, "zgamma": zg},
                                                 ER.CANDIDATES["rlg"]), dtype=float)
        F = gmm_nll(d["X"], ok)
        B = (zr + zl + zg + rz(F, ok)) / 4.0
        ict = d["is_ictal"] & ok
        base = ~d["is_ictal"] & ~d["is_buffer"] & ok
        flag, bg = base & d["is_artifact"], base & ~d["is_artifact"]
        row = dict(subject=s)
        for name, sc in (("G0", G0), ("F", F), ("B", B)):
            row[f"{name}_sz_flag"] = E1.auc(sc, ict, flag); row[f"{name}_sz_bg"] = E1.auc(sc, ict, bg)
            for r in E1.event_grid(d, sc):
                rows.append(dict(subject=s, score=name, detector="D1", param=r["smooth"], top=r["top"],
                                 tp=r["tp"], fp=r["fp"], n_ref=r["n_ref"],
                                 nonict_h=float((~d["is_ictal"] & ok).sum()) * E1.WIN / 3600))
            for r in d2_grid(d, sc):
                r.update(subject=s, score=name); rows.append(r)
        per.append(row)
        print(f"{s}: sz/flag G0 {row['G0_sz_flag']:.3f} F {row['F_sz_flag']:.3f} B {row['B_sz_flag']:.3f} "
              f"({time.time()-t0:.0f}s)", flush=True)

    ps = pd.DataFrame(per).set_index("subject")
    gr = pd.DataFrame(rows)
    ps.to_csv(OUT / "per_subject.csv"); gr.to_csv(OUT / "grid_per_subject.csv", index=False)
    pooled = gr.groupby(["score", "detector", "param", "top"])[["tp", "fp", "n_ref", "nonict_h"]].sum().reset_index()
    pooled["sens"] = pooled.tp / pooled.n_ref; pooled["fa_day"] = pooled.fp / pooled.nonict_h * 24
    pooled.to_csv(OUT / "grid_pooled.csv", index=False)

    def best(score, det=None, cap=25):
        q = pooled[(pooled.score == score) & (pooled.fa_day <= cap)]
        if det:
            q = q[q.detector == det]
        if not len(q):
            return 0.0, None
        r = q.loc[q.sens.idxmax()]
        return float(r.sens), dict(detector=r.detector, param=float(r.param), top=float(r.top),
                                   tp=int(r.tp), fp=int(r.fp), fa_day=round(float(r.fa_day), 2))

    tab = []
    for sc in ("G0", "F", "B"):
        for det in ("D1", "D2"):
            b25, c25 = best(sc, det); b15, _ = best(sc, det, 15); b10, _ = best(sc, det, 10)
            tab.append(dict(score=sc, detector=det, sens_fa25=b25, sens_fa15=b15, sens_fa10=b10, cell25=c25))
    tab = pd.DataFrame(tab)
    bB, _ = best("B"); bF, _ = best("F"); bG, _ = best("G0")
    r1 = bB >= max(bF, bG) and bB >= bG + 0.10
    adopted = "B" if r1 else (None if bF > bB else "G0")
    r2_lines, r2_res = [], {}
    for sc in ("G0", "F", "B"):
        d1, c1 = best(sc, "D1"); d2, c2 = best(sc, "D2")
        det = "D2" if d2 >= d1 - 0.02 else "D1"
        r2_res[sc] = (det, c2 if det == "D2" else c1)
        r2_lines.append(f"- R2 on score {sc}: D1 {d1:.3f} vs D2 {d2:.3f} -> {det}")
    if adopted:
        frozen = f"score {adopted}, detector {r2_res[adopted][0]}, cell {r2_res[adopted][1]}"
    else:
        frozen = "NONE -- F alone beats B; supervisor decides between F and B before any test run"
    lines = ["# E7 -- 4-branch ensemble (B) and change-point segment detector (D2)\n",
             "## Best pooled sensitivity at FA/day caps (15 non-test subjects, SzCORE)\n", "```",
             tab.drop(columns="cell25").round(3).to_string(index=False), "```\n",
             "Cells at FA/day <= 25:\n", "```", tab[["score", "detector", "cell25"]].to_string(index=False), "```\n",
             f"- R1: B {bB:.3f} vs F {bF:.3f} vs G0 {bG:.3f} -> B {'ADOPTED' if r1 else 'NOT adopted'}"
             + ("" if r1 else (" (F alone is better than B: report, supervisor decides)" if bF > bB else "")),
             *r2_lines,
             f"\n**FROZEN for the one-shot test: {frozen}**\n",
             "## Per subject AUROC\n", "```", ps.round(4).to_string(), "```",
             f"\nElapsed {time.time()-t0:.0f} s."]
    (OUT / "SUMMARY.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines[:25]))


if __name__ == "__main__":
    main()
