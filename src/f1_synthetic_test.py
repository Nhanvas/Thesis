#!/usr/bin/env python
"""
f1_synthetic_test.py -- end-to-end test of the Track F1/F2 code on SYNTHETIC data (no EEG, nothing here is a result).

Builds, under a scratch directory:
  fake_repo/   a copy of src/ + the committed fold files (folds.json, fold_manifests.json, f1 partitions.json) whose
               "committed" fold-model checkpoints and reference results (results/v9_x3, v9_final/hard, model_cmp) are
               produced HERE on synthetic data by the CLOSED model-comparison code (model_cmp_core) -- so gates D0,
               G-const, GG0, G-vec and G-mlp test the new code against the closed code exactly as on Kaggle;
  input/       24 synthetic cases chbXX.npz with the fields of the real arrays (adj, bp5, f7, is_ictal, is_buffer,
               is_signal_loss, is_flag5sd, file_idx, files), split over two dataset folders like v9-x3-fold1/3.
Then runs the notebook steps (setup, gates, smoke, full, merge) for two random partitions with F1_EPOCHS=2, and the
aggregate (--allow-test). With --notebook it executes a generated Kaggle notebook (F1_SMOKE + F1_p1) instead.

  python src/f1_synthetic_test.py --work <scratch dir> [--notebook]
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np

REAL = Path(__file__).resolve().parents[1]
CASES = sorted([f"chb{i:02d}" for i in range(1, 25)])


def make_case(s, rng, n_files=2, n_win=900):
    n = n_files * n_win
    fidx = np.repeat(np.arange(n_files), n_win)
    ict = np.zeros(n, bool); buf = np.zeros(n, bool)
    n_sz = int(rng.integers(1, 4))
    for _ in range(n_sz):
        f = int(rng.integers(0, n_files)); a = f * n_win + int(rng.integers(100, n_win - 150)); d = int(rng.integers(6, 25))
        ict[a:a + d] = True; buf[a + d:a + d + 60] = True
    buf &= ~ict
    loss = np.zeros(n, bool); loss[rng.choice(n, 15, replace=False)] = True
    loss &= ~ict
    adj = rng.random((n, 18, 18)).astype(np.float32); adj = (adj + adj.transpose(0, 2, 1)) / 2
    for w in adj:
        np.fill_diagonal(w, 0); w[w < np.quantile(w, 0.8)] = 0
    bp5 = np.abs(rng.normal(1, 0.3, (n, 18, 5))).astype(np.float32)
    f7 = rng.normal(0, 1, (n, 18, 7)) + np.sin(np.arange(n) / 300.0)[:, None, None] * 0.3   # slow drift
    amp = 1 + 2.5 * ict
    f7[ict] *= amp[ict, None, None]; bp5[ict] *= 3
    adj[ict] = np.minimum(1, adj[ict] * 1.8)
    fl5 = np.zeros(n, bool); fl5[rng.choice(n, 20, replace=False)] = True; fl5 |= ict & (rng.random(n) < 0.5)
    files = np.array([f"{s}_{i+1:02d}.edf" for i in range(n_files)])
    return dict(adj=adj, bp5=bp5, f7=f7, is_ictal=ict, is_buffer=buf, is_signal_loss=loss, is_flag5sd=fl5,
                file_idx=fidx, files=files)


def build(work):
    fr = work / "fake_repo"; inp = work / "input"
    for d in (fr, inp):
        if d.exists():
            shutil.rmtree(d)
    shutil.copytree(REAL / "src", fr / "src")
    for rel in ("results/v9_x3/folds.json", "results/v9_x3/fold_manifests.json", "results/f1_repcv/partitions.json"):
        (fr / rel).parent.mkdir(parents=True, exist_ok=True); shutil.copy(REAL / rel, fr / rel)
    rng = np.random.default_rng(7)
    for i, s in enumerate(CASES):
        d = inp / ("v9-x3-fold1" if i % 2 else "v9-x3-fold3"); d.mkdir(parents=True, exist_ok=True)
        np.savez(d / f"{s}.npz", **make_case(s, rng))
    subprocess.run(["git", "init", "-q"], cwd=fr); subprocess.run(["git", "add", "-A"], cwd=fr)
    subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "fake"], cwd=fr)
    return fr, inp


def make_committed(fr, inp):
    """the 'committed' references, produced by the closed model-comparison code on the synthetic data."""
    code = f"""
import os, sys, json, numpy as np, pandas as pd, torch
os.environ['THESIS_REPO'] = r'{fr}'; os.environ['F1_EPOCHS'] = '2'
sys.path.insert(0, r'{fr / "src"}')
import f1_core as F
C = F.C
C.locate_all(r'{inp}')
x3 = C.X3
for f in C.FOLDS:
    man = C.MAN[str(f)]
    mu, sd = F.fold_constants(man['train_cases'])
    nt = {{s: int(C.clean_mask(C.npz(s)).sum()) for s in man['train_cases']}}
    meta = dict(fold=f, seed=42, in_dim=30, out_x=12, clip=4.0, add_mean=mu.tolist(), add_std=sd.tolist(), n_train=nt)
    model, info, _ = F.train('gae', man['train_cases'], meta, 42, torch.device('cpu'), epochs=2)
    d = x3 / 'models' / f'fold{{f}}'; d.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), d / f'gae_fold{{f}}_seed42.pt')
    (d / f'gae_fold{{f}}_seed42.json').write_text(json.dumps(meta))
C._GAE.clear()
C.MLP_EPOCHS = 2
per_all, cur_all, au_all, sz_all = [], [], [], []
for f in C.FOLDS:
    P, Cc, A, S, k = C.run_fold('gae', f, lambda ctx, f=f: C.gae_D(f, ctx), 'D')
    ref = pd.DataFrame([r for r in P if r['point'] == 'own'])
    ref.assign(seed=42)[['fold','seed','subject','stage','tp','fp','n_ref','nonict_h','short_tp','short_n','top','q_raw']] \
       .to_csv(x3 / f'fold{{f}}_seed42_per_subject.csv', index=False)
    (x3 / f'fold{{f}}_seed42_calibration.json').write_text(json.dumps(dict(fold=f, seed=42, k=k)))
    per_all += P; cur_all += Cc; au_all += A; sz_all += S
    model, info, rows = C.mlp_train(f, torch.device('cpu'))
    P, Cc, A, S, k = C.run_fold('mlp', f, lambda ctx, m=model, f=f: C.mlp_D(m, f, ctx, torch.device('cpu')), 'D')
    per_all += P; cur_all += Cc; au_all += A; sz_all += S
hard = C.REPO / 'results' / 'v9_final' / 'hard'; hard.mkdir(parents=True, exist_ok=True)
sz = pd.DataFrame(sz_all)
sz[sz.model == 'gae'].assign(set='x')[['subject','set','fold','file','onset_s','duration_s','caught']].to_csv(hard / 'gae_cv_seizures.csv', index=False)
mc = C.REPO / 'results' / 'model_cmp'; mc.mkdir(parents=True, exist_ok=True)
for name, rows in (('per_subject', per_all), ('curves', cur_all), ('auroc', au_all), ('seizures', sz_all)):
    pd.DataFrame(rows).to_csv(mc / f'{{name}}.csv', index=False)
print('committed references built')
"""
    subprocess.run([sys.executable, "-c", code], check=True)
    subprocess.run(["git", "add", "-A"], cwd=fr); subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t",
                                                                  "commit", "-qm", "refs"], cwd=fr)


def run_steps(fr, inp, out, partitions=(1, 2)):
    code = f"""
import os, sys, time
os.environ['THESIS_REPO'] = r'{fr}'; os.environ['F1_EPOCHS'] = '2'; os.environ['F1_OUT'] = r'{out}'
sys.path.insert(0, r'{fr / "src"}')
import f1_run as R
for p in {list(partitions)}:
    R.GATES.clear(); R.PROJ.clear()
    R.run_meta('synthetic', p)
    R.setup(p, r'{inp}')
    R.gates(p)
    R.smoke(p)
    R.import_previous(p, r'{inp}')
    R.full(p)
    assert R.merge(p) == 8, 'not all jobs done'
    R.summary(p)
"""
    subprocess.run([sys.executable, "-c", code], check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--work", required=True)
    ap.add_argument("--notebook", action="store_true")
    ap.add_argument("--reuse", action="store_true", help="reuse the fake repo and input of a previous run")
    a = ap.parse_args()
    work = Path(a.work); work.mkdir(parents=True, exist_ok=True)
    if a.reuse and (work / "fake_repo").exists():
        fr, inp = work / "fake_repo", work / "input"
        for f in ("f1_core.py", "f1_run.py", "f1_aggregate.py", "f1_make_notebooks.py"):
            if (REAL / "src" / f).exists():
                shutil.copy(REAL / "src" / f, fr / "src" / f)
    else:
        fr, inp = build(work)
        make_committed(fr, inp)
    out = work / "out"
    if out.exists():
        shutil.rmtree(out)
    if a.notebook:
        return fr, inp, out
    run_steps(fr, inp, out)
    subprocess.run([sys.executable, str(fr / "src" / "f1_aggregate.py"), str(out), "--out", str(work / "agg"),
                    "--allow-test"], check=True)
    print("SYNTHETIC TEST PASS")


if __name__ == "__main__":
    main()
