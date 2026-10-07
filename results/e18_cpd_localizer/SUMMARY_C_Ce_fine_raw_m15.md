# E18 -- kernel CPD onset/offset localizer, arm C_Ce_fine_raw_m15, 4 seeds, 15 non-test

Detector cell (re-selected): smooth 5, top 0.0075; D1 reproduction of event_grid exact.

## Detection (guard only; CPD cannot raise sensitivity or lower FA)

```
detector  sens 0.681  FA/day 24.25
cpd       sens 0.662  FA/day 23.70
```

## Localization on matched seizures (n = 249 reference-seed pairs; CPD used on 96% of them; fallback rate on all events 14%, short events 16%)

```
all (n = 249)
  onset   detector median  16.0 s  IQR [8.0, 20.0]  bias +16.0 s | cpd median   8.0 s  IQR [4.0, 16.0]  bias  +8.0 s
          no-CPD control (unsmoothed > threshold) median  12.0 s  IQR [8.0, 24.0]  bias  +8.0 s
  offset  detector median  24.0 s  IQR [8.0, 64.0]  bias  +0.0 s | cpd median  12.0 s  IQR [4.0, 36.0]  bias  -4.0 s
          no-CPD control (unsmoothed > threshold) median  40.0 s  IQR [16.0, 104.0]  bias +28.0 s
events <= 30 s (n = 69)
  onset   detector median  20.0 s  IQR [12.0, 20.0]  bias +20.0 s | cpd median  12.0 s  IQR [4.0, 16.0]  bias +12.0 s
          no-CPD control (unsmoothed > threshold) median  16.0 s  IQR [4.0, 24.0]  bias  +4.0 s
  offset  detector median  12.0 s  IQR [4.0, 28.0]  bias  -8.0 s | cpd median   8.0 s  IQR [4.0, 20.0]  bias  -4.0 s
          no-CPD control (unsmoothed > threshold) median  20.0 s  IQR [4.0, 40.0]  bias  +4.0 s
events > 30 s (n = 180)
  onset   detector median  16.0 s  IQR [8.0, 20.0]  bias +14.0 s | cpd median   8.0 s  IQR [4.0, 17.0]  bias  +8.0 s
          no-CPD control (unsmoothed > threshold) median  12.0 s  IQR [8.0, 20.0]  bias  +8.0 s
  offset  detector median  36.0 s  IQR [8.0, 109.0]  bias  +4.0 s | cpd median  12.0 s  IQR [4.0, 52.0]  bias  -4.0 s
          no-CPD control (unsmoothed > threshold) median  52.0 s  IQR [24.0, 116.0]  bias +40.0 s
```

- detection guard -> pass
- localization: onset 8.0 vs 16.0 s, offset 12.0 vs 24.0 s -> pass

**ADOPTED: kernel CPD is the onset/offset localizer**

Elapsed 44 s.