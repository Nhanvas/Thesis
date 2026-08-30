#!/usr/bin/env python3
"""
Minimum-event-duration post-filter (Phase-B), per PREREG_09.

Imports the repo's szcore_eval (SE) + cpd_pipeline_v14 (V14) + ruptures (rpt).
Derives D* on VAL (largest sensitivity-neutral duration) at mag80/pen5, applies once to test.
Label-free; core CPD untouched (post-filter on hyp events only).

Run:
  python duration_filter_sweep.py \
      --ens_dir results/retrain_v3p1/ens \
      --val_ens_dir results/retrain_v3p1/val_ens \
      --summary_dir "F:/Study/Thesis/Dataset/CHB-MIT/CHB info/summary" --seed 42
  python duration_filter_sweep.py --smoke     # logic-only self-test, no repo modules
"""
import argparse, sys
import numpy as np

TEST_SUBJS = ["chb03", "chb06", "chb13", "chb14", "chb15", "chb16", "chb17", "chb18"]
VAL_SUBJS  = ["chb10", "chb11", "chb22"]
D_GRID = [0, 4, 8, 12, 16, 20, 30]
OP = dict(mag=80.0, pen=5.0)          # balanced headline
TRIAGE = dict(mag=55.0, pen=0.3)      # triage point


def min_dur_filter(hyp_iv, D):
    """PREREG_09 s1: drop events shorter than D seconds."""
    return [(a, b) for (a, b) in hyp_iv if (b - a) >= D]


# ---------- logic-only smoke test (no repo modules) ----------
def smoke():
    hyp = [(0, 4), (100, 104), (200, 260), (300, 304), (400, 420)]  # 3 short, 2 long
    for D in [0, 4, 8, 20]:
        kept = min_dur_filter(hyp, D)
        print(f"  D={D:2d}s -> kept {len(kept)}/{len(hyp)}: {kept}")
    # sensitivity-neutral selection logic
    # fake: VAL TP count per D (D=0..30). pick largest D with TP unchanged.
    val_tp = {0: 12, 4: 12, 8: 12, 12: 11, 16: 10, 20: 9, 30: 7}
    base = val_tp[0]
    dstar = max([d for d in D_GRID if val_tp[d] == base])
    print(f"  VAL TP by D={val_tp}; D*={dstar} (largest sensitivity-neutral)")
    assert dstar == 8
    print("  [SMOKE] duration filter + D* selection OK")


def _mag_filter(V14, smoothed, cps_pen, mag_pct, local_win, real_inter):
    mags_d = {c: V14._cp_magnitude(smoothed, c, local_win) for c in cps_pen}
    if real_inter is not None and np.any(real_inter):
        bg = [m for c, m in mags_d.items() if real_inter[c]]
    else:
        bg = list(mags_d.values())
    thr = float(np.percentile(bg, mag_pct)) if bg else 0.0
    return [c for c in cps_pen if mags_d[c] >= thr]


def hyp_at(SE, V14, rpt, subj, ei, ec, summary_dir, mag, pen, local_win=15):
    """Return (hyp_iv, ref_iv, total_dur_s, n_inter_h) at one operating point."""
    signal, is_ictal, is_buffer, real_inter, sz_ranges, n_inter_h = \
        SE.build_timeline_masked(subj, ei, ec, summary_dir)
    ref_iv = [(s*SE.WIN_SEC, e*SE.WIN_SEC) for (s, e) in sz_ranges]
    total_dur_s = len(signal) * SE.WIN_SEC
    smoothed = V14._smooth(np.asarray(signal, dtype=float)); n = len(smoothed)
    if n < 10:
        return [], ref_iv, total_dur_s, n_inter_h
    s2 = V14._robust_variance(smoothed, real_inter)
    algo = rpt.Pelt(model="l2", min_size=V14.PELT_MIN_SIZE, jump=V14.PELT_JUMP).fit(smoothed.reshape(-1, 1))
    beta = pen * s2 * np.log(n)
    cps_pen = [c for c in algo.predict(pen=beta) if 0 < c < n]
    cps = _mag_filter(V14, smoothed, cps_pen, mag, local_win, real_inter)
    hyp_iv = SE.cps_to_events(cps, is_buffer, n, sz_ranges=sz_ranges)
    return hyp_iv, ref_iv, total_dur_s, n_inter_h


def pooled_score(SE, cache, D):
    TP = FP = 0; Nref = 0; H = 0.0
    for subj, (hyp, ref, dur, nih) in cache.items():
        sc = SE.score_szcore(ref, min_dur_filter(hyp, D), dur, nih)
        TP += sc["tp"]; FP += sc["fp"]; Nref += sc.get("n_ref", len(ref)); H += nih
    sens = TP/Nref if Nref else 0.0; prec = TP/(TP+FP) if TP+FP else 0.0
    f1 = 2*prec*sens/(prec+sens) if prec+sens else 0.0
    return dict(D=D, TP=TP, FP=FP, Nref=Nref, sens=sens, prec=prec, f1=f1, fpd=FP/H*24 if H else float("nan"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ens_dir", default="results/retrain_v3p1/ens")
    ap.add_argument("--val_ens_dir", default="results/retrain_v3p1/val_ens")
    ap.add_argument("--summary_dir", required=False, default="data/summaries")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--smoke", action="store_true")
    a = ap.parse_args()
    if a.smoke:
        smoke(); return

    # locate the repo single-sources (szcore_eval, cpd_pipeline_v14) — they live in src/
    import os
    from pathlib import Path
    here = os.path.dirname(os.path.abspath(__file__))
    cands = [here, os.getcwd(),
             os.path.join(here, "src"), os.path.join(os.getcwd(), "src"),
             os.path.join(here, "src", "retrain"), os.path.join(os.getcwd(), "src", "retrain")]
    for c in cands:
        if os.path.isfile(os.path.join(c, "szcore_eval.py")) and c not in sys.path:
            sys.path.insert(0, c)
    try:
        import szcore_eval as SE, cpd_pipeline_v14 as V14, ruptures as rpt
    except ModuleNotFoundError as e:
        sys.exit(f"[path] cannot import {e.name}. Searched: {cands}\n"
                 f"       Run from repo root, or pass the folder containing szcore_eval.py on PYTHONPATH.")
    def load(d, subj):
        ei = np.load(Path(d)/f"ens_seed{a.seed}_{subj}_inter.npy")
        ec = np.load(Path(d)/f"ens_seed{a.seed}_{subj}_ictal.npy")
        return ei, ec

    def build_cache(subs, d, mag, pen):
        c = {}
        for s in subs:
            ei, ec = load(d, s)
            c[s] = hyp_at(SE, V14, rpt, s, ei, ec, a.summary_dir, mag, pen)
        return c

    # ---- VAL derive D* at mag80/pen5 ----
    vcache = build_cache(VAL_SUBJS, a.val_ens_dir, OP["mag"], OP["pen"])
    val_by_D = {D: pooled_score(SE, vcache, D) for D in D_GRID}
    base_tp = val_by_D[0]["TP"]
    dstar = max([D for D in D_GRID if val_by_D[D]["TP"] == base_tp])
    print("VAL sweep @ mag80/pen5 (TP must stay", base_tp, "for sensitivity-neutral):")
    for D in D_GRID:
        v = val_by_D[D]
        print(f"  D={D:2d}s: TP={v['TP']} FP={v['FP']} sens={v['sens']:.3f} FP/day={v['fpd']:.2f}")
    print(f"  => D* = {dstar} s (largest sensitivity-neutral)\n")

    # ---- TEST one-shot: D=0 vs D* at balanced + triage ----
    for name, op in [("BALANCED mag80/pen5", OP), ("TRIAGE mag55/pen0.3", TRIAGE)]:
        tc = build_cache(TEST_SUBJS, a.ens_dir, op["mag"], op["pen"])
        s0 = pooled_score(SE, tc, 0); sd = pooled_score(SE, tc, dstar)
        print(f"=== {name} ===")
        if abs(op["mag"]-80) < 1 and abs(op["pen"]-5) < 0.01:
            ok = abs(s0["sens"]-0.395) < 0.01 and abs(s0["fpd"]-5.6) < 0.3
            print(f"  [selfcheck D=0] sens={s0['sens']:.3f} FP/day={s0['fpd']:.2f} -> {'OK' if ok else 'MISMATCH'}")
        print(f"  D=0 : sens={s0['sens']:.3f} prec={s0['prec']:.3f} F1={s0['f1']:.3f} FP/day={s0['fpd']:.2f} TP/FP={s0['TP']}/{s0['FP']}")
        print(f"  D={dstar}: sens={sd['sens']:.3f} prec={sd['prec']:.3f} F1={sd['f1']:.3f} FP/day={sd['fpd']:.2f} TP/FP={sd['TP']}/{sd['FP']}")
        verdict = ("KEEP (FP down, sensitivity held)" if sd["TP"] == s0["TP"] and sd["FP"] < s0["FP"]
                   else "REVERT (sensitivity dropped)" if sd["TP"] < s0["TP"]
                   else "no material change")
        print(f"  verdict: {verdict}\n")


if __name__ == "__main__":
    main()