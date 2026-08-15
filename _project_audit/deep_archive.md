# Deep scan — `F:\Study\Thesis\Code\archive`

Generated: 2026-08-13 16:45

Total files: **81**  |  Total size: **542.6KB**

## Flagged files (ten goi y cu/backup/test/draft/duplicate)

| Path | Size | Modified | Flags |
|---|---|---|---|
| cpd_history/cpd_pipeline_v10.py | 17.3KB | 2026-07-26 00:20 | v1 |
| cpd_history/cpd_pipeline_v11.py | 18.1KB | 2026-07-26 00:20 | v1 |
| cpd_history/cpd_pipeline_v12.py | 18.7KB | 2026-07-26 00:20 | v1 |
| cpd_history/cpd_pipeline_v13.py | 20.5KB | 2026-07-26 00:20 | v1 |
| cpd_history/cpd_pipeline_v2.py | 17.0KB | 2026-07-26 00:20 | v2 |
| cpd_history/cpd_pipeline_v6.py | 17.1KB | 2026-07-26 00:20 | v6 |
| cpd_history/cpd_pipeline_v7.py | 15.7KB | 2026-07-26 00:20 | v7 |
| cpd_history/cpd_pipeline_v8.py | 15.6KB | 2026-07-26 00:20 | v8 |
| cpd_history/cpd_pipeline_v9.py | 15.6KB | 2026-07-26 00:20 | v9 |
| scaffolding/test_pipeline.py | 1.9KB | 2026-07-26 00:20 | test_ |

## Danh sach day du theo sub-folder


### attribution_superseded

| File | Size | Modified | Peek |
|---|---|---|---|
| attribution_c1.py | 10.3KB | 2026-07-26 00:20 | """ \| ================================================================================ \|  attribution_c1.py  (Phase B / Stage C1) \|    Seizure channel |
| attribution_c2.py | 12.4KB | 2026-07-26 00:20 | """ \| ================================================================================ \|  attribution_c2.py  (Phase B / Stage C2) \|    Consolidate sei |
| attribution_c3.py | 8.7KB | 2026-07-26 00:20 | """ \| ================================================================================ \|  attribution_c3.py  (Phase B / Stage C3)  —  FAITHFULNESS of  |

### cpd_history

| File | Size | Modified | Peek |
|---|---|---|---|
| build_cpd_timeline.py | 5.6KB | 2026-07-26 00:20 | # src/build_cpd_timeline.py \| """ \| Reconstruct chronological score timeline from separate inter/ictal arrays. \|  \| Algorithm: \|   1. Parse summary fi |
| compute_window_metrics.py | 4.6KB | 2026-07-26 00:20 | """ \| compute_window_metrics.py — Window-level precision, recall, F1, specificity \| Uses per-subject P95 interictal threshold (fully unsupervised, no  |
| cpd_eval.py | 2.7KB | 2026-07-26 00:20 | # src/cpd_eval.py \| """ \| Change Point Detection on ensemble anomaly score timeline. \| No threshold required. Detects both upward and downward changes |
| cpd_pipeline.py | 21.5KB | 2026-07-26 00:20 | """ \| CPD Pipeline: Unsupervised Seizure Localization via Change Point Detection \|  \| Problem reframing: \|   Threshold approach: "Is window t a seizur |
| cpd_pipeline_v10.py | 17.3KB | 2026-07-26 00:20 | """ \| CPD Pipeline v10 — Multivariate Change Point Detection \| Author: Stanford/MIT Research Team (GAE & CPD for Epilepsy Research) \|  \| Changes imple |
| cpd_pipeline_v11.py | 18.1KB | 2026-07-26 00:20 | """ \| CPD Pipeline v11 — Unsupervised ROI-Guided Change Point Detection \| Author: Stanford/MIT Research Team (GAE & CPD for Epilepsy Research) \|  \| Ch |
| cpd_pipeline_v12.py | 18.7KB | 2026-07-26 00:20 | """ \| CPD Pipeline v12 (Combined)  \|  \| Theoretical Framework: \| This pipeline solves the sensitivity-specificity trade-off in seizure localization  \| |
| cpd_pipeline_v13.py | 20.5KB | 2026-07-26 00:20 | """ \| CPD Pipeline v13 (Ultimate Robust - Instant CPU Execution) — Production-Grade Master Implementation \| Author: Stanford/MIT Research Team (GAE &  |
| cpd_pipeline_v2.py | 17.0KB | 2026-07-26 00:20 | """ \| CPD Pipeline v2 — corrected: \| Fix 1: chb17 filename pattern (chb17a/b/c prefix support) \| Fix 2: Empty signal crash in run_pelt \| Fix 3: Inter- |
| cpd_pipeline_v6.py | 17.1KB | 2026-07-26 00:20 | import numpy as np \| import torch \| import torch.nn as nn \| import re \| import pandas as pd \| import ruptures as rpt \| from pathlib import Path \| from |
| cpd_pipeline_v7.py | 15.7KB | 2026-07-26 00:20 | """ \| CPD Pipeline v7 — Temporal Smoothing Implementation \| Author: Stanford/MIT Research Team (GAE & CPD for Epilepsy Research) \|  \| Changes implemen |
| cpd_pipeline_v8.py | 15.6KB | 2026-07-26 00:20 | """ \| CPD Pipeline v8 — Robust L1 Cost Implementation \| Author: Stanford/MIT Research Team (GAE & CPD for Epilepsy Research) \|  \| Changes implemented: |
| cpd_pipeline_v9.py | 15.6KB | 2026-07-26 00:20 | """ \| CPD Pipeline v9 — Kernel RBF Cost Implementation \| Author: Stanford/MIT Research Team (GAE & CPD for Epilepsy Research) \|  \| Changes implemented |
| cpd_tolerance_sweep.py | 8.6KB | 2026-07-26 00:20 | """ \| cpd_tolerance_sweep.py — Tolerance Sensitivity Analysis \| Tests ±10s, ±20s, ±30s at pen=0.3, 0.5, 1.0 \| Reads cached bidirectional gamma ensembl |

### probes_old

| File | Size | Modified | Peek |
|---|---|---|---|
| inventory_probe.py | 6.6KB | 2026-07-26 00:20 | """ \| ================================================================================ \|  inventory_probe.py  —  READ-ONLY artifact discovery for the  |
| recipe_probe.py | 8.9KB | 2026-07-26 00:20 | """ \| ================================================================================ \|  recipe_probe.py  —  READ-ONLY: lock the ensemble recipe + re |

### rejected

| File | Size | Modified | Peek |
|---|---|---|---|
| build_spli.py | 3.3KB | 2026-07-26 00:20 | # src/build_spli.py \| """ \| Build signed PLI adjacency matrices from raw EEG windows. \|  \| sPLI[i,j] = E[Im(C_ij)] / E[\|Im(C_ij)\|] \|           ∈ [-1,  |
| check_band_aec.py | 3.0KB | 2026-07-26 00:20 | # src/check_band_aec.py \| """ \| Pre-check: Does delta/gamma AEC increase during chb06 seizures? \| If yes → band-specific AEC could fix chb06 inverted  |
| check_data.py | 3.9KB | 2026-07-26 00:20 | """ \| check_data.py \| ============= \| Verify preprocessed data integrity before running any model. \| Run this before smoke test. Reports: \|   - Which  |
| check_spectral.py | 2.3KB | 2026-07-26 00:20 | """ \| check_spectral.py \| ================= \| Check whether band power features change during ictal windows \| for the subjects with low AUROC: chb14,  |
| diagnose_components.py | 6.9KB | 2026-07-26 00:20 | """ \| diagnose_components.py \| ====================== \| Diagnose whether AEC or wPLI individually carries the ictal signal. \|  \| Hypothesis: wPLI supp |
| diagnose_gamma_emg.py | 6.0KB | 2026-07-26 00:20 | """ \| diagnose_gamma_emg.py — EMG Artifact Diagnostic for Gamma AEC \| 3 checks per subject: channel power ratio, pair spatial distribution, amplitude  |
| diagnose_signal.py | 13.9KB | 2026-07-26 00:20 | """ \| diagnose_signal.py \| ================== \| Diagnose whether the signal exists in adjacency matrices BEFORE \| trying to fix the model. If adjacenc |
| eval_gamma_aec.py | 1.4KB | 2026-05-31 01:41 | # src/eval_gamma_aec.py \| import numpy as np \| from pathlib import Path \| from sklearn.metrics import roc_auc_score \|  \| DATA_DIR   = Path("data/proce |
| evaluate_full.py | 17.7KB | 2026-06-15 16:06 | """ \| Full Evaluation Script — Two-Tier Assessment \| ============================================= \| Tier 1: Window/Score-level  →  AUROC + AUPRC per  |
| graph_construction_dense_baseline.py | 7.1KB | 2026-07-26 00:20 | """ \| graph_construction.py \| ===================== \| Graph construction pipeline for one 4s EEG window. \| CAR applied before connectivity computation |
| mag_pen_grid_sweep.py | 9.1KB | 2026-07-26 00:20 | """ \| ================================================================================ \|  mag_pen_grid_sweep.py  —  Joint (min_mag_pct x pen_mult) Par |
| mag_pen_sweep.py | 8.4KB | 2026-07-26 00:20 | """ \| ================================================================================ \|  mag_pen_sweep.py  —  WEEK 3 (optimization): operating-point  |
| oversegmentation_diag.py | 11.4KB | 2026-06-27 11:52 | """ \| ================================================================================ \|  oversegmentation_diag.py  —  WEEK 3 (diagnosis): why does PE |
| topo_ensemble_eval.py | 11.1KB | 2026-07-26 00:20 | """ \| ================================================================================ \|  topo_ensemble_eval.py  (Script B2)  —  does a topology view  |
| topo_extract.py | 8.8KB | 2026-07-26 00:20 | """ \| ================================================================================ \|  topo_extract.py  (Script B1)  —  DIAGNOSTIC ONLY: does graph |
| topo_standalone_auroc.csv | 1.7KB | 2026-06-30 23:50 |  |
| verify_chb14_gamma.py | 15.1KB | 2026-07-26 00:20 | """ \| verify_chb14_gamma.py — Verify gamma AEC impact on chb14 detection \| 3 scenarios: full ensemble / no gamma / reversed gamma \| Usage: python src/ |
| verify_cpd_ictal_counts.py | 1.3KB | 2026-07-26 00:20 | # src/verify_cpd_ictal_counts.py \| import re, numpy as np \| from pathlib import Path \|  \| DATA_DIR    = Path("data/processed") \| SUMMARY_DIR = Path("p |
| verify_spli.py | 817.0B | 2026-07-26 00:20 | # verify_spli.py — chạy local sau khi build_spli.py xong \| import numpy as np \| from pathlib import Path \|  \| DATA_DIR   = Path("data/processed") \| TE |
| verify_spli_pattern.py | 2.2KB | 2026-07-26 00:20 | # src/verify_spli_pattern.py \| import numpy as np \| from pathlib import Path \|  \| DATA_DIR   = Path("data/processed") \| TEST_SUBJS = ["chb03","chb06", |

### scaffolding

| File | Size | Modified | Peek |
|---|---|---|---|
| auroc_visualizer.py | 3.9KB | 2026-07-26 00:20 | import numpy as np \| import matplotlib.pyplot as plt \| from scipy.stats import norm \|  \| # =========================================================== |
| evaluate.py | 5.0KB | 2026-07-26 00:20 | """ \| evaluate.py \| =========== \| Evaluation for one LTSO fold. Now uses node features. \| """ \|  \| import json \| import numpy as np |
| finalize_attribution.py | 7.5KB | 2026-07-26 00:20 | """ \| finalize_attribution.py — closes the attribution redesign in the record. \| Performs the 4 remaining bookkeeping actions. DRY-RUN by default; --a |
| inference_pipeline.py | 1.7KB | 2026-07-26 00:20 | # Inference pipeline. \| # Modify for your task. \|  \| import torch \|  \| from configs import ConfigReader \| from shared.services.data import Transformer |
| run_main.py | 1.9KB | 2026-07-26 00:20 | """ \| run_main.py \| =========== \| E_main experiment entry point. \|  \| Usage (from project root with venv activated): \|     python run_main.py \|  |
| test_pipeline.py | 1.9KB | 2026-07-26 00:20 | # Testing pipeline. \| # Modify for your task. \|  \| import torch \| from torch.utils.data import DataLoader \|  \| from configs import ConfigReader \| from |
| train_pipeline.py | 7.2KB | 2026-07-26 00:20 | """ \| train_pipeline.py \| ================= \| Train GAE on interictal data — E_main pipeline. \|  \| Split  : 15 subjects for training, 8 subjects held  |
| visualize_progress.py | 9.9KB | 2026-07-26 00:20 | """ \| visualize_progress.py \| ===================== \| Create 3 figures for supervisor report. \|  \| Output (saved in results/figures/): \|   fig1_prepro |

### scaffolding/checkpoints

| File | Size | Modified | Peek |
|---|---|---|---|
| .gitkeep | 0.0B | 2026-07-26 00:20 |  |

### scaffolding/checkpoints/E5_proposed_gae_seed42/fold_01

| File | Size | Modified | Peek |
|---|---|---|---|
| best_model.pt | 12.4KB | 2026-04-12 12:20 |  |

### scaffolding/checkpoints/E5_smoke_test/smoke_chb01_train_chb09_test

| File | Size | Modified | Peek |
|---|---|---|---|
| best_model.pt | 11.1KB | 2026-04-05 22:46 |  |
| model_weights.pt | 11.1KB | 2026-04-05 22:49 |  |

### scaffolding/checkpoints/E5_within_subject_smoke/smoke_chb01

| File | Size | Modified | Peek |
|---|---|---|---|
| best_model.pt | 7.9KB | 2026-04-10 19:27 |  |
| model_weights.pt | 7.9KB | 2026-04-10 19:54 |  |

### scaffolding/checkpoints/E5_within_subject_smoke_v2/smoke_chb01

| File | Size | Modified | Peek |
|---|---|---|---|
| best_model.pt | 12.4KB | 2026-04-13 10:17 |  |
| model_weights.pt | 12.4KB | 2026-04-13 10:20 |  |

### scaffolding/checkpoints/E_main

| File | Size | Modified | Peek |
|---|---|---|---|
| best_model.pt | 12.4KB | 2026-04-19 01:03 |  |

### scaffolding/configs

| File | Size | Modified | Peek |
|---|---|---|---|
| __init__.py | 111.0B | 2026-07-26 00:20 | from .config import ConfigReader, ConfigException \|  \| __all__ = [ \|     "ConfigReader", \|     "ConfigException" \| ] |
| config.py | 1.6KB | 2026-07-26 00:20 | # config.py \| import os \| import yaml \|  \|  \| class ConfigException(Exception): \|     def __init__(self, message="Config error"): \|         self.messa |
| defaults.yaml | 772.0B | 2026-07-26 00:20 | data: \|   processed_dir: "F:/Study/Thesis/Code/data/processed/" \|   splits_dir: "F:/Study/Thesis/Code/data/splits/" \|   batch_size: 32 \|   num_workers |
| experiment.yaml | 183.0B | 2026-07-26 00:20 | # Override defaults for specific experiment. \| # Modify for your task. \|  \| data: \|   batch_size: 8 \|  \| training: \|   max_epochs: 200 |
| experiment_gae.yaml | 349.0B | 2026-07-26 00:20 | # experiment_gae.yaml \| # Reference config for E_main experiment. \| # NOT loaded automatically — only when explicitly passed to ConfigReader.merge().  |

### scaffolding/shared/models

| File | Size | Modified | Peek |
|---|---|---|---|
| __init__.py | 314.0B | 2026-07-26 00:20 | from .loss_function import LossHandler \| from .metrics import MetricHandler \| from .optimization import OptimizerHandler \| from .trainer import Traine |
| logger.py | 2.0KB | 2026-07-26 00:20 | # logger.py \| # Experiment logging utilities. \|  \| import os \| import json \| import yaml \| import shutil \| from datetime import datetime |
| loss_function.py | 3.4KB | 2026-07-26 00:20 | """ \| loss_function.py \| ================ \| Graph reconstruction loss for GAE — Eq (8). \|  \| Two loss options: \|   graph_bce: Weighted BCE (Kipf & Wel |
| metrics.py | 4.4KB | 2026-07-26 00:20 | """ \| metrics.py \| ========== \| Evaluation metrics for unsupervised seizure detection. \|  \| Accuracy is intentionally excluded: \|   0.18% seizure prev |
| optimization.py | 2.2KB | 2026-07-26 00:20 | """ \| optimization.py \| =============== \| Optimizer and learning rate scheduler. \| """ \|  \| import torch \| import torch.optim as optim |
| trainer.py | 5.1KB | 2026-07-26 00:20 | """ \| trainer.py \| ========== \| Plain PyTorch training loop for GAE with node features. \|  \| Training runs for exactly max_epochs epochs (no early sto |
| visualization.py | 2.5KB | 2026-07-26 00:20 | # visualization.py \| # Plotting utilities. \| # Modify for your task. \|  \| import pandas as pd \| import matplotlib.pyplot as plt \| from pathlib import  |

### scaffolding/shared/services/data

| File | Size | Modified | Peek |
|---|---|---|---|
| __init__.py | 71.0B | 2026-07-26 00:20 | from .dataset import EEGGraphDataset \|  \| __all__ = ["EEGGraphDataset"] |
| dataset.py | 2.2KB | 2026-07-26 00:20 | """ \| dataset.py \| ========== \| Dataset for GAE training. \|  \| Node feature design (Kipf & Welling 2016 + domain extension): \|     X = concat(A_row_no |
| transforms.py | 1.7KB | 2026-07-26 00:20 | from typing import Tuple \| from abc import ABC, abstractmethod \|  \|  \| class BaseTransformer(ABC): \|     """ \|     Base transformer class. \|     Modif |

### scaffolding/shared/services/models_hub

| File | Size | Modified | Peek |
|---|---|---|---|
| __init__.py | 140.0B | 2026-07-26 00:20 | from .base import ModelManager \| from . import utils \| from .unet import UNet \|  \| __all__ = [ \|     "ModelManager", \|     "utils", \|     "UNet" |
| base.py | 1.1KB | 2026-07-26 00:20 | # base.py \| import torch \| from abc import ABC, abstractmethod \|  \|  \| class ModelManager(ABC): \|     """ \|     Base class for all models. |
| utils.py | 2.3KB | 2026-07-26 00:20 | # utils.py \| # Shared layers for models. \| # Add your reusable layers here. \|  \| import torch \| import torch.nn as nn \| import torch.nn.functional as  |

### scaffolding/shared/services/models_hub/baselines

| File | Size | Modified | Peek |
|---|---|---|---|
| __init__.py | 0.0B | 2026-07-26 00:20 |  |
| lstm_ae.py | 0.0B | 2026-07-26 00:20 |  |
| svm_baseline.py | 0.0B | 2026-07-26 00:20 |  |

### scaffolding/shared/services/models_hub/gae

| File | Size | Modified | Peek |
|---|---|---|---|
| __init__.py | 27.0B | 2026-07-26 00:20 | from .model import GAEModel |
| model.py | 2.6KB | 2026-07-26 00:20 | """ \| gae_model.py \| ============ \| Graph Autoencoder for unsupervised seizure detection — Eq (5)-(9). \|  \| Architecture: \|     Encoder: 2-layer GCNCo |

### scaffolding/shared/services/models_hub/unet

| File | Size | Modified | Peek |
|---|---|---|---|
| __init__.py | 23.0B | 2026-07-26 00:20 | from .model import UNet |
| model.py | 2.5KB | 2026-07-26 00:20 | # Example: UNet for segmentation. \| # Copy this folder, rename, and modify for your model. \| # \| # Learn more about UNet: \| # - Paper: https://arxiv.o |