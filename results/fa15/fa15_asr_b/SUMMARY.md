# fa15_asr_b -- F-A1.5 / PC5 training and scoring (gates and timing; no research number; mode exact)

| gate | status | summary |
|---|---|---|
| G-mod | PASS | r2_r1 76cbe51ff0180d4a, r2_rp 5281446e6168312e (control's code), fa15_run effcdf70588ae6b1 |
| G-data | PASS | 63 files hashed = pinned R1_SMOKE hashes |
| G-repro | PASS | mode exact: control seed 4 rescored = rp2 (456 rows, 456 exact, 0 mismatches; 0 error groups differ) |
| G-asr-data | PASS | 38 ASR cases; labels / buffer / signal loss / file index / files = R0 in 38 of 38 |
| G-asr-counts | PASS | clean training windows ASR 219055 vs R0 270758; validation 53539 vs 56070 (logged; counted on the ASR files) |
| G-vec | PASS | train_gae_v2.py --smoke vs tensor loop: max /weight difference/ 0.000e+00 |
| R1.1-training | PASS | seeds [4, 5, 6, 7]: n_train 219055, 3,964 parameters, G2 PASS |
| RUN-complete | PASS | 1824 rows (expected 1824); k per seed {'clean_seed4': 2.8721520873445447, 'clean_seed5': 2.792166414852648, 'clean_seed6': 2.8666195672726937, 'clean_seed7': 2.9521611642498593} |
| G-worker-sha | PASS | 4 of 4 workers imported r2_r1 76cbe51ff0180d4a, r2_rp 5281446e6168312e, fa15_run effcdf70588ae6b1 |

Phases (s): {"views": 294.4, "gate_data": 21.2, "D_repro": 297.6, "score_repro": 185.5, "g_repro": 483.3, "views_asr": 2.9, "gate_asr_data": 93.8, "gate_vec": 3.8, "train": 12710.1, "D_run": 609.8, "score_run": 930.3}

Tables: `python src/fa15_aggregate.py` (committed before this run).
