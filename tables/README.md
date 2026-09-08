# Tables

Every table the report needs, split by chapter so five accounts can write in parallel without
reading past tables that are not theirs. `docs/VERIFIED_NUMBERS.md` is the authority for every
number in every file below; `docs/LOCKED_DOCS_ADDENDUM.md` where it supersedes the exhibit list;
`FIGURES_TABLES_LIST.md` for what each table must contain.

This directory replaces the single `docs/TABLES_PACK.md` (moved to `docs/archive/` by
docs/FIGURE_ROUND6.md §4) and the CSV outputs formerly under `results/report_tables/` (moved to
`tables/csv/` by the same round).

## Where each table lives

| File | Tables |
|---|---|
| `tables/tables_ch2.md` | 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.9, 2.12 |
| `tables/tables_ch3.md` | 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9, 3.10 |
| `tables/tables_ch4.md` | 4.1, 1.1, the Figure 4.1 plotting note |
| `tables/tables_appendix.md` | A.1, A.2, A.3, A.4, A.5, A.6, A.7 |

Each of the four files above repeats the rules section (decimal convention, no-blank-cells rule,
source-line requirement) in full at its own top, so a writer opening one file does not have to
find another to know the conventions.

## `tables/csv/`

The machine-emitted tables, one CSV each, plus a `.md` sibling for every one of them except
Table A.3 (see below). Regenerate with:

```
python src/figures/emit_tables.py                 # Tables 3.4, A.1, A.2, A.3
python -c "import sys; sys.path.insert(0,'src/figures'); sys.path.insert(0,'src'); \
           import attribution_figures as A; A.table_top3()"   # Table A.7
```

| File | Table | Rendered to markdown? |
|---|---|---|
| `table_3_4_event_level_per_patient.csv` | 3.4 | Yes — embedded in `tables_ch3.md` |
| `table_A1_corpus_metadata.csv` | A.1 | Yes — embedded in `tables_appendix.md` |
| `table_A2_channel_annotation.csv` | A.2 | Yes — embedded in `tables_appendix.md` |
| `table_A3_full_grid.csv` | A.3 | **No** — 384 rows; `tables_appendix.md` gives a one-line pointer to this CSV instead |
| `table_A7_top_channels.csv` | A.7 | Yes — embedded in `tables_appendix.md` |
| `timeline_composition.csv` | — (diagnostic) | Copied from `results/diagnostics/timeline_composition.csv`, which remains the tracked original; not a report exhibit |

`render_markdown()` (in `src/figures/emit_tables.py`) is the single renderer both `emit_tables.py`
and `attribution_figures.py::table_top3` call; it writes sentence-case headers with no code
variable names and no internal shorthand, three decimals for sensitivity/precision/F1/
discrimination, one decimal for false alarms per day, and `undefined` left as the literal word.

## Tables not filled here, and why

| Table | What is missing |
|---|---|
| 1.2 | Design requirements and targets. Comes from the outline's requirements section, not from a result file. |
| 1.3, and the timeline figure | Calendar dates. Boti supplies. |
| 2.1 | Candidate corpora. Every cell needs the corpus's own documentation and a citation; none of it is in this repository. |
| 2.8, 2.10 | Decision matrices for the detection stage and the deployment strategy. Qualitative; the criteria come from the outline. |
| 2.11 | Application processing stages. Comes from the application specification, which is not attached to this project. |
| 3.11, 3.12 | Processing time per stage waits on the application build. The objectives table is written last, from the finished Chapters 2 and 3. |
| 4.2 | Cost profile. One measured value exists — 16.9 ms per window on the development processor, about 15 s per hour of recording — recorded in the application specification. The rest is not measured and must be marked so. |

As of docs/FIGURE_ROUND6.md, Tables A.1, A.2, A.3 and A.7 are no longer in this list: all four are
now emitted from committed files and live in `tables/tables_appendix.md` (A.3 as a CSV pointer,
the other three as rendered markdown tables).

## Status of each table (readiness, as of Round 6)

| Ready to drop in | Needs re-running an emit script | Needs an input only Boti has |
|---|---|---|
| 1.1 · 2.2 · 2.3 · 2.4 · 2.5 · 2.6 · 2.7 · 2.9 · 2.12 · 3.1 · 3.2 · 3.3 · 3.5 · 3.6 · 3.7 · 3.8 · 3.9 · 3.10 · 4.1 · A.4 · A.5 · A.6 | 3.4 · A.1 · A.2 · A.3 · A.7 | 1.2 · 1.3 · 2.1 · 2.8 · 2.10 · 2.11 · 3.11 · 3.12 · 4.2 |

"Needs re-running an emit script" tables are already filled with committed, self-checked values;
re-running the script only reproduces them from source rather than filling in anything new.
