#!/usr/bin/env python
"""r2_r3_synthetic_test.py -- end-to-end test of the stage R3 notebooks (R3_p1 ... R3_p5) and the R3 aggregate on
SYNTHETIC feature files (build container only; never on Kaggle, never on real data).

World (under --root): the R2 synthetic world (src/r2_r2_synthetic_test.build_world: 24 real case names, the real folds and
partitions.json, earlier .npz in v9-x3-fold1/3, thesis-r2-chbmit-features with the SAME arrays for the 22 gap-free cases
and one added seizure-free file for chb11 / chb21, a fake R0 diff report and a fake pinned data_sha256.csv) plus, made by
the closed code paths themselves (gen.py):
  - committed GAE fold models (random) + the v9_x3 per-subject rows they give (r2_r2's counterfactual path, earlier view);
  - the record's partition 0 (results/model_cmp per_subject / curves / auroc / seizures for the GAE and fake MLP-AE fold
    checkpoints, earlier view);
  - the F1 record results/f1_repcv/raw/p1..p5, trained and scored by f1_core.job itself (the record's own job function,
    2 epochs, earlier view), merged as f1_run.merge does, + the committed tables by src/f1_aggregate.py;
  - R2_A (results/r2/r2_cv/a: r2_r2.job "ae" on the new view, 2 epochs) and R2_B's counterfactual (r2_r2.job "cf").
Non-circular checks:
  N1  R3.0: the r2_r3 path, reloading the F1 checkpoints from disk, reproduces the rows f1_core.job wrote with the
      in-memory models EXACTLY (96 rows per model, own-point k, caught flags) in all five partitions;
  N2  a fold whose training cases are gap-free (partitions 1, 2, 5: fold 2 holds chb11 and chb21 out): new constants =
      the F1 record's (change 0), the rerun's trained weights = the F1 checkpoint BIT FOR BIT (same f1_core.train, same
      windows, same seed), its own-point k = the record's and its gap-free held-out rows identical; the counterfactual of
      that fold likewise;
  N3  the session guard: a job whose projected end passes the limit is not started (in the worker, at its start).
Runs: R3_p1 ... R3_p5 PASS (every gate; R3.0 exact; 8 trainings + 8 counterfactual jobs each); negative paths: one F1
record row fp + 3 -> STOP R3.0; an F1 checkpoint absent -> STOP (R3.0 job failed); one F1 checkpoint constant x (1 + 1e-7)
-> STOP G-const-p; a pinned data hash changed -> STOP G-data; each before any training job exists; R3_p1 resumed with its
output attached reuses all 24 jobs (merged rows byte-identical); the aggregate (src/r2_r3_aggregate.py): A0 on the REAL
record of this clone PASS (incl. the S18 §18.8 locks), on the synthetic record PASS; A1 PASS; the closed F1 / F2 reading
on the rerun and every table written; A1 STOPs when one partition's gates.json lacks R3.0-mlp or one training job is
missing.
  python src/r2_r3_synthetic_test.py [--root DIR]
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from r2_r1_synthetic_test import RUNNER, run              # noqa: E402  (shared synthetic helpers)
from r2_r2_synthetic_test import build_world as r2_world  # noqa: E402

GEN = r'''
# gen.py: committed models, the record (v9_x3, model_cmp partition 0, F1 raw p1..p5 by f1_core.job) and R2_A / R2_B cf
import json, os, shutil, sys
from pathlib import Path
import numpy as np, pandas as pd, torch
REPO = Path(os.environ["THESIS_REPO"])
sys.path.insert(0, str(REPO / "src"))
import r2_r2 as R2
F, C = R2.F, R2.C
R2.OUT_ROOT = REPO / "results" / "r2" / "r2_cv"
R2.STATE["tag"] = "gen"
R2.build_views()
R2.use_view("earlier")
X3, MC = REPO / "results" / "v9_x3", REPO / "results" / "model_cmp"
counts = {s: int(C.clean_mask(C.npz(s)).sum()) for s in C.ALL}
for f in C.FOLDS:
    tr = sorted(C.MAN[str(f)]["train_cases"])
    mu, sd = F.fold_constants(tr)
    d = X3 / "models" / f"fold{f}"; d.mkdir(parents=True, exist_ok=True)
    torch.manual_seed(f); torch.save(F.build("gae").state_dict(), d / f"gae_fold{f}_seed42.pt")
    (d / f"gae_fold{f}_seed42.json").write_text(json.dumps(dict(fold=f, seed=42, in_dim=30, out_x=12, clip=4.0,
        add_mean=mu.tolist(), add_std=sd.tolist(), n_train={s: counts[s] for s in tr}), indent=1))
(MC / "ckpt").mkdir(parents=True, exist_ok=True)
for f in C.FOLDS:
    torch.manual_seed(10 + f); torch.save(C.build_mlp_ae().state_dict(), MC / "ckpt" / f"mlp_fold{f}.pt")
def go(spec, tag="gen"):
    R2.STATE["tag"] = tag
    r = R2.job(spec)
    assert r["status"] == "done", r
    return {n: pd.read_csv(R2.out_dir() / spec["stage"] / spec["name"] / f"{n}.csv") for n in
            ("per_subject", "curves", "auroc", "seizures")}
rec = {n: [] for n in ("per_subject", "curves", "auroc", "seizures")}
for f in C.FOLDS:
    G = go(dict(stage="gen", name=f"gae_f{f}", kind="cf", model="gae", fold=f, view="earlier"))
    own = G["per_subject"][G["per_subject"].point == "own"].assign(seed=42)
    own[["fold", "seed", "subject", "stage", "tp", "fp", "n_ref", "nonict_h", "short_tp", "short_n", "top", "q_raw"]].to_csv(
        X3 / f"fold{f}_seed42_per_subject.csv", index=False)
    M = go(dict(stage="gen", name=f"mlp_f{f}", kind="cf", model="mlp", fold=f, view="earlier"))
    for n in rec:
        rec[n] += [G[n], M[n]]
for n, L in rec.items():
    pd.concat(L, ignore_index=True).to_csv(MC / f"{n}.csv", index=False)
# F1 record: f1_core.job itself (the record's job function), earlier view, 2 epochs (F1_EPOCHS)
raw = REPO / "results" / "f1_repcv" / "raw"
for p in (1, 2, 3, 4, 5):
    for model in F.MODELS:
        for f in C.FOLDS:
            F.job(p, model, f, torch.device("cpu"), raw)
    pd_ = raw / f"p{p}"
    for n in ("per_subject", "curves", "auroc", "seizures", "training_log"):
        pd.concat([pd.read_csv(d.parent / f"{n}.csv") for d in sorted((pd_ / "jobs").glob("*/DONE.json"))],
                  ignore_index=True).to_csv(pd_ / f"{n}.csv", index=False)
    (pd_ / "gates.json").write_text(json.dumps([dict(gate=g, status="PASS") for g in ("D0", "G-const", "G-vec", "G-mlp", "GG0")]))
    (pd_ / "run_meta.json").write_text(json.dumps(dict(notebook=f"F1_p{p}", partition=p, seed=p, epochs=F.EPOCHS,
        core_sha=F.sha16(F.__file__), partitions_sha=F.sha16(F.PARTITIONS), notebook_runtime_h=0.0, jobs_done=8)))
import subprocess
subprocess.check_call([sys.executable, str(REPO / "src" / "f1_aggregate.py"), str(raw), "--out", str(raw.parent),
                       "--allow-test"], stdout=subprocess.DEVNULL)
# R2_A (r2_r2.job "ae" on the new view) and R2_B's counterfactual (r2_r2.job "cf")
R2.STATE["tag"] = "a"
R2.run_meta("a", "R2_A", "synthetic")
R2.use_view("new")
metas = R2.new_metas()
mj = {str(f): m for f, m in metas.items()}
res = []
for m in F.MODELS:
    for f in C.FOLDS:
        R2.STATE["tag"] = "a"
        r = R2.job(dict(stage="jobs", name=f"{m}_f{f}", kind="ae", model=m, fold=f, view="new", metas=mj))
        assert r["status"] == "done", r
        res.append(r)
R2.STATE["tag"] = "a"
R2._jdump(R2.out_dir() / "jobs.json", res)
R2.finalise_model_cmp(None)
(R2.out_dir() / "gates.json").write_text(json.dumps([dict(gate=g, status="PASS") for g in ("G-data", "D0'", "G-const", "G-vec", "G-mlp")]))
for m in F.MODELS:
    for f in C.FOLDS:
        go(dict(stage="cfjobs", name=f"cf_{m}_f{f}", kind="cf", model=m, fold=f, view="new"), tag="b")
R2.STATE["tag"] = "b"
R2.merge("cfjobs", "cf")
shutil.rmtree(R2.OUT_ROOT / "gen", ignore_errors=True)
print("generated: v9_x3, model_cmp (partition 0), f1_repcv raw p1..p5 + tables, r2_cv/a, r2_cv/b/cf")
'''

CHECK = r'''
# check.py <work_root>: N1, N2 on the R3 outputs; N3 the session guard
import json, os, sys
from pathlib import Path
import numpy as np, pandas as pd, torch
REPO = Path(os.environ["THESIS_REPO"])
sys.path.insert(0, str(REPO / "src"))
WR = Path(sys.argv[1])
raw = REPO / "results" / "f1_repcv" / "raw"
GAPFREE = {1: 2, 2: 2, 5: 2}
for p in (1, 2, 3, 4, 5):
    out = WR / f"p{p}" / "r2" / "r3_repcv" / f"p{p}"
    s = json.loads((out / "r30" / "r30_summary.json").read_text())
    for m in ("gae", "mlp"):
        assert s[m]["exact_rows"] == s[m]["rows"] == 96 and s[m]["k_max_rel"] == 0.0 and s[m]["caught_differ"] == 0, (p, m, s[m])
    if p in GAPFREE:
        f = GAPFREE[p]
        man = json.loads((REPO / "results" / "f1_repcv" / "partitions.json").read_text())["partitions"][str(p)]["folds"][str(f)]
        assert {"chb11", "chb21"} <= set(man["held_out_cases"]), man
        fc = pd.read_csv(out / "fold_constants.csv")
        assert (fc[(fc.fold == f) & fc.key.isin(["add_mean", "add_std"])].max_rel_change == 0).all(), fc
        assert (fc[(fc.fold != f) & (fc.key == "add_mean")].max_rel_change > 0).all(), fc
        for m in ("gae", "mlp"):
            a = torch.load(out / "jobs" / f"{m}_fold{f}" / f"{m}_p{p}_fold{f}_seed{p}.pt")
            b = torch.load(raw / f"p{p}" / "jobs" / f"{m}_fold{f}" / f"{m}_p{p}_fold{f}_seed{p}.pt")
            assert all(torch.equal(a[k], b[k]) for k in a), (p, m, "weights differ")
            kn = json.loads((out / "jobs" / f"{m}_fold{f}" / "fit.json").read_text())["k"]
            kr = json.loads((raw / f"p{p}" / "jobs" / f"{m}_fold{f}" / "fit.json").read_text())["k"]
            kc = json.loads((out / "cfjobs" / f"cf_{m}_fold{f}" / "fit.json").read_text())["k"]
            assert kn == kr == kc, (p, m, kn, kr, kc)
            for sub in ("jobs", "cfjobs"):
                nm = f"{m}_fold{f}" if sub == "jobs" else f"cf_{m}_fold{f}"
                mine = pd.read_csv(out / sub / nm / "per_subject.csv")
                ref = pd.read_csv(raw / f"p{p}" / "jobs" / f"{m}_fold{f}" / "per_subject.csv")
                mg = mine.merge(ref, on=["subject", "point", "stage"], suffixes=("", "_r"))
                free = mg[~mg.subject.isin(["chb11", "chb21"])]
                assert len(free) == 4 * (len(man["held_out_cases"]) - 2) and (free.tp == free.tp_r).all() \
                    and (free.fp == free.fp_r).all(), (p, m, sub)
                gap = mg[mg.subject.isin(["chb11", "chb21"])]
                assert (gap.nonict_h > gap.nonict_h_r).all(), (p, m, sub)
print("N1: R3.0 = f1_core.job's rows exactly (96 rows per model, k, caught flags) in 5 partitions")
print("N2: gap-free fold 2 of partitions 1, 2, 5: constants unchanged, rerun weights = F1 checkpoint bit for bit, k equal, "
      "gap-free held-out rows identical (run and counterfactual); chb11 / chb21 more non-ictal hours")
os.environ["R2_T0"] = str(__import__("time").time() - 11.0 * 3600)       # 11 h already elapsed
os.environ["R2_WORK"] = str(WR / "guard")
import r2_r3 as R3
r = R3.job(dict(stage="jobs", name="gae_fold1", kind="train", model="gae", fold=1, partition=1, view="new", meta={},
                est_h=1.0))
assert r["status"].startswith("NOT RUN"), r
assert not (R3.OUT_ROOT / "p1" / "jobs" / "gae_fold1").exists()
print("N3: a job whose projected end passes the session limit is not started (worker check at start)")
'''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="/tmp/r2_r3_synth")
    a = ap.parse_args()
    t0 = time.time()
    root = Path(a.root)
    repo, inp = r2_world(root)
    for rel in ("results/r2/r2_cv/b",):
        (repo / rel).mkdir(parents=True, exist_ok=True)
    # A0 of the aggregate on the REAL record files of this clone (incl. the S18 §18.8 locks)
    p = subprocess.run([sys.executable, str(ROOT / "src" / "r2_r3_aggregate.py"), "--a0-only"], capture_output=True,
                       text=True, env={k: v for k, v in os.environ.items() if k not in ("R2_TEST", "THESIS_REPO")})
    assert p.returncode == 0 and "A0 PASS" in p.stdout, p.stdout + p.stderr
    print(f"A0 on the real record (f1_aggregate reproduces results/f1_repcv; S18 §18.8 locks): PASS ({time.time()-t0:.0f} s)")
    for name, body in (("gen.py", GEN), ("check.py", CHECK), ("runner.py", RUNNER)):
        (root / name).write_text(body)
    base = dict(R2_TEST="1", THESIS_REPO=str(repo), R2_INPUT=str(inp), OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1",
                MKL_NUM_THREADS="1", PYTHONHASHSEED="0", R2_TEST_EPOCHS="2", F1_EPOCHS="2")
    print(run(root / "gen.py", dict(base, R2_WORK=str(root / "gen_work"), R2_SCRATCH=str(root / "gen_scratch")))[-300:])
    print(f"world generated ({time.time()-t0:.0f} s)")
    nbdir = root / "notebooks"
    subprocess.check_call([sys.executable, str(ROOT / "src" / "r2_r3_make_notebooks.py"), "--runs", "0" * 40],
                          env=dict(os.environ, R2_NB_OUTDIR=str(nbdir)))

    def nb_env(tag):
        return dict(R2_TEST_REPO=str(repo), R2_TEST_INPUT=str(inp), R2_TEST_WORK=str(root / "work" / tag),
                    R2_TEST_SCRATCH=str(root / "scratch" / tag), R2_TEST="1", OMP_NUM_THREADS="1", PYTHONHASHSEED="0",
                    R2_TEST_EPOCHS="2")

    def out(tag, p):
        return root / "work" / tag / "r2" / "r3_repcv" / f"p{p}"

    import pandas as pd
    # --- negative paths first (each must STOP before any training job exists)
    def perturb_csv(rel, fn):
        pth = repo / rel
        keep = pth.read_bytes()
        d = pd.read_csv(pth); fn(d); d.to_csv(pth, index=False)
        return pth, keep
    pth, keep = perturb_csv("results/f1_repcv/raw/p1/per_subject.csv",
                            lambda d: d.__setitem__("fp", d.fp + 3 * (d.index == d[d.model == "mlp"].index[5])))
    run(root / "runner.py", nb_env("neg_r30"), [nbdir / "R3_p1.ipynb"], expect_fail="R3.0-mlp FAIL")
    pth.write_bytes(keep)
    assert not (out("neg_r30", 1) / "jobs").exists()
    ck = repo / "results" / "f1_repcv" / "raw" / "p2" / "jobs" / "gae_fold3" / "gae_p2_fold3_seed2.pt"
    ck.rename(ck.with_suffix(".away"))
    run(root / "runner.py", nb_env("neg_ckpt"), [nbdir / "R3_p2.ipynb"], expect_fail="R3.0-jobs FAIL")
    ck.with_suffix(".away").rename(ck)
    assert not (out("neg_ckpt", 2) / "jobs").exists()
    js = repo / "results" / "f1_repcv" / "raw" / "p3" / "jobs" / "mlp_fold1" / "mlp_p3_fold1_seed3.json"
    keep = js.read_bytes()
    m = json.loads(keep); m["add_mean"][2] *= 1 + 1e-7; js.write_text(json.dumps(m))
    run(root / "runner.py", nb_env("neg_const"), [nbdir / "R3_p3.ipynb"], expect_fail="G-const-p FAIL")
    js.write_bytes(keep)
    assert not (out("neg_const", 3) / "jobs").exists() and not (out("neg_const", 3) / "r30").exists()
    pin = repo / "results" / "r2" / "r1_system" / "smoke" / "data_sha256.csv"
    keep = pin.read_bytes()
    pv = pd.read_csv(pin); pv.loc[3, "sha256"] = "0" * 64; pv.to_csv(pin, index=False)
    run(root / "runner.py", nb_env("neg_pin"), [nbdir / "R3_p4.ipynb"], expect_fail="G-data FAIL")
    pin.write_bytes(keep)
    print(f"negative paths: R3.0 (F1 record fp + 3), F1 checkpoint absent, G-const-p (constant x (1 + 1e-7)), G-data "
          f"(pinned hash) -> STOP before any training ({time.time()-t0:.0f} s)")
    # --- the five notebooks
    for p in (1, 2, 3, 4, 5):
        s = run(root / "runner.py", nb_env(f"p{p}"), [nbdir / f"R3_p{p}.ipynb"])
        g = {x["gate"]: x for x in json.loads((out(f"p{p}", p) / "gates.json").read_text())}
        want = ["G-data", "D0'", "R3-projection", "G-const", "G-vec", "G-mlp", "G-const-p", "R3.0-gae", "R3.0-mlp"]
        assert list(g) == want and all(g[w]["status"] == "PASS" for w in want), {w: g.get(w, {}).get("status") for w in want}
        jobs = json.loads((out(f"p{p}", p) / "jobs.json").read_text())
        assert len(jobs) == 16 and all(j["status"] == "done" for j in jobs), jobs
        ps = pd.read_csv(out(f"p{p}", p) / "per_subject.csv")
        assert len(ps) == 2 * 24 * 4 and set(ps.partition) == {p}, len(ps)
        assert len(pd.read_csv(out(f"p{p}", p) / "cf" / "per_subject.csv")) == 2 * 24 * 4
        meta = json.loads((out(f"p{p}", p) / "run_meta.json").read_text())
        assert meta["partition"] == p and meta["seed"] == p and meta["jobs_done"] == 8 and meta["core_sha"] == meta["r2_r3_sha"]
        first_train = min((out(f"p{p}", p) / "jobs" / n / "DONE.json").stat().st_mtime for n in
                          [f"{x}_fold{f}" for x in ("gae", "mlp") for f in (1, 2, 3, 4)])
        last_gate = max((out(f"p{p}", p) / "r30" / n / "DONE.json").stat().st_mtime for n in
                        [f"{x}_fold{f}" for x in ("gae", "mlp") for f in (1, 2, 3, 4)])
        assert last_gate < first_train
        print(f"R3_p{p} PASS: 9 gates, 8 trainings + 8 counterfactual jobs, rows complete ({time.time()-t0:.0f} s)")
    print(run(root / "check.py", dict(THESIS_REPO=str(repo), R2_TEST="1", R2_INPUT=str(inp), PYTHONHASHSEED="0",
                                      R2_SCRATCH=str(root / "scratch" / "p1"), R2_TEST_EPOCHS="2"),
              [root / "work"])[-700:])
    # --- resume R3_p1 with its output attached
    prev = inp / "datasets" / "u" / "r3-p1-v1"
    shutil.copytree(root / "work" / "p1", prev)
    run(root / "runner.py", nb_env("p1b"), [nbdir / "R3_p1.ipynb"])
    jb = json.loads((out("p1b", 1) / "jobs.json").read_text())
    r3 = json.loads((out("p1b", 1) / "progress_r30.json").read_text())
    assert all(j["reused"] for j in jb) and len(jb) == 16 and all(r["status"] == "reused" for r in r3), (jb, r3)
    for f in ("per_subject.csv", "cf/per_subject.csv", "seizures.csv"):
        assert (out("p1b", 1) / f).read_bytes() == (out("p1", 1) / f).read_bytes(), f
    shutil.rmtree(prev)
    print("R3_p1 resumed: 24 jobs reused (8 gate, 8 training, 8 counterfactual), merged rows byte-identical")
    # --- the aggregate
    runs = root / "r3_repcv"
    for p in (1, 2, 3, 4, 5):
        shutil.copytree(out(f"p{p}", p), runs / f"p{p}")
    env = dict(R2_TEST="1", THESIS_REPO=str(repo), PYTHONHASHSEED="0")
    print(run(repo / "src" / "r2_r3_aggregate.py", env, ["--runs", runs, "--out", root / "agg"])[-1500:])
    ag = {x["gate"]: x for x in json.loads((root / "agg" / "gates.json").read_text())}
    assert ag["A0"]["status"] == "PASS" and ag["A1"]["status"] == "PASS", ag
    for f in ("record_vs_rerun.csv", "verdict.csv", "F2_across_record_vs_rerun.csv", "F1_across_record_vs_rerun.csv",
              "summary.csv", "bootstrap.csv", "dF1_by_system.csv", "per_subject.csv", "k.csv", "seizures.csv", "test8.csv",
              "r30.csv", "SUMMARY.md", "f1_reading/SUMMARY.md", "f1_reading/VERDICT.json", "f1_reading/F2_per_partition.csv"):
        assert (root / "agg" / f).exists(), f
    v = pd.read_csv(root / "agg" / "verdict.csv")
    assert len(v) == 2 and json.loads((root / "agg" / "f1_reading" / "VERDICT.json").read_text())["partitions"] == [0, 1, 2, 3, 4, 5]
    bt = pd.read_csv(root / "agg" / "bootstrap.csv")
    assert {"rerun - record", "data (cf - record)", "new models (rerun - cf)"} == set(bt.step)
    assert set(bt.partition.astype(str)) == {"0", "1", "2", "3", "4", "5", "all"}
    sz = pd.read_csv(root / "agg" / "seizures.csv")
    assert len(sz) == 12 and (sz.unmatched == 0).all(), sz
    print("aggregate: A0, A1 PASS; f1_aggregate (unchanged) read the rerun with partition 0 = R2_A; every table written")
    neg = root / "r3_neg"
    shutil.copytree(runs, neg)
    gj = [x for x in json.loads((neg / "p4" / "gates.json").read_text()) if x["gate"] != "R3.0-mlp"]
    (neg / "p4" / "gates.json").write_text(json.dumps(gj))
    run(repo / "src" / "r2_r3_aggregate.py", env, ["--runs", neg, "--out", root / "agg_neg"], expect_fail="STOP A1")
    shutil.rmtree(neg)
    shutil.copytree(runs, neg)
    shutil.rmtree(neg / "p2" / "jobs" / "mlp_fold3")
    run(repo / "src" / "r2_r3_aggregate.py", env, ["--runs", neg, "--out", root / "agg_neg2"], expect_fail="STOP A1")
    print("aggregate negative paths: a partition without R3.0-mlp, a missing training job -> STOP A1")
    print(f"ALL PASS ({time.time() - t0:.0f} s)")


if __name__ == "__main__":
    main()
