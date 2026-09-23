# Exhibit set — figures and tables of the report

**Revision 4 (2026-09-23).** Rebuilt after the page cut of 2026-09-23, which brought the body from 59
pages to about 47 against the template's 50-page limit. Revision 3 is superseded; the old number of
every exhibit that moved is in `EXHIBIT_RENUMBER_MAP.md`.

Counts: **22 figures** (13 in the body, one of them pending the application; 9 in the appendix) and
**28 tables** (14 in the body, one of them pending the application; 14 in the appendix).

Captions: `tables/CAPTIONS.md` revision 9, which is copied verbatim from the finished chapters.

## Figures

| # | Subject | File | Chapter |
|---|---|---|---|
| 1.1 | Mean connectivity, background against seizure | `fig1_2_connectivity_heatmaps.png` | 1 |
| 1.2 | Research framework | `fig1_3_research_framework.png` | 1 |
| 2.1 | The eighteen bipolar derivations | `fig2_1_montage.png` | 2 |
| 2.2 | Graph construction from one window | `fig2_3_graph_construction.png` | 2 |
| 2.3 | The complete processing pipeline | `fig2_4_pipeline.png` | 2 |
| 2.4 | Architecture of the review application | `fig2_6_application_architecture.png` | 2 |
| 3.1 | Separation under the two sparsification rules | `fig3_1_separation.png` | 3 |
| 3.2 | ROC and precision-recall curves | `fig3_2_roc_pr_curves.png` | 3 |
| 3.3 | Detection output on one recording | `fig3_3_detection_output.png` | 3 |
| 3.4 | Sensitivity against false alarms across the grid | `fig3_5_operating_curve.png` | 3 |
| 3.5 | Per-seizure channel ranking | `fig3_9_attribution_rank_heatmap.png` | 3 (place 4.0 in wide) |
| 3.6 | Application screen | **PENDING BUILD** | 3 |
| 4.1 | Trade-off curve against published results | `fig4_1_comparison.png` | 4 |
| A.1 | Phases of the EEG signal around a seizure | `fig1_1_seizure_phases.png` | appendix |
| A.2 | One segment before and after preprocessing | `fig2_2_raw_vs_preprocessed.png` | appendix |
| A.3 | Reconstruction readout on two validation patients | `fig2_5_reconstruction_inversion.png` | appendix |
| A.4 | Event-based scoring convention | `fig2_7_event_scoring.png` | appendix |
| A.5 | Detection latency | `fig3_4_detection_latency.png` | appendix |
| A.6 | Window discrimination against event F1 | `fig3_6_window_vs_event.png` | appendix |
| A.7 | One false positive with the recording | `fig3_7_false_positive_eeg.png` | appendix |
| A.8 | Attribution on the synthetic grid | `fig3_8_attribution_synthetic.png` | appendix |
| A.9 | Diffuseness against injected channels | `fig3_10_diffuseness.png` | appendix |

`figures/` holds exactly these 21 PNGs; Figure 3.6 is the twenty-second exhibit and does not exist yet.

## Tables

| # | Subject | Chapter |
|---|---|---|
| 1.1 | Design requirements and targets | 1 |
| 1.2 | Thesis timeline | 1 |
| 2.1 | Assignment of patients to the three sets | 2 |
| 2.2 | Decision matrix, edge sparsification | 2 |
| 2.3 | Decision matrix, detection stage | 2 |
| 2.4 | Decision matrix, deployment strategy | 2 |
| 3.1 | Window-level discrimination per patient | 3 |
| 3.2 | Event-level results at each operating point | 3 |
| 3.3 | Results across four trained models | 3 |
| 3.4 | Component ablations and design alternatives | 3 |
| 3.5 | Agreement with the channel annotation | 3 |
| 3.6 | Detection of the application against the annotation | **PENDING BUILD**, 3 |
| 3.7 | Objectives and design requirements achieved | 3 |
| 4.1 | Comparison with published work | 4 |
| A.1 | Corpus metadata for all 23 patients | appendix |
| A.2 | Channel annotation for all 76 test seizures, with the model's ranking | appendix |
| A.3 | Composition of the reconstructed evaluation timeline | appendix |
| A.4 | Concentration of the top-ranked channel against a random null | appendix |
| A.5 | Software and library versions | appendix |
| A.6 | Specific task carried out in each week | appendix |
| A.7 | Preprocessing steps and their parameters | appendix |
| A.8 | Design of the synthetic validation grid | appendix |
| A.9 | Candidate public scalp EEG seizure corpora | appendix |
| A.10 | Model and training configuration | appendix |
| A.11 | Event-level performance per test patient | appendix |
| A.12 | Synthetic validation criteria and outcomes | appendix |
| A.13 | Composition of the channel annotation | appendix |
| A.14 | Computational and deployment cost profile | appendix |

## Cut, not moved

The old Table 1.1 (representative seizure detection approaches) was removed: Table 4.1 carries the same
studies with this work added, and §1.2 makes the same point in two paragraphs. The old Table A.6
(pre-registration index) was removed on 2026-09-22, because the report presents results rather than the
internal process.
