# CC_CHB06_DIAG2_REPORT.md

Answers `CC_CHB06_DIAG2_PROMPT.md`. Read-only throughout: no `src/*.py`, `web_demo/backend/*.py`,
or `uploads/` file was modified. One scratch script (`_diag_cpd_detail.py`, run-and-deleted, never
imported) was used to call `cpd_pipeline_v14.detect_changepoints` directly; it wrote nothing under
`uploads/` and was removed after use. Guards stayed 4/4 throughout (last check below). Never read
`*.edf.seizures` or any seizure field — every number below comes from the DB's own `events` table
(AI-source events already computed by the live pipeline) or from re-running the same production
score/CPD code, never from ground truth.

## 1 — DB record, wall-clock conversion, confirmation

`files` row for `chb06_02.edf` (file id **216**):

```
start_time: 2060-01-26T23:09:34+00:00   duration_seconds: 14400.0 (4h)
```

Its only event (`events` row, id **371**):

```
onset_sec=6936.0  offset_sec=7000.0  duration=64.0s  source=AI  name="Event 1"
```

Wall-clock (`start_time + offset`): onset **01:05:10**, offset **01:06:14** — this is the only
event in the file and it is exactly the one shown on screen as **onset 01:05:10**, length **64 s**
(matches the Analysis-screen "Onset: 01:05:10 Offset: 01:06:14 Duration: 1:04" panel exactly).

Reported stripe intervals converted to file offsets (`start_time` = 23:09:34, as confirmed above):

```
01:05:21 -> 6947 s     01:05:26 -> 6952 s     (prompt's predicted 6947-6952 — confirmed)
01:05:52 -> 6978 s     01:05:57 -> 6983 s     (prompt's predicted 6978-6983 — confirmed)
```

## 2 — per-second / per-channel min/max/std, event onset-20s to offset+20s (6916-7020s)

Full 104-second, per-second, all-18-channel table computed from `.raw.npy`/`.filtered.npy`
(`waveform_serving._load_window`, µV). Only two seconds meet "ALL 18 channels flat (max-min <
0.5 µV)" in **raw**: **6981, 6982** — bit-identical flat, inside the reported stripe-2 interval.
**No second in the 104 s window is flat in the filtered signal** (the notch/bandpass filter's own
ringing off the huge surrounding transients leaves every filtered second with some residual
spread — see §5's exact-window numbers below).

Representative rows (full second-by-second table available on request; the pattern either side of
each stripe is a fast ring-down into the flat run then an equally fast ring back out — not a
gradual fade):

```
  sec   raw min(µV)  raw max(µV)  allflat
 6946     -316.68      335.82      False
 6947    -1567.77     1758.83      False   <- huge transient right at stripe-1's start
 6948       -3.71       10.35      False   <- ringing down
 6949    -1939.73     1684.59      False   <- back to huge transient
 6950    -2128.84     2231.99      False
 ...      (peak amplitudes up to ±2680 µV through 6950-6979 — see §3)
 6978    -1440.78     1106.72      False
 6979    -1406.79     1625.59      False
 6980      -35.75        0.20      False   <- ringing down
 6981        0.20        0.20      True    <- FLAT
 6982        0.20        0.20      True    <- FLAT
 6983     -137.73      138.12      False   <- back out
 6984     -233.85      271.75      False
```

## 3 — EegPanel draw replication (60 s window, 7 s before onset, width_px=850)

Window = [6929, 6989)s (60 s, onset 6936 − 7). Replicated `waveform_serving._decimate_envelope`
exactly (same function, same `width_px=850` → 850 buckets, ~0.0706 s/bucket, ~18 samples/bucket)
on both raw and filtered, then applied `EegPanel.jsx`'s actual per-channel clip rule (read from
source, `drawSeries`/`ctx.clip()` at lines 117-164): a pixel column is blank **for a given
channel** only when that channel's own `[min, max]` bucket envelope lies **entirely on one side**
of that channel's own ±amplitude band (both endpoints above +amp, or both below −amp) — the canvas
clips the line to its own row, so a bucket whose envelope never re-enters the row paints nothing
there.

**Fraction of pixel columns where ALL 18 channels are simultaneously blank by this rule:**

```
                    whole window (850 col)   stripe1 [6947-6952] (71 col)   stripe2 [6978-6983] (71 col)
amp= 75 µV   raw:        0/850 (0.0%)              0/71 (0.0%)                   0/71 (0.0%)
             filt:       0/850 (0.0%)              0/71 (0.0%)                   0/71 (0.0%)
amp=150 µV   raw:        0/850 (0.0%)              0/71 (0.0%)                   0/71 (0.0%)
             filt:       0/850 (0.0%)              0/71 (0.0%)                   0/71 (0.0%)
amp=250 µV   raw:        0/850 (0.0%)              0/71 (0.0%)                   0/71 (0.0%)
             filt:       0/850 (0.0%)              0/71 (0.0%)                   0/71 (0.0%)
amp=500 µV   raw:        0/850 (0.0%)              0/71 (0.0%)                   0/71 (0.0%)
             filt:       0/850 (0.0%)              0/71 (0.0%)                   0/71 (0.0%)
```

**Finding: the per-channel-clip mechanism never fires here, at any amplitude 75-500 µV.** Every
bucket's per-channel envelope straddles zero (min far negative, max far positive within the same
~18-sample bucket) because the underlying signal oscillates fast enough that no single ~0.07 s
bucket sits entirely to one side of the ±amplitude band. **This rules out per-channel canvas
clipping as the cause of the reported blank stripes** — the actual cause is §2's finding: a
genuine ~1-3 s all-18-channel flatline in the underlying cached (and, per §4, source) signal
itself, which draws as a flat line at each channel's own vertical center rather than a rendering
gap. At low amplitude settings that flat line is easy to miss next to the huge neighboring
excursions, which is almost certainly what reads as "blank" on screen — but it is not a rendering
bug, and it is present at every amplitude tested.

Per-channel mean/std of **raw**, µV, over each 5 s stripe interval (also computed for filtered;
see §5 for the exact bit-flat sub-windows, which are narrower than these 5 s intervals):

```
RAW stripe1 [6947-6952]s (n=1280 samples)                    RAW stripe2 [6978-6983]s (n=1280 samples)
  FP1-F7  mean= -49.40  std=326.73                              FP1-F7  mean=   5.62  std= 49.07
  F7-T7   mean=  28.23  std=319.82                              F7-T7   mean=  -5.39  std= 41.45
  T7-P7   mean= -31.80  std=187.61                              T7-P7   mean=  -0.75  std=  4.12   <- near-flat all 5s
  P7-O1   mean=   3.71  std=202.12                              P7-O1   mean=  10.17  std= 63.91
  FP1-F3  mean= -52.66  std=321.30                              FP1-F3  mean=   9.78  std= 85.40
  F3-C3   mean=   9.39  std=285.01                              F3-C3   mean= -10.48  std= 80.90
  C3-P3   mean=  -9.53  std=235.55                              C3-P3   mean=  13.14  std= 76.17
  P3-O1   mean=   3.50  std=274.93                              P3-O1   mean=  -2.69  std= 64.60
  FP2-F4  mean=   1.72  std=153.54                              FP2-F4  mean=   0.46  std=270.21
  F4-C4   mean= -15.09  std=228.64                              F4-C4   mean=  -0.22  std=155.31
  C4-P4   mean=  21.42  std=314.28                              C4-P4   mean= -47.06  std=184.15
  P4-O2   mean=   4.59  std=238.33                              P4-O2   mean=  25.10  std=156.49
  FP2-F8  mean= -46.43  std=195.96                              FP2-F8  mean=  -2.15  std=273.54
  F8-T8   mean=  48.58  std=189.81                              F8-T8   mean=   2.26  std=  8.60   <- near-flat all 5s
  T8-P8   mean=  -8.45  std=172.75                              T8-P8   mean=   0.05  std=  0.76   <- near-flat all 5s
  P8-O2   mean=  18.39  std=338.32                              P8-O2   mean= -22.03  std= 87.47
  FZ-CZ   mean=  -1.57  std=139.56                              FZ-CZ   mean=   0.86  std= 65.04
  CZ-PZ   mean=   9.01  std=130.16                              CZ-PZ   mean=  -0.53  std= 35.85
```

Three channels (T7-P7, F8-T8, T8-P8) are conspicuously quiet through the whole stripe-2 5 s
interval, not just the exact flat sub-window — foreshadowing §5's attribution result.

## 4 — EDF vs. cache comparison

Opened `F:/Study/Thesis/Dataset/CHB-MIT/chb06/chb06_02.edf` directly with `mne.io.read_raw_edf`
via `src/dataprep/preprocessing.open_edf` (same channel rename/pick/reorder the pipeline uses,
read-only), pulled the same [6929, 6989)s segment, and diffed against `.raw.npy`'s cached samples
for the identical range:

```
max abs difference across all 18 channels, 15360 samples each: 1.15e-04 µV
(per-channel max: 5.7e-05 to 1.15e-04 µV; mean per-channel: ~1e-06 to 6e-06 µV)
```

This is exactly the size of `float32` rounding error (`.raw.npy` is stored as float32;
`raw.get_data()` is float64) — **the flatline artifact is present in the source EDF itself**, not
introduced by caching, Phase A windowing, or any pipeline step. It is a real artifact in the
CHB-MIT recording (consistent with a brief amplifier/common-mode saturation and recovery: every
channel pins to the identical constant value `0.1953602` µV — one ADC quantization step —
simultaneously, then rings back out; see §2's ring-down/ring-up pattern either side of each flat
run).

Finer-grained (0.1 s resolution) scan located the exact bit-identical spans, narrower than the 5 s
stripe intervals originally estimated:

```
stripe 1 exact flat span:  6948.3 - 6949.3 s  (~1.0 s)   wall-clock 01:05:22.3 - 01:05:23.3
stripe 2 exact flat span:  6980.5 - 6983.3 s  (~2.8 s)   wall-clock 01:05:54.5 - 01:05:57.3
```

## 5 — attribution table, filtered-std comparison, per-window stability

`GET /api/events/371/attribution` (called via `attribution.get_event_attribution` directly — same
function the endpoint calls, read-only, no DB write):

```
window_lo=1734 window_hi=1749 (6936-7000s, 16 windows, n_windows_used=16)

rank  channel   score      rank  channel   score
 1    T8-P8    6.9140       10   F3-C3    3.5823
 2    F8-T8    5.2869       11   FP2-F4   2.8470
 3    P7-O1    4.4344       12   C3-P3    2.5844
 4    FZ-CZ    4.2735       13   FP1-F3   2.5674
 5    FP2-F8   4.2522       14   T7-P7    2.5517
 6    CZ-PZ    3.8762       15   F7-T7    2.5318
 7    F4-C4    3.8426       16   C4-P4    2.4641
 8    P3-O1    3.8191       17   P4-O2    2.3548
 9    P8-O2    3.7885       18   FP1-F7   2.0952
```

Per-channel std of the **filtered** signal over the full event window (6936-7000s):

```
F7-T7  413.8   FP1-F7 405.5   FP1-F3 393.6   P8-O2  375.5   F3-C3  361.9   C4-P4  350.6
P3-O1  353.8   C3-P3  338.8   T7-P7  331.5   FP2-F8 315.7   F8-T8  299.2   P4-O2  288.4
P7-O1  286.8   FP2-F4 156.4   F4-C4  144.7   T8-P8  118.6   CZ-PZ  109.9   FZ-CZ  108.6
```

**Spearman correlation, attribution score vs. filtered std, across the 18 channels: ρ = −0.624,
p = 0.0056 — a statistically significant INVERSE relationship.** Top-5 by each measure barely
overlap (P7-O1 and FP2-F8 are the only two names shared):

```
Top-5 by attribution score:  T8-P8, F8-T8, P7-O1, FZ-CZ, FP2-F8
Top-5 by filtered std:       F7-T7, FP1-F7, FP1-F3, P8-O2, F3-C3
```

**This directly explains the reported "event/attribution vs. visible waveform" mismatch.**
Attribution is a reconstruction-anomaly z-score (`pernode`, p95 |robust-z| vs. the subject's whole-
recording median/MAD baseline — `attribution.py`'s docstring), not a measure of visible amplitude.
In this event the channels with the *largest* visible swings (F7-T7, FP1-F7, ~400 µV std) are
mid-to-low ranked, while the top-ranked channel, T8-P8, is one of the three quietest channels
identified in §3 — its own signal barely moves (118.6 µV std here, and near-flat, std<1 µV,
specifically through the stripe-2 window). An unexpectedly *quiet* channel against a baseline
built from that channel's own normal dynamics can register as anomalous by this reconstruction
metric exactly as an unexpectedly *loud* one can — the score is symmetric in surprise, not in raw
amplitude, so there is no reason to expect it to track the most visually dramatic channel.

Per-window top-3 channels from `chb06_02.pernode.npy` (16 windows spanning the event) — **the
event-level rank-1 channel, T8-P8, is NOT the top channel in most individual windows**: it appears
in the per-window top-3 for only 4 of 16 windows (1738, 1741, 1742, 1746), and never as window
rank-1 except at 1746:

```
w1734(6936-40s) F3-C3,CZ-PZ,P7-O1      w1742(6968-72s) FZ-CZ,F4-C4,T8-P8
w1735(6940-44s) F7-T7,FP2-F8,C4-P4     w1743(6972-76s) CZ-PZ,F4-C4,FP1-F7
w1736(6944-48s) F3-C3,F7-T7,F4-C4      w1744(6976-80s) F7-T7,FP1-F3,FP1-F7
w1737(6948-52s) P7-O1,P3-O1,FP2-F4  *  w1745(6980-84s) F3-C3,CZ-PZ,FP2-F8  *
w1738(6952-56s) F8-T8,T7-P7,T8-P8      w1746(6984-88s) T8-P8,CZ-PZ,P3-O1
w1739(6956-60s) CZ-PZ,C4-P4,FP2-F8     w1747(6988-92s) P7-O1,P3-O1,P8-O2
w1740(6960-64s) FP1-F7,F3-C3,F4-C4     w1748(6992-96s) P3-O1,FP1-F7,C3-P3
w1741(6964-68s) F4-C4,T8-P8,F8-T8      w1749(6996-00s) FZ-CZ,F4-C4,FP1-F7
```
(`*` = the two windows containing §4's exact flatline artifacts, 1737 = stripe 1, 1745 = stripe 2
— both produce unusually high top-3 scores, 0.118 and 0.104 respectively, the two highest single
top-1 values across all 16 windows: the flatline itself reads as a strong per-window anomaly.) The
event's rank-1 channel is an aggregate (95th percentile over 16 windows) of a quantity that moves
to a different channel almost every window — it does not correspond to any one window's most
anomalous channel, let alone the loudest visible one.

## 6 — ensemble score ±3 min, and where the change points actually fall

`chb06_02.score.npy` exists (written by the live Process flow, `CC_FIX_SCORECACHE_PROMPT.md`
Task 1a). Loaded directly — no recompute needed for the file-local score values. Windows
[1689, 1794] (6756-7180s, event windows 1734-1749 ± 45 windows / 180 s):

```
score range in this ±3min span: min=-1.477, max=5.847, mean=0.176
peak (5.847) at window 1745, t=6980-6984s -- i.e. exactly the window containing the stripe-2
  bit-flat artifact (6980.5-6983.3s). This is the single highest score anywhere in the ±3min span,
  well above the event's own onset/offset windows (-0.44 at 1734, -1.39 at 1749).
```

For "where the change points fall," recomputed the full production path in memory (no writes):
concatenated all 18 of chb06's cached `.score.npy` files in filename order (`process_subject_events`'s
own convention), ran `calibrate_operating_point` — **chosen pen_mult = 2.0**, event rate 29.13/day
(grid: 0.3→126.6/day, 0.5→90.3, 1.0→53.9, **2.0→29.1 (chosen)**, 5.0→16.2, 10.0→11.1 — reproduces
`PROJECT_STATUS.md`'s recorded chb06 pen_mult of 2.0 exactly), then called
`cpd_pipeline_v14.detect_changepoints` directly (below `detect_events`'s merge step) to see the
raw kept change points before they get expanded/merged into event intervals, and
`detect_events` to confirm the final merged interval matches the DB.

```
chb06_02.edf's raw kept change-point window indices: [1734, 1749]  (t = 6936s, 6996s)
detect_events()'s merged interval for chb06_02.edf: onset=6936.0 offset=7000.0
  (matches the DB's stored event exactly, and matches the earlier CC_FIX_SCORECACHE_REPORT.md-era
  chb18 verification pattern: recomputed events reproduce the stored ones bit-for-bit)
```

**There are only two PELT change points anywhere near this event, at the very first window
(6936s, score −0.44) and the very last window (6996s, score −1.39) of the eventual 64 s span — not
at the score's actual peak.** `detect_events` expands each into its own 4 s interval
(`[6936,6940]` and `[6996,7000]`) and merges them into one because they are only 56 s apart
(< `merge_s=90`). **The dramatic score spike at 6980-6984s (§6 above) and the two raw-signal
flatline artifacts (§2/§4) all sit strictly inside the merged 64 s span but are not themselves
change points** — PELT is keying on the two level-shift boundaries at the edges of this noisy
region, not on any point of peak anomaly within it. So the demo's three different signals —
change-point-defined event boundaries, the raw waveform's visually loudest moments, and the
attribution ranking's top channel — are computed from three different quantities (a subject-wide
score-timeline level shift; per-channel raw amplitude; a per-channel reconstruction z-score) and
have no built-in reason to visually agree on this file. That is the root of every mismatch the
author reported, not a bug in any one of the three.

## Guard status

```
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-9.1.1, pluggy-1.6.0
collected 4 items

tests/test_guards.py::test_guard_no_build_timeline_masked PASSED         [ 25%]
tests/test_guards.py::test_guard_no_seizure_fields_at_runtime PASSED     [ 50%]
tests/test_guards.py::test_guard_no_labeled_npy PASSED                   [ 75%]
tests/test_guards.py::test_guard_no_writes_outside_web_demo PASSED       [100%]

============================== 4 passed ==============================
```

No code or data was changed. Nothing was committed.
