# F5a synthetic test record (chat D36-F, 21/11/2026)

`python src/r4_f5a_synthetic_test.py --root /tmp/f5a_synth` in the build container (Linux, Python 3.13, torch 2.15 CPU,
torch_geometric 2.7.0, ruptures 1.1.10, numpy 2.5.3, pandas 3.0.5, scipy 1.18.1, scikit-learn 1.9.1, mne 1.12.1).
**ALL PASS in 585 s** (measured). Synthetic data only; nothing here is a research result.

| check | result |
|---|---|
| S2 planted worlds | post-ictal plateau of 60 s: return time 60 s, 3-change-point fit at onset / offset / plateau end (± 8 s); abrupt symmetric seizure: return 0 s, null ≤ 12 s, rise and fall ≤ 8 s, record localizer at both boundaries (± 4 s); 60-s ramp: fall ≥ 40 s, rise ≤ 8 s; within-patient ρ insensitive to between-patient offsets; chb01 + chb21 one unit |
| S1 notebook F5A_V5 (synthetic world of `r2_r1_synthetic_test`, 2 workers) | every gate PASS: G-self, G-data, SMOKE, R1.0-dev, R1.0-test, GE, G-k, G-eng[smoke / full], G-seg, G-mf, G-worker-sha; 221 pairs, 25 of 26 cases with a matched pair (random checkpoints), 50 seizures; notebook 0.067 h |
| S1b aggregate on an independent abl record (`p3c_freeze.run_budget` called directly, no r4_f5a code) | A0, A1, A2, A3 PASS; every table written (B = 200 in the test) |
| NEG-A3 | a flat stored search window → aggregate STOP A3 |
| NEG1 | one `p3c_freeze/per_subject.csv` row tp + 1 → STOP R1.0-dev in the SMOKE, no full-run output |
| NEG2 | `e18_cpd_localizer.py` edited after the build → the notebook refuses to start (sha assert) |

**Found by the test and fixed before any output:** the approved return-time rule (inside the pre-onset IQR for 3
consecutive windows) returned 176 s on a planted 60-s plateau because a white-noise window lies inside an IQR only half
of the time; changed to the 5th–95th percentile band plus a null value (DESIGN_F5A.md §9).
Aggregate runtime (computed from the synthetic run: 60 s at B = 1,000 on 221 pairs): ≈ 30–60 min at B = 10,000 on the real
≈ 1,030 pairs (V0 own + fixed, every set), in the container.
