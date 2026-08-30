"""
artifact_gate.py — Phase C-final, label-free artifact gate. numpy only (no GPU/retrain).

PRE-REGISTERED (Boti-approved 2026-08, after artifact_fp_diagnostic PASS: FP-prone
interictal windows are artifact-associated, best-AUROC 0.78-0.80, grad_max dominant):

  H: suppressing the ensemble anomaly score on transient-artifact windows (grad_max-led,
     which the 5-SD amplitude preproc gate lets through) removes FP-driving spikes ->
     Pareto-win on VAL (F1 up at matched FP/day, or sens up), WITHOUT sens drop > seed-SD.

  Gate (label-free, ONE config — no threshold sweep = no fishing):
    * artifact score = grad_max = max |first-difference| over channels, per window
      (the diagnostic's dominant metric; catches jumps/pops that pass 5-SD amplitude).
    * threshold = INTERICTAL PCTL-th percentile (label-free; seizures never used to set it).
    * SAME threshold applied to BOTH inter and ictal ens (label-free -> cannot cheat by
      sparing ictal). Flagged window's ens score -> interictal MEDIAN (background) so it
      cannot spawn a false change-point.

  Falsification (measured by score_ens on the gated ens, matched FP/day):
    no Pareto-win, or macro sensitivity drop > seed-SD -> clean negative -> queue #2.

  This script only PRODUCES the gated ens arrays (parallel dir; rlg ens untouched). The
  VAL gate itself is the LOCKED score_ens.py run on gated vs original -> zero scorer
  reimplementation (same path used to VAL-gate C4-lite / slope-gate).

  It also PREVIEWS the falsification: prints % of ICTAL windows the label-free threshold
  flags per subject -> a high number forecasts a sensitivity hit before any scoring.

Usage (local, minutes):
  python src/phaseC/artifact_gate.py \
    --ens_dir results/phaseB/tier2/ens_val_tf/rlg --seed 42 \
    --raw_dir data/processed --pctl 95 \
    --out_dir results/phaseC/artifact_gate/ens_val_gated
  # then VAL-gate with the LOCKED scorer:
  #   score_ens.py --ens_dir <that out_dir> --seed 42 --only_subjects chb10,chb11,chb22 ...
  #   score_ens.py --ens_dir results/phaseB/tier2/ens_val_tf/rlg --seed 42 --only_subjects chb10,chb11,chb22 ...
  # compare F1/sens at matched FP/day (g2_val_gate / c1_lowfp_compare).
"""
import argparse, json
from pathlib import Path

import numpy as np

VAL = ["chb10", "chb11", "chb22"]
TEST = {"chb03", "chb06", "chb13", "chb14", "chb15", "chb16", "chb17", "chb18"}
FS = 256


def grad_max_per_window(raw_path):
    """[N,18,1024] -> [N] max |first-difference| across channels/time (label-free)."""
    raw = np.load(raw_path, mmap_mode="r")
    N = len(raw)
    out = np.empty(N, dtype=np.float32)
    for i in range(N):
        out[i] = np.abs(np.diff(np.asarray(raw[i], np.float64), axis=1)).max()
    return out


def isolated_mask(cand, max_run):
    """True only where `cand` is inside a run of consecutive True of length <= max_run.
    Duration/isolation mechanism (pre-registered rationale): brief artifact spikes are
    isolated (short runs); sustained seizures span long runs -> NOT flagged -> spared.
    A seizure onset sits at the START of a long ictal run -> also spared."""
    cand = np.asarray(cand, bool); n = len(cand); out = np.zeros(n, bool)
    i = 0
    while i < n:
        if cand[i]:
            j = i
            while j < n and cand[j]:
                j += 1
            if (j - i) <= max_run:
                out[i:j] = True
            i = j
        else:
            i += 1
    return out


def apply_gate(ens, art, thr, fill, isolation=0):
    """Suppress ens where flagged -> fill. isolation=0 -> per-window (flag all art>thr);
    isolation>0 -> flag only isolated runs (<= isolation consecutive) so sustained
    seizures survive. Returns (gated, n_flagged)."""
    ens = np.asarray(ens, np.float32).copy()
    cand = art > thr
    mask = isolated_mask(cand, isolation) if isolation > 0 else cand
    ens[mask] = fill
    return ens, int(mask.sum())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ens_dir", default="results/phaseB/tier2/ens_val_tf/rlg")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--raw_dir", default="data/processed")
    ap.add_argument("--pctl", type=float, default=95.0, help="interictal grad_max percentile (label-free)")
    ap.add_argument("--isolation", type=int, default=0, help="0=per-window; >0=flag only runs <= N consecutive (spare sustained seizures)")
    ap.add_argument("--out_dir", default="results/phaseC/artifact_gate/ens_val_gated")
    ap.add_argument("--subjects", default=None)
    ap.add_argument("--allow_test", action="store_true")
    a = ap.parse_args()

    subjs = a.subjects.split(",") if a.subjects else VAL
    leak = [s for s in subjs if s in TEST]
    if leak and not a.allow_test:
        raise SystemExit(f"INTEGRITY ABORT: TEST subject(s) {leak}. --allow_test for Stage-2 one-shot only.")

    out = Path(a.out_dir); out.mkdir(parents=True, exist_ok=True)
    iso = f", isolation<= {a.isolation} win" if a.isolation>0 else ", per-window"
    print(f"gate: grad_max > interictal p{a.pctl:.0f}{iso}, suppress->interictal median (label-free)\n")
    print(f"{'subj':7s} {'n_inter':>8s} {'flag_int%':>9s} {'n_ictal':>8s} {'flag_ict%':>9s}  falsif-preview")
    report = {}
    for subj in subjs:
        ei = np.load(Path(a.ens_dir) / f"ens_seed{a.seed}_{subj}_inter.npy")
        ec = np.load(Path(a.ens_dir) / f"ens_seed{a.seed}_{subj}_ictal.npy")
        ai = grad_max_per_window(Path(a.raw_dir) / f"{subj}_interictal.npy")
        ac = grad_max_per_window(Path(a.raw_dir) / f"{subj}_ictal.npy")
        ni, nc = min(len(ei), len(ai)), min(len(ec), len(ac))
        assert abs(len(ei)-len(ai)) <= 1 and abs(len(ec)-len(ac)) <= 1, \
            f"{subj} align ens/raw inter {len(ei)}/{len(ai)} ictal {len(ec)}/{len(ac)}"
        ei, ai, ec, ac = ei[:ni], ai[:ni], ec[:nc], ac[:nc]

        thr = float(np.percentile(ai, a.pctl))     # label-free: from interictal only
        fill = float(np.median(ei))
        ei_g, nfi = apply_gate(ei, ai, thr, fill, isolation=a.isolation)
        ec_g, nfc = apply_gate(ec, ac, thr, fill, isolation=a.isolation)   # SAME thr on ictal (label-free)

        np.save(out / f"ens_seed{a.seed}_{subj}_inter.npy", ei_g)
        np.save(out / f"ens_seed{a.seed}_{subj}_ictal.npy", ec_g)
        pct_i, pct_c = 100.0*nfi/max(ni,1), 100.0*nfc/max(nc,1)
        warn = "  <-- high ictal flag: sens risk!" if pct_c > 15 else ""
        print(f"{subj:7s} {ni:8d} {pct_i:9.1f} {nc:8d} {pct_c:9.1f}{warn}")
        report[subj] = dict(n_inter=ni, flag_inter_pct=round(pct_i,2),
                            n_ictal=nc, flag_ictal_pct=round(pct_c,2),
                            thr=round(thr,4), fill=round(fill,4))

    macro_ict = float(np.mean([report[s]["flag_ictal_pct"] for s in subjs]))
    print(f"\n[preview] macro ictal-flag {macro_ict:.1f}%  "
          f"(low = gate spares seizures; high = expect sensitivity hit)")
    print(f"[saved] gated ens -> {out}")
    print("\nNEXT: VAL-gate with the LOCKED scorer (gated vs original), compare F1/sens @ matched FP/day.")
    (out / "artifact_gate_report.json").write_text(json.dumps(
        dict(pctl=a.pctl, isolation=a.isolation, per_subject=report, macro_ictal_flag_pct=round(macro_ict,2)), indent=2))


def _smoke():
    rng = np.random.default_rng(0)
    raw = rng.standard_normal((50, 18, 1024)).astype(np.float32)
    raw[7, 3, 500] += 40.0                       # inject a jump artifact in window 7
    import tempfile, os
    d = tempfile.mkdtemp()
    np.save(os.path.join(d, "chbX_interictal.npy"), raw)
    art = grad_max_per_window(os.path.join(d, "chbX_interictal.npy"))
    assert art.argmax() == 7, "grad_max should peak on the injected jump window"
    ens = rng.random(50).astype(np.float32); ens[7] = 5.0    # artifact also spikes anomaly
    thr = float(np.percentile(art, 90)); g, nf = apply_gate(ens, art, thr, float(np.median(ens)))
    assert g[7] < ens[7] and nf >= 1, "gate should suppress the artifact spike"
    print(f"[SMOKE] grad_max peaks on injected jump (win 7); gate suppressed {nf} window(s); "
          f"ens[7] {ens[7]:.2f}->{g[7]:.2f}  PASS")


if __name__ == "__main__":
    import sys
    if "--smoke" in sys.argv:
        _smoke()
    else:
        main()
