#!/usr/bin/env python
"""r4_f5a_cv_synthetic_test.py -- tests of F5a Part B (run F5A_CV and its aggregate) on SYNTHETIC data (build container
only; never on Kaggle). Design results/r4_f5a/DESIGN_F5A.md §10.

World: src/r2_r2_synthetic_test.build_world (24 real case names, the real folds and partitions.json, earlier .npz in
v9-x3-fold1/3, thesis-r2-chbmit-features, a fake R0 diff and pinned hashes) plus, made by the record code paths (gen.py,
no r4_f5a_cv code): the committed fold GAE models of v9_x3 and their per-subject rows (D0' reads them), and the 48 CV
"checkpoints" (random GAE / MLP-AE, fold constants of the new view) with per_subject / seizures / fit.json written by
f1_core.run_fold itself, at the R2_A / R3 paths.
Checks:
  C1  the F5A_CV notebook (src/r4_f5a_cv_make_notebook.py, cell by cell in a fresh interpreter, 2 workers): every gate
      PASS (G-data, D0', SMOKE, G-k, G-rows, G-eng, G-seg, G-worker-sha); outputs written; 48 jobs
  C2  the aggregate: A0, A1, A3 PASS; every table written
Negative paths: one committed per_subject row tp + 1 (p0 GAE fold 1) -> STOP G-rows in the SMOKE; one committed k
x (1 + 1e-5) -> STOP G-k; an edited module -> the notebook refuses to start; a flat stored search window -> aggregate
STOP A3.
  python src/r4_f5a_cv_synthetic_test.py [--root DIR]
"""
import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import r2_r1_synthetic_test as W1        # noqa: E402  (notebook runner and run(): unchanged)
from r2_r2_synthetic_test import build_world  # noqa: E402

GEN = r'''
# gen.py: v9_x3 fold models + rows (earlier view, r2_r2's cf path) and the 48 CV checkpoints + rows (f1_core.run_fold)
import json, os, sys
from pathlib import Path
import numpy as np, pandas as pd, torch
REPO = Path(os.environ["THESIS_REPO"])
sys.path.insert(0, str(REPO / "src"))
if __name__ == "__main__":
    import r2_r2 as R2
    F, C = R2.F, R2.C
    R2.STATE["tag"] = "gen"
    R2.build_views()
    R2.use_view("earlier")
    X3 = REPO / "results" / "v9_x3"
    counts = {s: int(C.clean_mask(C.npz(s)).sum()) for s in C.ALL}
    for f in C.FOLDS:
        tr = sorted(C.MAN[str(f)]["train_cases"])
        mu, sd = F.fold_constants(tr)
        d = X3 / "models" / f"fold{f}"; d.mkdir(parents=True, exist_ok=True)
        torch.manual_seed(f); torch.save(F.build("gae").state_dict(), d / f"gae_fold{f}_seed42.pt")
        (d / f"gae_fold{f}_seed42.json").write_text(json.dumps(dict(fold=f, seed=42, in_dim=30, out_x=12, clip=4.0,
            add_mean=mu.tolist(), add_std=sd.tolist(), n_train={s: counts[s] for s in tr}), indent=1))
    for f in C.FOLDS:
        r = R2.job(dict(stage="gen", name=f"gae_f{f}", kind="cf", model="gae", fold=f, view="earlier"))
        assert r["status"] == "done", r
        g = pd.read_csv(R2.out_dir() / "gen" / f"gae_f{f}" / "per_subject.csv")
        own = g[g.point == "own"].assign(seed=42)
        own[["fold", "seed", "subject", "stage", "tp", "fp", "n_ref", "nonict_h", "short_tp", "short_n", "top", "q_raw"]].to_csv(
            X3 / f"fold{f}_seed42_per_subject.csv", index=False)
    R2.use_view("new")
    for p in range(6):
        man = F.manifest(p)
        for model in ("gae", "mlp"):
            for f in (1, 2, 3, 4):
                tr = sorted(man[f]["train_cases"])
                mu, sd = F.fold_constants(tr)
                meta = dict(partition=p, fold=f, seed=F.seed_of(p), in_dim=30, out_x=12, clip=4.0, add_mean=mu.tolist(),
                            add_std=sd.tolist(), train_cases=tr, held_out_cases=list(man[f]["held_out_cases"]))
                torch.manual_seed(100 * p + 10 * f + (model == "mlp"))
                mdl = F.build(model).eval()
                if p == 0:
                    jd = REPO / "results" / "r2" / "r2_cv" / "a" / "jobs" / f"{model}_f{f}"; stem = f"{model}_fold{f}_seed42"
                else:
                    jd = REPO / "results" / "r2" / "r3_repcv" / f"p{p}" / "jobs" / f"{model}_fold{f}"
                    stem = f"{model}_p{p}_fold{f}_seed{F.seed_of(p)}"
                jd.mkdir(parents=True, exist_ok=True)
                torch.save({k: v.cpu() for k, v in mdl.state_dict().items()}, jd / f"{stem}.pt")
                (jd / f"{stem}.json").write_text(json.dumps(meta, indent=1))
                per, cur, au, seiz, k, sec = F.run_fold(model, p, f, man[f], lambda ctx: F.encode_D(model, mdl, meta, ctx))
                pd.DataFrame(per).to_csv(jd / "per_subject.csv", index=False)
                pd.DataFrame(seiz).to_csv(jd / "seizures.csv", index=False)
                (jd / "fit.json").write_text(json.dumps(dict(model=model, partition=p, fold=f, k=k)))
    print("generated: v9_x3 fold models and rows; 48 CV checkpoints with their rows")
'''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="/tmp/f5acv_synth")
    a = ap.parse_args()
    t0 = time.time()
    root = Path(a.root)
    repo, inp = build_world(root)
    for name, body in (("gen.py", GEN), ("runner.py", W1.RUNNER)):
        (root / name).write_text(body)
    base = dict(R2_TEST="1", THESIS_REPO=str(repo), R2_INPUT=str(inp), OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1",
                MKL_NUM_THREADS="1", PYTHONHASHSEED="0")
    print(W1.run(root / "gen.py", dict(base, R2_WORK=str(root / "gen_work"), R2_SCRATCH=str(root / "gen_scratch")))[-300:])
    print(f"world generated ({time.time() - t0:.0f} s)")
    nbdir = root / "notebooks"
    subprocess.check_call([sys.executable, str(ROOT / "src" / "r4_f5a_cv_make_notebook.py")],
                          env=dict(os.environ, F5A_NB_OUTDIR=str(nbdir)))
    nb = nbdir / "F5A_CV.ipynb"

    def nb_env(tag):
        return dict(F5A_TEST_REPO=str(repo), F5A_TEST_INPUT=str(inp), F5A_TEST_WORK=str(root / f"work_{tag}"),
                    F5A_TEST_SCRATCH=str(root / f"scratch_{tag}"), F5A_WORKERS="2", PYTHONHASHSEED="0")

    # ---- negative paths first
    psub = repo / "results" / "r2" / "r2_cv" / "a" / "jobs" / "gae_f1" / "per_subject.csv"
    keep = psub.read_bytes()
    d = pd.read_csv(psub)
    i = d[(d.point == "own") & (d.stage == "localized")].index[0]
    d.loc[i, "tp"] += 1
    d.to_csv(psub, index=False)
    W1.run(root / "runner.py", nb_env("neg_rows"), [nb], expect_fail="G-rows[smoke] FAIL")
    psub.write_bytes(keep)
    print("NEG-ROWS PASS: a changed committed row stops the SMOKE (G-rows)")
    fj = repo / "results" / "r2" / "r2_cv" / "a" / "jobs" / "mlp_f1" / "fit.json"
    keep = fj.read_bytes()
    m = json.loads(keep); m["k"] *= 1 + 1e-5; fj.write_text(json.dumps(m))
    W1.run(root / "runner.py", nb_env("neg_k"), [nb], expect_fail="G-k[smoke] FAIL")
    fj.write_bytes(keep)
    print("NEG-K PASS: a changed committed k stops the SMOKE (G-k)")
    mod = repo / "src" / "f1_core.py"
    keepm = mod.read_text()
    mod.write_text(keepm + "\n# edited\n")
    W1.run(root / "runner.py", nb_env("neg_mod"), [nb], expect_fail="modules differ")
    mod.write_text(keepm)
    print("NEG-MOD PASS: an edited module stops the notebook before it starts")
    # ---- C1: the full notebook
    t = time.time()
    print(W1.run(root / "runner.py", nb_env("ok"), [nb])[-2000:])
    print(f"C1 notebook {time.time() - t:.0f} s")
    out = root / "work_ok" / "r4" / "f5a_cv"
    g = {x["gate"]: x for x in json.loads((out / "gates.json").read_text())}
    want = ["G-data", "D0'", "G-k[smoke]", "G-rows[smoke]", "G-eng[smoke]", "G-seg[smoke]", "G-worker-sha[smoke]", "SMOKE",
            "G-k[full]", "G-rows[full]", "G-eng[full]", "G-seg[full]", "G-worker-sha[full]"]
    assert all(g.get(w, {}).get("status") == "PASS" for w in want), {w: g.get(w, {}).get("status") for w in want}
    for f in ("events.csv", "rows.csv", "seizures.csv", "series.csv.gz", "mf_series.csv.gz", "jobs.csv", "projection.json",
              "SUMMARY.md", "smoke/events.csv"):
        assert (out / f).exists(), f
    J = pd.read_csv(out / "jobs.csv")
    assert len(J) == 48 and set(J.partition) == set(range(6)), len(J)
    print(f"C1 PASS: every gate; {len(J)} jobs, {len(pd.read_csv(out / 'events.csv'))} pairs")
    # ---- C2: aggregate
    env = dict(os.environ, THESIS_REPO=str(ROOT))
    p = subprocess.run([sys.executable, str(ROOT / "src" / "r4_f5a_cv_aggregate.py"), "--run", str(out), "--out",
                        str(root / "agg"), "--b", "200"], env=env, capture_output=True, text=True)
    print(p.stdout[-3500:], p.stderr[-2500:])
    assert p.returncode == 0 and "AGGREGATE DONE" in p.stdout, "aggregate failed"
    for f in ("gates.json", "V1_detection.csv", "V2_boundaries.csv", "V2_per_partition.csv", "D3_seizure_profiles.csv",
              "D3_mf_profiles.csv", "D4_D5_pairs.csv", "H_items.csv", "T_F5A_CV.md"):
        assert (root / "agg" / f).exists(), f
    print("C2 PASS: aggregate A0, A1, A3; every table written")
    # ---- NEG-A3
    sp = out / "series.csv.gz"
    keep = sp.read_bytes()
    S = pd.read_csv(sp, float_precision="round_trip")
    E = pd.read_csv(out / "events.csv")
    sz = pd.read_csv(out / "seizures.csv")
    ev = E[E.used_cpd].iloc[0]
    sid = sz[(sz.model == ev.model) & (sz.partition == ev.partition) & (sz.subject == ev.subject) & (sz.file == ev.file)
             & (sz.ref_on == ev.ref_on)].sz.iloc[0]
    sel = (S.model == ev.model) & (S.partition == ev.partition) & (S.sz == sid) & (S.w >= ev.win_a // 4) & (S.w < ev.win_b // 4)
    S.loc[sel, "x"] = 0.5
    S.to_csv(sp, index=False, compression="gzip")
    p = subprocess.run([sys.executable, str(ROOT / "src" / "r4_f5a_cv_aggregate.py"), "--run", str(out), "--out",
                        str(root / "agg_neg"), "--b", "20"], env=env, capture_output=True, text=True)
    assert p.returncode != 0 and "STOP A3" in (p.stdout + p.stderr), (p.stdout[-800:], p.stderr[-800:])
    sp.write_bytes(keep)
    print("NEG-A3 PASS: a flat stored search window stops the aggregate at A3")
    print(f"ALL PASS in {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
