# F-A1.4 run (2026-11-14 18:34 UTC; code 0e0b4f7087704650; mode exact)

| gate | status | summary |
|---|---|---|
| G-mod | PASS | closed modules from /tmp/Thesis/src |
| mode | PASS | exact (versions vs R2_A: equal) |
| G-data | PASS | 24 earlier .npz, sha256 = R0 references for 24; differing [] |
| G-gcn | PASS | self weight 1/(1 + column sum w) vs gcn_norm on 36495 windows of chb01: max |diff| 1.6e-07 |
| G-jobs | PASS | 4 jobs, 0 not done |
| G-arm | PASS | encode_Z(window graph) = f1_core.encode_D on every held-out case |
| G-base p0 | PASS | gae: PASS 96 rows, 96 exact, k 0.0e+00, caught differ 0/185, fp own/fixed 1129/920; mlp: PASS 96 rows, 96 exact, k 0.0e+00, caught differ 0/185, fp own/fixed 827/650 |

