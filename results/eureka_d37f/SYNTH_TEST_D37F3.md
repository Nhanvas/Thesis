# Synthetic test of delivery D37F3 (chat D37-F, 22/11/2026)

Delivery D37F3 = the data step of PC6 (`DESIGN_PC6.md` §3): `src/eur_pc6_data.py`, its test, the notebook builder entry
and the notebook `EUR_PC6_DATA`. Run in the build container from a frozen copy of the repository (main `e32902b` + D37F2
+ D37F3 files; compared file by file with the delivered files after the run: identical; the delivered notebook = the
tested one); library versions as in `SYNTH_TEST_D37F1.md` plus pyedflib 0.1.42 (synthetic EDF writer only); 2 CPU cores.

| test | result | measured |
|---|---|---|
| `src/eur_pc6_data_synthetic_test.py` (new) | **ALL PASS** — P1 every gate (G-raw, G-data, G-stack[smoke], G-feat0, PROJ, G-stack, G-struct, G-adj, G-edges, G-worker[pool], G-done); 26 graph files with the record's window counts; manifest sha256 = the files; the rebuilt combined graph = the record graph exactly in every case (one container); no EDF or feature `.npz` in the output. N1 (non-circular) wPLI-only and AEC-only graphs of chb03 (record signal path, committed statistics) and of Siena PN00 (x1 loader, filter, label-free statistics) recomputed from the raw EDF without the builders = the stored graphs. N2 the arm graphs differ from each other and from the record; ≥ 30 edges per chain window. NEG1 wrapper not installed → STOP G-stack; NEG2 a record graph changed in 5 % of one case's windows → STOP G-adj; NEG3 edited module → the notebook refuses | 406 s |

Found and fixed during the test: the CHB-MIT jobs run in spawn workers, which do not hold the parent's output-folder
state, so the graph folder is now passed into each job.
