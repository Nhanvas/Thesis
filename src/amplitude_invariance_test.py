#!/usr/bin/env python
"""
amplitude_invariance_test.py -- does the scoring respond to window AMPLITUDE?  (diagnostic, no training)

Save as src/amplitude_invariance_test.py and run from the repo root:
    python src/amplitude_invariance_test.py

For each validation patient it takes the one recording file with the most artifact-flagged windows,
scores it with the canonical GAE (continuous_eval functions, unchanged), then re-scores the SAME
windows after two transformations applied to the z-scored signal, window by window:
    gain   : every channel of the window multiplied by 5      (common gain)
    chunit : every channel of the window rescaled to unit variance (per-channel normalization)
and reports, per branch (reconstruction, latent-distance proxy, gamma coupling):
    - Spearman correlation between the original and transformed scores over all windows
    - AUROC of artifact windows against ordinary background windows, original vs transformed
Reads no seizure annotation except to EXCLUDE ictal and post-seizure windows from the background set.
Validation patients only. Nothing is selected from this output; it tests a premise.
"""
import sys
import time
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import json                       # noqa: E402
import continuous_eval as CE      # noqa: E402

CHUNK = 256
VARIANTS = {
    "orig":   lambda z: z,
    "gain":   lambda z: z * 5.0,
    "chunit": lambda z: (z - z.mean(axis=2, keepdims=True)) / (z.std(axis=2, keepdims=True) + 1e-12),
}
OUT = CE.OUT_DIR / "amplitude_invariance_test.txt"


def pick_file(subj):
    m = CE.load_mask(subj)
    best = None
    for fname, s, e in m["spans"]:
        n_art = int(m["is_artifact"][s:e].sum())
        if best is None or n_art > best[3]:
            best = (fname, int(s), int(e), n_art)
    return m, best


def auc(y, s):
    return float(roc_auc_score(y, s)) if 0 < y.sum() < len(y) else float("nan")


def main():
    model = CE.get_model()
    gb, ga = CE.get_gamma_filter()
    lines = ["# Amplitude-invariance test (validation patients, one file each)", ""]
    for subj in CE.VAL_SUBJS:
        m, (fname, s0, e0, n_art) = pick_file(subj)
        art = m["is_artifact"][s0:e0]
        bad = m["is_ictal"][s0:e0] | m["is_buffer"][s0:e0]
        a_set = art & ~bad
        b_set = ~art & ~bad
        stats = json.loads((CE.PROCESSED_DIR / f"{subj}_stats.json").read_text())
        mean = np.asarray(stats["ch_mean_uV"], dtype=np.float64) * 1e-6
        std = np.asarray(stats["ch_std_uV"], dtype=np.float64) * 1e-6
        t0 = time.time()
        filtered, nw = CE.filter_file(CE.edf_path(subj, fname))
        assert nw == e0 - s0, f"{subj}/{fname}: {nw} windows vs mask {e0 - s0}"
        res = {v: dict(zrecon=[], gz=[], zgamma=[]) for v in VARIANTS}
        for s in range(0, nw, CHUNK):
            e = min(s + CHUNK, nw)
            zsc = CE.zscore(filtered[s:e], mean, std)
            for v, fn in VARIANTS.items():
                c = CE.compute_window_components(fn(zsc), model, gb, ga)
                res[v]["zrecon"].append(c["zrecon_raw"])
                res[v]["gz"].append(c["graph_z"])
                res[v]["zgamma"].append(c["zgamma_raw"])
        del filtered
        sc = {}
        for v in VARIANTS:
            gz = np.concatenate(res[v]["gz"])
            ref = np.median(gz[b_set], axis=0)
            sc[v] = dict(zrecon=np.concatenate(res[v]["zrecon"]),
                         latent=np.linalg.norm(gz - ref, axis=1),      # proxy for the Mahalanobis readout
                         zgamma=np.concatenate(res[v]["zgamma"]))
        y = np.concatenate([np.ones(int(a_set.sum())), np.zeros(int(b_set.sum()))])
        lines += [f"## {subj}  {fname}  windows={nw}  artifact={int(a_set.sum())}  background={int(b_set.sum())}"
                  f"  ({time.time() - t0:.0f}s)", "",
                  "| variant | branch | Spearman vs original | AUROC artifact vs background |", "|---|---|---|---|"]
        for v in VARIANTS:
            for br in ("zrecon", "latent", "zgamma"):
                rho = spearmanr(sc["orig"][br], sc[v][br]).correlation
                a = auc(y, np.concatenate([sc[v][br][a_set], sc[v][br][b_set]]))
                lines.append(f"| {v} | {br} | {rho:.4f} | {a:.3f} |")
        lines.append("")
        print("\n".join(lines[-12:]))
    lines += ["Reading: Spearman 1.0000 under 'gain' = the input is exactly invariant to a common gain, so a "
              "window-wise z-score changes nothing. If artifact-vs-background AUROC stays high under 'chunit', "
              "amplitude is not what makes artifact windows look anomalous and amplitude normalization "
              "will not remove them."]
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print("written", OUT)


if __name__ == "__main__":
    main()
