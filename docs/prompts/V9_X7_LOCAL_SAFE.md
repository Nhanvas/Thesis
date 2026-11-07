# V9-X7 — Two further protocol fixes: local background contrast, and safe artifact exclusion before ranking (Claude Code, laptop)

Estimated runtime: 1.5–3 h (estimated, not measured). Run after V9-X1 and V9-V1-FIX (one heavy job at a time); cache-based where possible; single worker; smoke first; resumable.

## Why
1. **Local contrast.** The thesis score compares a window with the patient's whole normal (per-patient Mahalanobis) and removes slow file drift (±15-min running median). If a patient's normal contains frequent seizure-like discharges (chb06, chb16 — see V9-V1-FIX), a seizure is not unusual for that patient, but it is still a *change from the minutes just before it*. Classic seizure detectors use exactly this contrast (Gotman 1982: epoch vs a background 16 s earlier). Add it as one member, not a replacement.
2. **Safe exclusion with budget refill.** The artifact veto of V9-E2 deleted events after ranking without refilling the alarm budget, so it could only lose sensitivity. Here only artifact types that a seizure cannot produce are excluded, **before** ranking, so the budget is spent on the remaining windows: flat-line (any channel with SD < 1 µV over a 4-s window), amplifier saturation / clipping (≥ 1 % of samples at the recording's digital min/max on any channel), and signal loss (all channels near zero). Seizures are never flat or clipped, so these rules cannot remove seizure activity; they do remove the square saturation blocks seen in the hospital recording.

## Arms (fixed now; G and F; each on top of the V9-X1 verdict: if X1's change was adopted, build on it, otherwise on the frozen members)
- **LC** — add one member: for each window, the per-channel robust-z minus its median over the preceding 60 s (15 windows, causal), 9th largest channel, same percentile mapping, equal mean with the other members.
- **SX** — safe exclusion before ranking (rules above, label-free), budget refilled.
- **LC + SX** — both.
k recalibrated with `p3_levers.calibrate()` unchanged on the 15 development patients for each arm.

## Evaluation and rule
Same report set as V9-X1 (development, CHB-MIT test, chb24, Siena 14; 4 seeds for G and F; matched-FP curve; paired bootstrap vs the base; duration bins; annotated channel count bins; onset/offset; FP types). SX also reports how many windows and how many seizure windows were excluded (must be 0 seizure windows; if not, stop and report).
**Adoption rule (fixed now):** an arm is adopted if on development the paired difference at 27.5 FP/day has point estimate > 0 and 95 % CI lower bound ≥ −0.02. Test, chb24 and Siena are reported whatever the verdict. EEG: up to 6 newly caught and 6 newly lost test seizures (slide + full versions, convention of `src/v9_eeg_samples.py`).

## Rules
Read-only on frozen scripts and committed results; new code `src/v9_x7_local_safe.py`; outputs `results/v9_x7/`, figures `F:/Study/Thesis/Defense/slides/figs/eeg_evidence/x7/`; commit only these paths.

## Return format
Full report to `F:/Study/Thesis/Agent/inbox/V9_X7_REPORT.md`.
