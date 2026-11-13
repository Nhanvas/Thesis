"""D4g appendix, groups C-D (new pages)."""
from lib import *

S = {}

# ---------------------------------------------------------------- C1 Autoencoder Specification
rows = [["Encoder layer 1", "graph convolution + ReLU", "30 → 64", "1,984 (30 × 64 + 64)"],
        ["Encoder layer 2", "graph convolution", "64 → 16", "1,040 (64 × 16 + 16)"],
        ["Adjacency decoder", "Â = clamp(ZZᵀ, 0, 1)", "18 × 16 → 18 × 18", "0"],
        ["Feature decoder", "two-layer network", "16 → 32 → 12", "940 (16 × 32 + 32 + 32 × 12 + 12)"],
        ["<b>Total</b>", "", "", "<b>3,964</b>"]]
t = table(["Part", "Operation", "Size per channel", "Parameters"], rows, [24, 28, 22, 26], fs=28)
eqs = (f'<div style="display:flex;flex-direction:column;gap:10px;border-left:5px solid {BLUE};padding:4px 0px 4px 16px">'
       f'<p style="font-size:27px;font-weight:700;color:{BLUE}">Encoder (Eq. 4) and training loss (Eq. 5)</p>'
       f'{img("eq_gcn", "Eq. 4", 774, 61)}{img("eq_loss", "Eq. 5", 1000, 54)}'
       f'<p style="font-size:27px;line-height:1.3">X: 18 × 30 node features; A: sparse weighted adjacency; each row of Z is the 16-number latent vector of one channel; Xt: the 12 features of blocks 2–3.</p></div>')
train = (f'<div style="width:620px;display:flex;flex-direction:column;gap:10px">'
         + card("Training data", ["Windows of the 12 training patients outside seizures and the 4 h after them, with signal, not flagged high-amplitude",
                                  "Loss on the same kind of windows of the 3 validation patients monitored for overfitting"])
         + card("Optimization", ["Adam, learning rate 1 × 10⁻³, cosine annealing", "Batch 32 windows, 200 epochs, last epoch kept",
                                 "Seeds 42 (main), 1, 2, 3"])
         + card("At review time", ["Only the encoder is used: Z of every channel → anomaly score", "Small enough for an ordinary CPU"], border=GREEN)
         + "</div>")
S["aC1"] = section("aC1", "Appendix C1 · Autoencoder Specification",
    f'<div style="display:flex;flex-direction:row;gap:30px;align-items:start"><div style="flex:1;display:flex;flex-direction:column;gap:18px">{t}{eqs}</div>{train}</div>', 37,
    sub="A two-layer graph convolutional encoder gives every channel a 16-number latent vector; both decoders are used only in training",
    cite="Kipf & Welling, 2016, 2017 · Kingma & Ba, 2017 · Report Section 2.4, Eq. 4–5, Appendix B · loss curves: main slide 15")

# ---------------------------------------------------------------- C3 Normal Reference Decision
Y, N, P = span("Yes", GREEN, True), span("No", RED, True), span("Partly", ORANGE, True)
rows = [["Seizure labels needed", "None", "None", "None"],
        ["Separates seizures from the patient’s own high-amplitude activity", f"{N}: that activity lies outside other patients’ normal",
         f"{P}: only the states present at the start of the file", f"{Y}: those states are part of the reference"],
        ["Covers every state of the patient", N, f"{N} (one state per file)", Y],
        ["Usable in real time", Y, Y, f"{N} (the recording must be finished)"],
        ["Pooled sensitivity, development (≤ 25 false alarms per day)", "0.340 (feature model)",
         "0.191 (10 min) · 0.295 (30 min) · 0.487 (causal 30-min window)", "0.596 (feature model) · 0.612 (latent)"],
        ["<b>Adopted</b>", "", "", span("<b>C · whole recording</b>", GREEN)]]
S["aC3"] = section("aC3", "Appendix C3 · Normal Reference Decision",
    table(["Criterion", "A · Other patients", "B · First minutes of each file", "C · Patient’s whole recording"], rows, [28, 22, 26, 24], fs=28), 39,
    sub="Only a reference that contains the patient’s own unusual but normal states can rank seizures above them; the cost is no real-time use",
    cite="Ojemann et al., 2026 (first-minutes baseline) · Report Table 6, Section 2.5.1 · A vs C: same input features; B vs C: same latent score, 4 seeds")

# ---------------------------------------------------------------- C4 Score Equations
def srow(step, k, w, h, meaning, fitted):
    return (f'<div style="display:flex;flex-direction:row;align-items:center;gap:20px;border-bottom:1px solid {LINE};padding:6px 0px">'
            f'<p style="width:250px;font-size:28px;font-weight:700;color:{BLUE}">{step}</p>'
            + (f'<div style="width:760px">{img(k, step, w, h)}</div>' if k else f'<p style="width:760px;font-size:27px;font-style:italic">{w}</p>') +
            f'<p style="flex:1;font-size:26px;line-height:1.3">{meaning}<br><span style="color:{MUTED}">{fitted}</span></p></div>')

body = (f'<div style="display:flex;flex-direction:column;gap:4px">'
        + srow("1 · Channel distance (Eq. 6)", "eq_maha", 599, 66, "Squared Mahalanobis distance of channel c’s latent vector from its own distribution",
               "μc, Σc per patient and channel, all windows with signal; Ledoit–Wolf shrinkage")
        + srow("2 · Robust z (Eq. 7)", "eq_rz", 353, 70, "Channel-level latent anomaly on a common scale; median and MAD resist seizure extremes",
               "median and MAD over all windows of the patient")
        + srow("3 · Four members", None, "S₁ = 6th, S₂ = 9th, S₃ = 12th largest of the 18 values rc(t); S₄ = their mean", 0, "6th, 9th and 12th largest of the 18 values of rc(t), and their mean: at least a third, half, two thirds of the channels, or all",
               "fixed; one faulty electrode raises only one channel")
        + srow("4 · Drift correction (Eq. 8)", "eq_drift", 744, 43, "Removes the level of each member file by file; a seizure of seconds to minutes still stands out",
               "running median ±15 min (225 windows) inside each file; level only")
        + srow("5 · Ensemble (Eq. 9)", "eq_ens", 297, 110, "Mean of the four percentile ranks: one score from 0 to 1 per window",
               "percentile rank among all windows of the patient")
        + "</div>")
S["aC4"] = section("aC4", "Appendix C4 · Score Equations", body, 40,
    sub="Every quantity that adapts the score to a patient is estimated from that patient’s own recording, without labels",
    cite="Ledoit & Wolf, 2004 · Mahalanobis, 1936/2018 · Leys et al., 2013 · Report Section 2.5, Eq. 6–9, Figure 8 (drift)")

# ---------------------------------------------------------------- C6 Detection Design Decision
rows = [["Cost function", "Least squares: assumes a shift in the mean", "Kernel cost: compares whole distributions, non-parametric"],
        ["Direction of response", "Rising and falling changes alike: the end of a high state is also an alarm", "Rising stretches; the localizer accepts only a segment above both neighbours"],
        ["Parameters set on data", "Penalty and magnitude filter, no patient-independent value", "One budget per patient, set without labels; the localizer has none"],
        ["Control of review load", "Number of alarms follows the number of state changes", "The budget bounds the share of each patient’s time flagged"],
        ["Detection, development patients (earlier score)", "Penalized segmentation 0.213 against 0.479; kernel segmentation on the threshold detector’s curve, not above it", "Reference"],
        ["<b>Adopted</b>", "", span("<b>B · threshold detector + change point localizer</b>", GREEN)]]
S["aC6"] = section("aC6", "Appendix C6 · Detection Design Decision",
    table(["Criterion", "A · Change points as the detector", "B · Threshold detector with a change point localizer"], rows, [26, 37, 37], fs=28), 42,
    sub="Change point detection is kept where it is strong, placing boundaries, and a label-free budget bounds how much a reviewer must read",
    cite="Killick et al., 2012 (penalized segmentation) · Arlot et al., 2012 (kernel cost) · Report Table 7, Section 2.6.1")

# ---------------------------------------------------------------- C7 Change Point Localizer (Canva p32 + Eq. 11)
right = (f'<div style="flex:1;display:flex;flex-direction:column;gap:14px">'
         f'<div style="border-left:5px solid {BLUE};padding:4px 0px 4px 16px;display:flex;flex-direction:column;gap:6px">'
         f'<p style="font-size:27px;font-weight:700;color:{BLUE}">Kernel cost, two change points (Eq. 11)</p>{img("eq_cpd", "Eq. 11", 700, 92)}'
         f'<p style="font-size:26px">s1, s2, s3: the three segments; x: the unsmoothed score; k: Gaussian (rbf) kernel</p></div>'
         f'<ul style="font-size:28px;line-height:1.4"><li>Search window: event ± 60 s (15 windows), inside the file</li>'
         f'<li>Exactly 2 change points → onset, offset; segments ≥ 2 windows</li>'
         f'<li>Middle segment kept only if its mean is above both neighbours; otherwise the detector’s boundaries stay</li>'
         f'<li>Bandwidth from the data: no penalty to tune</li><li>Localized events merged again at 90 s</li></ul></div>')
S["aC7"] = section("aC7", "Appendix C7 · Change Point Localizer",
    f'<div style="display:flex;flex-direction:row;gap:30px;align-items:center">{img("cpd_fig", "chb03 seizure: detector event from the smoothed score and the event after two change points on the unsmoothed score", 1080, 620)}{right}</div>', 43,
    sub="Change points place the boundaries; used as the detector they also fire when a high-amplitude state ends (0.213 vs 0.479, development)",
    cite="Arlot et al., 2012 · Truong et al., 2020 (ruptures) · Report Section 2.6.3, Eq. 11, Tables 7, 10")

# ---------------------------------------------------------------- D1 Scoring Rules and Statistics
rules = card("Event rules (SzCORE)", ["A detection is a true positive if it overlaps a seizure widened by 30 s before onset and 60 s after offset",
                                      "Events closer than 90 s are merged; events longer than 5 min are split",
                                      "Each recording scored on its own; counts summed per patient",
                                      "Specificity is undefined for events: false alarms per day replace it"], w=600, fs=27)
forms = (f'<div style="width:560px;display:flex;flex-direction:column;gap:14px;background:{PALE};border-top:5px solid {BLUE};padding:14px 18px">'
         f'<p style="font-size:26px;font-weight:700;color:{BLUE}">Metrics (Eq. 12)</p>'
         f'{img("eq_sens", "sensitivity", 344, 66)}{img("eq_prec", "precision", 319, 66)}{img("eq_f1", "F1", 295, 67)}{img("eq_fpday", "false alarms per day", 379, 70)}</div>')
ex = card("Worked example: held-out, seed 42", ["TP 26 · missed 50 · false alarms 257", "Non-seizure time 277.63 h",
                                               "FP/day = 257 / 277.63 × 24 = <b>22.2</b>", "Precision = 26 / 283 = <b>0.092</b>",
                                               "F1 = 52 / 359 = <b>0.145</b>", "Sensitivity = 26 / 76 = <b>0.342</b>"], fs=27, border=GREEN)
agg = (f'<div style="display:flex;flex-direction:row;gap:20px">'
       + card("Pooled", ["From the counts summed over all patients"], fs=26)
       + card("Per-patient mean", ["Mean of each patient’s value: the SzCORE official aggregate; one vote per patient"], fs=26)
       + card("4 seeds, mean ± SD", ["Spread from initialization only, not uncertainty"], fs=26)
       + card("Patient bootstrap 95 %", ["8 patients resampled with replacement, 10,000 times: uncertainty from having 8 patients"], fs=26)
       + card("Onset / offset error", ["Median absolute difference over matched seizure–seed pairs (4 seeds)"], fs=26)
       + "</div>")
S["aD1"] = section("aD1", "Appendix D1 · Scoring Rules and Statistics",
    f'<div style="display:flex;flex-direction:row;gap:20px">{rules}{forms}{ex}</div>{agg}', 44,
    sub="Every number is scored per event on the continuous recordings, and every metric comes from the scorer’s counts",
    cite="Dan et al., 2025 (SzCORE) · Ziyabari et al., 2019 · Efron, 1979 · Report Section 2.8, Eq. 12, Figure 9 · rules illustrated on main slide 14")

# ---------------------------------------------------------------- D3 Evaluation Timeline
def stage(n, name, data, rule, result, color):
    return (f'<div style="flex:1;display:flex;flex-direction:column;gap:8px;border:2px solid {color};border-radius:12px;padding:12px 14px">'
            f'<p style="font-family:{FH};font-size:28px;font-weight:600;color:{color}">{n} · {name}</p>'
            f'<p style="font-size:26px;line-height:1.3"><b>Data:</b> {data}</p>'
            f'<p style="font-size:26px;line-height:1.3"><b>Rule:</b> {rule}</p>'
            f'<p style="font-size:27px;line-height:1.3;color:{color}"><b>{result}</b></p></div>')

arr = f'<p style="width:30px;font-size:40px;color:{BLUE};padding:80px 0px 0px 0px">→</p>'
row = (f'<div style="display:flex;flex-direction:row;gap:6px;align-items:stretch">'
       + stage(1, "Development", "15 patients (12 training + 3 validation)", "every design choice, one rule: best pooled sensitivity at ≤ 25 false alarms per day",
               "0.670 at 23.3 (4 seeds); optimistic", MUTED) + arr
       + stage(2, "Held-out", "8 test patients, 76 seizures", "design fixed; one budget of 0.5 %; scored once, no change",
               "26 / 76 at 22.2 (seed 42): main estimate", BLUE) + arr
       + stage(3, "Final system", "the same 8 test patients", "+ per-patient budget, designed with test information",
               "37 / 76 at 27.5 (seed 42): test-informed", ORANGE) + arr
       + stage(4, "External", "chb24; Siena, 14 adults", "final system unchanged, scored once",
               "14 / 16 at 29.5 (seed 42); 0.633 at 41.0 (4 seeds)", GREEN) + arr
       + stage(5, "Application run", "8 test patients, frozen build, empty database", "label-free statistics; every event exported before review, scored outside the app",
               "33 / 76 at 27.9", GREEN) + "</div>")
side = (f'<div style="display:flex;flex-direction:row;gap:20px">'
        + card("Channel explanation", ["Method, prior and test order fixed before any comparison with the blind annotation of the 62 focal test seizures: AUROC 0.547 against a prior of 0.739"], fs=27)
        + card("Disclosure", ["Earlier versions of the system were also scored on the test patients during development, so the test set was not completely untouched; chb24, Siena and the application run are the independent evidence"], border=ORANGE, fs=27)
        + "</div>")
S["aD3"] = section("aD3", "Appendix D3 · Evaluation Timeline", row + side, 46,
    sub="Every design choice was made on the development patients; each later set was scored once, in this order",
    cite="Report Section 2.8.2–2.8.3, Table 11, 14, 17 · false alarms per day; pooled sensitivity unless marked")
