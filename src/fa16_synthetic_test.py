#!/usr/bin/env python
"""fa16_synthetic_test.py -- full test of F-A1.6 (src/fa16_kmeans.py, src/fa16_aggregate.py, src/fa16_make_notebook.py) on
SYNTHETIC data (build container only; never on Kaggle, never on real data), plus two read-only checks on the real clone.

Part U -- the K-means rule on planted data: U1 three blobs + far outliers -> k = 3 chosen, the outliers have the largest
  distances (AUROC > 0.99); U2 a positive affine map of every feature with IQR > 0 -> same k, same distances (fold-1 f7
  constants are not a choice); U3 sparse features (IQR 0) counted, distances finite; U4 a constant channel -> STOP G-km;
  U5 deterministic; U6 the 5,000-window sample is used when n > 5,000 and every window otherwise; U7 a silhouette tie ->
  the smaller k; U8 the committed-row gate (compare_rows): identical PASS; tp + 1, k x (1 + 1e-5), a flipped seizure flag,
  a missing row -> FAIL; k x (1 + 1e-8) PASS.
Part R -- real clone (read only): A1 of the aggregate reproduces the committed curves_mean.csv and paired_bootstrap.csv;
  the builder accepts the current main as the pin (fa16_kmeans.py absent there) and, in a scratch clone, refuses a pin
  whose model_cmp_core.py or fa16_kmeans.py differs from the local file and accepts one that holds the same files.
Part E -- end to end on a synthetic world (24 cases, the real folds, random GAE / MLP-AE fold models, the record generated
  by the record's own code: results/v9_x3, results/v9_final/hard, results/model_cmp with the GAE, MLP-AE and Isolation
  Forest rows): E1 the run, every gate PASS, K-means rows for 24 cases, km_k 24 x 18; E2 the aggregate: A0 / A1 PASS,
  every table and the seven-curve figure; E3 STOP paths: a committed IF row tp + 1 -> G-IF (no K-means row written);
  a committed model_cmp GAE row fp + 1 -> GG-mc; a v9_x3 row tp + 1 -> GG; the aggregate refuses a stopped run (A0) and an
  altered committed curves_mean.csv (A1); E4 the notebook run cell by cell = the direct run byte for byte; an edited
  embedded cell -> sha assert.
  python src/fa16_synthetic_test.py [--root DIR] [--part U|R|E|all]
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def expect_stop(fn, text):
    try:
        fn()
    except SystemExit as e:
        assert text in str(e), (text, str(e))
        return str(e)
    raise AssertionError(f"expected a STOP containing {text!r}")


# ============================================================================ Part U
def part_u():
    import fa16_kmeans as M
    from sklearn.metrics import roc_auc_score
    rng = np.random.default_rng(1)
    t = time.time()
    centers = rng.normal(0, 8, (3, 30))
    X = np.concatenate([c + rng.normal(0, 1, (1000, 30)) for c in centers])
    y = np.r_[np.zeros(len(X)), np.ones(30)]
    scat = rng.normal(0, 15, (30, 30)) + rng.choice([-1, 1], (30, 30)) * 20
    Xo = np.concatenate([X, scat])
    D, Du, sm, inf = M.km_channel(Xo)
    au, auu = roc_auc_score(y, D), roc_auc_score(y, Du)
    assert au > 0.99 and auu > 0.99, (au, auu, inf)
    print(f"U1a three blobs + scattered far outliers: k = {inf['k']}, outlier AUROC km {au:.4f}, km_u {auu:.4f} -> PASS")
    comp = rng.normal(0, 1, (30, 30)) + 40
    Dc, Duc, smc, infc = M.km_channel(np.concatenate([X, comp]))
    auc_, aucu = roc_auc_score(y, Dc), roc_auc_score(y, Duc)
    assert infc["small_clusters"] >= 1 and smc[-30:].all() and auc_ < 0.6 and aucu > 0.99, (auc_, aucu, infc)
    print(f"U1b three blobs + a compact far group (the masking found 17/11): k = {infc['k']}, the group is a small "
          f"cluster; outlier AUROC km {auc_:.3f} (masked), km_u {aucu:.4f} -> PASS")
    a = rng.uniform(0.2, 5, 30); b = rng.normal(0, 10, 30)
    D2, Du2, _, inf2 = M.km_channel(Xo * a + b)
    assert inf2["k"] == inf["k"] and np.allclose(D2, D, rtol=1e-6, atol=1e-9) and np.allclose(Du2, Du, rtol=1e-6, atol=1e-9)
    print(f"U2 per-feature positive affine map -> same k, same distances (max diff {np.abs(D2 - D).max():.2e}) -> PASS")
    Xs = Xo.copy()
    Xs[:, :4] = np.where(rng.random((len(Xs), 4)) < 0.8, 0.0, rng.random((len(Xs), 4)))
    D3, Du3, _, inf3 = M.km_channel(Xs)
    assert inf3["iqr0_features"] == 4 and np.isfinite(D3).all() and np.isfinite(Du3).all(), inf3
    print("U3 four sparse features (80 % zeros): IQR-0 count 4, distances finite -> PASS")
    expect_stop(lambda: M.km_channel(np.ones((500, 30))), "STOP G-km")
    print("U4 constant channel -> STOP G-km -> PASS")
    D4, Du4, _, _ = M.km_channel(Xo)
    assert np.array_equal(D4, D) and np.array_equal(Du4, Du)
    print("U5 deterministic (bit-identical) -> PASS")
    big = np.concatenate([X, X + 0.01])
    *_, i6 = M.km_channel(big, n_sil=5000)
    *_, i6b = M.km_channel(X[:900])
    assert i6["n_sample"] == 5000 and i6["n_windows"] == 6000 and i6b["n_sample"] == 900, (i6, i6b)
    print("U6 sample of 5,000 when n = 6,000; every window when n = 900 -> PASS")
    import sklearn.metrics as SM
    keep = SM.silhouette_score
    SM.silhouette_score = lambda *a, **k: 0.5
    try:
        *_, i7 = M.km_channel(Xo)
    finally:
        SM.silhouette_score = keep
    assert i7["k"] == 2, i7
    print("U7 silhouette tie over every k -> k = 2 -> PASS")
    for size, want_large, rule in (([990, 10], [True, False], "alpha+beta"), ([500, 500], [True, True], "none"),
                                   ([10, 600, 90, 300], [False, True, True, True], "alpha+beta"),
                                   ([400, 350, 250], [True, True, True], "none"),
                                   ([700, 210, 90], [True, True, False], "alpha")):
        lg, r = M.large_clusters(size)
        assert list(lg) == want_large and r == rule, (size, list(lg), r)
    print("U9 large / small clusters (alpha 0.9, beta 5, PyOD's order of rules) on five hand examples -> PASS")
    with tempfile.TemporaryDirectory() as td:
        td = Path(td); a_, b_ = td / "a", td / "b"; a_.mkdir(); b_.mkdir()
        per = pd.DataFrame([dict(model="if", subject=f"s{i}", point=p, stage=st, k=4.1 if p == "own" else np.nan,
                                 tp=i, fp=10 + i) for i in range(5) for p in ("own", "fixed0.005")
                            for st in ("detector", "localized")])
        cur = pd.DataFrame([dict(model="if", subject=f"s{i}", top=t_, tp=i, fp=i + 3) for i in range(5) for t_ in (0.01, 0.005)])
        sz = pd.DataFrame([dict(model="if", subject=f"s{i}", file="f", onset_s=100 * i, caught=bool(i % 2)) for i in range(5)])
        au_ = pd.DataFrame([dict(model="if", subject=f"s{i}", auroc=0.8 + 0.01 * i) for i in range(5)])

        def write(d, per=per, cur=cur, sz=sz, au_=au_):
            for n, df in (("per_subject", per), ("curves", cur), ("seizures", sz), ("auroc", au_)):
                df.to_csv(d / f"{n}.csv", index=False)
        write(a_); write(b_)
        assert M.compare_rows("if", a_, b_)["status"] == "PASS"
        for name, mod in (("tp + 1", lambda p: p.assign(tp=p.tp + (p.index == 3))),
                          ("k x (1 + 1e-5)", lambda p: p.assign(k=p.k * (1 + 1e-5))),
                          ("missing row", lambda p: p.drop(index=2))):
            write(a_, per=mod(per.copy()))
            assert M.compare_rows("if", a_, b_)["status"] == "FAIL", name
        write(a_, per=per.assign(k=per.k * (1 + 1e-8)))
        assert M.compare_rows("if", a_, b_)["status"] == "PASS"
        write(a_, sz=sz.assign(caught=~sz.caught))
        assert M.compare_rows("if", a_, b_)["status"] == "FAIL"
    print("U8 compare_rows: identical PASS; tp + 1, k x (1 + 1e-5), missing row, flipped caught FAIL; k x (1 + 1e-8) PASS")
    print(f"PART U ALL PASS ({time.time() - t:.0f} s)")


# ============================================================================ Part R
def part_r():
    t = time.time()
    import fa16_aggregate as A
    A.a1(ROOT / "results" / "model_cmp")
    print("R1 A1 on the real committed files: curves_mean.csv and paired_bootstrap.csv reproduced -> PASS")
    head = subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"]).decode().strip()
    files = ("fa16_kmeans.py", "fa16_make_notebook.py")
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        env = dict(os.environ, FA16_NB_OUTDIR=str(td / "nb"))
        has = subprocess.run(["git", "-C", str(ROOT), "cat-file", "-e", f"{head}:src/fa16_kmeans.py"], stderr=subprocess.DEVNULL).returncode == 0
        p = subprocess.run([sys.executable, str(ROOT / "src" / "fa16_make_notebook.py"), "--run", head], env=env,
                           capture_output=True, text=True)
        assert p.returncode == 0, p.stderr
        # a scratch clone: one commit with another model_cmp_core.py, one with another fa16_kmeans.py
        cl = td / "clone"
        subprocess.check_call(["git", "clone", "-q", str(ROOT), str(cl)])
        g = ["git", "-C", str(cl), "-c", "user.email=t@t", "-c", "user.name=t"]
        for f in files:
            shutil.copyfile(ROOT / "src" / f, cl / "src" / f)
        core = (cl / "src" / "model_cmp_core.py").read_bytes()
        (cl / "src" / "model_cmp_core.py").write_bytes(core + b"# other\n")
        subprocess.check_call(g + ["commit", "-qam", "other core"])
        x = subprocess.check_output(g + ["rev-parse", "HEAD"]).decode().strip()
        (cl / "src" / "model_cmp_core.py").write_bytes(core)
        mk = [sys.executable, str(cl / "src" / "fa16_make_notebook.py"), "--run"]
        p = subprocess.run(mk + [x], env=env, capture_output=True, text=True)
        assert p.returncode != 0 and f"model_cmp_core.py at {x[:7]} differs" in p.stderr, p.stderr
        subprocess.check_call(g + ["commit", "-qam", "core back"])
        km = (cl / "src" / "fa16_kmeans.py").read_bytes()
        (cl / "src" / "fa16_kmeans.py").write_bytes(km + b"# other\n")
        subprocess.check_call(g + ["add", "src/fa16_kmeans.py"]); subprocess.check_call(g + ["commit", "-qm", "other km"])
        y = subprocess.check_output(g + ["rev-parse", "HEAD"]).decode().strip()
        (cl / "src" / "fa16_kmeans.py").write_bytes(km)
        p = subprocess.run(mk + [y], env=env, capture_output=True, text=True)
        assert p.returncode != 0 and f"fa16_kmeans.py at {y[:7]} differs" in p.stderr, p.stderr
        subprocess.check_call(g + ["commit", "-qam", "km back"])
        z = subprocess.check_output(g + ["rev-parse", "HEAD"]).decode().strip()
        p = subprocess.run(mk + [z], env=env, capture_output=True, text=True)
        assert p.returncode == 0, p.stderr
    print(f"R2 builder (notebook pin rule): pin {head[:7]} accepted (fa16_kmeans.py {'equal' if has else 'absent'} there); "
          f"a pin with another model_cmp_core.py refused; a pin with another fa16_kmeans.py refused; a pin holding the "
          f"same files accepted -> PASS")
    print(f"PART R ALL PASS ({time.time() - t:.0f} s)")


# ============================================================================ Part E
COMMIT_IF = r"""
import os, sys, pandas as pd
sys.path.insert(0, os.environ['THESIS_REPO'] + '/src')
import model_cmp_core as C
C.locate_all(os.environ['FA16_INPUT'])
cache = {}
def sc(ctx):
    if ctx['s'] not in cache:
        cache[ctx['s']] = C.if_D(ctx)
    return cache[ctx['s']]
mc = C.REPO / 'results' / 'model_cmp'
add = {k: [] for k in ('per_subject', 'curves', 'auroc', 'seizures')}
for f in C.FOLDS:
    P, Cc, A, S, k = C.run_fold('if', f, sc, 'D')
    add['per_subject'] += P; add['curves'] += Cc; add['auroc'] += A; add['seizures'] += S
for n, rows in add.items():
    pd.concat([pd.read_csv(mc / f'{n}.csv'), pd.DataFrame(rows)], ignore_index=True).to_csv(mc / f'{n}.csv', index=False)
sys.path.insert(0, os.environ['FA16_REAL'] + '/src')
import model_cmp_aggregate as MA
per = MA.per_case(pd.read_csv(mc / 'per_subject.csv')); own = per[(per.point == 'own') & (per.stage == 'localized')]
cur = pd.read_csv(mc / 'curves.csv')
pd.concat([MA.curve_at(cur, m, 0.0)[1].assign(model=m) for m in ('gae', 'mlp', 'if')]).to_csv(mc / 'curves_mean.csv', index=False)
pd.DataFrame([MA.boot_diff(own, m, metric=mt) for m in ('mlp', 'if') for mt in ('f1', 'sens')]).to_csv(mc / 'paired_bootstrap.csv', index=False)
print('committed IF rows, curves_mean, paired_bootstrap built')
"""

RUN = r"""
import os, sys
sys.path[:0] = [os.environ['FA16_REAL'] + '/src', os.environ['THESIS_REPO'] + '/src']
import fa16_kmeans as M
M.main('synthetic', 'local', os.environ['FA16_INPUT'])
"""


def run(args, env, expect_fail=None):
    p = subprocess.run([sys.executable, *map(str, args)], env=dict(os.environ, **env), capture_output=True, text=True)
    tail = p.stdout[-3000:] + "\n" + p.stderr[-4000:]
    if expect_fail is None:
        if p.returncode != 0:
            print(tail)
            raise SystemExit(f"FAILED: {args}")
        return p.stdout
    if p.returncode == 0 or expect_fail not in tail:
        print(tail)
        raise SystemExit(f"expected a STOP containing {expect_fail!r}: {args}")
    return tail


def part_e(root):
    import f1_synthetic_test as F1S
    t = time.time()
    root.mkdir(parents=True, exist_ok=True)
    repo, inp = F1S.build(root)
    F1S.make_committed(repo, inp)
    for rel in ("results/v9_x3/folds.json", "results/v9_x3/fold_manifests.json"):
        assert (repo / rel).exists()
    base = dict(THESIS_REPO=str(repo), FA16_INPUT=str(inp), FA16_REAL=str(ROOT), OMP_NUM_THREADS="2",
                OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1", PYTHONHASHSEED="0")
    (root / "commit_if.py").write_text(COMMIT_IF)
    (root / "run_fa16.py").write_text(RUN)
    print(run([root / "commit_if.py"], base).strip().splitlines()[-1], f"({time.time() - t:.0f} s)")

    def env(tag):
        return dict(base, FA16_OUT=str(root / f"w_{tag}" / "fa16"))

    def gates(tag):
        return {g["gate"]: g for g in json.loads((root / f"w_{tag}" / "fa16" / "gates.json").read_text())}

    t1 = time.time()
    run([root / "run_fa16.py"], env("main"))
    G = gates("main")
    for k in ("D0", "G-mini", "GG", "GG-mc", "G-IF", "G-km"):
        assert G[k]["status"] == "PASS", (k, G[k])
    out = root / "w_main" / "fa16"
    per = pd.read_csv(out / "per_subject.csv")
    assert set(per.model) == {"gae", "if", "km", "km_u"} and all(per[per.model == m].subject.nunique() == 24 for m in ("km", "km_u"))
    kk = pd.read_csv(out / "km_k.csv")
    assert len(kk) == 24 * 18 and kk.subject.nunique() == 24 and kk.k.between(2, 10).all()
    jobs = json.loads((out / "jobs.json").read_text())
    assert len(jobs) == 16 and all(j["status"] == "done" for j in jobs)
    print(f"E1 run: every gate PASS (D0, G-mini, GG, GG-mc, G-IF, G-km), km and km_u rows for 24 cases, km_k 432 rows, "
          f"k chosen {kk.k.value_counts().sort_index().to_dict()} ({time.time() - t1:.0f} s)")
    agg = run([ROOT / "src" / "fa16_aggregate.py", root / "w_main", "--ref", repo / "results" / "model_cmp",
               "--out", root / "agg"], base)
    assert "A0 / A1 PASS" in agg
    for n in ("table7", "km_per_case", "paired_bootstrap_km", "matched_rate_km", "curves_mean7", "km_k_summary",
              "km_small_diag"):
        assert len(pd.read_csv(root / "agg" / f"{n}.csv")), n
    t7 = pd.read_csv(root / "agg" / "table7.csv")
    assert set(t7.model) >= {"gae", "mlp", "if", "km", "km_u"}
    pb = pd.read_csv(root / "agg" / "paired_bootstrap_km.csv")
    assert list(pb.metric) == ["sens", "f1", "fp_day"] * 3 and (pb.n_units == 23).all()
    assert list(pb.model) == ["km"] * 3 + ["km_u"] * 6 and list(pb.reference) == ["gae"] * 6 + ["km"] * 3
    assert (root / "agg" / "figures" / "fig_model_cmp_curves7.png").stat().st_size > 10000
    print("E2 aggregate: A0 / A1 PASS; table (7 models + km_u), K-means per case, bootstrap km - GAE, km_u - GAE, "
          "km_u - km (sens, F1, FP/day; 23 units), matched rate, seven-model curves, k summary, small-cluster diagnostic, "
          "figure -> PASS")
    mc = repo / "results" / "model_cmp"
    keep = {n: (mc / f"{n}.csv").read_bytes() for n in ("per_subject", "curves_mean")}
    d = pd.read_csv(mc / "per_subject.csv")
    i = d.index[(d.model == "if") & (d.point == "own") & (d.stage == "localized")][5]
    d.loc[i, "tp"] += 1; d.to_csv(mc / "per_subject.csv", index=False)
    run([root / "run_fa16.py"], env("stopif"), expect_fail="STOP G-IF")
    p2 = pd.read_csv(root / "w_stopif" / "fa16" / "per_subject.csv")
    assert not ({"km", "km_u"} & set(p2.model)) and gates("stopif")["G-IF"]["status"] == "FAIL"
    run([ROOT / "src" / "fa16_aggregate.py", root / "w_stopif", "--ref", mc, "--out", root / "agg_x"], base,
        expect_fail="STOP A0")
    (mc / "per_subject.csv").write_bytes(keep["per_subject"])
    d = pd.read_csv(mc / "per_subject.csv")
    i = d.index[(d.model == "gae") & (d.point == "fixed0.005") & (d.stage == "detector")][7]
    d.loc[i, "fp"] += 1; d.to_csv(mc / "per_subject.csv", index=False)
    run([root / "run_fa16.py"], env("stopgg"), expect_fail="STOP GG-mc")
    (mc / "per_subject.csv").write_bytes(keep["per_subject"])
    x3 = repo / "results" / "v9_x3" / "fold2_seed42_per_subject.csv"
    keep_x3 = x3.read_bytes()
    d = pd.read_csv(x3); d.loc[d.index[0], "tp"] += 1; d.to_csv(x3, index=False)
    run([root / "run_fa16.py"], env("stopx3"), expect_fail="STOP gate GG")
    x3.write_bytes(keep_x3)
    c = pd.read_csv(mc / "curves_mean.csv"); c.loc[3, "sens"] += 0.01; c.to_csv(mc / "curves_mean.csv", index=False)
    run([ROOT / "src" / "fa16_aggregate.py", root / "w_main", "--ref", mc, "--out", root / "agg_y"], base,
        expect_fail="STOP A1")
    (mc / "curves_mean.csv").write_bytes(keep["curves_mean"])
    print("E3 STOP paths: committed IF row tp + 1 -> G-IF (no K-means row); committed GAE row fp + 1 -> GG-mc; v9_x3 row "
          "tp + 1 -> GG; the aggregate refuses the stopped run (A0) and an altered curves_mean.csv (A1) -> PASS")
    from r2_r1_synthetic_test import RUNNER
    (root / "runner.py").write_text(RUNNER)
    nbdir = root / "nb"
    subprocess.check_call([sys.executable, str(ROOT / "src" / "fa16_make_notebook.py"), "--run", "0" * 40],
                          env=dict(os.environ, FA16_NB_OUTDIR=str(nbdir)), stdout=subprocess.DEVNULL)
    nbenv = dict(base, FA16_TEST_REPO=str(repo), FA16_TEST_INPUT=str(inp), FA16_TEST_WORK=str(root / "w_nb"))
    nbenv.pop("FA16_OUT", None)
    t3 = time.time()
    run([root / "runner.py", nbdir / "FA16_KMEANS.ipynb"], nbenv)
    for n in ("per_subject", "curves", "auroc", "seizures", "km_k"):
        a_ = pd.read_csv(out / f"{n}.csv"); b_ = pd.read_csv(root / "w_nb" / "fa16" / f"{n}.csv")
        if n == "km_k":
            a_, b_ = a_.drop(columns="seconds"), b_.drop(columns="seconds")
        pd.testing.assert_frame_equal(a_, b_, check_exact=True)
    nb = json.loads((nbdir / "FA16_KMEANS.ipynb").read_text())
    ci = next(i for i, c in enumerate(nb["cells"]) if "".join(c["source"]).startswith("%%writefile"))
    nb["cells"][ci]["source"].append("# edited\n")
    (nbdir / "edited.ipynb").write_text(json.dumps(nb))
    shutil.rmtree(root / "w_nb")
    run([root / "runner.py", nbdir / "edited.ipynb"], nbenv, expect_fail="cell edited or wrong commit")
    print(f"E4 notebook cell by cell: every table equal to the direct run (km_k without its timing column); an edited "
          f"embedded cell -> sha assert -> PASS ({time.time() - t3:.0f} s)")
    print(f"PART E ALL PASS ({time.time() - t:.0f} s)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=None)
    ap.add_argument("--part", default="all", choices=["U", "R", "E", "all"])
    a = ap.parse_args()
    if a.part in ("U", "all"):
        part_u()
    if a.part in ("R", "all"):
        part_r()
    if a.part in ("E", "all"):
        root = Path(a.root) if a.root else Path(tempfile.mkdtemp(prefix="fa16_test_"))
        part_e(root)
    print("ALL PASS" if a.part == "all" else f"PART {a.part} PASS")


if __name__ == "__main__":
    main()
