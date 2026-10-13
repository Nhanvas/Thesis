# CUT_PLAN_50p — how to bring the body (Chapters 1–5) to 50 pages, if the supervisor requires it (13/10, chat 7)

**Status: prepared, NOT applied.** Apply only if the supervisor says the 50-page limit is hard. The supervisor's
feedback on the 11/10 draft was "cut too much" and "results not detailed", so every step below moves material
to the appendix or tightens wording; none removes a result or a disclosure.

**Starting point (chat 7 build, LibreOffice render, measured):** body 62 pages — Ch1 12, Ch2 24, Ch3 15,
Ch4 9, Ch5 2 (template margins). Word measured about 2 pages less than LibreOffice on the chat-6 build.
All savings below are **estimated, not measured**; each group is applied, rebuilt and measured before the next.

## Never cut

Tables 9, 11, 13, 14, 16, 17, 18; Section 2.8.2 (held-out vs test-informed disclosure, normalisation, earlier
looks); Section 4.2 (mechanism of each design); Section 4.3 (why the system fails); Figure 14; every number of
the abstract.

## Group A — layout only (no content change), about −6 to −8 pages

| step | change | estimate |
|---|---|---|
| A1 | margins of `Report format.md` (left 1.5 in, others 1 in) instead of the template file — one line in `build_v8.py` (`pgmar` block) | −4 (measured in chat 6: 65 → 61) |
| A2 | tall figures bounded at 5.5 in instead of 6.8 in (`MAXH_IN`): Figures 3, 6, 10, 14, 16 | −1.5 |
| A3 | tables with ≥ 6 columns at 9 pt (Tables 11, 12, 14, 15, 17, 18) if the supervisor accepts | −1 to −2 |

## Group B — move to the appendix (results stay in the report), about −3 pages

| step | change | estimate | renumbering |
|---|---|---|---|
| B1 | Figure 5 (EEG before/after preprocessing) → Appendix A; one sentence stays | −0.7 | Figures 6–16 → 5–15 |
| B2 | Figure 9 (event-scoring rules) → Appendix B; the rule stays in the text | −0.5 | further −1 |
| B3 | Table 15 (Siena per patient) → Appendix D beside Table 24; 3.4.2 keeps its three sentences | −0.8 | Tables 16–18 → 15–17 |
| B4 | Table 10 to the 8 most informative rows (all 15 are in Table 22) | −0.5 | none |

Renumbering is done in the chapter files (markdown captions and every "Table n"/"Figure n" reference), then the
build's cross-reference check must pass (every reference resolves, every exhibit cited).

## Group C — tighter wording (no idea removed), about −3 to −4 pages

| step | where | how | estimate |
|---|---|---|---|
| C1 | Ch2 decision-matrix verdicts (2.3.3, 2.5.1, 2.6.1, 2.9.1) | "This decision was motivated by three factors…" paragraphs to 2–3 sentences each; the matrix carries the detail | −1.5 |
| C2 | Ch2 2.2, 2.4, 2.5.3 | remove repeated definitions (latent vector, robust z) already given once | −0.5 |
| C3 | Ch4 4.2 | one paragraph per design, first sentence = finding, numbers once | −1 |
| C4 | Ch1 1.1.2 and Table 1 | 1.1.2 to one paragraph; Table 1 to 10 rows (drop Shyu, Wang, Bomela — kept in prose) | −1 |

**Total A + B + C ≈ −12 to −15 pages (estimated)** → about 47–50 pages. After each group: rebuild, measure in
LibreOffice, then in Word; run the cross-reference and forbidden-number checks.
