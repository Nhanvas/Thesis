# Synthetic tests of delivery D37F4 (chat D37-F, 22/11/2026)

Delivery D37F4 = the training step of PC6 (`DESIGN_PC6.md` §4, §6): `src/eur_abl.py` (arms 11a / 11b, gates G-g11data and
G-pc6view, `arm_adj`), the notebook builder entry, the notebooks `EUR_PC6_11a` / `EUR_PC6_11b`, the reader
`src/eur_pc6_read.py` and its test. The run-record notebooks (`EUR_PC8_*`, `EUR_PC6_DATA`) are not rebuilt. Run in the
build container from a frozen copy of the repository (main `928b88f` + the D37F4 files; compared file by file with the
delivered files after the runs: identical); library versions as in `SYNTH_TEST_D37F3.md`; 2 CPU cores.

| test | result | measured |
|---|---|---|
| `src/eur_pc6_synthetic_test.py` (new) | **ALL PASS** — P1 both notebooks, every gate incl. G-g11data, G-pc6view, G-pc7reuse (R0 seed 42 only), G-pc7rep, G-guard (2 chunks), G-pc7k, G-pc7r0; V0 × 4, R0 × seed 42, arm × 3 seeds on 26 cases; the arm json names its graph. N1 (non-circular) 11a seed 1 = `f1_core.train` on views of the record `.npz` written by the test with adj = the 11a graph, exactly; the 11b scalar of chb03 recomputed from `model_cmp_core.node_input` on the 11b graph with a per-window forward (max abs diff 0.0); the same checkpoint on the record graph gives another scalar (the graph is used). R reader gates M0 / M1 / M2 / M4, every table. NEG1 a changed graph file → STOP G-g11data; NEG2 a graph one window short with a matching manifest → STOP G-pc6view; NEG3 one run twice → the reader stops; NEG4 edited module → the notebook refuses | 1,800 s |
| `src/eur_pc8_synthetic_test.py` | **ALL PASS** (PC8 behaviour unchanged) | 2,071 s |
| `src/eur_pc7_synthetic_test.py` | **ALL PASS** (PC7 behaviour unchanged) | 1,200 s |
| `src/eur_pc1_synthetic_test.py` | **ALL PASS** (PC1 behaviour unchanged) | 1,143 s |
| `src/eur_pc6_data_synthetic_test.py` | **ALL PASS** (data step with the changed `eur_abl.py`) | 370 s |

Found and fixed during the tests: (1) the view check compared the view's adj dtype with the record's instead of the stored
arm graph's; (2) float arrays were compared without NaN = NaN (f7 holds NaN on some signal-loss windows), which would have
stopped the real run at G-pc6view; (3) the test world took two cases from a complete-data copy instead of the record copy.
