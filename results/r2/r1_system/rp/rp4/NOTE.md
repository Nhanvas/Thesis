# rp/rp4 — RP4 first run (D21-F, 12/11) — history

Missed-seizure / false-alarm analysis of the main model **before** board R170 (data without chb12_27–29; seeds 1–3 =
R1 checkpoints, seed 4 = RP1), read from `rp/rp2/scores`. Rules: `docs/FUTURE_RESEARCH_PLAN.md` §12 rows 12/11 09:40
and 10:05; reading: row 10:43. Script `src/r2_rp4.py` (sha16 `df08595b2f550d2d`), measured 279.7 s in the container.
The flagged-share part did not run (`flags/` arrived after the run). **Not report numbers**: RP4 is re-run with the same
code and rules on the rebuilt model (`results/r2/r1_system/rb/`). `flags/` (laptop export, commit `5e9ae8b`) depends on
the test data only and is reused.
