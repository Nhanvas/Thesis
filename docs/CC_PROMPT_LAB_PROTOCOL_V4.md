# CC_PROMPT_LAB_PROTOCOL_V4.md — event-level evaluation on artifact-free EEG (scoring side only)

Pre-registered 2026-10-01 before any result of this version exists; commit this file alone first.
Same code base as `src/lab_protocol_eval.py`; outputs `results/lab_protocol/v4/`; cached Scope T (A2)
scores only. **Expected time 40 minutes.** Do not edit v1, v2 or v3 outputs.

## Purpose

The event-level counterpart of the window-level definition already used by the thesis (seizure
windows against artifact-free background, AUROC 0.805): the detector is untouched, and the evaluation
ignores false alarms that fall in artifact-contaminated or post-ictal EEG, as studies that evaluate
on artifact-free recordings do. Declared as a laboratory convention, reported beside the strict
continuous result and the application's deployment result, never merged with them.

## Protocol v4

1. **Detector:** unchanged from v3 (Scope T A2 scores, signal-loss masking only, no amplitude masking).
2. **Don't-care regions (evaluation side only):** (a) the 4 h post-seizure buffer as in v3;
   (b) every window flagged by the ±5 SD artifact rule, computed for **every** window including ictal
   ones, from the raw signal with the same rule and thresholds as v2's corrected flags (no annotation
   used to compute the flag). A detection that overlaps an annotated seizure (SzCORE tolerances) is
   scored normally wherever it starts, so sensitivity is never affected by the convention. A detection
   that overlaps no seizure is a false alarm only if its onset window is outside both don't-care
   regions; otherwise it is ignored.
3. **FA/day denominator:** recorded − seizure − post-ictal don't-care − artifact don't-care −
   signal-loss time, each component reported per patient.
4. **Selection on validation only** (chb10, chb11, chb22), same 96-cell grid, A8 rule (max pooled
   sensitivity with pooled FA/day ≤ 25); also report the best F1 cell on validation for information.
   **Test scored once** at the A8 point: per patient, pooled, pooled without chb17, median latency.
5. Also report, for the A8 point on test: false alarms ignored by each don't-care component (counts),
   so the effect of the convention is visible.

No other test point is computed or reported. Nothing is chosen after the test is seen.

## Output

`results/lab_protocol/v4/SUMMARY.md` and CSVs; commit script changes and outputs with explicit paths
in `bash -e`.
