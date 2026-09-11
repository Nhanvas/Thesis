# Figure and Table Phase — Closeout

Written at the end of the session that produced the report's figures, tables and captions. Its purpose
is to make that session disposable: everything decided in it is either already in a committed file, or
recorded below.

---

# 1 · What exists, and where

Nothing below needs to be rebuilt, re-verified or re-derived. All of it is committed.

| What | Where |
|---|---|
| Every number in the report | `docs/VERIFIED_NUMBERS.md` |
| Corrections that override the planning documents | `docs/LOCKED_DOCS_ADDENDUM.md` |
| Twenty-five finished figures | `figures/figNN_MM_slug.png` |
| Every table for Chapters 1–4 and the appendices | `tables/tables_ch1.md` … `tables_ch4.md`, `tables_appendix.md` |
| The four emitted data tables | `tables/csv/` |
| The final caption for every exhibit | `docs/CAPTIONS.md` |
| Drawing specs for the ten hand-drawn figures | `docs/HANDDRAWN_FIGURES_SPEC.md` + `docs/HANDDRAWN_SPEC_ADDENDUM.md` |
| Rules and per-chapter briefs for the five writing accounts | `docs/CHAPTER_WRITING_BRIEF.md` |
| What changed since that brief was written | `docs/WRITING_PHASE_ADDENDUM.md` |
| The running-example recording and how it was chosen | `docs/RUNNING_EXAMPLE.md` |
| Timeline composition across the held-out patients | `results/diagnostics/timeline_composition.csv` |
| Every round of figure work, in order | `docs/FIGURE_ROUND2.md` … `FIGURE_ROUND9.md` |

**The two documents a new session should read first** are `docs/WRITING_PHASE_ADDENDUM.md` and
`docs/CAPTIONS.md`. Between them they carry every decision that would otherwise have to be
reconstructed from a transcript.

---

# 2 · Five findings that changed the report

Each is now in a committed file, listed here so none is mistaken for a detail.

**The reconstructed timeline is more than half substituted.** Artifact rejection removes background
windows without recording their positions. Rebuilding a timeline shifts the surviving scores and, once
the stored array is exhausted, fills the rest by resampling. Across the eight held-out patients the
substituted share averages **53.9 percent**, range **40.0 to 66.9**. The false-alarm rate is measured
on those timelines and the direction of the resulting bias is not established. This needs its own
paragraph in the limitations, and it is also the reason the application recomputes rather than replays.

**The three running-example figures are recomputed, and the recomputation was validated.** Because the
stored arrays cannot support a time axis, Figures 2.10, 3.4 and 3.10 recompute scores on the continuous
recording with every window retained, using the study's fitted parameters. The gate was a correlation
of at least 0.99 against the committed ictal scores; it returned **0.999861**. Those three figures are
not the source of any reported number and their captions say so.

**The channel annotation was generated automatically, and is not circular.** A language model read
rendered segments of the raw recordings. It read the recordings and the summary timings only, never the
model's own output. It was not blind and has not been clinically reviewed. Every result scored against
it is provisional, and the source file's claim of blindness — which cited a section that does not
exist — was corrected.

**Five comparator papers were read from source, and one of them is the comparison that carries Chapter
4.** Ali et al. 2024 evaluates the same corpus, at event level, across patients, and reports a
false-alarm rate: 0.726 sensitivity at 127.7 false alarms per day, and 0.753 at 115.0. Against those,
this system produces four to five times fewer false alarms at a sensitivity about eleven points lower,
without using any label. That comparison needs no caveat about differing datasets, which is what makes
it worth making.

**chb17 does not support the decision-limited grouping** that earlier project material asserts. Figure
3.8 places it at 0.782 discrimination and 0.207 event F1, just below both reference lines, in the same
quadrant as the representation-limited patients. Chapter 4 may group chb16 alone or call chb17
marginal, but must not assert a grouping the figure contradicts.

---

# 3 · Open items

## 3.1 Table 2.1 — three corpus rows

Citations are settled. **The table's cells are not**: it needs subjects, recorded hours, seizures,
channels, sampling rate and annotation type for each corpus, and none of that comes from a DOI.

| Corpus | DOI |
|---|---|
| Siena Scalp EEG | 10.13026/5d4a-j060 |
| Helsinki neonatal | 10.5281/zenodo.2547147 |
| TUH Seizure Corpus | 10.3389/fninf.2018.00083 |

Open each dataset page, copy the description, fill the cells from it. **No cell may be filled from
recollection** — a citation supplied from memory was rejected once in this project and was wrong.

Consider dropping the Helsinki row. It is neonatal data with a different montage and a different task,
and it does not strengthen the argument for the corpus that was chosen.

## 3.2 Ten hand-drawn figures

Fig 1.3, 1.4, 1.5, 2.1, 2.6, 2.7, 2.11, 2.12, 2.13, 2.14. Specs are written; captions are written.
Review them in two batches of four and six rather than all at once.

Three values are locked and must be checked on delivery: Fig 2.6 carries **3,285** parameters, Fig 2.7
shows **three** branches and never a recurrent one, and Fig 2.13 carries the measured substitution
figures without any claim about the direction of the bias.

## 3.3 One reproducibility line for the appendix

Four figure scripts hard-code the dataset directory as an absolute path near the top of the file:
`fig1_1_seizure_phases.py`, `fig2_10_changepoint_detection.py`, `fig3_4_detection_output.py`,
`fig3_10_false_positive_eeg.py`. Anyone reproducing the figures edits four constants. Not worth
rebuilding now, but the appendix must say so, or the report's reproducibility claim has a hole in it.

## 3.4 One unfinished check

`src/figures/fig2_5_sparsification_rules.py` did not match the data-source scan run across the figure
scripts. Confirm what it reads:
`grep -n "processed\|npy\|density_frobenius" src/figures/fig2_5_sparsification_rules.py`

## 3.5 Waiting on the application

Table 2.11's stage boundaries, Table 3.11, Table 3.12's application row, and Figures 3.16 to 3.18.

## 3.6 One caption that cannot be written from the record

Figure 2.8 predates the caption sheet and its axes are not described anywhere in the exhibit list. The
Chapter 2 writer describes it from the figure itself and must not accept a guessed description.

---

# 4 · Two repository hazards

**The figure ignore rule has hidden files twice.** `/figures/*` with `!/figures/*.png` admits only
root-level PNGs. The qualitative tables landed in `figures/tables/` and were invisible; a packaging
archive sat in `figures/` unnoticed. `figures/drawio_sources/` now has an explicit exception. Run
`git status --ignored --short figures/` after any round that writes there.

**`figures/archive/` is not tracked.** Six superseded figures exist only on the local disk. The
project's rule is to archive rather than delete, and that rule is currently guaranteed by one hard
drive. Copying the directory somewhere outside the repository once would close it.

---

# 5 · What the next session inherits

The figures, tables and captions are finished and need no further work from anyone except the ten
hand-drawn diagrams. The next phase is two jobs that do not depend on each other: reviewing the five
chapter drafts as they arrive, and building the application.

For review, the governing documents are `docs/CHAPTER_REVIEW_PROTOCOL.md`, `docs/RUBRIC_TRACKING.md`,
and the authority chain in `docs/WRITING_PHASE_ADDENDUM.md` Part A. The single most common failure to
watch for is a chapter quoting a number that is neither in `docs/VERIFIED_NUMBERS.md` nor in its own
table file.

For the application, the governing documents are the `web_demo/` spec set, and the finding in §2 above
about the substituted timeline is the measured justification for its architecture.
