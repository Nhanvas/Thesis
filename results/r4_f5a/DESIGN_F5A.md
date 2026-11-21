# DESIGN_F5A — offset verification and diagnosis on V5 (Track F, chat D36-F)

**Approved by the author 21/11/2026 02:37** (proposal of 02:09, chat D36-F). Written **before** any F5a output.
Plan `FUTURE_RESEARCH_PLAN.md` §8.1 (F5a), adapted as stated in §1. No training. Result → Q&A of 11/12 and the basis
of F5b after 11/12; no number of the Euréka deliverables changes (freeze 22/11).

## 0 · Question

Why does the change point localizer of V5 improve the onsets on every set but not the offsets (V5 Section 3.2,
Table 10: median |offset| detector → localizer: development 24 → 16 s, test held-out 16 → 20, test final 20 → 24,
chb24 8 → 4, Siena 28 → 28)? The defense slide explains it by "seizures fade out gradually"; that sentence has not
been measured (H5 below measures it).

**Seen before this design (disclosed):** Table 10 of V5; the signed medians of `results/eureka_d31f/abl/errors.csv`
(V0, read while opening the file): localizer offset +16 s (test final), +20 (Siena), +4 (development), 0 (chb24);
detector offset −4 … +8 s; hybrid ≈ 0. No interval and no diagnostic was computed before this design.

## 1 · Data, system, arms (change to plan §8.1)

- **System = V5** (`data/models_v2/gae_v2_clean_seed{42,1,2,3}.pt`, the defense-time data copy `v9-x3-fold1/3`, the
  external features `thesis-r2-external-features`, k = 4.0677), not R1: the Euréka council sees V5's numbers. R1
  (path 2) is parked (plan §14). The CV models of R2 / R3 (GAE and MLP-AE, 6 partitions) are **Part B**, a later step
  of this chat, designed after Part A's reading.
- Arms: **own** = the final system (clip(q, 0.005, 0.02), record arm L2f) and **fixed** = 0.005 for every patient
  (record arm frozen). Sets and arms read: development own; test fixed (held-out) and own (final); chb24 own;
  Siena own. **Primary diagnostic sets: development own and test own.**
- Stages: detector boundaries; change point localizer (`e18_cpd_localizer.cpd_event`, kernel rbf, exactly 2 change
  points, min_size 2, on the unsmoothed scalar over the event ± 15 windows; fallback to the detector's boundaries);
  hybrid (L6 as coded, `p3_levers.localize`).
- Error pairs: `e18_cpd_localizer.match_errors` (each reference seizure matched by the first detector event that
  overlaps it within −30 / +60 s; the same pairs for the three boundary sets), as in Table 10.

## 2 · Verification (V) — from committed record files, no run

Source: `results/eureka_d31f/abl/` V0 (= V5 exactly on development and test, gates R1.0; external from the rebuilt
features within the GE tolerance, 54 / 117 pairs against Table 10's 53 / 116). The x1 record medians of chb24 and
Siena (`results/x1_external/errors_*.csv`, exactly Table 10) are printed beside as a check.

- **V1 detection:** per-patient sensitivity, F1, FP/day (4-seed means) of detector, localizer, hybrid; paired
  localizer − detector and hybrid − localizer; seizures lost / gained and false alarms changed (sums over seeds / 4).
- **V2 boundaries:** median |onset| and |offset|, signed median, IQR, share late (> 0) and early (< 0) for the three
  stages; paired differences of the median |error| (localizer − detector, hybrid − localizer).
- **Statistics:** patient bootstrap, B = 10,000, rng 0, chb01 + chb21 one resampling unit; medians by resampling units
  and pooling their pairs. No pass / fail threshold.

## 3 · Diagnosis (D1–D5) — from the run `F5A_V5` (§5)

- **D1 bias:** signed onset / offset errors per stage, set and arm (median, IQR, share late), and per patient.
- **D2 where the error comes from:** |offset| and signed offset error of localizer and detector by stratum — localizer
  accepted vs fallback; detector event > 300 s; detector event made of ≥ 2 above-threshold runs merged at 90 s; event
  covering ≥ 2 reference seizures; reference duration < 20 s, 20–60 s, 60–300 s, > 300 s. Counts per stratum; for
  each stratum, localizer − detector |offset| in the pairs that remain without it.
- **D3 post-ictal profile — every annotated seizure with a valid span** (not selected by detection; the caught subset
  beside). Series per window: **x** = the unsmoothed final scalar (what the localizer sees), **m** = member-mean robust
  z (the budget signal), and **model-free** series from the node features of the cache (f7): log line length, the five
  log band powers (δ θ α β γ) and the log total power — per channel robust z over the patient's valid windows
  (median / 1.4826 MAD, no labels), mean over the 18 channels.
  - Pre-onset reference: valid non-ictal windows in [onset − 300 s, onset − 60 s); ≥ 30 of the 60 windows required.
  - **Return time** (R4-c, band changed before any output — see §9): the first window start t ≥ annotated offset from
    which the series stays inside the pre-onset **5th–95th percentile band** for **3** consecutive valid windows (2 and
    5 reported beside); return time = t − offset; censored at +180 s (value 180, flagged). **Null value:** the same rule
    started at the beginning of the pre-onset reference (onset − 300 s), i.e. what the statistic gives in background
    without a seizure; H1 / H2 are read on return − null.
  - **Rise / fall time:** baseline b = pre-onset median, peak p = maximum over the annotated seizure; levels b + 0.1
    (p − b) and b + 0.9 (p − b). Rise = first window ≥ 90 % in [onset − 60 s, offset] minus the last window ≤ 10 % before
    it (searched back to onset − 120 s). Fall = first window ≤ 10 % after the last window ≥ 90 % in [onset, offset +
    60 s], minus that last window (censored at offset + 180 s). Undefined if p ≤ b (counted).
  - Median curves (series − pre-onset median) from −120 to +180 s around the offset and around the onset (control),
    per set; seizure-weighted and patient-weighted.
  - **Exclusions:** span [onset − 300 s, offset + 180 s] outside the file, or overlapping another seizure's
    [onset, offset + 180 s]; excluded seizures are counted.
- **D4 where the localizer puts the offset** (matched pairs, localizer accepted): signed offset error; distance of the
  localizer's end to the return point (offset + return time of x, same seizure and seed); share of pairs whose end is
  nearer the return point than the annotated offset; within-patient Spearman ρ (values centred on each patient's
  median) between the signed offset error and the return time; share of ends in the last 2 windows of the search
  window ("edge").
- **D5 diagnostic interventions** (not a localizer rule: O2 is closed and any new offset rule belongs to F5b, selected
  by nested CV after 11/12). On the same pairs and the same search window: (a) **3 change points** (same kernel and
  preparation) → offset errors of the 2nd and 3rd change points; (b) **margin 30 windows** with 2 change points
  (`cpd_event` with margin 30) → offset error. Run on every set, read on development; paired differences against the
  record localizer with the patient bootstrap.

## 4 · Hypotheses and the patterns that support or contradict each (fixed now; no threshold)

| # | explanation | supported if | contradicted if |
|---|---|---|---|
| H1 | the score keeps a post-ictal tail and the localizer's 2nd change point follows its end | D3 return − null of x > 0 (interval above 0) **and** D4 ρ(signed offset error, return time) > 0 (interval above 0) **and** share of ends nearer the return point > 0.5 (interval above 0.5) | return time ≈ 0, or ρ ≤ 0 |
| H2 | the post-ictal change is in the EEG itself (model-free) | D3 return − null of log line length or log δ power > 0 (interval above 0); ρ(return time x, return time line length) > 0 | model-free series back inside the pre-onset band at the offset while x is not (then the tail is made by the model) |
| H3 | three states (pre, seizure, post-ictal) but two change points | D5a: median \|offset\| of the 2nd change point < the record localizer's (paired interval below 0) and the 3rd change point nearer the return point than the 2nd | 2nd change point of D5a no nearer the offset |
| H4 | the search window has too little background after the event | edge share high; D5b moves the signed offset error (paired interval excludes 0) | edge share small and D5b unchanged |
| H5 | "seizures fade out gradually": the score falls slowly and rises fast | fall − rise of x > 0 (interval above 0) and ρ(signed offset error, fall time) > 0 | fall ≈ rise |
| H6 | special cases of the construction (D2) | localizer − detector \|offset\| ≤ 0 once one stratum is removed | no stratum changes it |
| H7 | the set differences come from a few seizure-rich patients | patient-weighted medians differ from the pair-weighted ones in direction; 2 patients hold most pairs | same direction in both weightings |

Several explanations may hold at once; the reading states each pattern as measured. The literature context (offset
annotation less reliable than onset) is not testable with one annotation per seizure and is stated as context only.

## 5 · Run `F5A_V5` (Kaggle CPU, Internet on, inputs `v9-x3-fold1`, `v9-x3-fold3`, `thesis-r2-external-features`)

`src/r4_f5a.py` imports every record module read only through `r2_r1` (as the EUR suite does, without importing it).
1. G-data (sha256 of the earlier caches = `docs/PROVENANCE_V2.md`; external = R1_SMOKE's pin).
2. SMOKE on chb01, chb03, chb24: `r2_r1.r10` (R1.0 / GE rows) and the extraction; measured → projection (STOP > 10.5 h).
3. Full: `r2_r1.r10` on every case (R1.0-dev, R1.0-test, GE, G-k), then the extraction per case and seed: for both
   arms, `p3c_freeze.run_budget` (record) and, from the same quantities, every matched pair's event record
   (boundaries, localizer accepted, search window, above-threshold runs, references covered, hybrid / run rule) and,
   per annotated seizure, the per-window series of §3 over [onset − 300 s, offset + 300 s] extended to cover each
   matched event ± 30 windows (inside the file).
4. Gates: **G-eng** (the extracted boundaries and errors = `run_budget`'s, exactly, every pair), **G-seg** (every
   search window ± 15 more windows lies inside its stored segment), **G-mf** (model-free series finite on valid
   windows), **G-worker-sha** (every job ran the reviewed modules).
Outputs `WORK/r4/f5a_v5/` → `results/r4_f5a/v5/`: run_meta.json, gates.json, data_sha256.csv, r10/, events.csv,
seizures.csv, series.csv.gz (derived per-window values only, no EEG), jobs.csv, projection.json, SUMMARY.md.
Runtime ≈ 0.3–0.6 h (computed from EUR_ABL 0.868 h for 18 variants and R1_RUN's 0.42 h; the smoke measures it).

## 6 · Aggregate `src/r4_f5a_aggregate.py` (committed before the run)

A0 every run gate PASS; A1 completeness (every case × seed × arm); A2 the run's error pairs = `abl/errors.csv` V0,
exactly; A3 the localizer boundaries and the run-rule boundaries recomputed from the stored series = the run's,
exactly, every pair. Then V, D1–D5, the H table and figures from the committed tables →
`results/r4_f5a/aggregate/` (T_F5A.md and CSVs).

## 7 · Synthetic test `src/r4_f5a_synthetic_test.py`

S1 the notebook end to end on the synthetic world of `r2_r1_synthetic_test` (every gate PASS; outputs; aggregate
A0–A3 PASS). S2 planted worlds for the analysis functions: a post-ictal plateau (return time and the 2-change-point
end follow the plateau; the 3-change-point 2nd point recovers the offset), an abrupt symmetric seizure (return ≈ 0,
end ≈ offset), a slow ramp (fall ≫ rise). Negative paths: a changed record row → STOP R1.0-dev; an edited module →
the notebook refuses to start; an altered stored series value → A3 FAIL.

## 8 · Real-EEG panels (rule R4-e, fixed now; drawn later only if the author asks)

Per set, final arm, seed 42: the matched seizure with the median late localizer offset error and the one with the
largest late error; drawn on the laptop from the raw EDF with the deck's style.

## 9 · Changes after approval, before any output (logged)

- **21/11 (D36-F), return-time band.** The synthetic test showed that the approved rule ("inside the pre-onset
  interquartile range for 3 consecutive windows") is met by chance only 1 time in 8 per window even in pure background
  (each window is inside an IQR with probability 0.5), so it reports long "return times" with no post-ictal tail (176 s
  on a planted 60-s plateau with white noise). Changed to the pre-onset 5th–95th percentile band (probability 0.9 per
  window) and a null value computed with the same rule in the pre-onset background; H1 / H2 read return − null.
  Seen at the change: synthetic data only.

## 10 · Part B — the CV models (approved by the author 21/11/2026 12:43; written before any Part B output)

**Question.** Do the two V5 findings — the localizer places the offset late, at the end of the score's post-ictal
elevation, and the offset error changes by no measurable amount — hold for both models and every patient partition,
or are they specific to the GAE (message passing)?
- **Models:** the 48 committed checkpoints, never retrained — GAE and MLP-AE × partitions 0–5 × 4 folds: partition 0 =
  R2_A (`results/r2/r2_cv/a/jobs`), partitions 1–5 = R3 (`results/r2/r3_repcv/p1–p5/jobs`); complete data
  `thesis-r2-chbmit-features`, 24 cases out of fold (≈ 185 seizures per partition). Arms own (the fold's k, as V5) and
  fixed 0.5 %. The partitions play the role of V5's seeds; patient bootstrap, chb01 + chb21 one unit.
- **Gates:** G-data, D0' (`r2_r2`); **G-k** (k recomputed = the job's committed `fit.json` k, relative 1e-6); **G-rows**
  (`f1_core.evaluate_case` rows of both points × detector / localized — tp, fp, n_ref — and the seizure caught flags =
  the committed `per_subject.csv` / `seizures.csv`, exactly); G-eng, G-seg, G-worker-sha as in Part A; smoke on fold 1
  of partition 0 (GAE and MLP-AE) first. Aggregate gates A0, A1, A3 (A2 has no counterpart: the CV record holds no error
  pairs; G-eng ties the extraction to the record rows instead).
- **Extraction and analysis:** as Part A (`src/r4_f5a_cv.py`, `src/r4_f5a_cv_aggregate.py`, which imports the Part A
  helpers unchanged): pairs, segments of x, model-free series once per case; V1, V2 (pooled and per partition), D3
  (return − null, fall − rise, and the level of x in the 60 s after the offset relative to the pre-onset median, alone
  and as a share of the seizure level), D4, D5.

| # | explanation | supported if |
|---|---|---|
| HB1 | the behaviour is general (not message passing) | for both models: localizer signed offset > 0 in ≥ 5 of 6 partitions; localizer − detector \|offset\| interval contains 0 or lies above 0; the onset gain holds |
| HB2 | an additional GAE-specific part | GAE − MLP-AE, paired by patient, in the localizer signed offset, return − null of x, or the level after the offset (absolute or relative to the seizure level): interval excluding 0 |
| HB3 | V5's mechanism repeats | for both models: ρ(offset error, return time) > 0, fall − rise ≈ 0, and neither 3 change points nor margin 30 brings the offset nearer the annotation |

Run `F5A_CV` (Kaggle CPU, Internet on, input `thesis-r2-chbmit-features`), outputs `results/r4_f5a/cv/`; runtime ≈ 0.4–0.6 h
computed from R3's measured scoring times (GAE 137–163 s, MLP-AE 50–76 s per fold; 48 jobs on 4 workers). Synthetic test
`src/r4_f5a_cv_synthetic_test.py`.
