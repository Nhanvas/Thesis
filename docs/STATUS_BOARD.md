# STATUS_BOARD — DEFENSE phase (rev 18, 2026-10-17, end of chat D4 rework)

**Read this first in every chat.** It says what is done, what is open, what the author still has to give or approve,
where every file lives and what the next chat does. At the end of every chat the board is rewritten as a whole file
(new rev number) and delivered with the project file list.

**Practical facts.**
- Defense **05–06/11/2026**, in English; 12–15 min of speaking **including the demo**; questions after (length not yet known).
- Reviewer: **TS. Ngô Thị Lụa**. Chair on the report's approval page: Assoc. Prof. Nguyễn Thị Hiệp.
- Supervisor meetings Thursdays 08:00 (22/10, 29/10).

**Report.**
- Report-phase history: board rev 9 (2026-10-13) in git.
- The report is locked when it is submitted to the faculty on 17/10/2026.

**For any slide work, read `DECK_BRIEF.md` (how slides look and flow; every author request so far) and
`SLIDE_OUTLINE.md` rev 2 (what each slide carries) before anything else.**

---

## 1 · Chat protocol (binding)

1. One task per chat from section 5, unless the author decides otherwise.
2. **Start:** read this board → the files named for the task → nothing else unless the task needs it.
3. **End:**
   - (a) this board rewritten (rev + 1);
   - (b) **one** list for the author (project files add / replace / delete, with local paths; instruction text if changed);
   - (c) the start prompt of the next chat.
4. **Where things live.**
   - Defense material lives in `F:/Study/Thesis/Defense/` (private, outside the repository).
   - The repository (public) holds this board and the instructions; cloud chats clone it to read code, results and `web_demo/`.
   - Cloud chats cannot open the author's local folders: a local file a chat needs is attached.
5. Every number on a slide, in the script or in an answer matches the final report **and** `NUMBERS_LOCK.md`. A number not in that file goes to the author.
6. **No script before the slide freeze** (anh Trí).
7. **Questions come from the slides and the talk** (author, 16/10): every number on a main slide has an answer in `QA_BANK.md` or a backup slide.
8. **Requests are not repeated** (author, 17/10): every author request about slides is logged in `DECK_BRIEF.md` §1. A chat reads it before proposing anything and never re-asks what is there.

## 2 · Where things stand (17/10)

| track | state | next |
|---|---|---|
| Report | submission copy checked 16/10; to the faculty 17/10 | author confirms the submission; re-exports `Thesis_Final_Report.md` if the text changed |
| Numbers (D1a) | `notes/NUMBERS_LOCK.md` (N1–N9 approved) | closed; new figure numbers are checked against it |
| Figures (D1b) | `slides/figs/F1–F10` + `HANDBACK.md`, all gates OK | closed; new result figures R1–R12 → D4c |
| Study guide (D2) | `content/STUDY_GUIDE_part1_vi.md`, `part2_vi.md` | author studies |
| Q&A bank (D3) | `qa/QA_BANK.md`: 79 questions, A1–A21 | A# → B# mapping in SLIDE_OUTLINE §4; C8-1 answer to update if P-D4 = yes |
| **Slide design (D4 rework, 16–17/10)** | three deck iterations (v1 Canva build sheet → v2 → **v3 Slides artifact**); author feedback A1–A17 logged; senior's decks studied (BME11 oral = the style to follow; HD4 defense = committee habits) → **`outline/DECK_BRIEF.md` (new)** + **`outline/SLIDE_OUTLINE.md` rev 2** (v4 plan: 19 content slides + Thank you, R-figures, 26 backups) | **open decisions P-D1…P-D8 → then D4c** |
| Deck (artifact) | "Thesis Defense Slides v3": https://claude.ai/artifact/RQNQLEV2gmfjrcrZUuzid9. A **draft**: its storytelling, wording and assets (diagrams, icons, logos, F-figures) are reused; layout, section structure and result slides are rebuilt to v4 in D4d | D4d updates the **same** artifact |
| App (D1c) | `notes/APP_FACTS.md` | slides 17–18 of v4; demo checklist in D8 |
| Repository | public; `web_demo/` identical to tag `szscan-frozen-v4.1` | read only |
| Defense rubric | not given yet; working rubric = `RUBRIC_MAP.md` | re-run SLIDE_OUTLINE §5 when known |
| Committee | — | author adds info (P1) |
| Slide tool | **Slides artifact → download .pptx → Canva** (author finishes in Canva); 16:9; purple title slide with both logos (midterm look) | — |

## 3 · Feedback and rules in force

| # | source | rule | where it lands |
|---|---|---|---|
| R1 | anh Trí | slides matter more than the report; finish early | plan, section 5 |
| R2 | anh Trí | app briefly: technology per layer, which does what; a demo that runs is enough | v4 slides 17–18 |
| R3 | anh Trí / cô | no AI images. Result figures come from scripts on committed results. Schematics are self-drawn (P-D4) | DECK_BRIEF §5; SLIDE_OUTLINE §3 |
| R4 | cô 15/10 | understand every plot; check results are correct | D1, D2 done |
| R5 | lab notes | answer from the rubric, not only the thesis | D3; SLIDE_OUTLINE §5 |
| R6 | lab notes | novelty and contribution versus prior research | v4 slides 5, 19; B20 |
| R7 | lab notes | backup slides after References, with page numbers | v4: References → Thank you → B1–B26 |
| R8 | lab notes | not too little, not too much text | DECK_BRIEF §3.3 |
| R9 | lab notes | slide title shows section and main message | DECK_BRIEF §3.2: numbered section label + keyword title + coloured takeaway (P-D8) |
| R10 | lab notes | ≤ 20 main slides | 19 content + Thank you |
| R11 | lab notes | every rubric item has scorable content | SLIDE_OUTLINE §5 |
| R12 | lab notes | look at seniors' slides | **done 17/10** (DECK_BRIEF §2; `SAMPLE_BME11_oral.pdf`) |
| R13 | lab notes | demo prepared carefully: patient ingested beforehand, video fallback | slide 18 + B26 → D8 |
| **R14** | **author 17/10** | slides ≠ report: sequential pitch-style storytelling for listeners who have not read the report | DECK_BRIEF §0, §4 |
| **R15** | **author 17/10** | follow the BME11 oral style closely; HD4 for understanding | DECK_BRIEF §2–§3 |
| **R16** | **author 17/10** | Background explains disease → impact → clinician pain → mechanism → why graph / GAE, with **no dataset numbers** | SLIDE_OUTLINE slides 3–6, 9 |
| **R17** | **author 17/10** | researcher-style full sentences, no repeated ideas, keyword titles, highlighted keywords, little text | DECK_BRIEF §3.2–§3.4 |
| **R18** | **author 17/10** | paper-style diagrams (GAE etc.), app tool diagram with logos | DECK_BRIEF §5 |
| **R19** | **author 17/10 + senior** | results as **coded figures**, not text or tables; **many visual backups**; no appendix index | SLIDE_OUTLINE §3–§4 |

## 4 · Decisions

- **D0–D3:** see rev 13.
- **D4 / D4b (16/10):** see rev 17 in git. Still valid:
  - D4-2: demo slot 1:30 on chb03 ingested the evening before; fallback after 10 s.
  - D4-3, first part: "4 seeds" label on onset numbers; nothing on network blocking (N2).
  - D4b-2: Reviewer on the title slide.
  - D4b-4: midterm illustrations and earlier-pipeline diagrams are not reused.
  - D4b-5: References list only works cited on slides.
- **Superseded 17/10 by the author's feedback** (details in DECK_BRIEF §7):
  - `SLIDE_DECK_v1.md` and SLIDE_OUTLINE rev c §2–§5 → artifact deck + SLIDE_OUTLINE rev 2;
  - D4b-3 "no Thank-you slide" → Thank you after References;
  - appendix index → dropped;
  - "0.4 %" on slide 2 → dropped;
  - D4-3 "benchmark scatter not used" → reopened as P-D7.
- **Approved earlier:** N1–N9; P5 (equal weights only in Q&A); P7; P3 answer C8-2; report fixes R1.
- **Open (author):**
  - **P-D1 … P-D8** (SLIDE_OUTLINE §6, each with a recommendation);
  - P1 committee research fields → `Defense/inputs/committee.md`.

## 5 · Plan of chats

| # | date | task | output (in `F:/Study/Thesis/Defense/`) |
|---|---|---|---|
| D0–D3 | 15–16/10 ✔ | plan; numbers, provenance, app facts; study guide; Q&A bank | see rev 17 |
| D4 / D4b | 16/10 ✔ | outline rev c; Canva build sheet v1 | superseded 17/10 |
| D4 rework | 16–17/10 ✔ | deck v2 → v3 (Slides artifact) on author feedback; seniors' decks studied | `outline/DECK_BRIEF.md`, `outline/SLIDE_OUTLINE.md` rev 2; artifact v3 |
| **D4c** | **18/10** | ask P-D1…P-D8 → code result figures R1, R3, R7–R12 (+ R2, R5 per P-D7) from committed results; upload them to the deck artifact's asset store; update QA_BANK C8-1 text if P-D4 = yes | `slides/figs/make_defense_figs.py`, `R*.png/.svg`, `HANDBACK_R.md` |
| **D4d** | 19/10 | rebuild **main slides 1–20 + References** of the same artifact to v4 (DECK_BRIEF + SLIDE_OUTLINE rev 2) | artifact v4 |
| **D4e** | 20/10 | backup slides B1–B26 in the artifact | artifact v4 complete |
| — | 20–21/10 | author: download .pptx → Canva, adjust | `slides/Defense_slides_v4.pdf` |
| D5 | 21/10 | review: numbers vs NUMBERS_LOCK (`xanh`), titles, figure sources, rubric, text density, English (`en`), compliance with DECK_BRIEF → cô 22/10 08:00, anh Trí | review list |
| D6 | ≈ 26–27/10 | apply feedback → **slide freeze** | `slides/…_FROZEN` |
| D7 | 28–30/10 | English script per slide, timed | `script/` |
| D8 | 30/10–04/11 | rehearsal: mock committee in English, timing, demo checklist, fallback video | `demo/DEMO_CHECKLIST.md` |

**Start prompt of chat D4c (copy):**
> Chat D4c — Result figures for the defense deck. Read `STATUS_BOARD.md` (rev 18) and the instructions (rev
> 2026-10-17e), then `DECK_BRIEF.md`, `SLIDE_OUTLINE.md` (rev 2: §3, §6), `NUMBERS_LOCK.md`.
> 1. First, ask me P-D1…P-D8 in one go (SLIDE_OUTLINE §6, recommendation first).
> 2. Then clone `github.com/Nhanvas/Thesis` (read only), **open each source file before using it**, and code the figures
>    R1, R3, R7, R8, R9, R10, R11, R12 (+ R2, R5 if P-D7 = yes):
>    - read committed results only, never recompute;
>    - every number on a figure must be in NUMBERS_LOCK, with set · seed · aggregate labels;
>    - style per DECK_BRIEF §5 and SLIDE_OUTLINE §3; layered exports for R1 and R3;
>    - view each figure before handing it over.
> 3. Upload the figures to the asset store of the deck artifact https://claude.ai/artifact/RQNQLEV2gmfjrcrZUuzid9.
> 4. Give me a zip with `make_defense_figs.py`, the PNG/SVG files and `HANDBACK_R.md` (sources, gates, numbers shown).
> 5. If P-D4 = yes: the new text of QA_BANK C8-1.
>
> End: board rev 19, project file list, prompt of chat D4d.

## 6 · Which file for what

| File | Use it to | When |
|---|---|---|
| **`outline/DECK_BRIEF.md`** | every author request, the sample lessons, presentation rules, design system, tools | **before any slide work** |
| **`outline/SLIDE_OUTLINE.md` (rev 2)** | content of each main slide, R-figures to code, backup list, rubric coverage, open decisions | D4c–D6 |
| `SAMPLE_BME11_oral.pdf` | the style to follow (20-slide oral of a lab senior) | D4c–D6 |
| deck artifact (link in §2) | the deck itself; download .pptx for Canva | D4d onward |
| `slides/gen/diagrams.py`, `icons.py` | redraw schematics / recolour icons (matplotlib + Inter) | if a schematic changes |
| `notes/NUMBERS_LOCK.md` | check any number | every slide, every answer |
| `content/STUDY_GUIDE_part1_vi.md`, `part2_vi.md` | understand methods and results | study, rehearsal |
| `qa/QA_BANK.md` | rehearse answers; A# ↔ B# in SLIDE_OUTLINE §4 | daily to 05/11 |
| `notes/APP_FACTS.md` | app layers, demo facts | slides 17–18, B23, D8 |
| `notes/FIGURE_PROVENANCE.md` | internal proof of figure sources | only if asked |
| `slides/figs/*` | F1–F10 (done), R1–R12 (D4c) | building |

## 7 · Layout

```
F:/Study/Thesis/
  Code/                       repository (public): docs/STATUS_BOARD.md, docs/PROJECT_INSTRUCTIONS.md, results/, src/, web_demo/
  Reports/final/              submitted report (.docx) + Thesis_Final_Report.md
  Defense/                    private, not committed
    inputs/      rubric, committee (P1), lab_slides/ (SAMPLE_BME11_oral.pdf, HD4 deck), midterm slides
    notes/       NUMBERS_LOCK.md, FIGURE_PROVENANCE.md, APP_FACTS.md
    content/     study guide (Vietnamese)
    qa/          QA_BANK.md
    outline/     DECK_BRIEF.md, SLIDE_OUTLINE.md (rev 2)
    slides/      figs/ (F1–F10, make_slide_figs.py, HANDBACK.md; R-figures from D4c), gen/ (diagrams.py, icons.py),
                 Defense_slides_v4.pdf (author, from Canva)
    script/  demo/
  Archive/2026-10-17/         SLIDE_DECK_v1.md, SLIDE_OUTLINE_rev_c.md (superseded)
```

## 8 · Where the numbers are

| content | file |
|---|---|
| every number of the final system, decisions | `docs/PERF_PHASE_RECORD.md` (rev R), the authority |
| what the committee read | `Thesis_Final_Report.md` |
| **numbers allowed on slides** | `Defense/notes/NUMBERS_LOCK.md` |
| what each slide carries | `Defense/outline/SLIDE_OUTLINE.md` rev 2 |
| application facts | `Defense/notes/APP_FACTS.md` |
| answers to committee questions | `Defense/qa/QA_BANK.md` |
| benchmark entries on Siena | `docs/BENCHMARK_CHECK_szcore_c57da2f.md` |

## 9 · Decisions log

- Report phase (2026-10-08 → 13): board rev 9 in git.
- 2026-10-15: report submitted after the author's revision; anh Trí's feedback; defense phase opened (D0).
- 2026-10-16: D1, D2a/b, D3, D4, D4b done (numbers, study guide, Q&A bank, outline rev c, Canva build sheet v1).
- 2026-10-17: D4 rework.
  - v2, then v3 of the deck built as a Slides artifact after the author's feedback (slides ≠ report; storytelling;
    general Background; researcher-style wording; paper-style diagrams; app diagram with logos).
  - The seniors' decks were studied: BME11 oral = style to follow; HD4 defense = committee habits.
  - `DECK_BRIEF.md` (new) and `SLIDE_OUTLINE.md` rev 2 record every request and the v4 plan.
  - Instructions → rev 2026-10-17e.
