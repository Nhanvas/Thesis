# RP_SERIES fix B — pass-A component timing (container) and the computed Kaggle runtime (timing only; no research number)

Script `src/r2_rps_timing.py` (D27-F, 14/11). Build container: 2 cores, 1 process, numpy 2.5.3, pandas 3.0.5, ruptures
1.1.10. Series: the committed path-2 final scores (`rp/rp2/scores`), seeds 1–4: chb06 (real, 60,060 windows, 18 files of
up to 3,606 windows) and a chb04-shaped series (real values of 8 test series, 140,453 windows cut into chb04's 42 file
lengths). Latent / distance arrays random of the real shapes (cost depends on size only).

| component (4 seeds) | chb06 s | chb04-shaped s | growth exponent |
|---|---|---|---|
| test path (final scalar, q, run_budget × 4 arms, compare, save) | 5.2 | 13.1 | 1.10 |
| e16 arms (S9 base + a–e, grid, mechanism, diagnostics) | 32.2 | 75.0 | 1.00 |
| D1b grid | 2.7 | 6.6 | 1.03 |
| Table 7: locked PELT (2 points, ruptures pure Python, whole timeline) | 163.6 | 619.0 | 1.57 |
| Table 7: E7 D2, exact (`r2_e7exact`, incl. scoring) | 41.0 | 84.0 | 1.00 (fitted 0.85, floored) |
| Table 7: E10 D1 + K | 58.0 | 119.5 | 1.00 |

For comparison (the cause of the stop): ruptures' E7 D2 on one chb06 file of 3,606 windows, one seed, takes 12 / 98 / 91 s
for c = 1 / 3 / 10 (container spot check, D27-F), against 0.2–0.3 s for the exact implementation.

Kaggle factor: 105 s measured for chb06 in the first RP_SERIES run minus its distances (0.93 s per hour of EEG, R1_SMOKE)
over the container's test path = 8.3 (upper bound: it includes the worker start, ≈ 24 s in R1_SMOKE); the earlier ratio
2.5 reproduces chb10's measured 15,052 s from its computed container time. Projection (`projection.csv`, `projection.json`):

| | factor 2.5 | factor 8.3 |
|---|---|---|
| chb04 (largest case) | 0.7 h | 2.2 h |
| pass A, 4 workers (largest first) | 0.7 h | 2.2 h |
| + A-latent, flags (raw EEG of 12 patients), RP5, setup (allowances) | 1.3 h | 1.3 h |
| notebook | ≈ 2.0 h | ≈ 3.5 h |

Against the 12-h session: no resume and no split by case needed. RP_SERIES writes `timing.csv` with every component per
case (measured on Kaggle).
