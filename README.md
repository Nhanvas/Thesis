# Unsupervised Epileptic Seizure Temporal Localization in Scalp EEG using Graph Autoencoder and Change Point Detection

Undergraduate thesis, School of Biomedical Engineering, International University (VNU-HCM), 2026.
**Author:** Nguyen Quoc Trung Nhan (BEBEIU22184) · **Advisor:** Assoc. Prof. Ha Thi Thanh Huong

This repository holds the code, the trained models and the result files of the thesis. The report was
submitted to the faculty on 17/10/2026. The **final system** is the git tag `p3-frozen`; the review
application used in the report is the tag `szscan-frozen-v4.1` (folder `web_demo/`).

> Everything above the *History* section describes the final system. Older systems of this project
> (a PELT detector on a three-readout ensemble, the "v3.1 rebuild") are history only (section 10).

---

## 1 · The final system in one picture

```
raw EDF (18 bipolar channels, 256 Hz)
 → band-pass 0.5–60 Hz + notch (60 Hz; Siena 50 Hz), 4 s windows, per-patient channel z-score
 → per window: common average reference → wPLI + AEC graph, strongest 20 % of edges kept
 → node features (30) = adjacency row 18 + relative band powers 5 + absolute features 7
 → graph autoencoder v2 (3,964 parameters; seeds 42 / 1 / 2 / 3; seed 42 = main model)
 → per patient, per channel: Ledoit–Wolf Mahalanobis distance of the 16-d node latent → robust z
 → members: 6th / 9th / 12th largest of 18 + channel mean, each minus its ±15 min running median per file
 → percentile rank per patient, equal mean = ONE ensemble anomaly score
 → detector: 20 s smoothing, per-patient label-free alarm budget clip(q_i, 0.005, 0.02), merge 90 s
 → kernel change point localizer (rbf, 2 change points, event ± 60 s) = onset / offset
```

All settings and the data each was fitted on: report Appendix B (Table 21); machine-readable in
`results/p3c_freeze/freeze.json` and `data/models_v2/gae_v2_clean_seed*.json`.

## 2 · Headline results (as in the report)

All results are event-based (SzCORE rules) on continuous recordings, seed 42 unless marked.

| Evaluation | Result | File |
|---|---|---|
| CHB-MIT test, held-out (8 patients, 76 seizures) | 26/76, pooled sensitivity 0.342 (per-patient mean 0.508) at 22.2 FP/day | `results/e22_test_oneshot/` |
| CHB-MIT test, final system (**test-informed**) | 37/76, pooled 0.487 (per-patient mean 0.577) at 27.5 FP/day | `results/e23_test_look7/` |
| External, chb24 | 14 of 16 at 29.5 FP/day | `results/x1_external/` |
| External, Siena (14 adults, 47 seizures) | per-patient mean 0.633 at 41.0 FP/day (four seeds) | `results/x1_external/` |
| Review application, 8 test patients, no label | 33/76 (pooled 0.434) at 27.9 FP/day | `results/application_eval_v4/` |
| Channel-level explanation vs blind annotation | mean AUROC 0.547, anatomical prior 0.739 | `results/attribution_v8/` |

The final system's per-patient budget was designed after the held-out look, with information from
the test patients; the held-out result stays the main CHB-MIT estimate (report Section 2.8.2).

---

## 3 · Environment

Python **3.11.9** (the author's laptop; the autoencoder training and the original external run used Kaggle's
environment). A CPU is enough for everything except retraining.

```bash
python -m venv .venv
source .venv/bin/activate          # Windows (Git Bash): source .venv/Scripts/activate
pip install -r requirements.txt    # pinned list of the author's laptop
```

- On Linux, install the CPU build of PyTorch first to avoid the CUDA download:
  `pip install torch==2.12.0 --index-url https://download.pytorch.org/whl/cpu`, then the line above.
- **Check level 1 (section 5) needs no PyTorch:** `pip install numpy pandas matplotlib` is enough.
- Run every command **from the repository root**; scripts add their own `src/` folders to `sys.path`.
- Training of the autoencoder was done on Kaggle (GPU); GPU training is not bit-reproducible, so the
  committed checkpoints (section 4.3) are the reference.

## 4 · Data and paths

### 4.1 Public recordings (PhysioNet)

| Corpus | Used for | Source |
|---|---|---|
| CHB-MIT Scalp EEG Database 1.0.0 (cases chb01–chb24) | training, validation, test (chb01–chb23); external case chb24 | https://physionet.org/content/chbmit/1.0.0/ (DOI 10.13026/C2K01R) |
| Siena Scalp EEG Database 1.0.0 (PN00–PN17) | external validation | https://physionet.org/content/siena-scalp-eeg/1.0.0/ (DOI 10.13026/5d4a-j060) |

```bash
wget -r -N -c -np https://physionet.org/files/chbmit/1.0.0/
wget -r -N -c -np https://physionet.org/files/siena-scalp-eeg/1.0.0/
# one case only, e.g.:  wget -r -N -c -np https://physionet.org/files/chbmit/1.0.0/chb24/
```

Both downloads are large; check the size on the PhysioNet page first.

### 4.2 Where the code looks for the recordings

| Variable / argument | Meaning | Default |
|---|---|---|
| `CHBMIT_DIR` (environment variable) | folder that contains `chb01/ … chb23/` with the `.edf` files | the author's `F:/Study/Thesis/Dataset/CHB-MIT` |
| `CHBMIT_SUMMARY_DIR` (only `eval_application_events.py`) | folder with the author's `chbXX-summary.md` files | `$CHBMIT_DIR/CHB info/summary` |
| `--data DIR` (`x1_external.py`) | any folder; recordings and seizure lists are found recursively (`rglob`) | — |
| `--data_root DIR` (`retrain/train_gae_v2.py`) | folder that contains the `chbXX.npz` training files | `/kaggle/input` |

```bash
export CHBMIT_DIR=/path/to/physionet.org/files/chbmit/1.0.0
```

Diagnostic scripts of earlier stages (`app_val_op.py`, `diag_*.py`, `lab_protocol_eval.py`,
`raw_eeg_view.py`, …) still carry the author's path; they are not needed for any check below.

### 4.3 Inputs committed in the repository

| Path | What it is |
|---|---|
| `data/models_v2/gae_v2_clean_seed{42,1,2,3}.pt` + `.json` | the four autoencoders of the final system and their feature-scaling constants; sha256 in `docs/PROVENANCE_V2.md` |
| `results/p3c_freeze/freeze.json` | frozen detector settings (budget constant k, limits, smoothing, localizer) |
| `data/processed/chbXX_stats.json` | per-patient channel mean/SD of CHB-MIT (estimated **without** the annotated seizures and the 4 h after them, the one label-dependent input, report Section 2.1.3); sha256 in `docs/PROVENANCE_STATS.txt` |
| `data/summaries/chbXX-summary.txt` | CHB-MIT summary files (file list and seizure times) of chb01–chb23 |
| `results/**` | every result file a report number is read from (section 6) |

Not committed (too large, rebuilt from EDF): `data/trainset_v2/`, `data/testset_v2/` (graphs and
features, identity by sha256 in `docs/PROVENANCE_V2.md`) and score caches such as `results/p2_test/`.

---

## 5 · Reproduce, in four levels

| Level | What it shows | Needs | Runtime |
|---|---|---|---|
| 1 | every table and result figure of the report is redrawn from the committed result files and gated against the numbers of record | repository only | ~5 s (measured on a cloud CPU) |
| 2 | the final system, run from raw EDF with the committed checkpoints, reproduces the committed external results | EDF of chb24 / Siena, PyTorch | about 6 min for PN10 (18.7 h) on a laptop (measured); whole external set 29 min on Kaggle CPU (measured) |
| 3 | the CHB-MIT test results are rebuilt from EDF | EDF of the 8 test cases, PyTorch | see 5.3 (estimated, not measured) |
| 4 | the autoencoder is retrained from scratch | EDF of the 15 development cases, a GPU | ~3.0–3.8 h per seed on Kaggle GPU (measured) |

The results of each check are recorded in `docs/REPRODUCE.md`.

### 5.1 Level 1 — redraw the report exhibits (no EEG)

```bash
python src/figures_v8/make_v8_exhibits.py --out out/v8     # Tables 4, 11–17, 19, 22, 23; Figures 11, 12, 13, 16
python src/figures_v8/fig14_gallery.py   --out out/v8      # Figure 14 (from results/figures_v8_data/gallery/)
```

Each exhibit has a gate: if a value does not reproduce the number of record, the script stops with
`STOP (gate)`. A successful run ends with `ALL GATES PASSED`.
The script also draws `fig16_sens_fa.png`, which is not used in the report (comparisons are given as
Table 18).

### 5.2 Level 2 — run the final system on new recordings (external validation)

`src/x1_external.py` is the self-contained path from raw EDF to scored events. It uses label-free
z-score statistics (every tenth window of the whole recording), the committed checkpoints and
`freeze.json`; labels are read only to score.

```bash
python src/x1_external.py inventory --data /path/to/recordings          # lists files and parsed seizures, scores nothing
python src/x1_external.py run --data /path/to/recordings --subjects chb24 PN00 --procs 2
python src/x1_external.py report                                          # rewrites results/x1_external/SUMMARY.md
```

- `run` skips a subject whose `results/x1_external/rows_<subject>.csv` already exists. To rerun a
  committed subject, move its `rows_` and `errors_` files out first, then compare with `git diff`.
- `gates` (run once before the original external run) needs caches that are not committed
  (`data/testset_v2/chb03.npz`, `results/p2_test/chb03.npz`); the committed `GATES_OK` records that it passed.
- On Windows, the Siena seizure-list parser copied from `epilepsy2bids` raises `OverflowError`
  in `time.mktime` (a year-1900 date); run it on Linux or through a wrapper that replaces
  `time.mktime` by time-of-day arithmetic (see `docs/REPRODUCE.md`).
- Memory: about 1.5 GB per worker on the largest Siena files; use `--procs 2` on a 16 GB laptop.

### 5.3 Level 3 — rebuild the CHB-MIT test results

The scripts that produced the test results, in order (each one documents its gates in its header):

```bash
python src/c1t_build_testset.py                                   # EDF → data/testset_v2/*.npz (needs CHBMIT_DIR, data/processed/*_stats.json)
python src/p2_test_dump.py                                        # 4 seeds → results/p2_test/*.npz (per-channel distances)
python src/e22_test_oneshot.py --confirm-look-6 --localizer kernel1d   # held-out evaluation → results/e22_test_oneshot/
python src/p2_test_bootstrap.py                                   # patient bootstrap → results/e22_test_oneshot/BOOTSTRAP.md
python src/e23_test_look7.py --confirm-look-7                      # final system → results/e23_test_look7/
```

These are the original one-time runs. Their built-in reproduction gates compare with score caches
of earlier stages that are not in the repository (for example `results/e9_test_oneshot/scores/`),
so on a clean clone they stop at the gate. A clean-clone rebuild of the test set has not been done
yet; its status is kept in `docs/REPRODUCE.md`.

### 5.4 Level 4 — retrain the autoencoder

```bash
python src/c1b_build_trainset.py                                   # EDF of the 15 development cases → data/trainset_v2/*.npz (test cases refused)
python src/retrain/train_gae_v2.py --variant clean --seed 42 --data_root data/trainset_v2 --out_dir out/gae_v2
```

Adam 1e-3, cosine schedule, 200 epochs, batch 32, final epoch kept; validation loss on chb10, chb11,
chb22. Seed 42 took 10,824 s on Kaggle GPU (`elapsed_s` in `data/models_v2/gae_v2_clean_seed42.json`).
CPU training time has not been measured.

### 5.5 How the settings were chosen (development chain, 15 development patients)

| Order | Script | Output | Decision it supported |
|---|---|---|---|
| 1 | `src/p2_dump_seeds23.py` (+ earlier dumps E8/E14/E15) | node latents and distances, 4 seeds | — |
| 2 | `src/e16_recording_baseline.py` (+ `src/e21_fine_grid.py`) | `results/e16_recording_baseline/`, `results/e21_fine_grid/` | per-file baselines not adopted; ±15 min level-only drift correction (arm e) adopted |
| 3 | `src/e17b_latent_family.py` | `results/e17b_latent_family/` | ensemble of four spatial scales |
| 4 | `src/e18_cpd_localizer.py` | `results/e18_cpd_localizer/` | kernel change point localizer |
| 5 | `src/p3_anatomy.py` | `results/p3_anatomy/` | failure anatomy (also reads test labels: disclosed) |
| 6 | `src/p3_levers.py` | `results/p3_levers/` | budget constant k |
| 7 | `src/p3c_freeze.py` | `results/p3c_freeze/freeze.json` | frozen detector and localizer |

Every arm that was tried is listed in `results/p2_ledger.csv` (its `verdict` column is the gate of
that step, not the final choice). The reasons and numbers of each step: `docs/PERF_PHASE_RECORD.md`.
Shared code: `src/p2_scalars.py` (score and detector), `src/szcore_eval.py` (SzCORE scoring with
`timescoring`).

---

## 6 · Report exhibit → result file → command

| Report | Result file(s) | Command |
|---|---|---|
| Table 4 (hours, seizures) | `data/summaries/`, `results/p3_anatomy/labelfree.csv` | level 1 (`table04_split_totals`) |
| Table 6, 9, 10 (development) | `docs/PERF_PHASE_RECORD.md`, `results/p2_ledger.csv`, step folders of 5.5 | written from these files; claim-by-claim sources in `docs/writing/CLAIM_AUDIT_v8.md` |
| Table 11 | `results/e22_test_oneshot/`, `results/e23_test_look7/` (`summary_per_seed.csv`, `BOOTSTRAP.md`) | level 1 (`table11_test`) |
| Table 12, 22 | `results/e22_test_oneshot/per_subject_seed.csv`, `results/e23_test_look7/per_subject_seed.csv` | level 1 (`table12_per_patient`, `appD1_test_seeds`) |
| Table 13, Figure 13 | `results/p3c_freeze/errors.csv`, `results/e22_test_oneshot/errors.csv`, `results/e23_test_look7/errors.csv`, `results/x1_external/errors_*.csv` | level 1 (`table13_boundaries`, `fig13_boundaries`) |
| Table 14, 15, 23 | `results/x1_external/rows_*.csv` | level 1 (`table14_external`, `table15_siena`, `appD2_siena_seeds`, `appD3_chb24_seeds`); level 2 reruns them |
| Table 16, 24 | `results/attribution_v8/` (labels: `results/attribution_v7/labels/source/`) | level 1 (`table16_channel`); `python src/attribution_v8.py` |
| Table 17 | `results/application_eval_v4/per_subject.csv` | level 1 (`table17_application`); `src/eval_application_events.py` |
| Table 18 | `src/figures_v8/comparison_rows.csv` (benchmark `esl-epfl/szcore`, commit c57da2f) + this work from `results/x1_external/` | written from these files |
| Table 19 | `data/summaries/`, `results/p3_anatomy/labelfree.csv` | level 1 (`appA1_chbmit_accounting`) |
| Table 20 | `results/x1_external/rows_*.csv` (`hours`) + PhysioNet subject table | written from these files |
| Table 21 | `results/p3c_freeze/freeze.json`, `data/models_v2/gae_v2_clean_seed*.json` | — |
| Table 25 | `results/t1_demo/timing.csv`, `results/t1_demo/TIMING.md` | `src/t1_demo_gate.py` (application timing on chb16) |
| Figure 11 | `results/diagnostics/density_frobenius_v2/` | level 1 (`fig11_sparsification`) |
| Figure 12 | `results/figures_v8_data/perseizure_final.csv` | level 1 (`fig12_duration`) |
| Figure 14 | `results/figures_v8_data/gallery/{a,b,c,d}.npz` (written from EDF by `src/figures_v8/export_v8_data.py`) | `src/figures_v8/fig14_gallery.py` |
| Figure 16 | `results/p3_anatomy/seizures.csv` | level 1 (`fig17_budget_needed.png`) |
| Figure 8 (drift correction) | drawn from development score caches | script to be added (`docs/REPRODUCE.md`) |
| Figures 1, 2, 5, 7 | illustrations drawn from raw EEG of validation cases | earlier illustration scripts in `src/figures/`, `src/dataprep/plot_raw_vs_preprocessed.py` |
| Figures 3, 4, 6, 9, 10, 15 | diagrams and application screenshots | not code-generated |
| Tables 1–3, 5, 7, 8 | literature, requirements, timeline, decision matrices | text |

## 7 · Review application (SzScan)

`web_demo/` is a local prototype: FastAPI backend, browser frontend, local database. It recomputes
the final system from the raw EDF of a patient and never reads seizure labels at run time (enforced by
`web_demo/backend/tests/test_guards.py`). Build of record: tag `szscan-frozen-v4.1`. Setup and rules:
`web_demo/CLAUDE.md`, `web_demo/SZSCAN_SPEC_v5.md`. Measured processing time: median 21.68 s per hour of
EEG on a laptop CPU (`results/t1_demo/TIMING.md`).

## 8 · Repository map (final system)

```
src/                      final-system code (flat; run as python src/<name>.py from the root)
  c1b_build_trainset.py · c1t_build_testset.py      EDF → graphs and features (v2 signal path)
  retrain/train_gae_v2.py · retrain/gae_joint.py    autoencoder
  p2_scalars.py · e16_* · e17b_* · e18_* · p3_*      score, detector, localizer, design steps
  e22_test_oneshot.py · e23_test_look7.py           test evaluations
  x1_external.py                                    external validation (raw EDF → events)
  attribution_v8.py                                 channel-level explanation
  szcore_eval.py                                    SzCORE event scoring (timescoring)
  figures_v8/                                       report exhibits (level 1)
  dataprep/                                         preprocessing, graph construction, features
data/models_v2/           final checkpoints        data/processed/   z-score statistics
data/summaries/           CHB-MIT summary files
results/                  result files (section 6); results/history_superseded/ = do not cite
docs/                     PERF_PHASE_RECORD.md (every number and decision), PROVENANCE_V2.md,
                          ATTRIBUTION_SPEC.md, REPRODUCE.md, STATUS_BOARD.md
web_demo/                 review application
archive/                  superseded code and files
```

## 9 · Integrity notes

- The test set was scored once for the held-out system and once for the final system; the final
  system is labeled test-informed. External sets were scored once, with nothing changed.
- The CHB-MIT z-score statistics exclude annotated seizures (the only label-dependent input); the
  external validation and the application use label-free statistics. The effect on the test set was
  measured: 33 instead of 37 of 76 seizures (report Section 3.6).
- Precision, F1 and false alarms per day come from the scorer's counts; every reported number is read
  from a committed result file.
- Scoring uses this project's implementation of the SzCORE rules (`src/szcore_eval.py`, `timescoring`).

---

## 10 · History

Earlier stages of the project, kept for provenance only. **None of their numbers are results of the
thesis.**

- **Earlier systems (until 2026-09):** graph autoencoder v1 (`data/models_retrain/gae_joint_seed*.pt`)
  with a PELT change point detector (`src/cpd_pipeline_v14.py`, `src/ensemble_recipe.py`, `src/retrain/`).
  The baseline used in the report is its equal-weight ensemble of reconstruction error, graph-level
  latent distance and gamma-band AEC (report Table 9, first row); an intermediate "v3.1 rebuild" used an
  LSTM temporal readout instead of the latent distance. Both were replaced because the v1 node features
  removed amplitude and spectral shape, and because PELT also alarms on falling changes (report Table 7).
- **Offline protocol:** an earlier evaluation rebuilt each timeline from the annotations; it is not
  used for any result (report Section 2.8.2).
- The previous README (describing that system) is in the git history before the R1 commit
  (`git show 7cd0446:README.md`). Superseded result folders: `results/history_superseded/`,
  `results/retrain_v3p1/`, `results/attribution_v5/`; superseded documents: `docs/archive/`.
