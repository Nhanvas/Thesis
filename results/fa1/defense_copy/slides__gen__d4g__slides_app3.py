"""D4g appendix, groups E-I (new pages) + G1 replacing Canva page 44."""
from lib import *

S = {}

# ---------------------------------------------------------------- E1 Development Components (Table 9)
rows = [["Three-readout ensemble, earlier node features (seed 42 only)", "0.330", "23.7", "—"],
        ["+ amplitude-preserving node features", "0.489", "20.1", "—"],
        ["Graph-level latent distance alone (two seeds)", "0.553", "23.8", "—"],
        ["Channel-level latent anomaly, 9th largest of 18", "0.612", "24.6", "0.742"],
        ["+ baseline drift correction", "0.681", "24.3", "0.821"],
        ["+ ensemble of four spatial scales", "0.668", "20.0", "0.828"],
        ["+ per-patient alarm budget", "0.678", "23.8", "0.842"],
        ["<b>+ kernel change point localizer (final system)</b>", "<b>0.670</b>", "<b>23.3</b>", "<b>0.832</b>"]]
t = table(["Configuration (15 development patients)", "Pooled sensitivity", "False alarms per day", "Per-patient mean sensitivity"],
          rows, [55, 15, 15, 15], fs=31, hl=(7,))
note = (f'<p style="font-size:26px;color:{MUTED}">Mean over four seeds unless marked; best operating point at ≤ 25 false alarms per day. '
        f'The four-scale ensemble kept sensitivity, removed about four false alarms per day and caught 2.0 of the 3 short development seizures (1.5 for one member). '
        f'Development is optimistic: the held-out test reached about half (0.336 vs 0.662, 4 seeds).</p>')
S["aE1"] = section("aE1", "Appendix E1 · Development Components", t + note, 48,
    sub="Without any seizure label, the components raised pooled sensitivity on the development patients from 0.330 to 0.670",
    cite="Report Table 9, Section 3.2.1, 4.1 · figure version: main slide 16")

# ---------------------------------------------------------------- E3 Test per Patient and Seed (Tables 12, 22)
rows = [["chb03", "7", "7 / 7 / 6 / 7", "22", "13.9", "0.0052", "7 / 7 / 6 / 7", "22", "13.9"],
        ["chb06", "10", "2 / 1 / 1 / 2", "90", "32.4", "0.005", "2 / 1 / 1 / 2", "90", "32.4"],
        ["chb13", "12", "1 / 2 / 2 / 2", "40", "29.2", "0.005", "1 / 2 / 2 / 2", "40", "29.2"],
        ["chb14", "8", "6 / 5 / 6 / 5", "27", "25.0", "0.0065", "6 / 5 / 6 / 6", "34", "31.5"],
        ["chb15", "20", "0 / 0 / 0 / 0", "14", "8.5", "<b>0.02</b>", "<b>11 / 11 / 9 / 11</b>", "53", "32.3"],
        ["chb16", "10", "2 / 2 / 2 / 2", "16", "20.2", "0.005", "2 / 2 / 2 / 2", "16", "20.2"],
        ["chb17", "3", "3 / 3 / 3 / 3", "25", "29.5", "0.005", "3 / 3 / 3 / 3", "25", "29.5"],
        ["chb18", "6", "5 / 5 / 5 / 5", "23", "15.5", "0.0082", "5 / 5 / 5 / 5", "38", "25.7"],
        ["<b>Total</b>", "<b>76</b>", "<b>26</b> (seed 42)", "<b>257</b>", "<b>22.2</b>", "", "<b>37</b> (seed 42)", "<b>318</b>", "<b>27.5</b>"]]
t = table(["Patient", "Seizures", "Held-out detected, seeds 42 / 1 / 2 / 3", "Held-out false alarms", "Held-out FA/day",
           "Final budget", "Final detected, seeds 42 / 1 / 2 / 3", "Final false alarms", "Final FA/day"],
          rows, [8, 8, 16, 10, 9, 9, 16, 12, 12], fs=28, hl=(4,))
note = (f'<p style="font-size:26px;color:{MUTED}">False alarms and FA/day: seed 42, after the localizer. Four seeds, pooled sensitivity: held-out 0.336 ± 0.008, '
        f'final 0.477 ± 0.022. Only chb15 reached the 2 % cap; chb14 and chb18 got larger budgets that added false alarms but no seizure (seed 42).</p>')
S["aE3"] = section("aE3", "Appendix E3 · Test Patients per Seed", t + note, 50,
    sub="Seeds change a patient’s held-out count by at most one seizure; with seed 42, chb15 is the only patient whose detections changed in the final system",
    cite="Report Tables 11, 12, 22 · results/e22_test_oneshot, results/e23_test_look7")

# ---------------------------------------------------------------- E6 Detection Gallery (Fig. 14)
S["aE6"] = section("aE6", "Appendix E6 · Detection Gallery",
    f'<div style="display:flex;flex-direction:row;justify-content:center">{img("fig14", "Report Figure 14: (a) chb03 detected, (b) chb15 detected with the per-patient budget, (c) chb16 short seizure missed, (d) chb03 false alarm", 1840, 584)}</div>'
    f'<p style="font-size:26px;line-height:1.35">Panels chosen by fixed rules before drawing: (a) first seizure of chb03; (b) first chb15 seizure found by the final system '
    f'but not the held-out evaluation (40 windows); (c) shortest missed seizure of chb16 (two windows); (d) highest-scoring false alarm more than '
    f'10 min from any seizure, 132 s of sustained high-amplitude activity whose cause the figure alone cannot show.</p>', 53,
    sub="Detected seizures rise above the patient’s threshold; misses are short or sit inside the patient’s own activity",
    cite="Report Section 3.3.5, Figure 14 · final system, seed 42 · left: EEG 30 s around onset; right: score ±5 min")

# ---------------------------------------------------------------- E10 Siena per Patient and Seed (Tables 15, 23)
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
side = (f'<div style="flex:1;display:flex;flex-direction:column;gap:14px">'
        + card("Siena, four seeds", ["Per-patient mean sensitivity 0.633 ± 0.079 at 41.0 false alarms per day; precision 0.160, F1 0.226",
                                     "Patient bootstrap: [0.477, 0.777]; FA/day [32.3, 53.9]"])
        + card("chb24 (child, never used)", ["Seeds 42 / 1 / 2 / 3: 14 / 13 / 12 / 14 of 16 detected, with 26 / 23 / 26 / 25 false alarms"], border=GREEN)
        + card("Where false alarms sit", ["Rows shaded: budget above 1.7 %; these seven patients hold 197 of 257 false alarms",
                                          "Short recordings inflate the daily rate: PN11 has 3 false alarms in 2.41 h = 30.1 per day"], border=ORANGE)
        + "</div>")
S["aE10"] = section("aE10", "Appendix E10 · Siena per Patient and Seed",
    f'<div style="display:flex;flex-direction:row;gap:26px;align-items:start">{t}{side}</div>', 57,
    sub="Ten of 14 adults had at least two thirds of their seizures found; false alarms concentrate in the patients with large label-free budgets",
    cite="Report Tables 14, 15, 23, Section 3.4 · FA, FA/day and budget: seed 42, after the localizer · results/x1_external")

# ---------------------------------------------------------------- F1 Annotation Protocol
cards = (f'<div style="display:flex;flex-direction:row;gap:16px">'
         + card("What was marked", ["Every channel with a clear ictal discharge (rhythmic evolution, sharp-and-slow, evolving low-voltage fast) at any time in the seizure; attenuation alone, artifact or a single transient not counted"], fs=23)
         + card("Blind", ["Read from the raw 18-channel EEG in a fixed bipolar display, without viewing any model output (no score, rank or heat map)"], fs=23)
         + card("Approved", ["Protocol and annotation reviewed and approved by the supervisor before any comparison; the source file is kept unedited with its SHA-256"], fs=23, border=GREEN)
         + card("Result", ["62 focal seizures: 1–10 channels, mean 4.55, 282 labels", "14 generalized (all 18 channels): chb06 10, chb03 3, chb13 1"], fs=23)
         + "</div>")
S["aF1"] = section("aF1", "Appendix F1 · Annotation Protocol",
    cards + f'<div style="display:flex;flex-direction:row;justify-content:center">{img("F1map", "Channel annotation of the 76 test seizures: 18 channels by 76 seizures, grouped by patient", 1290, 532)}</div>', 61,
    sub="CHB-MIT has no channel labels, so every channel of the 76 test seizures was annotated blind to the model and approved before any comparison",
    cite="Report Section 2.7, Appendix D · map drawn from results/attribution_v7/labels/ictal_channels_FINAL.csv (one reader: agreement, not accuracy)")

# ---------------------------------------------------------------- F3 Attribution Method and Tests
def box(t, w):
    return f'<p style="width:{w}px;font-size:27px;line-height:1.3;background:{PALE};border:2px solid {BLUE};border-radius:10px;padding:10px 14px">{t}</p>'
ar = f'<p style="width:36px;font-size:40px;color:{BLUE}">→</p>'
flow = (f'<div style="display:flex;flex-direction:row;align-items:center;gap:6px">'
        + box("<b>Channel-level latent anomaly</b> rc(t), Eq. 7", 350) + ar
        + box("<b>Per seizure:</b> 95th percentile of |rc(t)| over its windows", 330) + ar
        + box("<b>Rank</b> the 18 channels", 210) + ar
        + box("<b>AUROC</b> of the ranking against the blind annotation", 330) + ar
        + box("<b>Mean</b> over the 62 focal seizures", 300) + "</div>")
rows = [["1 · Chance", "Does the ranking beat a random one?", "Scores permuted across channels within each seizure, 1,000 times", "0.547 [0.499, 0.597], p = 0.018", span("Above chance, weakly", ORANGE, True)],
        ["2 · Anatomical prior", "Is it better than a rule that ignores the EEG?", "Prior: how often each channel is annotated in the other 7 patients; paired bootstrap over seizures", "0.547 − 0.739 = −0.191 [−0.262, −0.118]", span("Below the prior", RED, True)],
        ["3 · Seizure-specific", "Does a seizure’s ranking fit its own annotation better than its sibling seizures’ rankings?", "Matched minus swapped, within each patient; permutation, 1,000 times", "−0.002, p = 0.53", span("No", RED, True)]]
t = table(["Test (fixed order)", "Question", "Method", "Result, seed 42", "Reading"], rows, [14, 24, 28, 19, 15], fs=27)
note = (f'<p style="font-size:26px;color:{MUTED}">Method, prior and test order fixed before any comparison; tests 2–3 Holm-corrected; '
        f'the 14 generalized seizures excluded because AUROC is undefined when all 18 channels are positive. Reading: the channel panel shows the model’s anomaly, not an onset map.</p>')
S["aF3"] = section("aF3", "Appendix F3 · Attribution Method and Tests", flow + t + note, 63,
    sub="The channel ranking was tested in a fixed order against chance, an anatomical prior and the patient’s other seizures",
    cite="Craley et al., 2022 (focal-only scoring) · Zhang et al., 2018 (input-blind baseline) · Report Sections 2.7, 3.5 · results/attribution_v8/attribution_tests.csv")

# ---------------------------------------------------------------- F4 Attribution per Patient (Table 24)
rows = [["chb03", "4", "0.404 [0.319, 0.529]", "0.93", "0.903"], ["chb06", "0", "— (all ten generalized)", "—", "—"],
        ["chb13", "11", "0.508 [0.428, 0.585]", "0.45", "0.753"], ["chb14", "8", "0.555 [0.445, 0.672]", "0.14", "0.807"],
        ["chb15", "20", "<b>0.675 [0.602, 0.754]</b>", "<b>0.001</b>", "0.576"], ["chb16", "10", "0.487 [0.363, 0.611]", "0.59", "0.846"],
        ["chb17", "3", "0.418 [0.268, 0.646]", "0.79", "0.831"], ["chb18", "6", "0.444 [0.359, 0.518]", "0.81", "0.831"],
        ["<b>All</b>", "<b>62</b>", "<b>0.547 [0.499, 0.597]</b>", "<b>0.018</b>", "<b>0.739</b>"]]
t = table(["Patient", "Focal seizures", "Mean AUROC [95 % CI]", "p vs chance", "Anatomical prior"], rows, [16, 18, 32, 16, 18], fs=27, hl=(4,), width=1180)
side = (f'<div style="flex:1;display:flex;flex-direction:column;gap:14px">'
        + card("Robustness", ["Seeds 1 / 2 / 3: 0.543 / 0.588 / 0.545", "Without chb15: 0.486 (42 seizures), at chance"])
        + card("Earlier reconstruction readout", ["0.569, without chb15 0.501: the same pattern (experiment record)"], border=MUTED)
        + card("Why the prior is strong", ["Frontopolar derivations carry 116 of 282 labels (41 %); five channels are never annotated"], border=ORANGE)
        + "</div>")
S["aF4"] = section("aF4", "Appendix F4 · Attribution per Patient",
    f'<div style="display:flex;flex-direction:row;gap:26px;align-items:start">{t}{side}</div>', 64,
    sub="Only chb15 lies above chance and above its anatomical prior; without it the agreement falls to chance",
    cite="Report Table 24, Section 4.4, Appendix D · seed 42; bootstrap over seizures · results/attribution_v8, results/attribution_v7 (earlier readout)")

# ---------------------------------------------------------------- G1 Architecture without Labels (replaces Canva p44)
side = (f'<div style="flex:1;display:flex;flex-direction:column;gap:16px">'
        + card("15 automated tests passed", ["4 guards: no annotation timeline, no seizure fields of the summary files, no label-split arrays, no writing outside the app folder",
                                             "7 final-system equivalence · 4 file matching"])
        + card("Identity on chb03", ["Thesis statistics: 7 / 7 seizures, 22 false alarms, same budget 0.005175, score difference ≤ 7.31 × 10⁻⁶",
                                     "Label-free statistics (used in practice): 6 / 7, 20 false alarms"], border=GREEN)
        + card("The one difference", ["The app estimates the z-score statistics from every 10th window of the whole recording, as for the external sets"], border=ORANGE)
        + "</div>")
S["aG1"] = section("aG1", "Appendix G1 · Application without Labels",
    f'<div style="display:flex;flex-direction:row;gap:30px;align-items:start">{img("fig10", "Report Figure 10: browser, application server, scoring and storage layers; annotations, rebuilt timelines and label-split arrays are never read at run time", 1090, 761)}{side}</div>', 65,
    sub="The application never reads a label: automated tests guard every label path, and on chb03 it reproduces the thesis system",
    cite="Report Section 2.9.2, Figure 10, Section 3.6, Appendix E · server code imports no network library")

# ---------------------------------------------------------------- G2 Review Screens (Fig. 15)
side = (f'<div style="flex:1;display:flex;flex-direction:column;gap:16px">'
        + card("(a) Recordings", ["Import the recordings of a patient or open one already processed"])
        + card("(b) Review", ["Score timeline of each file with its events; the EEG around the onset and offset of the selected event",
                              "Panel “Channel-level latent anomaly — Event N”: the model’s output, not an onset map"])
        + card("(c) Decision", ["Accept, reject or mark uncertain, with a comment", "No evaluation metric and no threshold in the product"], border=GREEN)
        + "</div>")
S["aG2"] = section("aG2", "Appendix G2 · Review Screens",
    f'<div style="display:flex;flex-direction:row;gap:30px;align-items:start">{img("fig15", "Report Figure 15: review application screens a, b, c", 1180, 794)}{side}</div>', 66,
    sub="The reviewer starts from the event list, checks the EEG around each event and records a decision",
    cite="Report Section 3.6, Figure 15 · chb03, event 1")

# ---------------------------------------------------------------- H1 Earlier and Final System
rows = [["Node features", "Adjacency row + relative band powers (23)", "+ 7 absolute features (30)", "Relative features erase amplitude and waveform: 0.330 → 0.489"],
        ["Readout", "Reconstruction error + graph-level latent + gamma coupling, equal weights", "Channel-level latent, four spatial scales, drift-corrected",
         "Reconstruction near chance against high-amplitude windows (0.527–0.534 vs 0.966); gamma drifts between files; channel 0.622 vs graph 0.553"],
        ["Detector", "Change points on the whole score (penalized segmentation)", "Threshold with a per-patient budget + kernel change point localizer",
         "Segmentation also fires when a high state ends: 0.213 vs 0.479"],
        ["Evaluation", "Timeline rebuilt from the annotations: 0.618 at 27.4", "Continuous recordings, every window in time order",
         "The rebuilt timeline removed the windows that cause most false alarms"],
        ["<b>Continuous test result</b>", "<b>23 / 76 (0.303) at 73.3</b>", "<b>Held-out 26 / 76 (0.342) at 22.2; final 37 / 76 at 27.5</b> (seed 42)", "8 test patients, 76 seizures, false alarms per day"]]
S["aH1"] = section("aH1", "Appendix H1 · Earlier and Final System",
    table(["Stage", "Earlier system", "Final system", "Why it changed (measured, development unless marked)"], rows, [14, 26, 27, 33], fs=29, hl=(4,)), 69,
    sub="Each change from the earlier system answered a measured failure; on the continuous recordings it cut false alarms from 73.3 to 22.2 per day",
    cite="Report Sections 2.8.2, 3.2, 4.2, Tables 9, 10 · development: pooled sensitivity at ≤ 25 false alarms per day")

# ---------------------------------------------------------------- H2 Models Evaluated
X = span("experiment record", MUTED)
rows = [["Feature density, normal from other patients", "Node features; other patients’ seizure-free EEG", "0.340", "Not adopted: the patient’s own high-amplitude activity lies outside other patients’ normal"],
        ["Feature density, patient’s own recording", "Node features; the patient’s whole recording", "0.596", "Not adopted: below the channel-level latent with the same reference (0.612)"],
        ["Artifact model on the high-amplitude flag", "Flagged windows treated as artifact", "0.096", "Not adopted: called 81.5 % of seizure windows artifact; the flag marks amplitude"],
        ["GAE reconstruction error", "Decoder output vs input", "AUROC 0.527–0.534", "Dropped: does not separate seizures from high-amplitude windows (latent 0.966)"],
        ["GAE graph-level latent", "Mahalanobis distance of the mean of 18 latent vectors", "0.553 (2 seeds)", "Replaced: channel-level reading 0.622 (same seeds)"],
        ["GAE fine-tuned per patient", "Unsupervised, on the patient’s own windows", "0.628 vs 0.622 (2 seeds)", "Not adopted: seizure scores rose, non-seizure scores did not fall"],
        [f"Multi-relational GAE, directed coupling ({X})", "+ transfer-entropy graph, earlier system", "Window AUROC 0.926 vs 0.928 (validation)", "Not adopted: a tie within the spread between seeds"],
        [f"Temporal LSTM branch ({X})", "Sequence of windows, earlier system", "—", "Removed: the system without it detected as well as with it"],
        ["Supervised gradient-boosted trees", "Seizure labels of the other development patients, leave one out", "0.702 at 20.5", "Reference only: labels are excluded by the registered aim"],
        ["<b>Final: GAE channel-level latent</b>", "Own-recording reference, drift, 4 scales, budget, localizer", "<b>0.670 at 23.3</b>", span("<b>Adopted</b>", GREEN)]]
S["aH2"] = section("aH2", "Appendix H2 · Models Evaluated",
    table(["Model", "Input and reference", "Development result", "Decision and reason"], rows, [25, 26, 17, 32], fs=23, hl=(9,)), 70,
    sub="Every alternative was scored under the same rule on the development patients and kept or dropped for a measured reason",
    cite="Report Tables 6, 10, Section 4.1–4.2 · rows marked experiment record: not in the report (record of the earlier system) · pooled sensitivity at ≤ 25 false alarms per day")

