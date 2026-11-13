# RP-dm group 1 — Chapter 2 numbers of version A2 from committed files (no run)

Script `src/r2_rpdm1.py`. Values are read from the named files; derived values are computed.

| ID | item | value | source | note |
|---|---|---|---|---|
| F-R170.1 | scored hours, training | 563.4 | `results/r2/r0_data/chb/inventory_cases.csv (hours_used_windows)` | seizures in used files 80 |
| F-R170.1 | scored hours, validation | 115.82 | `results/r2/r0_data/chb/inventory_cases.csv (hours_used_windows)` | seizures in used files 13 |
| F-R170.1 | scored hours, test | 279.38 | `results/r2/r0_data/chb/inventory_cases.csv (hours_used_windows)` | seizures in used files 76 |
| F-R170.2 | training windows (clean, 12 training patients), every seed | 270758 | `results/r2/r1_system/rp/models/gae_v2_clean_seed4.json` | seed 4; seeds 1-3 = R1 gate R1.1-training n_train 270758 (run/SUMMARY.md), same data |
| F-R170.3 | k, seed 1 | 4.1313 | `results/r2/r1_system/rp/rp2/k.json` |  |
| F-R170.3 | k, seed 2 | 3.9446 | `results/r2/r1_system/rp/rp2/k.json` |  |
| F-R170.3 | k, seed 3 | 4.0384 | `results/r2/r1_system/rp/rp2/k.json` |  |
| F-R170.3 | k, seed 4 | 4.0092 | `results/r2/r1_system/rp/rp2/k.json` |  |
| F-R170.4 | validation loss, seed 1 | 0.020844 | `results/r2/r1_system/rp/demo_model.json` |  |
| F-R170.4 | validation loss, seed 2 | 0.020849 | `results/r2/r1_system/rp/demo_model.json` |  |
| F-R170.4 | validation loss, seed 3 | 0.020768 | `results/r2/r1_system/rp/demo_model.json` |  |
| F-R170.4 | validation loss, seed 4 | 0.020801 | `results/r2/r1_system/rp/demo_model.json` |  |
| F-R170.6 | application model (lowest validation loss) | seed 3 | `results/r2/r1_system/rp/demo_model.json` | checkpoint results/r2/r1_system/run/models/gae_v2_clean_seed3.pt |
| F-dm.3b | largest development budget, seed 1 | 0.0106 | `results/r2/r1_system/rp/rp2/q.csv` | patient chb08; median q_raw 0.00500; patients at the upper limit 0.02: 0 |
| F-dm.3b | largest development budget, seed 2 | 0.0125 | `results/r2/r1_system/rp/rp2/q.csv` | patient chb19; median q_raw 0.00499; patients at the upper limit 0.02: 0 |
| F-dm.3b | largest development budget, seed 3 | 0.0116 | `results/r2/r1_system/rp/rp2/q.csv` | patient chb09; median q_raw 0.00502; patients at the upper limit 0.02: 0 |
| F-dm.3b | largest development budget, seed 4 | 0.0105 | `results/r2/r1_system/rp/rp2/q.csv` | patient chb19; median q_raw 0.00502; patients at the upper limit 0.02: 0 |
| F-dm.6 | 5-SD flag share of non-seizure training windows (12 training patients, all files) | 0.4249 | `results/r2/r0_data/chb/stats_earlier/*.json + diff_chb11_chb21.json (chb21 complete)` | flagged 200050, not flagged 270754 (computed) |

Not here (need a run): F-dm.7 (flag share of seizure windows; chb12's seizure windows under R0's thresholds are not in a committed file), F-dm.8 (from RP7, application seed 3 with label-free statistics vs RP2 seed 3), F-dm.1, F-dm.2, F-dm.3a, F-dm.4, F-dm.5, F-dm.9 (RP_SERIES, design to approve).
