# Prompt for `en` — English polish of the v8 chapter files (13/10, after chat 7)

Attach: the 7 files of `Reports/v8/chapters/` and `Reports/v8/appendix/` (Front_matter_v8.md,
Chapter_1 … Chapter_5, Appendix_v8.md), `PROSE_STYLE_SPEC.md`, and `REPORT_OUTLINE_v8.md` (for section 7,
the fixed terms). Paste the text below.

---

You are polishing the English of an undergraduate thesis in biomedical engineering. Readers are examiners who
did not do the work. Follow `PROSE_STYLE_SPEC.md`.

Do:
- Fix grammar, articles and agreement; join short, choppy sentences into fluent ones; add a linking phrase
  where two paragraphs or sentences do not connect; prefer plain words over jargon; keep an academic,
  impersonal tone (no "I", "my", "we").
- Keep units written directly after numbers (10%, 4s, 60Hz, 30min); write "false alarms per day" in words in
  prose.

Do not change:
- any number, any citation [n], any reference to a Section, Table, Figure, Equation or Appendix;
- the strength of a claim (words such as "suggests", "about", "slightly", "not tested", "computed");
- the fixed terms of the outline (section 7), e.g. development patients, held-out evaluation, final system
  (test-informed), external validation, pooled / per-patient mean, channel-level latent anomaly, ensemble
  anomaly score, review application;
- table rows, captions ("Table n: …", "[Figure n: …]"), equations (```latex blocks) and the section
  headings;
- anything under "# Notes — not part of the report" (leave it exactly as it is).

Return each file complete, in markdown, with the same file name. After the files, give one short list of the
sentences where you changed meaning-bearing words (if any), so they can be checked.
