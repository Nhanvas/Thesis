# CC_CHB06_DIAG2_PROMPT.md — redo the chb06 diagnostic on the segment actually viewed

Read-only. No code or data changes; write only the report. Never read `*.edf.seizures` or any
seizure field. Guards must stay 4/4. Run this AFTER CC_FIX_SCORECACHE_PROMPT.md has landed.

Correction: the previous diagnostic treated on-screen times as elapsed seconds. They are
WALL-CLOCK times (file `start_time` + offset; MiniTimeline's tick labels show e.g. 23:09 ... 00:09
for a file starting at 23:09:34). So the earlier analysis of chb06_04 at 3900 s was the wrong
segment, and its "no flat run" and Spearman results do not apply to what the author saw.

Segment actually viewed: chb06_02.edf (start 23:09:34 per the Database screen — confirm from the
DB), Event 1, shown on screen as onset 01:05:10 with a block of roughly 64 s. Reported anomalies:
raw view saturated at 75 uV; blank vertical stripes across ALL 18 channels at wall-clock about
01:05:21-01:05:26 and 01:05:52-01:05:57 (present in both raw and preprocessed views); the event
and the top attribution channel do not seem to match the visible waveform.

1. From the DB: chb06_02.edf file id, start_time, duration, and its events with onset/offset in
   seconds AND as wall-clock (start_time + offset). Confirm which event is on screen as 01:05:10
   and its length. Convert the two stripe intervals to file offsets (expect about 6947-6952 s and
   6978-6983 s if the start is 23:09:34).
2. From `{stem}.raw.npy` and `.filtered.npy`: per second and per channel min/max/std (uV) from
   event onset - 20 s to offset + 20 s; report any run where ALL 18 channels are flat
   (max-min < 0.5 uV).
3. Replicate the EegPanel draw for a 60 s window starting 7 s before the event onset at
   width_px = 850 (same decimation as `waveform_serving._decimate_envelope`): for raw and for
   filtered, and at amplitude 75 / 150 / 250 / 500 uV, the fraction of pixel columns in which ALL
   18 channels' [min, max] envelopes lie entirely outside their own +-amplitude band (those are
   blank on screen because of the per-channel clip). Report it for the two stripe intervals and
   for the whole window. Also list per-channel mean and std of raw over each stripe interval.
4. Compare the EDF samples with the cache for this segment (read-only via mne, same 18-channel
   pick): max abs difference per channel.
5. For the on-screen event: the full table returned by `GET /api/events/{id}/attribution`
   (rank / channel / score). Then the per-channel std of the filtered signal inside the event, the
   Spearman correlation between the two, and top-5 lists by each measure. Also, from
   `pernode.npy`, the top-3 channels for each individual window of the event, to show whether the
   top channel is stable across windows.
6. Ensemble score (`score.npy` if it exists by now, otherwise recompute in memory via the
   production path without writing to `uploads/`) for the event windows +-3 min, and where the
   change points fall relative to it.

Report to `CC_CHB06_DIAG2_REPORT.md`.
