# Application tier -- rebuilt demo (final system), 8 test subjects

Build commit 8aabf4d4c8ee2892a808e25b9c7839291803f436; export manifest:

```
commit 8aabf4d4c8ee2892a808e25b9c7839291803f436
uncommitted changes in web_demo/backend or src: no
exported 19:08:00 (local time; no date written)
subjects 8, files 231, events 350
sha256 ba62c1607c3c49ae0894ffb0e779a7dba4e63567b52f9c738a3463b8131153df  chb03_events.csv
sha256 35b0babfc3f7425824e0027e6588fb855f34ec776c05b4a36741eff83edfb473  chb06_events.csv
sha256 3787eac11ebd09d2ef90b23f55d3db920f8ac1d26bcf260ddbf77ab1f55a3925  chb13_events.csv
sha256 46672f17a8fd57f346ed72b7be2a6de16715527e4d36d609568c8d0e2f878098  chb14_events.csv
sha256 c05066361d76400bb82ab53cb55f2361ac25af699e66996337196e1280d03b51  chb15_events.csv
sha256 3298eae9f696ee8534e905fddcf9c820eda4ab2ced2727db9bf173df5f78734a  chb16_events.csv
sha256 ad10dcb766934ba328c8b6b0dc7fccc2e51ef7d6d45bc3f74dd982f71bd2330e  chb17_events.csv
sha256 668d27ac5457417e49a5912caf81d6fd9cdfbb559247f691334d47534fc617e1  chb18_events.csv
sha256 d99d6e677f093ca9f51d971e92991cffb36aa22ce09113b96b481fe26098575b  files.csv
```

Scorer: src/eval_application_events.py (unchanged): SzCORE event scoring per file, counts summed per subject; FP/day denominator = recorded time of the processed files minus seizure time. Every AI event, before review.

## Per subject

```
subject  files   hours  seizures  detected  false_alarms  sensitivity  precision_counts  f1_counts  false_alarms_per_day
  chb03     38 38.0017         7         6            20       0.8571            0.2308     0.3636               12.6683
  chb06     18 66.7350        10         1            97       0.1000            0.0102     0.0185               34.9065
  chb13     33 33.0000        12         1            41       0.0833            0.0238     0.0370               29.9531
  chb14     26 26.0000         8         6            33       0.7500            0.1538     0.2553               30.5166
  chb15     40 40.0100        20        10            59       0.5000            0.1449     0.2247               35.8875
  chb16     19 19.0000        10         1            16       0.1000            0.0588     0.0741               20.2354
  chb17     21 21.0067         3         3            27       1.0000            0.1000     0.1818               30.9673
  chb18     36 35.6347         6         5            30       0.8333            0.1429     0.2439               20.2551
```

## Pooled and subject-mean (from the scorer's counts)

```
pooled        33/76 detected, 323 false alarms, sensitivity 0.434, precision 0.093, F1 0.153, FP/day 27.86
subject-mean  sensitivity 0.528, precision 0.108, F1 0.175, FP/day 26.92
```

Boundary lines: chb03: 0; chb06: 0; chb13: 0; chb14: 0; chb15: 0; chb16: 0; chb17: 0; chb18: 0

Coverage: chb18: 6/6 annotated seizures in processed files; Total annotated seizures in processed files: 76/76; Total processed hours: 279.39 vs 279.39 (report Table 2.1), delta -0.00 h