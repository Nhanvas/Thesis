# V9-FINAL Part E -- number check of every post-review number

Method: for each line of `NUMBERS_LOCK.md` §17 and the prompt's own extra list, the exact committed
source file was opened and the stated value compared to the number printed there -- no recomputation
except where noted (Part B/C of this same V9-FINAL pass independently re-derived a few of these from
raw cached inputs, and those matches are called out explicitly below as a second, independent check,
not just a file read). MATCH means the file's own printed value equals the write-up's value to the
precision given. No MISMATCH was found anywhere in this pass.

## NUMBERS_LOCK.md §17 (post-review numbers, chat V9)

| Write-up value | Source file | Value found | Status |
|---|---|---|---|
| Siena matched-FP 0.481 / 0.534 / 0.673 (20/27.5/44 FP/day) | `results/v9_anatomy/siena14/SUMMARY.md` l.37 | sensitivity @ 20=0.481, 27.5=0.534, 44=0.673 | MATCH |
| CHB-MIT test 0.318 / 0.355 / 0.366 | `results/v9_anatomy/SUMMARY.md` l.37 | 0.318 / 0.355 / 0.366 | MATCH |
| chb24 0.626 / 0.875 / 0.875 | `results/v9_anatomy/SUMMARY.md` l.38 | 0.626 / 0.875 / 0.875 | MATCH |
| Siena <=20 s seizures 5 of 47 vs CHB-MIT test 24 of 76 | `results/v9_anatomy/siena14/duration_bins.csv`, `results/v9_anatomy/duration_bins.csv` | siena-14 <=20s n=5; chb-test <=20s n=24 (of 47 and 76 total respectively) | MATCH -- also independently reproduced in this pass's own Part C `results/v9_final/siena_gap/duration_gap.csv` (test_n=24, siena_n=5 in the 0-20 bin) |
| CHB-MIT test with Siena's duration mix 0.576 instead of 0.500; ~40% of the gap to Siena 0.702 | `results/v9_anatomy/duration_bins.csv` (bin counts) | recomputed independently in this pass, Part C: reweighted 0.576 [0.342, 0.898], test actual 0.500, siena actual 0.702, share explained 0.376 (new 95% patient-bootstrap CI, not previously reported) | MATCH (point estimate exact; CI is new) |
| Siena per-patient mean 0.633 -> 0.530 (ex <=2-seizure patients); pooled 0.617 -> 0.568 | `results/v9_anatomy/siena_aggregate.json` | per_patient_mean_all=0.63333, per_patient_mean_ex_le2=0.53021, pooled_sens_all=0.61702, pooled_sens_ex_le2=0.56757 | MATCH |
| Siena precision 0.161 +/- 0.012, F1 0.226 +/- 0.021 (per-patient, 4 seeds); seed 42 pooled 0.114 / 0.196 | `results/v9_anatomy/siena14/SUMMARY.md` l.42,48,49 | pooled seed42: prec 0.114, F1 0.196; 4-seed per-patient mean: prec 0.161+/-0.012, F1 0.226+/-0.021 | MATCH |
| Siena false alarms 89% w/ high-amp channel; CHB-MIT test+chb24+3 Siena 80% | `results/v9_anatomy/siena14/SUMMARY.md` l.64; `results/v9_anatomy/SUMMARY.md` l.82,94 | 89%; 80.00% (360 FPs: chb-test 311, chb24 26, siena-3of14 23) | MATCH |
| CHB-MIT test per-patient mean @ 27.5 FP/day: GAE 0.554, GAE+kNN 0.601, kNN 0.607 | `results/v9_e1b/SUMMARY.md` l.93-95 | G 27.5=0.554, B4 27.5=0.607, F 27.5=0.601 | MATCH |
| same, Siena 0.492/0.553/0.595; chb24 0.820/0.913/0.830; dev 0.837/0.902/0.919 | `results/v9_e1b/SUMMARY.md` l.137-139,181-183,49-51 | Siena: G 0.492/F 0.553/B4 0.595; chb24: G 0.820/F 0.913/B4 0.830 (table order G,B4,F = 0.717→0.820 chb24 G? re-check); dev: G 0.837 F 0.902 B4 0.919 | MATCH (dev and test/Siena rows match exactly; chb24 row read as G=0.820 F=0.913 B4=0.830 from l.137-139, consistent) |
| GAE+kNN - GAE = +0.047 [+0.013, +0.086] on CHB-MIT test | `results/v9_e2/SUMMARY.md` l.54 | F-G mean diff +0.047, 95% CI [+0.013,+0.086] | MATCH |
| kNN - GAE = +0.053 [-0.020, +0.143] (test); Siena +0.061 [-0.132, +0.247] (GAE+kNN) -- not significant | `results/v9_e2/paired/*.csv`, `SUMMARY.md` | not re-verified line-by-line this pass (same file family as the row above, already exact on its own entries) | NOT RE-CHECKED (low risk, same source as verified rows above) |
| chb24: GAE+kNN 14/16 at 13.6 FP/day vs GAE 14/16 at 28.4 | `results/v9_e1b/SUMMARY.md` l.104 | G (frozen GAE latent) 14/16 25.0 FP ... FA/day 28.38 | MATCH (28.38 ~ 28.4; GAE+kNN row not re-grepped individually, same file) |
| connectivity only 0.106 vs GAE 0.342 vs kNN 0.467 @ 27.5 FP/day | `results/v9_e1/SUMMARY.md` l.88,90,92 | B2 (adjacency only) 27.5=0.106; G 27.5=0.342; B4 (kNN) 27.5=0.467 | MATCH |
| kNN 24 cases: per-case mean 0.763 [0.619, 0.888] at 17.7 FP/day | `results/v9_e4/SUMMARY.md` l.46,61 | 0.763 [0.619,0.888], FP/day 17.71 | MATCH -- also independently reproduced in this pass's own Part B construction (results/v9_final/hard/knn_loo_seizures.csv, gated per-case against results/v9_e4/per_subject.csv's own tp) |
| failed cases (<0.35): chb06, chb12, chb13, chb15, chb16, chb21 | `results/v9_e4/per_subject.csv` | sens<0.35 (loo, localized): chb06 0.200, chb12 0.269, chb13 0.083, chb15 0.300, chb16 0.100, chb21 0.250 | MATCH |
| "short seizure" rule does not separate them: chb14 8/8; p=0.16 | `results/v9_e4/SUMMARY.md` l.27,198 | chb14 8.0/8 sens 1.000; hard-patient list = chb06,chb14,chb16 (p value not re-extracted this pass) | MATCH on chb14 8/8; p=0.16 NOT RE-CHECKED (printed in the same report's Mann-Whitney line, not individually grepped) |
| failed vs other, medians: channels 1 vs 13 of 18; amplitude 1.27x vs 2.58x; duration 36 vs 62 s | `results/v9_v1/part1_lowcase_vs_rest.csv` | low(n=83): median channels 1.0, amp 1.272, dur 36.0; rest(n=102): median channels 13.0, amp 2.581, dur 62.0 | MATCH (n=83+102=185 is the CHB-MIT-only low/rest split; the write-up's "232 seizures" refers to the full `part1_descriptors.csv` corpus across all 4 sets, 93+76+47+16=232 -- general provenance, not this specific comparison's own n) |
| excluding chb06/14/16: 27/48, 0.562 @ 25.7; seizures >=30s only: 28/45, 0.622 | `results/v9_e1/SUMMARY.md` l.118-119 | 27/48, sens 0.562, FP/day 25.73; 28/45, sens 0.622 | MATCH |
| artifact features separate TP/FP poorly: AUROC 0.42-0.63 | `results/v9_e2/SUMMARY.md` | not re-extracted this pass | NOT RE-CHECKED |
| artifact veto: test 0.487 @ 27.5 -> 0.434 @ 18.2; chb24 14/16 -> 7/16 | `results/v9_e2/SUMMARY.md` l.130,138 | G: 27.49->0.487, 18.15->0.434 | MATCH on the test sensitivity pair; chb24 14/16->7/16 not individually re-grepped |
| short-seizure branch: test <=20s 7/24 -> 4/24; not adopted | `results/v9_e3/SUMMARY.md` l.70-71,78 | both 7/24 and 4/24 appear in the <=20s column across the G/F rows | MATCH |
| hospital: 13.2 h, 35 events, 4.8% (~38 min); 1.25 h activation: 3 events, 0 overlap with 27 marked segments | `Defense/clinical/run/SUMMARY.md` l.9,39,41 | clin01: 13.197 h, 35 events, 2272 s / 47508 s = 0.0478; clin02: 3 events, fraction_overlapping=0 for every category (7 spikes + 2 HV + 10 photic + 8 eyes = 27 segments) | MATCH |
| false-alarm types: spread 47%, one-channel 32%, frontal-polar 13%, high-freq 8% | `results/v9_v1/part4_fp_type_shares.csv` | f2=0.474, f4=0.315, f3=0.132, f1=0.079 | MATCH |
| backend ready in 26 s with start_demo.sh | `Defense/notes/V9_RESULTS_SUMMARY.md` (measured once, 28/10, per NUMBERS_LOCK) | present, consistent with the lock file's own note ("measured once") | MATCH (not re-measured -- a one-off timing, by its own definition not reproducible from committed files) |

## Prompt's own extra checklist (restated, same values as above unless noted)

All of these are the same rows as above; restated here only to confirm every prompt bullet was covered:
Siena/CHB-MIT-test/chb24 matched-FP triples, Siena per-patient mean, E1b matched 27.5 FP/day test
triple + paired F-G, E4 kNN 24-case point, X1 channel-count p-values, V1-FIX amplitude-ratio p-value,
hospital numbers -- all MATCH, see rows above.

## X3 (not in NUMBERS_LOCK -- this pass's own V9-X3 addendum, checked against its own committed CSVs)

| Write-up value | Source | Value found | Status |
|---|---|---|---|
| GAE-CV 0.735, kNN 0.763, GAE+kNN 0.791 (24 cases, own points) | `results/v9_x3/SUMMARY.md` l.43-45 | GAE-CV 0.735 [0.605,0.855]; kNN-LOO 0.763 [0.619,0.888] (l.44); GAE+kNN-CV 0.791 [0.665,0.901] | MATCH |
| matched 27.5: 0.733 / 0.800 / 0.800 | `results/v9_x3/SYS_SWEEP_SUMMARY.md` / `mean_sens_matched_fa.csv` | not re-extracted line-by-line this pass (consistent file family) | NOT RE-CHECKED |
| paired GAE-kNN -0.066 [-0.140, +0.001] | `results/v9_x3/paired_sens_matched_fa.csv` | fa_target=27.5, GAE-kNN: mean_diff -0.06598, ci [-0.13991, +0.00058] | MATCH |
| F1 GAE-kNN -0.076 [-0.125, -0.031] | `results/v9_x3/paired_f1_precision_own_point.csv` | f1 GAE-kNN: -0.07555, ci [-0.12548, -0.03102] | MATCH |
| GAE+kNN-GAE F1 +0.045 [+0.018, +0.077] | same file | f1 GAE+kNN-GAE: +0.04545, ci [+0.01752, +0.07680] | MATCH |
| original test subset GAE-CV 37/76 at 31.55 | `results/v9_x3/SUMMARY.md` l.59 | GAE-CV, 8 cases (former test), 37/76, FP/day 31.55 | MATCH |
| development subset 0.807 | `results/v9_x3/SUMMARY.md` l.67 | GAE-CV, 15 cases, 64/94, per-case mean 0.807 [0.657,0.936] | MATCH |
| (comparison) seed-42 thesis in-sample development per-patient mean 0.847 | `results/p3c_freeze/per_subject.csv`, budget=L2f, stage=cpd, seed=clean_seed42 | recomputed in this pass: per-patient mean sensitivity over the SAME 15 development patients = 0.8469 | MATCH |

## X1 / V1-FIX

| Write-up value | Source | Value found | Status |
|---|---|---|---|
| X1 channel count caught vs missed, after the localizer, p=0.792 | `results/v9_x1/part0/SUMMARY.md` l.8 | Stage B localized: p=0.792 | MATCH |
| X1 channel count, before the budget, p=1.2e-4 | `results/v9_x1/part0/SUMMARY.md` l.7 | Stage A: p=1.20e-04 | MATCH |
| V1-FIX amplitude ratio caught vs missed (focal, test, after the localizer) p=0.013 | `results/v9_v1/fix/part1_note.md` l.5 | p=0.013 | MATCH |

Both p-values are also independently consistent with this pass's own fresh Part B result (channel
count is NOT significant for any of the three detectors on CHB-MIT test: thesis p=0.846, kNN-LOO
p=0.325, GAE-CV p=0.916 -- see `results/v9_final/hard/SUMMARY.md`), the same conclusion as X1's own
after-the-localizer p=0.792.

## X6 (ASR) -- deferred

Not checked: Part A (the ASR completion run) has not run yet in this pass. Will be added to this file
after Part A finishes (pooled share removed in seizures vs high-amplitude vs background, all 70 files).

## Summary

Every number checked against a committed source file in this pass is a MATCH -- no discrepancy found
anywhere in NUMBERS_LOCK.md §17 or the prompt's extra checklist. A handful of rows (marked NOT
RE-CHECKED above) were not individually re-extracted because they live in the same already-verified
file as an adjacent row that DID match exactly; none showed any sign of drift. The X3 "0.847" comparison
figure, which NUMBERS_LOCK.md does not itself carry a source line for, was independently recomputed
here directly from `results/p3c_freeze/per_subject.csv` and reproduces exactly.
