# SzScan Step 2 gates — SMOKE

Commit `20c5172b3585504bdb88e82b4c8a3c1a1eff5e09`.

- **G1** session engine = committed application-tier events: PASS (1 subjects, 0 files differ)
- **G3** Siena through edf_input = x1_external.load_18: PASS (1 files, load_18 itself on 0 files, skipped on 1 (predicted above the limit); sha256 not matching PhysioNet: none)
- **G4** mains suggestion on Siena: 50 Hz 1, 60 Hz 0, none 0
- **G5** bad-electrode rule on Siena: 0 files flagged 
- **G6** private memory peak (resident peaks, file pages included, in the CSVs): load max 1622 MB, Phase A max 1624 MB; G1 per subject max 1208 MB

Per row: `g1.csv`, `siena.csv`. Hospital records: private report in Agent/inbox only.
