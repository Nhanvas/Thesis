# SzCORE benchmark check — esl-epfl/szcore, commit c57da2f (2026-09-06)

Verified 2026-10-08 by cloning the repository (container) and reading every
`results/*/siena.json` and `results/*/chbmit.json` (`event_results`, subject-mean, the benchmark's
official aggregate) and every `algorithms/*.yaml`. In `config/schema.json` the `datasets` field of an
algorithm is defined as "A dataset used for training the algorithm"; the out-of-sample column below
is read from that field. Numbers are copied, not recomputed.

Use: reference-sheet group K, Figure 12, Tables 12 and 16. The figure step later reads a committed
CSV made from the same files (rule 13), not this note.

### Siena

| entry (short title) | training data declared | sens | prec | F1 | FP/day | out-of-sample on Siena? |
|---|---|---|---|---|---|---|
| DeepSOZ-HEM | Physionet Siena Scalp EEG; TUH Seizure Corpus | 0.893 | 0.807 | 0.820 | 1.77 | no — trained on it |
| IctalTraceV4R69 | TUH EEG Corpus; TUH Seizure Corpus | 0.279 | 0.358 | 0.301 | 6.86 | yes |
| CA-EEGWaveNet | Physionet CHB-MIT Scalp EEG dataset; Physionet Siena Scalp EEG; TUH Seizure Corpus | 0.000 | 0.000 | 0.000 | 1.42 | no — trained on it |
| MV-AFA | CHB-MIT Scalp EEG Database; Siena Scalp EEG Database; TUH EEG Seizure Corpus | 1.000 | 0.037 | 0.071 | 274.67 | no — trained on it |
| SD2025 | Physionet Siena Scalp EEG; TUH Seizure Corpus; TUH EEG Corpus | 0.350 | 0.075 | 0.116 | 73.55 | no — trained on it |
| BrainGoBrr | TUH EEG Sz Corpus v2 | 0.129 | 0.210 | 0.047 | 6.94 | yes |
| Multi-scale XB | Physionet Siena Scalp EEG; TUH Seizure Corpus | 0.014 | 1.000 | 0.333 | 0.00 | no — trained on it |
| EEGWaveNet 2021 | Physionet CHB-MIT Scalp EEG dataset | 0.858 | 0.072 | 0.127 | 145.48 | yes |
| EventNet 2024 | TUH Seizure Corpus | 0.587 | 0.578 | 0.526 | 8.21 | yes |
| Gotman 1982 | Gotman 1982 | 0.986 | 0.036 | 0.067 | 286.05 | yes |
| Self-GNN - Tang 2021 | TUH Seizure Corpus | 0.824 | 0.151 | 0.198 | 112.50 | yes |
| Zhu Transformer 2023 | TUH Seizure Corpus | 0.674 | 0.484 | 0.479 | 15.30 | yes |
| DynaSD | Physionet CHB-MIT Scalp EEG dataset; Intracranial EEG recordings of Seizures from HUP | 0.664 | 0.126 | 0.170 | 77.74 | yes |
| SeizUnet | TUH Seizure Corpus; KU Leuven SeizeIT2 | 0.287 | 0.490 | 0.207 | 3.53 | yes |
| Velland_2025 v0.1 | TUH Seizure Corpus | 1.000 | 0.037 | 0.071 | 274.24 | yes |
| Wu Transformer | Physionet Siena Scalp EEG; TUH Seizure Corpus | 0.685 | 0.887 | 0.706 | 0.99 | no — trained on it |
| He Random-Forest | Physionet CHB-MIT Scalp EEG dataset | 0.168 | 0.302 | 0.091 | 8.08 | yes |

### CHB-MIT

| entry (short title) | training data declared | sens | prec | F1 | FP/day | out-of-sample on CHB-MIT? |
|---|---|---|---|---|---|---|
| DeepSOZ-HEM | Physionet Siena Scalp EEG; TUH Seizure Corpus | 0.000 | — | — | 0.00 | yes; no detections (precision undefined) |
| IctalTraceV4R69 | TUH EEG Corpus; TUH Seizure Corpus | 0.326 | 0.069 | 0.101 | 26.00 | yes |
| CA-EEGWaveNet | Physionet CHB-MIT Scalp EEG dataset; Physionet Siena Scalp EEG; TUH Seizure Corpus | 0.368 | 0.356 | 0.265 | 5.03 | no — trained on it |
| MV-AFA | CHB-MIT Scalp EEG Database; Siena Scalp EEG Database; TUH EEG Seizure Corpus | 0.749 | 0.463 | 0.520 | 12.83 | no — trained on it |
| SD2025 | Physionet Siena Scalp EEG; TUH Seizure Corpus; TUH EEG Corpus | 0.000 | — | — | 0.00 | yes; no detections (precision undefined) |
| BrainGoBrr | TUH EEG Sz Corpus v2 | 0.000 | — | 0.000 | 0.00 | yes; no detections (precision undefined) |
| Multi-scale XB | Physionet Siena Scalp EEG; TUH Seizure Corpus | 0.000 | — | — | 0.00 | yes; no detections (precision undefined) |
| EEGWaveNet 2021 | Physionet CHB-MIT Scalp EEG dataset | 1.000 | 0.071 | 0.128 | 113.64 | no — trained on it |
| EventNet 2024 | TUH Seizure Corpus | 0.000 | — | — | 0.00 | yes; no detections (precision undefined) |
| Gotman 1982 | Gotman 1982 | 0.913 | 0.027 | 0.051 | 237.51 | yes |
| Self-GNN - Tang 2021 | TUH Seizure Corpus | 0.000 | — | — | 0.00 | yes; no detections (precision undefined) |
| Zhu Transformer 2023 | TUH Seizure Corpus | 0.000 | — | — | 0.00 | yes; no detections (precision undefined) |
| DynaSD | Physionet CHB-MIT Scalp EEG dataset; Intracranial EEG recordings of Seizures from HUP | 0.608 | 0.199 | 0.218 | 23.21 | no — trained on it |
| SeizUnet | TUH Seizure Corpus; KU Leuven SeizeIT2 | 0.000 | — | — | 0.00 | yes; no detections (precision undefined) |
| Velland_2025 v0.1 | TUH Seizure Corpus | 1.000 | 0.024 | 0.045 | 278.99 | yes |
| Wu Transformer | Physionet Siena Scalp EEG; TUH Seizure Corpus | 0.000 | — | — | 0.00 | yes; no detections (precision undefined) |
| He Random-Forest | Physionet CHB-MIT Scalp EEG dataset | 0.995 | 0.797 | 0.851 | 4.04 | no — trained on it |


## What this changes

1. **SeizureTransformer (Wu Transformer) declares Siena as training data.** Its Siena row (0.685 @
   0.99 FP/day) is not out-of-sample. PERF_PHASE_RECORD 9.9 and the 08/10 briefing call it "trained on
   other corpora"; that is wrong. Five more Siena rows are in-sample: DeepSOZ-HEM, SD2025,
   Multi-scale XB, MV-AFA, CA-EEGWaveNet.
2. **DynaSD declares CHB-MIT as training data** (its yaml: processing hyperparameters tuned on a subset
   of CHB-MIT; detection threshold tuned on intracranial EEG from HUP). Its CHB-MIT row (0.608 @ 23.2)
   is therefore not out-of-sample; its Siena row (0.664 @ 77.7) is.
3. **On CHB-MIT, 9 of 17 entries produce no detections** (sensitivity 0, precision undefined, 0 FP/day),
   consistent with SzCORE keeping CHB-MIT in its bipolar montage. Out-of-sample CHB-MIT rows with
   detections: IctalTrace V4 0.326 @ 26.0, Gotman 1982 0.913 @ 237.5, Velland 2025 1.000 @ 279.0.
4. Out-of-sample Siena rows usable beside ours (subject-mean): DynaSD (the only unsupervised entry)
   0.664 / 0.126 / 0.170 @ 77.7; Zhu 2023 0.674 @ 15.3; EventNet 0.587 @ 8.2; Tang 2021 0.824 @ 112.5;
   SeizUnet 0.287 @ 3.5; EEGWaveNet 0.858 @ 145.5; He RF 0.168 @ 8.1; Gotman 1982 0.986 @ 286.1.
   The record's DynaSD, Zhu and EventNet values match these files exactly.
5. Caveat that travels with every row: same annotations and scoring definitions, but our own scorer
   implementation and signal path; our system was not run inside the benchmark.
