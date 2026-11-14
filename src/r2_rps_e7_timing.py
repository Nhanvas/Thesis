"""Timing of the Table 7 detectors of RP_SERIES on committed path-2 final scores (D26-F, 14/11; plan §12 14/11 18:30).

Why: the first RP_SERIES run (clone f526e9d) spent 15,052 s on chb10 and had not finished chb04 / chb07 / chb09 after
5.7 h. This script measures, on real series, which detector takes the time. It reads only committed files
(`results/r2/r1_system/rp/rp2/scores/{case}.csv.gz`: x of seed 3, ok, ictal, file_idx). The ictal column is used only to
build the label-aware magnitude mask of the locked PELT, as `diag_detector_ceiling` does; no result is scored or read.

    python src/r2_rps_e7_timing.py chb16 detectors      # E7 D2 (3 penalties), E10 K (3 penalties), locked PELT (2 points)
    python src/r2_rps_e7_timing.py chb06 scaling        # E7 D2 on one file cut to 900 / 1,800 / whole windows

Measured in the chat container (2 cores, 1 process, ruptures 1.1.10), 14/11:
    chb16 (17,100 windows, 19 files of 900): E7 D2 pen 1 / 3 / 10 = 9.9 / 55.4 / 81.7 s; E10 K 0.2-0.3 s each;
    locked PELT 50/2.0/90 2.0 s, 75/5/300 4.0 s.
    chb06 longest file: n = 900: 5.5 / 6.0 s (pen 3 / 10); n = 1,800: 20.4 / 19.6 s; n = 3,606: 89.4 / 86.4 s.
"""
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import ruptures as rpt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import cpd_pipeline_v14 as V14          # noqa: E402
import e10_kernel_cpd as E10            # noqa: E402
import e7_ensemble_cpd as E7            # noqa: E402

SEED_COL = "x_s3"


def load(case):
    d = pd.read_csv(ROOT / "results/r2/r1_system/rp/rp2/scores" / f"{case}.csv.gz")
    x = d[SEED_COL].values.astype(float)
    return d, x, d.file_idx.values.astype(int), d.ok.values.astype(bool)


def sigma_e7(x, ok):
    """e7_ensemble_cpd.d2_grid's noise scale, verbatim."""
    x_all = x.copy()
    x_all[~ok] = np.median(x_all[ok])
    dif = np.diff(x_all[ok])
    return x_all, 1.4826 * np.median(np.abs(dif - np.median(dif))) / np.sqrt(2) + 1e-9


def detectors(case):
    d, x, fidx, ok = load(case)
    print(case, "windows", len(x), "files", len(np.unique(fidx)), "longest file", int(np.bincount(fidx).max()), flush=True)
    x_all, sigma = sigma_e7(x, ok)
    for c in E7.PENS:
        t = time.time()
        nseg = 0
        for f in np.unique(fidx):
            xx = x_all[fidx == f]
            if len(xx) < 4:
                continue
            nseg += len(rpt.Pelt(model="l2", min_size=2, jump=1).fit(xx.reshape(-1, 1))
                        .predict(pen=c * sigma ** 2 * np.log(len(xx))))
        print(f"E7 D2 pen {c}: {time.time() - t:.1f} s, segments {nseg}", flush=True)
    z = dict(is_signal_loss=~ok, file_idx=fidx)
    for pen in E10.PENS:
        t = time.time()
        E10.k_segments(z, x, pen)
        print(f"E10 K pen {pen}: {time.time() - t:.1f} s", flush=True)
    inter = ok & (d.ictal.values == 0)
    for mag, pen, ms in ((50, 2.0, 90), (75, 5, 300)):
        t = time.time()
        V14.detect_events(x, pen, min_mag_pct=mag, local_win=15, inter_mask=inter, merge_s=ms)
        print(f"locked PELT {mag}/{pen}/{ms}: {time.time() - t:.1f} s", flush=True)


def scaling(case):
    _, x, fidx, ok = load(case)
    x_all, sigma = sigma_e7(x, ok)
    f = int(np.argmax(np.bincount(fidx)))
    xx = x_all[fidx == f]
    for n in (900, 1800, len(xx)):
        for c in (3.0, 10.0):
            t = time.time()
            bk = rpt.Pelt(model="l2", min_size=2, jump=1).fit(xx[:n].reshape(-1, 1)).predict(pen=c * sigma ** 2 * np.log(n))
            print(f"n={n} pen {c}: {time.time() - t:.1f} s, segments {len(bk)}", flush=True)


if __name__ == "__main__":
    {"detectors": detectors, "scaling": scaling}[sys.argv[2]](sys.argv[1])
