# CC_PROMPT_LAB_PROTOCOL.md — laboratory evaluation protocol on the real continuous timeline

Pre-registered 2026-10-01 before any result of this protocol exists. Commit this file alone before
running. Thesis side: code `src/lab_protocol_eval.py`, outputs `results/lab_protocol/`. Uses only
cached scores and flags; no EDF is re-read, no model is run. **Expected time 20–40 minutes.**

## Purpose

Separate the laboratory evaluation of the model from the deployment evaluation of the application.
The laboratory protocol keeps the real continuous timeline (no reconstruction, no resampling, every
false alarm counted where it can occur) and applies two declared conventions that published detectors
commonly use. The application keeps the strict deployment protocol.

## Protocol (both conventions declared in the report)

1. **Detector side, label-free preprocessing applied to every window, ictal included:** a window is
   masked if it is flagged by the thesis's own ±5 SD artifact rule (same thresholds as the Scope T
   artifact-mask cache) or by the signal-loss rule. Masked windows keep their place on the timeline
   with fused score 0 (the robust-z median) before smoothing, so they cannot create change points on
   their own. Scope T fits are unchanged (their background mask already excludes these windows).
2. **Evaluation side, post-ictal don't-care:** the thesis's existing post-seizure buffer (4 h after
   each annotated offset, within the same file, exactly as `preprocessing.build_buffer_mask`) is a
   don't-care region. A detection whose onset falls in it and that does not overlap an annotated
   seizure (with the SzCORE tolerances) is neither a true nor a false positive; detections that
   overlap a seizure are scored normally wherever they start.
3. **FA/day denominator:** recorded time minus seizure time minus don't-care time minus masked time,
   reported per patient with each excluded component.
4. Scoring otherwise exactly SzCORE via `timescoring`, files concatenated in file-name order,
   change points from the cached Scope T (A2) fused scores, same CPD code.

## Steps

A. **Validation (chb10, chb11, chb22) only:** full grid, 8 magnitude percentiles × 6 penalty
   multipliers × merge_s ∈ {90, 300}. Select the operating point by the A8 rule (maximize pooled
   sensitivity subject to pooled FA/day ≤ 25; ties by lower FA/day, then lower penalty). Also report
   the sensitivity-equals-precision point for information.
B. **Test, scored once at the A8-selected point:** per patient and pooled (and pooled without chb17):
   seizures, detected, false alarms, sensitivity, precision, F1, FA/day, median latency.
C. Window-level macro AUROC on test under the same conventions (negatives = non-ictal windows that are
   neither masked nor in the don't-care region), beside the all-windows value 0.621.
D. Cost of masking: number of test seizures with any masked window, and number entirely masked.

No other test point is computed or reported. Nothing chosen after B is seen.

## Output

`results/lab_protocol/SUMMARY.md` (A, B, C, D, wall-clock), CSVs, commit script and outputs with
explicit paths inside `bash -e`.
