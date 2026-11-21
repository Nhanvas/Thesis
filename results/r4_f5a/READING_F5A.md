# READING_F5A — why the change point localizer improves onsets but not offsets (Track F, chat D36-F, 21/11/2026)

Design `DESIGN_F5A.md` (Part A approved 02:37, Part B §10 approved 12:43; written before every run; §9 = one rule
changed before any output, found by the synthetic test). Tables: `aggregate/T_F5A.md` (Part A, V5) and
`cv_aggregate/T_F5A_CV.md` (Part B, CV models). Runs: `v5/` (`F5A_V5`, measured 0.323 h) and `cv/` (`F5A_CV`, measured
0.455 h); every run gate and every aggregate gate PASS. No training. Patient bootstrap B = 10,000, rng 0, chb01 + chb21
one unit; [95 % interval]; seconds. Reading by the patterns fixed in the design (no pass / fail threshold).

## 1 · Part A — V5 (four checkpoints, defense-time data)

**Verification (V1–V2).** Matched pairs and medians reproduce V5 Table 10 exactly on development and test (247 / 103 /
146 pairs); chb24 and Siena from the rebuilt external features (54 / 117 pairs against 53 / 116; same medians).
- Onset: localizer − detector median |onset| development −12 [−12, −4], test held-out −20 [−28, −8], test final −20
  [−28, −8], Siena −16 [−24, −4] → a measurable gain on every set with an interval.
- Offset: localizer − detector median |offset| development −8 [−20, +4], test held-out +4 [−6, +20], test final +4
  [−4, +16], Siena 0 [−8, +24] → **no measurable change on any set**; Table 10's "20 → 24 s" is not a measurable
  worsening.
- What is measurable is a shift later: localizer signed offset +16 [+8, +36] on test final (share late 0.72 against
  0.44 for the detector), +16 [+4, +36] held-out, +20 [+4, +128] Siena, +4 [−4, +20] development (all matched pairs).
- Detection: the localizer changes sensitivity by −0.010 [−0.032, 0.000] on development and −0.003 on test, with
  0.5–2.3 fewer FP/day; the hybrid's offset is 4–8 s shorter than the localizer's (intervals include 0).

**Hypotheses (H1–H7).**

| # | explanation | result |
|---|---|---|
| H1 | the score keeps a post-ictal tail and the 2nd change point follows its end | **partly supported**: return − null of x development +7 [+2, +17], Siena +5 [+2, +10], test +3 [0, +8]; ρ(offset error, return time) test final +0.50 [+0.13, +0.79], held-out +0.60 [+0.01, +0.83], Siena +0.43 [+0.03, +0.75], development +0.19 [−0.05, +0.39]; end − return point 0 [0, +8] on test final; share of ends nearer the return point 0.51 [0.36, 0.65] (not above 0.5) |
| H2 | the post-ictal change is in the EEG itself | **supported on development and Siena**: return − null of δ power development +8 [+4, +20], Siena +16 [+4, +38], test +4 [0, +36]; line length development +16 [+4, +28], test 0 [0, +4]; median curves: δ power raised for 3 min after the offset on development, test and Siena; line length below background after the offset on development (post-ictal suppression) |
| H3 | three states, two change points | **contradicted**: a 3rd change point makes the offset worse (2nd point − record +20 [0, +40] development, +16 [−8, +28] test final) |
| H4 | too little background in the search window | **contradicted**: ends at the window edge ≤ 4 %; margin 30 moves the end later (+4 [0, +24] development), not earlier |
| H5 | "seizures fade out gradually" (defense slide) | **contradicted for the score**: fall − rise 0 [−1, +4] test, +1 [0, +9] development, +3 [+1, +14] Siena; the score drops abruptly at the offset to a lower level |
| H6 | special cases of the construction | **no stratum explains test**; without merged-run events development's difference becomes 0 |
| H7 | a few seizure-rich patients | **true for development**: −8 pair-weighted, 0 patient-weighted; test +4 / +10 (same direction); the 2 largest test patients hold 47 % of the pairs |

**Median curves (computed from `aggregate/D3_median_curves.csv`, descriptive).** In the 60 s after the annotated offset
the score keeps 59 % (development), 62 % (test) and 81 % (Siena) of its seizure level above the pre-onset median, and is
still raised at 120–180 s on development and Siena; the per-seizure return time (back inside the pre-onset 5th–95th
percentile band for 3 windows) is short because the band is wide, so it understates this lower, longer elevation.

## 2 · Part B — 48 CV checkpoints (GAE, MLP-AE; partitions 0–5; complete data, 24 cases out of fold)

Committed k (48 / 48) and per-subject rows and caught flags reproduced exactly.
- **HB1 (general, not message passing) — supported.** Localizer signed offset > 0 in 6 / 6 partitions for both models
  (+4 to +8 s); localizer − detector |offset| GAE 0 [−4, +8], MLP-AE +4 [−6, +8]; onset −8 [−12, −4] for both;
  detection −0.003 sensitivity for both.
- **HB2 (GAE-specific part) — none in the direction of the GAE.** GAE − MLP-AE paired by patient: localizer signed
  offset −0.8 [−7.4, +6.4]; |offset| change +2.9 [−6.7, +14.0]; the MLP-AE's post-offset tail is longer and higher
  (return − null, patient means, −17.5 [−31.8, −5.6]; level 0–60 s after the offset −0.046 [−0.089, −0.002]).
- **HB3 (V5's mechanism repeats) — supported.** ρ(error, return) GAE +0.39 [+0.22, +0.52], MLP-AE +0.25 [+0.11, +0.39];
  end − return point 0; level after the offset ≈ half the seizure level (median ratio 0.58 GAE, 0.49 MLP-AE); a 3rd
  change point +12 to +16 s worse, margin 30 +4 s later; fall − rise GAE +1 [0, +5], MLP-AE +7 [+4, +10].
- Model-free series on the complete data: δ power +8 [0, +20], line length +4 [0, +16] (weaker than on V5's sets).

## 3 · Answer (for the Q&A of 11/12; the wording is Track C's)

The change points help the onset because the detector's onset is late (+16 to +36 s, from the 5-window smoothing and a
high threshold) while the score rises abruptly when a seizure starts. At the offset the detector is already on time;
the score does not return to background but drops to about half its seizure level and stays raised through the
post-ictal period — a change that is also visible in the EEG's δ power without any model — so the second change point
lands about 16 s after the annotation, later when the post-ictal state lasts longer. The net offset error is neither
better nor worse in a measurable way. The same holds for an autoencoder without message passing, so it is not a GAE
effect.

**Wording limits.** "Post-ictal" = the period after the annotated offset; whether the annotation or the score's return
is the clinically right end is not measured (one annotation per seizure). Development includes the 12 training
patients; test, chb24 and Siena are descriptive. The interventions (3 change points, margin 30) are diagnostics, not a
localizer rule (O2 closed; a new offset rule belongs to F5b after 11/12). Never "the localizer makes offsets worse" and
never "seizures fade out gradually".

## 4 · For F5b (after 11/12)

The detector's own offset is unbiased and the run rule (hybrid) is 4–8 s shorter (intervals include 0). A family that
models the post-ictal level (or ends at the score's first drop rather than at its return to background) is what the
diagnosis points to; selection by nested CV over the 6 partitions × 2 models (plan §8.2). `cv/events.csv`,
`cv/series.csv.gz` hold every pair and the score around it (± 30 windows), enough for score-based families without
rescoring; multichannel families need the per-channel distances (a new run).
