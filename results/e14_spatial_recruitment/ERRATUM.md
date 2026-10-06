# ERRATUM — results/e14_spatial_recruitment/SUMMARY.md (commit e292234)

Added 2026-10-07. The SUMMARY above was produced by a script whose decision line omitted the
mechanism check that its own docstring declares required ("Mechanism check (required to read a pass
as a pass): flagged share in the top-2 % non-ictal tail falls below L's (E12: 0.87)").

- G1, G2, G3 passed (0.622 vs 0.589; validation 0.867; 12/15 subjects).
- The mechanism check FAILED: tail flagged share 0.95, not below 0.87.
- Correct verdict under the pre-registration: **NOT adopted as written; nothing frozen; no test look.**
  The printed "ADOPTED -> FROZEN" line is void.
- Reading: an empirical gain at <= 25 FA/day not explained by the spread hypothesis
  (channel mean 0.601 is close to S9 0.622). S9 remains the reference candidate for E15.
- The decision line in `src/e14_spatial_recruitment.py` is corrected in the commit that adds this file;
  the SUMMARY numbers are unchanged and are not regenerated.
