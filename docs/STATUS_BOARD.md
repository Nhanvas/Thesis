# STATUS_BOARD — DEFENSE phase (rev 25, 2026-10-20, end of chat D4g: 5 fixes + documented appendix)

**Read this first in every chat.** It says what is done, what is open, what the author still has to give or approve,
where every file lives and what the next chat does. At the end of every chat the board is rewritten as a whole file
(new rev number) and delivered with the project file list.

**Practical facts.**
- Defense **05–06/11/2026**, in English; 12–15 min of speaking **including the demo**; questions after.
- Reviewer: **TS. Ngô Thị Lụa** (expected to focus on performance: why the metrics are low, other models, novelty).
  Chair on the report's approval page: Assoc. Prof. Nguyễn Thị Hiệp.
- Supervisor meetings Thursdays 08:00 (22/10, 29/10).

**Report.** Locked at the faculty submission (17/10/2026). Report-phase history: board rev 9 in git.

**For any slide work, read `DECK_BRIEF.md` rev 3.3 (requests A1–A33, lessons L1–L17) and `SLIDE_OUTLINE.md` rev 4
(page map of the Canva deck 1–69 with the state of every page) before anything else.**

---

## 1 · Chat protocol (binding)

1. One task per chat from section 5, unless the author decides otherwise.
2. **Start:** read this board → the files named for the task → nothing else unless the task needs it.
3. **End:** (a) this board rewritten (rev + 1); (b) **one** list for the author (project files add / replace / delete,
   with local paths); (c) the start prompt of the next chat.
4. Defense material lives in `F:/Study/Thesis/Defense/` (private). The repository (public) holds this board; cloud
   chats clone it to read code and results. A local file a chat needs is attached.
5. Every number on a slide, in the script or in an answer matches the final report **and** `NUMBERS_LOCK.md`.
6. **No script before the slide freeze.**
7. Every number on a main slide has an answer in `QA_BANK.md` or an appendix page.
8. Requests are not repeated: every author request about slides is logged in `DECK_BRIEF.md` §1.
9. **Before sending anything for approval, render and look at every changed slide** (A24).

## 2 · Where things stand (20/10, end of D4g)

| track | state | next |
|---|---|---|
| Report | submitted 17/10 | — |
| Numbers | `notes/NUMBERS_LOCK.md` §1–§15 (§15: slide-4 sources, dataset facts, appendix-only values) | D5: `xanh` check of the Canva deck |
| Study guide (D2) | `content/STUDY_GUIDE_part1_vi.md`, `part2_vi.md` | author studies |
| Q&A bank (D3) | `qa/QA_BANK.md` + §14 C9 | D5: point each question to its appendix page (A–H) |
| Slide design | `outline/DECK_BRIEF.md` **rev 3.3**, `outline/SLIDE_OUTLINE.md` **rev 4** | — |
| **Deck** | Content baseline = author's Canva deck `Defense/slides/Thesis_final_slide.pdf`. **Artifact https://claude.ai/artifact/RQNQLEV2gmfjrcrZUuzid9 v64 = D4g pack** (31 pages): fixed p2, p4, p6, p25; **References one page p26** (main-slide citations only, A33); 26 new appendix pages (I1 removed by the author). Author pastes them into Canva, applies the text fixes and renames of SLIDE_OUTLINE rev 4 | **author in Canva** (20–21/10) → D5 review |
| Slide 3 image | WHO numbers re-checked; no chart on the WHO fact sheet; the WHO 2019 summary has no image either (author 20/10) | **author** finds an existing image (A32, L14) |
| App (D1c) | `notes/APP_FACTS.md` | — |
| Demo prep (A22) | `Defense/demo/CC_DEMO_PREP.md` | author runs it; video into Appendix G4 (p67) |
| Repository | public; `web_demo/` = tag `szscan-frozen-v4.1`; figures read at `45a17e2` | read only |
| Defense rubric | not given; working rubric = `RUBRIC_MAP.md` (coverage in SLIDE_OUTLINE rev 4 §3) | re-run when known |
| Committee | — | author adds info (P1) |

## 3 · Feedback and rules in force

R1–R27 of rev 24 stand (anh Trí, cô, lab notes, author 17–19/10). Added in D4g (details DECK_BRIEF A32–A33, L14–L17):

| # | source | rule |
|---|---|---|
| R28 | author 20/10 | Background images are **found, existing images** — never self-drawn, not even a coded chart (L14) |
| R29 | author 20/10 | Image sources are **not credited** on slides or in References |
| R30 | author 20/10 | A request about **how** a slide shows its content does not change **what** it says (slide 4 keeps its title and its EEG-and-challenges message, shown along the review process) (L15) |
| R32 | author 20/10 | **References = one page, only works cited on the main slides** (like the sample); appendix pages keep their own source lines (L17) |
| R33 | author 20/10 | Multi-step commands come as a **`.sh` file in the zip + one command line**, never a long pasted heredoc (L16) |
| R31 | A31 / D4g | Goals are closed with neutral labels: Aim + Goal 1–2 registered (Achieved; Goal 2 "achieved and evaluated", offset a limitation), Goal 3–4 added (Evaluated / Delivered); numbers stay, no "not met / fail" wording on slides |

## 4 · Decisions

- Earlier decisions D0–D4f and P-D1…P-D11: rev 22–24 (in git).
- **D4g (20/10):**
  - ToC sub-lines, slide 4 (Record → Read → Mark → Decide with "Challenge" lines; sources Timpte 2023, Tatum 2022,
    Tatum 2011, Halford 2015), slide 6 tags, Conclusion table, page 44 → report Fig. 10, text fixes (p8, p14, p18, p20,
    p23, p40): built / listed by Claude; the author did not object to the proposals (R27).
  - HCMC prevalence line on slide 3 accepted (HD4 shows the same number).
  - Appendix A–H fixed at 42 pages (28–69); References one page (26), Thank you 27; I1 (Registered vs Delivered)
    removed by the author. H2 includes two rows from the experiment record (multi-relational GAE,
    LSTM branch), labelled on the page; VGAE and learned-graph left out (only in `docs/archive`, never cited).
  - P-D9 (Timpte line): kept, now cited on slide 4 — closed.
- **Open (author):** slide-3 image; P1 committee research fields → `Defense/inputs/committee.md`; H2 option (b) can be
  reversed to report-only rows if the author prefers.

## 5 · Plan of chats

| # | date | task | output |
|---|---|---|---|
| D0–D4f | 15–19/10 ✔ | plan, numbers, study guide, Q&A, design, figures, deck rev 3 | rev 22–24 |
| ✔ | 20/10 | author: Canva deck, kept ~80 % (A31) | `slides/Thesis_final_slide.pdf` |
| **D4g** | **20/10 ✔** | 5 fixes + documented appendix A–H (A31–A33) | artifact v64 (31 pages); NL §15; DECK_BRIEF rev 3.3; SLIDE_OUTLINE rev 4; `slides/gen/d4g/`, `slides/figs/d4g/` |
| — | 20–21/10 | **author:** paste the D4g pages into Canva, apply SLIDE_OUTLINE rev 4 fixes and renames, set Calibri, add the slide-3 image; export `Thesis_final_slide_v2.pdf` | Canva deck v2 |
| **D5** | 21–22/10 | review of Canva deck v2: numbers vs NUMBERS_LOCK (`xanh`), English (`en`), rubric (`boti`), image legibility, DECK_BRIEF A1–A33, L1–L17; QA_BANK → appendix pages; list for cô (22/10) and anh Trí | review list; QA page map |
| D6 | ≈ 26–27/10 | apply feedback → **slide freeze** | `slides/…_FROZEN` |
| D7 | 28–30/10 | English script per slide, timed | `script/` |
| D8 | 30/10–04/11 | rehearsal: mock committee, timing, demo checklist, fallback video | `demo/DEMO_CHECKLIST.md` |

**Start prompt of chat D5 (copy):**
> Chat D5 — Review my Canva deck v2 before cô (22/10). Read `STATUS_BOARD.md` (rev 25), the instructions,
> `DECK_BRIEF.md` (rev 3.3: A1–A33, L1–L17), `SLIDE_OUTLINE.md` (rev 4: page map 1–69), `NUMBERS_LOCK.md` (§1–§15),
> `QA_BANK.md` (incl. §14 C9) and `RUBRIC_MAP.md`. Attached: `Thesis_final_slide_v2.pdf` (Canva, after the D4g pages).
> 1. Check every page against SLIDE_OUTLINE rev 4 (fixes applied, renames, page numbers 1–69, one References page, Calibri, nothing lost in
>    the pptx → Canva copy). 2. Check every number on every page against NUMBERS_LOCK with its label (set · seed ·
>    aggregate) — give the `xanh` prompt and do the check yourself. 3. English and wording (`en` prompt), rubric coverage
>    (`boti` prompt). 4. Image legibility and image ↔ text agreement (L1–L10, L14). 5. Map every QA_BANK question to the
>    main or appendix page that answers it; list gaps. Output: one review list (page · problem · exact fix), the three
>    account prompts, and a short summary for cô. End: board rev 26, file list, prompt of chat D6 (freeze).

## 6 · Which file for what

| File | Use it to | When |
|---|---|---|
| **`outline/DECK_BRIEF.md` (rev 3.3)** | every author request (A1–A33), lessons L1–L17, presentation rules, design system | before any slide work |
| **`outline/SLIDE_OUTLINE.md` (rev 4)** | page map 1–69, state of every page, Canva fixes and renames, rubric coverage | D5–D7 |
| deck artifact (link in §2) | the D4g pack; download .pptx for Canva | until the freeze |
| `slides/gen/d4g/` | scripts of the D4g pages (Canva style, gated figures, equations, preview/overflow check) | only if a D4g page changes |
| `slides/gen/` (rev 3), `slides/figs/rev3/` | record of rev 3 slides and figures | only if a rev 3 figure changes |
| `notes/NUMBERS_LOCK.md` | check any number (§15 = D4g) | every slide, every answer |
| `qa/QA_BANK.md` (§14 C9) | rehearse answers | daily to 05/11 |
| `content/STUDY_GUIDE_part1_vi.md`, `part2_vi.md` | understand methods and results | study |
| `notes/APP_FACTS.md` | app layers, demo facts | slide 21, D8 |

## 7 · Layout

```
F:/Study/Thesis/
  Code/                       repository (public): docs/STATUS_BOARD.md, results/, src/, web_demo/
  Reports/final/              submitted report (.docx) + Thesis_Final_Report.md
  Defense/                    private, not committed
    inputs/      rubric, committee (P1), lab_slides/ (SAMPLE_BME11_oral.pdf, HD4 deck), images/
    notes/       NUMBERS_LOCK.md (§15 D4g), FIGURE_PROVENANCE.md, APP_FACTS.md
    content/     study guide (Vietnamese)
    qa/          QA_BANK.md (§14 C9)
    outline/     DECK_BRIEF.md (rev 3.3), SLIDE_OUTLINE.md (rev 4)
    slides/      Thesis_final_slide.pdf (Canva, 20/10); figs/ (D1b, D4c, rev3/, d4g/); gen/ (v4, rev 3, d4g/)
    script/
    demo/        CC_DEMO_PREP.md, then DEMO_CHECKLIST.md, demo_fallback_chb03.mp4, DEMO_PREP_HANDBACK.md
  Agent/inbox/                hand-over tray (D4g_bundle.zip)
  Archive/2026-10-20/         DECK_BRIEF rev 3.1–3.2, SLIDE_OUTLINE rev 3.1, D4g_BRIEF.md
```

## 8 · Where the numbers are

| content | file |
|---|---|
| every number of the final system | `docs/PERF_PHASE_RECORD.md` (rev R) |
| what the committee read | `Thesis_Final_Report.md` |
| numbers allowed on slides | `Defense/notes/NUMBERS_LOCK.md` (§1–§15) |
| benchmark entries on Siena | `docs/BENCHMARK_CHECK_szcore_c57da2f.md` |

## 9 · Decisions log

- 2026-10-15 → 19: defense phase opened; D1–D4f (rev 22–24 in git).
- 2026-10-20 (morning): author's Canva deck (46 pages); D4g brief prepared.
- 2026-10-20 (afternoon, D4g): proposals put to the author; answers A32 (background = found images only; HCMC
  prevalence accepted; no image credit; slide 4 keeps its content, shown as a process). Built in the artifact (v61,
  Canva style): p2, p4, p6, p25, References, 27 appendix pages (A1–A4, B1–B4, C1, C3, C4, C6, C7, D1, D3, E1, E3, E6,
  E10, F1, F3, F4, G1, G2, H1, H2, I1); every page rendered locally and checked for overflow and legibility; new sources
  verified at source (Tatum 2022, Tatum 2011, Halford 2015, Shah 2018, Andrzejak 2001, Stevenson 2019) → NL §15.
- 2026-10-20 (evening, D4g): author: WHO 2019 summary has no image; References shortened to the 23 works cited on the
  main slides (one page); I1 removed (author); A1 keeps the author's own edit; appendix renumbered 28–69; artifact
  v64. Command delivery changed to a script file + one line (the pasted heredoc did not run in Git Bash).
