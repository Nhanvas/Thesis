# Figure Work — Round 8

Two figure items, one pass across the older figures, and one table filing job.

`docs/VERIFIED_NUMBERS.md` is the authority for every number. `docs/FIGURE_BRIEF_ROUND2.md` §1 holds
the standing rules.

**Report every item as applied or not applied**, with file and line.

---

# 1 · Fig 1.1 — rebuild, the layout does not work

The figure draws 322 s of 256 Hz data across four channels in one panel. At print size that is a
solid block: the individual traces cannot be separated and no waveform morphology is visible. Worse,
the ictal region does not look different from the background, so the figure fails at the one thing it
exists to do. The 2.1 to 3.6 × amplitude contrast the script measured is real but is not visible at
this compression.

This is not fixable by adjusting the amplitude or the offsets. The layout has to change.

**New layout — two rows.**

**Top row, full width: a compressed overview.** The same 322 s, but **one channel only**, drawn as a
thin trace, with the four regions shaded and labelled as they are now, and onset and offset marked.
Its job is temporal context, not morphology, so compression is acceptable here. Add four small
brackets or markers beneath it showing where each excerpt below was taken from.

**Bottom row: four excerpts, side by side, equal width.** One per region, **10 s each**, same four
channels, stacked with enough vertical offset that every trace is clearly separated, one shared
amplitude scale bar. Each excerpt headed with its region name only. The four share one amplitude
scale so the reader can compare them — say so in the console output so the caption can state it.

Pick each 10 s excerpt from the middle of its region. For the ictal excerpt, the seizure is 22 s, so
a 10 s window sits comfortably inside it.

**Terminology.** Relabel the background regions **`Background`**, not `Interictal`. In this thesis
"interictal" names a *defined set* — artifact-rejected, with 4 h after each seizure excluded, and it
is the set the model is trained on. The region either side of this seizure is not that set. One word
carrying two meanings in one document is where a reviewer stops. Keep `Preictal`, `Ictal` and
`Postictal` as they are.

**Unchanged constraints.** Preictal and postictal are fixed windows, not annotations — print the
lengths and state them in the caption text you return. No prediction horizon and no seizure
occurrence period: this thesis is post-hoc review triage, not prediction.

---

# 2 · Fig 4.1 — legend wording

The figure itself is correct. Three strings in the legend are not.

| Current | Becomes |
|---|---|
| `This work -- Pareto front (committed grid)` | `This work, achievable trade-off curve` |
| `Reported operating point (m50/p2.0)` | `Reported operating point` |
| `Best point on the curve (located post-hoc)` | `Best point on the curve, located after scoring` |

`m50/p2.0` is this project's own shorthand and appears nowhere in the thesis. "Committed grid" is
repository vocabulary. The double hyphen is not an em dash.

Also move the `Community challenge 2025, winner` label clear of the vertical axis, where it currently
collides.

---

# 3 · Strip figure titles from the older figures

Standing rule 5 — no figure number and no descriptive title inside the image, because the report's
caption carries both — was applied to every figure built from round two onward. The fourteen figures
that predate it were deferred to "a single later pass". That pass has not happened.

Fig 3.7 still carries `Fig 3.7 — event-level per-subject breakdown at the headline point only
(m50/p2.0)` as a suptitle, and states the operating point a second time in its panel (a) title. Placed
under a caption reading "Figure 3.7 …", the same information prints twice.

Go through every figure at the root of `figures/` and remove, from inside the image:

- any suptitle containing a figure number;
- any descriptive title that a caption would carry;
- any repetition of the operating point where it already appears elsewhere in the same figure;
- any occurrence of the grid notation `m…/p…` in a title, label or legend.

**Keep** panel tags `(a)`, `(b)`, short panel headings that name what a panel shows, axis labels,
units, and legends.

Return the list of figures you changed and the exact string removed from each. If a figure has no
title to remove, say so rather than skipping it silently.

---

# 4 · File the qualitative tables into the chapter files

`tables/tables_qualitative.md` holds eight tables that belong in four different chapters, and
`tables/` has no Chapter 1 file at all. Distribute them, preserving text exactly — this is a move, not
a rewrite, and no number or sentence changes:

| Table | Goes to |
|---|---|
| 1.1, 1.2, 1.3 | `tables/tables_ch1.md` — **supplied, do not rebuild** |
| 2.1, 2.8, 2.10, 2.11 | `tables/tables_ch2.md` |
| 3.11, 3.12 | `tables/tables_ch3.md` |
| 4.2 | `tables/tables_ch4.md` |

`tables/tables_ch1.md` is being added to the repository alongside this brief. It already contains
Tables 1.1, 1.2 and 1.3 in final form. **Do not generate it and do not modify its contents.** If it is
not present, stop and report that rather than reconstructing it.

Remove Table 1.1 from `tables/tables_ch4.md`, since it now lives in the Chapter 1 file. Leave Table
4.1 and the Figure 4.1 plotting note where they are.

Each chapter file must open with the rules section in full, as the existing ones do, so a writer
opening one file never has to find another to know the conventions.

Then move `tables/tables_qualitative.md` to `docs/archive/` and update `tables/README.md` to list
Chapter 1 and the newly filed tables. Two copies of the same table in two places is how a corrected
value survives in one and not the other.

---

# 5 · What to report back

Each item applied or not applied, with file and line. Then:

- the four excerpt time ranges chosen for Fig 1.1, and confirmation that the four share one amplitude
  scale;
- the list of figures whose titles were stripped, with the exact string removed from each;
- confirmation that `tables/` now holds Chapter 1 through 4 plus the appendix, and that no table
  appears in two files;
- `find figures -iname "*.pdf"` returning nothing.

Push back rather than accommodate on anything here that disagrees with a committed value. Commit when
the round is complete.
