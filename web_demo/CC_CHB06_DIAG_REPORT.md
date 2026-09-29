# CC_CHB06_DIAG_REPORT.md — chb06 Analysis-screen diagnostic

Read-only diagnostic per `CC_CHB06_DIAG_PROMPT.md`. No code or data was changed; the only
compute performed was an in-memory re-run of the existing `process_subject_phase_b_from_paths` /
`process_subject_events` functions (via `pipeline_worker.py`, the exact code the live app uses),
writing its output to a scratch `.npz` outside the repo, never to `web_demo/backend/uploads/`.
Guards: never read `.edf.seizures` or any seizure field, never touched
`results/`/`data/models_retrain/`/`data/processed/`/`docs/`. 4/4 intact.

## TL;DR

Two independent, code-confirmed bugs explain symptom (c); symptom (a)/(b) turned out **not** to
be a data problem at all — the cache is bit-identical to the source EDF and contains no flat or
dropout interval anywhere near the reported times.

1. **`{stem}.score.npy` is never written for chb06 (or any subject processed through the live
   upload flow).** `waveform_serving.get_timeline()` raises `FileNotFoundError` when it's
   missing (`backend/waveform_serving.py:140-145`), which is why the mini-timeline shows no
   score line and no event blocks — there's no server response to draw at all.
2. **`MiniTimeline.jsx` hardcodes a 1-hour time domain** (`DOMAIN_SEC = 3600`) and silently drops
   anything past it — both the score polyline and the event blocks. Boti's viewing position,
   01:05:11 (3911 s), is itself past that cutoff, on a file (`chb06_04.edf`) that runs 3.68 h.
   Even if `.score.npy` existed, nothing would render there.
3. **(a)/(b) are not a corruption or dropout.** The EDF and the `.raw.npy`/`.filtered.npy`
   caches are bit-identical (max diff ~3e-5 µV, pure float32 rounding). No 18-channel flat run
   of any length exists anywhere in chb06's caches near 01:05:11. The amplitude toolbar's
   *default* is 75 µV (`AnalysisScreen.jsx:70`), and this file's real amplitude routinely swings
   into the hundreds of µV (channel std up to ~155 µV over a 20 s window, transient bursts to
   ~900 µV) — so "saturates at 75 µV" describes the display floor meeting a genuinely
   high-amplitude recording, not a bug. I could not reproduce an all-18-channel blank column at
   the two reported stripe times by testing the "envelope entirely outside ±75 µV" clipping
   theory either (0% of columns had all 18 channels outside the band, vs. 65% at a random
   control second elsewhere in the same file) — see §2/§6 for what this leaves open.

---

## 1 — File identification

Query: `events` joined to `files` for `subject_id='chb06'`, onset within ±10 s of 3911.

**No AI event exists within ±10 s of 3911 s for any chb06 file.** The two closest:

| file_id | filename | event onset | offset | distance from 3911 s |
|---|---|---|---|---|
| 218 | `chb06_04.edf` | 3876.0 | 3880.0 | 35 s |
| 217 | `chb06_03.edf` | 3856.0 | 3860.0 | 55 s |

`chb06_04.edf`'s 3876 s event is also that file's **Event 1** (earliest onset among its 6 stored
events), which lines up with "Event 1" in the prompt's framing, so the rest of this report
treats `chb06_04.edf` as the subject file. The 35 s gap from the eyeballed 3911 s is plausible
error for reading an onset off a multi-hour timeline by eye, but it's reported here rather than
assumed away, since resolving §6's mini-timeline bug matters more the further Boti's read was
from the true onset.

**File 218 — `chb06_04.edf`:**
- DB `duration_seconds` (EDF header): 13261.0 s
- Usable duration (cache, `n_windows * 4 s`): **13260.0 s** — 1 s shorter, the trailing partial
  4 s window Phase A drops by construction (`waveform_serving.usable_duration_seconds`'s own
  docstring). Not a bug.
- `n_windows` = **3315**

**All 6 stored AI events for `chb06_04.edf`:**

| Event | onset_sec | offset_sec |
|---|---|---|
| 1 | 3876.0 | 3880.0 |
| 2 | 6256.0 | 6260.0 |
| 3 | 6516.0 | 6520.0 |
| 4 | 7616.0 | 7700.0 |
| 5 | 12416.0 | 12420.0 |
| 6 | 12896.0 | 12900.0 |

## 2 — Per-second cache stats, 01:05:00–01:06:15 (3900–3975 s), `chb06_04`

**No flat run of any length exists.** Scanned at 0.5 s resolution (all 18 channels,
max−min < 0.5 µV) across 3900–3975 s, and again at 1 s resolution across the wider 3800–4000 s —
zero hits. Widened further to every chb06 file (all 18), same two suspect windows
(01:05:21–26 and 01:05:52–57 exactly) — zero hits in any file. So (i)/(ii) are moot: there is no
flat run to check for 4 s-boundary alignment or filtered-vs-raw agreement, because there is no
flat run.

Per-second overview (raw, µV, summarized across 18 channels — full per-channel values were
computed but omitted here for length; min/max/mean-std shown):

```
t=3900.0s (01:05:00.00)  min= -723.03 max=  740.61 std=120.226
t=3905.0s (01:05:05.00)  min= -394.43 max=  641.76 std= 77.522
t=3911.0s (01:05:11.00)  min= -459.68 max=  447.18 std= 98.025   <- eyeballed Event-1 time
t=3915.0s (01:05:15.00)  min= -408.11 max=  312.77 std= 97.057
t=3920.0s (01:05:20.00)  min= -432.33 max=  512.04 std=123.771
t=3921.0s (01:05:21.00)  min= -356.92 max=  613.24 std=110.137   <- reported stripe 1 starts
t=3922.0s (01:05:22.00)  min= -479.22 max=  587.45 std=119.805
t=3923.0s (01:05:23.00)  min= -848.06 max=  885.57 std=178.431   <- largest single burst in range
t=3924.0s (01:05:24.00)  min= -485.08 max=  526.10 std= 99.082
t=3925.0s (01:05:25.00)  min= -384.66 max=  621.83 std=116.539
t=3926.0s (01:05:26.00)  min= -740.22 max=  761.32 std=128.648   <- reported stripe 1 ends
t=3930.0s (01:05:30.00)  min= -237.36 max=  318.24 std= 73.322
t=3940.0s (01:05:40.00)  min= -374.11 max=  282.69 std= 70.861
t=3950.0s (01:05:50.00)  min= -170.16 max=  168.21 std= 46.087
t=3952.0s (01:05:52.00)  min= -234.63 max=  439.76 std= 62.590   <- reported stripe 2 starts
t=3957.0s (01:05:57.00)  min= -193.21 max=  237.36 std= 48.771   <- reported stripe 2 ends
t=3974.0s (01:06:14.00)  min= -338.56 max=  197.12 std= 59.950
```

Every second in this range is non-flat and well above the 0.5 µV flatness threshold on every
channel; the two reported "stripe" windows sit inside ordinary (if bursty) signal, with the
single largest excursion of the whole 75 s span (t=3923 s: −848…+885 µV) landing inside stripe 1.

**(iii) Per-channel raw DC mean and std**, two 20 s windows:

`01:05:00–01:05:20` (3900–3920 s):

| ch | mean (µV) | std (µV) | | ch | mean (µV) | std (µV) |
|---|---|---|---|---|---|---|
| FP1-F7 | 0.360 | 42.285 | | FP2-F4 | 0.639 | 103.715 |
| F7-T7 | 0.178 | 74.179 | | F4-C4 | -1.108 | 118.235 |
| T7-P7 | -0.188 | 53.503 | | C4-P4 | 0.000 | 110.596 |
| P7-O1 | -0.195 | 59.435 | | P4-O2 | 0.927 | 107.051 |
| FP1-F3 | 1.195 | 104.436 | | FP2-F8 | -0.097 | 51.574 |
| F3-C3 | -0.326 | 144.736 | | F8-T8 | -0.336 | 67.982 |
| C3-P3 | 0.341 | 103.494 | | T8-P8 | -0.505 | 62.579 |
| P3-O1 | -0.980 | 107.659 | | P8-O2 | 1.505 | 68.671 |
| FZ-CZ | 0.886 | 155.399 | | CZ-PZ | -1.361 | 140.284 |

`01:05:30–01:05:50` (3930–3950 s):

| ch | mean (µV) | std (µV) | | ch | mean (µV) | std (µV) |
|---|---|---|---|---|---|---|
| FP1-F7 | 0.012 | 42.773 | | FP2-F4 | 0.483 | 80.705 |
| F7-T7 | 0.453 | 59.402 | | F4-C4 | -0.356 | 96.092 |
| T7-P7 | 0.039 | 46.018 | | C4-P4 | 0.092 | 81.042 |
| P7-O1 | 0.279 | 67.021 | | P4-O2 | 0.242 | 91.925 |
| FP1-F3 | 1.150 | 94.016 | | FP2-F8 | -0.130 | 49.084 |
| F3-C3 | 0.113 | 103.567 | | F8-T8 | 0.165 | 70.278 |
| C3-P3 | -0.486 | 85.154 | | T8-P8 | 0.118 | 54.151 |
| P3-O1 | -0.140 | 87.446 | | P8-O2 | 0.364 | 72.962 |
| FZ-CZ | 0.295 | 120.943 | | CZ-PZ | -0.916 | 119.180 |

DC means are all ≈0 (no electrode-offset/rail issue); std drops from the first window to the
second (bursty period settling down), consistent with the visual "quieter after ~3930s" read
in the per-second table above. Nothing here looks like corruption — it looks like ordinary
noisy/artifacted scalp EEG.

## 3 — EDF vs. cache identity check

Read `chb06_04.edf` directly via `mne` (signal only, same 18-channel pick/reorder as
`preprocessing.open_edf`, no `.seizures` file touched), same 3900–3975 s segment, compared
sample-for-sample against `chb06_04.raw.npy`:

```
edf segment shape:   (18, 19200)
cache segment shape: (18, 19200)
max abs diff: 2.9e-11 V  =  2.9e-05 µV
```

Per-channel max diff ranges 7e-6–2.9e-5 µV — pure float32 storage rounding, nothing else.
**Pipeline corruption is ruled out**: the cache is a faithful copy of the source EDF for this
file/segment.

## 4 — Ensemble score, windows covering 01:04:00–01:07:00

`{stem}.score.npy` does not exist on disk for any chb06 file (see §6/root-cause below), so it
was recomputed in memory using the production code path (`pipeline_worker.py`'s `phase_b` mode,
which calls `pipeline_demo.process_subject_phase_b_from_paths` — the exact function the live
Create-New/Process flow already runs) over all 18 of chb06's cached `.filtered.npy` files, since
the ensemble's LedoitWolf/robust-z stats are fit subject-wide, not per-file. Nothing was written
back to `uploads/`; the result only exists in a scratch `.npz`.

Windows 960–1004 (t = 3840.0–4016.0 s, 4 s/window):

```
win=960 t=3840.0s (01:04:00.00) score=-0.4424
win=961 t=3844.0s (01:04:04.00) score=-0.7289
win=962 t=3848.0s (01:04:08.00) score=-0.5909
win=963 t=3852.0s (01:04:12.00) score=-0.4278
win=964 t=3856.0s (01:04:16.00) score=-0.8835
win=965 t=3860.0s (01:04:20.00) score= 0.3595
win=966 t=3864.0s (01:04:24.00) score= 0.6534
win=967 t=3868.0s (01:04:28.00) score= 0.3793
win=968 t=3872.0s (01:04:32.00) score= 0.5816
win=969 t=3876.0s (01:04:36.00) score=-0.6093   <- Event 1 onset window (3876-3880s)
win=970 t=3880.0s (01:04:40.00) score= 2.8583   <- sharp jump immediately after the event window
win=971 t=3884.0s (01:04:44.00) score= 1.4224
win=972 t=3888.0s (01:04:48.00) score= 0.7125
win=973 t=3892.0s (01:04:52.00) score= 0.2270
win=974 t=3896.0s (01:04:56.00) score= 1.6569
win=975 t=3900.0s (01:05:00.00) score= 1.6096
win=976 t=3904.0s (01:05:04.00) score= 2.4450
win=977 t=3908.0s (01:05:08.00) score= 0.9007
win=978 t=3912.0s (01:05:12.00) score= 1.1652
win=979 t=3916.0s (01:05:16.00) score= 1.4814
win=980 t=3920.0s (01:05:20.00) score= 1.3917
win=981 t=3924.0s (01:05:24.00) score= 1.0323   <- inside reported stripe 1 (3921-3926s)
win=982 t=3928.0s (01:05:28.00) score= 0.9329
win=983 t=3932.0s (01:05:32.00) score= 0.9969
win=984 t=3936.0s (01:05:36.00) score=-0.3175
win=985 t=3940.0s (01:05:40.00) score= 0.6518
win=986 t=3944.0s (01:05:44.00) score= 0.1342
win=987 t=3948.0s (01:05:48.00) score=-0.5470
win=988 t=3952.0s (01:05:52.00) score= 1.4537   <- inside reported stripe 2 (3952-3957s)
win=989 t=3956.0s (01:05:56.00) score=-0.6631
win=990 t=3960.0s (01:06:00.00) score= 0.0150
win=991 t=3964.0s (01:06:04.00) score= 0.3443
win=992 t=3968.0s (01:06:08.00) score=-0.3995
win=993 t=3972.0s (01:06:12.00) score= 2.4884
win=994 t=3976.0s (01:06:16.00) score= 1.3701
win=995 t=3980.0s (01:06:20.00) score= 0.4010
win=996 t=3984.0s (01:06:24.00) score= 0.5272
win=997 t=3988.0s (01:06:28.00) score=-0.7808
win=998 t=3992.0s (01:06:32.00) score=-0.1639
win=999 t=3996.0s (01:06:36.00) score=-0.1520
win=1000 t=4000.0s (01:06:40.00) score=-0.4589
win=1001 t=4004.0s (01:06:44.00) score=-0.4856
win=1002 t=4008.0s (01:06:48.00) score= 0.7676
win=1003 t=4012.0s (01:06:52.00) score= 1.2833
win=1004 t=4016.0s (01:06:56.00) score= 0.5099
```

File-wide stats for context: mean=0.536, std=0.998, p99=3.460, max=5.254 (at t=7664 s).

**Event 1's own onset window (969) has a below-average score (−0.61)**; the window right after
it (970, 3880–3884 s) has the sharpest local jump (2.86, above p99). The whole 01:04:36–01:06:56
stretch runs persistently above the file's mean (mostly 0.9–2.5) rather than showing one isolated
spike — this reads as a genuinely elevated/artifacted segment of the recording (matching §2's
"bursty" std profile), not a single-window change-point artifact. Nothing in this score trace
lines up specifically with the two reported "blank stripe" times more than with the rest of this
elevated stretch — consistent with §2/§6's finding that those stripes aren't a real data event.

## 5 — Spearman correlation: attribution score vs. per-channel std (Event 1)

Event 1 = window 969 only (3876–3880 s, one 4 s window). Attribution = that window's row of the
already-cached `chb06_04.pernode.npy` (per-node/per-channel reconstruction score — the same
array the Channel Attribution Panel uses); per-channel std = std of `chb06_04.filtered.npy`'s
samples inside that same window, in µV.

```
Spearman rho = 0.6842, p = 0.0017   (n=18 channels)
```

Top-5 by attribution score: `FP2-F4` (0.0548), `C4-P4` (0.0485), `F3-C3` (0.0445),
`F4-C4` (0.0418), `FZ-CZ` (0.0409)

Top-5 by filtered std: `CZ-PZ` (143.9 µV), `FZ-CZ` (114.8 µV), `C4-P4` (96.5 µV),
`FP1-F3` (82.6 µV), `F4-C4` (80.0 µV)

3 of 5 channels overlap (`C4-P4`, `F4-C4`, `FZ-CZ`), consistent with the moderate-strong
monotonic correlation — the attribution score is picking up roughly the same channels the raw
variance highlights, though not identically ranked (`FP2-F4`/`F3-C3` rank high on attribution
but not on std; `CZ-PZ`/`FP1-F3` are the reverse).

## 6 — MiniTimeline.jsx time domain

`frontend/src/components/MiniTimeline.jsx:10`:

```js
const DOMAIN_SEC = 3600 // SPEC §6.3's stated default; none of the current allowlist's files
// exceed 1 h, so there's no pan/zoom case to handle here yet (flagged in the report).
```

**Confirmed: it cannot show anything beyond 3600 s.** Both rows independently hard-cut at
`DOMAIN_SEC`:
- Score polyline, line 57: `if (t > DOMAIN_SEC) break` — any window at or past 3600 s is simply
  never added to the plotted path.
- Detections row, line 132: `if (ev.onset_sec > DOMAIN_SEC) return null` — any event whose onset
  is past 3600 s is not rendered at all, regardless of how much of it might overlap the visible
  hour.

The x-axis mapping itself (`xFrac = t / DOMAIN_SEC`, `left = onset_sec / DOMAIN_SEC * 100`) also
has no offset/pan term — this is a single fixed [0, 3600 s) window over the *whole* file, not a
scrollable viewport, so there is currently no way to see anything past the first hour of a
longer file at all, not even by interacting with the component (it has no click handler, per its
own header comment).

The code comment's premise is false for the real subject data: `chb06_04.edf` alone is
13260 s (3.68 h) of usable recording, and the DB query in §1 shows most chb06 files run
13261–14400 s (all 8 allowlisted subjects were uploaded as real, multi-hour files in Step 9 —
`BUILD_PROGRESS.md` §15). Boti's viewing position, 01:05:11 = 3911 s, is itself 311 s past the
3600 s cutoff — so even with `.score.npy` present, neither the score line nor Event 1's block
would render there. This is a second, independent cause of symptom (c), on top of the missing
`.score.npy` cache (§0/TL;DR item 1).

---

## 4a — Recomputed score validation (not in the original prompt, done for confidence)

Ran `process_subject_events()` on the recomputed scores from §4 (same subject-wide PELT +
label-free operating-point calibration the live Process flow uses) and compared its output
against every AI event already stored in the DB for chb06 (§1's full query, files 215–232).

**Exact match, every file, every event, onset and offset both** (e.g. `chb06_04.edf` →
`(3876.0, 3880.0), (6256.0, 6260.0), (6516.0, 6520.0), (7616.0, 7700.0), (12416.0, 12420.0),
(12896.0, 12900.0)` — identical to the DB row-for-row). This confirms the recomputed score in §4
is not an approximation or a different code path drifting from what originally produced these
events — it's the same deterministic computation, and the DB's stored events are reproducible
and internally consistent with the (uncached) score array. It does not change any conclusion
above; it just means §4's numbers can be trusted as "the real score," not a guess.

## Root cause summary for symptom (c) ("no score line, no event blocks")

Two bugs, either one sufficient on its own at this viewing position:

1. `{stem}.score.npy` was never persisted for chb06. The live Create-New/Process flow
   (`upload_manager.py:_run_process`, `pipeline_worker.py:_run_phase_b`) only ever routes the
   ensemble score through temporary `.npz` files that get `unlink()`-ed once consumed —
   `pipeline_worker.py:39`'s own comment says as much ("Never touches `.score.npy` or any other
   existing output"). Only a separate backfill pass (`CC_STEP5_REPORT.md`) ever wrote
   `.score.npy` to the persistent per-subject directory, and it was only run for `chb13`/`chb16`
   (the two subjects that existed in the DB at that point), never for chb06 or the other five
   subjects uploaded for real in Step 9 phase 2. `waveform_serving.get_timeline()` then raises
   `FileNotFoundError` for every other subject, chb06 included.
2. `MiniTimeline.jsx`'s `DOMAIN_SEC = 3600` hard limit (§6) means even a correctly-cached score
   array would not render past the file's first hour — and 01:05:11 already is past it.

Symptom (a) ("saturates at 75 µV") is the toolbar's documented default floor
(`AnalysisScreen.jsx:70`) meeting a recording whose real amplitude (std up to ~155 µV, bursts to
~900 µV, §2) routinely exceeds it — not a bug, though it may be worth reconsidering the default
for subjects/files this noisy.

Symptom (b) ("blank vertical stripes") remains only partly explained. It is **not** missing or
corrupted data (§2/§3: no flat run anywhere, cache = EDF bit-for-bit). I also tested and could
**not** confirm the most likely rendering explanation — that `EegPanel.jsx`'s per-channel
`ctx.clip()` (lines 153-156) blanks a whole vertical column when a decimated bucket's envelope
lands entirely outside a channel's own ±amplitudeUv band, which would look exactly like a
"blank stripe" if it happened to all 18 channels' buckets at once. At the two reported times, 0%
of columns had *all* 18 channels outside ±75 µV (95% and 64% had *at least one* channel outside,
respectively) — and a same-length control window elsewhere in the same file, picked with no
special significance, showed a comparable 65% any-channel-outside rate. So this file's amplitude
routinely exceeds 75 µV throughout, not just at the two reported times, which weakens (without
fully ruling out) the per-column-clip theory as the specific explanation for why those two
particular 5 s spans looked blank rather than merely busy/clipped like the rest of the file.
Given the ±10 s DB-event mismatch in §1, it's also possible Boti was looking at a slightly
different scroll position or file than the one this report pinned down — worth a quick live
screen-share check before spending more time chasing (b) further in the cache alone.
