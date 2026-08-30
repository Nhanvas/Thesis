"""
artifact_fp_diagnostic.py — Phase C-final, artifact-gate PRE-CONDITION test. numpy only.

QUESTION (answer in minutes, no retrain, no overnight): are rlg's false-positive-prone
VAL interictal windows ARTIFACT-associated? Preprocessing already drops >5 SD amplitude
artifacts from interictal, so the surviving FPs may NOT be gross artifacts — if so, an
extra artifact gate cannot help BY CONSTRUCTION, and we skip it in minutes instead of
burning an overnight run.

METHOD (label-free, VAL only):
  * FP-prone label = top-Q% ensemble anomaly score among INTERICTAL windows (these are
    exactly the windows that create false change-points / false positives).
  * For each label-free signal-quality metric computed from the raw window, measure
    AUROC separating FP-prone vs the rest. Also Spearman(anomaly_score, metric).
  Metrics (from raw [18,1024], fs=256, already bandpassed 0.5-60 + notch 60, z-scored):
    hf_ratio (30-60Hz / total; muscle), line60 (58-62Hz residual), delta_ratio (0.5-4Hz;
    movement/sweat), var_mean, max_abs (residual high-amp), grad_max (jumps/pops),
    flat_min (electrode disconnect), chan_disp (single-channel blow-up).

DECISION (pre-registered):
  * best-metric AUROC >= 0.65 (and > the shuffled null) on >=2/3 VAL subjects
        -> FPs ARE artifact-associated -> BUILD the score-level gate (high confidence).
  * best-metric AUROC < 0.60 on >=2/3 subjects
        -> FPs are NOT artifacts (the 5-SD preproc gate already removed gross ones)
        -> an artifact gate cannot help; SKIP -> move to queue #2 (multi-band AEC).
  * in between -> marginal; report, decide with Boti.

Usage (local, ~minutes):
  python src/phaseC/artifact_fp_diagnostic.py \
    --ens_dir results/phaseB/tier2/ens_val_tf/rlg --seed 42 \
    --raw_dir data/processed --out_dir results/phaseC/artifact_probe
"""
import argparse, glob, json
from pathlib import Path

import numpy as np
from sklearn.metrics import roc_auc_score

VAL = ["chb10", "chb11", "chb22"]
TEST = {"chb03", "chb06", "chb13", "chb14", "chb15", "chb16", "chb17", "chb18"}
FS = 256
TOPQ = 0.10                       # top 10% anomaly = FP-prone
GO_AUROC, SKIP_AUROC = 0.65, 0.60


def quality_metrics(W):
    """W [18,1024] -> dict of scalar label-free quality metrics."""
    C, T = W.shape
    W = np.asarray(W, np.float64)
    # spectral (per-channel rfft power, averaged over channels)
    fr = np.fft.rfftfreq(T, 1.0 / FS)
    psd = (np.abs(np.fft.rfft(W, axis=1)) ** 2)              # [18, F]
    tot = psd.sum(axis=1) + 1e-12
    band = lambda lo, hi: psd[:, (fr >= lo) & (fr < hi)].sum(axis=1)
    hf = (band(30, 60) / tot).mean()
    line = (band(58, 62) / tot).mean()
    del_ = (band(0.5, 4) / tot).mean()
    # time-domain
    var = W.var(axis=1)
    return dict(hf_ratio=float(hf), line60=float(line), delta_ratio=float(del_),
                var_mean=float(var.mean()), max_abs=float(np.abs(W).max()),
                grad_max=float(np.abs(np.diff(W, axis=1)).max()),
                flat_min=float(np.sqrt(var).min()),
                chan_disp=float(var.std()))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ens_dir", default="results/phaseB/tier2/ens_val_tf/rlg")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--raw_dir", default="data/processed")
    ap.add_argument("--out_dir", default="results/phaseC/artifact_probe")
    ap.add_argument("--topq", type=float, default=TOPQ)
    a = ap.parse_args()

    metrics = ["hf_ratio", "line60", "delta_ratio", "var_mean", "max_abs",
               "grad_max", "flat_min", "chan_disp"]
    per_subj = {}
    print(f"FP-prone = top {a.topq:.0%} anomaly among interictal. AUROC: metric separates FP-prone vs rest.\n")
    header = "subj    " + "".join(f"{m[:8]:>9s}" for m in metrics) + "   best"
    print(header)

    for subj in VAL:
        assert subj not in TEST
        ens = np.load(Path(a.ens_dir) / f"ens_seed{a.seed}_{subj}_inter.npy")
        raw = np.load(Path(a.raw_dir) / f"{subj}_interictal.npy", mmap_mode="r")
        n = min(len(ens), len(raw))
        assert abs(len(ens) - len(raw)) <= 1, f"{subj} align ens {len(ens)} vs raw {len(raw)}"
        ens = np.asarray(ens[:n], float)
        # FP-prone label
        thr = np.quantile(ens, 1 - a.topq)
        y = (ens >= thr).astype(int)
        # quality metrics per window
        Q = np.array([[quality_metrics(raw[i])[m] for m in metrics] for i in range(n)])
        aus = {}
        for j, m in enumerate(metrics):
            q = Q[:, j]
            # AUROC in the direction that best separates (artifact could be high OR low)
            au = roc_auc_score(y, q)
            aus[m] = round(max(au, 1 - au), 3)      # |direction|
        best_m = max(aus, key=aus.get)
        per_subj[subj] = dict(aurocs=aus, best_metric=best_m, best_auroc=aus[best_m],
                              n=int(n), n_fp_prone=int(y.sum()))
        row = f"{subj:7s} " + "".join(f"{aus[m]:9.3f}" for m in metrics) + f"   {best_m}={aus[best_m]:.3f}"
        print(row)

    # null: shuffle labels once per subject, best-metric AUROC should collapse to ~0.5
    print("\n[null] shuffled-label best-metric AUROC (should be ~0.5):")
    rng = np.random.default_rng(0)
    for subj in VAL:
        ens = np.load(Path(a.ens_dir) / f"ens_seed{a.seed}_{subj}_inter.npy")
        raw = np.load(Path(a.raw_dir) / f"{subj}_interictal.npy", mmap_mode="r")
        n = min(len(ens), len(raw))
        Q = np.array([[quality_metrics(raw[i])[m] for m in metrics] for i in range(n)])
        yr = rng.integers(0, 2, n)
        best = max(max(roc_auc_score(yr, Q[:, j]), 1 - roc_auc_score(yr, Q[:, j])) for j in range(len(metrics)))
        print(f"  {subj}: null best-AUROC={best:.3f}")

    bests = [per_subj[s]["best_auroc"] for s in VAL]
    n_go = sum(b >= GO_AUROC for b in bests)
    n_skip = sum(b < SKIP_AUROC for b in bests)
    print("\n" + "=" * 60)
    if n_go >= 2:
        verdict = "BUILD artifact gate — FPs ARE artifact-associated (high confidence)"
    elif n_skip >= 2:
        verdict = "SKIP artifact gate — FPs NOT artifact-distinguishable (5-SD preproc already removed gross ones) -> queue #2 (multi-band AEC)"
    else:
        verdict = "MARGINAL — report, decide with Boti"
    print(f"best-AUROC per subject: {dict(zip(VAL, [round(b,3) for b in bests]))}")
    print(f"PRE-REGISTERED: {verdict}")
    print("=" * 60)

    out = Path(a.out_dir); out.mkdir(parents=True, exist_ok=True)
    (out / f"artifact_fp_diagnostic_seed{a.seed}.json").write_text(
        json.dumps(dict(per_subject=per_subj, verdict=verdict), indent=2))
    print(f"[saved] {out}/artifact_fp_diagnostic_seed{a.seed}.json")


if __name__ == "__main__":
    main()
