# Request from the report project to Project 2 — what the thesis report needs from SzScan

**From:** the thesis report project (Project 1). **To:** Project 2 (SzScan build).
**Date:** 2026-09-25. **Relayed by:** Boti.

The web application is built. The thesis report has a fixed set of places that can only be written from
the built application, and they are listed here. Please answer every item in one response file,
`web_demo/REPORT_HANDBACK.md`, using the template in Part 5, and put every artifact it refers to under
`web_demo/report_handback/`. Boti will pass the response back to Project 1, which writes the report text.
Project 1 does not edit anything in `web_demo/`; Project 2 does not write report text.

**Ground rules for the whole response.**
1. Report what the built application does, read from the code and from runs, not from the spec. Where the
   build differs from `SZSCAN_SPEC_v5.md`, say so explicitly; the difference is what the report needs.
2. Every number comes from a run or a file, with the command that produced it. No estimates, no "~".
   If something was not measured, write "not measured".
3. The application never reads seizure annotations (project instructions §11.2, `test_guards.py`).
   Nothing in this request changes that. **Do not score the application's detections and do not open
   `chb*-summary.md` seizure fields or `results/attribution_v7/labels/`.** Scoring is done by Project 1
   in `src/`, outside the application, on the exports of Part 3.
4. No evaluation metric appears in the product (instructions §11.4). Screenshots must not show one.
5. `meas_date` in the EDF headers is anonymization-shifted (years 2057 to 2075). No calendar date may
   appear in any screenshot or export.

---

## Part 0 — Freeze the build first

Everything in Parts 1 to 4 must come from **one frozen build**, so that the screenshots, the timing and
the evaluation describe the same software (instructions §11.5 rule 9).

- 0.1 Commit the finished build and tag it, e.g. `szscan-frozen-v1`. Report the tag and the full commit
  hash.
- 0.2 Run the guard tests on that commit and paste the full output:
  `python -m pytest web_demo/backend/tests/test_guards.py -v`
- 0.3 Confirm `python src/verify_provenance.py | grep -a -i verdict` prints `VERDICT: PASS` on the same
  checkout, and that the application loads `data/models_retrain/gae_joint_seed42.pt` (sha256
  `dea06cb5…726ea108`). State where in the backend the checkpoint path is set.
- 0.4 If a defect is found after Part 3 has run, fix it, re-tag, and repeat Parts 2 and 3 in full. Do
  not re-run single subjects.

---

## Part 1 — What the application does (for Chapter 2 §2.5.2, Figure 2.6, and Chapter 3 §3.5.1)

### 1.1 Detection path, as built

The report states that the application runs the thesis detection routine with **three divergences**
(Chapter 2 §2.5.2): (a) normalization statistics, the Ledoit-Wolf covariance of the latent distance,
and the per-branch robust standardization are fitted on the whole recording, and artifact rejection is
not applied; (b) no four-hour post-seizure buffer; (c) the change point penalty and the magnitude
threshold are estimated over the whole recording. Scope is **per subject, not per file** (decided
2026-09-12). Every window is kept, and `t_seconds = window_index × 4`.

Please answer each of these with the file and function that implements it:

- 1.1.1 Is each of (a), (b), (c) implemented exactly as stated? For (a), is the fit per subject, over
  every window of every file of the subject?
- 1.1.2 Is there **any other difference** from the thesis pipeline? Check at least: filtering (0.5 to
  60 Hz fourth-order Butterworth, 60 Hz notch Q = 30, zero-phase, 3 s padding); channel selection and
  the duplicate T8-P8; common average reference inside the adjacency builders; wPLI and AEC with
  α = 0.5; top 20 % sparsification; band powers (Welch, 2 s segments, 50 % overlap); the three
  scores; equal-weight fusion; smoothing (15-window centered moving average); PELT at 20 s resolution
  with minimum segment of three windows; the magnitude filter; merging of candidates 90 s apart or
  less. List every difference, however small.
- 1.1.3 How are several files of one subject handled by the change point stage: is PELT run per file,
  or on a concatenated subject timeline? Are event times reported relative to each file?
- 1.1.4 **Operating point.** State every detection parameter the application uses (magnitude
  percentile, penalty multiplier, and any other), with the file and line where each is set. The report
  must say these are the ones fixed on the validation patients: the validation-derived point is
  `mag_pct = 50`, `pen_mult = 2.0`. If the application uses anything else, say so and why; Project 1
  will decide before Part 3 is scored (instructions §11.5 rule 1).

### 1.2 Channel-level reconstruction-anomaly panel

The decided definition (instructions §11.3, 2026-09-25) is the thesis score with a subject-wide
baseline: per-node reconstruction error; `med` and `mad + 1e-9` (no 1.4826 factor) fitted on every
window of every file of the subject in the processing stage and stored; `|z| = |(r − med) / mad|`;
95th percentile over the windows whose 4 s span overlaps the event's onset to offset; channels ranked
by that value; displayed as `|z|` with two decimals.

- 1.2.1 Is Step 7 round 2 done, so that the panel shows exactly this? Quote the implementing lines
  **with their surrounding lines**, including the line that takes the absolute value.
- 1.2.2 Exact panel title as shown in the UI. It must be `Channel-level reconstruction anomaly — Event N`.
- 1.2.3 Is the baseline recomputed on read, or only when the subject is processed again?

### 1.3 Architecture (checks Figure 2.6 and Chapter 2 §2.5.1)

- 1.3.1 List the components as built: frontend framework, backend framework, database, background
  processing (queue or worker), file storage, authentication. One line each, with version.
- 1.3.2 Does the whole application run on one machine inside a local network, with no component
  calling an external service? List **every** outbound network request made at runtime (fonts, CDNs,
  telemetry, update checks), or state that there are none and how that was checked.
- 1.3.3 Does anything in `web_demo/UI/` or the current architecture differ from what Figure 2.6 shows
  (the application recomputes scores on the continuous recording, keeps every window, and never reads
  annotations, a label-based timeline, or the pre-split interictal and ictal arrays)? Project 1 will
  send the current Figure 2.6 through Boti if needed.

### 1.4 Functions, for the §3.5.1 text

For each user-facing function, two to four factual sentences on what it does and how a reviewer uses
it: sign-in; recording import and processing (what the user sees while a file is processed); the
detection timeline (how AI events are drawn, navigation, playback speeds 1x/2x/4x/8x, the EEG view);
event review (Accept, Reject, Uncertain, and adding a Human event); the channel panel; any export.
Also list anything specified but **not** built, and any known defect at the frozen tag. This feeds the
"status at submission" sentence in Chapter 4 §4.4 and Chapter 5.

---

## Part 2 — Screenshots (Figure 3.6, Chapter 3 §3.5.1)

The report has one figure for the application, Figure 3.6, which Project 1 assembles as panels. Please
provide separate PNGs from the frozen build:

| File | Screen | Content |
|---|---|---|
| `fig3_6a_import.png` | Import and processing | A recording being added and processed, showing progress |
| `fig3_6b_timeline.png` | Detection timeline | One full test recording with its AI events on the timeline and the EEG view |
| `fig3_6c_channel_panel.png` | Channel panel | The channel-level reconstruction-anomaly panel for one event, with its title visible |
| `fig3_6d_review.png` (optional) | Review | An event being accepted, rejected or marked uncertain |

Requirements: a test patient only; recording **chb13_62** if possible, because Figure 3.3 of the report
shows the offline pipeline on that recording and the two can then be compared; at least 1600 px wide;
light theme; no browser chrome; no calendar date anywhere; no metric of any kind. State which recording
and which event each screenshot shows.

---

## Part 3 — The second evaluation tier (Chapter 3 §3.5.2, Table 3.7, Chapter 4 §4.4)

The application's own detections on the eight test patients are compared with the annotation by Project
1. Project 2 produces the detections and exports them; it does not score them. Rules fixed before the
run (instructions §11.5):

- 3.1 **Clean database.** Start from an empty database holding only the eight test subjects, chb03,
  chb06, chb13, chb14, chb15, chb16, chb17, chb18, processed from their EDFs with the frozen build. No
  synthetic files, no events left from build testing. State how the database was emptied.
- 3.2 **Every EDF** in `F:/Study/Thesis/Dataset/CHB-MIT/chbNN/` for each of the eight subjects, not
  only the files containing seizures. Report the file list per subject with the duration of each file
  in seconds (from the EDF header, not a calendar time), and any file that failed or was skipped, with
  the reason.
- 3.3 **Export**, one CSV per subject, `web_demo/report_handback/tier2/{subject}_events.csv`, columns
  exactly:

  ```
  subject,file_name,event_id,onset_s,offset_s,source,review_status
  ```

  `onset_s` and `offset_s` are seconds relative to the start of that EDF file; `source` is `AI` or
  `Human`; `review_status` is whatever the database holds (the scorer ignores it). Every AI event the
  application produced, **before any review**. No calendar date. Also export
  `web_demo/report_handback/tier2/files.csv` with columns `subject,file_name,duration_s,n_windows,status`.
- 3.4 **Do not review events before exporting**, and do not add Human events during this run. If the
  export must be taken after review for technical reasons, say so; the scorer will keep every AI event
  regardless of status.
- 3.5 Report the count of AI events per subject as a sanity figure. No other number about the detections.

Project 1 will then join the exports to the annotation with the SzCORE scorer in `src/`, with the
false-alarm denominator equal to the recorded time of the processed files minus seizure time.

---

## Part 4 — Processing time (Chapter 2 §2.5.2, Chapter 4 §4.4, Table 3.8 rows 7 and 8, Table A.10)

The report currently says 9.76 s per hour of EEG, measured once, end to end on one four-hour recording,
with one stage varying about fivefold between runs. Instructions §11.5 require the figure to be measured
on the frozen build, per stage, over repeated runs, and reported as a median with its range. The three
places in the report that carry it change together.

- 4.1 **Hardware and software.** CPU model (`wmic cpu get name`), core and thread count, RAM, operating
  system, Python version, PyTorch version and device (confirm CPU, no CUDA). State whether other
  programs were running.
- 4.2 **Repeated runs.** Process the same reference recording at least **five** times on the frozen
  build (the four-hour recording used for the 9.76 s figure; name it). For each run, the wall time of
  every stage (reading and filtering; windowing and normalization; adjacency and band powers; model
  forward pass and the three scores; per-channel scoring; fusion; change point detection; database
  write) and the total. Save as `web_demo/report_handback/timing_repeated.csv` with one row per run and
  stage.
- 4.3 **Full-run log.** From the Part 3 run, the per-file stage times and the file duration, as
  `web_demo/report_handback/timing_tier2.csv`. This gives the time per hour of EEG over all test files.
- 4.4 Report the median and range of seconds per hour of EEG for each stage and for the total, from
  4.2 and from 4.3 separately, and the command that computed them.
- 4.5 Peak memory during processing, if it can be measured (for example with `psutil`); otherwise
  "not measured". Table A.10 currently lists peak memory and energy as not measured.
- 4.6 Confirm that `web_demo/CLAUDE.md` no longer states "~15 s/hour" (flagged 2026-09-25; the figure
  is forbidden). If it still does, correct it.

---

## Part 5 — Response template for `web_demo/REPORT_HANDBACK.md`

```markdown
# SzScan — handback to the report project

## 0. Frozen build
- Tag / commit:
- test_guards.py output: (paste)
- verify_provenance verdict:
- Checkpoint path and where it is set:

## 1. As built
### 1.1 Detection path
- 1.1.1 Divergences (a), (b), (c): implemented as stated? file:function for each
- 1.1.2 Every other difference from the thesis pipeline: (list, or "none found after checking: …")
- 1.1.3 Multiple files per subject:
- 1.1.4 Operating point parameters, with file:line:
### 1.2 Channel panel
- 1.2.1 Implementation, quoted with surrounding lines:
- 1.2.2 Panel title:
- 1.2.3 Baseline recomputed when:
### 1.3 Architecture
- 1.3.1 Components and versions:
- 1.3.2 Outbound network requests at runtime:
- 1.3.3 Differences from Figure 2.6:
### 1.4 Functions
- (one short paragraph per function)
- Specified but not built:
- Known defects at the frozen tag:

## 2. Screenshots
- (file → recording, event, what is shown)

## 3. Tier 2 run
- Database emptied how:
- Files per subject, failures and skips:
- Export paths:
- AI events per subject:
- Reviewed before export? (should be "no")

## 4. Timing
- Hardware and software:
- Reference recording:
- Repeated runs, per stage: median [min, max] s per hour of EEG
- Full tier-2 run, per stage: median [min, max] s per hour of EEG
- Commands used:
- Peak memory:
- CLAUDE.md "~15 s/hour" corrected?

## 5. Anything else the report should know
```

---

## Where each answer goes in the report (for reference)

| Answer | Report location |
|---|---|
| 1.1, 1.2 | Chapter 2 §2.5.2 (the three divergences; the per-channel baseline clause is added to the first) |
| 1.3 | Figure 2.6, Chapter 2 §2.5.1, requirement 9 of Table 3.8 |
| 1.4, Part 2 | Chapter 3 §3.5.1 and Figure 3.6; status sentence in Chapter 4 §4.4 and Chapter 5 |
| Part 3 | Chapter 3 §3.5.2 and Table 3.7; the [PENDING] paragraph of Chapter 4 §4.4; Goal 4 of Table 3.8 |
| Part 4 | Chapter 2 §2.5.2, Chapter 4 §4.4, requirements 7 and 8 of Table 3.8, Table A.10 |
