# Round 6 — Report assets

Small round. One directory move, one rendering script, one archive.

The goal: everything the report needs sits in two folders at the repository root, `figures/` and
`tables/`, so a chapter can be assembled without re-running anything and without knowing where in
`results/` a number came from.

**Report every item as applied or not applied**, with file and line.

---

# 1 · What is NOT moving

`figures/` stays where it is. It was consolidated last round, all 23 exhibits are at its root under
their exhibit numbers, fifteen generating scripts point at it, and the ignore pattern was fixed for
it. Moving it again would mean another pass over every one of those scripts, and the failure mode of
that pass — a script quietly recreating the old path beside the new one — has already happened once
in this project. The gain does not cover the risk.

`results/` keeps its meaning: outputs of experiments, tracked by `docs/PROVENANCE.md`. Report assets
are a different kind of thing and get their own place.

---

# 2 · Create `tables/`

```
tables/
  README.md
  tables_ch2.md
  tables_ch3.md
  tables_ch4.md
  tables_appendix.md
  csv/
    table_3_4_event_level_per_patient.csv
    table_A1_corpus_metadata.csv
    table_A2_channel_annotation.csv
    table_A3_full_grid.csv
    table_A7_top_channels.csv
    timeline_composition.csv
```

`git mv` the five files from `results/report_tables/` into `tables/csv/`, and copy
`results/diagnostics/timeline_composition.csv` in as a sixth — copy that one rather than move it,
because it is a diagnostic output that belongs in `results/` as well.

Update whatever writes those paths: `src/figures/emit_tables.py` and `src/figures/attribution_figures.py`
at minimum. Run the import scan in `REPO_MAP.md` §7.7 afterwards. Remove `results/report_tables/`
once it is empty.

Check that `.gitignore` does not match `tables/` or anything under it. Confirm with
`git check-ignore -v` on one file in `tables/csv/`, as was done for the figures last round.

---

# 3 · Render the emitted tables to markdown

Add a `render_markdown` step to `src/figures/emit_tables.py` that writes, alongside each CSV, a
markdown table ready to paste into a chapter. These go into the chapter files in §4, not into
separate files.

Formatting, matching the report's convention and the CSV output:

- three decimals for sensitivity, precision, F1 and discrimination; one decimal for false alarms per
  day; `undefined` left as the literal word;
- header row in sentence case, no internal shorthand, no column named after a variable in the code;
- Table A.3 has 384 rows and is **not** rendered to markdown — it goes into the report as a CSV
  attachment or a long appendix listing, and the chapter file gets a one-line pointer to the CSV
  instead;
- Table A.2 has 76 rows; render it, and carry the `label_source` column through verbatim.

---

# 4 · Split the tables pack by chapter

`docs/TABLES_PACK.md` holds every table that could be filled from the verification record. Five
accounts write chapters in parallel, so one monolithic file means five people reading past four
chapters of tables that are not theirs.

Split it, preserving text exactly — this is a split, not a rewrite, and no number or sentence
changes:

| New file | Takes |
|---|---|
| `tables/tables_ch2.md` | Tables 2.2 through 2.12 |
| `tables/tables_ch3.md` | Tables 3.1 through 3.10, with the rendered Table 3.4 from §3 replacing the transcribed block |
| `tables/tables_ch4.md` | Table 4.1, Table 1.1, and the Figure 4.1 plotting note |
| `tables/tables_appendix.md` | Tables A.1 through A.7, with the rendered A.1, A.2 and A.7 from §3 |

Each file opens with the rules section from the top of the pack — the decimal convention, the "no
blank cells" rule, the source-line requirement — repeated in full, because a writer opening one file
must not have to find another to know the conventions.

`tables/README.md` lists which table lives in which file, which tables are still unfilled and why,
and states that `docs/VERIFIED_NUMBERS.md` is the authority for every number.

Then move `docs/TABLES_PACK.md` to `docs/archive/`. Two copies of the same tables in two places is
how a corrected number survives in one and not the other.

**If `docs/TABLES_PACK.md` is not in the repository**, stop and report that rather than reconstructing
it. It exists; if it is missing it was never committed, and it must be supplied rather than rebuilt
from anything.

---

# 5 · What to report back

Each item applied or not applied, with file and line. Then:

- confirm `tables/csv/` is tracked and not matched by any ignore rule;
- confirm `results/report_tables/` is gone and nothing still writes to it;
- the import scan result after the move;
- the row count of every rendered markdown table, against its CSV.

Commit when complete. Do not leave the working tree dirty between rounds.
