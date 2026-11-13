"""D4g appendix, groups A-D (new pages). Numbers: report tables / NUMBERS_LOCK; external facts: NL §15."""
from lib import *

S = {}
YES, NO = span("Yes", GREEN, True), span("No", RED, True)
PART = span("Partly", ORANGE, True)

# ---------------------------------------------------------------- A1 Dataset Selection
rows = [
    ["<b>CHB-MIT</b> (Shoeb, 2010)", "Scalp, 256 Hz; 23 cases from 22 children + chb24",
     f"{YES}: hours of continuous EEG per case", f"{YES}", f"{YES}: native 18 bipolar", "Development, held-out test; chb24 external"],
    ["<b>Siena</b> (Detti et al., 2020)", "Scalp, 512 Hz; 14 adults, another hospital",
     f"{YES}: 141.0 h in the files", f"{YES}: read with the SzCORE converter", f"{YES}: formed from referential", "External; public SzCORE benchmark"],
    ["<b>TUH Seizure Corpus</b> v1.2.0 (Shah et al., 2018)", "Scalp clinical EEG; 315 subjects, 822 sessions, 504 h",
     f"{PART}: about 37 min per session on average", f"{YES}: start and end of each event", f"{YES}: 19 channels, 10–20", "Not used: future work"],
    ["<b>Bonn</b> (Andrzejak et al., 2001)", "5 sets × 100 single-channel segments, 173.6 Hz",
     f"{NO}: 23.6 s segments", f"{NO}: one class per segment", f"{NO}: single channel; seizure set intracranial", "Not used"],
    ["<b>Helsinki neonatal</b> (Stevenson et al., 2019)", "Scalp, 256 Hz; 79 neonates, 3 expert annotators",
     f"{PART}: median 74 min", f"{YES}: 1 s resolution", f"{YES}: 18-derivation bipolar", "Not used: neonates, short recordings"],
]
body = table(["Dataset", "Recording", "Long, continuous", "Onset and offset", "18 bipolar derivations", "Role here"],
             rows, [16, 21, 17, 15, 15, 16], fs=27, hl=(0, 1))
body += (f'<p style="font-size:27px;color:{MUTED}">Criteria: scalp EEG of people with epilepsy, long continuous recordings scored per event, '
         f'onset and offset of every seizure, and the 10–20 electrodes needed for the 18 bipolar derivations. '
         f'TUH: 504 h / 822 sessions (computed).</p>')
S["aA1"] = section("aA1", "Appendix A1 · Dataset Selection", body, 29,
    sub="CHB-MIT and Siena are the public scalp corpora that combine long continuous recordings, onset and offset of every seizure and the 18-derivation montage",
    cite="Shoeb, 2010 · Detti et al., 2020 · Shah et al., 2018 · Andrzejak et al., 2001 · Stevenson et al., 2019 · EPFL SzCORE benchmark")

# ---------------------------------------------------------------- A2 CHB-MIT Recordings
sets = table(["Set", "Cases", "Hours", "Seizures"],
             [["Training", "12", "566.43", "93"], ["Validation", "3", "115.82", "13"],
              ["Test", "8", "279.39", "76"], ["External", "chb24", "21.3", "16"]], [34, 22, 24, 20], fs=24)
notes = (f'<p style="font-size:26px;line-height:1.3;color:{MUTED}">Hours and seizures as listed in the summary files. '
         f'Scored: 562.40 / 111.82 / 279.38 h. chb12_27–29 skipped (a derivation missing, 13 seizures); '
         f'chb11_12–15 and chb21_11 missing from the copy used (seizure-free, 0.7 % of development hours).</p>')
body = (f'<div style="display:flex;flex-direction:row;gap:30px;align-items:start">'
        f'{img("A2dur", "Seizure duration range and median for each of the 23 CHB-MIT cases, coloured by set", 1360, 634)}'
        f'<div style="flex:1;display:flex;flex-direction:column;gap:16px">{sets}{notes}</div></div>')
S["aA2"] = section("aA2", "Appendix A2 · CHB-MIT Recordings", body, 30,
    sub="23 cases from 22 children (chb21 is chb01 1.5 years later); test seizures last 6–205 s, and 23 of them are shorter than 20 s",
    cite="Shoeb, 2010 · Report Table 4, Table 19, Appendix A · figure: results/p3_seizure_burden/burden.txt (n = seizures listed; chb12: 27 scored)")

# ---------------------------------------------------------------- A3 Siena Recordings
sien = [("PN00", "3.24", "3.30", "−0.06", "5"), ("PN01", "13.49", "13.48", "0.00", "2"), ("PN03", "24.23", "12.53", "+11.69", "2"),
        ("PN05", "6.03", "5.98", "+0.05", "3"), ("PN06", "12.07", "12.03", "+0.04", "5"), ("PN07", "8.74", "8.72", "+0.02", "1"),
        ("PN09", "6.85", "6.83", "+0.01", "3"), ("PN10", "18.72", "16.70", "+2.02", "10"), ("PN11", "2.41", "2.42", "−0.01", "1"),
        ("PN12", "6.10", "4.10", "+2.00", "4"), ("PN13", "8.66", "8.65", "+0.01", "3"), ("PN14", "20.46", "23.47", "−3.00", "4"),
        ("PN16", "4.88", "5.05", "−0.17", "2"), ("PN17", "5.12", "5.13", "−0.01", "2"), ("<b>Total</b>", "<b>141.01</b>", "128.40", "+12.61", "<b>47</b>")]
t = table(["Patient", "Hours in EDF (scored)", "PhysioNet table", "Difference", "Seizures"], [list(r) for r in sien],
          [16, 27, 23, 18, 16], fs=23, hl=(2, 7, 9, 11), width=1000)
side = (f'<div style="flex:1;display:flex;flex-direction:column;gap:14px">'
        + card("Signal path", ["512 Hz → 256 Hz; referential → 18 bipolar derivations; notch 50 Hz",
                               "Seizure times read with the SzCORE converter, which corrects known annotation errors"])
        + card("Hours", ["False alarms per day use the 141.0 h actually in the files",
                         "PN03, PN10, PN12: the table is shorter than the files; their own seizure lists agree with the files",
                         "PN14: table and seizure list ≈ 3 h longer than its four files (20.46 h); all 4 seizures scored"], border=ORANGE)
        + card("Patients", ["14 adults: 8 men 25–71 y, 6 women 20–58 y (per-patient table; the paper reports 9 / 5)"])
        + "</div>")
S["aA3"] = section("aA3", "Appendix A3 · Siena Recordings",
    f'<div style="display:flex;flex-direction:row;gap:30px;align-items:start">{t}{side}</div>', 31,
    sub="The external adult set was scored on the 141.0 h actually in its EDF files; PhysioNet’s summary table lists 128.40 h",
    cite="Detti et al., 2020 · EPFL epilepsy2bids converter · Report Table 20, Appendix A.2")

# ---------------------------------------------------------------- A4 Patient Split
def chips(names, color, bg):
    return (f'<div style="display:flex;flex-direction:row;flex-wrap:wrap;gap:10px">'
            + "".join(f'<p style="font-size:30px;color:{color};background:{bg};border-radius:22px;padding:6px 18px">{n}</p>' for n in names)
            + "</div>")

def block(title, sub, names, color, bg, w):
    return (f'<div style="width:{w}px;display:flex;flex-direction:column;gap:10px;border:2px solid {color};border-radius:12px;padding:14px 18px">'
            f'<p style="font-size:34px;font-weight:700;color:{color}">{title}</p>'
            f'<p style="font-size:29px;color:{INK}">{sub}</p>{chips(names, color, bg)}</div>')

tr = ["chb01", "chb02", "chb04", "chb05", "chb07", "chb08", "chb09", "chb12", "chb19", "chb20", "chb21", "chb23"]
row1 = (f'<div style="display:flex;flex-direction:row;gap:24px">'
        + block("Training · 12 patients", "fit the autoencoder (seizure-free windows); 566.43 h, 93 seizures", tr, "#3E78B5", "#E3EEF8", 1060)
        + block("Validation · 3 patients", "monitor training; 115.82 h, 13 seizures", ["chb10", "chb11", "chb22"], "#B87600", "#FBEFD9", 756)
        + "</div>")
dev = (f'<p style="font-size:26px;color:{INK};background:#F2F5F9;border-left:6px solid {BLUE};padding:8px 16px">'
       f'<b>Development = training + validation (15 patients):</b> every design choice was made here, under one rule '
       f'(best pooled sensitivity at ≤ 25 false alarms per day).</p>')
row2 = (f'<div style="display:flex;flex-direction:row;gap:24px">'
        + block("Test · 8 patients", "held-out and final evaluation; 279.39 h, 76 seizures",
                ["chb03", "chb06", "chb13", "chb14", "chb15", "chb16", "chb17", "chb18"], BLUE, "#DCEBF8", 900)
        + block("External · scored once", "chb24: 21.3 h, 16 seizures · Siena: 14 adults, 141.0 h, 47 seizures",
                ["chb24", "PN00–PN17 (14)"], GREEN, "#E2F2EA", 916)
        + "</div>")
foot = (f'<p style="font-size:27px;color:{MUTED}">chb01 and chb21 are one child recorded 1.5 years apart: both in training. '
        f'chb24 was added to the archive after the original 23 cases.</p>')
S["aA4"] = section("aA4", "Appendix A4 · Patient Split", row1 + dev + row2 + foot, 32,
    sub="Patients were assigned once, before any training, so every recording of a test patient stays out of training and design",
    cite="Report Section 2.1.1, Table 4 · Ali et al., 2024 (split by patient)")

# ---------------------------------------------------------------- B1 Preprocessing and Graph Settings
rows = [
    ["Filter", "Band-pass 0.5–60 Hz, 4th-order Butterworth; notch 60 Hz (Siena 50 Hz), Q = 30; both zero-phase", "Fixed"],
    ["Window", "4 s, non-overlapping (1,024 samples at 256 Hz); windows without signal excluded", "Fixed"],
    ["Channel z-score", "Mean and SD from every 10th window", "Each patient. CHB-MIT evaluation: seizures and the 4 h after them excluded; external sets and application: whole recording"],
    ["High-amplitude flag", "Any sample above 5 SD; used only to select training windows (46 % of non-seizure training windows, about 90 % of seizure windows)", "Each patient"],
    ["Reference", "Common average reference per window, only before coupling", "Fixed"],
    ["Coupling", "A = 0.5 wPLI + 0.5 AEC over the 153 channel pairs", "Fixed"],
    ["Sparsification", "Strongest 20 % of pairs kept (30 edges), weights unchanged", "Fixed"],
    ["Node features", "30 = adjacency row 18 + relative band powers 5 + absolute features 7", "Fixed"],
    ["Feature scaling", "7 absolute features: training mean and SD, clip ±4, mapped to [0, 1]", "12 training patients"],
]
S["aB1"] = section("aB1", "Appendix B1 · Signal and Graph Settings",
    table(["Stage", "Setting", "Fitted on"], rows, [18, 52, 30], fs=27), 33,
    sub="Every setting before the autoencoder is fixed or estimated per patient without labels, except one disclosed z-score step",
    cite="Report Section 2.1.3, 2.3, Table 21 · the label-dependent z-score step is measured in Appendix E9 (33 vs 37 of 76)")

# ---------------------------------------------------------------- B2 Edges Calculation
def eqrow(name, k, w, h, text):
    return (f'<div style="display:flex;flex-direction:column;gap:4px;border-left:5px solid {BLUE};padding:4px 0px 4px 16px">'
            f'<p style="font-size:25px;font-weight:700;color:{BLUE}">{name}</p>{img(k, name, w, h)}'
            f'<p style="font-size:23px;line-height:1.25;color:{INK}">{text}</p></div>')

left = (f'<div style="width:800px;display:flex;flex-direction:column;gap:10px">'
        + eqrow("1 · Common average reference", "eq_car", 380, 102, "Applied to each window just before coupling; the reference changes estimated channel relations (Nunez et al., 1997)")
        + eqrow("2 · Weighted phase lag index (Eq. 1)", "eq_wpli", 336, 77, "Consistent phase delay from the imaginary cross-spectrum over the bins of the window; zero-lag coupling from one shared source is ignored")
        + eqrow("3 · Amplitude envelope correlation (Eq. 2)", "eq_aec", 470, 60, "Do the Hilbert envelopes of two channels rise and fall together; not protected against shared sources")
        + eqrow("4 · Combine and sparsify", "eq_adj", 400, 58, "153 pairs per window; keep the strongest 20 % (30 edges) with their weights")
        + "</div>")
right = (f'<div style="flex:1;display:flex;flex-direction:column;gap:6px">{img("fig7_cd", "Report Figure 7c-d: combined wPLI plus AEC matrix and the sparse graph of one chb11 window", 1060, 394)}'
         f'<p style="font-size:22px;font-style:italic;color:{MUTED}">Report Figure 7 (c) combined adjacency and (d) graph after sparsification, one 4 s window of chb11</p></div>')
S["aB2"] = section("aB2", "Appendix B2 · Edges Calculation",
    f'<div style="display:flex;flex-direction:row;gap:30px;align-items:start">{left}{right}</div>', 34,
    sub="Each 4 s window becomes an 18-node graph whose edges average phase-lag and envelope coupling, keeping the strongest 30 of 153 pairs",
    cite="Vinck et al., 2011 · Bruns et al., 2000 · Nunez et al., 1997 · Report Section 2.3.1, Eq. 1–2, Figure 7")

# ---------------------------------------------------------------- B3 Node Features Calculation
def fblock(title, n, eqs, lines, color):
    inner = "".join(img(k, title, w, h) for k, w, h in eqs)
    return (f'<div style="flex:1;display:flex;flex-direction:column;gap:10px;background:{PALE};border-top:6px solid {color};padding:14px 18px">'
            f'<p style="font-size:28px;font-weight:700;color:{color}">{title} · {n}</p>{inner}'
            + "".join(f'<p style="font-size:26px;line-height:1.3">{l}</p>' for l in lines) + "</div>")

blocks = (f'<div style="display:flex;flex-direction:row;gap:20px">'
          + fblock("Adjacency row", 18, [("eq_row", 424, 68)],
                   ["How channel c couples to every other channel", "Divided by the largest edge weight of the window"], BLUE)
          + fblock("Relative band powers", 5, [("eq_bp", 391, 77)],
                   ["Welch spectrum, 2 s segments, 50 % overlap; δ 0.5–4, θ 4–8, α 8–13, β 13–30, γ 30–60 Hz",
                    "The 90 values of a window z-scored together, then scaled per band to [0, 1] across the 18 channels: how power is spread, not how large"], BLUE)
          + fblock("Absolute features", 7, [("eq_ll", 434, 63), ("eq_kurt", 351, 50)],
                   ["5 log band powers of Eq. 3 without rescaling, log line length, signed-log excess kurtosis",
                    "Training mean and SD, clip ±4, mapped to [0, 1]; they restore amplitude and waveform (development 0.330 → 0.489)"], ORANGE)
          + "</div>")
bottom = (f'<div style="display:flex;flex-direction:row;align-items:center;gap:24px">'
          f'{img("fig7_b", "Report Figure 7b: log band power per channel of one chb11 window", 330, 263)}'
          f'<p style="flex:1;font-size:26px;line-height:1.35">Node feature matrix <b>X = [18 | 5 | 7]</b>, size 18 × 30, one row per channel. '
          f'The two relative blocks hide the rise in amplitude and the change in waveform that a reader notices first; '
          f'the absolute block brings them back. The decoder rebuilds the 12 features of blocks 2 and 3.</p></div>')
S["aB3"] = section("aB3", "Appendix B3 · Node Features Calculation", blocks + bottom, 35,
    sub="Each node carries 30 numbers: how the channel couples, how its power is spread, and how large and sharp its signal is",
    cite="Welch, 1967 · Tang et al., 2022 (feature standardization) · Report Section 2.3.2, Eq. 3, Figure 7b")

# ---------------------------------------------------------------- B4 Sparsification Decision
rows = [["Density across patients and states", "0.921 to 0.973; varies by patient and state", "0.196 in both states for every patient (chb17 non-seizure 0.224)"],
        ["Effect on message passing", "Graph almost complete: averaging over neighbours approaches a global mean", "Sparse neighbourhoods keep topological structure"],
        ["Free parameter", "An absolute threshold with no patient-independent value", "A proportion that transfers unchanged between patients"],
        ["Separation of seizure and background connectivity (measured afterwards)", "Reference", "Higher on 8 of 8 test patients: relative Frobenius +48 % to +196 %, cosine +545 % to +903 %"],
        ["<b>Adopted</b>", "", span("<b>Strongest 20 % of edges</b>", GREEN)]]
S["aB4"] = section("aB4", "Appendix B4 · Sparsification Decision",
    table(["Criterion", "Fixed weight threshold", "Strongest 20 % of edges"], rows, [30, 33, 37], fs=28), 36,
    sub="Keeping a fixed share of edges gives every patient the same graph density and a larger seizure–background difference",
    cite="ElGazzar et al., 2022 · Li et al., 2026 · Report Table 5, Section 3.1, Figure 11 (main slide 15)")
