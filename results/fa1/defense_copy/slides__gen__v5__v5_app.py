"""Deck v5 (21/10), appendix 28-61: codes A-H, order of the talk, 5 pages merged away (author 21/10):
Missed Seizure & False Alarm -> E5 Detection Gallery; Siena False Alarms -> E7; Channel Annotation -> F1;
Processing Time -> G1; Development Components -> main slide 16. One Label-Dependent Step -> G2 Application per Patient.
Base: the author's Canva deck v2 pages + D4g sources. Numbers: report tables / NUMBERS_LOCK §1-§15.
Two transcription errors of the Canva copy corrected from the report: Siena FA/day column (Table 15) and chb18 = 6 seizures."""
from lib5 import *

S = {}
YES, NO, PART = span("Yes", GREEN, True), span("No", HL, True), span("Partly", ORANGE, True)


def A(sid, code, title, body, page, sub=None, cite=None, notes=None, gap=16):
    return slide(sid, f"{code} · {title}", body, page, sub=sub, cite=cite, notes=notes, gap=gap, sub_fs=32)


def F(name, alt, w, h, caption=None):
    return f'<div style="display:flex;flex-direction:column;align-items:center;gap:6px">{img(name, alt, w, h)}' + \
           (cap(caption, 26, "center") if caption else "") + "</div>"


# ================================================================== A · Data
rows = [["<b>CHB-MIT</b>", "Scalp, 256 Hz; 23 cases from 22 children + chb24", f"{YES}: hours of continuous EEG per case", f"{YES}", "development, held-out test; chb24 external"],
        ["<b>Siena</b>", "Scalp, 512 Hz; 14 adults, another hospital", f"{YES}: 141.0 h in the files", f"{YES}: read with the SzCORE converter", "external; public SzCORE benchmark"],
        ["<b>TUH Seizure Corpus</b>", "Scalp clinical EEG; 315 subjects, 822 sessions, 504 h", f"{PART}: about 37 min per session on average", f"{YES}: start and end of each event", "not used: future work"],
        ["<b>Bonn</b>", "5 sets × 100 single-channel segments, 173.6 Hz", f"{NO}: 23.6 s segments", f"{NO}: one class per segment", "not used"],
        ["<b>Helsinki neonatal</b>", "Scalp, 256 Hz; 79 neonates, 3 expert annotators", f"{PART}: median 74 min", f"{YES}: 1 s resolution", "not used: neonates, short recordings"]]
S["aA1"] = A("aA1", "A1", "Dataset Selection",
    table(["Dataset", "Recording", "Long, continuous", "Onset and offset", "Role here"], rows, [15, 25, 22, 19, 19], fs=29, hl=(0, 1)), 28,
    sub="CHB-MIT and Siena are the public scalp sets that combine long continuous recordings with the onset and offset of every seizure",
    cite="Shoeb, 2010 · Detti et al., 2020 · Shah et al., 2018 (TUH) · Andrzejak et al., 2001 (Bonn) · Stevenson et al., 2019 (Helsinki) · TUH 504 h / 822 sessions: computed")

sien = [("PN00", "3.24", "3.30", "−0.06", "5"), ("PN01", "13.49", "13.48", "0.00", "2"), ("PN03", "24.23", "12.53", "+11.69", "2"),
        ("PN05", "6.03", "5.98", "+0.05", "3"), ("PN06", "12.07", "12.03", "+0.04", "5"), ("PN07", "8.74", "8.72", "+0.02", "1"),
        ("PN09", "6.85", "6.83", "+0.01", "3"), ("PN10", "18.72", "16.70", "+2.02", "10"), ("PN11", "2.41", "2.42", "−0.01", "1"),
        ("PN12", "6.10", "4.10", "+2.00", "4"), ("PN13", "8.66", "8.65", "+0.01", "3"), ("PN14", "20.46", "23.47", "−3.00", "4"),
        ("PN16", "4.88", "5.05", "−0.17", "2"), ("PN17", "5.12", "5.13", "−0.01", "2"), ("<b>Total</b>", "<b>141.01</b>", "128.40", "+12.61", "<b>47</b>")]
t = table(["Patient", "Hours in EDF (scored)", "PhysioNet table", "Difference", "Seizures"], [list(r) for r in sien],
          [16, 27, 23, 18, 16], fs=23, hl=(2, 7, 9, 11), width=1000)
side = colm(card("Signal path", ["512 Hz → 256 Hz; referential → 18 bipolar derivations; notch 50 Hz",
                                 "Seizure times read with the SzCORE converter, which corrects known annotation errors"], fs=28, tfs=30),
            card("Hours", ["False alarms per day use the 141.0 h actually in the files",
                           "PN03, PN10, PN12: the table is shorter than the files; their own seizure lists agree with the files",
                           "PN14: table and seizure list ≈ 3 h longer than its four files (20.46 h); all 4 seizures scored"], border=ORANGE, fs=28, tfs=30), gap=16)
S["aA2"] = A("aA2", "A2", "Siena Recordings", row(t, side, gap=30), 29,
    sub="The external adult set was scored on the 141.0 h actually in its EDF files; PhysioNet’s summary table lists 128.40 h",
    cite="Detti et al., 2020 · EPFL epilepsy2bids converter · Report Table 20, Appendix A.2")

# ================================================================== B · Signal and graph
rows = [["Filter", "Band-pass 0.5–60 Hz, 4th-order Butterworth; notch 60 Hz (Siena 50 Hz), Q = 30; both zero-phase", "Fixed"],
        ["Window", "4 s, non-overlapping (1,024 samples at 256 Hz); windows without signal excluded", "Fixed"],
        ["Channel z-score", "Mean and SD from every 10th window", "Each patient. CHB-MIT evaluation: seizures and the 4 h after them excluded; external sets and application: whole recording"],
        ["High-amplitude flag", "Any sample above 5 SD; used only to select training windows (46% of non-seizure training windows, about 90% of seizure windows)", "Each patient"],
        ["Reference", "Common average reference per window, only before coupling", "Fixed"],
        ["Coupling", "A = 0.5 wPLI + 0.5 AEC over the 153 channel pairs", "Fixed"],
        ["Sparsification", "Strongest 20% of pairs kept (30 edges), weights unchanged", "Fixed"],
        ["Node features", "30 = adjacency row 18 + relative band powers 5 + absolute features 7", "Fixed"],
        ["Feature scaling", "7 absolute features: training mean and SD, clip ±4, mapped to [0, 1]", "12 training patients"]]
S["aB1"] = A("aB1", "B1", "Signal and Graph Settings", table(["Stage", "Setting", "Fitted on"], rows, [18, 52, 30], fs=28), 30,
    sub="Every setting before the autoencoder is fixed or estimated per patient without labels, except one disclosed z-score step",
    cite="Report Section 2.1.3, 2.3, Table 21 · the label-dependent z-score step is measured in Appendix G2 (33 vs 37 of 76)")


def eqb(name, k, w, h):
    return colm(p(f"<b>{span(name, BLUE)}</b>", 29), img(k, name, w, h), gap=4, extra=f";border-left:5px solid {BLUE};padding:2px 0px 2px 16px")


left = colm(eqb("Common average reference", "eq_car", 400, 107), eqb("Weighted phase lag index", "eq_wpli", 380, 87),
            eqb("Amplitude envelope correlation", "eq_aec", 520, 66), eqb("Combine and sparsify", "eq_adj", 460, 67), w=640, gap=16)
S["aB2"] = A("aB2", "B2", "Edges Calculation",
    row(left, F("fig7_cd", "Combined wPLI plus AEC matrix and the sparse graph of one chb11 window", 1180, 438,
                "(c) combined adjacency and (d) graph after sparsification, one 4 s window of chb11"), gap=30, align="center"), 31,
    sub="Each 4 s window becomes an 18-node graph whose edges average phase-lag and envelope coupling, keeping the strongest 30 of 153 pairs",
    cite="Vinck et al., 2011 · Bruns et al., 2000 · Nunez et al., 1997 · Report Section 2.3.1, Eq. 1–2, Figure 7")

left = colm(eqb("Adjacency row (18)", "eq_row", 470, 75), eqb("Relative band powers (5)", "eq_bp", 440, 87),
            eqb("Absolute features (7)", "eq_ll", 480, 70), img("eq_kurt", "signed-log kurtosis", 400, 57), w=640, gap=14)
S["aB3"] = A("aB3", "B3", "Node Features Calculation",
    row(left, F("fig7_b", "Log band power per channel of one chb11 window", 640, 510, "(b) log band power per channel, one window of chb11"), gap=60, align="center") +
    p("Node feature matrix <b>X = [18 | 5 | 7]</b>, size 18 × 30, one row per channel. The two relative blocks hide the rise in amplitude and the "
      "change in waveform that a reader notices first; the absolute block brings them back. The decoder rebuilds the 12 features of blocks 2 and 3.", 28),
    32, sub="Each node carries 30 numbers: how the channel couples, how its power is spread, and how large and sharp its signal is",
    cite="Welch, 1967 · Tang et al., 2022 (feature standardization) · Report Section 2.3.2, Eq. 3, Figure 7b")

rows = [["Density across patients and states", "0.921 to 0.973; varies by patient and state", "0.196 in both states for every patient (chb17 non-seizure 0.224)"],
        ["Effect on message passing", "Graph almost complete: averaging over neighbours approaches a global mean", "Sparse neighbourhoods keep topological structure"],
        ["Free parameter", "An absolute threshold with no patient-independent value", "A proportion that transfers unchanged between patients"],
        ["Separation of seizure and background connectivity (measured afterwards)", "Reference", "Higher on 8 of 8 test patients: relative Frobenius +48% to +196%, cosine +545% to +903%"],
        ["<b>Adopted</b>", "", span("<b>Strongest 20% of edges</b>", GREEN)]]
S["aB4"] = A("aB4", "B4", "Sparsification Decision",
    table(["Criterion", "Fixed weight threshold", "Strongest 20% of edges"], rows, [30, 33, 37], fs=30), 33,
    sub="Keeping a fixed share of edges gives every patient the same graph density and a larger seizure–background difference",
    cite="ElGazzar et al., 2022 · Li et al., 2026 · Report Table 5, Section 3.1 · figure version: main slide 15")

# ================================================================== C · Model and score
rows = [["Encoder layer 1", "graph convolution + ReLU", "30 → 64", "1,984 (30 × 64 + 64)"],
        ["Encoder layer 2", "graph convolution", "64 → 16", "1,040 (64 × 16 + 16)"],
        ["Adjacency decoder", "Â = clamp(ZZᵀ, 0, 1)", "18 × 16 → 18 × 18", "0"],
        ["Feature decoder", "two-layer network", "16 → 32 → 12", "940 (16 × 32 + 32 + 32 × 12 + 12)"],
        ["<b>Total</b>", "", "", "<b>3,964</b>"]]
eqs = colm(p(f"<b>{span('Encoder and training loss', BLUE)}</b>", 29), img("eq_gcn", "Eq. 4", 774, 61), img("eq_loss", "Eq. 5", 1000, 54),
           p("X: 18 × 30 node features; A: sparse weighted adjacency; each row of Z is the 16-number latent vector of one channel; Xt: the 12 features of blocks 2–3", 26),
           w=1820, gap=8, extra=f";border-left:5px solid {BLUE};padding:4px 0px 4px 16px")
S["aC1"] = A("aC1", "C1", "Autoencoder Specification",
    table(["Part", "Operation", "Size per channel", "Parameters"], rows, [22, 30, 22, 26], fs=29) + eqs +
    p("<b>Training:</b> seizure-free, unflagged windows of the 12 training patients; validation loss on 3 patients; Adam 1 × 10⁻³, cosine annealing, "
      "batch 32, 200 epochs, last epoch kept; seeds 42 (main), 1, 2, 3. At review time only the encoder is used.", 27),
    34, sub="A two-layer graph convolutional encoder gives every channel a 16-number latent vector; both decoders are used only in training",
    cite="Kipf & Welling, 2016, 2017 · Kingma & Ba, 2017 · Report Section 2.4, Eq. 4–5, Appendix B · loss curves: main slide 15")

S["aC2"] = A("aC2", "C2", "Why a Graph Autoencoder",
    F("a32_why", "Reconstruction error 0.527-0.534, latent distance 0.966, channel reading 0.622 vs 0.553", 1700, 645) +
    p("<b>Why a graph:</b> a seizure changes how channels interact. <b>Why an autoencoder:</b> a new patient has no labels, so the model learns "
      "normal coupling. The reference matters most: a feature density with the same reference reached 0.596.", 30),
    35, sub="The latent distance separates seizures from the patient’s own high-amplitude windows; the reconstruction error does not",
    cite="Report Sections 2.4, 4.2, Table 10 · development patients; AUROC seizure vs high-amplitude windows; pooled sensitivity (2 seeds)")

Y2, N2, P2 = span("Yes", GREEN, True), span("No", HL, True), span("Partly", ORANGE, True)
rows = [["Seizure labels needed", "None", "None", "None"],
        ["Separates seizures from the patient’s own high-amplitude activity", f"{N2}: that activity lies outside other patients’ normal",
         f"{P2}: only the states present at the start of the file", f"{Y2}: those states are part of the reference"],
        ["Covers every state of the patient", N2, f"{N2} (one state per file)", Y2],
        ["Usable in real time", Y2, Y2, f"{N2} (the recording must be finished)"],
        ["Pooled sensitivity, development (≤ 25 false alarms per day)", "0.340 (feature model)",
         "0.191 (10 min) · 0.295 (30 min) · 0.487 (causal 30-min window)", "0.596 (feature model) · 0.612 (latent)"],
        ["<b>Adopted</b>", "", "", span("<b>Patient’s whole recording</b>", GREEN)]]
S["aC3"] = A("aC3", "C3", "Normal Reference Decision",
    table(["Criterion", "Other patients", "First minutes of each file", "Patient’s whole recording"], rows, [28, 22, 26, 24], fs=29), 36,
    sub="Only a reference that contains the patient’s own unusual but normal states can rank seizures above them; the cost is no real-time use",
    cite="Ojemann et al., 2026 (first-minutes baseline) · Report Table 6, Section 2.5.1 · 4 seeds")


def eql(name, k, w, h):
    return row(p(f"<b>{span(name, BLUE)}</b>", 30, ";width:280px"), img(k, name, w, h) if k else "", gap=20, align="center")


S["aC4"] = A("aC4", "C4", "Score Equations",
    eql("Channel distance", "eq_maha", 760, 84) + eql("Robust z", "eq_rz", 420, 83) +
    row(p(f"<b>{span('Four members', BLUE)}</b>", 30, ";width:280px"),
        p("S₁ = 6th, S₂ = 9th, S₃ = 12th largest of the 18 values rc(t); S₄ = their mean", 31), gap=20, align="center") +
    eql("Drift correction", "eq_drift", 1040, 60) + eql("Ensemble", "eq_ens", 330, 122) +
    p("All fitted per patient on the whole recording, without labels: μc and Σc (Ledoit–Wolf), median and MAD, running median ±15 min "
      "(225 windows) inside each file, percentile ranks.", 27, f";color:{MUTED}"),
    37, gap=18, sub="Every quantity that adapts the score to a patient is estimated from that patient’s own recording, without labels",
    cite="Ledoit & Wolf, 2004 · Mahalanobis, 1936/2018 · Leys et al., 2013 · Report Section 2.5, Eq. 6–9")

box = dashed(p("pᵢ = min(max(qᵢ, 0.5%), 2%)", 32) +
             p("qᵢ = share of the patient’s windows where the smoothed mean robust z of the 4 members exceeds k = 4.0677", 30) +
             p("k calibrated once on the 15 development patients so that the median qᵢ = 0.5%; largest development budget 1.1%", 30), w=600, pad="18px 22px")
S["aC5"] = A("aC5", "C5", "Alarm Budget",
    row(box, F("a43_budget", "Alarm budget per test patient: chb15 at the 2 % cap", 1180, 499), gap=40, align="center") +
    p(f"Only chb15 reached the cap, so the whole final gain (0 → 11 of 20) is {hl('one patient: test-informed')}", 32),
    38, gap=22, sub="The budget is read from the score itself: it moves review time between patients without enlarging it on average",
    cite="Report Section 2.6.2, Eq. 10, Table 12 · seed 42")

rows = [["Cost function", "Least squares: assumes a shift in the mean", "Kernel cost: compares whole distributions, non-parametric"],
        ["Direction of response", "Rising and falling changes alike: the end of a high state is also an alarm", "Rising stretches; the localizer accepts only a segment above both neighbours"],
        ["Parameters set on data", "Penalty and magnitude filter, no patient-independent value", "One budget per patient, set without labels; the localizer has none"],
        ["Control of review load", "Number of alarms follows the number of state changes", "The budget bounds the share of each patient’s time flagged"],
        ["Detection, development patients (earlier score)", "Penalized segmentation 0.213 against 0.479; kernel segmentation on the threshold detector’s curve, not above it", "Reference"],
        ["<b>Adopted</b>", "", span("<b>Threshold detector + change point localizer</b>", GREEN)]]
S["aC6"] = A("aC6", "C6", "Detection Design Decision",
    table(["Criterion", "Change points as the detector", "Threshold detector with a change point localizer"], rows, [26, 37, 37], fs=29), 39,
    sub="Change point detection is kept where it is strong, placing boundaries, and a label-free budget bounds how much a reviewer must read",
    cite="Killick et al., 2012 (penalized segmentation) · Arlot et al., 2012 (kernel cost) · Report Table 7, Section 2.6.1")

right = colm(colm(p(f"<b>{span('Kernel cost, 2 change points', BLUE)}</b>", 29), img("eq_cpd", "Eq. 11", 720, 95),
                  p("s1, s2, s3: the three segments; x: the unsmoothed score; k: Gaussian (rbf) kernel", 26), gap=6,
                  extra=f";border-left:5px solid {BLUE};padding:4px 0px 4px 16px"),
             ul(["Search window: event ± 60 s (15 windows), inside the file", "Exactly 2 change points → onset, offset; segments ≥ 2 windows",
                 "Middle segment kept only if its mean is above both neighbours; otherwise the detector’s boundaries stay",
                 "Bandwidth from the data: no penalty to tune", "Localized events merged again at 90 s"], 28, 1.35), gap=14)
S["aC7"] = A("aC7", "C7", "Change Point Localizer",
    row(img("cpd_fig", "chb03 seizure: detector event from the smoothed score and the event after two change points", 1060, 631), right, gap=30, align="center"), 40,
    sub="Change points place the boundaries; used as the detector they also fire when a high-amplitude state ends (0.213 vs 0.479, development)",
    cite="Arlot et al., 2012 · Truong et al., 2020 (ruptures) · Report Section 2.6.3, Eq. 11, Tables 7, 10")

# ================================================================== D · Evaluation
rules = card("Event rules (SzCORE)", ["A detection is a true positive if it overlaps a seizure widened by 30 s before onset and 60 s after offset",
                                      "Events closer than 90 s are merged; events longer than 5 min are split",
                                      "Each recording scored on its own; counts summed per patient",
                                      "Specificity is undefined for events: false alarms per day replace it"], fs=28, tfs=30)
forms = colm(p(f"<b>{span('Metrics', BLUE)}</b>", 30),
             row(img("eq_sens", "sensitivity", 360, 69), img("eq_prec", "precision", 334, 69), gap=60),
             row(img("eq_f1", "F1", 309, 70), img("eq_fpday", "false alarms per day", 397, 73), gap=85), gap=14,
             extra=f";background:{PALE};border-top:5px solid {BLUE};padding:14px 18px")
aggs = card("Aggregates and uncertainty", ["<b>Pooled:</b> from the counts summed over all patients",
                                           "<b>Per-patient mean:</b> mean of each patient’s value: the SzCORE official aggregate; one vote per patient",
                                           "<b>4 seeds, mean ± SD:</b> spread from initialization only, not uncertainty",
                                           "<b>Patient bootstrap 95%:</b> 8 patients resampled with replacement, 10,000 times: uncertainty from having 8 patients",
                                           "<b>Onset / offset error:</b> median absolute difference over matched seizure–seed pairs (4 seeds)"], fs=28, tfs=30)
S["aD1"] = A("aD1", "D1", "Scoring Rules and Statistics", row(colm(rules, forms, gap=18), aggs, gap=24), 41,
    sub="Every number is scored per event on the continuous recordings, and every metric comes from the scorer’s counts",
    cite="Dan et al., 2025 (SzCORE) · Ziyabari et al., 2019 · Efron, 1979 · Report Section 2.8, Eq. 12 · rules illustrated on main slide 14")

S["aD2"] = A("aD2", "D2", "Why Event Metrics",
    F("a42_event", "Window view of 900 scores vs event view of one seizure in the first file of chb03", 1640, 724) +
    p("Window gains did not carry over to events, so every design choice was judged on events", 32), 42,
    sub="A window metric ranks thousands of 4 s windows; the reviewer needs seizure events with onset, offset and a false-alarm rate",
    cite="Dan et al., 2025 (SzCORE) · Report Section 2.8.1")


def stage(n, name, data, rule, result, color):
    return (f'<div style="flex:1;display:flex;flex-direction:column;gap:8px;border:2px solid {color};border-radius:12px;padding:12px 14px">'
            f'<p style="font-family:{FH};font-size:30px;font-weight:600;color:{color}">{n}. {name}</p>'
            f'<p style="font-size:26px;line-height:1.3"><b>Data:</b> {data}</p>'
            f'<p style="font-size:26px;line-height:1.3"><b>Rule:</b> {rule}</p>'
            f'<p style="font-size:27px;line-height:1.3;color:{color}"><b>{result}</b></p></div>')


arr = f'<p style="width:40px;font-size:34px;color:{BLUE};padding:80px 0px 0px 0px">→</p>'
tl = (f'<div style="display:flex;flex-direction:row;gap:6px;align-items:stretch">'
      + stage(1, "Development", "15 patients (12 training + 3 validation)", "every design choice, one rule: best pooled sensitivity at ≤ 25 FA/day",
              "0.670 at 23.3 (4 seeds); optimistic", MUTED) + arr
      + stage(2, "Held-out", "8 test patients, 76 seizures", "design fixed; one budget of 0.5%; scored once, no change",
              "26/76 at 22.2 (seed 42): main estimate", BLUE) + arr
      + stage(3, "Final system", "the same 8 test patients", "+ per-patient budget, designed with test information",
              "37/76 at 27.5 (seed 42): test-informed", ORANGE) + arr
      + stage(4, "External", "chb24; Siena, 14 adults", "final system unchanged, scored once",
              "14/16 at 29.5 (seed 42); 0.633 at 41.0 (4 seeds)", GREEN) + arr
      + stage(5, "Application", "8 test patients, frozen build, empty database", "label-free statistics; every event exported before review, scored outside the app",
              "33/76 at 27.9", GREEN) + "</div>")
split = table(["Split (fixed in the code; the same for all 4 seeds)", "Patients"],
              [["Training (12)", "chb01, chb02, chb04, chb05, chb07, chb08, chb09, chb12, chb19, chb20, chb21, chb23"],
               ["Validation (3)", "chb10, chb11, chb22"], ["Test (8)", "chb03, chb06, chb13, chb14, chb15, chb16, chb17, chb18"]], [34, 66], fs=26)
S["aD3"] = A("aD3", "D3", "Evaluation Timeline",
    tl + split + p("Disclosure: earlier versions were also scored on the test patients during development; chb24, Siena and the application run are the independent evidence.", 26, f";color:{MUTED}"),
    43, gap=14, sub="Every design choice was made on the development patients; each later set was scored once, in this order",
    cite="Report Section 2.8.2–2.8.3, Tables 4, 11, 14, 17 · seeds change only the initialization and the order of training batches")

S["aD4"] = A("aD4", "D4", "Earlier Evaluation Protocol",
    F("a45_proto", "Continuous recording vs a timeline rebuilt from the annotations: 0.303 at 73.3 vs 0.618 at 27.4", 1800, 529) +
    p("The rebuilt timeline removed the high-amplitude windows that cause most false alarms, so it is not used for any result", 32), 44,
    sub="The earlier 0.618 came from a timeline rebuilt from the annotations; on the continuous recording the same system gave 0.303 at 73.3 false alarms per day",
    cite="Report Section 2.8.2 · earlier system, same operating point, 8 test patients")

# ================================================================== E · Results
S["aE1"] = A("aE1", "E1", "Designs Not Adopted",
    F("a44_notadopt", "Pooled sensitivity of each alternative design vs the design kept, development patients", 1800, 662), 45,
    sub="Every alternative was scored with the same rule on the development patients; none gave a gain worth its cost",
    cite="Report Table 10, Section 4.2 · pooled sensitivity at ≤ 25 false alarms per day unless noted")

rows = [["chb03", "7", "7 / 7 / 6 / 7", "22", "13.9", "0.0052", "7 / 7 / 6 / 7", "22", "13.9"],
        ["chb06", "10", "2 / 1 / 1 / 2", "90", "32.4", "0.005", "2 / 1 / 1 / 2", "90", "32.4"],
        ["chb13", "12", "1 / 2 / 2 / 2", "40", "29.2", "0.005", "1 / 2 / 2 / 2", "40", "29.2"],
        ["chb14", "8", "6 / 5 / 6 / 5", "27", "25.0", "0.0065", "6 / 5 / 6 / 6", "34", "31.5"],
        ["chb15", "20", "0 / 0 / 0 / 0", "14", "8.5", "<b>0.02</b>", "<b>11 / 11 / 9 / 11</b>", "53", "32.3"],
        ["chb16", "10", "2 / 2 / 2 / 2", "16", "20.2", "0.005", "2 / 2 / 2 / 2", "16", "20.2"],
        ["chb17", "3", "3 / 3 / 3 / 3", "25", "29.5", "0.005", "3 / 3 / 3 / 3", "25", "29.5"],
        ["chb18", "6", "5 / 5 / 5 / 5", "23", "15.5", "0.0082", "5 / 5 / 5 / 5", "38", "25.7"],
        ["<b>Total</b>", "<b>76</b>", "<b>26</b> (seed 42)", "<b>257</b>", "<b>22.2</b>", "", "<b>37</b> (seed 42)", "<b>318</b>", "<b>27.5</b>"]]
S["aE2"] = A("aE2", "E2", "Test Patients per Seed",
    table(["Patient", "Seizures", "Held-out detected, seeds 42 / 1 / 2 / 3", "Held-out false alarms", "Held-out FA/day",
           "Final budget", "Final detected, seeds 42 / 1 / 2 / 3", "Final false alarms", "Final FA/day"],
          rows, [8, 8, 16, 10, 9, 9, 16, 12, 12], fs=28, hl=(4,)) +
    p("False alarms and FA/day: seed 42, after the localizer. Four seeds, pooled sensitivity: held-out 0.336 ± 0.008, final 0.477 ± 0.022. "
      "Only chb15 reached the 2% cap; chb14 and chb18 got larger budgets that added false alarms but no seizure.", 26, f";color:{MUTED}"), 46,
    sub="Seeds change a patient’s held-out count by at most one seizure; with seed 42, chb15 is the only patient whose detections changed in the final system",
    cite="Report Tables 11, 12, 22")

S["aE3"] = A("aE3", "E3", "Seeds and Intervals",
    F("a47_seeds", "Seed spread vs patient bootstrap interval, and the gain of the final system with its interval", 1800, 541) +
    p(f"The interval of the final gain starts at zero: the gain is {hl('one patient (chb15)')}", 32), 47,
    sub="Seeds change the held-out result by at most one seizure; the patient bootstrap is wide, so the uncertainty is the 8 patients, not the model",
    cite="Report Table 11 · 4 seeds; patient bootstrap, 10,000 resamples")

S["aE4"] = A("aE4", "E4", "Why the Metrics Are Low",
    F("a46_low", "Detected, missed and false alarms per evaluation, and the high-amplitude share of the top non-seizure windows", 1800, 589), 48,
    sub="Precision and F1 are low because false alarms outnumber seizures; most false alarms are the patient’s own high-amplitude states, not seizures nearby",
    cite="Report Sections 3.3, 4.3 · seed 42; 8 test patients, 279.39 h · seizures fill 0.4% of the recorded time")

S["aE5"] = A("aE5", "E5", "Detection Gallery",
    F("a50_gallery", "chb03 detected, chb15 detected with the per-patient budget, chb16 short seizure missed, chb03 false alarm", 1840, 585) +
    p("Panels chosen by fixed rules before drawing: (a) first seizure of chb03; (b) first chb15 seizure found by the final system but not the held-out "
      "evaluation (40 windows); (c) shortest missed seizure of chb16: two 4 s windows, shorter than the 20 s smoothing; (d) highest-scoring false "
      "alarm more than 10 min from any seizure: 132 s of sustained high-amplitude activity whose cause the figure alone cannot show.", 27), 49,
    sub="Detected seizures rise above the patient’s threshold; misses are short or sit inside the patient’s own activity",
    cite="Report Section 3.3.5, Figure 14 · final system, seed 42 · EEG 30 s around onset; score ±5 min")

S["aE6"] = A("aE6", "E6", "Onset and Offset on Every Set",
    F("a51_onoff", "Median onset and offset error of the detector and of the change point localizer on every set", 1800, 606), 50,
    sub="Change points cut the onset error on every set; the offset improves on development and chb24 only",
    cite="Report Table 13 · median absolute error over matched seizure–seed pairs, 4 seeds")

sr = [("PN00", "3.24", "5", "5 / 3 / 4 / 3", "1", "7.6", "0.0113"), ("PN01", "13.49", "2", "2 / 2 / 2 / 2", "10", "17.8", "0.005"),
      ("PN03", "24.23", "2", "2 / 2 / 2 / 2", "54", "53.6", "0.02"), ("PN05", "6.03", "3", "0 / 0 / 0 / 0", "6", "24.0", "0.005"),
      ("PN06", "12.07", "5", "3 / 3 / 3 / 3", "38", "76.1", "0.02"), ("PN07", "8.74", "1", "1 / 0 / 0 / 0", "33", "90.9", "0.0174"),
      ("PN09", "6.85", "3", "1 / 1 / 1 / 1", "6", "21.2", "0.0052"), ("PN10", "18.72", "10", "7 / 6 / 5 / 6", "18", "23.2", "0.005"),
      ("PN11", "2.41", "1", "1 / 1 / 1 / 1", "3", "30.1", "0.02"), ("PN12", "6.10", "4", "3 / 3 / 3 / 1", "8", "31.9", "0.0137"),
      ("PN13", "8.66", "3", "1 / 1 / 3 / 2", "11", "30.7", "0.0113"), ("PN14", "20.46", "4", "3 / 3 / 3 / 3", "44", "51.7", "0.0189"),
      ("PN16", "4.88", "2", "2 / 0 / 1 / 1", "16", "79.8", "0.02"), ("PN17", "5.12", "2", "2 / 2 / 1 / 2", "9", "42.5", "0.02"),
      ("<b>Total</b>", "<b>141.0</b>", "<b>47</b>", "<b>33</b> (seed 42)", "<b>257</b>", "<b>44.0</b>", "")]
t = table(["Patient", "Hours", "Seizures", "Detected, seeds 42 / 1 / 2 / 3", "False alarms", "FA/day", "Budget"],
          [list(r) for r in sr], [12, 11, 11, 26, 14, 12, 14], fs=22, hl=(2, 4, 5, 8, 11, 12, 13), width=1180)
side = colm(card("Siena, 4 seeds", ["Per-patient mean sensitivity 0.633 ± 0.079 at 41.0 FA/day; precision 0.160, F1 0.226",
                                    "Patient bootstrap [0.477, 0.777]; FA/day [32.3, 53.9]"], fs=26),
            card("chb24 (child, never used)", ["Seeds 42 / 1 / 2 / 3: 14 / 13 / 12 / 14 of 16 detected, with 26 / 23 / 26 / 25 false alarms"], border=GREEN, fs=26),
            card("Where false alarms sit", ["Rows shaded: budget above 1.7%; these 7 patients hold 197 of the 257 false alarms",
                                            "10 of 14 patients: at least two thirds of seizures found; PN05: 0 of 3",
                                            "Short recordings inflate the daily rate: PN11 has 3 false alarms in 2.41 h = 30.1 per day"], border=ORANGE, fs=26), gap=14)
S["aE7"] = A("aE7", "E7", "Siena per Patient and Seed", row(t, side, gap=26), 51,
    sub="Ten of 14 adults had at least two thirds of their seizures found; false alarms concentrate in the patients with large label-free budgets",
    cite="Report Tables 14, 15, 23, Section 3.4 · false alarms, FA/day and budget: seed 42, after the localizer")

bench = [["SeizUnet", "TUH, SeizeIT2", "0.287", "0.490", "0.207", "3.5"], ["IctalTrace V4", "TUH", "0.279", "0.358", "0.301", "6.9"],
         ["BrainGoBrr", "TUH", "0.129", "0.210", "0.047", "6.9"], ["He random forest", "CHB-MIT", "0.168", "0.302", "0.091", "8.1"],
         ["EventNet 2024", "TUH", "0.587", "0.578", "0.526", "8.2"], ["Zhu Transformer 2023", "TUH", "0.674", "0.484", "0.479", "15.3"],
         ["<b>This work (4 seeds)</b>", "<b>CHB-MIT, seizure-free windows</b>", "<b>0.633</b>", "<b>0.160</b>", "<b>0.226</b>", "<b>41.0</b>"],
         ["DynaSD", "CHB-MIT subset, iEEG", "0.664", "0.126", "0.170", "77.7"], ["Self-GNN, Tang 2021", "TUH", "0.824", "0.151", "0.198", "112.5"],
         ["EEGWaveNet 2021", "CHB-MIT", "0.858", "0.072", "0.127", "145.5"], ["Velland 2025", "TUH", "1.000", "0.037", "0.071", "274.2"],
         ["Gotman 1982", "none (rule-based)", "0.986", "0.036", "0.067", "286.1"]]
S["aE8"] = A("aE8", "E8", "Siena Benchmark in Full",
    table(["Entry", "Training data", "Sens.", "Prec.", "F1", "FA/day"], bench, [26, 30, 11, 11, 11, 11], fs=27, hl=(6,)), 52,
    sub="Among methods not trained on Siena, this work sits between the supervised low-alarm entries and the high-sensitivity entries that need over 100 alarms per day",
    cite="EPFL SzCORE benchmark (siena.json, commit c57da2f) · Report Table 18 · per-patient mean; entries trained on Siena excluded")

pub = [["Chung 2024", "yes, per patient", "CHB-MIT, 13 selected cases", "100% events, 0.30 FA/h"],
       ["Shyu 2023", "yes", "CHB-MIT, with vs without test subject", "F1 69.34% → 37.31%"],
       ["Ali 2024", "yes", "CHB-MIT, leave-one-subject-out", "75.34%, 4.79 FA/h"],
       ["Yıldız 2022", "no", "CHB-MIT windows, same patients", "AUC 0.68"],
       ["Wang 2024", "no", "CHB-MIT, per patient, segments", "97.69% sensitivity"],
       ["Tang 2022", "for the classifier", "TUH clips", "AUROC 0.875"],
       ["Ho & Armanfard 2023", "no", "channels and clips", "precision 0.704"],
       ["Ojemann 2026 (DynaSD)", "threshold from labelled iEEG", "events, Siena (SzCORE)", "0.664 at 77.7/day"],
       ["Mirzaei & Singh 2025", "threshold per patient", "CHB-MIT, 18 of 24 patients, seizures ≥ 40 s", "91.56%, 0.1 FA/h"],
       ["<b>This work</b>", "<b>none of the reviewed patient</b>", "<b>events, continuous; 8 unseen + 2 external sets</b>", "<b>26/76 at 22.2/day; Siena 0.633 at 41.0</b>"]]
S["aE9"] = A("aE9", "E9", "Published CHB-MIT Results",
    table(["Study", "Seizure labels", "Data and protocol", "Reported result"], pub, [21, 22, 32, 25], fs=27, hl=(9,)), 53,
    sub="Published CHB-MIT numbers use labels, exclude short-seizure patients or tune per patient, so they cannot share a table with an unseen-patient, every-event result",
    cite="Chung et al., 2024 · Shyu et al., 2023 · Ali et al., 2024 · Yıldız et al., 2022 · Wang et al., 2024 · Tang et al., 2022 · Ho & Armanfard, 2023 · Ojemann et al., 2026 · Mirzaei & Singh, 2025 · Report Table 1")

# ================================================================== F · Channel explanation
facts = row(card("Blind", ["Read from the raw EEG, without any model output"], fs=26),
            card("Every channel", ["62 focal seizures: 1–10 channels each, 282 labels; 14 generalized (all 18)"], fs=26),
            card("Approved", ["Protocol and annotation approved by the supervisor before any comparison"], fs=26, border=GREEN),
            card("Where labels sit", ["T7-P7 most often (45); frontopolar 116 of 282 labels (41%); five channels never annotated"], fs=26, border=ORANGE), gap=14)
S["aF1"] = A("aF1", "F1", "Annotation Protocol",
    facts + F("a59_map", "Channel annotation of the 76 test seizures: 18 channels by 76 seizures, grouped by patient", 1330, 549), 54, gap=14,
    sub="CHB-MIT has no channel labels, so every channel of the 76 test seizures was annotated blind to the model and approved before any comparison",
    cite="Report Section 2.7, Appendix D · one reader: agreement, not accuracy · the strong frontopolar and temporal share makes the anatomical prior a strong baseline (0.739)")


def bx(t, w):
    return f'<p style="width:{w}px;font-size:27px;line-height:1.3;background:{PALE};border:2px solid {BLUE};border-radius:10px;padding:10px 14px">{t}</p>'


ar = f'<p style="width:36px;font-size:40px;color:{BLUE}">→</p>'
flow = row(bx("<b>Channel-level latent anomaly</b> rc(t)", 330), ar, bx("<b>Per seizure:</b> 95th percentile of |rc(t)| over its windows", 340), ar,
           bx("<b>Rank</b> the 18 channels", 220), ar, bx("<b>AUROC</b> of the ranking against the blind annotation", 340), ar,
           bx("<b>Mean</b> over the 62 focal seizures", 300), gap=6, align="center")
rows = [["1 · Chance", "Does the ranking beat a random one?", "Scores permuted across channels within each seizure, 1,000 times", "0.547 [0.499, 0.597], p = 0.018", "Above chance, weakly"],
        ["2 · Anatomical prior", "Is it better than a rule that ignores the EEG?", "Prior: how often each channel is annotated in the other 7 patients; paired bootstrap over seizures", "0.547 − 0.739 = −0.191 [−0.262, −0.118]", "Below the prior"],
        ["3 · Seizure-specific", "Does a seizure’s ranking fit its own annotation better than its sibling seizures’ rankings?", "Matched minus swapped, within each patient; permutation, 1,000 times", "−0.002, p = 0.53", "No"]]
S["aF2"] = A("aF2", "F2", "Attribution Method and Tests",
    flow + table(["Test (fixed order)", "Question", "Method", "Result, seed 42", "Reading"], rows, [14, 24, 28, 19, 15], fs=28) +
    p("Method, prior and test order fixed before any comparison; tests 2–3 Holm-corrected; the 14 generalized seizures excluded because AUROC is undefined when all 18 channels are positive.", 26, f";color:{MUTED}"),
    55, sub="The channel ranking was tested in a fixed order against chance, an anatomical prior and the patient’s other seizures",
    cite="Craley et al., 2022 (focal-only scoring) · Zhang et al., 2018 (input-blind baseline) · Report Sections 2.7, 3.5")

rows = [["chb03", "4", "0.404 [0.319, 0.529]", "0.93", "0.903"], ["chb06", "0", "— (all ten generalized)", "—", "—"],
        ["chb13", "11", "0.508 [0.428, 0.585]", "0.45", "0.753"], ["chb14", "8", "0.555 [0.445, 0.672]", "0.14", "0.807"],
        ["chb15", "20", "<b>0.675 [0.602, 0.754]</b>", "<b>0.001</b>", "0.576"], ["chb16", "10", "0.487 [0.363, 0.611]", "0.59", "0.846"],
        ["chb17", "3", "0.418 [0.268, 0.646]", "0.79", "0.831"], ["chb18", "6", "0.444 [0.359, 0.518]", "0.81", "0.831"],
        ["<b>All</b>", "<b>62</b>", "<b>0.547 [0.499, 0.597]</b>", "<b>0.018</b>", "<b>0.739</b>"]]
t = table(["Patient", "Focal seizures", "Mean AUROC [95% CI]", "p vs chance", "Anatomical prior"], rows, [16, 18, 32, 16, 18], fs=29, hl=(4,), width=1180)
side = colm(card("Robustness", ["Seeds 1 / 2 / 3: 0.543 / 0.588 / 0.545", "Without chb15: 0.486 (42 seizures), at chance"], fs=28, tfs=30),
            card("Earlier reconstruction readout", ["0.569, without chb15 0.501: the same pattern"], border=MUTED, fs=28, tfs=30), gap=16)
S["aF3"] = A("aF3", "F3", "Attribution per Patient", row(t, side, gap=30), 56,
    sub="Only chb15 lies above chance and above its anatomical prior; without it the agreement falls to chance",
    cite="Report Table 24, Section 4.4, Appendix D · seed 42; bootstrap over seizures")

# ================================================================== G · Application
side = colm(card("Never reads a label", ["15 automated tests passed: 4 label guards, 7 final-system equivalence, 4 file matching"], fs=26),
            card("Identity on chb03", ["Thesis statistics: 7/7, 22 false alarms, same budget, score difference ≤ 7.31 × 10⁻⁶; label-free statistics (used in practice): 6/7, 20 false alarms"], border=GREEN, fs=26),
            F("a65_time", "Processing time of chb16 (19 files, 19.0 h) in three runs on a laptop CPU", 840, 383,
              "21.68 s per hour of EEG (median of 3 runs, chb16, Intel i5-8250U, no GPU)"), gap=12)
S["aG1"] = A("aG1", "G1", "Application without Labels",
    row(img("a63_arch", "Browser, application server, scoring and storage layers; annotations, rebuilt timelines and label-split arrays are never read at run time", 930, 650), side, gap=26), 57,
    sub="The application never reads a label: automated tests guard every label path, and on chb03 it reproduces the thesis system",
    cite="Report Section 2.9.2, Figure 10, Section 3.6, Appendix E, Table 25 · graph construction takes most of the processing time")

S["aG2"] = A("aG2", "G2", "Application per Patient",
    F("a48_label", "Seizures detected and false alarms per test patient: final system vs application with label-free statistics", 1800, 662) +
    p("The application run: 8 test patients, 231 files, 279.39 h, every event exported before review: 33/76 (pooled 0.434) at 27.9 FA/day, per-patient mean 0.528", 28), 58,
    sub="One step of the thesis evaluation used labels (CHB-MIT z-score statistics exclude annotated seizures); with label-free statistics the application found 33 instead of 37 of 76",
    cite="Report Section 3.6, Table 17 · seed 42 · one seizure fewer in chb03, chb06, chb15 and chb16; 323 vs 318 false alarms")

S["aG3"] = A("aG3", "G3", "Demo Recording",
    row(img("a64_demo", "SzScan recording list of the 8 test patients (insert the demo video here)", 1500, 844), extra=";justify-content:center"), 59,
    notes="Fallback: play the recorded demo video here if the live demo fails. Insert the video in Canva on this page.")

# ================================================================== H · Models explored
rows = [["Node features", "Adjacency row + relative band powers (23)", "+ 7 absolute features (30)", "Relative features erase amplitude and waveform: 0.330 → 0.489"],
        ["Readout", "Reconstruction error + graph-level latent + gamma coupling, equal weights", "Channel-level latent, four spatial scales, drift-corrected",
         "Reconstruction near chance against high-amplitude windows (0.527–0.534 vs 0.966); gamma drifts between files; channel 0.622 vs graph 0.553"],
        ["Detector", "Change points on the whole score (penalized segmentation)", "Threshold with a per-patient budget + kernel change point localizer",
         "Segmentation also fires when a high state ends: 0.213 vs 0.479"],
        ["Evaluation", "Timeline rebuilt from the annotations: 0.618 at 27.4", "Continuous recordings, every window in time order",
         "The rebuilt timeline removed the windows that cause most false alarms"],
        ["<b>Continuous test result</b>", "<b>23/76 (0.303) at 73.3</b>", "<b>Held-out 26/76 (0.342) at 22.2; final 37/76 at 27.5</b> (seed 42)", "8 test patients, 76 seizures, false alarms per day"]]
S["aH1"] = A("aH1", "H1", "Earlier and Final System",
    table(["Stage", "Earlier system", "Final system", "Why it changed (measured, development unless marked)"], rows, [14, 26, 27, 33], fs=29, hl=(4,)), 60,
    sub="Each change from the earlier system answered a measured failure; on the continuous recordings it cut false alarms from 73.3 to 22.2 per day",
    cite="Report Sections 2.8.2, 3.2, 4.2, Tables 9, 10 · development: pooled sensitivity at ≤ 25 false alarms per day")

X = span("experiment record", MUTED)
rows = [["Feature density, normal from other patients", "Node features; other patients’ seizure-free EEG", "0.340", "Not adopted: the patient’s own high-amplitude activity lies outside other patients’ normal"],
        ["Feature density, patient’s own recording", "Node features; the patient’s whole recording", "0.596", "Not adopted: below the channel-level latent with the same reference (0.612)"],
        ["Artifact model on the high-amplitude flag", "Flagged windows treated as artifact", "0.096", "Not adopted: called 81.5% of seizure windows artifact; the flag marks amplitude"],
        ["GAE reconstruction error", "Decoder output vs input", "AUROC 0.527–0.534", "Dropped: does not separate seizures from high-amplitude windows (latent 0.966)"],
        ["GAE graph-level latent", "Mahalanobis distance of the mean of 18 latent vectors", "0.553 (2 seeds)", "Replaced: channel-level reading 0.622 (same seeds)"],
        ["GAE fine-tuned per patient", "Unsupervised, on the patient’s own windows", "0.628 vs 0.622 (2 seeds)", "Not adopted: seizure scores rose, non-seizure scores did not fall"],
        [f"Multi-relational GAE, directed coupling ({X})", "+ transfer-entropy graph, earlier system", "Window AUROC 0.926 vs 0.928 (validation)", "Not adopted: a tie within the spread between seeds"],
        [f"Temporal LSTM branch ({X})", "Sequence of windows, earlier system", "—", "Removed: the system without it detected as well as with it"],
        ["Supervised gradient-boosted trees", "Seizure labels of the other development patients, leave one out", "0.702 at 20.5", "Reference only: labels are excluded by the registered aim"],
        ["<b>Final: GAE channel-level latent</b>", "Own-recording reference, drift, 4 scales, budget, localizer", "<b>0.670 at 23.3</b>", span("<b>Adopted</b>", GREEN)]]
S["aH2"] = A("aH2", "H2", "Models Evaluated",
    table(["Model", "Input and reference", "Development result", "Decision and reason"], rows, [25, 26, 17, 32], fs=23, hl=(9,)), 61, gap=12,
    sub="Every alternative was scored under the same rule on the development patients and kept or dropped for a measured reason",
    cite="Report Tables 6, 10, Section 4.1–4.2 · experiment record: not in the report · pooled sensitivity at ≤ 25 false alarms per day")
