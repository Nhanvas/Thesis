# archive/scaffolding — PRE-THESIS E_main pipeline. NOT part of the rlg pipeline of record.

Config-driven training scaffold (`run_main.py`, `train_pipeline.py`, `shared/`, `configs/`) from the
E_main / LTSO era, before Phase A. Superseded end-to-end by the locked rlg pipeline:
`src/dataprep/` -> `src/retrain/gae_joint.py` -> `src/ensemble_recipe.py` ->
`src/cpd_pipeline_v14.py` -> `src/szcore_eval.py`.

Checkpoints under `checkpoints/` are E5/E_main-era and do NOT load with the current GAEModel class.
Kept for provenance only. DO NOT CITE, DO NOT RUN.
