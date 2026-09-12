# Figure Work — Round 10

One new figure, nine figures to archive, one ignore-rule fix.

`docs/VERIFIED_NUMBERS.md` is the authority for every number. Standing rules as before: palette, PNG
only, no confidence intervals, no figure number or descriptive title inside the image, no internal
shorthand in any label.

**Report every item as applied or not applied**, with file and line.

---

# 1 · Fig 2.14 — event-based scoring

`fig2_14_event_scoring.py` is supplied alongside this brief. Place it at
`src/figures/fig2_14_event_scoring.py` and run it. **Do not modify it and do not rewrite it.** It was
written and rendered before delivery.

Two properties of it matter and must survive any later edit:

**It reads the five scoring parameters from `src/szcore_eval.py` rather than containing them.** If the
lookup fails it exits rather than drawing. A figure that teaches a tolerance rule must not be able to
disagree with the scorer that implements it.

**The scenario is illustrative and reports no result.** Three annotated seizures and four detections,
constructed to produce one match by overlap, one match by the post-offset tolerance alone, one merge,
one false positive and one missed seizure. The script prints the outcome of each so the caption can be
checked against the scoring rule rather than against the picture.

Run it and report the printed parameter block and the printed outcomes. If the parameters printed
differ from 30, 60, 90 and 300 seconds, **stop** — that means the scorer changed and several documents
need updating, not just this figure.

The caption is printed by the script. Add it to `docs/CAPTIONS.md`, replacing the existing Figure 2.14
entry.

---

# 2 · Archive nine cut figures

The exhibit set was reduced. These nine are cut and move to `figures/archive/`:

```
fig2_2_seizure_durations.png
fig2_5_sparsification_rules.png
fig2_9_weight_simplex.png
fig2_10_changepoint_detection.png
fig3_2_score_distributions.png
fig3_7_persubject_event.png
fig3_9_alternatives_effect.png
fig3_12_attribution_seed_stability.png
fig3_14_attribution_persubject_forest.png
```

Use `git mv`. **Archive, do not delete** — several of these may return if a cut is overruled.

**Leave their generating scripts alone.** This is a deliberate departure from the rule applied in
earlier rounds. Those scripts still run correctly and their output paths are still right; a cut is an
editorial decision about the report, not a defect in the figure. Instead, write
`figures/archive/README.md` recording which exhibit each archived file was, the round at which it was
cut, and the one-line reason. Note in it that re-running the generator puts the file back at the root
of `figures/`, which is the intended behaviour if a cut is reversed.

**Do not renumber anything.** Renumbering after the cuts is a separate job, to be done once, later,
across the figure filenames, `docs/CAPTIONS.md` and the cross-references in all five table files. Doing
it piecemeal now would leave the two halves inconsistent.

---

# 3 · Fix the ignore rule so the archive is tracked

`figures/archive/` is currently outside version control, because `/figures/*` with `!/figures/*.png`
admits only root-level PNGs. Nine figures are about to move into a directory that git does not see, and
the project's rule is to archive rather than delete. That rule is currently guaranteed by one hard
drive.

Add an exception for `figures/archive/`, in the same shape as the one already added for
`figures/drawio_sources/`. Verify with `git check-ignore -v` on one file inside it after the move, and
confirm the nine archived figures appear in `git status`.

Then run `git status --ignored --short figures/` and report anything still ignored. That rule has
hidden a file twice.

---

# 4 · What to report back

Each item applied or not applied, with file and line. Then:

- the parameter block and the per-interval outcomes printed by the new script;
- confirmation that the nine archived figures are tracked by git after the move;
- the output of the ignored-files check;
- `find figures -iname "*.pdf"` returning nothing.

Push back rather than accommodate on anything here that disagrees with a committed value. Commit when
the round is complete, and push.
