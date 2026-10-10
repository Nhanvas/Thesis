# Archived: the demo backend of the earlier system (V1, `rlg` + PELT)

Archived 2026-10-10 when the demo was rebuilt on the final thesis system (tag `p3-frozen`,
`docs/DEMO_REBUILD_BRIEF.md`). Kept for the record, never imported by the live app.

- the V1 pipeline itself stays in git history (`git show f37a7b1:web_demo/backend/pipeline_demo.py`; recon + graph-mean latent +
  gamma-AEC, equal weights, PELT at a fixed operating point).
- `backfill_*.py`, `measure_stage_timing.py` — one-off maintenance scripts written against the V1
  pipeline's functions; they do not run against the rebuilt pipeline.
- `tests/test_signal_loss_v3.py` — tests of the V1 pipeline (App v3 signal-loss rule).
