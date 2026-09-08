# Writing Phase — Addendum

`docs/CHAPTER_WRITING_BRIEF.md` was written before the figures, the tables and the caption sheet
existed. It is still the governing document for register, structure and the honesty rules. This file
records what has changed since, and **overrides the brief wherever the two disagree**.

Read this file after the brief and before writing anything.

---

# Part A · Project instructions for a writing account

Paste this as the Project Instructions of each writing project, replacing the research-phase spec.
Change only the chapter number on the first line.

```
You are helping write Chapter N of an undergraduate biomedical engineering thesis:
"Unsupervised Epileptic Seizure Temporal Localization in Scalp EEG using Graph
Autoencoder and Change Point Detection." Boti (Nguyen Quoc Trung Nhan) is the author
and the final decision-maker. Converse in Vietnamese; write the chapter in English.

YOUR SCOPE IS ONE CHAPTER. Do not write, revise or summarise any other chapter.
Four other accounts are writing the others in parallel from the same source files.

AUTHORITY ORDER, on any conflict:
  docs/VERIFIED_NUMBERS.md          every number
  docs/LOCKED_DOCS_ADDENDUM.md      overrides the planning documents
  docs/WRITING_PHASE_ADDENDUM.md    overrides the writing brief
  docs/CHAPTER_WRITING_BRIEF.md     register, structure, honesty rules
  docs/THESIS_OUTLINE_FINAL.md      section order
  tables/tables_chN.md              your chapter's tables, already filled
  docs/CAPTIONS.md                  every caption, already written

THE RULE THAT MATTERS MOST: never write a number you have not read from one of the
files above. Not an estimate, not "approximately", not a rounded value, not a number
recalled from this conversation. If a number is not in VERIFIED_NUMBERS or in your
chapter's table file, it is not a number you may write. Say so and leave a marked
placeholder instead.

DO NOT recompute anything, do not open result CSVs to derive new values, and do not
re-verify numbers that are already in VERIFIED_NUMBERS. That work is closed. Deriving
a new value at writing time is how two chapters end up disagreeing.

DO NOT invent citations. If a source is not in docs/Thesis_Reference_Sheet.md, say so
rather than supplying one from memory. This has already gone wrong once in this project.

Tables are already written in tables/tables_chN.md — use them as they are rather than
rebuilding them in prose. Captions are already written in docs/CAPTIONS.md — use the
text given, and never cut a sentence marked mandatory.

Ask before making any substantive choice. Propose, wait for approval, then write.
```

---

# Part B · What each account opens

Every account opens the four authority documents above. Beyond those:

| Account | Chapter | Also opens |
|---|---|---|
| 1 | Introduction | `tables/tables_ch1.md` · `docs/Thesis_Reference_Sheet.md` |
| 2 | Methodology | `tables/tables_ch2.md` |
| 3 | Results | `tables/tables_ch3.md` |
| 4 | Discussion | `tables/tables_ch4.md` · `tables/tables_ch1.md` for Table 1.1, whose wording Table 4.1 must match |
| 5 | Chapter 5, abstract, front and back matter | `tables/tables_appendix.md` · every other chapter file, for the abstract only |

No account opens `results/`, `src/` or `data/`. Everything needed has been extracted.

---

# Part C · Placeholders now resolved

The brief lists three placeholders. One is resolved and must not be left in any draft.

**`[EXAMPLE PATIENT]` is resolved.** The running example is patient **chb13**, recording
**chb13_62.edf**. It appears in Figure 2.10, Figure 3.4 and Figure 3.10, and Chapters 2 and 3 must
describe the same recording. On that recording, three seizures are annotated, two are matched, and
three detections are false positives.

**`[PENDING BUILD]` remains open.** It applies to Table 3.11, Table 3.12's application row, and
Figures 3.16 to 3.18.

**`[VALUE — source not located]` remains open** and should now be rare, since every table has been
filled from the record.

---

# Part D · Where numbers come from now

Part 2 of the brief tells each account to read values from the underlying modules and result files.
**That is superseded.** Every number the report needs has already been extracted, checked against its
source file, and written into either `docs/VERIFIED_NUMBERS.md` or the chapter's own table file.

Read from those two. Opening a result file at writing time risks producing a value that differs in the
last decimal from the one another chapter quotes, and there is no longer any reason to do it.

The three published values the brief flags for checking against their source papers **have now been
checked**, and five comparator papers were read from source. The results are in `tables/tables_ch1.md`
and `tables/tables_ch4.md`, with the caveats attached to each row.

---

# Part E · Facts established since the brief was written

These are settled, sourced, and belong in the chapters named. None of them is optional.

**The four dataset citations.** The corpus is cited as Guttag (2010), the original publication as
Shoeb (2009), and the platform per its own request. The montage is cited to the clinical montage
guideline. All four are now in the reference sheet. *Chapters 1 and 2.*

**The reconstructed timeline carries substituted scores.** Artifact rejection removes background
windows without recording their positions, so rebuilding a timeline shifts the surviving scores and,
once the stored array is exhausted, fills the remainder by resampling. Across the eight held-out
patients an average of **53.9 percent** of each timeline carries a resampled score, ranging from
**40.0 to 66.9 percent**. The false-alarm rate is measured on those timelines.

This needs its own paragraph in the limitations section, not a clause. Two things must be said and one
must not. Say that the resampling draws from the patient's own background distribution, so the
marginal statistics are preserved. Say that what is lost is temporal autocorrelation, which the change
point stage depends on. **Do not say the bias is small, or conservative, or that it does not affect the
conclusions** — nobody has measured it, and the direction is not established. *Chapter 4, and Figure
2.13 in Chapter 2.*

**The channel annotation was generated automatically.** A language model read rendered segments of the
raw recordings and produced the channel sets. It read the recordings and the summary timings only, and
never the model's own output, so the comparison is not circular. It was **not** produced blind, and it
has **not** been reviewed by a clinician. Every result scored against it is provisional. Because the
annotation was not blind, the within-patient similarity of 0.888 may partly reflect the annotator's own
consistency rather than anatomy alone. *Chapter 3 for the results, Chapter 4 for the limitation.*

**chb06's F1 is undefined at the reported operating point**, not zero. Its sensitivity and precision
are both zero and the harmonic mean of two zeros has no value. *Chapter 3.*

**chb17 does not support the decision-limited grouping.** Earlier project material places chb16 and
chb17 together as decision-limited. Figure 3.8 puts chb17 at 0.782 discrimination and 0.207 event F1 —
just below both reference lines, in the same quadrant as the representation-limited patients. Chapter 4
may group chb16 alone, or discuss chb17 as marginal, but must not assert a grouping the figure
contradicts. *Chapter 4.*

**Directed connectivity is a boundary case, not a clean rejection.** At −0.0339 it sits outside the
0.0338 noise band by one ten-thousandth. Do not write it as decisively falsified. *Chapters 3 and 4.*

**Six alternatives were measured, not seven.** Seven were registered; the seventh, additional
per-channel time-domain features, was never built and belongs in future work rather than in the count.
*Chapter 3.*

**The comparison that carries Chapter 4** is against the two rows of Table 4.1 that share this work's
corpus, scoring level and patient split. Against them, this system produces four to five times fewer
false alarms at a sensitivity about eleven points lower, without using any seizure label. Four caveats
travel with that sentence: the comparator is supervised, uses twenty-four patients rather than
twenty-three, segments at five seconds rather than four, and uses its own event-matching rule.
*Chapter 4.*

**The commercial system's F1 of 0.441 is quoted from a separate evaluation** on different data, not
produced by the 2025 challenge. Attribute it that way or leave it out. *Chapter 4.*

---

# Part F · Figures and tables — what exists

**Twenty-five figures are drawn and final:** 1.1, 1.2, 2.2, 2.3, 2.4, 2.5, 2.8, 2.9, 2.10, 3.1 through
3.15, and 4.1. They are at the root of `figures/`, named `figNN_MM_slug.png`.

**Ten figures are hand-drawn** and arrive separately: 1.3, 1.4, 1.5, 2.1, 2.6, 2.7, 2.11, 2.12, 2.13,
2.14. Write the text as though they exist; the caption for each is already in `docs/CAPTIONS.md`.

**Three figures wait on the application:** 3.16, 3.17, 3.18.

**Every table for Chapters 1 to 4 and the appendices is written** in `tables/`, except Table 2.1's
non-corpus rows, Table 2.11's stage boundaries, and Tables 3.11 and 3.12.

**One caption could not be written from the record.** Figure 2.8 predates the caption sheet and its
axes are not described anywhere in the exhibit list. Account 2 describes it from the figure itself and
must not accept a guessed description.

---

# Part G · Two things no chapter may contain

**Internal vocabulary.** No lever codes, no phase names, no branch nicknames, no operating-point grid
notation, no file paths, no repository terms. If a word appears in this project's notes but not in the
seizure detection literature, it does not belong in the report.

**The superseded numbers.** Five values from a pre-rebuild configuration survive in archived
documents and must never appear as current results: 0.750, 0.829, 0.791, 39.77 and 71.25. A parameter
count of roughly 8.7k is likewise wrong; the model has 3,285 parameters.
