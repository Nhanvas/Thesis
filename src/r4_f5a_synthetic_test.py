#!/usr/bin/env python
"""r4_f5a_synthetic_test.py -- tests of the F5a run and aggregate on SYNTHETIC data (build container only; never on Kaggle).
Design results/r4_f5a/DESIGN_F5A.md §7.

World: src/r2_r1_synthetic_test.build_world (23 CHB-MIT-like cases in v9-x3-fold1/3, chb24 / PN00 / PN01 as external
features, four randomly initialised checkpoints) and its RECORD_GEN (the fake record files made by r2_r1's own R1.0
path). So R1.0 / GE test the mechanics here; equivalence with the real V5 record is gate R1.0 on Kaggle.
Checks:
  S1  the F5A_V5 notebook (src/r4_f5a_make_notebook.py, run cell by cell in a fresh interpreter, 2 workers): every gate
      PASS (G-self, G-data, SMOKE, R1.0-dev / -test, GE, G-k, G-eng, G-seg, G-mf, G-worker-sha); outputs written
  S1b (non-circular) an independent "abl" file made by p3c_freeze.run_budget directly on the record bookkeeping
      (abl_gen.py, no r4_f5a code); the aggregate on the run: A0-A3 PASS, every table written
  S2  planted worlds for the analysis functions: post-ictal plateau (return time = plateau length; the 3-change-point
      fit puts its 2nd point at the offset and its 3rd at the plateau end), abrupt symmetric seizure (return 0, fall and
      rise short), slow ramp (fall >> rise); bootstrap and within-patient correlation on planted data
Negative paths: one p3c_freeze row tp + 1 -> STOP R1.0-dev in the SMOKE; one module edited after the build -> the
notebook refuses to start; one stored series value altered inside a search window -> aggregate STOP A3.
  python src/r4_f5a_synthetic_test.py [--root DIR]
"""
import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import r2_r1_synthetic_test as W        # noqa: E402  (world builder, record generator, notebook runner: unchanged)

ABL_GEN = r'''
# abl_gen.py: an independent V0 "abl" record for the synthetic world -- p3c_freeze.run_budget called directly on the
# record bookkeeping (r2_r1.ctx_from_store on the record generator's distances), arms own = L2f, fixed = frozen
import os, sys
from pathlib import Path
import numpy as np, pandas as pd
if __name__ == "__main__":
    sys.path.insert(0, os.environ["R1_SRC"])
    import r2_r1 as R1
    PS, P3L, P3C, E22 = R1.PS, R1.P3L, R1.P3C, R1.E22
    R1.STATE["tag"] = "ablgen"
    R1.build_views()
    rows, errs = [], []
    for c, src in [(c, "earlier") for c in R1.DEV + R1.TEST] + [(c, "ext") for c in R1.EXT]:
        ctx, _ = R1.ctx_from_store(c, src, "gen")
        st = "external" if src == "ext" else ("development" if c in R1.DEV else "test")
        for t in R1.TAGS:
            x = E22.final_scalar(ctx, t)
            q = P3L.q_of(PS.smoothed(ctx, P3L.member_mean_z(ctx, t), 5), R1.K_RECORD)
            r_, e_ = [], []
            for arm, rec in (("own", "L2f"), ("fixed", "frozen")):
                fl, cp = R1.ARMS[rec]
                P3C.run_budget(ctx, c, t, x, q, fl, cp, arm, r_, e_)
            rows += [dict(r, variant="V0", set=st) for r in r_]
            errs += [dict(e, variant="V0", set=st) for e in e_]
    out = Path(os.environ["ABL_OUT"]); out.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(out / "per_subject.csv", index=False)
    pd.DataFrame(errs).to_csv(out / "errors.csv", index=False)
    print("abl generated", len(rows), "rows", len(errs), "pairs")
'''


def gates(work):
    return {g["gate"]: g for g in json.loads((work / "r4" / "f5a_v5" / "gates.json").read_text())}


def s2_planted():
    import r4_f5a_aggregate as AG
    rng = np.random.default_rng(1)
    t = np.arange(0, 1200, 4)
    on, off = 600, 660
    ok = np.ones(len(t), bool)

    def base():
        return rng.normal(0, 0.05, len(t))
    # (i) post-ictal plateau of 60 s at half height
    v = base(); v[(t >= on) & (t < off)] += 1.0; v[(t >= off) & (t < off + 60)] += 0.5
    p = AG.profile_one(t, v, ok, on, off, 3)
    assert p["pre_ok"] and abs(p["ret"] - 60) <= 8 and not p["ret_cens"], p
    aw, bw = on // 4, (off + 60) // 4                      # a detector event spanning seizure + plateau
    k3 = AG.cpd_k(v, ok, aw, bw, 15, 3)
    assert abs(k3[0] * 4 - on) <= 8 and abs(k3[1] * 4 - off) <= 8 and abs(k3[2] * 4 - (off + 60)) <= 8, k3
    # (ii) abrupt symmetric seizure
    v = base(); v[(t >= on) & (t < off)] += 1.0
    p = AG.profile_one(t, v, ok, on, off, 3)
    assert p["ret"] <= 4 and p["rise"] <= 8 and p["fall"] <= 8 and p["ret_null"] <= 12, p
    import e18_cpd_localizer as E18
    ca, cb, used = E18.cpd_event(v, ok, on // 4, off // 4, 15)
    assert used and abs(ca * 4 - on) <= 4 and abs(cb * 4 - off) <= 4, (ca, cb)
    # (iii) slow ramp after the offset (60 s linear decay) with an abrupt onset
    v = base(); v[(t >= on) & (t < off)] += 1.0
    r = (t >= off) & (t < off + 60); v[r] += 1.0 - (t[r] - off) / 60
    p = AG.profile_one(t, v, ok, on, off, 3)
    assert p["fall"] >= 40 and p["rise"] <= 8 and p["fall"] - p["rise"] >= 32, p
    # bootstrap and within-patient correlation on planted data
    d = pd.DataFrame(dict(subject=np.repeat([f"s{i}" for i in range(8)], 10)))
    d["x"] = rng.normal(0, 1, len(d)); d["y"] = 2 * d.x + rng.normal(0, 0.3, len(d))
    d["x"] += np.repeat(np.arange(8) * 10.0, 10)            # between-patient offsets must not matter
    rho = AG.within_spearman(d, "x", "y")
    e, lo, hi = AG.boot_stat(d, lambda q: AG.within_spearman(q, "x", "y"), b=500)
    assert rho > 0.9 and lo > 0.8, (rho, lo, hi)
    d2 = pd.DataFrame(dict(subject=["chb01"] * 5 + ["chb21"] * 5 + ["chb03"] * 5, v=np.arange(15.0)))
    assert len(np.unique(AG.units_of(d2.subject))) == 2
    print("S2 PASS: plateau (return 60 s; 3 change points at onset / offset / plateau end), abrupt (return 0, "
          "localizer at the boundaries), ramp (fall >> rise); within-patient rho; chb01 + chb21 one unit")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="/tmp/f5a_synth")
    a = ap.parse_args()
    t0 = time.time()
    s2_planted()
    root = Path(a.root)
    repo, inp = W.build_world(root)
    for name, body in (("record_gen.py", W.RECORD_GEN), ("runner.py", W.RUNNER), ("abl_gen.py", ABL_GEN)):
        (root / name).write_text(body)
    base = dict(R2_TEST="1", THESIS_REPO=str(repo), R2_INPUT=str(inp), R1_SRC=str(repo / "src"), OMP_NUM_THREADS="1",
                OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1", PYTHONHASHSEED="0")
    print(W.run(root / "record_gen.py", dict(base, R2_WORK=str(root / "gen_work"), R2_SCRATCH=str(root / "gen_scratch")))[-300:])
    abl = root / "abl"
    print(W.run(root / "abl_gen.py", dict(base, R2_WORK=str(root / "gen_work"), R2_SCRATCH=str(root / "gen_scratch"),
                                          ABL_OUT=str(abl)))[-200:])
    nbdir = root / "notebooks"
    subprocess.check_call([sys.executable, str(ROOT / "src" / "r4_f5a_make_notebook.py")],
                          env=dict(os.environ, F5A_NB_OUTDIR=str(nbdir)))
    nb = nbdir / "F5A_V5.ipynb"

    def nb_env(tag):
        return dict(F5A_TEST_REPO=str(repo), F5A_TEST_INPUT=str(inp), F5A_TEST_WORK=str(root / f"work_{tag}"),
                    F5A_TEST_SCRATCH=str(root / f"scratch_{tag}"), F5A_WORKERS="2", PYTHONHASHSEED="0")

    # ---- S1: the full notebook
    t = time.time()
    print(W.run(root / "runner.py", nb_env("ok"), [nb])[-2500:])
    print(f"S1 notebook {time.time() - t:.0f} s")
    work = root / "work_ok"
    g = gates(work)
    want = ["G-self", "G-data", "SMOKE", "R1.0-dev", "R1.0-test", "GE", "G-k", "G-eng[smoke]", "G-eng[full]",
            "G-seg[full]", "G-mf[full]", "G-worker-sha[full]"]
    assert all(g.get(w, {}).get("status") == "PASS" for w in want), {w: g.get(w, {}).get("status") for w in want}
    out = work / "r4" / "f5a_v5"
    for f in ("events.csv", "seizures.csv", "series.csv.gz", "jobs.csv", "projection.json", "SUMMARY.md",
              "r10/dev_per_subject.csv", "smoke/events.csv"):
        assert (out / f).exists(), f
    E = pd.read_csv(out / "events.csv")
    Sz = pd.read_csv(out / "seizures.csv")
    assert Sz.subject.nunique() == 26 and E.subject.nunique() >= 20, (Sz.subject.nunique(), E.subject.nunique())
    assert set(E.arm) == {"own", "fixed"} and E.seed.nunique() == 4
    print(f"S1 PASS: every gate; {len(E)} pairs, {E.subject.nunique()} cases")

    # ---- S1b: aggregate with the independent abl record
    env = dict(os.environ, THESIS_REPO=str(ROOT))
    p = subprocess.run([sys.executable, str(ROOT / "src" / "r4_f5a_aggregate.py"), "--run", str(out), "--abl", str(abl),
                        "--out", str(root / "agg"), "--b", "200"], env=env, capture_output=True, text=True)
    print(p.stdout[-3000:], p.stderr[-3000:])
    assert p.returncode == 0 and "AGGREGATE DONE" in p.stdout, "aggregate failed"
    for f in ("gates.json", "V1_detection.csv", "V2_boundaries.csv", "D1_per_patient.csv", "D3_seizure_profiles.csv",
              "D4_D5_pairs.csv", "D2_strata.csv", "H_items.csv", "T_F5A.md"):
        assert (root / "agg" / f).exists(), f
    ga = json.loads((root / "agg" / "gates.json").read_text())
    assert all(x["status"] == "PASS" for x in ga), ga
    print("S1b PASS: aggregate A0-A3 on an independent abl record; every table written")

    # ---- negative paths
    sp = out / "series.csv.gz"
    keep = sp.read_bytes()
    S = pd.read_csv(sp)
    ev = E[E.used_cpd].iloc[0]
    sz = pd.read_csv(out / "seizures.csv")
    sid = sz[(sz.subject == ev.subject) & (sz.file == ev.file) & (sz.ref_on == ev.ref_on)].sz.iloc[0]
    col = f"x{ev.seed.split('seed')[1]}"
    sel = (S.sz == sid) & (S.w >= ev.win_a // 4) & (S.w < ev.win_b // 4)
    S.loc[sel, col] = 0.5                                   # a flat search window: the localizer must fall back
    S.to_csv(sp, index=False, compression="gzip")
    p = subprocess.run([sys.executable, str(ROOT / "src" / "r4_f5a_aggregate.py"), "--run", str(out), "--abl", str(abl),
                        "--out", str(root / "agg_neg"), "--b", "50"], env=env, capture_output=True, text=True)
    assert p.returncode != 0 and "STOP A3" in (p.stdout + p.stderr), (p.stdout[-800:], p.stderr[-800:])
    sp.write_bytes(keep)
    print("NEG-A3 PASS: an altered stored series value stops the aggregate at A3")
    rec = repo / "results" / "p3c_freeze" / "per_subject.csv"
    keepr = rec.read_text()
    d = pd.read_csv(rec)
    j = d[(d.subject == "chb01") & (d.budget == "L2f") & (d.stage == "cpd")].index[0]
    d.loc[j, "tp"] += 1
    d.to_csv(rec, index=False)
    W.run(root / "runner.py", nb_env("neg1"), [nb], expect_fail="R1.0-dev")
    assert not (root / "work_neg1" / "r4" / "f5a_v5" / "events.csv").exists()
    rec.write_text(keepr)
    print("NEG1 PASS: a changed record row stops the SMOKE (R1.0-dev) before the full run")
    m = repo / "src" / "e18_cpd_localizer.py"
    keepm = m.read_text()
    m.write_text(keepm + "\n# edited\n")
    W.run(root / "runner.py", nb_env("neg2"), [nb], expect_fail="modules differ")
    m.write_text(keepm)
    print("NEG2 PASS: an edited module stops the notebook before it starts")
    print(f"ALL PASS in {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
