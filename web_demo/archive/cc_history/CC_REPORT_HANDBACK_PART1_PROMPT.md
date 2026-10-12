# CC_REPORT_HANDBACK_PART1_PROMPT.md — Part 1 of REPORT_REQUEST_TO_PROJECT2.md

Prerequisite: run this only after CC_REPORT_HANDBACK_PART0_PROMPT.md has committed and tagged
szscan-frozen-v1, and report_handback/PART0 section of REPORT_HANDBACK.md exists. Work on that
exact commit; do not make any code change in this prompt (read-only, code-reading answers only).

Answer every sub-question of Part 1 (1.1 through 1.4) of REPORT_REQUEST_TO_PROJECT2.md, in the
template's own structure, appended to web_demo/REPORT_HANDBACK.md under "## 1. As built".

Ground rules restated: quote file:line for every factual claim; where the build differs from
SZSCAN_SPEC_v5.md, say so explicitly; no estimates; "not measured" where nothing was measured;
never open chb*-summary.md seizure fields or results/attribution_v7/labels/. For 1.1.2, check
every item the request lists (filtering parameters, channel selection/duplicate T8-P8, CAR
placement, wPLI/AEC alpha, top-20% sparsification, band powers, the three scores, fusion weights,
smoothing window, PELT resolution/min-segment, magnitude filter, merge gap) against the actual
src/dataprep and src/*.py implementations Project 2 imports — list every difference found,
however small, or state "none found after checking: <list>". For 1.1.4, the operating point is
now the fixed mag_pct=50/pen_mult=2.0 from CC_FIX_OPPOINT_REPORT.md — quote its current file:line.
For 1.2.1, quote attribution.py's scoring lines with enough surrounding context to show the abs()
call. For 1.3.2, list every outbound network call path examined (fonts, any CDN reference, any
telemetry) and how it was checked (code read, or the network-off run already done 2026-09-28).

Guards must stay 4/4 (re-run, paste raw output) — this prompt should not need any code change, so
guards passing again is a no-op confirmation, not a fix. No git add/commit/push (this is
documentation added on top of the tagged commit; committing it, if wanted, is a separate step
Boti decides).