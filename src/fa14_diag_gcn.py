#!/usr/bin/env python
"""
fa14_diag_gcn.py -- diagnosis of the G-gcn FAIL of FA14_P0 / FA14_REPL (15/11, D28-F; plan §12 15/11 01:20).

The gate compared torch_geometric's gcn_norm self weight with 1 / (1 + sum_j w_ij) (row sums of the window's adjacency)
on 256 windows of chb01 and found max |diff| 0.27; the synthetic test had passed (its graphs: symmetric, zero diagonal).
Candidate causes, told apart here on EVERY valid window of the 24 cases (the same earlier .npz, sha256-gated):
  C1 one-directional edges: A[i,j] > 0 with A[j,i] == 0. gcn_norm's degree is the TARGET-index (column) sum, so a row
     sum differs from it. Expected mechanism: np.corrcoef (AEC) is symmetric only up to rounding; apply_topk_threshold
     keeps A >= cutoff element-wise, so a pair at the cut can be kept in one direction only (the R0_DIAG17 note: "the
     top-k cut flips a few entries even on normal windows"). Signature: such edges sit at the window's smallest kept
     value (at the cut), and the column-sum formula equals gcn_norm.
  C2 nonzero diagonal: add_remaining_self_loops keeps an existing self loop (its own weight, not fill 1).
     Signature: diagonal entries != 0; neither formula equals gcn_norm, the diagonal-aware formula does.
  C3 both nonzero but unequal values A[i,j] != A[j,i] (float16 rounding of an asymmetric float64 value).
  C4 anything else: none of the three formulas equals gcn_norm.
Per case: windows, one-directional / unequal / diagonal entries and the windows holding them, the share of one-directional
edges at the cut, kept edges per window (union of both directions), and the self-weight error of three formulas
against gcn_norm computed on all windows. Nothing here changes data, models or any record; descriptive only.

  python src/fa14_diag_gcn.py          (env as fa14_mech: THESIS_REPO, R2_INPUT; output FA14_DIAG_OUT)
"""
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fa14_mech as M  # noqa: E402

OUT = Path(os.environ.get("FA14_DIAG_OUT", "/kaggle/working/fa14_diag"))
TOL = 1e-6


def case_rows(A):
    """A (n, 18, 18) float32 as the GAE sees it. Returns the per-case row (no gcn_norm)."""
    At = A.transpose(0, 2, 1)
    nz, nzt = A > 0, At > 0
    off = ~np.eye(M.N_CH, dtype=bool)[None]
    one_dir = nz & ~nzt & off
    unequal = nz & nzt & (A != At) & off
    diag = np.einsum("nii->ni", A) != 0
    big = np.where(nz & off, A, np.inf).min(axis=(1, 2))          # the window's smallest kept value
    at_cut = one_dir & (A == big[:, None, None])
    union = (nz | nzt) & off
    kept = union.sum(axis=(1, 2)) // 2
    return dict(windows=len(A), one_dir_entries=int(one_dir.sum()), one_dir_windows=int(one_dir.any((1, 2)).sum()),
                one_dir_at_cut=int(at_cut.sum()), unequal_entries=int(unequal.sum()),
                unequal_windows=int(unequal.any((1, 2)).sum()), diag_entries=int(diag.sum()),
                diag_windows=int(diag.any(1).sum()), kept_edges_min=int(kept.min()), kept_edges_median=float(np.median(kept)),
                kept_edges_max=int(kept.max()), empty_windows=int((kept == 0).sum()))


def self_weights(A, chunk=4096):
    """gcn_norm's self weight per node (add_self_loops=True, fill 1, symmetric norm; flow source_to_target) and three
    closed forms: row sums, column sums (target index), column sums with the diagonal kept as the self loop."""
    import torch
    from torch_geometric.nn.conv.gcn_conv import gcn_norm
    n = len(A)
    got = np.empty((n, M.N_CH))
    for s in range(0, n, chunk):
        T = torch.tensor(A[s:s + chunk]); B = T.shape[0]
        b, i, j = T.nonzero(as_tuple=True)
        ei = torch.stack([b * M.N_CH + i, b * M.N_CH + j])
        ei2, w2 = gcn_norm(ei, T[b, i, j], num_nodes=B * M.N_CH, add_self_loops=True)
        sl = ei2[0] == ei2[1]
        g = np.zeros(B * M.N_CH)
        g[ei2[0][sl].numpy()] = w2[sl].numpy()
        got[s:s + B] = g.reshape(B, M.N_CH)
    A64 = A.astype(np.float64)
    d = np.einsum("nii->ni", A64)
    row = 1.0 / (1.0 + A64.sum(2))
    col = 1.0 / (1.0 + A64.sum(1))
    dg = np.where(d != 0, d, 1.0)
    col_diag = dg / (dg + A64.sum(1) - d)
    return got, dict(row=row, col=col, col_diag=col_diag)


def main():
    t0 = time.time()
    OUT.mkdir(parents=True, exist_ok=True)
    M.build_view()                                      # G-data: the earlier .npz = R0's pinned sha256 (STOP if not)
    rows = []
    for c in M.C.ALL:
        t = time.time()
        ctx = M.C.make_ctx(c)
        A = M.valid_adj(ctx)
        r = dict(case=c, **case_rows(A))
        got, forms = self_weights(A)
        for k, v in forms.items():
            e = np.abs(got - v)
            r[f"err_{k}_max"] = float(e.max())
            r[f"err_{k}_nodes"] = int((e > TOL).sum())
        r["nodes"] = int(got.size)
        r["seconds"] = round(time.time() - t, 1)
        rows.append(r)
        M.C._CACHE.clear()
        print(c, {k: r[k] for k in ("windows", "one_dir_entries", "diag_entries", "err_row_max", "err_col_max",
                                    "err_col_diag_max")}, flush=True)
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "per_case.csv", index=False)
    tot = df.drop(columns=["case"]).sum(numeric_only=True)
    reading = []
    if tot.one_dir_entries == 0 and tot.unequal_entries == 0 and tot.diag_entries == 0:
        reading.append("C0: every graph symmetric with a zero diagonal" + ("; all forms = gcn_norm" if
                       (df.err_row_max <= TOL).all() else "; yet the row form differs -- see per_case.csv"))
    elif (df.err_col_max <= TOL).all() and tot.diag_entries == 0:
        reading.append("C1 (+C3 if unequal entries > 0): column sums (target index) = gcn_norm on every node of every case")
    elif (df.err_col_diag_max <= TOL).all() and tot.diag_entries > 0:
        reading.append("C2: the diagonal-aware column form = gcn_norm on every node; diagonal entries present")
    else:
        reading.append("C4: no closed form equals gcn_norm on every node -- see per_case.csv")
    S = dict(windows=int(tot.windows), nodes=int(tot.nodes), one_dir_entries=int(tot.one_dir_entries),
             one_dir_windows=int(tot.one_dir_windows), one_dir_at_cut=int(tot.one_dir_at_cut),
             unequal_entries=int(tot.unequal_entries), diag_entries=int(tot.diag_entries),
             err_row_max=float(df.err_row_max.max()), err_row_nodes=int(tot.err_row_nodes),
             err_col_max=float(df.err_col_max.max()), err_col_nodes=int(tot.err_col_nodes),
             err_col_diag_max=float(df.err_col_diag_max.max()), err_col_diag_nodes=int(tot.err_col_diag_nodes),
             reading=reading, runtime_h=round((time.time() - t0) / 3600, 3))
    (OUT / "summary.json").write_text(json.dumps(S, indent=1))
    L = ["# G-gcn diagnosis (fa14_diag_gcn.py)", "", "| quantity | value |", "|---|---|"]
    L += [f"| {k} | {v} |" for k, v in S.items()]
    (OUT / "SUMMARY.md").write_text("\n".join(L) + "\n")
    if (M.OUT / "gates.json").exists():
        (OUT / "gates.json").write_text((M.OUT / "gates.json").read_text())
    print("\n".join(L))


if __name__ == "__main__":
    main()
