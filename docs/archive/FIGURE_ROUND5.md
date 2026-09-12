# Figure Work — Round 5

Small round. Seven figure fixes, one docstring correction, one repository note.

Read `docs/FIGURE_BRIEF_ROUND2.md` §1 for the standing rules if they are not already in context:
palette, PNG only, no confidence intervals, no figure number or descriptive title inside the image,
no internal shorthand in any label. `docs/VERIFIED_NUMBERS.md` remains the authority for every
number.

**Report every item as applied or not applied**, with file and line. When several items touch one
file, none is skipped because another one in that file needed no change.

**Four figures are finished and must not be touched:** Fig 1.2, Fig 2.5, Fig 3.8, and the four
attribution figures 3.11 to 3.14.

---

# 1 · Fig 2.3 — the vertical clipping introduced a new error

Clipping panel (c) at 10⁻⁴ cuts the preprocessed curve off from about 30 Hz upward, so it appears to
vanish at 30 Hz. A reader will conclude the band-pass stops at 30 Hz. It does not — it stops at
60 Hz, and Table 2.5 of the report lists a gamma band spanning 30 to 60 Hz. The figure as drawn
contradicts the table.

The fix is not a lower floor. **Normalise both spectra** — divide each by its own total power, or
express each in decibels relative to its own maximum — so the two curves occupy the same range.
The panel then shows exactly the two things it exists to show: the 60 Hz peak present in the raw
trace and absent after filtering, and the roll-off above 60 Hz. State in the axis label which
normalisation you used.

Keep panels (a) and (b) as they are. The scale bars and units are correct.

---

# 2 · Fig 3.4 — internal branch names are leaking into the report

The three component panels are labelled `GAE reconstruction (zrecon)`, `Latent Mahalanobis
(zlatent)` and `Gamma-band AEC (zgamma)`. Those parenthesised names are this project's own working
shorthand and appear nowhere in the thesis. Remove them:

| Current | Becomes |
|---|---|
| `GAE reconstruction (zrecon)` | `Reconstruction error (standardised)` |
| `Latent Mahalanobis (zlatent)` | `Latent Mahalanobis distance (standardised)` |
| `Gamma-band AEC (zgamma)` | `Gamma-band amplitude coupling (standardised)` |

Also print, for each detected interval on this recording, whether it matched an annotated seizure or
not, with its boundaries in seconds. The figure shows one detection starting close to the end of the
first annotated seizure; whether that counts as a match depends on the scoring tolerance, and the
caption must not claim a detection the scoring rule did not award. I need the assignment from the
scorer, not from reading the picture.

---

# 3 · Fig 2.10 — it currently duplicates Fig 3.4

Fig 2.10 and the bottom panel of Fig 3.4 show the same recording over the same hour, differing only
in whether the detections are drawn as vertical lines or shaded bands. Two consecutive chapters
would print almost the same picture.

Fig 2.10 sits in the methodology chapter and its job is to show what change-point detection *does*.
Rebuild it as a **zoom of about five minutes centred on one annotated seizure** of the same
recording, so the mechanism is visible: the score level before the shift, the shift itself, the
change points bracketing it, and the annotated seizure shaded.

Fig 3.4 keeps the full hour unchanged apart from item 2 above.

Remove `(recomputed)` from the legend entry. That belongs in the caption, not on the plot.

---

# 4 · Fig 3.10 — the traces are unreadable

The six signal traces overlap into a solid block. Increase the vertical offset until each trace is
clearly separated across the whole window, even where the amplitude is largest inside the
false-positive interval. This is the most informative figure in the results chapter and the reader
has to be able to see the individual channels.

State in the console output whether the signal panel shows the raw recording or the band-pass
filtered signal, so the caption can say which. The scale bar reads microvolts, so it is not the
z-scored version — confirm which of the other two it is.

---

# 5 · Fig 3.15 — three items

- The explanatory sentence sits inside the image. Move it out. Print it to the console as caption
  text instead. No figure in this report carries a sentence of prose inside the axes.
- The diffuse group is drawn in the purple reserved for the post-hoc best operating point
  (`BEST_ACHIEVABLE`). Reusing that colour for an unrelated category breaks the one meaning it
  carries across the figure set. Pick another colour and add it to `palette.py` as a named constant.
- The synthetic line has markers at 1, 2, 4, 12 and 18 injected channels, with **no point at 8**,
  while the pre-registered grid is 1, 2, 4, 8, 12. Report what `synthetic_spread.csv` actually
  contains and why those two sets differ. Do not add or remove a point to make them agree — if the
  spread experiment used a different grid from the discrimination experiment, that is a fact about
  the experiment and belongs in the caption.

---

# 6 · Fig 2.2 — a legend entry for a line that is not drawn

The legend lists the 4 s analysis window, but the horizontal axis starts near 6 s, so the line falls
outside the plot. Extend the lower limit to about 3.5 s so the line appears. It is a meaningful
reference: it shows that the shortest annotated seizure is barely longer than one and a half
analysis windows.

Clip the upper limit to just past the longest seizure. The axis currently runs well past the last
bar.

---

# 7 · Fig 2.4 — cosmetic only

The circular layout in panel (d) starts at a different node from the first row of panel (c). The
cyclic order is the same, so a reader can still follow an edge, but starting both at `FP1-F7` would
make the correspondence immediate. Apply if it is a one-line change; skip and say so if it is not.

---

# 8 · `src/labeling/label_eeg_pilot.py` — a claim that contradicts the specification

The file states that the labelling was "BLIND by construction" and cites a section of PREREG_05 that
does not exist. `docs/ATTRIBUTION_SPEC.md` states directly that the labels are an AI draft, not
blind and not supervisor-frozen. The specification is the higher authority and it is the one the
report follows.

Replace the claim in the docstring with an accurate description: the script renders segments of the
raw recording for annotation, it reads the recordings and the summary timings only and never any
model output, and the annotations produced from it are **not blind**. Remove the citation to the
non-existent section rather than repointing it at a real one.

Change nothing else in that file, and change nothing in `ATTRIBUTION_SPEC.md`. This is a correction
to a source file whose comment disagrees with the record, not a change to the record.

---

# 9 · Repository note — no action, confirm you have seen it

The new ignore pattern `/figures/*` with `!/figures/*.png` correctly tracks root-level figures. It
also means `figures/archive/` is no longer tracked. The project's rule is to archive rather than
delete, and superseded figures now exist only on the local disk.

Report whether `figures/archive/` currently holds anything, and how many files. No change until
that is decided.

---

# 10 · What to report back

Each item applied or not applied, with file and line. Then:

- the match assignment for every detected interval on the running-example recording, from the
  scorer, with boundaries in seconds;
- what `synthetic_spread.csv` contains for the injected-channel grid;
- whether the Fig 3.10 signal panel shows raw or filtered signal;
- the contents count of `figures/archive/`;
- `find figures -iname "*.pdf"` returning nothing, and every changed file tracked without `-f`.

Push back rather than accommodate on anything here that disagrees with a committed value. Commit
when the round is complete; the working tree should not be left dirty between rounds.
