# Application-vs-offline gap diagnostic -- SUMMARY

Read-only diagnostic (docs/CC_PROMPT_GAP_DIAGNOSTIC.md): nothing tuned, no setting of the
application or the thesis pipeline changed, the application not re-run. Test patients used
only to explain an already-scored result.

This run (`src/diag_application_gap.py`, seed=0 throughout) completed D0 and D1 in full, then
crashed while formatting this file, on a Windows console-encoding error in the D1-fail branch's
text (non-ASCII "rho"/">=" characters written without `encoding="utf-8"`). The bug is fixed in
`src/diag_application_gap.py` (all `write_text` calls now pass `encoding="utf-8"`, and the
offending characters were also replaced with ASCII). The run was not repeated: it is fully
deterministic (fixed seed, no randomness left unseeded) and D0/D1 had already produced their
complete, correct output on disk before the crash -- `d0.csv` and `d1.csv` in this directory are
that same run's actual output, recovered as-is; `run_log_D0_D1.txt` in this directory is that
run's captured stdout/traceback. D2, D3 and D4 were never started (D1 already failed).

## D0a -- offline reproduction (rlg, mag_pct=50, pen_mult=2.0)

Pooled: `{'tp': 47, 'fp': 318, 'n_ref': 76, 'fn': 29, 'sensitivity': 0.618, 'precision': 0.129, 'f1': 0.213, 'fp_per_day': 27.4, 'n_inter_h': 278.2}`

Expected (docs/RESULTS_OF_RECORD_phaseB.md): `{'tp': 47, 'fn': 29, 'fp': 318, 'sensitivity': 0.618, 'precision': 0.129, 'f1': 0.213, 'fp_per_day': 27.4}`

**D0a reproduction: PASS** (exact match on every field).

Per-subject D0a grid was not preserved for this exact run: `write_summary` only prints that
table inline in this file's text, and the crash happened before this file was ever written, so
it was lost with the process. It is not reconstructed here from a separate invocation, to keep
every number in this file traceable to `run_log_D0_D1.txt` / `d0.csv` / `d1.csv` from this one
run. Re-running `src/diag_application_gap.py` (now fixed) will reproduce it if needed.

## D0b -- timeline position accounting

| subject | timeline_positions | real_windows_from_edf | positions_minus_real_windows | reported_fa_denominator_h | recomputed_fa_denominator_h | reported_fp | recomputed_fp_per_day |
|---|---|---|---|---|---|---|---|
| chb03 | 34201 | 34201 | 0 | 37.883 | 37.883 | 39 | 24.707 |
| chb06 | 60060 | 60060 | 0 | 66.683 | 66.683 | 54 | 19.435 |
| chb13 | 29700 | 29700 | 0 | 32.840 | 32.840 | 32 | 23.386 |
| chb14 | 23400 | 23400 | 0 | 25.946 | 25.946 | 58 | 53.651 |
| chb15 | 36008 | 36008 | 0 | 39.437 | 39.437 | 45 | 27.386 |
| chb16 | 17100 | 17100 | 0 | 18.969 | 18.969 | 17 | 21.509 |
| chb17 | 18906 | 18906 | 0 | 20.924 | 20.924 | 23 | 26.381 |
| chb18 | 32070 | 32070 | 0 | 35.541 | 35.541 | 50 | 33.764 |

Pooled: timeline_positions=251445, real_windows_from_edf=251445, reported_fa_denominator_h=278.2,
recomputed_fa_denominator_h=278.2.

`build_timeline_masked`'s own position count (`len(signal)`) equals, per file and pooled, the
real-window count computed directly from each EDF's sample count (`floor(n_samples/1024)`) --
0 mismatch on every file, every subject. The timeline does not leave out any real window at the
position level; every ictal, buffer, and interictal window gets a slot, so a false alarm can
occur at any position on the timeline. The recomputed FA/day denominator (timeline duration
minus ictal seconds) is algebraically identical to `build_timeline_masked`'s own `n_inter_h`
(both sum the buffer + real-interictal branches), so the two FA/day figures agree exactly in
every row above.

**D0b criterion: descriptive step, no pre-registered pass/fail.**

## D1 -- application defect check

| subject | n_app_ictal | n_offline_ictal | ictal_count_match | ictal_best_lag_k | ictal_rho_at_best_k | ictal_rho_at_k0 | n_app_inter_retained | n_offline_inter | inter_count_match | inter_rho_at_k0 | d1_pass |
|---|---|---|---|---|---|---|---|---|---|---|---|
| chb03 | 106 | 106 | True | 0 | 0.9523 | 0.9523 | 17204 | 17204 | True | 0.9126 | True |
| chb06 | 45 | 45 | True | 0 | 0.9626 | 0.9626 | 19826 | 19826 | True | 0.9550 | True |
| chb13 | 144 | 144 | True | 0 | 0.7872 | 0.7872 | 12452 | 12452 | True | 0.8553 | **False** |
| chb14 | 49 | 49 | True | 0 | 0.9842 | 0.9842 | 13983 | 13983 | True | 0.9886 | True |
| chb15 | 515 | 515 | True | 0 | 0.9728 | 0.9728 | 17026 | 17026 | True | 0.9470 | True |
| chb16 | 28 | 28 | True | 0 | 0.9529 | 0.9529 | 6428 | 6428 | True | 0.8003 | True |
| chb17 | 74 | 74 | True | 0 | 0.9247 | 0.9247 | 9304 | 9304 | True | 0.9328 | True |
| chb18 | 83 | 83 | True | 0 | 0.8532 | 0.8532 | 14853 | 14853 | True | 0.8054 | True |

Every patient's ictal-window count and retained-interictal-window count matches the offline
arrays exactly (`n_app_ictal == n_offline_ictal`, `n_app_inter_retained == n_offline_inter` for
all eight), and the ictal Spearman lag scan peaks at k=0 for all eight patients (no timing
misalignment). The single failure is **chb13**, whose ictal-window Spearman correlation at the
peak lag (k=0) is **rho = 0.7872**, below the pre-registered 0.80 threshold -- every other
patient clears it (range 0.8532-0.9842).

**D1 criterion (every patient: counts match, ictal Spearman peaks at k=0 with rho>=0.80): FAIL**
(chb13 fails on the rho>=0.80 clause only; counts and best-lag both pass for all 8 patients).

Per the pre-registered stopping rule: **D1 failed for one patient (chb13) -- stopping here.**
D2 (window discrimination), D3 (application scores through the offline harness) and D4
(exhaustion-point timeline analysis) were **not run**. This is reported as a possible
application defect specific to chb13's ictal-window score-to-annotation correspondence
(the fused score ranks ictal windows correctly in relative order almost everywhere except on
chb13, where the rank agreement with the offline ictal array is weaker than the other seven
patients, though still positive and still peaking at zero lag -- i.e. not a timing/alignment
bug, but a weaker-than-threshold rank agreement specifically on that patient).

## Computation time

Not available for this run: `src/diag_application_gap.py` measures and prints total elapsed
time only at the very end of `main()`, and the process crashed (Windows console-encoding error,
now fixed) before reaching that line, so no self-reported figure exists for this exact
invocation. Component costs observed during development of this diagnostic: a full D0a
(`evaluate_subject`, 6 PELT fits x 8 subjects) took approximately 6120 s (~102 min) in an
isolated timing run; the D1 per-window artifact-reconstruction pass (`build_app_window_table`,
which calls `preprocessing.filter_window` on every non-ictal, non-buffer window) took 327 s for
chb16 alone (17100 windows, 19 EDFs) in an isolated timing run, which scales to roughly 80 min
across all eight subjects (251445 total real windows). Re-running the fixed script end-to-end
will report an authoritative total.
