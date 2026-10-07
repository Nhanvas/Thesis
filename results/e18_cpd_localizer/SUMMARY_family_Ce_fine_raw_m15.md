# E18 -- kernel CPD onset/offset localizer, arm family_Ce_fine_raw_m15, 4 seeds, 15 non-test

Detector cell (re-selected): smooth 5, top 0.005; D1 reproduction of event_grid exact.

## Detection (guard only; CPD cannot raise sensitivity or lower FA)

```
detector  sens 0.668  FA/day 19.98
cpd       sens 0.662  FA/day 19.55
```

## Localization on matched seizures (n = 243 reference-seed pairs; CPD used on 93% of them; fallback rate on all events 20%, short events 22%)

```
all (n = 243)
  onset   detector median  16.0 s  IQR [12.0, 28.0]  bias +16.0 s | cpd median   8.0 s  IQR [4.0, 12.0]  bias  +4.0 s
          no-CPD control (unsmoothed > threshold) median   8.0 s  IQR [4.0, 18.0]  bias  +4.0 s
  offset  detector median  20.0 s  IQR [8.0, 56.0]  bias  -4.0 s | cpd median  16.0 s  IQR [4.0, 44.0]  bias  +4.0 s
          no-CPD control (unsmoothed > threshold) median  40.0 s  IQR [16.0, 90.0]  bias +32.0 s
events <= 30 s (n = 84)
  onset   detector median  20.0 s  IQR [12.0, 32.0]  bias +20.0 s | cpd median  10.0 s  IQR [4.0, 17.0]  bias  +4.0 s
          no-CPD control (unsmoothed > threshold) median  12.0 s  IQR [4.0, 24.0]  bias  +4.0 s
  offset  detector median  12.0 s  IQR [8.0, 48.0]  bias  -8.0 s | cpd median  12.0 s  IQR [4.0, 41.0]  bias  +0.0 s
          no-CPD control (unsmoothed > threshold) median  32.0 s  IQR [8.0, 57.0]  bias +10.0 s
events > 30 s (n = 159)
  onset   detector median  16.0 s  IQR [12.0, 20.0]  bias +16.0 s | cpd median   8.0 s  IQR [4.0, 12.0]  bias  +4.0 s
          no-CPD control (unsmoothed > threshold) median   8.0 s  IQR [4.0, 16.0]  bias  +8.0 s
  offset  detector median  24.0 s  IQR [8.0, 64.0]  bias  +0.0 s | cpd median  20.0 s  IQR [4.0, 46.0]  bias  +4.0 s
          no-CPD control (unsmoothed > threshold) median  52.0 s  IQR [24.0, 104.0]  bias +44.0 s
```

- detection guard -> pass
- localization: onset 8.0 vs 16.0 s, offset 16.0 vs 20.0 s -> pass

**ADOPTED: kernel CPD is the onset/offset localizer**

## Seizure-seed pairs caught by the detector but lost after CPD: 0 (0.0 per seed)


Elapsed 141 s.