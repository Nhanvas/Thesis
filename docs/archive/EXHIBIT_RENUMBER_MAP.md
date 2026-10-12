# Exhibit and section renumbering map

**Revision 2 (2026-09-25).** Maps exhibit set revision 4 (2026-09-23) to revision 5 (2026-09-25), and the
section numbers of Chapters 1 to 4 before and after the v3 restructure. The rev 3 → rev 4 map of
2026-09-23 is in the git history of this file.

## Figures, rev 4 → rev 5

| Rev 4 | Rev 5 | Subject | File |
|---|---|---|---|
| 1.1, 1.2 | unchanged | connectivity heatmaps, research framework | `fig1_2_…`, `fig1_3_…` |
| 2.1 | 2.1 | montage | `fig2_1_montage.png` |
| **A.2** | **2.2** | raw against preprocessed (moved up) | `fig2_2_raw_vs_preprocessed.png` |
| 2.2 | 2.3 | graph construction | `fig2_3_graph_construction.png` |
| 2.3 | 2.4 | pipeline | `fig2_4_pipeline.png` |
| **A.3** | **2.5** | reconstruction inversion (moved up) | `fig2_5_reconstruction_inversion.png` |
| 2.4 | 2.6 | application architecture | `fig2_6_application_architecture.png` |
| 3.1 to 3.6 | unchanged | separation, curves, detection output, operating curve, rank heatmap, application screen (pending) | `fig3_1…`, `fig3_2…`, `fig3_3…`, `fig3_5…`, `fig3_9…` |
| 4.1 | unchanged | comparison | `fig4_1_comparison.png` |
| A.1 | A.1 | seizure phases | `fig1_1_seizure_phases.png` |
| A.4 | A.2 | event scoring | `fig2_7_event_scoring.png` |
| A.5 | A.3 | detection latency | `fig3_4_detection_latency.png` |
| A.6 | A.4 | window against event | `fig3_6_window_vs_event.png` |
| A.7 | A.5 | false positive with the recording | `fig3_7_false_positive_eeg.png` |
| A.8 | A.6 | attribution on the synthetic grid | `fig3_8_attribution_synthetic.png` |
| A.9 | A.7 | diffuseness | `fig3_10_diffuseness.png` |

## Tables, rev 4 → rev 5

| Rev 4 | Rev 5 | Subject |
|---|---|---|
| 1.1, 1.2, 2.1 to 2.4, 3.1, 3.2, 4.1 | unchanged | |
| **A.11** | **3.3** | per-patient event results (moved up) |
| 3.3 | 3.4 | four trained models |
| 3.4 | 3.5 | ablations and design alternatives |
| 3.5 | 3.6 | agreement with the channel annotation |
| 3.6 | 3.7 | application detection (pending) |
| 3.7 | 3.8 | objectives and requirements |
| A.1 to A.5 | unchanged | |
| A.6 | **deleted** | task per week |
| A.7 | **deleted** | preprocessing steps |
| A.8 | A.6 | synthetic grid design |
| A.9 | A.7 | candidate corpora |
| A.10 | A.8 | model and training configuration |
| A.12 | A.9 | synthetic criteria |
| A.13 | **deleted** | annotation composition |
| A.14 | A.10 | cost profile |

## Sections, v2 → v3

**Chapter 1** (7 sections → 6): 1.1.1 + 1.1.2 → 1.1.1 · 1.1.3 → 1.1.2 · 1.2.1 to 1.2.6 unchanged ·
1.2.7 gaps → opening of 1.3 · 1.5 requirements → inside 1.3 · 1.4 goals unchanged · 1.6 timeline → 1.5 ·
1.7 framework → 1.6.

**Chapter 2** (7 sections → 6):

| v2 | v3 |
|---|---|
| 2.1.1, 2.1.2 | 2.1.1 |
| 2.2.1 | 2.1.2 |
| 2.2.2, 2.2.3 | 2.1.3 |
| 2.2.4, 2.2.5 | 2.1.4 |
| 2.2.6 | 2.1.5 |
| 2.3.1, 2.3.2 | 2.2.1 |
| 2.2.7, 2.3.3, 2.3.4 | 2.2.2 |
| 2.3.5 | 2.2.3 |
| 2.4.1 | 2.3.1 |
| 2.4.2, 2.4.3 | 2.3.2 |
| 2.5.1 | 2.4.1 |
| 2.5.2, 2.5.3 | 2.4.2 |
| 2.6.1 | 2.5.1 |
| 2.6.2, 2.6.3 | 2.5.2 |
| 2.7.1, 2.7.2, 2.7.3 | 2.6.1 |
| 2.7.4 | 2.6.2 |

**Chapter 3** (8 sections → 6): 3.1 unchanged · 3.2 → 3.2.1 · 3.3.1 to 3.3.3 → 3.2.2 · 3.4 → 3.3.1 ·
3.5 → 3.3.2 · 3.6.1, 3.6.2, 3.6.4 → 3.4.1 · 3.6.3 → 3.4.2 · 3.7.1 to 3.7.3 → 3.5.1 · 3.7.4 → 3.5.2 ·
3.8 → 3.6.

**Chapter 4** (9 sections → 5): 4.1 unchanged · 4.2, 4.3 → 4.2 · 4.4 → 4.3 · 4.5, 4.6, 4.7 → 4.4 ·
4.8, 4.9 → 4.5.

## References elsewhere that still use old numbers

The project instructions (rev. 2026-09-25) and `THESIS_OUTLINE_FINAL.md` still cite old numbers. Read
them through this map: §2.6.3 → §2.5.2; §2.2.3 → §2.1.3; §2.3.4 → §2.2.2; §2.5.1 → §2.4.1; §3.7 →
§3.5; §3.7.3 → §3.5.1; §3.7.4 → §3.5.2; Table 3.6 (application) → Table 3.7; Table 3.7 (objectives) →
Table 3.8; Chapter 4 §4.3 (directed connectivity) → §4.2; §4.5 (application tier) → §4.4; §4.6
(processing time) → §4.4. The future divergence clause of instructions §11.3 becomes: "The
normalization statistics of §2.1.3, the covariance of §2.2.2 and the per-channel baseline of §2.4.1 are
fitted on the whole recording…".
