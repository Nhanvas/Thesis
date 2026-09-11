# CC_STEP1_FILTER_OPT_PROMPT.md — one-pass fix for filter_window's 63% cost

Good diagnosis, no code changes needed to confirm it. Do ONE optimization pass on this, then
re-measure and stop — don't keep iterating past this regardless of the resulting number, report
deadline is priority.

## The fix

Replace the per-window call to `preprocessing.filter_window(raw, start, end)` (called once per
window — 3606 times on chb06_01.edf — each re-reading a padded slice and running
`sosfiltfilt`+`filtfilt` on it) with filtering the WHOLE continuous recording ONCE, then slicing
into windows:

1. Read the entire raw signal once: `data = raw.get_data()` → `[18, n_total_samples]`.
2. Apply the SAME filter design `preprocessing.py` uses — import its actual filter objects rather
   than reconstructing them from memory: `preprocessing._BP_SOS` (bandpass, `sosfiltfilt`) and
   `preprocessing._NOTCH_B` / `preprocessing._NOTCH_A` (notch, `filtfilt`). Apply `sosfiltfilt` then
   `filtfilt` ONCE over the full data array (`axis=1`), not per-window.
3. Slice the filtered continuous array into non-overlapping 4 s windows (same window count and
   `preprocessing.WIN_SAMPLES` per window as before).

This is both faster (no repeated per-window `filtfilt` overhead/padding) and slightly MORE correct
than the original per-window approach: `filter_window()`'s padding exists specifically to suppress
`filtfilt` edge-transients at every 4 s window boundary; a single continuous filter pass only has
edge effects at the true start/end of the file. Add a short comment saying so, so it reads as an
intentional choice, not a shortcut.

Do not touch `preprocessing.py` itself (read-only) — importing its private `_BP_SOS` /
`_NOTCH_B` / `_NOTCH_A` attributes is fine, that's still importing from a read-only module, not
copying its code.

## Stop condition

Re-run the timed CLI once on `chb06_01.edf` after this change, report the new stage breakdown +
total, and confirm `test_guards.py` still passes. Stop after that one report — do not start Step 2.
