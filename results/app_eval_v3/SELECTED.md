# Application v3 -- validation operating point -- SELECTED

docs/CC_PROMPT_APP_VAL_OP.md. The application v3's own headless computation (web_demo/backend/pipeline_demo.process_subject_headless), scored against the validation annotations (chb10, chb11, chb22) -- never read by the application itself. Not applied to any application constant here; the selected values go to Project 2 in a separate instruction.

- repo HEAD: `3f49d2804fd2d4af172387729516b7ac46f987fd`
- `web_demo/backend/pipeline_demo.py` commit: `3336bd7fe063fe86cc8878de4d4ec44fd50bb883` (App v3 code)
- wall-clock time: 50.9 min

## Amendment A8 rule (reported result)

Maximize pooled validation sensitivity subject to pooled validation FA/day <= 25; ties by lower FA/day, then lower penalty.

- mag_pct = 40, pen_mult = 10, merge_s = 300
- pooled: sensitivity=0.4000 precision=0.0698 f1=0.1188118811881188 FA/day=17.232825141176033 seizures=15 detected=6 false_alarms=80

Per subject (and pooled):

```
subject  seizures  detected  false_alarms  sensitivity  precision        f1  false_alarms_per_day    hours  signal_loss_hours
  chb11         5         1            31     0.200000   0.031250  0.054054             24.337807  30.7936                0.0
  chb22         3         3            13     1.000000   0.187500  0.315789             10.081952  31.0031                0.0
  chb10         7         2            36     0.285714   0.052632  0.088889             17.314918  50.0233                0.0
 POOLED        15         6            80     0.400000   0.069767  0.118812             17.232825 111.8200                0.0
```

## Step A rule (information)

Sensitivity and precision closest to equal.

- mag_pct = 80, pen_mult = 5, merge_s = 300
- pooled: sensitivity=0.1333 precision=0.0392 f1=0.0606060606060606 FA/day=10.55510539897032 seizures=15 detected=2 false_alarms=49

Per subject (and pooled):

```
subject  seizures  detected  false_alarms  sensitivity  precision        f1  false_alarms_per_day    hours  signal_loss_hours
  chb11         5         1            15     0.200000   0.062500  0.095238             11.776358  30.7936                0.0
  chb22         3         0            13     0.000000   0.000000 undefined             10.081952  31.0031                0.0
  chb10         7         1            21     0.142857   0.045455  0.068966             10.100369  50.0233                0.0
 POOLED        15         2            49     0.133333   0.039216  0.060606             10.555105 111.8200                0.0
```
