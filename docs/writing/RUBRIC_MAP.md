# Rubric map — where the v5 report earns each criterion

**Source:** rubric in `THESIS_REPORT_WRITING_GUIDE.md` section 0 (100 points, no band descriptors) and
`Report format.md`. Sections and exhibit numbers refer to `REPORT_BLUEPRINT_v5.md`.

| # | Criterion | Pts | Where it is met | Evidence the grader sees | Main risk |
|---|---|---|---|---|---|
| 1 | Literature review and realisation of the knowledge gap | 15 | 1.2.1–1.2.5, closing gap paragraph; Table 1 | Five named categories, including threshold calibration and baseline drift (the registered literature focus); each ends on what it leaves unsolved; the gap is a synthesis, not a list | Categories that never return in Ch2–Ch4 |
| 2 | Problem formulation and realistic constraints | 10 | 1.1, 1.3, Table 2; constraints recalled in Ch2 where they decide | Post-hoc review triage; unsupervised; scalp EEG; CPU laptop; label-free at use; patient data stays on site | Constraints stated once and never used |
| 3 | Appropriate principles, methods and tools | 10 | Ch2, Eq (1)–(n), Table 7 | Every stage re-implementable from the text; one-clause reason per non-obvious value | Missing parameter or unexplained term |
| 4 | Design considers global, economic, environmental and societal impact | 10 | 2.3.3, 2.6.1, 2.9.1 (Tables 5, 6, 8) + verdict paragraphs | Deployment matrix with impact categories as concrete criteria (AR 18); enumerated verdict ("First, … Second, …") with cited or measured support | Vague weighted labels; bare table |
| 5 | Results meet or exceed objectives | 20 | 3.2 (Objective 1), 3.3 (Objective 2), 3.4, 3.5; Ch5 per objective | Each Ch3 section opens by naming the objective it answers; Tables 9–14, Fig 11; Ch5 closes each objective with its number | Overclaiming vs honest, modest numbers; dropped objectives table (AR 4) must be replaced by this explicit mapping |
| 6 | Validity, reliability, performance evaluation | 10 | 2.8, 3.3, 3.4, 4.1–4.3 | 4 seeds (mean ± SD), patient bootstrap intervals, component ablation (Table 9), external patients (chb24, Siena), held-out vs final disclosed, failures with a named mechanism (Fig 14), channel-level negative result | Seed spread presented as uncertainty; test-informed result as the clean one |
| 7 | Significance, positive/negative impacts, applicability | 10 | 4.6 (dedicated, right before Ch5) | Who benefits (EEG reviewers, patients waiting for review), mechanism (shortlist of segments to review), who bears the risk (missed seizures, reviewer time on false alarms), global framing (open data, shared scoring), proof-of-concept scope | Mixed with criterion 4; claims of clinical use |
| 8 | Format, graphics, statistics, citations | 15 | Whole document | Consecutive integer numbering, short captions (AR 22), figures from committed results, statistics glossed in plain words, numeric citations with DOI, abbreviation list, body ≤ 50 pages measured (target ≤ 48) | Number mismatch between Abstract, text and tables |

**Conflicts between the rubric/format documents and project decisions (resolved):**
- Citation style: format asks author–date and alphabetical; guide accepts numeric. → Numeric [n] (Tri also numeric).
- Appendix listed in the order → none (format: "use this part wisely"; AR 3).
- Keywords: guide 8–12, format ≤ 10 separate words → ≤ 10 words.
- "Limitation" part in Ch1 (format) → scope and constraints in 1.3; limitations in 4.5.
- Self-contained captions (guide) → short titles, explanation in text (AR 22).
- Ch1 "structure of research" (format) and roadmap openings → none (AR 7); Section 1.6 ends with one sentence mapping the framework stages to Chapters 2–4.
