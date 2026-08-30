"""
build_te_adj.py — Phase C-final / C4-full, Stage 0 asset #1. CPU ONLY (numpy).

Precompute the SECOND relation (R2) for the multi-relational GAE: a directed
Transfer-Entropy adjacency, top-k20 sparsified, ALIGNED BY CONSTRUCTION to the
canonical windows — the exact analogue of the committed symmetric R1 adjacency
`data/processed/{subj}_{split}_adjs_topk20.npy`.

    R2 output: data/processed/{subj}_{split}_te_topk20.npy   [N,18,18] float32

WHY THIS FILE (not re-computing TE inside training)
  TE is a CPU numpy op (~8.7 ms/window). Precomputing it ONCE lets multi-seed GAE
  training stay GPU-only and fast (just loads arrays, exactly like R1). It is the
  ONE non-parallel gating step before train + multi-seed, so this script is
  resumable (per-subject cache; skip if output exists) and per-subject independent
  (chunk the 12 train subjects across Kaggle accounts if wall-time matters).

FIDELITY (reproduce-before-trust)
  Reuses the VALIDATED vectorized `te_matrix` from build_te_branch.py (max|Δ|~1e-15
  vs connectivity_probe.conn_matrix('te'), the C0 probe). --verify_fidelity re-asserts.

SPARSIFICATION (R2 = directed top-k20, mirrors R1's rationale)
  A dense 18x18 directed TE (306 off-diagonal edges) fed to a GCN degenerates toward
  global mean pooling (the exact failure graph_construction.py warns about for dense
  graphs). We keep the top 20% of the 306 DIRECTED off-diagonal edges (~61 edges),
  original TE values retained (not rescaled) — so both topology and magnitude carry
  signal, exactly as R1. Ties at the cutoff are kept (density may exceed 20% by 1-2).

INTEGRITY: default = the 12 TRAIN subjects + 3 VAL (for the encode check). TEST
  subjects refused unless --allow_test (one-shot, Stage 2 only). rlg untouched.

USAGE (Cursor CPU)
  python src/dataprep/build_te_adj.py --smoke
  python src/dataprep/build_te_adj.py --verify_fidelity
  python src/dataprep/build_te_adj.py --raw_dir data/processed --out_dir data/processed
  # VAL only (for the Stage-0 encode check):
  #   ... --subjects chb10,chb11,chb22
"""
import os as _os, sys as _sys
# build_te_adj.py lives in src/dataprep/; add sibling src dirs so flat imports resolve
_here = _os.path.dirname(_os.path.abspath(__file__))            # .../src/dataprep
_src = _os.path.dirname(_here)                                  # .../src
for _p in (_src, _here,
           _os.path.join(_src, "phaseC"),                       # build_te_branch, connectivity_probe
           _os.path.join(_src, "retrain"),
           _os.path.join(_src, "phaseB")):
    if _os.path.isdir(_p) and _p not in _sys.path:
        _sys.path.insert(0, _p)

import argparse
import time
from pathlib import Path

import numpy as np

# reuse the VALIDATED TE (do NOT re-implement — keeps C0 fidelity)
from build_te_branch import te_matrix          # noqa: E402
import graph_construction as GC                 # apply_car (optional)  # noqa: E402

TRAIN = ["chb01", "chb02", "chb04", "chb05", "chb07", "chb08",
         "chb09", "chb12", "chb19", "chb20", "chb21", "chb23"]
VAL = ["chb10", "chb11", "chb22"]
TEST = {"chb03", "chb06", "chb13", "chb14", "chb15", "chb16", "chb17", "chb18"}

KEEP_RATIO = 0.20    # directed top-k20 — mirrors R1 DEFAULT_KEEP_RATIO


# ----------------------------------------------------------------------------
def apply_topk_directed(A, keep_ratio=KEEP_RATIO):
    """Retain the top keep_ratio fraction of the n*(n-1) DIRECTED off-diagonal
    edges. Original values retained; diagonal zeroed; ties at cutoff kept.
    Degenerate (near-zero) windows -> keep whatever strictly-positive edges exist
    (never fabricate edges), which yields an empty/near-empty R2 graph that the
    GCN handles via its added self-loops (no NaN — asserted in --smoke)."""
    n = A.shape[0]
    A = np.array(A, dtype=np.float64, copy=True)
    np.fill_diagonal(A, 0.0)
    off_mask = ~np.eye(n, dtype=bool)
    n_edges = n * (n - 1)                       # 306 directed for n=18
    k = max(1, int(n_edges * keep_ratio))       # 61
    vals = np.sort(A[off_mask])                 # ascending, length 306
    cutoff = vals[-k]
    if cutoff <= 0.0:                           # fewer than k positive edges
        result = np.where(A > 0.0, A, 0.0)
    else:
        result = np.where(A >= cutoff, A, 0.0)
    np.fill_diagonal(result, 0.0)
    return result.astype(np.float32)


def te_adj_stack(windows, use_car=False, keep_ratio=KEEP_RATIO):
    """[N,18,1024] -> [N,18,18] directed-TE top-k20. Also returns mean ms/window."""
    N = len(windows)
    out = np.empty((N, 18, 18), dtype=np.float32)
    t0 = time.time()
    for n in range(N):
        W = np.asarray(windows[n], dtype=np.float64)
        if use_car:
            W = GC.apply_car(W)
        M = te_matrix(W)                        # validated directed TE, TE>=0
        out[n] = apply_topk_directed(M, keep_ratio)
    ms = 1000.0 * (time.time() - t0) / max(N, 1)
    return out, ms


# ----------------------------------------------------------------------------
def run_smoke():
    import connectivity_probe as CP
    rng = np.random.default_rng(0)
    # 1) fidelity: vectorized te_matrix == validated C0 conn_matrix('te')
    Wf = rng.standard_normal((18, 1024))
    dmax = float(np.abs(CP.conn_matrix(Wf, "te") - te_matrix(Wf)).max())
    assert dmax < 1e-9, f"TE fidelity broken: {dmax}"
    print(f"[SMOKE] TE fidelity vs C0 conn_matrix: max|Δ|={dmax:.1e}  PASS")

    # 2) TE >= 0 always (max(0,.) inside te_matrix)
    M = te_matrix(Wf)
    assert np.all(M >= 0.0), "TE has negative entries — invariant broken"
    print(f"[SMOKE] TE>=0 invariant PASS (min={M.min():.2e})")

    # 3) edge-cases Boti flagged: constant channel, all-quiet, NaN in raw
    Wc = rng.standard_normal((18, 1024)); Wc[3] = 7.0            # constant channel
    Wz = np.zeros((18, 1024))                                    # all-zero -> zero TE
    Wn = rng.standard_normal((18, 1024)); Wn[5, :10] = np.nan    # NaN in raw
    for name, W in [("const_chan", Wc), ("all_zero", Wz), ("nan_raw", np.nan_to_num(Wn))]:
        M = te_matrix(W)
        A = apply_topk_directed(M)
        assert np.isfinite(A).all(), f"{name}: non-finite in R2 adj"
        assert np.all(np.diag(A) == 0), f"{name}: diagonal not zeroed"
        print(f"[SMOKE] edge-case {name:10s}: finite, diag=0, nnz={int((A>0).sum()):3d}  PASS")

    # 4) density ~ top-k20 on a generic window
    A = apply_topk_directed(te_matrix(rng.standard_normal((18, 1024))))
    nnz = int((A > 0).sum())
    print(f"[SMOKE] directed top-k20 density: nnz={nnz} (target ~61 of 306)")
    assert 40 <= nnz <= 80, f"density off: {nnz}"

    # 5) stack + timing on a mini batch
    wi = rng.standard_normal((20, 18, 1024))
    stk, ms = te_adj_stack(wi)
    assert stk.shape == (20, 18, 18) and np.isfinite(stk).all()
    print(f"[SMOKE] stack {stk.shape} finite; ~{ms:.1f} ms/window on this box")
    print("[SMOKE] PASS")


def verify_fidelity():
    import connectivity_probe as CP
    rng = np.random.default_rng(3); md = 0.0
    for _ in range(8):
        W = rng.standard_normal((18, 1024))
        md = max(md, float(np.abs(CP.conn_matrix(W, "te") - te_matrix(W)).max()))
    print(f"max|Δ| te_matrix vs validated conn_matrix('te'): {md:.2e}")
    assert md < 1e-9, "TE fidelity broken — DO NOT build R2"
    print("[FIDELITY PASS] R2 TE is numerically identical to the C0 probe.")


# ----------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw_dir", default="data/processed",
                    help="dir with {subj}_{interictal,ictal}.npy [N,18,1024]")
    ap.add_argument("--out_dir", default="data/processed",
                    help="where to write {subj}_{split}_te_topk20.npy")
    ap.add_argument("--subjects", default=None,
                    help="comma list; default = 12 TRAIN + 3 VAL")
    ap.add_argument("--keep_ratio", type=float, default=KEEP_RATIO)
    ap.add_argument("--car", action="store_true",
                    help="apply CAR before TE (OFF by default; matches C0 probe)")
    ap.add_argument("--overwrite", action="store_true", help="recompute even if cached")
    ap.add_argument("--allow_test", action="store_true", help="required to touch TEST")
    ap.add_argument("--verify_fidelity", action="store_true")
    ap.add_argument("--smoke", action="store_true")
    a = ap.parse_args()

    if a.verify_fidelity:
        verify_fidelity(); return
    if a.smoke:
        run_smoke(); return

    subjs = a.subjects.split(",") if a.subjects else (TRAIN + VAL)
    leak = [s for s in subjs if s in TEST]
    if leak and not a.allow_test:
        raise SystemExit(f"INTEGRITY ABORT: TEST subject(s) {leak}. Pass --allow_test "
                         f"ONLY for the Stage-2 one-shot after VAL gate passes.")
    if leak:
        print(f"*** ONE-SHOT TEST: {leak} — the single allowed TEST exposure. ***")

    raw, out = Path(a.raw_dir), Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    print(f"keep_ratio={a.keep_ratio} car={a.car}  subjects={subjs}")
    print(f"{'subj':7s} {'split':10s} {'N':>7s} {'ms/win':>7s} {'nnz/win':>8s} {'status':>8s}")

    total_win = 0; t_start = time.time()
    for subj in subjs:
        for split, raw_tag in [("interictal", "interictal"), ("ictal", "ictal")]:
            fout = out / f"{subj}_{split}_te_topk20.npy"
            if fout.exists() and not a.overwrite:
                arr = np.load(fout, mmap_mode="r")
                print(f"{subj:7s} {split:10s} {len(arr):7d} {'--':>7s} {'--':>8s} {'cached':>8s}")
                total_win += len(arr)
                continue
            fin = raw / f"{subj}_{raw_tag}.npy"
            if not fin.exists():
                print(f"{subj:7s} {split:10s} {'--':>7s} {'--':>7s} {'--':>8s} {'MISSING':>8s}")
                continue
            win = np.load(fin, mmap_mode="r")
            stk, ms = te_adj_stack(win, use_car=a.car, keep_ratio=a.keep_ratio)
            np.save(fout, stk)
            nnz = float((stk > 0).sum(axis=(1, 2)).mean())
            print(f"{subj:7s} {split:10s} {len(stk):7d} {ms:7.1f} {nnz:8.1f} {'built':>8s}")
            total_win += len(stk)

    dt = time.time() - t_start
    print(f"\n[done] {total_win} windows, wall {dt/60:.1f} min. "
          f"R2 at {out}/{{subj}}_{{split}}_te_topk20.npy")


if __name__ == "__main__":
    main()
