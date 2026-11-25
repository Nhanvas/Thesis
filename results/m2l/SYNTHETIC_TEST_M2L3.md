# Synthetic test M2L3 (chat F2-03, 25/11/2026) — m2l_sched after M2L_L3_EVAL Version 1

Command: `python src/m2l_synthetic_test.py --root /tmp/m2l_synth` (build container: Python 3.13.18, numpy 2.1.3, scipy 1.16.3, scikit-learn 1.6.1, pandas 2.3.3, torch 2.11.0, torch_geometric 2.7.0, mne 1.12.1). Every earlier check re-run; new: U3, P5, NEG7–NEG9 (`results/m2l/l3eval_v1_timeout/DIAGNOSIS.md`). Code tested = code committed (m2l_sched `ec2841629bdeb87c`, m2l_run `f0f8c563e5c3726a`, m2l_core `9690cac7f91f52b2` unchanged). Not covered: real-EEG memory and Kaggle speed (measured by the run: PROJ, G-sched, per-job VmHWM).

```
world: 23 cases of EDF written (4 s)
world ready (150 s)
U1 PASS: selection rule and minimum-length rule on hand-made tables
U2 PASS: segment cuts, top = 0, statistics R / B, MCD distances
U3 PASS: memory model, over-budget STOP, admission simulation (makespan 2120 -> 5926 s under 20.4 GB)
P1 PASS M2L_L2_REC: every gate, 1080 rows, no .npz / EDF (172 s)
P1 PASS M2L_L2_ROB: every gate, 1080 rows, no .npz / EDF (176 s)
R2 PASS: L2 read: chosen R-LW-F (candidates []); outputs /tmp/m2l_synth/repo/results/m2l/l2
P4 PASS M2L_L3_SHORT_A (184 s)
P4 PASS M2L_L3_SHORT_B (182 s)
P4 PASS reader --l3short: L3-short read: minimum length 5 min (qualifying [5]); outputs /tmp/m2l_synth/repo/results/m2l/l3short
P5 PASS: one-job budget respected (21 jobs, none overlap), peaks measured (858-874 MB), scheduled = Pool arrays
P4 PASS L3-eval + reader --l3 (151 s)
P2 PASS: PN01 per-recording statistics = x1 label-free statistics (mean 5.1e-18, SD 0.0e+00)
P3 PASS: PN01 rows of the per-recording path = the V5 chain on the x1 .npz at the same k
NEG1 PASS: edited RB1c constants stop at G-c
NEG2 PASS: changed committed statistics stop at G-feat1
NEG3 PASS: a changed patient-unit path stops at G-chain
NEG4 PASS: an earlier .npz whose is_buffer differs passes R1.0 and stops at G-struct
NEG5 PASS: a missing selection stops at G-sel
NEG6 PASS: an edited module stops the notebook before it starts
NEG7 PASS: a worker killed from outside stops the run, naming PN01-1.edf (48 s, no hang)
NEG8 PASS: a stalled job stops at G-watchdog (148 s)
NEG9 PASS: a budget below one recording's estimate stops at PROJ
ALL PASS in 1490 s
```
