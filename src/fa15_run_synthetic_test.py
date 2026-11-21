#!/usr/bin/env python
"""fa15_run_synthetic_test.py -- end-to-end test of src/fa15_run.py, the notebooks FA15_RUN_CTRL / _ASR_A / _ASR_B and
src/fa15_aggregate.py on SYNTHETIC feature files (build container only; chat D35-F, 21/11). Reuses the stage-R1 / RP
synthetic world (src/r2_r1_synthetic_test.py, as src/r2_rp_synthetic_test.py does): fake datasets, the real R1_RUN and
RP_RUN notebooks (3 epochs) produce the "committed" control record (results/r2/r1_system/run, rp and their aggregates).
Fake ASR datasets = the R0 datasets with perturbed features (f7 x 0.8 + noise, bp5 + 0.05) and ~10 % of the non-ictal
5-SD flags flipped (labels unchanged), split over three inputs (a / b1 / b2) as the real ones.
Checks:
  FA15_RUN_CTRL (seed 5), FA15_RUN_ASR_A (seeds 42, 1), FA15_RUN_ASR_B (seeds 4, 5): every gate PASS in mode exact (G-mod
  passes by the test switch: the synthetic repository's shas differ); G-repro every row exact; the ASR runs read the ASR
  files (G-asr-data 26 cases, counts differ from R0's, training windows = the ASR counts); RUN-complete; G-worker-sha;
  machine in run_meta; the ASR scores differ from the control's
  aggregate: A0 (on the synthetic RP aggregate) / A1 / A2 PASS with the test's seed lists; every table; A0 on the REAL
  record of this clone PASS
  negative paths: one rp2 row of seed 4 tp + 1 -> STOP G-repro; one ASR label flipped -> STOP G-asr-data; a worker sha
  forced to differ -> STOP G-worker-sha; aggregate with a seed missing -> STOP A2; a run gate edited to FAIL -> STOP A1
  resume: the previous FA15_RUN_ASR_A output attached -> its seeds imported, rows byte-identical; the FA15_RUN_CTRL output
  attached to FA15_RUN_ASR_B -> NOT imported (seed 5 trained again)
  python src/fa15_run_synthetic_test.py [--root DIR]
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

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("r1t", ROOT / "src" / "r2_r1_synthetic_test.py")
T1 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(T1)
sys.path.insert(0, str(ROOT / "src"))
import fa15_make_notebooks as MK  # noqa: E402

RES = []


def check(name, ok, detail=""):
    RES.append((name, bool(ok)))
    print(f"[{'PASS' if ok else 'FAIL'}] {name} {detail}", flush=True)


def fake_asr(inp):
    """ASR-like datasets from the R0 ones: features perturbed, ~10 % of the non-ictal flags flipped, labels unchanged."""
    rng = np.random.default_rng(5)
    dc = inp / "datasets/u/thesis-r2-chbmit-features/thesis-r2-chbmit-features"
    dx = inp / "datasets/u/thesis-r2-external-features/thesis-r2-external-features"
    parts = {"a": [], "b1": [], "b2": []}
    cases = sorted(p.stem for p in dc.glob("chb*.npz") if p.stem != "chb24")
    for i, c in enumerate(cases):
        parts[["a", "b1", "b2"][i % 3]].append(c)
    for part, cs in parts.items():
        od = inp / f"datasets/u/fa15-asr-features-{part}/fa15-asr-chbmit-features-{part}"
        od.mkdir(parents=True, exist_ok=True)
        for c in cs:
            z = dict(np.load(dc / f"{c}.npz", allow_pickle=True))
            z["f7"] = (z["f7"] * 0.8 + rng.normal(0, 0.05, z["f7"].shape)).astype(z["f7"].dtype)
            z["bp5"] = (z["bp5"] + 0.05).astype(z["bp5"].dtype)
            fl = z["is_flag5sd"].copy()
            cand = np.flatnonzero(~z["is_ictal"].astype(bool) & ~z["is_buffer"].astype(bool))
            flip = rng.choice(cand, size=max(1, len(cand) // 10), replace=False)
            fl[flip] = np.logical_not(fl[flip].astype(bool)).astype(fl.dtype)
            z["is_flag5sd"] = fl
            np.savez(od / f"{c}.npz", **z)
            shutil.copyfile(dc / f"{c}_stats.json", od / f"{c}_stats.json")
    ox = inp / "datasets/u/fa15-asr-features-b2/fa15-asr-external-features-b2"
    ox.mkdir(parents=True, exist_ok=True)
    for p in sorted(dx.glob("*_lf.npz")):
        z = dict(np.load(p, allow_pickle=True))
        z["bp5"] = (z["bp5"] + 0.05).astype(z["bp5"].dtype)
        np.savez(ox / p.name, **z)
    return parts


def gates_of(d):
    return {g["gate"]: g for g in json.loads((Path(d) / "gates.json").read_text())}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="/tmp/fa15_run_synth")
    ap.add_argument("--reuse", action="store_true", help="reuse the world and control record of an earlier run in --root")
    ap.add_argument("--only-resume", action="store_true", help="only the two resume checks, on the outputs of an earlier "
                    "complete run in --root (its work_ctrl / work_asr_a)")
    a = ap.parse_args()
    t0 = time.time()
    root = Path(a.root)
    reuse = (a.reuse or a.only_resume) and (root / "repo/results/r2/r1_system/rp/aggregate/summary_per_seed.csv").exists()
    if a.only_resume:
        if not reuse:
            raise SystemExit("--only-resume needs an earlier run in --root")
        repo, inp = root / "repo", root / "input"
        for d in ("work_asr_a2", "scratch_asr_a2", "work_asr_b2", "scratch_asr_b2", "input/datasets/u/fa15-run-asr-a-v1",
                  "input/datasets/u/fa15-run-ctrl-v1"):
            shutil.rmtree(root / d, ignore_errors=True)
    elif reuse:
        repo, inp = root / "repo", root / "input"
        for d in [p for p in root.glob("work_*") if p.name not in ("work_r1", "work_rp")] + \
                 [p for p in root.glob("scratch_*") if p.name not in ("scratch_r1", "scratch_rp")] + \
                 [root / "repo/results/fa15/fa15_ctrl", root / "repo/results/fa15/fa15_asr_a",
                  root / "repo/results/fa15/fa15_asr_b"] + list(inp.glob("datasets/u/fa15-*")):
            shutil.rmtree(d, ignore_errors=True)
        for f_ in ("fa15_run.py", "fa15_aggregate.py"):
            shutil.copyfile(ROOT / "src" / f_, repo / "src" / f_)
    else:
        repo, inp = T1.build_world(root)
    for name, body in (("record_gen.py", T1.RECORD_GEN), ("runner.py", T1.RUNNER)):
        (root / name).write_text(body)
    nbdir = root / "notebooks"
    env_b = dict(os.environ, R2_NB_OUTDIR=str(nbdir))

    def nb_env(tag, extra=None):
        e = dict(R2_TEST_REPO=str(repo), R2_TEST_INPUT=str(inp), R2_TEST_WORK=str(root / f"work_{tag}"),
                 R2_TEST_SCRATCH=str(root / f"scratch_{tag}"), R2_TEST="1", R2_TEST_EPOCHS="3", OMP_NUM_THREADS="1",
                 PYTHONHASHSEED="0")
        e.update(extra or {})
        return e
    if not reuse:
        control_record(root, repo, inp, nbdir, env_b, nb_env)
    rp = repo / "results/r2/r1_system/rp"
    print(f"control record ready ({time.time() - t0:.0f} s; reused: {reuse})")
    if a.only_resume:
        resume_tests(root, inp, nbdir, nb_env, {"asr_a": root / "work_asr_a/r2/r1_system/fa15_asr_a"})
    else:
        parts = fake_asr(inp)
        run_tests(root, repo, inp, nbdir, nb_env, rp, parts, t0)
    n_ok = sum(r[1] for r in RES)
    print(f"\n{n_ok}/{len(RES)} checks PASS in {time.time() - t0:.0f} s")
    print("ALL PASS" if n_ok == len(RES) else "FAILURES: " + "; ".join(r[0] for r in RES if not r[1]))
    sys.exit(0 if n_ok == len(RES) else 1)


def control_record(root, repo, inp, nbdir, env_b, nb_env):
    """the committed control record: R1_RUN then RP_RUN on the synthetic world, with their aggregates."""
    t0 = time.time()
    base = dict(R2_TEST="1", THESIS_REPO=str(repo), R2_INPUT=str(inp), R1_SRC=str(repo / "src"), OMP_NUM_THREADS="1",
                OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1", PYTHONHASHSEED="0")
    T1.run(root / "record_gen.py", dict(base, R2_WORK=str(root / "gen_work"), R2_SCRATCH=str(root / "gen_scratch")))
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
    subprocess.check_call([sys.executable, str(ROOT / "src" / "r2_r1_make_notebooks.py"), "--run", "0" * 40], env=env_b)
    T1.run(root / "runner.py", nb_env("r1"), [nbdir / "R1_RUN.ipynb"])
    r1 = repo / "results/r2/r1_system/run"
    shutil.copytree(root / "work_r1/r2/r1_system/run", r1)
    ncases = json.dumps({"development": 15, "test": 8, "chb24": 1, "siena": 2})
    agg1 = dict(R2_TEST="1", THESIS_REPO=str(repo), PYTHONHASHSEED="0", R2_TEST_N_CASES=ncases)
    T1.run(repo / "src" / "r2_r1_aggregate.py", agg1, ["--run", r1])
    subprocess.check_call([sys.executable, str(ROOT / "src" / "r2_rp_make_notebooks.py"), "--run", "0" * 40], env=env_b)
    T1.run(root / "runner.py", nb_env("rp"), [nbdir / "RP_RUN.ipynb"])
    rp = repo / "results/r2/r1_system/rp"
    shutil.copytree(root / "work_rp/r2/r1_system/rp", rp)
    T1.run(repo / "src" / "r2_rp_aggregate.py", agg1, ["--rp", rp])
    print(f"control record (R1_RUN + RP_RUN, synthetic, 3 epochs) committed in the test repository ({time.time() - t0:.0f} s)")


def run_tests(root, repo, inp, nbdir, nb_env, rp, parts, t0):
    # notebooks
    MK.OUTDIR = nbdir
    MK.build_train("WORKTREE")
    runs = {}
    for arm, seeds in (("ctrl", [5]), ("asr_a", [42, 1]), ("asr_b", [4, 5])):
        nb = nbdir / f"{MK.TRAIN_NB[arm][0]}.ipynb"
        T1.run(root / "runner.py", nb_env(arm, dict(FA15_TEST_SEEDS=json.dumps(seeds))), [nb])
        runs[arm] = root / f"work_{arm}/r2/r1_system/fa15_{arm}"
        g = gates_of(runs[arm])
        need = ["G-mod", "G-data", "G-repro", "G-vec", "R1.1-training", "RUN-complete", "G-worker-sha"] + \
            (["G-const-new"] if arm == "ctrl" else ["G-asr-data", "G-asr-counts"])
        check(f"{arm}: every gate PASS, G-repro exact", all(g[x]["status"] == "PASS" for x in need)
              and g["G-repro"]["mode"] == "exact" and g["G-repro"]["exact_rows"] == g["G-repro"]["rows"] > 0,
              str({x: g.get(x, {}).get("status") for x in need}))
        rm = json.loads((runs[arm] / "run_meta.json").read_text())
        check(f"{arm}: run_meta holds the machine and the seeds", rm.get("machine", {}).get("cpu_model") and
              rm.get("seeds") == seeds, str(rm.get("machine")))
        for f in ("run/per_subject.csv", "run/errors.csv", "run/q.csv", "run/k.json", "run/thresholds.csv",
                  "repro/per_subject.csv", "SUMMARY.md"):
            assert (runs[arm] / f).exists(), (arm, f)
        assert all((runs[arm] / "models" / f"gae_v2_clean_seed{s}.pt").exists() for s in seeds)
    ga = gates_of(runs["asr_a"])
    jt = json.loads((runs["asr_a"] / "models/gae_v2_clean_seed42.json").read_text())
    check("asr: G-asr-data 26 cases; ASR training windows differ from R0's and the model was trained on the ASR count",
          ga["G-asr-data"]["cases"] == 26 and ga["G-asr-counts"]["n_train"] != ga["G-asr-counts"]["n_train_r0"]
          and sum(jt["n_train"].values()) == ga["G-asr-counts"]["n_train"],
          f"{ga['G-asr-counts']['n_train']} vs {ga['G-asr-counts']['n_train_r0']}")
    ad = pd.read_csv(runs["asr_a"] / "asr_data.csv")
    check("asr: every ASR file came from the three ASR inputs", ad.source.str.contains("fa15-asr-").all()
          and {p for p in ("-a/", "-b1/", "-b2/") if ad.source.str.contains(p).any()} == {"-a/", "-b1/", "-b2/"})
    rc = pd.read_csv(runs["ctrl"] / "run/per_subject.csv")
    ra = pd.read_csv(runs["asr_b"] / "run/per_subject.csv")
    m = rc.merge(ra, on=["set", "subject", "seed", "budget", "stage"], suffixes=("_c", "_a"))
    check("the ASR arm's rows differ from the control's for the same seed (5)", len(m) > 0 and
          ((m.tp_c != m.tp_a) | (m.fp_c != m.fp_a) | (m.top_c != m.top_a)).any(), f"{len(m)} rows compared")

    # aggregate
    res_dir = repo / "results/fa15"
    for arm in runs:
        shutil.copytree(runs[arm], res_dir / f"fa15_{arm}", dirs_exist_ok=True)
    agg = dict(THESIS_REPO=str(repo), PYTHONHASHSEED="0")
    args = ["--seeds-ctrl", "42,1,2,3,4,5", "--seeds-asr", "42,1,4,5", "--out", root / "reading"]
    T1.run(repo / "src" / "fa15_aggregate.py", agg, args)
    gg = {g["gate"]: g["status"] for g in json.loads((root / "reading/gates.json").read_text())}
    t1 = pd.read_csv(root / "reading/t1.csv")
    check("aggregate: A0, A1, A2 PASS; every table; T1 = 4 sets x 2 evaluations x 4 metrics; seeds-only bootstrap for chb24",
          gg == {"A0": "PASS", "A1": "PASS", "A2": "PASS"} and len(t1) == 32 and all(
              (root / "reading" / f).exists() for f in ("t2_seeds.csv", "t3_patients.csv", "t4_boundaries.csv",
                                                       "t5_data.csv", "T_PC5.md"))
          and (t1[t1.set == "chb24"].bootstrap == "seeds only (one patient)").all()
          and t1[t1.set == "development"].ci_lo.notna().all(), str(gg))
    env_real = {k_: v for k_, v in os.environ.items() if not k_.startswith("R2_TEST")}
    env_real["THESIS_REPO"] = str(ROOT)
    p = subprocess.run([sys.executable, "-c", "import sys; sys.path.insert(0, 'src'); import fa15_aggregate as A; "
                        "g = A.gate_a0('results/r2/r1_system/rp'); print(g['status'], g['rows'])"], cwd=str(ROOT),
                       env=env_real, capture_output=True, text=True)
    check("aggregate A0 on the REAL control record of this clone", p.stdout.startswith("PASS 240"), p.stdout + p.stderr[-300:])
    T1.run(repo / "src" / "fa15_aggregate.py", agg, ["--seeds-ctrl", "42,1,2,3,4,5,6", "--seeds-asr", "42,1,4,5", "--out",
                                                      root / "reading_neg"], expect_fail="STOP A2")
    gf = res_dir / "fa15_asr_b/gates.json"
    keep = gf.read_bytes()
    gl = json.loads(keep)
    gl[-1]["status"] = "FAIL"
    gf.write_text(json.dumps(gl))
    T1.run(repo / "src" / "fa15_aggregate.py", agg, args[:4] + ["--out", root / "reading_neg2"], expect_fail="STOP A1")
    gf.write_bytes(keep)
    check("aggregate negative paths: seed missing -> STOP A2; a run gate FAIL -> STOP A1", True)

    # notebook negative paths
    f = rp / "rp2/per_subject.csv"
    keep = f.read_bytes()
    d = pd.read_csv(f)
    i = d.index[d.seed == "clean_seed4"][3]
    d.loc[i, "tp"] += 1
    d.to_csv(f, index=False)
    T1.run(root / "runner.py", nb_env("neg_repro", dict(FA15_TEST_SEEDS="[5]")),
           [nbdir / "FA15_RUN_CTRL.ipynb"], expect_fail="G-repro FAIL")
    f.write_bytes(keep)
    zf = inp / f"datasets/u/fa15-asr-features-a/fa15-asr-chbmit-features-a/{parts['a'][0]}.npz"
    keep = zf.read_bytes()
    z = dict(np.load(zf, allow_pickle=True))
    z["is_ictal"] = z["is_ictal"].copy()
    z["is_ictal"][0] = ~z["is_ictal"][0]
    with open(zf, "wb") as fh:
        np.savez(fh, **z)
    T1.run(root / "runner.py", nb_env("neg_lab", dict(FA15_TEST_SEEDS="[42]")),
           [nbdir / "FA15_RUN_ASR_A.ipynb"], expect_fail="G-asr-data FAIL")
    zf.write_bytes(keep)
    T1.run(root / "runner.py", nb_env("neg_sha", dict(FA15_TEST_SEEDS="[5]", FA15_TEST_WORKER_SHA="deadbeefdeadbeef")),
           [nbdir / "FA15_RUN_CTRL.ipynb"], expect_fail="G-worker-sha FAIL")
    check("notebook negative paths: rp2 seed-4 row changed -> STOP G-repro; ASR label flipped -> STOP G-asr-data; worker "
          "sha differs -> STOP G-worker-sha (each archived)",
          (root / "work_neg_repro/fa15_ctrl_results.zip").exists() and (root / "work_neg_lab/fa15_asr_a_results.zip").exists())

    resume_tests(root, inp, nbdir, nb_env, runs)


def resume_tests(root, inp, nbdir, nb_env, runs):
    prev = inp / "datasets/u/fa15-run-asr-a-v1"
    shutil.copytree(root / "work_asr_a", prev)
    T1.run(root / "runner.py", nb_env("asr_a2", dict(FA15_TEST_SEEDS="[42, 1]")), [nbdir / "FA15_RUN_ASR_A.ipynb"])
    g2 = gates_of(root / "work_asr_a2/r2/r1_system/fa15_asr_a")
    same = all((root / "work_asr_a2/r2/r1_system/fa15_asr_a/run" / f).read_bytes() == (runs["asr_a"] / "run" / f).read_bytes()
               for f in ("per_subject.csv", "errors.csv", "q.csv"))
    check("resume: previous FA15_RUN_ASR_A output attached -> seeds imported, rows byte-identical",
          g2["R1.1-training"]["trained_now"] == [] and same, str(g2["R1.1-training"]["trained_now"]))
    shutil.rmtree(prev)
    prevc = inp / "datasets/u/fa15-run-ctrl-v1"
    shutil.copytree(root / "work_ctrl", prevc)
    T1.run(root / "runner.py", nb_env("asr_b2", dict(FA15_TEST_SEEDS="[5]")), [nbdir / "FA15_RUN_ASR_B.ipynb"])
    g3 = gates_of(root / "work_asr_b2/r2/r1_system/fa15_asr_b")
    check("a control output attached to FA15_RUN_ASR_B is NOT imported (seed 5 trained again)",
          g3["R1.1-training"]["trained_now"] == [5], str(g3["R1.1-training"]["trained_now"]))
    shutil.rmtree(prevc)


if __name__ == "__main__":
    main()
