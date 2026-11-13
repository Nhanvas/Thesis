"""Deck v5 (21/10), main slides 1-27. Base: the author's Canva deck v2 (Thesis_final_slide.pdf, 21/10).
Changes = the feedback list of chat D4g (21/10) that the author approved: fixes, fewer words, cite lines, one References page.
Numbers: NUMBERS_LOCK §1-§15 only."""
from lib5 import *

S = {}
NAVI, NAVM, NAVR, NAVD, NAVC = "Introduction", "Methodology", "Results", "Discussion", "Conclusion"


def ab(t, x, y, w, fs, extra=""):
    return (f'<p style="position:absolute;left:{x}px;top:{y}px;width:{w}px;font-family:{FH};font-size:{fs}px;'
            f'line-height:1.2;text-align:center;color:#0B0908{extra}">{t}</p>')


# ------------------------------------------------------------------ 1 Title
S["s01"] = (
    '<section id="s01" data-transition="fade" style="background:#FFFFFF;padding:0px">'
    f'{img("title_bg", "International University and School of Biomedical Engineering logos", 1920, 1080, ";position:absolute;left:0px;top:0px")}'
    + ab("VIETNAM NATIONAL UNIVERSITY - HO CHI MINH CITY<br>INTERNATIONAL UNIVERSITY<br>SCHOOL OF BIOMEDICAL ENGINEERING", 300, 58, 1320, 44)
    + ab("<b>Thesis Defense</b>", 775, 297, 371, 46, ";height:95px;line-height:89px;border:3px solid #0B0908;border-radius:48px")
    + ab("<b>Unsupervised Epileptic Seizure Temporal Localization in Scalp<br>EEG using Graph Autoencoder and Change Point Detection</b>",
         40, 462, 1840, 66, f";color:{BLUE}")
    + ab("<b>Advisor:</b> Assoc. Prof. Ha Thi Thanh Huong &#160;&#160;&#160;&#160; <b>Reviewer:</b> Dr. Ngo Thi Lua", 160, 726, 1600, 46)
    + ab("<b>Student:</b> Nguyen Quoc Trung Nhan - BEBEIU22184", 260, 818, 1400, 46)
    + ab("November 2026", 660, 932, 600, 46)
    + "<aside>Title. Greet the committee; one sentence on the topic.</aside></section>")

# ------------------------------------------------------------------ 2 Table of Content
rows = [("01.", "Introduction", "Epilepsy, EEG review and the research gap"),
        ("02.", "Methodology", "From raw EEG to seizure onset and offset"),
        ("03.", "Results", "Unseen patients, external data and the review app"),
        ("04.", "Discussion", "Comparison, deployment and limits"),
        ("05.", "Conclusion", "Goals achieved and next steps")]
items = "".join(
    f'<div style="display:flex;flex-direction:row;align-items:center;gap:28px;border-bottom:2px solid #C9D9EA;padding:24px 0px">'
    f'<p style="width:110px;font-family:{FH};font-size:66px;font-weight:700;color:{BLUE}">{n}</p>'
    f'<p style="width:420px;font-family:{FH};font-size:58px;color:{INK}">{t}</p>'
    f'<p style="flex:1;font-size:50px;color:{INK}">{d}</p></div>' for n, t, d in rows)
S["s02"] = slide("s02", "Table of Content", f'<div style="display:flex;flex-direction:column;gap:4px;padding:10px 40px 0px 80px">{items}</div>', 2)

# ------------------------------------------------------------------ 3 Epilepsy
left = colm(p("<b>A common chronic disease</b>", 36),
            ul([f"About {hl('50 million', False)} people worldwide, nearly {hl('80%', False)} in low- and middle-income countries",
                f"Up to {hl('70%', False)} could be seizure-free with the right medicine",
                f"Ho Chi Minh City: about {hl('5.5 per 1,000', False)} people live with epilepsy"], 34), gap=6)
right = colm(p("<b>What a seizure is</b>", 36),
             ul([f"{hl('Excessive electrical discharges', False)} in a group of brain cells",
                 f"{hl('Focal', False)} onset: networks of one hemisphere, can spread to both",
                 f"{hl('Generalized', False)} onset: both hemispheres engaged rapidly"], 34), gap=6)
pics = row(img("ep_person", "A person having a seizure and an overactive brain with EEG waves", 600, 450),
           img("ep_brain", "No seizure, focal seizure and generalized seizure on the brain with their EEG", 640, 462),
           gap=400, align="end", extra=";justify-content:space-between")
S["s03"] = slide("s03", "Epilepsy",
    row(left, right, gap=60) + pics +
    p(f"<b>→ A seizure arises in and spreads through {hl('brain networks')}, so it shows on several channels together</b>", 34),
    3, nav=NAVI, gap=14, cite="World Health Organization, 2024 · Phạm & Vũ, 2023",
    notes="Disease and burden, then the mechanism that motivates a graph: a seizure is a network event seen on several channels.")

# ------------------------------------------------------------------ 4 EEG and the Review Burden
imgs = row(img("eeg_cap", "Scalp electrodes on the head and the EEG reading on a monitor", 600, 345),
           f'<p style="font-size:90px;color:{BLUE};padding:110px 0px 0px 0px">➜</p>',
           img("eeg_onset", "EEG trace from preictal to postictal with the seizure onset marked in red", 760, 285),
           gap=40, align="start", extra=";justify-content:center")
t4 = table(["", "Step 1: Record", "Step 2: Read", "Step 3: Labeling", "Step 4: Decide"],
           [["<b>Protocol</b>", "Records brain electrical activity for hours to days",
             "The reader goes through the whole recording before the report is finalized",
             "Each seizure is marked with its onset, offset and the channels involved",
             "The marks support diagnosis, classification and pre-surgical evaluation"],
            [f"<b>{span('Challenge', HL)}</b>", f"Recordings run for days: {hl('1 in 3', False)} first seizures appear only after 24 h",
             "Time-consuming and labour-intensive", f"Artifacts can mimic or hide seizures; experts agree only moderately ({hl('κ = 0.58', False)})",
             "The labels must be accurate"]],
           [13, 21, 22, 23, 21], fs=29)
S["s04"] = slide("s04", "EEG and the Review Burden",
    imgs + p("Long-term scalp EEG is the clinical standard: non-invasive, it records brain electrical activity directly", 32) + t4 +
    p(f"<b>→ Need: {hl('review triage')}: candidate seizure intervals with onset and offset, for the reader to confirm</b>", 33),
    4, nav=NAVI, gap=12,
    cite="Timpte et al., 2023 · Tatum et al., 2022 (ILAE–IFCN guideline) · Tatum et al., 2011 · Halford et al., 2015 (8 experts, ICU EEG)",
    notes="Follow the EEG from recording to decision. 1 in 3 first seizures after 24 h: Timpte 2023 (19 patients, 72 h). "
          "Whole file read before the report: ILAE-IFCN guideline. kappa 0.58: Halford 2015, 8 experts, ICU EEG.")

# ------------------------------------------------------------------ 5 Related Work and Gap
t5 = table(["Study", "Labels used", "“Normal” learned from", "Output · evaluated on"],
           [["Shyu et al., 2023 · CNN", "yes", "— (supervised)", "window class · F1 69% → 37% on unseen patients"],
            ["Yıldız et al., 2022 · VAE", "no", "windows of the same patients", "window score · same patients"],
            ["Ho & Armanfard, 2023 · graph SSL", "no", "seizure-free corpus", "channel / clip scores"],
            ["Ojemann et al., 2026 · DynaSD", "threshold from labelled iEEG", "first minutes of the recording", "events · Siena, SzCORE"]],
           [27, 18, 25, 30], fs=34)
gaps = colm(p(hl("Gaps for a new patient:"), 34),
            ul(["“Normal” from other patients or a short baseline", "Threshold and drift set with labels",
                "Window or channel scores: no onset / offset", "Rarely scored per event on unseen patients"], 35), w=780, gap=4)
rq = dashed(p(f"<b>Research question:</b> can a learned anomaly score place seizure {hl('onsets and offsets')} in a new "
              f"patient’s recording, without any {hl('seizure label')} of that patient?", 38, ";line-height:1.45"), pad="20px 26px", fill=True)
S["s05"] = slide("s05", "Related Work and Gap",
    t5 + row(gaps, f'<p style="font-size:90px;color:{BLUE};padding:40px 0px 0px 0px">➜</p>', rq, gap=26, align="start"),
    5, nav=NAVI, gap=18,
    notes="Four families, one row each; the four gaps lead to one research question.")

# ------------------------------------------------------------------ 6 Thesis Goals
def tagp(t, reg=True):
    c = BLUE if reg else MUTED
    return f' <span style="color:{c}">({t})</span>'


def goal(lab, title, line, t, reg=True):
    return (f'<div style="display:flex;flex-direction:column;gap:2px">'
            f'<p style="font-size:38px;font-weight:700">{span(lab, HL)} {title}{tagp(t, reg)}</p>'
            f'<p style="font-size:36px;padding:0px 0px 0px 6px">→ {line}</p></div>')


left = colm(f'<p style="font-size:39px;font-weight:700">{span("Goal:", HL)} localize seizure onset and offset without labels{tagp("Registered")}</p>',
            goal("Objective 1:", "An unsupervised anomaly score", "built from the spatial-temporal connectivity of multi-channel scalp EEG", "Registered"),
            goal("Objective 2:", "Onset and offset localization", "by non-parametric change point detection on that score", "Registered"),
            goal("Objective 3:", "A channel-level explanation", "tested against a blind channel annotation", "Added", False),
            goal("Objective 4:", "A review application", "that runs the whole system on complete recordings", "Added", False), gap=44)
reqs = dashed(p("<b>Design requirements:</b>", 34) + ul(["No seizure label of the reviewed patient", "Events with onset and offset",
              "One model for every new patient", "Bounded review load", "Settings fixed before testing",
              "Ordinary CPU, data stay in the hospital", "Every number traceable to a result file"], 34), w=640)
S["s06"] = slide("s06", "Thesis Goals", row(left, reqs, gap=40, extra=";padding:14px 0px 0px 0px"), 6, nav=NAVI,
    notes="Goal and Objectives 1-2 are the signed registration form; Objectives 3-4 were added. The conclusion closes each one.")

# ------------------------------------------------------------------ 7 Study Design Overview
S["s07"] = slide("s07", "Study Design Overview",
    fig("m07_pipe", "Processing pipeline from 18-channel bipolar EEG to seizure events with onset and offset", 1720, 726,
        "Figure 1: Processing pipeline"), 7, nav=NAVM, gap=10,
    sub=f"<b>From raw EEG to seizure events in one pipeline: a {hl('graph per window')}, a {hl('learned score')}, a budgeted detector and change points</b>",
    notes="Walk the pipeline once: window graphs, autoencoder, per-channel distance, ensemble score, budget detector, change points.")

# ------------------------------------------------------------------ 8 Datasets
b1 = dashed(p(f"<b>{span('CHB-MIT', BLUE)} · Boston Children’s Hospital, PhysioNet</b>", 33) +
            ul(["24 cases of children: 23 original + 1 added later", "256 Hz, 10–20 system, 18 bipolar derivations"], 33), pad="12px 20px", fill=True)
b2 = dashed(p(f"<b>{span('Siena Scalp EEG', BLUE)} · University of Siena, PhysioNet</b>", 33) +
            ul(["14 adults (8 men 25–71 y, 6 women 20–58 y), another hospital", "512 Hz → 256 Hz, referential → 18 bipolar, notch 50 Hz"], 33), pad="12px 20px", fill=True)
t8 = table(["Set", "Patients", "Hours", "Seizures", "Used for"],
           [["Training", "12 CHB-MIT", "566.43", "93", "train the autoencoder"],
            ["Validation", "3 CHB-MIT", "115.82", "13", "monitor training; design"],
            ["Test", "8 CHB-MIT", "279.39", "76", "held-out and final evaluation"],
            ["External", "chb24 (CHB-MIT)", "21.3", "16", "scored once, unchanged"],
            ["External", "Siena, 14 adults", "141.0", "47", "scored once, unchanged"]], [14, 22, 13, 13, 38], fs=34, width=1330)
S["s08"] = slide("s08", "Datasets",
    row(b1, b2, gap=24) +
    row(colm(t8, p(f"Split {hl('by patient', False)} before any training (chb01 and chb21 are one child: both in training)", 31), w=1330, gap=14),
        fig("m08_mont", "The 18 bipolar derivations of the 10-20 system", 470, 438, "Figure 2: 18 bipolar derivations", 26), gap=30),
    8, nav=NAVM, gap=18, cite="Shoeb, 2010 · Detti et al., 2020 · EPFL SzCORE benchmark (Siena annotations)",
    notes="Data slide: development on CHB-MIT children, two external sets scored once.")

# ------------------------------------------------------------------ 9 Preprocessing
steps = colm(
    p(f"1. <b>Band-pass {hl('0.5–60 Hz')}, 4th order, zero phase</b><br>→ removes slow drift and fast noise without shifting the waveform", 33),
    p(f"2. <b>Notch {hl('60 Hz')} (Siena 50 Hz)</b><br>→ removes power-line interference", 33),
    p(f"3. <b>Non-overlapping {hl('4 s windows')}</b> (1,024 samples)<br>→ one graph per window", 33),
    p(f"4. <b>Per-patient {hl('channel z-score')}</b><br>→ one scale across channels and recordings", 33),
    p(span("CHB-MIT z-score statistics exclude annotated seizures (disclosed and measured)", HL), 30), gap=18)
S["s09"] = slide("s09", "Preprocessing",
    row(fig("m09_pre", "chb10 raw and filtered EEG and the spectrum of P7-O1", 1060, 706,
            "Figure 3: chb10: (a) raw, (b) filtered and z-scored, (c) spectrum of P7-O1, 60 Hz peak removed", 27), steps, gap=30),
    9, nav=NAVM, gap=12,
    sub=f"<b>Filtering and {hl('per-patient scaling')} make channels and recordings comparable before any graph is built</b>")

# ------------------------------------------------------------------ 10 Graph Construction
S["s10"] = slide("s10", "Graph Construction and Node Features",
    img("m10_graph", "Edges from wPLI and AEC coupling, sparsified to the strongest 20 %; node features of 18 + 5 + 7 numbers", 1840, 692) +
    p(f"<b>→</b> One graph per 4 s window: {hl('edges')} = coupling, {hl('nodes')} = each channel’s own activity, {hl('amplitude')} included", 35),
    10, nav=NAVM, gap=24, cite="Vinck et al., 2011 (wPLI) · Bruns et al., 2000 (AEC)")

# ------------------------------------------------------------------ 11 Graph Autoencoder
S["s11"] = slide("s11", "Graph Autoencoder",
    img("m11_gae", "Two-layer graph convolutional encoder to a 16-number latent per channel; adjacency and feature decoders in training only", 1840, 671) +
    p(f"<b>→</b> Learns normal coupling from {hl('seizure-free')} windows of the 12 training patients; {hl('3,964')} parameters run on a CPU", 35),
    11, nav=NAVM, gap=24, cite="Kipf & Welling, 2016, 2017")

# ------------------------------------------------------------------ 12 Ensemble Anomaly Score
S["s12"] = slide("s12", "Ensemble Anomaly Score",
    img("m12_score", "Per-channel Mahalanobis distance, robust z, four members, drift correction and the ensemble score", 1840, 690) +
    p(f"<b>Key idea:</b> “normal” = the patient’s {hl('own whole recording')}, so no label is needed; the cost is {hl('no real-time use')}", 35),
    12, nav=NAVM, gap=24, cite="Ledoit & Wolf, 2004")

# ------------------------------------------------------------------ 13 Detection and Localization
txt = colm(p("<b>Detection</b>", 35),
           ul(["Smooth 20 s (5 windows)", f"Per-patient {hl('alarm budget')}: p = clip(q, 0.5%, 2%)",
               "q read from the score itself, no labels", "Above the threshold → events, merge &lt; 90 s"], 34),
           p("<b>Localization</b>", 35, ";padding:12px 0px 0px 0px"),
           ul([f"{hl('Kernel change points')} (rbf) on event ± 60 s", "Exactly 2 change points → onset, offset", "No penalty to tune"], 34), gap=6)
S["s13"] = slide("s13", "Detection and Localization",
    row(fig("m13_det", "chb03 seizure: score, threshold, detector event and localized event", 1110, 677,
            "Figure 4: One recorded seizure (chb03): score, threshold, detector event and localized event", 27), txt, gap=34),
    13, nav=NAVM, gap=12, cite="Arlot et al., 2012 · Truong et al., 2020",
    sub=f"<b>A {hl('label-free budget')} decides how much to flag; {hl('change points')} then place the onset and offset</b>")

# ------------------------------------------------------------------ 14 Evaluation
t14 = table(["Evaluation", "Patients", "Role"],
            [["Development", "15 CHB-MIT", "every design choice"],
             ["Held-out", "8 test", "main estimate, scored once"],
             ["Final (test-informed)", "8 test", "+ per-patient budget, designed with test information"],
             ["External", "chb24, Siena", "scored once, unchanged"],
             ["Application", "8 test", "the app, no labels"]], [32, 22, 46], fs=31)
leftc = colm(fig("m14_ev", "Event-based scoring: tolerance before and after, merging, a false alarm", 980, 481,
                 "Figure 5: Event-based scoring: tolerance, merging, false alarm", 27),
             ul(["Hit: overlap with the seizure widened 30 s before, 60 s after", "Merge events &lt; 90 s apart, split events &gt; 5 min"], 33), w=980, gap=12)
rightc = colm(p(f"Sensitivity, precision, F1 and {hl('false alarms per day (FA/day)')}", 33),
              p(f"Pooled and {hl('per-patient mean')} (SzCORE official) · seed 42 and 4 seeds · patient bootstrap", 33), t14, gap=16)
S["s14"] = slide("s14", "Evaluation", row(leftc, rightc, gap=30), 14, nav=NAVM, cite="Dan et al., 2025 (SzCORE)", gap=12,
    sub=f"<b>Every result is scored {hl('per event')} on {hl('continuous recordings')}, the way a reviewer would meet it</b>",
    notes="Formulas of the metrics: Appendix D1.")

# ------------------------------------------------------------------ 15 Graphs and Training
S["s15"] = slide("s15", "Graphs and Training",
    row(fig("m15_den", "Graph density and seizure-background distance per test patient, fixed threshold vs strongest 20 %", 1150, 410,
            "Figure 6: 8 test patients", 27),
        fig("m15_loss", "Training and validation loss of the autoencoder over 200 epochs, 4 seeds", 660, 364,
            "Figure 7: Autoencoder loss, 4 seeds (bold: seed 42)", 27), gap=30) +
    ul([f"Strongest 20%: density {hl('0.196')} for every patient (fixed threshold: 0.92–0.97); separation higher in {hl('8/8')} test patients",
        f"Loss converges in all 4 seeds and validation stays flat → {hl('no overfitting')}",
        f"Latent distance separates seizures from high-amplitude windows: AUROC {hl('0.966')} vs 0.53 for the reconstruction error (development)"], 34),
    15, nav=NAVR, gap=20,
    sub=f"<b>The graphs {hl('separate seizure from background')}, and the autoencoder trains {hl('without overfitting')}</b>")

# ------------------------------------------------------------------ 16 Development and Ablation
S["s16"] = slide("s16", "Development and Ablation",
    fig("m16_dev", "Pooled sensitivity by normal reference and by added component, development patients", 1600, 647) +
    p("15 development patients, 4 seeds, pooled sensitivity at ≤ 25 FA/day. Development is optimistic: the held-out test reached about half (0.336 vs 0.662)", 28, f";font-style:italic"),
    16, nav=NAVR, gap=14,
    sub=f"The patient’s {hl('own recording')}, the {hl('7 absolute features')} and {hl('drift correction')} gave the largest gains")

# ------------------------------------------------------------------ 17 Test Patients
t17 = table(["Seed 42<br><span style='font-weight:400;font-size:24px'>pooled / per-patient mean</span>", "Held-out", "Final (test-informed)"],
            [["Seizures detected", "26 / 76", "37 / 76"], ["Sensitivity", "0.342 / 0.508", "0.487 / 0.577"],
             ["Precision", "0.092 / 0.108", "0.104 / 0.118"], ["F1 score", "0.145 / 0.174", "0.172 / 0.190"],
             ["False alarms/day", "22.2 / 21.8", "27.5 / 26.8"]], [36, 30, 34], fs=31, width=790)
lft = colm(t17, ul([f"{span('Held-out:', BLUE, True)} designed on development, scored once",
                    f"{hl('Final:')} + per-patient budget, designed with test information"], 31), w=790, gap=16)
S["s17"] = slide("s17", "Test Patients",
    row(lft, fig("m17_test", "Seizures detected and false alarms per day for the 8 test patients, held-out and final", 1000, 691,
                 "Figure 8: 8 test patients, seed 42. Red: chb15, the only patient whose detections changed", 26), gap=30),
    17, nav=NAVR, gap=14,
    sub=f"<b>Held-out: {hl('26/76')} unseen seizures at {hl('22.2')} FA/day; the final gain is {hl('1 patient')}</b>")

# ------------------------------------------------------------------ 18 Onset and Offset
S["s18"] = slide("s18", "Onset and Offset",
    fig("m18_bound", "Onset and offset errors of the change point localizer and of the detector boundaries", 1780, 565,
        "Figure 9: Final system, 146 matched seizure–seed pairs (4 seeds), red line = annotated boundary", 27) +
    ul([f"Median absolute error, {hl('final', False)}: onset 32 → 12 s, offset 20 → 24 s; {hl('held-out', False)}: onset 28 → 8 s, offset 16 → 20 s",
        "A simple contiguous-run rule gives 16 s offsets → multichannel change points are the next step"], 34),
    18, nav=NAVR, gap=16,
    sub=f"<b>Change points cut the onset error from {hl('32 s to 12 s')}; the offset is not improved</b>")

# ------------------------------------------------------------------ 19 External Validation
txt = colm(p("<b>chb24 (child, never used):</b>", 34), p(f"{hl('14/16')} at 29.5 FA/day (seed 42)", 34),
           p("<b>Siena (adults):</b>", 34, ";padding:18px 0px 0px 0px"), p(f"per-patient mean {hl('0.633 ± 0.079')} at 41.0 FA/day (4 seeds)", 34),
           p("False alarms concentrate in patients with large budgets (PN06, PN07, PN16)", 32, ";padding:18px 0px 0px 0px"), gap=4)
S["s19"] = slide("s19", "External Validation",
    row(fig("m19_ext", "Siena per patient: seizures detected and false alarms per day", 1370, 627,
            "Figure 10: Siena, 14 adults, seed 42. Red: missed patient and &gt; 70 FA/day", 27), txt, gap=34),
    19, nav=NAVR, gap=16,
    sub=f"<b>On data never used in design, the system transferred from children to {hl('adults')} of another hospital</b>")

# ------------------------------------------------------------------ 20 Channel-Level Explanation
txt = colm(ul([f"Mean AUROC {hl('0.547')} [0.499, 0.597]", f"Anatomical prior {hl('0.739')}; random 0.500",
               "Only chb15 above its prior; without it 0.486", "Blind, every-channel annotation, approved by the supervisor"], 33),
           p(hl("→ Objective 3 evaluated: the app shows the model’s channel anomaly, not an onset map"), 33, ";padding:10px 0px 0px 0px"), gap=6)
S["s20"] = slide("s20", "Channel-Level Explanation",
    row(fig("m20_chan", "Channel ranking AUROC per test patient, this model vs an anatomical prior", 1040, 716,
            "Figure 11: 62 focal test seizures, seed 42, number of seizures in brackets", 26), txt, gap=34),
    20, nav=NAVR, gap=12,
    sub="<b>The channel ranking agrees with a blind annotation only slightly above chance, below an anatomical prior</b>")

# ------------------------------------------------------------------ 21 Review Application
S["s21"] = slide("s21", "Review Application",
    row(img("m21_app", "Application layers: browser (React, Vite, Tailwind), server (Python, FastAPI, PyTorch, PyG, scikit-learn, NumPy), SQLite and disk cache", 930, 683),
        img("m21_shot", "SzScan review screen: score timeline, EEG around an event, channel panel", 820, 513), gap=30) +
    ul([f"8 test patients, 231 files, no labels: {hl('33/76')} at 27.9 FA/day (per-patient mean 0.528)",
        f"{hl('21.68 s')} per hour of EEG on a laptop CPU: about 9 min per recorded day"], 33),
    21, nav=NAVR, gap=12,
    sub=f"<b>The thesis system runs {hl('end to end')} in a local review application, {hl('without labels')}</b>", notes="Then switch to the live demo (patient ingested beforehand); fallback video in Appendix G3.")

# ------------------------------------------------------------------ 22 Comparison
t22 = table(["Method", "Labels", "Sens.", "Prec.", "F1", "FA/day"],
            [["<b>This work</b>", "none of the patient", "<b>0.633</b>", "0.160", "0.226", "<b>41.0</b>"],
             ["DynaSD (Ojemann, 2026)", "threshold: labelled iEEG", "0.664", "0.126", "0.170", "77.7"],
             ["Transformer (Zhu, 2023)", "supervised, TUH", "0.674", "0.484", "0.479", "15.3"],
             ["EventNet (2024)", "supervised, TUH", "0.587", "0.578", "0.526", "8.2"]],
            [30, 26, 11, 11, 11, 11], fs=38, hl=(0,), width=1600)
S["s22"] = slide("s22", "Comparison with Other Studies",
    p("<b>Siena, SzCORE benchmark (per-patient mean)</b>", 33) + t22 +
    p("Entries trained on Siena excluded · this work: 4 seeds, own implementation of the scoring rules", 31, f";color:{MUTED}") +
    p("On CHB-MIT, supervised results fall on unseen patients: F1 69% → 37% (Shyu, 2023); 75% at ~115 FA/day (Ali, 2024); "
      "the SzCORE challenge leader found 37% at ~1 FA/day (Dan, 2026)", 34, ";padding:16px 0px 0px 0px"),
    22, nav=NAVD, gap=16,
    sub=f"<b>Same data and rules: similar sensitivity to the only label-free method at {hl('half its false alarms')}; supervised methods raise fewer</b>",
    cite="EPFL SzCORE benchmark (Zhu 2023, EventNet 2024 entries) · Ojemann et al., 2026 · Shyu et al., 2023 · Ali et al., 2024 · Dan et al., 2026")

# ------------------------------------------------------------------ 23 Deployment and Impact
t23 = table(["Criterion (weight)", "Cloud", "Workstation", "Bedside"],
            [["Data protection, societal (30%)", "2", "<b>5</b>", "4"], ["Cost, economic (25%)", "3", "<b>4</b>", "2"],
             ["Processing time, technical (20%)", "5", "<b>4</b>", "2"], ["Hardware and energy, environmental (15%)", "2", "<b>4</b>", "3"],
             ["Maintenance and scaling, global (10%)", "5", "<b>3</b>", "2"], ["<b>Weighted total</b>", "3.15", "<b>4.20</b>", "2.75"]],
            [52, 14, 20, 14], fs=34, hl=(5,), width=1150)
side = colm(p(f"<b>{span('Who benefits', GREEN)}</b>", 34),
            ul(["Patients whose recordings wait longest for a reader", "Sites without labels, GPU or cloud"], 34),
            p(f"<b>{span('Who bears the risk', HL)}</b>", 34, ";padding:14px 0px 0px 0px"),
            ul(["Patients with missed seizures: the reviewer must still read everything", "The reviewer: 27.5 FA/day (final, seed 42)"], 34), gap=6)
S["s23"] = slide("s23", "Deployment and Impact",
    row(colm(t23, cap("Deployment decision matrix (scores 1–5)", 28), w=1150, gap=8), side, gap=40),
    23, nav=NAVD, gap=20,
    sub=f"<b>Processing on the hospital’s own workstation keeps a child’s EEG {hl('on site')}; the reviewer starts from about "
        f"{hl('31 minutes')} of candidates per recorded day, prepared in about 9 minutes on a laptop CPU</b>",
    notes="Weights are engineering judgment; with equal weights the workstation still ranks first (4.0 vs 3.4 and 2.6).")

# ------------------------------------------------------------------ 24 Limitations
t24 = table(["Limit", "Measured cause", "Next step"],
            [["Short seizures", "4 of 18 under 20 s detected; 4 s windows + 20 s smoothing", "shorter or overlapping windows, retrain"],
             ["Seizures under the patient’s own activity", "chb06, chb13, chb16: 5 of 32 found; need a 3–4% budget", "a representation that separates seizures from high-amplitude states"],
             ["False alarms", "62–91% of top non-seizure windows are high amplitude", "a supervised second stage when labels exist"],
             ["Offsets; 8 test patients", "offset error 24 s (4 seeds); wide bootstrap", "multichannel change points; new patients, prospective study"]],
            [24, 40, 36], fs=28)
S["s24"] = slide("s24", "Limitations",
    row(fig("m24_budget", "Budget a threshold would need to reach each test seizure, with the patient's alarm budget", 780, 380,
            "Figure 12: Budget a threshold would need to reach each seizure (seed 42)", 25),
        fig("m24_dur", "Seizures detected by duration bin, held-out and final", 650, 379,
            "Figure 13: Detection by duration", 25), gap=40, extra=";justify-content:center") + t24,
    24, nav=NAVD, gap=10,
    sub=f"<b>Every limit has a {hl('measured cause')}, and each cause points to the {hl('next step')}</b>")

# ------------------------------------------------------------------ 25 Conclusion
key = dashed(p(f"{hl('Label-free triage of finished EEG recordings:')} without any label of the reviewed patient, the system found about "
               f"a third of unseen seizures at about 22 false alarms per day and placed their onsets. It points the reader to "
               f"candidates; it does not replace reading.", 35, ";line-height:1.4"), pad="14px 24px")
A, AE, EV, DL = span("Achieved", GREEN, True), span("Achieved and evaluated", GREEN, True), span("Evaluated", GREEN, True), span("Delivered", GREEN, True)
goals = ul([f"<b>Goal (registered, localization without labels):</b> onset and offset placed on unseen patients → {A}",
            f"<b>Objective 1 (unsupervised anomaly score):</b> held-out 26/76 at 22.2 FA/day (seed 42) → {A}",
            f"<b>Objective 2 (change point localization):</b> onset error 32 → 12 s (4 seeds), offset not improved → {AE}",
            f"<b>Objective 3 (channel explanation):</b> 0.547, below the prior 0.739 → {EV}",
            f"<b>Objective 4 (application):</b> 33/76 without labels, 21.68 s per hour of EEG → {DL}"], 35, 1.55)
contrib = row(ul(["the patient’s whole recording as the normal reference", "a label-free alarm budget and drift correction"], 35),
              ul(["change points on a learned anomaly score", "event-level tests on unseen and external patients"], 35), gap=40)
S["s25"] = slide("s25", "Conclusion",
    key + p(span("<b>Goal and objectives:</b>", BLUE), 34) + goals + p(span("<b>Contributions:</b>", BLUE), 34) + contrib +
    p(f"<b>{span('Limit:', ORANGE)}</b> short seizures and seizures hidden in the patient’s own activity &#160;·&#160; "
      f"<b>{span('Next:', BLUE)}</b> shorter windows, new patients, a prospective study", 33, ";padding:6px 0px 0px 0px"),
    25, nav=NAVC, gap=10,
    notes="Answer first, then each registered goal and objective with its outcome, then the contributions.")

# ------------------------------------------------------------------ 26 References (one page; works cited on slides 3-22)
import slides_refs as _r
R = _r.R


def rcol(items):
    return colm(*[f'<p style="font-size:24px;line-height:1.25">{r}</p>' for r in items], gap=11)


q = (len(R) + 1) // 2
S["s26"] = slide("s26", "References", row(rcol(R[:q]), rcol(R[q:]), gap=40), 26, gap=14,
                 notes="Works cited on the main slides only; appendix pages carry their own source lines.")

# ------------------------------------------------------------------ 27 Thank you
S["s27"] = (
    '<section id="s27" data-transition="fade" style="background:#FFFFFF;padding:0px">'
    f'{img("thanks_bg", "International University and School of Biomedical Engineering logos", 1920, 1080, ";position:absolute;left:0px;top:0px")}'
    + ab("VIETNAM NATIONAL UNIVERSITY - HO CHI MINH CITY<br>INTERNATIONAL UNIVERSITY<br>SCHOOL OF BIOMEDICAL ENGINEERING", 300, 58, 1320, 44)
    + ab("<b>Thank you for your attention</b>", 260, 490, 1400, 80, ";color:#0F2A3A")
    + ab("Questions &amp; discussion", 460, 640, 1000, 56, ";color:#0F2A3A")
    + f'<p style="position:absolute;right:40px;bottom:22px;width:90px;font-family:{FH};font-size:32px;font-weight:700;color:#5F8FB5;text-align:right">27</p>'
    + "</section>")
