# Subject-level bootstrap: final (family, C = e, cell (5, 0.005), CPD plain) minus references

Reproduction of E8 (seeds 42+1): 0.489 @ 19.78 OK. 4-seed means; B = 10000. E_fine cell (fine grid, <= 25): (15, 0.02, 20.06).

## final - E (15, 0.02)

```
set           quantity                 point    95 % interval       share > 0
all 15        pooled sensitivity      +0.173  [ +0.075,  +0.287]   0.999
all 15        subject-mean sens.      +0.171  [ +0.055,  +0.303]   0.999
all 15        FA/day                  -0.509  [ -6.798,  +4.544]   0.410
without chb12 pooled sensitivity      +0.184  [ +0.050,  +0.315]   0.997
without chb12 subject-mean sens.      +0.173  [ +0.046,  +0.307]   0.998
without chb12 FA/day                  -0.994  [ -7.616,  +4.174]   0.344
```
Levels: final pooled 0.662 @ 19.55 FA/day; E pooled 0.489 @ 20.06 FA/day

## final - E_fine (15, 0.02)

```
set           quantity                 point    95 % interval       share > 0
all 15        pooled sensitivity      +0.173  [ +0.074,  +0.283]   1.000
all 15        subject-mean sens.      +0.171  [ +0.055,  +0.296]   0.999
all 15        FA/day                  -0.509  [ -6.772,  +4.427]   0.405
without chb12 pooled sensitivity      +0.184  [ +0.051,  +0.317]   0.997
without chb12 subject-mean sens.      +0.173  [ +0.049,  +0.313]   0.998
without chb12 FA/day                  -0.994  [ -7.524,  +4.142]   0.355
```
Levels: final pooled 0.662 @ 19.55 FA/day; E_fine pooled 0.489 @ 20.06 FA/day


Elapsed 321 s.