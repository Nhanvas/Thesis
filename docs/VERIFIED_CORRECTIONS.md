# Verified Corrections — writing phase

Every entry below was settled by opening a file or running a command during the report-writing sessions
of 2026-09-12. Each one **supersedes** a statement that is still carried, at the time of writing, by the
project instructions, an older revision of a caption sheet or table pack, or a drawn figure. This file
exists so that none of them is re-litigated a fifth time.

Authority is unchanged: `RESULTS_OF_RECORD_phaseB.md` for numbers, `PROVENANCE.md` for artifact
identity, `REPO_MAP.md` for paths. This file records where a *derived* statement went wrong, and what
the evidence says instead.

---

## 1 · Common average reference exists and is part of the pipeline

**Wrong statement, now retired:** CAR does not exist in this project's code, so the two paragraphs
describing it were cut from Chapter 2.

**Evidence.** `apply_car` is defined at `src/dataprep/graph_construction.py:84` and called inside the
adjacency builders at lines 260 and 380. It subtracts the across-channel mean at each time point, on
each analysis window, before wPLI and AEC are computed. Its own docstring states that it must be
applied before wPLI. Every figure generator that builds an adjacency calls it.

**How the error happened.** The confirming grep covered `preprocessing.py` and `build_graphs.py` only.
It returned nothing, and the empty result was read as proof of absence. `graph_construction.py`, where
the function actually lives, was not in the search path.

**What follows.**
- CAR is a graph-construction step, not a preprocessing step. It is correctly absent from the
  preprocessing table, and the stored signals in `data/processed/` are not CAR-referenced.
- Chapter 2 §2.2.1 and §2.2.5 describe it. Both were restored.
- **Do not credit CAR with resistance to volume conduction.** That is wPLI's own property, since wPLI
  uses only the imaginary part of the cross-spectrum, and the chapter says so two paragraphs later. AEC
  is the branch that benefits. The defensible claim is that the reference alters estimated inter-channel
  relationships, so it is applied where those relationships are computed and nowhere else.
- Applying CAR on an already bipolar montage is unusual and is the likeliest question at the defense.
  There is no ablation for this step; the honest answer is that it was in the locked pipeline.

---

## 2 · Preprocessing step order: post-seizure exclusion precedes artifact rejection

**Wrong statement, now retired:** artifact rejection is step 4 and the post-seizure exclusion step 5.

**Evidence.** In `src/dataprep/preprocessing.py`, `compute_subject_stats` builds the post-seizure
buffer mask and skips every ictal or buffered window before accumulating the per-channel mean and
standard deviation. The artifact threshold is five times that standard deviation. The exclusion
therefore has to come first: the threshold is derived from statistics the exclusion has already
filtered.

**How the error happened.** The file's opening docstring numbers amplitude artifact rejection as
"Step 4". A table was numbered from the docstring rather than from the executed order.

**What follows.**
- `tables/tables_ch2.md` Table 2.3: corrected, and both writer's traps are recorded in the block.
- Chapter 2 §2.2.2 and Table 2.3: corrected, and the dependency between the two steps is now stated.
- **Figure 2.4 is drawn with the two boxes the wrong way round and needs redrawing.** This is the only
  outstanding artefact.

---

## 3 · The background statistics are subsampled, at a stride whose value is unread

**Two wrong statements, one in each direction.** First, that the statistics come from a fixed
one-in-ten subsample, asserted from `PROPOSED_SOLUTION.md`, a planning document. Then, on seeing
Welford's online algorithm named in the code, that there is no subsample at all.

**Evidence.** `compute_subject_stats` skips every ictal or buffered window, then advances a counter and
processes only every `STATS_SUBSAMPLE`-th surviving window. The stride is real. Welford's algorithm and
a stride are not alternatives; the algorithm streams whatever the loop feeds it.

**What follows.** Chapter 2 §2.2.2 says "a fixed subsample taken at a regular stride", which is true
whatever the constant turns out to be. To name the ratio:
`grep -n "STATS_SUBSAMPLE" src/dataprep/preprocessing.py`. The same output also confirms entry 2, since
the ictal-and-buffered skip sits above the subsample counter in the same loop.

**Worth noting.** The second error was mine, and it was the same mistake as the first in reverse:
inferring absence from a partial view instead of reading the loop.

---

## 4 · The ensemble weight surface is not flat

**Wrong statement, now retired, and this is its fifth appearance:** the weight surface is flat, so equal
weighting falls within tolerance.

**Evidence.** `VERIFIED_NUMBERS.md` Part 5 and `LOCKED_DOCS_ADDENDUM.md` §1.3: the optimum is 0.9405 at
(0.10, 0.45, 0.45) against 0.9283 at equal weights, a gap of 0.0122 on a cross-model spread of 0.0025,
and equal weighting is **not** among the 29 points within tolerance of the optimum.

**What follows.** Equal weights remain what the system uses. They are justified as an inherited choice
that a later, more targeted search did not confirm, never as a measured flat surface. The four values
belong to Chapter 3 §3.5.4; Chapter 2 §2.3.5 states the relation without numbers, because Chapter 2
reports no measurement.

---

## 5 · Parameter count is 3,285

**Wrong statement, now retired:** approximately 8.7k trainable parameters.

**Evidence.** `VERIFIED_NUMBERS.md` Parts 2.1 and 2.2, read from the checkpoint state dictionary. The
figure is also inconsistent with the checkpoint's own file size of 15,258 bytes. Figure 2.4 prints
3,285.

---

## 6 · Processing time is 9.76 s per hour, and the variance belongs to one stage

**Wrong statements, now retired:** 16.9 ms per analysis window; approximately 15 s per hour of EEG; and
a fivefold run-to-run variation on the end-to-end figure.

**Evidence.** `REPO_MAP.md` §3b, dated 2026-09-10, records that 16.9 ms was a component benchmark
covering adjacency construction and band powers only, never the full pipeline.
`web_demo/BUILD_PROGRESS.md` §4 records the end-to-end figure as **9.76 s per hour of EEG** on
`chb06_01.edf`, CPU only, after `filter_window()` was changed to filter the whole recording once rather
than per window. The same record notes run-to-run variation of roughly fivefold, **22 to 110 s on the
adjacency and band-power stage**, on identical code and the same file, attributed to background load.

**What follows.** The end-to-end figure was measured once. Report it as indicative, state the
variation, and do not attach the fivefold range to the end-to-end number as though it had been measured
there. The per-window figure appears nowhere in the report.

---

## 7 · Demo normalisation scope is per subject

**Unresolved state, now decided:** the code fits z-score statistics and the Ledoit-Wolf covariance per
file, carrying two open `# TODO(step3)` markers, while `SZSCAN_SPEC_v5` intends per subject.

**Decision (Boti, 2026-09-12): per subject.** The thesis normalises per subject at step 6 of the
preprocessing table, so a per-subject fit is the faithful mirror of the offline pipeline; a per-file fit
gives each file its own baseline and loses comparability between the files of one patient. Chapter 2
§2.6.3 is written per subject. The per-file code is build debt to close in Step 3, not the design.

---

## 8 · The three sets are training, validation and test

**Retired term:** *held-out*. The report uses **test** everywhere, matching the split file's own key
names. Applied across `CAPTIONS.md` revision 5 and all five files in `tables/`. Nothing about the split
itself changes: it is still scored once, and no recording from it reaches training or tuning.

---

## 9 · Table 2.8 uses the four criteria the outline requires

**Superseded:** the six-criterion deployment matrix.

**Evidence.** `THESIS_OUTLINE_FINAL.md` §2.6.1 requires cloud, on-premise and bedside scored against
weighted **economic, societal, environmental and scalability** criteria. `tables/tables_ch2.md` has been
replaced with that form, matching Chapter 2 §2.6.1.

---

## 10 · Outstanding artefacts

The queue that held them, `docs/FIX_QUEUE.md`, was worked through on 2026-09-12 and 2026-09-16 and
then deleted, as it was written to be. What it closed is recorded in `docs/EXHIBIT_SET_FINAL.md`
revision 3 under "Closed since revision 2", and what remains open is in the section after it.

---

## 11 · Method of record

Four of the ten entries above were caused by the same thing: a statement inferred from a filename, a
docstring, a planning document or an empty grep, rather than read from the code that runs. The command
that settles a question is almost always one line. Prefer the command.
