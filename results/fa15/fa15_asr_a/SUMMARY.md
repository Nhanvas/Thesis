# fa15_asr_a -- F-A1.5 / PC5 training and scoring (gates and timing; no research number; mode exact)

| gate | status | summary |
|---|---|---|
| G-mod | PASS | r2_r1 76cbe51ff0180d4a, r2_rp 5281446e6168312e (control's code), fa15_run effcdf70588ae6b1 |
| G-data | PASS | 63 files hashed = pinned R1_SMOKE hashes |
| G-repro | PASS | mode exact: control seed 4 rescored = rp2 (456 rows, 456 exact, 0 mismatches; 0 error groups differ) |
| G-asr-data | PASS | 38 ASR cases; labels / buffer / signal loss / file index / files = R0 in 38 of 38 |
| G-asr-counts | PASS | clean training windows ASR 219055 vs R0 270758; validation 53539 vs 56070 (logged; counted on the ASR files) |
| G-vec | PASS | train_gae_v2.py --smoke vs tensor loop: max /weight difference/ 0.000e+00 |
| R1.1-training | PASS | seeds [42, 1, 2, 3]: n_train 219055, 3,964 parameters, G2 PASS |
| RUN-complete | PASS | 1824 rows (expected 1824); k per seed {'clean_seed42': 2.8786777530639167, 'clean_seed1': 2.7997982302226267, 'clean_seed2': 2.8320106815676818, 'clean_seed3': 2.9227961006663703} |
| G-worker-sha | PASS | 4 of 4 workers imported r2_r1 76cbe51ff0180d4a, r2_rp 5281446e6168312e, fa15_run effcdf70588ae6b1 |

Phases (s): {"views": 79.6, "gate_data": 20.8, "D_repro": 247.0, "score_repro": 163.7, "g_repro": 410.9, "views_asr": 2.0, "gate_asr_data": 20.7, "gate_vec": 3.3, "train": 10563.6, "D_run": 539.1, "score_run": 806.5}

Tables: `python src/fa15_aggregate.py` (committed before this run).
