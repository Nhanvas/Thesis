# V9-V1-FIX Part 1 extra -- chb06 background generalized-discharge scan (vs chb03)

Rule (fixed before counting): every NON-SEIZURE 4 s window (ctx['nonict']: not ictal, not the 4 h post-seizure buffer, not signal-loss) where >= 12/18 channels have RMS ratio > 3 vs the preceding 60 s (same kind of event as the chb06_01.edf/1724 s one the reviewer pointed at); ensemble percentile = the frozen final scalar's own within-patient percentile at that window (v9_anatomy.final_events, unsmoothed).


## chb06

```
n flagged = 3
ensemble percentile: median 0.999, IQR [0.997, 0.999], max 1.000
```

## chb03

```
n flagged = 19
ensemble percentile: median 0.927, IQR [0.784, 0.984], max 1.000
```

## The referenced event itself (chb06_01.edf, 1700-1732 s, around onset 1724 s)

Measured directly (not inferred from the counts above): this specific event's own max channel RMS ratio vs its preceding 60 s, every 4 s window.

```
   t  n_ch_gt3  max_ratio
1700         0   0.834414
1704         0   1.219197
1708         0   1.879867
1712         0   1.850046
1716         0   1.777429
1720         0   2.313293
1724         0   1.479084
1728         0   1.188229
1732         0   1.303316
```

max over the whole span: n_ch_gt3=0, max_ratio=2.31 -- never reaches the >=12-channel/ratio>3 rule used above. The low ensemble score the reviewer saw (~0.2 just before onset) is therefore NOT a case of chb06's background containing frequent RMS-amplitude look-alikes of this event (chb06 has FEWER flagged background windows than chb03, 3 vs 19, and scores them near-maximal when they do occur, not absorbed). The pre-onset discharge the reviewer describes as 'large' is rhythmic/morphological, not a sudden RMS-amplitude surge relative to the preceding minute -- a different mechanism than the one this scan was built to detect, and a finding that argues AGAINST the 'frequent background look-alikes' hypothesis as measured here.

Elapsed 169 s.