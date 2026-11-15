#!/usr/bin/env python
"""
r2_rpsdevx.py -- research track, stage RP, path 2: diagnosis of the slow RP_SERIES pass A (docs/FUTURE_RESEARCH_PLAN.md
§12 15/11 10:30, D27-F; approved by the author 15/11 10:12). Kaggle CPU, notebook RPS_DEVX (src/r2_rpsdevx_make_notebook.py).

WHY. The RP_SERIES rerun with fix B took 16,054 s for chb10 (first run 15,052 s) while the test patients took 64-108 s;
the components that only development patients run (e16 arms, D1b grid, Table 7: locked PELT, E7 D2, E10) had been timed
on test-patient values only. Candidate causes, to be told apart on the real development series before any fix
(instructions §1 item 18): H1 the locked PELT of Table 7 (pure-Python ruptures on the whole patient timeline) is
~quadratic on these series; H2 the exact E7 D2 recomputes too many candidates on them; H3 another component.

WHAT. The path-2 final scalar of the 15 development patients (seeds 1-4), computed exactly as RP_SERIES does it
(r2_rps.model_outputs_z -> r2_r1.chb_ctx -> e22_test_oneshot.final_scalar), with the window masks the Table 7 detectors
read, exported as scores_dev/<case>.csv.gz (window, file_idx, t_in_file_s, ok, ictal, buffer, flag5sd, x_s1..x_s4 at
full float64 precision, %.17g). Derived scores, not EEG (like rp2/scores). The timing of every component on them is then
measured in the build container (src/r2_rpsdevx_timing.py), not here.
Gates (STOP): G-data (the 63 dataset files = the pinned hashes), versions (mode exact / tolerance), RS.0-dev (the
run_budget rows of the 15 development patients, seeds 1-4, 4 arms x 3 stages, from these x = rp2/per_subject.csv incl.
every error pair and q_raw, as RP_SERIES' RS.0 for the development set).
Outputs: WORK/r2/r1_system/rps_devx/ (-> results/r2/r1_system/rps_devx/): gates.json, run_meta.json, rs0/, scores_dev/,
timing.csv, SUMMARY.md. Test: src/r2_rpsdevx_synthetic_test.py.
"""
import time
import traceback
from pathlib import Path

import numpy as np
import pandas as pd

import r2_rps as RS
RP, R1 = RS.RP, RS.R1
TAG = "rps_devx"
DEV, TAGS, SEED_N = RS.DEV, RS.TAGS, RS.SEED_N


def job(a):
    """one development patient: distances, final scalar of the 4 seeds, run_budget rows (RS.0-dev), the exported file."""
    case, ckpt_dir, kmap, outdir = a
    t = time.time()
    try:
        RS.PD.CKPT = Path(ckpt_dir)
        z, _ = R1.load_case(case, "new")
        idx, D, _ = RS.model_outputs_z(z)
        Ds = {t_: D[t_].astype(np.float32) for t_ in R1.TAGS}
        ctx = R1.chb_ctx(case, z, idx, Ds)
        rows, errs, qs, X = [], [], [], {}
        for tag in R1.TAGS:
            x = RS.E22.final_scalar(ctx, tag)
            X[tag] = x
            q = RS.P3L.q_of(RS.PS.smoothed(ctx, RS.P3L.member_mean_z(ctx, tag), RS.P3C.SMOOTH), kmap[tag])
            qs.append(dict(set="development", subject=case, seed=tag, k=kmap[tag], q_raw=q))
            for name, (fl, cp) in R1.ARMS.items():
                RS.P3C.run_budget(ctx, case, tag, x, q, fl, cp, name, rows, errs)
        for r in rows + errs:
            r["set"] = "development"
        fidx = z["file_idx"].astype(int)
        tif = np.zeros(len(fidx), int)
        for f in np.unique(fidx):
            m = np.flatnonzero(fidx == f)
            tif[m] = np.arange(len(m)) * RS.WIN
        df = pd.DataFrame(dict(window=np.arange(len(fidx)), file_idx=fidx, t_in_file_s=tif,
                               ok=(~z["is_signal_loss"].astype(bool)).astype(int), ictal=z["is_ictal"].astype(int),
                               buffer=z["is_buffer"].astype(int), flag5sd=z["is_flag5sd"].astype(int)))
        for tag in TAGS:
            df[f"x_s{SEED_N[tag]}"] = X[tag]
        o = Path(outdir) / "scores_dev"                 # a spawned worker has no run state: the path comes in the spec
        o.mkdir(parents=True, exist_ok=True)
        df.to_csv(o / f"{case}.csv.gz", index=False, float_format="%.17g")
        return dict(case=case, rows=rows, errs=errs, q=qs, windows=int(len(fidx)), s=round(time.time() - t, 1))
    except SystemExit as e:
        return dict(case=case, error=f"STOP: {e}")
    except Exception:                    # noqa: BLE001
        return dict(case=case, error=traceback.format_exc()[-3000:])


def run(workers):
    t = time.time()
    kmap = {k: float(v) for k, v in RS.json.loads((RS.RP_DIR / "rp2" / "k.json").read_text())["k"].items() if k in TAGS}
    ck = RP.ckpt_dir_all(RS.RP_DIR / "models")
    specs = sorted([(c, str(ck), kmap, str(R1.out_dir())) for c in DEV], key=lambda s: -R1._size(s[0], "new"))
    res = {r["case"]: r for r in RP._run(job, specs, workers, TAGS, "devx")}
    R1.phase("devx", t)
    mode = RP.STATE["mode"]
    tol = RP.TOL[mode]
    rows = pd.DataFrame([r for c in DEV for r in res[c]["rows"]])
    errs = pd.DataFrame([r for c in DEV for r in res[c]["errs"]])
    q = pd.DataFrame([r for c in DEV for r in res[c]["q"]])
    o = R1.out_dir() / "rs0"
    o.mkdir(parents=True, exist_ok=True)
    rows.to_csv(o / "per_subject.csv", index=False); errs.to_csv(o / "errors.csv", index=False); q.to_csv(o / "q.csv", index=False)
    keep = lambda df: df[df.seed.isin(TAGS) & (df["set"] == "development")]   # noqa: E731
    ref_rows = keep(pd.read_csv(RS.RP_DIR / "rp2" / "per_subject.csv"))
    ref_errs = keep(pd.read_csv(RS.RP_DIR / "rp2" / "errors.csv"))
    ref_q = keep(pd.read_csv(RS.RP_DIR / "rp2" / "q.csv"))
    n, exact, bad = RP._cmp_rows(rows, ref_rows, mode)
    ne, ebad = RP._cmp_errors(errs, ref_errs)
    qm = q.merge(ref_q, on=["set", "subject", "seed"], suffixes=("", "_ref"), how="outer", indicator=True)
    qrel = (qm.q_raw - qm.q_raw_ref).abs() / qm.q_raw_ref.abs().clip(lower=1e-12)
    qbad = int((qm._merge != "both").sum() + (qrel > tol["float_rel"]).sum())
    n_want = len(DEV) * len(TAGS) * len(R1.ARMS) * 3
    files = sorted((R1.out_dir() / "scores_dev").glob("*.csv.gz"))
    ok = (n == n_want and not bad and len(files) == len(DEV)
          and (mode == "tolerance" or (not ebad and not qbad and exact == n)))
    pd.DataFrame([dict(case=c, windows=res[c]["windows"], s=res[c]["s"]) for c in DEV]).to_csv(
        R1.out_dir() / "timing.csv", index=False)
    R1.gate(dict(gate="RS.0-dev", status="PASS" if ok else "FAIL", mode=mode, rows=n, rows_expected=n_want, exact_rows=exact,
                 mismatches=bad[:30], error_pairs=ne, error_groups_differ=len(ebad), q_differ=qbad, files=len(files),
                 summary=f"mode {mode}: {n} rows ({exact} exact, expected {n_want}), {ne} error pairs ({len(ebad)} groups "
                         f"differ), q {qbad} differ, {len(files)} score files"))


def summary_md():
    L = [f"# RPS_DEVX — development final scores of the path-2 model (diagnosis export; no research number)\n",
         "| gate | status | summary |", "|---|---|---|"]
    L += [f"| {g['gate']} | {g['status']} | {g.get('summary', '')} |" for g in R1.STATE["gates"]]
    L += ["", f"Phases (s): {R1.jdumps(R1.STATE['phases'])}", "",
          "Timing of the Table 7 / e16 components on these series: `python src/r2_rpsdevx_timing.py` (container)."]
    (R1.out_dir() / "SUMMARY.md").write_text("\n".join(L) + "\n")
    return "\n".join(L)
