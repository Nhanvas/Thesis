Task: look at the raw EEG and measure what the +-5 SD flagged windows actually are. One pass over the
EDFs. Write only src/raw_eeg_view.py and results/raw_eeg_view/. Change no other file. Commit only those
paths, with explicit paths, inside bash -e. Stream file by file, keep memory under ~3 GB, do not run
alongside another heavy job. Print the elapsed time per subject.

Read first: src/continuous_eval.py (layout of results/continuous_eval/cache/mask/{subj}.npz: is_ictal,
is_buffer, is_artifact, is_signal_loss, spans), src/dataprep/preprocessing.py (open_edf, filter_window,
FS, WIN_SAMPLES, FILTER_PAD, parse_summary), results/continuous_eval/signal_loss.csv.

PART 1 - pictures. Window onset-20 s to onset+40 s for seizures, 30 s for other windows. 18 channels
stacked, signal as the pipeline filters it (0.5-60 Hz + 60 Hz notch), common amplitude scale in uV
written on the figure, plus a second panel with the PSD of the same segment (raw, unfiltered, 0.5-100 Hz,
log axis). No figure number or title text beyond subject, file, time and seizure duration. Selection
uses no model score: A) the 3 shortest seizures of chb16, 3 of chb06, 2 of chb14; B) 3 seizures of
chb15, 2 of chb03, 2 of chb18; C) flagged non-ictal non-buffer windows (is_artifact True), 8 random
(seed 42) from chb10, chb11, chb22 and chb13, drawn so that both causes below are represented;
D) for chb13 the 2 files with the highest flagged share, 3 random windows each, with the per-channel
SD of that file divided by the subject-wide per-channel SD printed on the figure. Combine into contact
sheets (A, B, C+D), at most 8 panels per PNG, readable at 1600 px width. Save as
results/raw_eeg_view/sheet_A.png, sheet_B.png, sheet_CD.png and the individual panels in a subfolder.

PART 2 - what the flagged windows are. For every flagged window, using the pipeline-filtered signal,
record: number of samples above 5 SD (per channel, then summed), number of channels with at least one
exceedance, the channel with most exceedances, and cause = single-spike (<=3 samples above 5 SD in
total) or sustained (otherwise). Table: share of windows by cause and by channel group (frontopolar
FP1/FP2, temporal, central, parietal-occipital, midline), per subject and pooled.

PART 3 - label-free features, labels used ONLY to score separability, never to set a threshold.
Per window and per channel, then summarised across channels as median and max: Hjorth mobility and
complexity, line length divided by channel SD, relative power in 0.5-4, 4-8, 8-13, 13-30, 30-60 Hz,
the ratio 20-60 Hz / 0.5-60 Hz (muscle proxy), the ratio 0.5-2 Hz / 0.5-60 Hz (slow/eye/sleep proxy),
spectral entropy, rhythmicity = fraction of 0.5-60 Hz power within +-1.5 Hz of the spectral peak,
kurtosis; spatial: fraction of channels whose window SD exceeds 3x the subject median. Data: all files
of chb10, chb11, chb22; for each of the 12 training subjects all files that contain a seizure plus 2
other random files (seed 42). Do NOT use any test subject for numbers; test subjects appear only in the
pictures of Part 1.
Report AUROC (value and direction) for each feature, separately for: seizure windows vs flagged
non-seizure windows; seizure windows vs unflagged background; flagged vs unflagged background. Give
per-subject values and the pooled value over validation and training subjects, and repeat for
seizures shorter than 20 s and 20 s or longer. Mark any feature with pooled AUROC >= 0.75 or <= 0.25
for seizure-vs-flagged, and say whether its direction agrees across at least 2 of the 3 validation
subjects.

PART 4 - read-only facts, report them, change nothing. (a) From preprocessing.py write_windows, state
whether data/processed/{subj}_interictal.npy contains only windows that passed the +-5 SD rule, and how
many windows each of the 12 training subjects has in it. (b) From notebooks/, docs/prereg/PREREG_01*
and results/retrain_v3p1, find how many windows the original GAE was trained on, the wall-clock time of
that training on Kaggle, and which script defines the training windows.

Write results/raw_eeg_view/SUMMARY.md with all tables and the three facts of Part 4, copying numbers
exactly. Report the elapsed total and the path of SUMMARY.md.