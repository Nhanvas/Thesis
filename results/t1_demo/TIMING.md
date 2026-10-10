# T1 -- processing time of the rebuilt demo pipeline (chb16, 19.0 h, 3 runs)

Full headless path (open, filter, statistics, graph and features, GAE, distances, score, alarm budget, detector, localizer), same functions as the upload flow, CPU.

```
 run subject  files  hours  phase_a_s  stats_s  features_s  gae_s  distances_and_score_s  phase_b_s  events_s  stage2_s  total_s  s_per_hour
   1   chb16     19   19.0      157.8      0.0       289.8   13.4                    1.2      304.5       1.3       1.3    463.9       24.41
   2   chb16     19   19.0      131.1      0.0       266.1   11.4                    0.7      278.3       0.7       0.7    410.3       21.60
   3   chb16     19   19.0      156.2      0.0       250.6    4.3                    0.3      255.2       0.3       0.3    411.9       21.68
```

**Median 21.68 s per hour of EEG** (range 21.60-24.41).
Median per stage (s): phase_a 156.2, stats 0.0, features 266.1, gae 11.4, distances_and_score 0.7, events 0.7