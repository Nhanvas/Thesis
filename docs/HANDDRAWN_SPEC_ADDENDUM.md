# Hand-Drawn Figures — Addendum

Two more diagrams, bringing the hand-drawn set to ten. Same conventions as
`docs/HANDDRAWN_FIGURES_SPEC.md` §0: serif type, white fills with coloured borders, orthogonal
arrows, no figure number and no descriptive title inside the image, PNG at 300 dpi into `figures/`,
`.drawio` source into `figures/drawio_sources/`.

Both of these were previously listed as adaptations of published figures. Neither is. The content of
each comes from a source already in this project, so no external figure needs to be traced.

---

# Fig 2.1 — The bipolar longitudinal montage

**Base image.** The 10–20 electrode schematic already saved in the project. Import it into draw.io,
place it on a locked background layer, and draw on top of it. Do not redraw the head or the electrode
circles — they are correct.

**What to add: eighteen connecting lines**, one per derivation, drawn as arcs or straight segments
between the two electrode circles named. Colour each of the five chains differently, and add a small
legend naming the chains.

| Chain | Derivations |
|---|---|
| Left temporal | FP1–F7 · F7–T7 · T7–P7 · P7–O1 |
| Left parasagittal | FP1–F3 · F3–C3 · C3–P3 · P3–O1 |
| Right parasagittal | FP2–F4 · F4–C4 · C4–P4 · P4–O2 |
| Right temporal | FP2–F8 · F8–T8 · T8–P8 · P8–O2 |
| Midline | FZ–CZ · CZ–PZ |

That is eighteen lines, in the order used by every other figure in the report. Keep this order in the
legend so a reader comparing it against Fig 1.2, Fig 2.4 or Fig 3.10 finds the same sequence.

The two outer chains on each side form the arc shape that gives this montage its clinical nickname,
the "double banana". Say so in the caption — a clinical reader recognises it immediately, and it
signals that the montage was not invented for this thesis.

**Three electrodes carry no derivation** in this set: FZ and PZ appear only in the midline pair, and
CZ appears twice. Every other electrode appears in exactly two derivations. If a line is missing or
doubled, that check will find it. Count before exporting.

**Do not relabel anything.** The schematic uses T7, T8, P7 and P8. Those are the names the corpus
uses and the names every other figure and table in this report uses. Older clinical material calls the
same electrodes T3, T4, T5 and T6; do not add those as alternatives, because a reader would then have
to decide which set the results refer to.

---

# Fig 2.14 — Event-based scoring rules

Two tracks on a shared horizontal time axis, plus a rules panel beneath.

**Track 1, upper, labelled `Annotated seizures`.** Two bars in the ictal colour. Around each bar, a
lighter shaded margin extending **30 s to the left** and **60 s to the right**, labelled once as
`matching tolerance`. Place the two annotated seizures far enough apart that their tolerance margins
do not touch.

**Track 2, lower, labelled `Detected intervals`.** Four bars in the detected-interval colour,
positioned to produce one instance of each outcome:

| Bar | Position | Outcome |
|---|---|---|
| 1 | overlapping the first annotated seizure | true positive |
| 2 | starting shortly after the first seizure ends, inside the 60 s margin | true positive — matched by tolerance, not by overlap with the annotation itself |
| 3 | far from any annotated seizure | false positive |
| 4 | none — the second annotated seizure has no detection | false negative |

Label each outcome directly beneath its bar. Bar 2 is the one that teaches the figure's point, so give
it a short call-out: *matched because it falls inside the post-offset tolerance.*

**Rules panel beneath the tracks**, five lines, plain text in a bordered box:

```
Matching                any overlap between a detected interval and an
                        annotated seizure, after tolerances are applied
Tolerance before onset  30 s
Tolerance after offset  60 s
Merging                 detections separated by less than 90 s are joined
Maximum event length    detections longer than 5 minutes are split
```

**These five values come from `src/szcore_eval.py`, lines 72 to 75**, where they are set and where the
file records that they were checked against the scoring library. They do not come from a paper and
they do not come from memory. If a value in the drawing disagrees with that file, the file is right.

**One line to the right of the rules panel**, in the problem colour:

```
Specificity is not defined at event level: a true-negative
event has no meaning once a timeline is expressed as events.
False alarms per day replaces it.
```

That sentence is the reason this figure exists in a methodology chapter rather than a footnote. It is
a structural property of event-level scoring, not a choice this thesis made, and the caption should
say so.

The caption cites the scoring framework paper already recorded in the reference sheet as the source of
the convention.
