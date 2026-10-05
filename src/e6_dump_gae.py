#!/usr/bin/env python
"""
e6_dump_gae.py -- dump the locked GAE's per-window components (graph-mean latent Z [16],
raw reconstruction error, per-node reconstruction error [18] if the model exposes it, raw
gamma-AEC score) for exactly the files and windows of results/raw_eeg_view/cache, so the
E1-E5 protocol can be repeated on the real GAE outputs.

Signal path = the application's own (continuous_eval.filter_file: whole-file filtering;
input z-scoring with the committed per-subject stats.json, as the thesis does). Canonical
checkpoint, hash-checked by continuous_eval.get_model(). No label is read here.

  python src/e6_dump_gae.py --smoke     # 1 subject, 1 file: checks the pipeline end to end
  python src/e6_dump_gae.py             # the 15 non-test subjects of raw_eeg_view
TEST GUARD: refuses test subjects. Writes only results/e6_gae_dump/.
"""
import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT / "src", ROOT / "src" / "dataprep", ROOT / "src" / "phaseB",
          ROOT / "src" / "phaseC", ROOT / "src" / "retrain"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
import continuous_eval as CE  # noqa: E402
import szcore_eval as SE      # noqa: E402

SUBJS = ["chb01", "chb02", "chb04", "chb05", "chb07", "chb08", "chb09", "chb12",
         "chb19", "chb20", "chb21", "chb23", "chb10", "chb11", "chb22"]
assert not (set(SUBJS) & set(SE.TEST_SUBJS)), "TEST GUARD"
RAW = ROOT / "results" / "raw_eeg_view" / "cache"
OUT = ROOT / "results" / "e6_gae_dump"
OUT.mkdir(parents=True, exist_ok=True)


def components(zscored, model, gamma_b, gamma_a):
    """continuous_eval.compute_window_components + per-node reconstruction error."""
    n = zscored.shape[0]
    adj = np.empty((n, CE.N_CH, CE.N_CH), dtype=np.float32)
    bp = np.empty((n, CE.N_CH, 5), dtype=np.float32)
    for i in range(n):
        w = zscored[i]
        car = CE.GC.apply_car(w)
        A = CE.GC.combine_adjacency(CE.GC.compute_wpli(car), CE.GC.compute_aec(car),
                                    alpha=CE.GC.DEFAULT_ALPHA)
        adj[i] = CE.GC.apply_topk_threshold(A, keep_ratio=CE.GC.DEFAULT_KEEP_RATIO).astype(np.float32)
        bp[i] = CE.FE.compute_band_powers(w)
    pg, A_b, X_b, B = CE.G.build_batch(torch.tensor(adj), torch.tensor(bp), "cpu")
    with torch.no_grad():
        z = model.encoder(pg.x, pg.edge_index, pg.edge_attr)
        graph_z = z.view(B, CE.N_CH, CE.G.LATENT_DIM).mean(dim=1).numpy().astype(np.float64)
        zrecon = CE.G.joint_score(model, pg, A_b, X_b, B, per_node=False).cpu().numpy().astype(np.float64)
        try:
            pn = CE.G.joint_score(model, pg, A_b, X_b, B, per_node=True).cpu().numpy().astype(np.float64)
            pn = pn.reshape(B, CE.N_CH) if pn.size == B * CE.N_CH else None
        except Exception:
            pn = None
    zg = np.empty(n, dtype=np.float32)
    zf = zscored.astype(np.float32)
    for s in range(0, n, CE.GA.BATCH_SIZE):
        e = min(s + CE.GA.BATCH_SIZE, n)
        zg[s:e] = CE.GA.compute_gamma_scores_batch(zf[s:e], gamma_b, gamma_a)
    return graph_z, zrecon, pn, zg.astype(np.float64)


def dump(subj, max_files=None):
    if subj in SE.TEST_SUBJS:
        raise SystemExit(f"TEST GUARD: {subj}")
    t0 = time.time()
    rc = np.load(RAW / f"{subj}.npz", allow_pickle=True)
    files = [str(f) for f in rc["files"]]
    counts = np.bincount(rc["file_idx"].astype(int), minlength=len(files))
    stats = json.loads((CE.PROCESSED_DIR / f"{subj}_stats.json").read_text())
    mu = np.asarray(stats["ch_mean_uV"], dtype=np.float64) * 1e-6
    sd = np.asarray(stats["ch_std_uV"], dtype=np.float64) * 1e-6
    model = CE.get_model()
    gb, ga = CE.get_gamma_filter()
    GZ, ZR, PN, ZG = [], [], [], []
    for fi, fname in enumerate(files[:max_files] if max_files else files):
        filt, n = CE.filter_file(CE.edf_path(subj, fname))
        if n != counts[fi]:
            raise SystemExit(f"{subj}/{fname}: {n} windows here vs {counts[fi]} in raw_eeg_view cache")
        for s in range(0, n, CE.CHUNK_WINDOWS):
            e = min(s + CE.CHUNK_WINDOWS, n)
            gz, zr, pn, zg = components(CE.zscore(filt[s:e], mu, sd), model, gb, ga)
            GZ.append(gz); ZR.append(zr); ZG.append(zg)
            PN.append(pn if pn is not None else np.full((e - s, CE.N_CH), np.nan))
        del filt
        print(f"  {subj}/{fname}: {n} windows ({time.time()-t0:.0f}s)", flush=True)
    out = OUT / (f"{subj}_SMOKE.npz" if max_files else f"{subj}.npz")
    np.savez(out, graph_z=np.vstack(GZ), zrecon_raw=np.concatenate(ZR),
             pernode=np.vstack(PN), zgamma_raw=np.concatenate(ZG))
    pn_ok = not np.isnan(np.vstack(PN)).all()
    print(f"{subj}: saved {out.name}, {sum(len(z) for z in ZR)} windows, per-node "
          f"{'available' if pn_ok else 'NOT available'}, {time.time()-t0:.0f}s", flush=True)
    return time.time() - t0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    a = ap.parse_args()
    if a.smoke:
        dump("chb10", max_files=1)
        return
    T0 = time.time()
    for s in SUBJS:
        if (OUT / f"{s}.npz").exists():
            print(f"{s}: exists, skip"); continue
        dump(s)
    print(f"ALL DONE {time.time()-T0:.0f}s")


if __name__ == "__main__":
    main()
