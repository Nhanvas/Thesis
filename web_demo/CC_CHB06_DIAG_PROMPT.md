Read-only diagnostic on chb06. No code or data changes; write only the report.

Context: on the Analysis screen of a chb06 file, "Event 1" starts at about 01:05:11
(file-relative, ~3911 s). Observed: (a) raw view saturates at 75 uV; (b) blank vertical
stripes across ALL 18 channels at about 01:05:21-01:05:26 and 01:05:52-01:05:57, in both
raw and preprocessed views; (c) the mini-timeline shows no score line and no event blocks.

1. Locate the file: query the DB for chb06 AI events with onset within +-10 s of 3911.
   Report file id/name, usable duration, n_windows, and that file's events (Event N,
   onset, offset).
2. From that file's caches ({stem}.raw.npy, {stem}.filtered.npy) for 01:05:00-01:06:15,
   per second and per channel: min, max, std in uV. Report (i) every run >= 0.5 s where
   ALL 18 channels are flat (max-min < 0.5 uV) in raw, and whether it is also flat in
   filtered; (ii) whether those runs align with 4 s window boundaries; (iii) per-channel
   mean (DC) and std of raw across 01:05:00-01:05:20 and 01:05:30-01:05:50.
3. Read the same time segment straight from the source .edf (read-only, signal only, via
   mne) and compare with the cache, per channel: identical or not. This rules pipeline
   corruption in or out.
4. Print the ensemble score (score.npy) for windows covering 01:04:00-01:07:00, and the
   event's onset/offset windows, to show where the change points sit relative to the score.
5. For Event 1: Spearman correlation across the 18 channels between the attribution score
   and the per-channel std of the filtered signal inside the event; print the top-5 channels
   by each measure.
6. Read MiniTimeline.jsx and state how its time domain is computed; confirm or refute
   that it cannot show anything beyond 3600 s.

Never read *.edf.seizures or any seizure field of a summary file. Guards must stay 4/4.
Report to CC_CHB06_DIAG_REPORT.md.