# Exhibit Set — Final

The authoritative list of what the report contains.

**Revision 2.** Two changes since revision 1: Figure 2.13 was cut after its evidence was found to be
better served by a table, and the whole exhibit set was renumbered to close the gaps the P3 cuts left
behind. The numbers in this file are final. `docs/CAPTIONS.md` revision 3 carries the caption for every
exhibit under these numbers, together with the old-to-new map.

A decision record is not edited after the fact. `docs/EXHIBIT_TRIAGE.md` stays as written; this file
records what the set became.

---

# What changed since revision 1

| Change | Reason |
|---|---|
| **Figure 2.13 cut** | The evidence it carried is eight per-patient measurements, which a table reports more precisely than a diagram of one patient. It became Table A.3, where the figures are checkable per patient instead of quoted as a summary pair. |
| **Table A.3 added** | Holds what Figure 2.13 carried, including the mandatory sentence about the direction of the bias. |
| **Table 1.4 added** | The timeline follows the reference thesis, which presents a schedule as a calendar grid plus a task table. Table 1.3 is the grid, Table 1.4 the week-by-week detail. |
| **Everything renumbered** | The cuts left gaps at 1.3, 2.2, 2.5, 2.7, 2.9, 2.10, 2.11, 3.2, 3.7, 3.9, 3.12, 3.14 and at Tables 2.2, 2.5, 2.11, 2.12, 3.1, 3.7, 3.11, A.3, A.7. Figures and tables now run consecutively within each chapter, in order of first reference. Image filenames were renamed to match. |

---

# Figures

Twenty-one exist. One waits on the application.

| Number | Filename | Source |
|---|---|---|
| 1.1 | `fig1_1_seizure_phases.png` | code |
| 1.2 | `fig1_2_connectivity_heatmaps.png` | code |
| 1.3 | `fig1_3_research_framework.png` | hand |
| 2.1 | `fig2_1_montage.png` | hand |
| 2.2 | `fig2_2_raw_vs_preprocessed.png` | code |
| 2.3 | `fig2_3_graph_construction.png` | code |
| 2.4 | `fig2_4_pipeline.png` | hand |
| 2.5 | `fig2_5_reconstruction_inversion.png` | code |
| 2.6 | `fig2_6_application_architecture.png` | code |
| 2.7 | `fig2_7_event_scoring.png` | code |
| 3.1 | `fig3_1_separation.png` | code |
| 3.2 | `fig3_2_roc_pr_curves.png` | code |
| 3.3 | `fig3_3_detection_output.png` | code |
| 3.4 | `fig3_4_detection_latency.png` | code |
| 3.5 | `fig3_5_operating_curve.png` | code |
| 3.6 | `fig3_6_window_vs_event.png` | code |
| 3.7 | `fig3_7_false_positive_eeg.png` | code |
| 3.8 | `fig3_8_attribution_synthetic.png` | code |
| 3.9 | `fig3_9_attribution_rank_heatmap.png` | code |
| 3.10 | `fig3_10_diffuseness.png` | code |
| **3.11** | **pending the application build** | |
| 4.1 | `fig4_1_comparison.png` | code |

Eighteen are generated in `src/figures/` and each carries a numeric self-check against
`docs/VERIFIED_NUMBERS.md`, stopping rather than drawing a value it cannot confirm. Three are drawn by
hand: 1.3, 2.1 and 2.4.

---

# Tables

Twenty-nine, of which two wait on the application or on the finished chapters.

| Chapter | Tables |
|---|---|
| 1 | 1.1 comparison · 1.2 requirements · 1.3 timeline grid · 1.4 weekly task detail |
| 2 | 2.1 corpora · 2.2 patient split · 2.3 preprocessing · 2.4 sparsification matrix · 2.5 model configuration · 2.6 detection matrix · 2.7 synthetic grid · 2.8 deployment matrix |
| 3 | 3.1 window discrimination · 3.2 operating points · 3.3 per-patient event · 3.4 four models · 3.5 alternatives · 3.6 synthetic criteria · 3.7 attribution agreement · 3.8 annotation similarity · 3.9 objectives and requirements |
| 4 | 4.1 comparison · 4.2 cost profile |
| Appendix | A.1 corpus metadata · A.2 channel annotation · A.3 timeline composition · A.4 channel concentration · A.5 software versions · A.6 pre-registration index |

Table 2.1's two non-corpus rows are filled from the Siena and TUH source papers. Table 3.9 is written
last, from the finished chapters. Table A.3 is new and its body is in this file's last section.

---

# Archived

Eleven figures and eleven tables were removed across the triage and P3. The figures are in
`figures/archive/` with the reason for each in its README; the tables' content, and what the prose must
now carry in its place, is at the end of `docs/CAPTIONS.md`.

Archived, not deleted. A cut can be reversed, and re-running a generator puts its figure back at the
root of `figures/`.

---

# Still open

**The generator scripts still write the old filenames.** Renaming the images did not change the output
paths inside `src/figures/`, so re-running any generator recreates a file under its old name beside the
new one. Fifteen lines need editing, in: `attribution_figures.py` (four), `fig1_1_seizure_phases.py`,
`fig1_2_connectivity_heatmaps.py`, `fig2_12_and_2_13_application.py` (two, and the second output should
be dropped since Figure 2.13 is cut), `fig2_14_event_scoring.py`, `fig2_4_graph_construction.py`,
`fig3_4_detection_output.py`, `fig3_8_window_vs_event.py`, `fig3_10_false_positive_eeg.py`,
`fig3_15_diffuseness.py`, `plot_event_level.py`, `plot_latency.py`,
`plot_reconstruction_inversion.py`, `plot_separation.py`, `plot_window_level.py`. The script filenames
themselves may keep their old numbers; only the output path matters.

**The five table files still carry the old numbers.** `tables/tables_ch1.md` through `tables_ch4.md` and
`tables_appendix.md` need the same renumbering, the cut tables removed, and Tables 1.4 and A.3 added.
One pass, with the files open.

**Table 3.9 and Figure 3.11** wait on the application build.

**Two values are recorded only in `docs/RESULTS_OF_RECORD_phaseB.md` and not in
`docs/VERIFIED_NUMBERS.md`:** the slope-filter window separation, 0.918 against 0.823, and its seed-42
event gain of 0.023 against losses of 0.039 to 0.065 and a sensitivity drop of 0.133 under the other
three models. Chapter 4 cites them. The results of record is the higher authority, so nothing is wrong;
adding them to the verified record would save the next reader the search.

---

# Table A.3 — body

Read from `results/diagnostics/timeline_composition.csv`. The last column is the fraction of each
reconstructed timeline that carries a resampled rather than a measured score.

| Patient | Timeline positions | Stored scores | Windows removed | Removed | Array exhausted at | Substituted |
|---|---|---|---|---|---|---|
| chb03 | 30,395 | 17,204 | 13,191 | 43.4% | 58.1% | 49.4% |
| chb06 | 47,523 | 19,826 | 27,697 | 58.3% | 43.7% | 66.9% |
| chb13 | 25,224 | 12,452 | 12,772 | 50.6% | 41.9% | 57.6% |
| chb14 | 20,651 | 13,983 | 6,668 | 32.3% | 70.7% | 40.0% |
| chb15 | 27,374 | 17,026 | 10,348 | 37.8% | 59.9% | 51.3% |
| chb16 | 13,530 | 6,428 | 7,102 | 52.5% | 37.6% | 62.3% |
| chb17 | 18,310 | 9,304 | 9,006 | 49.2% | 52.4% | 50.4% |
| chb18 | 29,668 | 14,853 | 14,815 | 49.9% | 46.3% | 53.4% |
| **Mean** | | | | **46.8%** | **51.3%** | **53.9%** |

*Source: `results/diagnostics/timeline_composition.csv`.*

The substituted fraction averages 53.9% and ranges from 40.0% for chb14 to 66.9% for chb06, which are
the two figures quoted in the text. The caption is in `docs/CAPTIONS.md` and carries the mandatory
sentence: the false-alarm rate is measured on these timelines, and the direction of the resulting bias
is not established.
