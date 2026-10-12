# Sample thesis patterns — VBPH (main model) vs Tri (secondary)

> **Author rules override the samples where they differ** (see `AUTHOR_REQUIREMENTS.md`): the samples put tried
> alternatives in Methods/Results; this thesis puts only the final system in Methods and its results in Results
> (an ablation of the final system's components is a result), and tried-and-failed designs in Discussion.
> The samples' captions are copied (short titles, "Figure n:" consecutive); their 61-page length (Tri) is not.

VBPH = chest-sound AI and Grad-CAM (K20, 2024). Tri = serverless application for Alzheimer's disease from MRI (K20, 2024). Page counts are measured from the LibreOffice PDF conversion (Tri was converted chapter by chapter because LibreOffice crashed on the whole file), after removing the 1–20-word overflow pages caused by the per-page section breaks of these PDF-derived .docx files. They agree with the authors' ToC page numbers.

## 1–3. Front matter, structure, size
| | VBPH | Tri |
|---|---|---|
| Front matter | Title → Approval (Advisor, Chair, Reviewer) → Acknowledgments → ToC → List of Figures → List of Tables → Abstract → Keyword (heading) | Title → Approval → Acknowledgments (+ ADNI data-use text) → ToC → List of tables → List of figures → Abstract (keywords line at end) |
| Abstract / keywords | 294 words, 1 paragraph / 10 | 238 words, 5 paragraphs / 6 |
| Declaration, abbreviations | none | none |
| Heading numbering | "1.1", "1.1.1" (3 levels) | restarts per chapter, up to "2.3.1.1" |
| Pages Ch1/2/3/4/5 | 14 / 14 / 8 / 3 / 1 = **40** | 18 / 23 / 14 / 5 / 1 = **61** |
| Figures (per ch.) | **15** (1/9/5/0/0) | **32** (3/12/16/1/0) |
| Tables (per ch.) | **12** (3/4/4/1/0) | **10** (2/2/5/1/0); the list shows 11, one broken |
| References | 26, author–year, alphabetical | 36 (1 duplicate), numeric superscript [n], APA entries |

Both theses follow the department template: Ch1 Introduction → Ch2 Methodology → Ch3 Results → Ch4 Discussion → Ch5 Conclusion (no subsections). **Ch1 sequence:** *Introduction to the biomedical problems → Analysis of current solutions → Proposed solutions → Project goals → (Timeline / Gantt) → Research framework.*
- **VBPH:** 2.1 Dataset (label conversion, augment) · 2.2 Data engineering (pipeline figure, then one subsection per transform) · 2.3 Model (decision matrix, CNN, ViT) · 2.4 Inference method (decision matrix, Grad-CAM, map→spectrum) ‖ 3.1 Model results · 3.2 Inference results ‖ 4.1 Modeling · 4.2 Frequency range.
- **Tri:** 2.1 Decision matrix for application architecture · 2.2 Methods (data, preprocessing, search space, preparation, search strategy, training, metrics, serverless application) ‖ 3.1 Preprocessing · 3.2 Search and classification · 3.3 Web application (UI, in-app test, cost) ‖ 4.1–4.4, one section per finding.

## 4. Captions
Figures and tables are numbered **consecutively across the whole thesis** ("Figure 12:"); figure captions sit below, table captions above. Average length: VBPH figures 8.9 words (median 6), tables ≈6; Tri figures 11.1 (median 8), tables ≈6.
- VBPH: "Figure 1: Research framework flowchart" · "Figure 2: Flowchart of biosignal processing and classification" · "Figure 8: A sample of STFT matrix before (left) and after (right) PCA and reconstruct" · "Table 6: Decision matrix for classification model architectures" · "Table 12: Comparison of result from other studies".
- Tri: "Figure 4: Universial Inverted Bottleneck blocks [27]" · "Figure 13: Application schematic design" · "Figure 25: Cell-based results. a) ROC curve. b) Confusion matrix." · "Table 3: Decision matrix for serverless and non-serverless architecture" · "Table 8: Cost estimation for AWS Lambda".
- **Borrowed figures:** VBPH has none. Tri uses them in **Ch1–Ch2 only**: Figs 4, 7, 8 and 12 append "[n]" to the caption, with no "adapted from" wording. The SE and ViT diagrams (Figs 5–6) appear to be reproduced from published papers but carry no caption citation.

## 5. Pipeline placement
Both samples work on two levels:
1. A **research-framework flowchart closes Chapter 1**, before any data description (VBPH 1.6, Fig 1; Tri 1.5, Fig 3 + Gantt + steps).
2. The **technical pipeline figure opens Methods, directly after the dataset section**. VBPH 2.2 begins: "The complete process of processing and classification is summarized in Figure 2". Tri's application schematic (Fig 13) heads 2.2.8.

Each later subsection then covers one pipeline block.

## 6. Methods
Both describe the **alternatives tried, not only the final method** (VBPH: 3 feature types and 2 models; Tri: 2 search spaces), and both report the selection in Results. Choices are justified in three ways:
- **Decision matrices.**
- **Citations:** e.g. VBPH's 0–600 Hz "based on the study of Gross".
- **One-clause rationales or bare assertions:** Tri "0.2 … was found to effectively balance"; VBPH "the 90% accuracy mark was chosen as the minimum threshold".

Tri lists its hyperparameters as bullets, each with a definition and the value used.

## 7. Results
- **VBPH:** selection tables (input × model, validation accuracy and F1; STFT variants), then interpretation figures. About 9 items. Validation only: no test set, confusion matrix, statistics or per-subject table.
- **Tri:** preprocessing → architecture search → per-class tables (precision, recall, specificity, F1, accuracy, AUC), with ROC curves and confusion matrices → application. About 21 items, no statistics.
- **Failed attempts:** both report them in Results (VBPH's fractal dimension and ViT; Tri's chain-based model at 46%). Tri explains the KAN failure in Discussion.

## 8–9. Discussion and conclusion
- **Comparison tables:** VBPH: Study | Method | Task | Accuracy | Precision | Recall | F1, with "The proposed method" as the last row. Its only caveat: "this study's task was comparatively easier". Tri: Author | Method | Performance, with the task inside the cell ("98.37% accuracy CN vs AD"). Its caveats are binary vs three-class tasks and pretrained weights.
- **Limitations:** neither has a separate section. They sit in the Conclusion (VBPH) or are spread through the Discussion (Tri).
- **Future work:** in the Discussion and the Conclusion.
- **Conclusion length:** VBPH 149 words (results, limits, next step); Tri 304 words in 6 paragraphs.

## 10. Application, decision matrix, social factors
- **Methods (Tri Ch2):** schematic; one justified choice per service; platform limits that drove the design (Lambda's 15 min and 50 MB, hence Docker); configuration (9 min, 1200 MB); database schema; API table.
- **Results (Tri Ch3):** UI screenshots with prose walkthroughs; a 30-sample in-app run framed as proof that the deployment matches the test results; cost tables in VND.
- **Not reported:** measured latency, memory use or usability. Only model size is given (1.7M parameters; 5.1 MB).
- **Decision matrices.** Tri 2.1 uses qualitative text cells (no scores) to compare serverless, containerized and VM options in three categories. *Engineering:* scalability, speed, maintenance. *Economic:* affordability, cost predictability. *Operations:* hardware, EHR integration, data privacy. VBPH's three matrices are technical only: complexity, input type, performance, explainability, downside, with a "Choice" column marked x.
- **Social and economic factors:** no dedicated section in either. They appear in **Ch1 1.1**: disease burden and cost; Tri's Vietnam AI adoption (9%) and fragmented hospital information systems; VBPH's check-up habits and home diagnosis. They return in Tri's cost results and VBPH's last Discussion paragraph. Ethics and standards are absent, apart from Tri's privacy row and the ADNI acknowledgement.

## 11. Terms for non-experts (what it is → what it does → why it matters here)
- Tri: "Serverless architecture simplifies backend components by breaking them down into single-purpose functions and leveraging containerization technology, packaging code into lightweight, isolated containers that can be easily deployed and scaled on demand."
- Tri: "FAST: Corrects for bias field, which improves image quality by eliminating intensity variations caused by the scanner's magnetic field [26]."
- VBPH: "Auscultation is a quick test where the doctor uses a stethoscope to listen to the chest sound on various positions to gain insight into the activities and conditions of the heart and lung of the patient."

## 12–13. Style; appendix
- **Tense:** VBPH is past tense throughout (even "STFT was a method"). Tri mixes present-tense definitions with proposal-style "will".
- **Person:** "this study" (VBPH, 17×) or "this project" (Tri, 26×), plus the passive; occasional "we" or "my".
- **Paragraphs:** median 59 and 68 words measured. Real paragraphs are about 60–120 words, because the conversion split them at page ends.
- **Transitions:** explicit ("Nevertheless", "In contrast").
- **Equations:** VBPH numbers its few equations (1)–(3), followed by a "Where …" line; Tri's are unnumbered.
- **Appendix / code link:** none in either.

## Patterns to copy
- The department Ch1 sequence, ending with a research-framework flowchart.
- The pipeline figure at the head of Methods, right after the data section, then one subsection per block.
- Consecutive "Figure n:" numbering with short noun-phrase captions (about 6–9 words).
- Borrowed figures only in Ch1–Ch2, cited in the caption with "[n]".
- A short decision matrix plus a 1–2-paragraph verdict for each design choice; add Tri-style economic and operational categories for the application.
- Each term defined in one sentence, followed by the value used.
- Discussion organised by finding, ending with a comparison table (Study | Method | Task/Data | metrics) whose last row is this work.
- Application: schematic in Methods; screenshots and the operational check in Results.
- A short Conclusion (150–300 words).

## Patterns not to copy
- Tri's 61-page body is over the 50-page limit. VBPH's 40 pages fit.
- Off-by-one table references, "Error! Bookmark not defined", captions styled as headings.
- Validation-only results without uncertainty or statistics; unscored matrices with criteria chosen after the fact.
- "Will" in Methods, "my model", borrowed figures cited only in the body text.
