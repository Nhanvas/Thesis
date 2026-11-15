# RPS_PROBE2: stopped run (record, D27-F, 15/11)

- Notebook `notebooks/r2/RPS_PROBE2.ipynb`, clone pinned at `64de3d8875c4d92f5bbcadae5a0cfe3a084a5c86`; Kaggle CPU, 4 cores,
  4 workers; python 3.13.18, numpy 2.1.3, scipy 1.16.3, sklearn 1.6.1, pandas 2.3.3, torch 2.11.0+cpu,
  torch_geometric 2.7.0, ruptures 1.1.10 → mode exact. The author stopped it after 4,461 s. There is no output. The log
  lines below were copied from the Kaggle log the author sent.
- Before the pool started: views 16 s, gate_data 16 s, **G-data PASS** (63 files hashed = pinned R1_SMOKE hashes).
- From 121.7 s onward, every spawned pool worker died while unpickling its task:
  `AttributeError: Can't get attribute 'pool_job' on <module 'r2_rpsprobe' from '/tmp/Thesis/src/r2_rpsprobe.py'>`.
  The pool kept starting new workers and stopped printing anything after that.
- **Cause.** The notebook was pinned to `64de3d8`. That is the commit before `4da671a`, which holds the probe's own pool
  code. The clone's `src/r2_rpsprobe.py` at `64de3d8` is the single-process version and has no `pool_job`. The main
  process used the copy embedded in the notebook. The workers loaded the clone's file.
- **Not rerun.** The same mechanism explains why `RP_SERIES` was slow: its workers ran the clone's older `r2_rps.py`. See
  `docs/FUTURE_RESEARCH_PLAN.md` §12, row 15/11 16:00.
