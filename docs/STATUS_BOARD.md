# STATUS_BOARD — DEFENSE phase (rev 20, 2026-10-17, end of chat D4c–D4d)

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

**For any slide work, read `DECK_BRIEF.md` (rev 2: how slides look and flow; every author request so far) and
`SLIDE_OUTLINE.md` rev 2.1 (what each slide carries; §7 = figures, decisions, v4 slide map) before anything else.**

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

## 2 · Where things stand (17/10, end of D4c–D4d)

| track | state | next |
|---|---|---|
| Report | submission copy checked 16/10; to the faculty 17/10 | author confirms the submission; re-exports `Thesis_Final_Report.md` if the text changed |
| Numbers (D1a) | `notes/NUMBERS_LOCK.md` (N1–N9 approved); **§13 added: Moura 2014 (approved), WHO wording, slide-15 table** | closed |
| Figures (D1b) | `slides/figs/F1–F10` + `HANDBACK.md`, all gates OK | closed |
| **Result figures (D4c)** | **done 17/10:** R1, R2, R3, R7, R7b, R8, R9, R10, R11, R12 (**R5 retired, A19**) by `slides/figs/make_defense_figs.py` (reads committed results at repo `45bfe64`, imports `make_v8_exhibits.py`; **ALL GATES PASSED**); R4 = F8, R6 = F5; layers for R1 (6) and R3 (3); every figure viewed and fixed; `HANDBACK_R.md` lists sources, gates, numbers shown | used by D4d / D4e |
| Study guide (D2) | `content/STUDY_GUIDE_part1_vi.md`, `part2_vi.md` | author studies |
| Q&A bank (D3) | `qa/QA_BANK.md`: 79 questions, A1–A21; **C8-1 rewritten (P-D4 = yes)** via `apply_d4c_patches.py` | A# → B# mapping in SLIDE_OUTLINE §4 |
| Slide design (D4 rework) | `outline/DECK_BRIEF.md` **rev 2** (A18–A20 added) + `outline/SLIDE_OUTLINE.md` **rev 2.1** (§6 decided, §7 figures + v4 slide map) | — |
| **Deck (artifact)** | "Thesis Defense Slides v4": https://claude.ai/artifact/RQNQLEV2gmfjrcrZUuzid9 (Slides type; `project/deck.json` + `project/slides/<id>.html`). **D4d done 17/10:** main slides s01–s19, References ref1–ref2, Thank you s23 (page 22) rebuilt to v4 — 5 numbered sections, keyword titles + coloured takeaway, logo footer, R-figures from the asset store; v3 s20–s22, ref3 removed (content merged). **Backups b01–b14 + demo are still v3** | **D4e**: backups B1–B26 |
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
| R3 | anh Trí / cô | no AI images. Result figures come from scripts on committed results. Schematics are self-drawn (P-D4 approved) | DECK_BRIEF §5; SLIDE_OUTLINE §3, §7 |
| R4 | cô 15/10 | understand every plot; check results are correct | D1, D2 done; D4c gates |
| R5 | lab notes | answer from the rubric, not only the thesis | D3; SLIDE_OUTLINE §5 |
| R6 | lab notes | novelty and contribution versus prior research | v4 slides 5, 19; B20 |
| R7 | lab notes | backup slides after References, with page numbers | v4: References → Thank you → B1–B26 |
| R8 | lab notes | not too little, not too much text | DECK_BRIEF §3.3 |
| R9 | lab notes | slide title shows section and main message | DECK_BRIEF §3.2 (P-D8 approved) |
| R10 | lab notes | ≤ 20 main slides | 19 content + Thank you |
| R11 | lab notes | every rubric item has scorable content | SLIDE_OUTLINE §5 |
| R12 | lab notes | look at seniors' slides | done 17/10 (DECK_BRIEF §2; `SAMPLE_BME11_oral.pdf`) |
| R13 | lab notes | demo prepared carefully: patient ingested beforehand, video fallback | slide 18 + B26 → D8 |
| R14 | author 17/10 | slides ≠ report: sequential pitch-style storytelling for listeners who have not read the report | DECK_BRIEF §0, §4 |
| R15 | author 17/10 | follow the BME11 oral style closely; HD4 for understanding | DECK_BRIEF §2–§3 |
| R16 | author 17/10 | Background explains disease → impact → clinician pain → mechanism → why graph / GAE, with **no dataset numbers** | SLIDE_OUTLINE slides 3–6, 9 |
| R17 | author 17/10 | researcher-style full sentences, no repeated ideas, keyword titles, highlighted keywords, little text | DECK_BRIEF §3.2–§3.4 |
| R18 | author 17/10 | paper-style diagrams (GAE etc.), app tool diagram with logos | DECK_BRIEF §5 |
| R19 | author 17/10 + senior | results as **coded figures**, not text or tables; **many visual backups**; no appendix index | SLIDE_OUTLINE §3–§4, §7 |
| R20 | author 17/10 (D4c) | Background numbers may come from verified papers outside the report (web search allowed); each still goes to the author and into NUMBERS_LOCK before a slide | DECK_BRIEF A18; NL §13 |
| **R21** | **author 17/10 (D4d)** | **comparisons with other studies are TABLES, never figures** (said many times during the report); Background facts stated generally, not tied to the thesis | DECK_BRIEF A19, A20 |

## 4 · Decisions

- **D0–D3:** see rev 13.
- **D4 / D4b (16/10):** see rev 17 in git. Still valid:
  - D4-2: demo slot 1:30 on chb03 ingested the evening before; fallback after 10 s.
  - D4-3, first part: "4 seeds" label on onset numbers; nothing on network blocking (N2).
  - D4b-2: Reviewer on the title slide.
  - D4b-4: midterm illustrations and earlier-pipeline diagrams are not reused.
  - D4b-5: References list only works cited on slides.
- **Superseded 17/10** (details in DECK_BRIEF §7): `SLIDE_DECK_v1.md`; D4b-3 "no Thank-you slide"; appendix index;
  "0.4 %" on slide 2; D4-3 "benchmark scatter not used" (→ P-D7 = use it).
- **D4c (17/10), author approved all eight as recommended:**
  - P-D1: 5 sections (Application separate).
  - P-D2: step-by-step reveal = one slide, layered figures, animated in Canva.
  - P-D3: R-figures coded in the cloud chat; script in `Defense/slides/figs/`.
  - P-D4: self-drawn schematics + Health Icons (MIT) + Simple Icons (CC0), credited in References; QA C8-1 rewritten.
  - P-D5: seizure definition cites WHO 2024 only.
  - P-D6: a review-burden number may come from a paper outside the report (web search) → **Moura et al. 2014**
    (Neurology 83(1):56–64): conventional review ≈ 38 min per 24 h of continuous EEG, adult ICU, 118 recordings.
    **P-D6b approved 17/10: on slide 4, said generally (A20).**
  - P-D7: **reversed the same day by the author (A19)** — no figure comparing with other studies; R5 retired; slide 15 = R11 + 4-row table.
  - P-D8: titles = numbered section label + keyword title (≤ 6 words) + one coloured takeaway line (≤ 14 words).
- **D4d (17/10):** deck v4 main slides built in the same artifact (slide map: SLIDE_OUTLINE §7); Siena comparison as a 4-row table; Moura 2014 on slide 4.
- **Approved earlier:** N1–N9; P5 (equal weights only in Q&A); P7; P3 answer C8-2; report fixes R1.
- **Open (author):**
  - P1 committee research fields → `Defense/inputs/committee.md`.

## 5 · Plan of chats

| # | date | task | output (in `F:/Study/Thesis/Defense/`) |
|---|---|---|---|
| D0–D3 | 15–16/10 ✔ | plan; numbers, provenance, app facts; study guide; Q&A bank | see rev 17 |
| D4 / D4b | 16/10 ✔ | outline rev c; Canva build sheet v1 | superseded 17/10 |
| D4 rework | 16–17/10 ✔ | deck v2 → v3 (Slides artifact); seniors' decks studied | `outline/DECK_BRIEF.md`, `outline/SLIDE_OUTLINE.md` rev 2; artifact v3 |
| **D4c** | **17/10 ✔** | P-D1…P-D8 decided; result figures R1–R12 coded from committed results, gated, viewed; uploaded to the deck's asset store; C8-1 rewritten; P-D6 source found | `slides/figs/make_defense_figs.py`, `R*.png/.svg`, `layers/`, `HANDBACK_R.md`; patches to DECK_BRIEF rev 2, SLIDE_OUTLINE rev 2.1, NL §13, QA C8-1 |
| **D4d** | **17/10 ✔** | main slides 1–20 + References rebuilt to v4 in the same artifact; R5 retired (A19); Moura on slide 4 | artifact v4 (main); `slides/gen/build_v4.py` |
| **D4e** | 18/10 | backup slides B1–B26 in the artifact (replace v3 b01–b14 + demo), each = one question + one figure/diagram + ≤ 2 sentences | artifact v4 complete |
| — | 20–21/10 | author: download .pptx → Canva, adjust (R1/R3 layers: stack + "appear") | `slides/Defense_slides_v4.pdf` |
| D5 | 21/10 | review: numbers vs NUMBERS_LOCK (`xanh`), titles, figure sources, rubric, text density, English (`en`), compliance with DECK_BRIEF → cô 22/10 08:00, anh Trí | review list |
| D6 | ≈ 26–27/10 | apply feedback → **slide freeze** | `slides/…_FROZEN` |
| D7 | 28–30/10 | English script per slide, timed | `script/` |
| D8 | 30/10–04/11 | rehearsal: mock committee in English, timing, demo checklist, fallback video | `demo/DEMO_CHECKLIST.md` |

**Start prompt of chat D4e (copy):**
> Chat D4e — Backup slides of deck v4. Read `STATUS_BOARD.md` (rev 20) and the instructions (rev 2026-10-17e), then
> `DECK_BRIEF.md` (rev 2, A1–A20), `SLIDE_OUTLINE.md` (rev 2.1: §4 backup list, §7), `NUMBERS_LOCK.md`, `QA_BANK.md`,
> `HANDBACK_R.md` (asset urls).
> 1. Read the deck artifact https://claude.ai/artifact/RQNQLEV2gmfjrcrZUuzid9 (`project/deck.json`, one main slide for
>    the v4 style, the v3 backups b01–b14 and demo).
> 2. Rebuild the backups B1–B26 of SLIDE_OUTLINE §4 in the **same** artifact, after Thank you:
>    - each answers one question with one figure or diagram + ≤ 2 sentences, keyword title, page number;
>    - no appendix index;
>    - comparisons with other studies only as tables (A19);
>    - reuse R2, R7b, R8, R9, R10, R11, F-figures and v3 diagrams; new small schematics only if needed.
> 3. Every number must be in NUMBERS_LOCK with set · seed · aggregate; no internal labels.
>
> End: board rev 21, project file list, prompt of chat D5 (review).

## 6 · Which file for what

| File | Use it to | When |
|---|---|---|
| **`outline/DECK_BRIEF.md` (rev 2)** | every author request (A1–A18), the sample lessons, presentation rules, design system, tools | **before any slide work** |
| **`outline/SLIDE_OUTLINE.md` (rev 2.1)** | content of each main slide, backup list, rubric coverage, decisions (§6), D4c figures (§7) | D4d–D6 |
| `SAMPLE_BME11_oral.pdf` | the style to follow (20-slide oral of a lab senior) | D4d–D6 |
| deck artifact (link in §2) | the deck itself; download .pptx for Canva | D4d onward |
| **`slides/figs/HANDBACK_R.md`** | R-figure sources, gates, numbers shown, **asset urls** | D4e, D5 |
| `slides/gen/build_v4.py` | record of how the v4 main slides were generated (reads the v3 files saved from the artifact) | only if rebuilding |
| `slides/figs/make_defense_figs.py` | redraw R-figures (`--repo F:/Study/Thesis/Code`; `--smoke` = gates only) | if a figure changes |
| `slides/gen/diagrams.py`, `icons.py` | redraw schematics / recolour icons (matplotlib + Inter) | if a schematic changes |
| `notes/NUMBERS_LOCK.md` | check any number | every slide, every answer |
| `content/STUDY_GUIDE_part1_vi.md`, `part2_vi.md` | understand methods and results | study, rehearsal |
| `qa/QA_BANK.md` | rehearse answers; A# ↔ B# in SLIDE_OUTLINE §4 | daily to 05/11 |
| `notes/APP_FACTS.md` | app layers, demo facts | slides 17–18, B23, D8 |
| `notes/FIGURE_PROVENANCE.md` | internal proof of figure sources | only if asked |

## 7 · Layout

```
F:/Study/Thesis/
  Code/                       repository (public): docs/STATUS_BOARD.md, docs/PROJECT_INSTRUCTIONS.md, results/, src/, web_demo/
  Reports/final/              submitted report (.docx) + Thesis_Final_Report.md
  Defense/                    private, not committed
    inputs/      rubric, committee (P1), lab_slides/ (SAMPLE_BME11_oral.pdf, HD4 deck), midterm slides
    notes/       NUMBERS_LOCK.md (§13 D4c), FIGURE_PROVENANCE.md, APP_FACTS.md
    content/     study guide (Vietnamese)
    qa/          QA_BANK.md (C8-1 D4c)
    outline/     DECK_BRIEF.md (rev 2), SLIDE_OUTLINE.md (rev 2.1)
    slides/      figs/  F1–F10, make_slide_figs.py, HANDBACK.md (D1b);
                        R1–R12 .png/.svg, layers/, make_defense_figs.py, figs_manifest.json, HANDBACK_R.md (D4c)
                 gen/   diagrams.py, icons.py, build_v4.py (D4d)
                 Defense_slides_v4.pdf (author, from Canva)
    script/  demo/
  Agent/inbox/                hand-over tray (D4cd_bundle.zip)
  Archive/2026-10-17/         SLIDE_DECK_v1.md, SLIDE_OUTLINE_rev_c.md; d4c_before/ (pre-patch copies)
```

## 8 · Where the numbers are

| content | file |
|---|---|
| every number of the final system, decisions | `docs/PERF_PHASE_RECORD.md` (rev R), the authority |
| what the committee read | `Thesis_Final_Report.md` |
| **numbers allowed on slides** | `Defense/notes/NUMBERS_LOCK.md` |
| numbers printed on each R-figure | `Defense/slides/figs/HANDBACK_R.md` §1 |
| what each slide carries | `Defense/outline/SLIDE_OUTLINE.md` rev 2.1 |
| application facts | `Defense/notes/APP_FACTS.md` |
| answers to committee questions | `Defense/qa/QA_BANK.md` |
| benchmark entries on Siena | `docs/BENCHMARK_CHECK_szcore_c57da2f.md` |

## 9 · Decisions log

- Report phase (2026-10-08 → 13): board rev 9 in git.
- 2026-10-15: report submitted after the author's revision; anh Trí's feedback; defense phase opened (D0).
- 2026-10-16: D1, D2a/b, D3, D4, D4b done (numbers, study guide, Q&A bank, outline rev c, Canva build sheet v1).
- 2026-10-17: D4 rework (deck v3 artifact, DECK_BRIEF, SLIDE_OUTLINE rev 2, instructions rev 2026-10-17e).
- 2026-10-17 (evening): **D4c.**
  - P-D1…P-D8 approved; P-D6 opened to outside papers, which gave Moura 2014 (pending P-D6b).
  - 11 R-figures coded from committed results with gates, viewed and corrected (label overlaps, legends, layout), layered R1 and R3.
  - 20 PNGs uploaded to the deck's asset store.
  - C8-1 rewritten; DECK_BRIEF rev 2, SLIDE_OUTLINE rev 2.1, NL §13 by patch script.
- 2026-10-17 (late): **D4d** in the same chat (author: "chat chưa dài, tiếp tục D4d tại đây").
  - P-D6b approved, stated generally (A20).
  - The author reminded that comparisons with other studies are never figures (A19): R5 retired, P-D7 reversed.
  - Deck v4 main slides 1–22 built and published to the same artifact; v3 s20–s22, ref3 removed.
