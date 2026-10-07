# HANDOFF_P3 — from stage P2 (closed 2026-10-07) to stage P3

Written 2026-10-07 at the end of the P2 chat. Read with `docs/PERF_PHASE_RECORD.md` rev P (the source of
every number below; on any conflict the record wins). This file is the starting brief for the P3 chat.

## 1 · Where we are

**P2 frozen system** (tag `p2-frozen`; record §6.6):
GAE v2 clean (seeds 42, 1, 2, 3; headline seed 42) → per patient, label-free: per-channel LedoitWolf
Mahalanobis of the 16-d node latent → per-channel robust-z → order statistics 6, 9, 12 of 18 and the
channel mean, each minus its ±15 min running median inside each file (non-causal; post-hoc triage) →
patient percentiles, equal mean = **one scalar ensemble anomaly score** → D1 detector (moving average
5 windows = 20 s, patient top 0.5 % of time, merge 90 s) → kernel CPD (rbf, 2 change points, event ± 60 s)
as the onset/offset localizer.

| | non-test (15, 4 seeds) | **test, look #6** (8 patients) | E = P1 frozen, test |
|---|---|---|---|
| pooled sensitivity (after localizer) | 0.662 @ 19.6 FP/day | **0.342 (26/76) @ 22.2** seed 42; 0.336 ± 0.008 @ 23.9 | 0.039 (3/76) @ 24.1 |
| subject-mean sensitivity | 0.828 @ 19.5 (detector) | 0.498 | 0.043 |
| precision / F1 (scorer counts) | — | 0.092 / 0.145 | 0.011 / 0.017 |
| short seizures (< 20 s) | 2/3 | 4/18 | 0/18 |
| onset / offset median abs error | 8 / 16 s | 8 / 20 s (offset bias +16 s) | — |

Per test subject (seed 42, after localizer): chb03 7/7, chb06 2/10, chb13 1/12, chb14 6/8, **chb15 0/20**,
chb16 2/10, chb17 3/3, chb18 5/6. Without chb15: 0.464. Patient-level bootstrap (seed 42, computed):
final − E pooled +0.303 [0.094, 0.630]. Seed SD (0.008) measures initialisation only.

**Author decision (2026-10-07):** the result is an improvement but is **not approved**. Stage P3 continues
the work and will test again. **Target: pooled test sensitivity ≥ 0.50 (38/76, i.e. +12 seizures) at the
best FP/day achievable; sensitivity has priority over FP/day.** The thesis shape is kept: GAE → one scalar
ensemble anomaly score → non-parametric CPD with a measured role in onset/offset localization.

## 2 · What P2 established (do not rediscover)

1. The v2 graph-level latent separates seizures from high-amplitude windows (AUROC 0.966); recon is near
   chance against them (0.53); gamma-AEC has a heavy upper tail that owned the old ensemble's top 2 %.
2. Per-channel modelling of the node latent (S-family) beats the graph mean; the spread hypothesis
   ("≥ half the montage") was not the mechanism (channel mean ≈ S9).
3. **File-level drift of the latent readout owns most false alarms** (84.5 % of the top-2 % non-ictal
   tail in the patient's top-quartile files under S9). A location-only correction (minus ±15 min running
   median) moves the whole curve left; scale corrections and short per-file baselines (10/30 min) hurt
   (one baseline = one brain state).
4. Rank (percentile) ensembles stop heavy-tailed readouts from owning the tail; cross-readout ensembles
   (with recon, L, gamma, gamma detrended) were inferior to the latent family.
5. The D1 top-p grid must be fine (factor-2 steps hid gains); validation in gates = `val` (best cell
   re-selected on the 3 validation subjects), `val_at_cell` is descriptive.
6. Patient fine-tuning of the GAE (one configuration, 2,000 steps, all parameters, 4 seeds) did not move
   flagged-window scores: not selected in that configuration.
7. Short seizures are missed because their peaks sit at the 0.81–0.995 percentile, below any affordable
   short-branch threshold (E19b); not a smoothing artefact alone.
8. CPD halves the onset error vs the detector's boundaries; on offset a simple contiguous-run rule
   (12 s) and multivariate CPD (8 s, E20a) beat 1-D CPD (16 s). The −0.006 sensitivity after CPD is the
   756-s chb11 seizure losing its last SzCORE split piece.
9. The 15-subject selection set over-predicts test by about 2× (0.662 → 0.336); ~40 gated decisions
   were taken on it (record §6.4 and `results/p2_ledger.csv`).

## 3 · P3 starting hypotheses (mechanism first; each needs a measurement before any arm)

| # | hypothesis | first measurement | non-test evidence available? |
|---|---|---|---|
| H1 | **Seizure-rich patients lose to the fixed top-p budget or to ranking**: top 0.5 % of time ≈ 12 min per 40 h; chb15 has 20 seizures, chb13 12 (author) | `src/p3_seizure_burden.py` (annotation metadata only: counts, durations, ictal minutes vs budget); then the percentile of each seizure's peak (smoothed 5) vs the threshold | **chb12** (26 seizures, low sensitivity on non-test) is the non-test analogue |
| H2 | **Contamination of the per-patient fit**: many stereotyped seizures enter the LedoitWolf fit and the robust-z, so they look less anomalous (risk named in P2 design, never measured) | on chb12: seizure z under the whole-recording fit vs a trimmed fit (exclude the top x % of an initial score, refit once) or MinCovDet | yes (chb12, chb10, chb20) |
| H3 | Threshold calibration (the form's literature focus): an absolute robust-z threshold with a per-patient FA cap could let seizure-rich patients spend more alarms than a fixed time fraction | characterise sensitivity/FA of `max(top-p quantile, median + k·MAD)` on non-test, pre-registered k | yes |
| H4 | Localization: hybrid CPD onset + multivariate or contiguous-run offset; split events > 300 s before CPD | non-test errors (E18 vs E20a vs control 2), already measured | yes |
| H5 | chb06 is inverted under every model (AUROC 0.25–0.38); chb16 has 10 short seizures | per-subject score anatomy; no fix proposed yet | partially (chb21 0/4) |

**Test-information rule for P3.** Look #6 per-subject results and test seizure durations are test
information. Any P3 design that uses them is listed in record §3, and look #7 is disclosed as
test-informed. Prefer evidence from non-test analogues (chb12, chb21, chb20).

## 4 · Binding working rules (author, kept from P2)

- No early verdict of failure: measure the mechanism → state a fix hypothesis → pre-register the gate
  (in the docstring) → run. Gates fixed; constructions redesigned. Every design has an "if not met" section.
- 4 seeds; G1 = 4-seed mean and ≥ 3/4 seeds not lower; D1 cell re-selected by the same pooled rule at
  ≤ 25 FA/day on the fine grid; pooled and subject-mean, validation-only and without-chb12 beside every
  number; precision/F1 only from scorer counts; every arm to `results/p2_ledger.csv` (or a P3 ledger).
- Reproduction gates before reading results; mock smoke tests before delivery; whole files with paths.
- Claude 2 (account `code`) reviews each batch; the author approves every design before it runs.

## 5 · Code map (all in `src/`, results in `results/<name>/`)

`p2_scalars.py` (shared scalar builders, D1 identical to `e1_normal_definition.event_grid`, SzCORE via
`e10_kernel_cpd.score_events`) · `e16_recording_baseline.py` (S9, drift arms a–f, `summarise`, `gate`,
`ledger`) · `e17b_latent_family.py` (final scalar `member`) · `e18_cpd_localizer.py` (CPD, E18d
`--overlap`, E20a `--multi`, controls, split-reference table) · `e21_fine_grid.py`, `e21b_gamma_detrend.py`,
`e19b_short_branch_fine.py`, `p2_bootstrap.py` · `p2_dump_seeds23.py` (seeds 2/3 non-test) ·
`p2_test_dump.py` + `e22_test_oneshot.py` (look #6; R1/R2 reproduction, tag guard, hashes) ·
`p2_test_bootstrap.py` (patient-level CI of look #6) · `p3_seizure_burden.py` (first P3 check).
Caches: `results/e8_gae_v2/scores`, `results/e14_spatial_recruitment/pernode`,
`results/e15_patient_adaptation/pernode` (node latents s0/s2000), `results/p2_seeds`, `results/p2_test`.

## 6 · Open items outside performance (waiting until the system is final)

Report Chapters 1–5 rewrite (system changed: no recon/gamma, per-patient label-free fitting, D1 detection
+ CPD localization; Chapter 2 Table 5; Goal 1 quoted verbatim), demo rebuild (Project 2; non-causal
±15 min median, per-patient fits, CPU cost), LiNDDA comparator after the final freeze, supervisor items
in record §7 (3: label-free per-patient fitting under "unsupervised"; 4: role of CPD). Literature lead on
onset/offset latency (Perplexity) is unverified. Report submission 15/10, defense 05–06/11.
