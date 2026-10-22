# `results/` — index

Each report table and figure is mapped to its result file and command in the main
[README](../README.md), section 6. The folders of the final system are:

| Folder | Content |
|---|---|
| `p3c_freeze/` | frozen detector and localizer settings (`freeze.json`), development results |
| `e22_test_oneshot/` | CHB-MIT test, held-out evaluation (+ `BOOTSTRAP.md`) |
| `e23_test_look7/` | CHB-MIT test, final system (test-informed) |
| `x1_external/` | external validation: chb24 and Siena |
| `attribution_v8/` | channel-level explanation of the final system (labels in `attribution_v7/labels/source/`) |
| `application_eval_v4/` | review application on the 8 test patients |
| `t1_demo/` | application identity check and timing |
| `p3_anatomy/`, `p3_levers/`, `e16_*`, `e17b_*`, `e18_*`, `e21_*` | design steps on the development patients |
| `figures_v8_data/`, `diagnostics/density_frobenius_v2/` | inputs of report figures |
| `p2_ledger.csv` | every arm tried (`verdict` = gate of that step, not the final choice) |

Folders of earlier systems (`retrain_v3p1/`, `attribution_v5/`, `phaseB/`, `history_superseded/`, …) are
kept for provenance and are **not** results of the thesis. The previous version of this index is in
`archive/docs/results_README_pre-R1.md`.
