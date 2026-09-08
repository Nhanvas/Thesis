# Figure Work — Round 9

The last round. Two cosmetic fixes, four files to place, one repository check.

**Report every item as applied or not applied**, with file and line.

---

# 1 · Fig 1.1 — two collisions

The rebuilt layout works: the ictal excerpt is now clearly distinguishable from the other three, which
is what the figure exists to show. Two overlaps remain.

- The four excerpt markers under the upper panel's axis sit on top of the tick labels 200, 250, 300
  and 350. Move them above the axis line, or drop them below the tick labels — either is fine, but
  they must not overlap the numbers.
- The `onset` and `offset` labels in the upper panel overlap each other and the edge of the ictal
  shading. Stagger them vertically or move them outside the shaded region.

Nothing else about this figure changes.

---

# 2 · Fig 4.1 — one collision

The legend and the three label strings are correct now. The `Community challenge 2025, winner` label
sits close enough to the `Best point, located after scoring` annotation that at print size they read
as one block. Move one of them.

Nothing else about this figure changes.

---

# 3 · Four files to place

Supplied alongside this brief. **Do not generate any of them and do not modify their contents.** If
one is missing, stop and report it rather than reconstructing it.

| File | Goes to | Note |
|---|---|---|
| `tables_ch1.md` | `tables/tables_ch1.md` | **replaces** the existing file — its rules block now matches the other four chapter files |
| `HANDDRAWN_SPEC_ADDENDUM.md` | `docs/HANDDRAWN_SPEC_ADDENDUM.md` | drawing specs for Fig 2.1 and Fig 2.14 |
| `CAPTIONS.md` | `docs/CAPTIONS.md` | the final caption for every exhibit |
| `FIGURE_ROUND9.md` | `docs/FIGURE_ROUND9.md` | this file |

Update `tables/README.md` to drop the note about `tables_ch1.md` having a shorter rules block; it no
longer does.

---

# 4 · Repository check

Two directories to look at:

- `figures/tables/` — the qualitative tables landed there by mistake last round, invisible to version
  control because the ignore rule admits only PNG files at the root of `figures/`. Confirm it is empty
  and remove it, so it cannot swallow another file.
- Run `git status --ignored --short figures/` and report anything ignored that is not in
  `figures/archive/` or `figures/drawio_sources/`. That ignore rule has now hidden a file twice, and a
  third time would be during the writing phase when it would be hardest to notice.

Also confirm `figures/drawio_sources/` exists, or create it — the hand-drawn diagrams' editable
sources go there and they must be tracked.

---

# 5 · What to report back

Each item applied or not applied, with file and line. Then:

- confirmation that `tables/` holds Chapter 1 through 4 plus the appendix, and that every file opens
  with the same rules block;
- the output of the ignored-files check;
- `find figures -iname "*.pdf"` returning nothing.

Commit when complete, and push.

---

# 6 · What remains after this round

Nothing further for you until the application build. For the record, so nobody re-opens closed work:

**Complete:** all twenty-five code-generated figures, all four emitted tables, the tables pack across
five chapter files, the caption sheet, and the drawing specifications for all ten hand-drawn figures.

**With Boti:** ten hand-drawn diagrams — Fig 1.3, 1.4, 1.5, 2.1, 2.6, 2.7, 2.11, 2.12, 2.13, 2.14.

**Blocked on inputs that do not exist yet:** the non-CHB-MIT rows of Table 2.1, which need each
corpus's own documentation opened and cited; Table 2.11's stage boundaries, which need the application
specification; and Table 3.11, Table 3.12 and Figures 3.16 to 3.18, which wait on the application
build and on the finished chapters.

**One caption cannot be written from the record:** Figure 2.8 predates the caption sheet and its axes
are not described in the exhibit list. The Chapter 2 writer describes it from the figure itself.
