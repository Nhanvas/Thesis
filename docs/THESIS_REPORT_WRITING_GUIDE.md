# THESIS REPORT WRITING GUIDE — how to write this report to score high
**Purpose:** This file is NOT an outline. It is a reference on *how to write* — structure, argumentation,
tone, transitions, citation/statistics conventions — distilled from (a) the official rubric/format/
registration-form governing this thesis, and (b) close reading of 11 real reports: 7 general BME theses
+ 2 outlines at IU (varying majors), and 4 epilepsy-domain theses (the author's own K22 pre-thesis, a
Sydney PhD on seizure detection/forecasting, and two European MSc theses on EEG seizure detection).
When it comes time to actually draft chapters, read this file first — it tells you the shape each section
should take, the sentence-level moves that make a paragraph read as rigorous rather than descriptive,
and the specific rubric point each structural choice is protecting.

This complements (does not replace) the project's technical source-of-truth files (`RESULTS_OF_RECORD.md`
§0, `REBUILD_BASELINE_LOCK.md`, `ATTRIBUTION_SPEC.md`, etc.) — those tell you *what happened and what the
numbers are*; this file tells you *how to present it*.

---

## 0. THE THREE GOVERNING DOCUMENTS — what they lock down

**Rubric (100 pts, 8 criteria) — read this as the report's real table of contents:**
| # | Criterion | Pts | Maps to chapter |
|---|---|---|---|
| 1 | Literature review + realization of knowledge gap (PI 7C) | 15 | Ch.1 §1–2 |
| 2 | Clear problem formulation + realistic constraints | 10 | Ch.1 (problem statement, scope, constraints) |
| 3 | Appropriate principles/methods/tools (PI 1A) | 10 | Ch.2 (named equations, math models) |
| 4 | Design considers global/economic/environmental/societal impact (PI 4C) | 10 | Ch.2 Decision Matrix |
| 5 | Result meets/exceeds objectives | 20 | Ch.3 (heaviest single line — results must map explicitly back to the 2 registered objectives) |
| 6 | Validity/reliability/performance evaluation | 10 | Ch.3–4 (CIs, seed robustness, ablations — already our strength) |
| 7 | Significance + positive/negative impacts + applicability (PI 4C, again) | 10 | Ch.4 (a *second*, separate PI4C hit — do not conflate with #4) |
| 8 | Format + graphics + statistics + citations | 15 | whole document |

Two rubric lines (**#4 and #7**) both carry the ABET PI 4C tag but sit in *different chapters* and ask
different questions: #4 asks whether impact was considered **while designing** (Decision Matrix,
Methodology); #7 asks whether the **finished result's** significance and applicability are recognized
(Discussion). Every sample thesis that scored well on this axis did **both**, as two separate, non-
overlapping pieces of writing — see §4.6 below. RUBRIC_TRACKING.md already flags this as the most
commonly under-served pair — treat it as a checklist item, not an afterthought.

**Report format (non-negotiable):** TNR 12pt; margins 1.5in left / 1in top-bottom-right; 1.5 line
spacing; first-line indent 0.5in; full justify. Max 50 pages excluding list of tables/figures, appendices,
references. Structure: Abstract (≤1 page, ≤10 keywords) → Ch.1 Introduction → Ch.2 Methodology
(with a "Decision Matrix for [aim]" section) → Ch.3 Results → Ch.4 Discussion → Ch.5 Conclusion →
References → Appendices.

**Registration form (the approved scope — do not drift from this in Ch.1):**
- Major: *Development/improvement of algorithms for image/signal/data processing.*
- Goal (verbatim from the signed form): "develop an unsupervised framework for temporal seizure
  localization (onset and offset detection) in multi-channel scalp EEG recordings."
- Objective 1: unsupervised anomaly scoring framework combining spatial-temporal features to detect
  deviations from normal brain connectivity.
- Objective 2: temporal seizure localization via non-parametric change point detection on the ensemble
  anomaly score time series.
- Chapter 3 (Results) and Chapter 5 (Conclusion) must be traceable, explicitly, back to these two
  objectives — a reviewer should be able to underline a sentence in Results/Conclusion for each
  objective and see it satisfied. This is the literal mechanism behind rubric criterion #5 (20 pts).

---

## 1. MASTER CHAPTER SKELETON (content requirements, not rigid headings)

Every sample thesis reviewed used its own subheading wording, but all of them delivered the same
underlying content items in the same order. **Match the content list below; the exact subheading
text is flexible.** This is the single most load-bearing finding from the sample review: no sample
thesis had a literal "Limitation" heading in Chapter 1 (as the format doc's example suggests), yet
every strong one still covered scope/constraints somewhere in Ch.1 prose. Content coverage is what is
graded; heading titles are not.

### Chapter 1: Introduction
1. **Introduction to the biomedical problem** — open at the disease/clinical level (what is the
   condition, who does it affect, why does it matter), escalate through global epidemiology with
   cited statistics (WHO/major registries), then narrow to the specific clinical gap this thesis
   addresses. End this subsection at the point where the *need for a technical solution* becomes
   obvious, not before.
2. **Analysis of current solutions** (this is where rubric criterion #1's 15 points live) —
   structure described fully in §2 below.
3. **Proposed solution** — a short, bulleted synthesis of what this thesis does, phrased as the
   direct answer to the gaps just identified.
4. **Project goals / objectives** — list them explicitly, and phrase them so they are recognizably
   the same two objectives as the registration form (word-for-word alignment is safer than
   paraphrase here).
5. **Research framework / project timeline** — a diagram or Gantt-style roadmap, or at minimum a
   short paragraph mapping the thesis phases to chapters. Every sample thesis included some form
   of this closing element.

### Chapter 2: Methodology
1. **Decision Matrix for [aim]** — required verbatim as a section title by the format doc. See §3.
2. **Materials / data** — name the dataset, give its scale in numbers (subjects, hours, channels,
   sampling rate, number of positive events — whatever quantifies "how much data"), then **justify the
   choice explicitly with a short bulleted list of reasons** (e.g., long-term continuous recording,
   expert-annotated ground truth, benchmark status enabling comparison to prior work). This
   bulleted-justification move is itself a mini decision-matrix in prose and is a real, repeated
   convention (confirmed in the author's own prior report) — use it for the CHB-MIT dataset here too.
3. **Methods** — the pipeline stages, each with its governing equation or algorithm stated explicitly
   (rubric #3, PI 1A: "identify which mathematics, biomedical science and engineering principles are
   used"). Write so a reader could re-implement each stage from the text alone. Number the stages and
   reference a pipeline figure explicitly ("As shown in the design schematic, the framework consists of
   five sequential stages: (1)...(5)..."). **Beyond the formal Decision Matrix, every individual
   non-obvious parameter choice (window length, threshold, band range, penalty multiplier) should get
   its own one-sentence justification, ideally citation-backed** — this is where rubric #2's "realistic
   constraints" actually gets satisfied in practice: not as a dedicated "Constraints" section (no
   sampled thesis has one), but as constraints named naturally at the point where they shape a decision
   ("due to the serverless architecture's constraints...", "given the computing time constraint of 15
   minutes, this influenced the choice of..."). Do this throughout Methodology, not once in Ch.1.
4. **Evaluation protocol** — how performance will be measured, stated *before* Results, not
   introduced ad hoc when a number is needed.

### Chapter 3: Results
- Report what was obtained (and, honestly, what was not), organized to **mirror the Methodology's
  stage order one-for-one** — every sampled thesis structures Results as a walk through the same
  pipeline stages in the same order as Methods, and opens each Results subsection with an explicit
  back-reference ("As outlined in the Method section...", "As shown in Figure 3..."). This, not
  literal "Objective 1 satisfied here" labeling, is how rubric #5 (result meets objectives) is actually
  demonstrated in practice — the two registered objectives correspond to two identifiable stretches of
  the pipeline (anomaly scoring; temporal localization), so make sure each stretch has a clearly
  reported result, and let the Conclusion do the explicit tying-back (see §5).
- Every figure/table should let a reader draw a conclusion without reading the caption twice — rubric
  #8 literally scores this ("graphic presentation... allows conclusion to be drawn").
- Do not editorialize here — interpretation belongs in Discussion. Results states facts; Discussion
  explains them. (Every sample thesis respects this split; blurring it reads as less rigorous.)

### Chapter 4: Discussion
- One thematic subsection per major finding, failure mode, or comparison — never a single
  undifferentiated block. See §4 below for the internal shape of each subsection.
- A literature-comparison table, revisited from Ch.1's table, now populated with *this thesis's*
  numbers alongside the prior-art numbers.
- A dedicated impact/significance subsection (rubric #7 — separate from Ch.2's Decision Matrix).
- Limitations, stated as specific and mechanism-backed, not generic hedges.

### Chapter 5: Conclusion
- Short. Restate → quantify → limit → contribute → future work → closing significance line. See §5.

### References / Appendices
- Numbered bracket citations `[1]`, `[2]` with full bibliographic detail (author, title, venue, vol/no/pp,
  year, DOI) is the dominant convention actually used across sampled theses, including the author's own
  prior work — safer default than the format doc's `(Author, Year)` example. **Pick one system and never
  mix within the document.**

---

## 1a. THE ABSTRACT FORMULA (verified across 4+ independent samples: prosthetic-hand, chest-sound AI,
skull-reconstruction SSM, AD-detection pipeline — different majors, same shape every time)

An abstract that reads as strong follows this exact sequence, almost always in under 300 words:
1. **Clinical/biomedical problem** (1–2 sentences) — name the condition/context and its consequence.
2. **Gap in current approaches** (1 sentence) — what existing solutions fail to do, stated plainly
   ("the problem then is...", "conventional approaches... remain limited, particularly for...").
3. **What this thesis built** (2–3 sentences) — name the system/framework and its key technical
   components by name (architecture, key algorithm, key measure) — specific enough that a reader could
   look the terms up, not "a machine learning model."
4. **How it was validated** (1 sentence) — dataset (with scale, if it strengthens credibility) and
   evaluation approach.
5. **Headline quantitative result(s)** (1–3 sentences) — actual numbers, and where possible a direct
   comparison ("outperforming all of the sound-based models from other studies," "sub-millimeter mean
   surface error"). Vague results ("the model performed well") never appear in the strong samples.
6. **A finding beyond the raw metric, if one exists** (optional but present in the best samples) — a
   result that is independently plausible against known domain physiology/theory, not just a number
   (e.g., one sample's Grad-CAM interpretability finding at 10–40 Hz matching known heart-sound
   physiology). This is the move that signals genuine scientific insight rather than a leaderboard
   entry — this thesis's attribution work (physiologically-grounded gamma-band findings, lateralization
   checks) is exactly this kind of material and belongs in the Abstract, not only in Ch.4.
7. **An honest limitation, stated in one clause** (present in roughly half the strong samples,
   including when the result is otherwise very positive — e.g., "despite limitations such as the
   absence of an opposable thumb...").
8. **Keywords** (8–12, comma-separated, immediately after the abstract text).
Do not introduce future-work detail or methodology minutiae in the Abstract — every strong sample
keeps it to these eight moves and nothing else.

---

## 2. HOW TO WRITE THE LITERATURE REVIEW (Ch.1 §2 "Analysis of current solutions")

This is the single most consistent structural pattern across every sample, general and epilepsy-domain
alike, and it is worth internalizing as close to verbatim procedure:

1. **Open with a comparison table.** Columns typically: `Author(s) | Dataset | Method | Performance |
   Approach type` or `Author | Method | Performance | Pros | Cons`. This table front-loads the
   evidence so the prose that follows can *argue* rather than *catalogue*.
2. **Group prior work into 3–5 named categories** (e.g., "spatial-only models," "temporal models,"
   "graph-based approaches" — or in our case: unsupervised vs supervised, window-level vs event-level,
   GAE-based vs classical connectivity). Give each category its own subsection.
3. **Each subsection follows the same internal micro-pattern:**
   - State what the category does and cite 2–4 representative papers with their headline numbers.
   - Immediately follow the numbers with the honest catch: *why the impressive number doesn't fully
     solve the problem* (wrong task, leaky evaluation, non-comparable protocol, structural limitation
     of the method). This is the move that turns a list of citations into a literature review with
     a gap. E.g., pattern: "*However, these high accuracy values are misleading because they reflect
     performance on [easier task X], not [the clinically relevant task Y].*"
   - Close with a **bridge sentence** that hands off to the next subsection or to the synthesis: e.g.,
     "*This presents an opportunity where [next approach] can be more suitable*," or "*A shared
     limitation across these paradigms is...*." Never end a subsection on a citation; end it on the
     gap.
4. **Synthesize, don't just conclude.** The paragraph that closes this section (leading into
   "Proposed solutions") should explicitly connect 2–3 of the identified gaps into the specific design
   choices the thesis makes — "*because approach A lacks X and approach B lacks Y, this thesis combines
   the strength of A with the fix from B by...*." This is the sentence a rubric-#1 grader is looking
   for: it proves the gap was *realized*, not just *listed*.
5. **The literature table returns in Discussion.** The strongest theses re-show the same comparison
   table in Ch.4 with a new row for "this study," so the reader sees the positioning move made twice —
   once as motivation, once as verdict. Do this.

**For this thesis specifically:** the existing `Literature_Review_and_Novelty_Assessment...md` and
`Lit_review.txt` already contain exactly this raw material (Yildiz 2022, EEG-CGS, GraphS4mer, IRENE,
SzCORE benchmarks, etc.) — the job when drafting Ch.1 is to compress it into the table-then-subsections-
then-bridge shape above, not to import it as continuous prose. Keep the "novel combination, not novel
primitive" framing already established there — it is exactly the kind of honest positioning that reads
well (see §6 on hedging).

---

## 3. HOW TO WRITE A DECISION MATRIX (rubric #4, PI 4C, Ch.2)

Two table formats are both acceptable, seen across samples:

**Format A — weighted numeric scoring** (used for e.g. actuation-mechanism or architecture choices):
```
Feature                          Weight   Option A   Option B   Option C
Criterion 1 (5=best – 1=worst)     W1        s1a        s1b        s1c
Criterion 2                        W2        s2a        s2b        s2c
...
Total (weighted)                  100        Σ           Σ          Σ
```
**Format B — qualitative feature comparison** (used for e.g. deployment architecture, connectivity
measure choice — closer to what DM1–DM6 in this thesis already do):
```
Category      Criterion            Option A              Option B              Option C
Engineering   Scalability          ...                   ...                   ...
Economic      Cost                 ...                   ...                   ...
```

**The paragraph after the table is what actually earns the points — never let the table stand alone.**
The strongest examples follow the table with a verdict paragraph structured as: *"This decision was
motivated by N factors: First, ... [cite]. Second, ... [cite]. Third, ..."* — each factor traceable to a
specific row of the table, each backed by a citation or a measured result, not asserted by authority.
A table with no such paragraph, or a paragraph that just restates the winning total, scores lower.

**This thesis already has 6 decision matrices (DM1–DM6) in `Proposed_solution_updated_v5.md` §XIII**,
including DM6 (deployment strategy) which is explicitly built as a PI4C exercise with weighted
global/economic/environmental/societal criteria — this is a strong, rubric-#4-complete asset. When
drafting Ch.2, port these near-verbatim; the main work is trimming DM1–DM5 to their table + verdict-
paragraph essentials and keeping DM6 closer to full length as the flagship PI4C artifact.

---

## 4. HOW TO WRITE THE DISCUSSION CHAPTER (rubric #6, #7)

This is where sample theses differentiate most sharply in quality, and where this thesis has the
richest raw material already (rejected experiments, ablations, honest baseline corrections). The
winning shape, consistent across the undergrad BME samples, the Tampere MSc, and the Aalto MSc alike:

### 4.1 One subsection per finding, not one block per chapter
Each subsection = one specific result, failure mode, or comparison. Never write "Discussion" as a
single essay; segment it exactly the way the Results chapter segments its findings.

### 4.2 Every subsection must explain a mechanism, not just report a number
The difference between a C-grade Discussion and an A-grade one is almost entirely this: does the text
explain *why* a result came out the way it did, at the level of the underlying method? Compare:
- Weak: "The chain-based model performed worse (46% accuracy) than the cell-based model (87%)."
- Strong: "The chain-based model's transformer encoder is highly sensitive to patch size: 14×14
  patches induce overfitting, while smaller 7×7 patches lose the spatial token information needed for
  the encoder to learn effectively — a structural trade-off the cell-based architecture avoids by
  retaining full-resolution feature maps through its fully-connected head."
Every sample thesis that reads as rigorous does the second move, every time, including for its own
negative results.

### 4.3 Do not soften or hide negative/partial results — explain them
Sampled theses openly report models that underperformed, features that broke (rank-deficient matrices,
numerical instability), and metrics that didn't reach the target — always paired with a diagnosed
mechanism and a stated next step. This maps exactly onto this project's existing house style
(Decision #10 topology rejection, S2/S3/S5 rejections, Decision #24 CUSUM rejection, the §0 baseline
honesty about the retired 0.750/0.829 numbers). **Do not write around these in the report — write them
up as findings.** A "falsification with a named mechanism" reads as more rigorous than a suspiciously
clean success story, and directly satisfies rubric #6 ("evaluation of validity and reliability").

### 4.4 Frame trade-offs in decision-relevant (often clinical) terms
The strongest Discussion sections don't stop at "Model X has higher precision, Model Y has higher
recall" — they translate the trade-off into what it means for the downstream user: which error is more
costly, in which deployment scenario, and therefore which operating point is defensible. This thesis's
existing balanced-vs-high-sensitivity operating-point story (§0) and its post-hoc-triage framing (FP/day
reframed as review burden, not alarm-fatigue) are already built this way — lean into it explicitly in
prose rather than leaving it implicit in the numbers.

### 4.5 Re-run the literature comparison table with this thesis's row added
Take the Ch.1 comparison table, add a final row for this work, and use it as the anchor for an honest
positioning paragraph: where this result sits relative to the cited unsupervised and supervised
baselines, and why direct numeric comparison is or isn't fair (different dataset scoring convention,
different task difficulty, etc.). **This is not a stylistic flourish from one strong example — it is a
convention confirmed independently across three different sample theses** (spanning AI-diagnosis,
chest-sound classification, and the author's own epilepsy pre-thesis), each with its own
"Comparison with prior/other studies" table placed in Discussion, always followed by a paragraph
naming what this work does differently/better and why the comparison is or isn't apples-to-apples.
Treat this as close to mandatory. This thesis's own Literature_Review doc already contains the raw
analysis (Yildiz 0.68 vs our window AUROC ≈0.775–0.805; SzCORE supervised baselines vs unsupervised
patient-independent framing; the 2025 SzCORE Challenge's own top F1 of 0.32–0.43 as the realistic
patient-independent ceiling) — it needs to be presented as a table + paragraph in Ch.4, not left as a
standalone memo.

### 4.6 A dedicated impact/significance subsection — separate from the Ch.2 Decision Matrix
This is the rubric-#7 hit, and it must read differently from Ch.2's DM6: DM6 asks "which deployment
option is best, given these criteria" (a design decision, made in advance). The Ch.4 subsection asks
"now that the system exists, what good or harm can it actually do, and to whom." Concretely, cover:
- who benefits directly (patients with drug-resistant epilepsy; clinicians reviewing long EEG),
- the mechanism of benefit (reduced review burden, faster flagging, not real-time alarm — restate the
  framing explicitly so it cannot be misread as a claim of real-time clinical deployment),
- who bears the cost/risk of the honest limitations (false positives → review burden, not patient harm,
  given the post-hoc framing; the chb06/chb14-type subject where the system is signal-limited),
- broader/global framing: low-resource settings, on-premise deployment for pediatric data privacy
  (this maps directly onto DM6's societal/economic criteria — cross-reference rather than repeat),
- honest scope statement: proof-of-concept, not a validated clinical product.
Both this project's own pre-thesis and one of the sampled general theses use almost this exact
subsection (titled "Economic, social costs and global impacts of the scientific approach" in one,
"Economic, social impact and global impacts of scientific approach" in the other) placed at the end of
Discussion, right before Conclusion. **Replicate this placement and framing.**

---

## 5. HOW TO WRITE THE CONCLUSION (short, five-move template)

Every sampled conclusion — undergrad and PhD-chapter alike — follows the same five moves, in this
order, in roughly half a page to one page:
1. **Restate** what was built/done, in one or two sentences (no new information).
2. **Quantify** the single most important result headline (one number or a small number of numbers —
   not a re-listing of every table).
3. **Name the key limitation** honestly, in one or two sentences (this is not optional — every strong
   sample includes it here, even after already covering limitations in Discussion; the Conclusion's job
   is to leave the reader with the boundary of the claim, clearly stated).
4. **Note a secondary contribution** if one exists (a tool, a methodological finding, a negative result
   with a mechanism, an evaluation-protocol contribution).
5. **Close on future work + a one-sentence significance statement** tying back to the real-world
   problem named in Ch.1's opening paragraph — this closes the loop the whole report opened with.
Do not introduce new citations, new numbers not already in Results, or new arguments in the Conclusion.

---

## 6. CROSS-CUTTING STYLE RULES (the "IELTS layer" — coherence, cohesion, register)

These are the sentence- and paragraph-level habits that separate reports that *read* rigorous from
reports that merely *are* rigorous. They matter for rubric #8 ("clear and well-structured... graphic
presentation... allows conclusion to be drawn") as much as content does.

### 6.1 One idea per paragraph, topic sentence first
Every strong paragraph in the sampled theses opens with a sentence stating its one claim, then spends
the rest of the paragraph supporting it with citations, numbers, or mechanism. Paragraphs that open
with a citation or a number rather than a claim read as weaker — reorder so the claim leads.

### 6.2 Bridge every subsection to the next — and bridge across chapters by explicit number
Never let a subsection just stop. Close it with a sentence that either (a) states the gap/limitation
it leaves open, or (b) explicitly hands off to what comes next ("This motivates...", "This raises the
question of...", "Building on this,..."). This is what makes a report feel like one continuous
argument rather than a stitched-together set of notes — directly the "coherence and cohesion" quality
IELTS-style writing is scored on, and it is exactly what distinguishes the better sampled theses from
the weaker ones.
**Verified separately: chapters do NOT open with a scene-setting "roadmap" paragraph in the sampled
theses** — Chapter 2 typically begins immediately with content (often the first Decision Matrix).
Instead, cross-chapter cohesion is built through **explicit numbered back-references**: "As previously
noted in chapter 1, section 1.2, ...", "As outlined in the Method section, ...". Use this device
liberally, by exact chapter/section number, whenever Results/Discussion depends on a choice made
earlier — it is a small habit that reads as noticeably more organized, and it costs nothing structurally
(no extra section needed, just the phrase).

### 6.3 Calibrate every claim to the evidence — this project already has a house rule for this
Use "demonstrates" only when the evidence is direct and unconfounded; otherwise "suggests," "is
consistent with," "indicates," or "provides evidence that." This is already Core Operating Rule #9 in
this project's own instructions, and it is exactly the register used in every strong sampled Discussion
section (e.g., "this comparative perspective... underscores... but also reveals..."; "the model's
ability to leverage... may enable..."). Never claim more than the design supports — a reviewer will
test exactly this.

### 6.4 Vary the reporting verb and sentence shape when presenting numbers back to back
Reports that repeat "achieved X% accuracy... achieved Y% accuracy... achieved Z% accuracy" read as
mechanical. Sampled strong writing varies: "reported," "reached," "demonstrated," "yielded," and varies
sentence position of the number (sometimes leading, sometimes trailing the method name).

### 6.5 Statistics for a mixed-expertise committee
The committee includes clinicians/biomedical faculty, not only ML specialists. Every sampled thesis
that reports statistics pairs the number with a plain-language gloss in the same sentence or the next:
not just "p < 0.05" but "...significantly higher than chance (p < 0.05), meaning the effect is unlikely
to be a random artifact of this sample." This thesis's CI-heavy reporting (Wilson, Poisson, DeLong,
bootstrap) should always be glossed this way in prose — the numbers already exist in the tables; the
prose's job is to state what they mean for someone who will not personally recompute a Wilson interval.
One sampled MSc thesis's Discussion explicitly justifies *why* it deliberately avoided over-claiming
from limited statistics (no universally accepted seizure-detection performance measure exists; a
single expert's annotations are not ground truth beyond doubt) — this is a legitimate, well-regarded
move, not a weakness, and maps directly onto this project's own attribution-honesty framing (low
inter-rater agreement on seizure onset localization, ICC ~0.15–0.26, already noted in
`ATTRIBUTION_SPEC.md`). Say this kind of thing plainly when it applies; it reads as maturity, not doubt.

### 6.6 Figure and table captions must be self-contained
A reader skimming only figures/tables should be able to follow the story. Captions in the stronger
samples state what is plotted, what the axes/columns mean, and often a one-clause takeaway — not just
"Figure 3: Results."

### 6.7 Abbreviation table
Every sampled thesis (this project's own pre-thesis included) opens with a full abbreviation table
after the table of contents. Build this early and keep it current as chapters are drafted — it is
graded implicitly under rubric #8 (clarity/structure) and is a common place for a first submission to
look sloppy if skipped.

### 6.8 Citation consistency
Pick numbered-bracket `[1]` (the de facto majority convention, including the author's own prior work)
or author-date `(Smith, 2020)` (the format doc's literal example) — either is acceptable, but every
sampled thesis is internally consistent. Mixing styles within one document is the one citation mistake
that reads as careless regardless of which style is chosen.

---

## 7. PITFALLS OBSERVED IN THE SAMPLES — avoid these specifically

- **Skipping the Decision Matrix, or treating it as decorative.** One sampled thesis had no Decision
  Matrix section at all and instead folded PI4C into a Discussion subsection only — workable, but it
  means the design-stage rubric line (#4) has no clean artifact to point to. This thesis already has
  DM1–DM6; the risk is *not* missing the matrix but writing a thin verdict paragraph after it. Do not
  let this happen — every matrix needs its enumerated-reasons paragraph (§3).
- **Reporting a headline metric without the caveat that makes it honest.** Several cited papers in the
  sampled literature reviews were dismissed by the sample's own authors precisely because a high
  reported number hid an easier task or a leaky protocol. Do not let this thesis's own presentation
  fall into that trap — anywhere a strong number appears (e.g., window AUROC vs the much harder event-
  level sensitivity/FP-day story), state the caveat in the same breath, not two paragraphs later.
- **Introduction that reads as a general essay on the disease rather than building toward the specific
  gap.** The strongest samples keep every Ch.1 paragraph moving toward the proposed solution; weaker
  ones spend pages on general disease background disconnected from the eventual method. Keep the
  epilepsy background (there is excellent reusable material — WHO ~50M patients, ILAE definition, ~30%
  drug-resistant epilepsy, SUDEP, EEG as the functional-imaging modality of choice, manual-review
  bottleneck, interictal/preictal/ictal states) tightly aimed at motivating *unsupervised, patient-
  independent, temporal localization* specifically — not seizure prediction in general, since that is
  not this thesis's task.
- **Treating Results and Discussion as interchangeable.** Keep interpretation strictly out of Chapter 3.
- **Forgetting the second PI4C hit.** #4 (Decision Matrix) and #7 (Discussion impact subsection) are
  both worth 10 points and are graded as separate lines — confirmed necessary by two independent
  samples (Hien's thesis, this project's own pre-thesis) doing exactly this two-part structure.

---

## 8. NOTES SPECIFIC TO THIS THESIS'S CURRENT MATERIAL

- The project's own `Proposed_solution_updated_v5.md` §VI ("Key Scientific Findings," 5 numbered
  findings) is already written in almost exactly the Discussion-subsection shape recommended in §4
  above — each finding names a mechanism, is honest about partial success (Finding 3: chb06 remains a
  genuine limitation), and several already end with a forward-looking sentence. This is very close to
  Ch.4-ready material; the main task is re-deriving these findings against whichever pipeline version
  becomes the final locked baseline (currently trending toward the Phase-C/Tier-2 result once that
  optimization work concludes), and re-checking every number against `RESULTS_OF_RECORD.md` §0 (or its
  successor) rather than the historical §1–§16 figures.
- The project's Decision Log (`PLAN_AND_STATUS.md`, "DECISIONS LOG") is a goldmine for Discussion
  material precisely because of its falsification-with-mechanism style (Decisions #10, #24, the S2/S3/S5
  graph-structure-learning rejections) — this is publication-quality honest-negative-result writing
  already; it mainly needs translating from lab-notebook register into thesis prose (see §4.3).
- No "Economic, social, global impact" subsection currently exists as a standalone Ch.4 item in the
  project's docs (DM6 covers the Ch.2 half only) — this should be explicitly drafted fresh when writing
  Discussion, using DM6's societal/economic/environmental criteria as raw material but reframed around
  *realized* significance per §4.6, not re-derived design criteria.
- The literature comparison table already exists in substance across `Literature_Review_and_Novelty...md`
  and `Lit_review.txt` (Yildiz 2022, SzCORE 2024/2025 benchmarks, EEG-CGS, GraphS4mer, IRENE, Ali et al.
  2024) — when drafting Ch.1/Ch.4, compress into the table-plus-subsections shape (§2) rather than
  importing the memos wholesale.
- Statistical apparatus (Wilson/Poisson/DeLong CIs, permutation nulls, seed-robustness checks) already
  exceeds the norm observed in every sampled undergraduate BME thesis — this is a genuine strength for
  rubric #6/#8, provided it is glossed in plain language per §6.5 rather than presented as bare
  statistics tables.
