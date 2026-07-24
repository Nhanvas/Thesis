"""
================================================================================
 topo_ensemble_eval.py  (Script B2)  —  does a topology view rescue chb06 under
                                        CPD, without hurting the other 7?
================================================================================
HYPOTHESIS (revised after B1)
    B1 showed graph-MAGNITUDE topology (graph_energy / spectral_radius) gives
    chb06 a clean, strong, INVERTED signal (detectability ~0.71, ictal-low) that
    the current 3-view ensemble lacks (chb06 ens AUROC 0.44). Because PELT/CPD
    detects mean shifts in BOTH directions, feeding this signed topology signal
    into the ensemble timeline should deepen chb06's onset shift (rescue) while
    reinforcing the other 7 (graph_energy is ictal-HIGH for them).

FALSIFICATION (pre-registered)
    ADD topology as a 4th view with weight w_topo. At the balanced operating
    point (pen=1.0, mag60), a SUCCESS requires BOTH:
      (1) chb06 event TP increases above the locked 2/10, AND
      (2) pooled sensitivity over the OTHER 7 subjects does NOT drop, and pooled
          FP/day does NOT rise materially (stay within the locked CI band).
    If chb06 improves only by degrading the 7 -> REJECT (document as future work).

METHOD (authoritative, no retrain)
    Reuses the EXACT locked scoring path from szcore_eval.py:
      build_timeline_masked -> V14.detect_changepoints -> cps_to_events ->
      score_szcore (timescoring).  We only swap the ensemble score fed in:
          ens4 = ens_locked + w_topo * robust_z(topology_feature)
    w_topo = 0 reproduces the locked numbers EXACTLY (built-in self-check).

USAGE  (Cursor / CPU)
    python topo_ensemble_eval.py \
        --scores_dir results/cpd/scores \
        --comp_dir   data/processed/components \
        --adj_root   data/processed \
        --summary_dir .                 # dir holding chbXX-summary.txt
    # options: --feature graph_energy|spectral_radius  --variant _adjs_topk20
    #          --wtopo 0,0.15,0.35,0.5  --pen 1.0  --min_mag_pct 60
Requires szcore_eval.py, evaluation_protocol.py, cpd_pipeline_v14.py, timescoring
in the same working dir / importable.
================================================================================
"""
import argparse
import glob
import os
import numpy as np

import szcore_eval as SE          # reuses the authoritative scoring path
import cpd_pipeline_v14 as V14

TEST_SUBJS = SE.TEST_SUBJS
WIN_SEC = SE.WIN_SEC
W_R, W_T, W_G = 0.35, 0.30, 0.35   # locked ensemble weights
FEAT_IDX = {"spectral_radius": 0, "graph_energy": 1, "fiedler": 2, "degree_entropy": 3}
# locked balanced (mag60/pen1.0) per-subject TP, from szcore_event_level_mag60.csv
LOCKED_TP_MAG60 = {"chb03": 7, "chb06": 2, "chb13": 10, "chb14": 8,
                   "chb15": 17, "chb16": 6, "chb17": 2, "chb18": 5}
N_SEIZ = {"chb03": 7, "chb06": 10, "chb13": 12, "chb14": 8,
          "chb15": 20, "chb16": 10, "chb17": 3, "chb18": 6}


def robust_z_pooled(x_in, x_ic):
    a = np.concatenate([x_in, x_ic])
    med = np.median(a)
    mad = np.median(np.abs(a - med)) + 1e-9
    return (x_in - med) / mad, (x_ic - med) / mad


def topo_feature_series(A, which):
    """A: (n_win, C, C) -> (n_win,) for the requested feature."""
    out = np.empty(len(A), dtype=np.float64)
    for i in range(len(A)):
        M = (A[i] + A[i].T) / 2.0
        np.fill_diagonal(M, 0.0)
        if which in ("spectral_radius", "graph_energy"):
            ev = np.linalg.eigvalsh(M)
            out[i] = np.max(np.abs(ev)) if which == "spectral_radius" else np.sum(np.abs(ev))
        elif which == "fiedler":
            deg = M.sum(1)
            ev = np.sort(np.linalg.eigvalsh(np.diag(deg) - M))
            out[i] = ev[1] if len(ev) > 1 else 0.0
        else:  # degree_entropy
            deg = M.sum(1); s = deg.sum()
            if s <= 1e-12:
                out[i] = 0.0
            else:
                p = deg / s; p = p[p > 0]
                out[i] = -np.sum(p * np.log(p)) / np.log(len(deg))
    return out


def _find_adj(adj_root, subj, split, variant):
    excl = ["interictal", "_inter"] if split == "ictal" else []
    toks = ["interictal", "inter"] if split == "inter" else ["ictal"]
    for p in sorted(glob.glob(os.path.join(adj_root, "**", "*.npy"), recursive=True)):
        b = os.path.basename(p).lower()
        if subj not in b or not b.endswith(variant.lower() + ".npy"):
            continue
        if any(t in b for t in excl):
            continue
        if any(t in b for t in toks):
            return p
    return None


def load_components(comp_dir, subj):
    def L(name, split):
        p = os.path.join(comp_dir, f"{name}_{subj}_{split}.npy")
        return np.load(p) if os.path.exists(p) else None
    return {k: (L(k, "inter"), L(k, "ictal"))
            for k in ("zrecon", "ztemp", "zgamma")}


def align_head(x, n):
    """Truncate (head) or pad-with-zeros to length n. Returns (x_aligned, note)."""
    if len(x) == n:
        return x, "exact"
    if len(x) > n:
        return x[:n], f"trunc {len(x)}->{n}"
    return np.concatenate([x, np.zeros(n - len(x))]), f"PAD {len(x)}->{n}"


def eval_ensemble(subj, ens_in, ens_ic, summary_dir, pen, min_mag_pct, seed=0):
    np.random.seed(seed)   # mirror szcore_eval.main(): seed before each timeline build
    signal, is_ictal, is_buffer, real_inter, sz_ranges, n_inter_h = \
        SE.build_timeline_masked(subj, ens_in, ens_ic, summary_dir)
    ref_iv = [(s * WIN_SEC, e * WIN_SEC) for (s, e) in sz_ranges]
    total_dur_s = len(signal) * WIN_SEC
    cps, _ = V14.detect_changepoints(signal, pen, min_mag_pct=min_mag_pct,
                                     local_win=15, inter_mask=real_inter)
    hyp_iv = SE.cps_to_events(cps, is_buffer, len(signal), sz_ranges=sz_ranges)
    sc = SE.score_szcore(ref_iv, hyp_iv, total_dur_s, n_inter_h)
    sc["n_seizures"] = len(sz_ranges)
    sc["n_inter_h"] = n_inter_h
    return sc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scores_dir", default="results/cpd/scores")
    ap.add_argument("--comp_dir", default="data/processed/components")
    ap.add_argument("--adj_root", default="data/processed")
    ap.add_argument("--summary_dir", default=".")
    ap.add_argument("--variant", default="_adjs_topk20")
    ap.add_argument("--feature", default="graph_energy", choices=list(FEAT_IDX))
    ap.add_argument("--wtopo", default="0,0.35",
                    help="comma list; start with 0,0.35 then expand e.g. 0,0.15,0.35,0.5")
    ap.add_argument("--pen", type=float, default=1.0)
    ap.add_argument("--min_mag_pct", type=float, default=60)
    ap.add_argument("--subjs", default=",".join(TEST_SUBJS))
    ap.add_argument("--seed", type=int, default=0,
                    help="canonical bootstrap seed; 0 matches the locked szcore_eval run")
    args = ap.parse_args()
    subjs = args.subjs.split(",")
    wtopos = [float(w) for w in args.wtopo.split(",")]

    print(f"\nFEATURE={args.feature}  VARIANT=*{args.variant}  "
          f"pen={args.pen}  mag={args.min_mag_pct}")
    print("=" * 78)

    # ---- per-subject: load ens, closure-check components, build z_topo ----
    ens, ztopo = {}, {}
    print("CLOSURE CHECK (rebuild 0.35 zr+0.30 zt+0.35 zg vs on-disk ens) + topo align")
    print(f"{'subj':<7}{'closure_max_err':>16}{'topo_inter_align':>20}{'topo_ictal_align':>18}")
    print("-" * 78)
    for s in subjs:
        ei = np.load(os.path.join(args.scores_dir, f"{s}_ens_inter.npy")).astype(np.float64)
        ec = np.load(os.path.join(args.scores_dir, f"{s}_ens_ictal.npy")).astype(np.float64)
        ens[s] = (ei, ec)
        comp = load_components(args.comp_dir, s)
        cerr = float("nan")
        if all(comp[k][0] is not None for k in comp):
            ni = min(len(ei), *(len(comp[k][0]) for k in comp))
            reb = (W_R * comp["zrecon"][0][:ni] + W_T * comp["ztemp"][0][:ni]
                   + W_G * comp["zgamma"][0][:ni])
            cerr = float(np.max(np.abs(reb - ei[:ni])))
        # topology feature series from adjacency
        ip = _find_adj(args.adj_root, s, "inter", args.variant)
        cp = _find_adj(args.adj_root, s, "ictal", args.variant)
        if not ip or not cp:
            print(f"{s:<7}{'[adj missing]':>16}")
            ztopo[s] = None
            continue
        fi = topo_feature_series(np.load(ip), args.feature)
        fc = topo_feature_series(np.load(cp), args.feature)
        zi, zc = robust_z_pooled(fi, fc)
        zi, na = align_head(zi, len(ei))
        zc, nb = align_head(zc, len(ec))
        ztopo[s] = (zi, zc)
        print(f"{s:<7}{cerr:>16.2e}{na:>20}{nb:>18}")

    # ---- sweep w_topo, evaluate, aggregate ----
    print("\nEVENT RESULTS by w_topo  (balanced point)")
    header = (f"{'w_topo':>7} | {'chb06 TP/sens':>15} | {'pooled-7 sens':>13} | "
              f"{'pooled-8 sens':>13} | {'pooled FP/day':>13}")
    print(header); print("-" * len(header))
    base_tp = {}
    for w in wtopos:
        per = {}
        for s in subjs:
            if ztopo[s] is None:
                continue
            ei, ec = ens[s]
            zi, zc = ztopo[s]
            e4i = ei + w * zi
            e4c = ec + w * zc
            per[s] = eval_ensemble(s, e4i, e4c, args.summary_dir,
                                   args.pen, args.min_mag_pct, seed=args.seed)
        # aggregate
        def pooled(sub_list):
            tp = sum(per[s]["tp"] for s in sub_list if s in per)
            nz = sum(per[s]["n_seizures"] for s in sub_list if s in per)
            return tp / nz if nz else float("nan")
        others = [s for s in subjs if s != "chb06" and s in per]
        all_s = [s for s in subjs if s in per]
        fp_tot = sum(per[s]["fp"] for s in all_s)
        h_tot = sum(per[s]["n_inter_h"] for s in all_s)
        fp_day = fp_tot / h_tot * 24 if h_tot else float("nan")
        c6 = per.get("chb06")
        c6str = f"{c6['tp']}/{c6['sensitivity']:.2f}" if c6 else "n/a"
        print(f"{w:>7} | {c6str:>15} | {pooled(others):>13.3f} | "
              f"{pooled(all_s):>13.3f} | {fp_day:>13.1f}")
        if w == 0.0:
            base_tp = {s: per[s]["tp"] for s in per}

    # ---- baseline fidelity self-check (w_topo=0 must reproduce locked mag60) ----
    if base_tp:
        print("\nBASELINE FIDELITY (w_topo=0 must reproduce locked mag60 per-subject TP)")
        ok = True
        for s in subjs:
            if s in base_tp:
                exp = LOCKED_TP_MAG60.get(s)
                got = base_tp[s]
                mark = "OK" if exp == got else "*** MISMATCH ***"
                if exp != got:
                    ok = False
                print(f"  {s:<7} locked_TP={exp}  got_TP={got}  {mark}")
        print("  => harness is FAITHFUL." if ok else
              "  => harness DEVIATES from locked numbers; do not trust w_topo>0 rows "
              "until resolved (likely summary_dir / alignment).")
    print("\nPaste this whole output back to me. I read the falsification directly "
          "from the chb06 TP vs pooled-7 sens / FP-day columns.\n")


if __name__ == "__main__":
    main()