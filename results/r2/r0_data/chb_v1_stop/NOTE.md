# R0_CHB version 1 — stopped (07/11/2026, r2_core sha 7191ad11) — record of the stop, not the R0 result

Stopped after 94.5 min at chb07: the comparison code raised `KeyError` because the earlier `chb07.npz` has no
`skipped_files` entry. G-stats chb06 / chb07 and G-feat chb06 passed before the stop (`gates.json`). No finished job
was kept. Fixed in sha 01c068f8 (plan §12 07/11 06:10); the R0 result is `results/r2/r0_data/chb/` from version 2.
