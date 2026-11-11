#!/usr/bin/env python
"""r2_rp_synthetic_test.py -- end-to-end test of RP_RUN and src/r2_rp_aggregate.py on SYNTHETIC feature files (build
container only). Reuses the stage-R1 synthetic world (src/r2_r1_synthetic_test.py): fake datasets, fake record, then the
real R1_RUN notebook (3 epochs) produces the "committed R1 output" that RP_RUN reads. So RP.0 compares this stage's new
per-seed-k path with rows written by r2_r1.score_job (non-circular).
Checks:
  N2  RP views + r2_r1.train_job (seed 1, 3 epochs) = the R1_RUN seed-1 checkpoint bit for bit, same final_val
  RP_RUN PASS in mode exact: every gate; RP.0 all rows exact; seed 42 at its own k = R1's k; outputs and scores present
  aggregate: A0 (on the synthetic R1 aggregate), A1 PASS, every table; A0 on the REAL R1 files of this clone PASS
  negative paths: one R1 row tp + 1 -> STOP RP.0; one pinned hash -> STOP G-data; one R1 final_val changed -> STOP
  G-val; demo_model.json seed changed -> aggregate STOP A1
  tolerance mode: R1 run_meta numpy version changed -> RP_RUN runs in mode tolerance and PASSES
  resume: previous RP output attached -> seed 4 reused, rp2 rows byte-identical
  python src/r2_rp_synthetic_test.py [--root DIR]
"""
import argparse
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("r1t", ROOT / "src" / "r2_r1_synthetic_test.py")
T1 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(T1)

CHECK_N2 = r'''
import json, os, sys
from pathlib import Path
if __name__ == "__main__":
    sys.path[:0] = [os.environ["R1_SRC"]]
    import torch, r2_rp as RP
    R1 = RP.R1
    R1.STATE["tag"] = "n2"
    V = RP.build_views()
    exp, exp_val = R1.expected_counts(V)
    out = R1.out_dir() / "models"
    r = R1.train_job((1, int(os.environ["R2_TEST_EPOCHS"]), out, R1.out_dir() / "training", exp, exp_val, False))
    assert r["status"] == "done", r
    a = torch.load(out / "gae_v2_clean_seed1.pt"); b = torch.load(RP.R1_RUN / "models" / "gae_v2_clean_seed1.pt")
    assert a.keys() == b.keys() and all(torch.equal(a[k], b[k]) for k in a), "weights differ"
    ja = json.loads((out / "gae_v2_clean_seed1.json").read_text()); jb = json.loads((RP.R1_RUN / "models" / "gae_v2_clean_seed1.json").read_text())
    assert ja["final_val"] == jb["final_val"], (ja["final_val"], jb["final_val"])
    print("N2: RP views + r2_r1.train_job reproduce the R1 seed-1 checkpoint bit for bit (final_val equal)")
'''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="/tmp/r2_rp_synth")
    a = ap.parse_args()
    t0 = time.time()
    root = Path(a.root)
    repo, inp = T1.build_world(root)
    for name, body in (("record_gen.py", T1.RECORD_GEN), ("runner.py", T1.RUNNER), ("check_n2.py", CHECK_N2)):
        (root / name).write_text(body)
    base = dict(R2_TEST="1", THESIS_REPO=str(repo), R2_INPUT=str(inp), R1_SRC=str(repo / "src"), OMP_NUM_THREADS="1",
                OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1", PYTHONHASHSEED="0")
    T1.run(root / "record_gen.py", dict(base, R2_WORK=str(root / "gen_work"), R2_SCRATCH=str(root / "gen_scratch")))
    # the pinned hashes (what R1_SMOKE commits): every dataset file
    sys.path[:0] = [str(repo / "src")]
    import r2_core as R0
    ds = inp / "datasets/u/thesis-r2-chbmit-features/thesis-r2-chbmit-features"
    dx = inp / "datasets/u/thesis-r2-external-features/thesis-r2-external-features"
    rows = [dict(dataset="thesis-r2-chbmit-features", file=p.name, sha256=R0.sha256_file(p)) for p in sorted(ds.glob("chb*"))
            if p.suffix in (".npz", ".json")] + \
           [dict(dataset="thesis-r2-external-features", file=p.name, sha256=R0.sha256_file(p)) for p in sorted(dx.glob("*_lf.npz"))]
    pin = repo / "results/r2/r1_system/smoke"
    pin.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(pin / "data_sha256.csv", index=False)
    assert len(rows) == 24 * 2 + 3, len(rows)
    # the "committed" R1_RUN output: the real R1_RUN notebook on the synthetic world (3 epochs), then its aggregate
    nbdir = root / "notebooks"
    env_b = dict(os.environ, R2_NB_OUTDIR=str(nbdir))
    subprocess.check_call([sys.executable, str(ROOT / "src" / "r2_r1_make_notebooks.py"), "--run", "0" * 40], env=env_b)

    def nb_env(tag, extra=None):
        e = dict(R2_TEST_REPO=str(repo), R2_TEST_INPUT=str(inp), R2_TEST_WORK=str(root / f"work_{tag}"),
                 R2_TEST_SCRATCH=str(root / f"scratch_{tag}"), R2_TEST="1", R2_TEST_EPOCHS="3", OMP_NUM_THREADS="1",
                 PYTHONHASHSEED="0")
        e.update(extra or {})
        return e
    print(T1.run(root / "runner.py", nb_env("r1"), [nbdir / "R1_RUN.ipynb"])[-400:])
    r1 = repo / "results/r2/r1_system/run"
    shutil.copytree(root / "work_r1/r2/r1_system/run", r1)
    ncases = json.dumps({"development": 15, "test": 8, "chb24": 1, "siena": 2})
    agg1 = dict(R2_TEST="1", THESIS_REPO=str(repo), PYTHONHASHSEED="0", R2_TEST_N_CASES=ncases)
    T1.run(repo / "src" / "r2_r1_aggregate.py", agg1, ["--run", r1])
    print("synthetic R1 output + its aggregate written as the committed R1 record")
    # N2
    print(T1.run(root / "check_n2.py", dict(base, R2_WORK=str(root / "n2_work"), R2_SCRATCH=str(root / "n2_scratch"),
                                            R2_TEST_EPOCHS="3")))
    # RP_RUN (mode exact)
    subprocess.check_call([sys.executable, str(ROOT / "src" / "r2_rp_make_notebooks.py"), "--run", "0" * 40], env=env_b)
    nb = nbdir / "RP_RUN.ipynb"
    print(T1.run(root / "runner.py", nb_env("rp"), [nb])[-1500:])
    rp = root / "work_rp/r2/r1_system/rp"
    g = {x["gate"]: x for x in json.loads((rp / "gates.json").read_text())}
    want = ["G-data", "G-const-new", "RP.0", "G-vec", "G-val", "R1.1-training", "RP2-complete", "RP3-demo"]
    assert all(g[w]["status"] == "PASS" for w in want), {w: g.get(w, {}).get("status") for w in want}
    assert g["RP.0"]["mode"] == "exact" and g["RP.0"]["exact_rows"] == g["RP.0"]["rows"] == (15 + 8 + 3) * 4 * 4 * 3, g["RP.0"]
    assert g["RP.0"]["k_rel"] == 0 and g["G-val"]["detail"]["clean_seed1"]["rel"] == 0, g["G-val"]
    assert g["R1.1-training"]["trained_now"] == [4], g["R1.1-training"]
    for f in ("rp2/per_subject.csv", "rp2/errors.csv", "rp2/q.csv", "rp2/k.json", "rp2/thresholds.csv", "demo_model.json",
              "models/gae_v2_clean_seed4.pt", "models/gae_v2_clean_seed4.json", "SUMMARY.md", "data_sha256.csv"):
        assert (rp / f).exists(), f
    sc = sorted(p.name for p in (rp / "rp2/scores").glob("*.csv.gz"))
    assert sc == sorted(f"{c}.csv.gz" for c in ["chb03", "chb06", "chb13", "chb14", "chb15", "chb16", "chb17", "chb18",
                                                "chb24", "PN00", "PN01"]), sc
    s3 = pd.read_csv(rp / "rp2/scores/chb03.csv.gz")
    assert {"x_s1", "xs_s1", "x_s4", "xs_s4", "ictal", "ok", "file_idx", "t_in_file_s"} <= set(s3.columns)
    th = pd.read_csv(rp / "rp2/thresholds.csv")
    assert len(th) == 11 * 4 * 4, len(th)
    k = json.loads((rp / "rp2/k.json").read_text())
    assert k["k"]["clean_seed42"] == json.loads((r1 / "r13/run/k.json").read_text())["k"]
    R = pd.read_csv(rp / "rp2/per_subject.csv")
    Rr = pd.read_csv(r1 / "r13/run/per_subject.csv")
    m = R.merge(Rr, on=["set", "subject", "seed", "budget", "stage"], suffixes=("", "_r1"))
    s42 = m[m.seed == "clean_seed42"]
    assert len(s42) == 26 * 12 and (s42.tp == s42.tp_r1).all() and (s42.fp == s42.fp_r1).all()
    fz = m[(m.budget == "frozen")]
    assert (fz.tp == fz.tp_r1).all() and (fz.fp == fz.fp_r1).all()
    print("RP_RUN PASS (mode exact; RP.0 every row exact; seed 42 and frozen rows = R1; 11 score files)")
    # aggregate
    agg = dict(agg1)
    T1.run(repo / "src" / "r2_rp_aggregate.py", agg, ["--rp", rp])
    ga = {x["gate"]: x for x in json.loads((rp / "aggregate/gates.json").read_text())}
    assert ga["A0"]["status"] == "PASS" and ga["A1"]["status"] == "PASS", ga
    for f in ("summary.csv", "summary_per_seed.csv", "per_subject.csv", "per_subject_mean.csv", "final_vs_heldout.csv",
              "k.csv", "correction.csv", "errors.csv", "errors_per_seed.csv", "review.csv", "demo.csv", "SUMMARY.md"):
        assert (rp / "aggregate" / f).exists(), f
    F = pd.read_csv(rp / "aggregate/summary.csv")
    assert (F.seeds == 4).all() and F.sens_ci_lo.notna().all()
    print("aggregate PASS (A0, A1; every table)")
    env_real = {k_: v for k_, v in os.environ.items() if not k_.startswith("R2_TEST")}
    env_real["THESIS_REPO"] = str(ROOT)
    p = subprocess.run([sys.executable, str(ROOT / "src/r2_rp_aggregate.py"), "--a0-only"], env=env_real,
                       capture_output=True, text=True)
    assert p.returncode == 0 and "A0 PASS" in p.stdout, p.stdout + p.stderr
    print("aggregate A0 on the REAL R1 files of this clone: PASS")
    # aggregate negative: demo seed changed
    dj = rp / "demo_model.json"
    keep = dj.read_bytes()
    d = json.loads(keep); d["seed"] = 1 if d["seed"] != 1 else 2
    dj.write_text(json.dumps(d))
    T1.run(repo / "src" / "r2_rp_aggregate.py", agg, ["--rp", rp, "--out", root / "agg_neg"], expect_fail="STOP A1")
    dj.write_bytes(keep)

    # negative paths of RP_RUN
    def perturb_csv(path, fn):
        keep = path.read_bytes()
        df = pd.read_csv(path)
        fn(df)
        df.to_csv(path, index=False)
        return keep
    f = r1 / "r13/run/per_subject.csv"
    keep = perturb_csv(f, lambda d: d.__setitem__("tp", d.tp + (d.index == 7)))
    T1.run(root / "runner.py", nb_env("neg_rp0"), [nb], expect_fail="RP.0 FAIL")
    f.write_bytes(keep)
    keep = perturb_csv(pin / "data_sha256.csv", lambda d: d.__setitem__("sha256", d.sha256.where(d.index != 4, "0" * 64)))
    T1.run(root / "runner.py", nb_env("neg_data"), [nb], expect_fail="G-data FAIL")
    (pin / "data_sha256.csv").write_bytes(keep)
    jf = r1 / "models/gae_v2_clean_seed2.json"
    keep = jf.read_bytes()
    j = json.loads(keep); j["final_val"] *= 1.0001
    jf.write_text(json.dumps(j, indent=1))
    T1.run(root / "runner.py", nb_env("neg_val"), [nb], expect_fail="G-val FAIL")
    jf.write_bytes(keep)
    print("RP_RUN negative paths: RP.0, G-data, G-val -> STOP; aggregate demo seed changed -> STOP A1")
    # tolerance mode
    mf = r1 / "run_meta.json"
    keep = mf.read_bytes()
    mm = json.loads(keep); mm["versions"]["numpy"] = "0.0.0"
    mf.write_text(json.dumps(mm, indent=1))
    T1.run(root / "runner.py", nb_env("tol"), [nb])
    gt = {x["gate"]: x for x in json.loads((root / "work_tol/r2/r1_system/rp/gates.json").read_text())}
    assert gt["RP.0"]["mode"] == "tolerance" and all(gt[w]["status"] == "PASS" for w in want), gt["RP.0"]
    mf.write_bytes(keep)
    print("tolerance mode (versions differ): RP_RUN PASS")
    # resume
    prev = inp / "datasets/u/rp-run-v1"
    shutil.copytree(root / "work_rp", prev)
    T1.run(root / "runner.py", nb_env("rp2"), [nb])
    g2 = {x["gate"]: x for x in json.loads((root / "work_rp2/r2/r1_system/rp/gates.json").read_text())}
    assert g2["R1.1-training"]["trained_now"] == [], g2["R1.1-training"]
    for f in ("per_subject.csv", "errors.csv", "q.csv", "thresholds.csv"):
        assert (root / "work_rp2/r2/r1_system/rp/rp2" / f).read_bytes() == (rp / "rp2" / f).read_bytes(), f
    shutil.rmtree(prev)
    print("resume: seed 4 reused, rp2 rows byte-identical")
    print(f"ALL PASS ({time.time() - t0:.0f} s)")


if __name__ == "__main__":
    main()
