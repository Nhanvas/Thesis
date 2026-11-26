# SzScan Step 2 gates

Commit `17b86fc`. Rebuilt from the run log by `src/c5_gates_from_log.py` (the run stopped in the hospital part before writing; every row below was printed by the run itself).

- **G1** session engine = committed application-tier events: PASS (8 subjects, 0 files differ)
- **G3** Siena through edf_input = x1_external.load_18: PASS (41 files, load_18 itself on 6 files, skipped on 35 (predicted above the limit); sha256 not matching PhysioNet: none)
- **G4** mains suggestion on Siena: 50 Hz 19, 60 Hz 0, none 22
- **G5** bad-electrode rule on Siena: 8 files flagged ['PN03-1.edf: FZ O2 P8', 'PN05-3.edf: P3 P4 PZ', 'PN05-4.edf: FZ', 'PN06-4.edf: PZ', 'PN06-5.edf: PZ', 'PN07-1.edf: F7 F8', 'PN10-1.edf: PZ', 'PN13-2.edf: CZ']
- **G6** private memory peak (resident peaks, file pages included, in the CSVs): load max 1691 MB, Phase A max 1692 MB; G1 per subject max 1596 MB

Per row: `g1.csv`, `siena.csv`. Hospital records: private report in Agent/inbox only.
