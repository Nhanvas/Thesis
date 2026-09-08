# Figure Work — Round 7

Two figures, one reference-sheet addition. This is the last round of code figures.

`docs/VERIFIED_NUMBERS.md` is the authority for every number. `docs/FIGURE_BRIEF_ROUND2.md` §1 holds
the standing rules: palette, PNG only, no confidence intervals, no figure number or descriptive title
inside the image, no internal shorthand in any label.

**Report every item as applied or not applied**, with file and line.

---

# 1 · Add the dataset citations to the reference sheet

`docs/Thesis_Reference_Sheet.md` has no entry for the corpus this entire thesis is built on. Add
these four, verbatim. Three come from the dataset's own citation page; the fourth is the montage
definition, taken from reference 64 of the Ingolfsson 2024 paper already held in the project's
reading set.

```
Guttag, J. (2010). CHB-MIT Scalp EEG Database (version 1.0.0). PhysioNet.
RRID:SCR_007345. https://doi.org/10.13026/C2K01R

Shoeb, A. (2009). Application of Machine Learning to Epileptic Seizure Onset
Detection and Treatment. PhD Thesis, Massachusetts Institute of Technology.
http://hdl.handle.net/1721.1/54669

Pollard, T., Moody, B. E., Lehman, L., Gow, B., Fernandes, C., Xie, C., Johnson, A.,
Mark, R. G., & Heldt, T. (2026). PhysioNet as a global platform for biomedical
research. Nature Health. https://doi.org/10.1038/s44360-026-00096-z

American Clinical Neurophysiology Society (2006). A proposal for standard montages
to be used in clinical EEG. ACNS Guideline 6.
```

Mark the first three **VERIFIED FROM SOURCE — dataset citation page**. Mark the fourth
**VERIFIED FROM SOURCE — reference 64 of Ingolfsson et al. 2024**, and note that the same paper's
Methods section states that the corpus follows the international 10–20 system of electrode placement,
which is the sentence the montage figure's caption rests on.

The first three are cited together wherever the corpus is introduced. The fourth is cited by the
montage figure and by the preprocessing section.

---

# 2 · Fig 1.1 — Phases of the EEG signal around a seizure

This figure was previously listed as an adaptation of a published source. It is not one any more.
The project has the recordings, so the figure is drawn from real data — which is cleaner than
adapting a schematic and is more honest about what the phases look like.

**Patient chb11**, a validation patient, per the illustration policy: Chapters 1 and 2 illustrate on
validation data, and the running example is the only exception.

One continuous stretch spanning a seizure, four labelled regions on a shared time axis:

| Region | Definition |
|---|---|
| Interictal | background, well away from any annotated seizure |
| Preictal | a fixed window immediately before annotated onset |
| Ictal | annotated onset to annotated offset |
| Postictal | a fixed window immediately after annotated offset |

Draw three or four channels stacked with a labelled amplitude scale bar, region boundaries as
vertical lines, region names above the trace, and onset and offset marked. Use the ictal colour for
the ictal region and neutral shading for the other three; the preictal and postictal regions must not
be coloured as though they were detections.

**Two constraints that matter more than the drawing.**

The preictal and postictal regions are **defined windows, not annotations**. The corpus provides
onset and offset only. Print the window lengths you used and state them in the caption text you
return. A caption that presents them as annotated states would be wrong.

This thesis is post-hoc review triage, **not prediction**. Do not draw a prediction horizon, a
seizure occurrence period, or anything implying the preictal region is a forecasting target. The
region is shown because it exists in the literature's vocabulary, not because this system uses it.

Print the recording, the seizure index, and the time span shown.

---

# 3 · Fig 4.1 — This work against published results

Previously blocked on the comparator set. That set is now closed: five papers were read from source
and `tables/tables_ch4.md` holds the result.

**Plane:** event sensitivity on the vertical axis, false alarms per day on the horizontal axis.

**This work's curve.** Compute the Pareto front over the committed grid in
`results/phaseB/tier2/rlg_test/final_eval_seed42.csv` — for each false-alarm level, the highest
sensitivity achieved at or below it — and draw it as a line. Mark two points on it:

- the **reported operating point**, sensitivity 0.618 at 27.4 false alarms per day, in the headline
  colour, labelled as the reported result;
- the **best point on the curve**, sensitivity 0.474 at 4.9 false alarms per day, in the
  post-hoc colour, labelled as located after the held-out set was scored.

Both values are self-checked against `docs/VERIFIED_NUMBERS.md` before drawing.

**Three published points.** These are the only published results that are scored at event level, on
a patient-independent split, and report a false-alarm rate. Every other row of Table 4.1 fails at
least one of those three conditions and must not appear here.

| Point | Sensitivity | False alarms / day | Corpus |
|---|---|---|---|
| Ali et al. 2024, 5-fold cross-subject | 0.726 | 127.7 | CHB-MIT |
| Ali et al. 2024, leave-one-out | 0.753 | 115.0 | CHB-MIT |
| Community challenge 2025, winning submission | 0.370 | 1.34 | private |

Label each point with its short name and its corpus. Draw the two same-corpus points in one marker
shape and the different-corpus point in another, so the distinction is visible without reading the
labels.

**Axis.** Use a **logarithmic** horizontal axis. The points span 1.34 to 127.7, and a linear axis
would collapse everything below ten into a single column. State in the axis label that the scale is
logarithmic so no reader misreads the magnitude of the gap.

**Nothing may be added to the plane to make it look fuller.** Three external points is the correct
number, and the sparseness is a finding about the literature rather than a defect of the figure.

Print every plotted coordinate for checking.

---

# 4 · What to report back

Each item applied or not applied, with file and line. Then:

- the preictal and postictal window lengths used in Fig 1.1, and the recording and seizure shown;
- every coordinate plotted in Fig 4.1, including the Pareto front vertices;
- confirmation that the two marked points match `docs/VERIFIED_NUMBERS.md`;
- `find figures -iname "*.pdf"` returning nothing, and every new file tracked without `-f`.

Push back rather than accommodate on anything here that disagrees with a committed value. Commit when
the round is complete.
