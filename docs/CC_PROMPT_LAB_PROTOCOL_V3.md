# CC_PROMPT_LAB_PROTOCOL_V3.md — laboratory protocol without amplitude masking

Pre-registered 2026-10-01 before any result of this version exists; commit this file alone first.
Same code base as `src/lab_protocol_eval.py`; outputs `results/lab_protocol/v3/`. Cached scores only.
**Expected time 15–20 minutes.**

## Why a third version

v1 exempted ictal windows from the ±5 SD mask (the cache skips the check for ictal and buffer windows),
which uses the annotation. v2 applied the rule to every window: 86 % of ictal windows were masked,
32/76 test seizures entirely, and the lab-convention window AUROC fell to 0.453, so its detections can
no longer be attributed to the model's score. Amplitude masking cannot separate artifact from seizure
and is dropped from the detector.

## Protocol v3

1. Detector side: only the signal-loss rule (A2) masks windows. No ±5 SD masking.
2. Evaluation side: post-ictal don't-care exactly as in the first protocol (4 h after each annotated
   offset within the same file; detections overlapping a seizure are scored normally).
3. FA/day denominator: recorded time − seizure time − don't-care time − signal-loss time.
4. Validation grid (8 × 6 × merge_s {90, 300}), A8 rule (max pooled sensitivity with pooled
   FA/day ≤ 25), then the test scored **once** at the selected point, per patient and pooled (and
   without chb17). Report window macro AUROC on test with negatives = non-ictal windows outside the
   don't-care region and not signal-loss, beside 0.621 (all windows) and 0.805 (artifact-free
   background, the offline definition).

## Also report, for the record of v2 (no rerun)

Of the 47 test seizures detected in v2, how many were entirely masked (fused score 0 on every one of
their windows), and for those, where the matching change point lies relative to the mask boundary.

## Output

`results/lab_protocol/v3/SUMMARY.md`, CSVs; commit script changes and outputs with explicit paths in
`bash -e`. Do not edit the v1 or v2 outputs.
