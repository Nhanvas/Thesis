# Addendum 2 to PREREG_VETO_SCREEN.md — test protocol, written 2026-10-05, BEFORE any test patient is run

Validation outcome of run 2 (results/veto_screen_v2/summary.md): A8 matched 9/15 (V0 5/15) at FA/day 21.5 (V0 25.0);
mean ictal-window veto share 0.122; no seizure with more than half of its windows vetoed. All three criteria met.
Run 1 (invalid, label-exempted flag) is not used.

## Test protocol (one shot)
Rule, Q = 95, replacement by the median of unflagged windows: identical to validation run 2. Flag computed from the signal
for every window. Operating cell fixed on validation: m75/p5.0/mg300 (the A8 cell of the veto on validation); the earlier
cell m50/p2.0/mg90 is reported alongside. No parameter, cell or rule is changed after seeing any test number.
V0 on test is recomputed from the cached score and checked against results/continuous_eval/stepC_full_test_grid_scopeT.csv
when its columns allow; any mismatch stops the run.

## Reporting rule
Reported as one-shot, with the statement that the test patients were scored several times earlier in the work.
An improvement is claimed only if, at the validation cell, the veto matches more events than V0 AND does not raise FA/day.
Otherwise the report states that the validation gain did not transfer. The best-with-FA<=25 line on the test grid is
descriptive only.

## Disclosure for the report
The veto is a label-free design addition; Q = 95 was read off training-patient diagnostics (design selection on training
patients). The validation set was looked at repeatedly for other variants (branch weights, rolling baseline, oracle bound);
only this configuration was pre-registered as a gate. The supervisor is to be told before the report states this stage.
