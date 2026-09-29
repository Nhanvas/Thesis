# Claude Code task — Figure 3.6 (application screens) and a text audit of the report figures

**Owner:** Project 1 (thesis report). **Written:** 2026-09-29. **Runs at:** repo root `F:/Study/Thesis/Code`.
Writes only `src/figures/make_fig3_6_application.py`, `figures/fig3_11_application.png` and
`figures/archive/` if needed. Never writes `web_demo/`. Figures read existing material and never
recompute results (instructions §6 rule 15).

Run **Part A now**. Run **Part B** only when the raw screenshots from Project 2 exist in
`web_demo/report_handback/`.

---

## Part A — audit the 21 report figures for internal vocabulary (read-only)

The report must not show the project's internal vocabulary. That includes words like "tier", "rlg",
"zrecon", "zlatent", "zgamma", "PREREG", "phase B/C/D", "lever", "held-out", "§0", "seed 42",
"Step N", "ONESHOT", "TE", file paths, or the names of internal documents. Figures were generated
before this rule was enforced, so their rendered text may still contain some of these words.

1. List `figures/*.png` and confirm the count is 21.
2. For each PNG, find its generator in `src/figures/` using `docs/EXHIBIT_SET_FINAL.md` (revision 5)
   and `docs/EXHIBIT_RENUMBER_MAP.md`. List every string the generator renders: titles, axis labels,
   legends, annotations, tick labels built from strings, and panel labels.
3. Report every rendered string that contains internal vocabulary, or a number that is not shown
   elsewhere in the report. Give figure number, file, generator file:line, and the string.
4. **Change nothing.** Boti decides which figures to regenerate, and a regenerated figure must reproduce
   its data exactly.

Also report the house style you find in the generators, so that Part B can match it: figure width and
dpi, font family and sizes, how panel labels are written ("(a)" or "a", bold or not, position), colour
palette, and whether figures carry titles.

---

## Part B — build Figure 3.6

**Inputs.** Three or four PNGs captured by Project 2 from the frozen application build:
`web_demo/report_handback/fig3_6a_import.png`, `fig3_6b_timeline.png`, `fig3_6c_channel_panel.png`,
and optionally `fig3_6d_review.png`. Panel (b) shows the recording and the event that panel (c)
explains; `REPORT_HANDBACK.md` §2 names both.

**Checks before composing.** Stop and report if any of these fails:
- Any visible calendar date or clock time of day. EDF dates are anonymization-shifted to 2057–2075 and
  may never appear. Use OCR (`pytesseract`) if it is available: search for 4-digit years, month names
  and hh:mm:ss patterns. If OCR is unavailable, say so and list what Boti should inspect by eye.
- Any evaluation metric: sensitivity, precision, F1, AUROC, false alarms per day, operating-point
  parameters.
- Any patient identifier other than the CHB-MIT subject and file name.
- The channel panel title must read `Channel-level reconstruction anomaly — Event N`.

**Composition.** Write `src/figures/make_fig3_6_application.py`:
- It reads the PNGs as images and places them as panels. Screenshots are never redrawn or retouched,
  apart from cropping away window chrome and empty margins.
- Layout: the timeline (b) is the widest panel and spans the full width. (a), (c) and (d) if present sit
  in a row below it, scaled to a common height. Keep every screenshot legible at the report's printed
  width of about 6 inches (text width on A4 with 1.5-inch and 1-inch margins); state the effective
  pixel density of the smallest panel.
- Panel labels and fonts follow the house style reported in Part A. No figure title: the caption carries
  it.
- Output: `figures/fig3_11_application.png`, at the same dpi as the other report figures.
- Afterwards, `ls figures/*.png | wc -l` must print 22.

**Report back:**
- the checks, including the OCR output or the list for visual inspection;
- the final size of the figure and the effective resolution of each panel;
- a one-line description of each panel, so that Project 1 can write the caption;
- the command that regenerates the figure.

**Commit** in one `bash -e` block, staging these two paths only: `src/figures/make_fig3_6_application.py`
and `figures/fig3_11_application.png`. Message: `Figure 3.6: application screens`.
