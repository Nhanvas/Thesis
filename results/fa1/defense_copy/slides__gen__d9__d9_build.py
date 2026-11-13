"""D9 deck build: rewrites the changed slides of the Slides artifact and renumbers every page to the D9 page map.
Numbers on the slides come only from NUMBERS_LOCK §1–§17 (checked by d9_numcheck.py).
Usage: python -I d9_build.py <artifact_root>   (folder holding project/)
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(sys.argv[1])
SL = ROOT / "project/slides"

# ------------------------------------------------------------------ assets
B = {
    "model": "/_blob/b74f4e4f17f65bf292e4f6d3b17be8b5",
    "siena": "/_blob/72eeee3abcc591b4dae3f03c7ca6ef42",
    "hard": "/_blob/b76825005c7727c1658fa31a2acba7ad",
    "five": "/_blob/1c6a3f5a87644c35471994b1856b4daa",
    "knn24": "/_blob/b8aad6d1173d83c0059bd144d66f07a5",
    "devpath": "/_blob/31a79c16c6da8e48ab375029ae717aa0",
    "szscan": "/_blob/aa5d917ecfbf9ea42320706ba86cd705",
    "graphs": "/_blob/5079cb82eb2e21e52a72055cc53f4e61",
    "fig11": "/_blob/9d5d05b7fa3525e047168180bbfe4569",
    "fig12": "/_blob/deada7127c16ddd84bf83caad950577d",
    "siena_pp": "/_blob/65fc079c5f9be055ab5511e75ec4b552",
}
RED, BLUE, ORANGE, GREEN, GREY, INK = "#DC433A", "#1F6FB2", "#C8641E", "#1B7F5B", "#5F6B7A", "#1E2430"

# ------------------------------------------------------------------ page map (Canva numbering)
ORDER_MAIN = ["s01", "s02", "s03", "s04", "s05", "s06", "s07", "s08", "s09", "s10", "s11", "s12", "s13", "s14",
              "s21", "s17", "s18", "s16", "s15", "s19", "s24", "s20", "s22", "s25b", "s23", "s25", "s26", "s27"]
PAGE = {sid: i + 1 for i, sid in enumerate(ORDER_MAIN)}
PAGE["s26"] = 27   # References 27–28 in Canva (one page here)
PAGE["s27"] = 29   # Thank you
APP = ["aA1", "aA2", "aB1", "aB2", "aB3", "aB4", "aB5", "aC1", "aC2", "aC3", "aC4", "aC5", "aC6", "aC7",
       "aD1", "aD2", "aD3", "aD4", "aE1", "aE2", "aE3", "aE4", "aE5", "aE6", "aE7", "aE8", "aE9", "aE10",
       "aF1", "aF2", "aF3", "aG1", "aG2", "aG3", "aH1", "aH2"] + [f"aI{i}" for i in range(1, 14)]
for i, sid in enumerate(APP):
    PAGE[sid] = 30 + i
ORDER = ORDER_MAIN + APP + ["aH3"]   # aH3 is not in the Canva deck (kept last, unnumbered change)

SECTION_OF = {}
for sid in ["s03", "s04", "s05", "s06"]:
    SECTION_OF[sid] = "Introduction"
for sid in ["s07", "s08", "s09", "s10", "s11", "s12", "s13", "s14", "s21"]:
    SECTION_OF[sid] = "Methodology"
for sid in ["s17", "s18", "s16", "s15", "s19", "s24", "s20"]:
    SECTION_OF[sid] = "Results"
for sid in ["s22", "s25b", "s23"]:
    SECTION_OF[sid] = "Discussion"
SECTION_OF["s25"] = "Conclusion"

PILLS = [("Introduction", 40, 214), ("Methodology", 268, 206), ("Results", 498, 124), ("Discussion", 646, 170),
         ("Conclusion", 840, 170)]
FOOT = '<div style="position:absolute;left:0;bottom:0;width:1920px;height:89px;background:linear-gradient(90deg, #D8E6F3 0%, #8DB6DD 40%, #2C67AE 100%)"></div>'


def pills(active):
    out = []
    for name, left, w in PILLS:
        on = name == active
        extra = "color:#FFFFFF;background:#1F6FB2;border-radius:28px" if on else f"color:{INK}"
        out.append(f'<p style="position:absolute;left:{left}px;bottom:16px;width:{w}px;height:56px;font-family:\'Cabin\', Arial, sans-serif;font-size:32px;line-height:1.6;text-align:center;{extra}">{name}</p>')
    return "\n".join(out)


def num(n):
    return f'<p style="position:absolute;right:40px;bottom:22px;width:90px;font-family:\'Cabin\', Arial, sans-serif;font-size:32px;font-weight:700;color:#FFFFFF;text-align:right">{n}</p>'


def h2(t):
    return f'<h2 style="font-family:\'Cabin\', Arial, sans-serif;font-size:53px;font-weight:700;line-height:1.15;color:#1F6FB2">{t}</h2>'


def take(html):
    return f'<p style="font-size:33px;line-height:1.3;color:#000000"><b>{html}</b></p>'


def arrow(html, size=33):
    return f'<p style="font-size:{size}px;line-height:1.3"><b><span style="color:{RED}">→ {html}</span></b></p>'


def cite(t):
    return f'<p style="position:absolute;left:40px;bottom:96px;width:1840px;font-size:22px;font-style:italic;color:{GREY}">{t}</p>'


def r(t):
    return f'<b><span style="color:{RED}">{t}</span></b>'


def img(src, alt, w, h, cap=None, capsize=25):
    s = f'<div style="display:flex;flex-direction:column;align-items:center;gap:6px"><img src="{src}" alt="{alt}" style="width:{w}px;height:{h}px;object-fit:contain">'
    if cap:
        s += f'<p style="width:{w}px;font-size:{capsize}px;font-style:italic;color:{INK};text-align:center">{cap}</p>'
    return s + "</div>"


def hole(w, h, what, cap=None, capsize=25):
    """Placeholder for a real-EEG figure the author inserts in Canva."""
    s = (f'<div style="display:flex;flex-direction:column;align-items:center;gap:6px"><div style="width:{w}px;height:{h}px;'
         f'display:flex;flex-direction:column;justify-content:center;align-items:center;background:#FFF8F0;border:3px dashed {ORANGE};border-radius:10px;padding:16px">'
         f'<p style="font-size:28px;line-height:1.3;color:{ORANGE};text-align:center"><b>Insert in Canva</b></p>'
         f'<p style="font-size:26px;line-height:1.3;color:{INK};text-align:center">{what}</p></div>')
    if cap:
        s += f'<p style="width:{w}px;font-size:{capsize}px;font-style:italic;color:{INK};text-align:center">{cap}</p>'
    return s + "</div>"


def ul(items, size=30, lh=1.35):
    return f'<ul style="font-size:{size}px;line-height:{lh}">' + "".join(f"<li>{i}</li>" for i in items) + "</ul>"


def table(rows, widths, size=27, hl=()):
    out = [f'<table style="font-size:{size}px;line-height:1.22;color:{INK}">']
    out.append('<tr style="background:#E9EEF4">' + "".join(f'<th style="width:{w}%">{c}</th>' for c, w in zip(rows[0], widths)) + "</tr>")
    for i, row in enumerate(rows[1:], 1):
        bg = ' style="background:#DCEBF8"' if i in hl else ""
        out.append(f"<tr{bg}>" + "".join(f"<td>{c}</td>" for c in row) + "</tr>")
    return "\n".join(out) + "\n</table>"


def main_slide(sid, title, body, gap=12, notes=None):
    page = PAGE[sid]
    s = (f'<section id="{sid}" data-transition="fade" style="background:#FFFFFF;color:{INK};font-family:\'Carlito\', Arial, sans-serif;'
         f'padding:26px 40px 116px;display:flex;flex-direction:column;gap:{gap}px">\n{FOOT}\n{pills(SECTION_OF[sid])}\n{num(page)}\n{h2(title)}\n{body}')
    if notes:
        s += f"\n<aside>{notes}</aside>"
    return s + "\n</section>\n"


def app_slide(sid, title, sub, body, gap=14, notes=None):
    s = (f'<section id="{sid}" data-transition="fade" style="background:#FFFFFF;color:{INK};font-family:\'Carlito\', Arial, sans-serif;'
         f'padding:26px 40px 116px;display:flex;flex-direction:column;gap:{gap}px">\n{FOOT}\n{num(PAGE[sid])}\n{h2(title)}\n'
         f'<p style="font-size:30px;line-height:1.3;color:#000000">{sub}</p>\n{body}')
    if notes:
        s += f"\n<aside>{notes}</aside>"
    return s + "\n</section>\n"


AFTER = f'<span style="color:{GREY}">(after the review)</span>'
SLIDES = {}

# ------------------------------------------------------------------ p15 · Review Application (tool, Method)
old = (SL / "s21.html").read_text(encoding="utf-8")
diagram = old.split('<div style="display:flex;flex-direction:row;gap:30px;align-items:start">', 1)[1]
diagram = diagram.split('<div style="flex:1;display:flex;flex-direction:column;gap:14px"><img', 1)[0]
SLIDES["s21"] = main_slide(
    "s21", "Review Application",
    take(f"The whole system runs {r('label-free')} on one hospital workstation; the reader {r('reviews each event')}") + "\n"
    + '<div style="display:flex;flex-direction:row;gap:30px;align-items:start">' + diagram
    + '<div style="flex:1;display:flex;flex-direction:column;gap:12px">'
    + img(B["szscan"], "SzScan review screen: score timeline, EEG around an event, channel panel", 790, 494,
          "SzScan review screen: score timeline, EEG around each event, channel panel")
    + ul(["Upload EDF → events with onset and offset", "Accept / Reject / Uncertain per event", "No metric and no threshold shown to the reader"], 29)
    + "</div></div>",
    notes="Method slide: the tool only, no result numbers (results on page 21). The live demo comes after the Conclusion (page 26); fallback video in Appendix G3. Logos: Simple Icons (CC0).")

# ------------------------------------------------------------------ p16 · Test Patients (precision and F1 back, A41)
s17 = (SL / "s17.html").read_text(encoding="utf-8")
s17 = s17.replace('<tr><td>False alarms/day</td>',
                  '<tr><td>Precision</td><td>0.092 / 0.108</td><td>0.104 / 0.118</td></tr>\n<tr><td>F1 score</td><td>0.145 / 0.174</td><td>0.172 / 0.190</td></tr>\n<tr><td>False alarms/day</td>')
s17 = s17.replace('<p style="font-size:26px;line-height:1.3;font-style:italic;color:#5F6B7A">Precision and F1: Appendix E4</p>', "")
s17 = s17.replace("Figure 7: 8 test patients", "Figure 6: 8 test patients")
SLIDES["s17"] = s17

s18 = (SL / "s18.html").read_text(encoding="utf-8").replace("Figure 8: Final system", "Figure 7: Final system")
SLIDES["s18"] = s18

# ------------------------------------------------------------------ p18 · Model Comparison
SLIDES["s16"] = main_slide(
    "s16", "Model Comparison",
    take(f"At the same false-alarm rate, adding a {r('kNN on the same channel features')} improves the GAE {AFTER}") + "\n"
    + '<div style="display:flex;flex-direction:row;gap:34px;align-items:start">'
    + img(B["model"], "Per-patient mean sensitivity at 27.5 false alarms per day for GAE, GAE + kNN and kNN on four sets", 1080, 576,
          "Figure 8: per-patient mean at 27.5 FA/day, after the localizer; GAE and GAE + kNN 4 seeds", 24)
    + '<div style="flex:1;display:flex;flex-direction:column;gap:6px">'
    + '<p style="font-size:30px;line-height:1.3"><b>Same chain after the per-channel score;</b> each model calibrated on development only</p>'
    + ul([f"CHB-MIT test, GAE + kNN − GAE: {r('+0.047')} [+0.013, +0.086]",
          "kNN − GAE: +0.053 [−0.020, +0.143], not significant",
          "chb24: GAE + kNN 14/16 at 13.6 FA/day vs GAE 14/16 at 28.4",
          f"Connectivity only: {r('0.106')} vs GAE 0.342 (pooled, seed 42, detector stage)"], 29)
    + f'<p style="font-size:24px;line-height:1.3;font-style:italic;color:{GREY}">Paired patient bootstrap, 10,000 resamples</p>'
    + "</div></div>\n"
    + arrow("The signal sits in per-channel spectral and amplitude features; GAE + kNN is the improvement, the GAE stays the thesis system", 31),
    notes="GAE = thesis system (report, demo). kNN = strongest baseline. Five representations: Appendix I2; full numbers: I1; EEG of seizures only one model catches: I3.")

# ------------------------------------------------------------------ p19 · Why Some Patients Are Hard
SLIDES["s15"] = main_slide(
    "s15", "Why Some Patients Are Hard",
    take(f"Missed seizures are {r('focal')} and {r('low-amplitude')}: about one channel, barely above the minute before {AFTER}") + "\n"
    + '<div style="display:flex;flex-direction:row;gap:30px;align-items:start">'
    + img(B["hard"], "Channels involved versus amplitude ratio for every CHB-MIT seizure, hard cases versus other cases", 900, 562,
          "Figure 9: 185 CHB-MIT seizures, real EEG; filled = detected, open = missed", 24)
    + '<div style="flex:1;display:flex;flex-direction:column;gap:8px">'
    + hole(890, 300, "One detected and one missed seizure on real EEG (rule-selected)",
           "Figure 10: real EEG, selection rule in the caption", 24)
    + ul([f"kNN on all 24 cases: 6 below 0.35 (chb06, 12, 13, 15, 16, 21)",
          f"Medians, hard vs other: {r('1 vs 13')} channels · {r('1.27× vs 2.58×')} · 36 vs 62 s",
          "Not just short: chb14 (short seizures) 8/8",
          "Test patients harder than CHB-MIT as a whole: 0.565 vs 0.763 per case"], 28)
    + "</div></div>\n"
    + arrow("The limit is the signal of focal seizures, not the post-processing", 31),
    notes="Hard cases defined by the kNN run on all 24 cases (leave-one-case-out k). EEG galleries: Appendix I5; per test patient: I6; kNN per case: I4.")

# ------------------------------------------------------------------ p20 · External Validation (+ Siena explained)
SLIDES["s19"] = main_slide(
    "s19", "External Validation",
    take(f"The system transfers to {r('adults')} of another hospital; Siena scores higher for {r('measured')} reasons") + "\n"
    + '<div style="display:flex;flex-direction:row;gap:30px;align-items:start">'
    + img(B["siena"], "Sensitivity at matched false alarms for CHB-MIT test, chb24 and Siena; seizure duration mix", 1160, 465,
          "Figure 11: seed 42, detector stage, one global budget; after the review", 24)
    + '<div style="flex:1;display:flex;flex-direction:column;gap:4px">'
    + '<p style="font-size:31px;line-height:1.3"><b>chb24 (child, never used):</b></p>'
    + f'<p style="font-size:31px;line-height:1.3">{r("14/16")} at 29.5 FA/day (seed 42)</p>'
    + '<p style="font-size:31px;line-height:1.3;padding:10px 0px 0px 0px"><b>Siena (14 adults):</b></p>'
    + f'<p style="font-size:31px;line-height:1.3">per-patient mean {r("0.633 ± 0.079")} at 41.0 FA/day (4 seeds)</p>'
    + f'<p style="font-size:29px;line-height:1.3;padding:10px 0px 0px 0px"><b>Why Siena is higher</b> {AFTER}</p>'
    + ul(["Same 27.5 FA/day: 0.534 vs CHB-MIT test 0.355",
          "≤ 20 s seizures: 5/47 vs 24/76 → about 40 % of the gap",
          "Many patients with 1–2 seizures: without them 0.530"], 28)
    + "</div></div>\n"
    + arrow("The label-free design moves to a new hospital without any retuning", 31),
    notes="Siena per patient (old Figure 9): Appendix I10 and E7. 40 % = computed from the bin counts (CHB-MIT test with Siena's duration mix gives 0.576 instead of 0.500).")

# ------------------------------------------------------------------ p21 · Label-free Runs
SLIDES["s24"] = main_slide(
    "s24", "Label-free Runs: App and Hospital EEG",
    take(f"Without any label, the app finds {r('33/76')} test seizures and flags {r('4.8 %')} of a real hospital recording") + "\n"
    + '<div style="display:flex;flex-direction:row;gap:36px;align-items:start">'
    + '<div style="width:900px;display:flex;flex-direction:column;gap:8px">'
    + hole(900, 380, "SzScan screenshot of a detected test seizure (real export)", "(a) review application, 8 test patients", 24)
    + ul([f"231 files: {r('33/76')} at 27.9 FA/day (per-patient mean 0.528)",
          f"{r('21.68 s')} per hour of EEG on a laptop CPU (about 9 min per recorded day)"], 29)
    + "</div>"
    + '<div style="flex:1;display:flex;flex-direction:column;gap:8px">'
    + hole(900, 380, "Hospital EEG: score timeline with the events and the marked segments",
           "(b) hospital EEG, Vietnam, no annotation (after the review)", 24)
    + ul([f"13.2 h recording: 35 events, {r('4.8 %')} flagged (about 38 min to review)",
          "1.25 h activation recording: none of its 3 events on the 27 marked segments (eyes, hyperventilation, photic, spikes)"], 29)
    + "</div></div>\n"
    + f'<p style="font-size:24px;line-height:1.3;font-style:italic;color:{GREY}">Figure 12 · hospital EEG: qualitative only; no names, file names or dates shown</p>\n'
    + arrow("Objective 4 delivered: the system runs on an ordinary laptop, on data it has never seen", 31),
    notes="38 min = computed (4.78 % of 13.2 h). Event panels and the activation markers: Appendix I13; every web-demo event on EEG: I12.")

# ------------------------------------------------------------------ p22 · Channel-Level Explanation (EEG panels)
SLIDES["s20"] = main_slide(
    "s20", "Channel-Level Explanation",
    take("The channel ranking agrees with a blind annotation only slightly above chance and below an anatomical prior") + "\n"
    + '<div style="display:flex;flex-direction:row;gap:34px;align-items:start">'
    + hole(1160, 600, "Three EEG panels with the channel heat strip: best focal (chb15 seizure 2), worst focal (chb16 seizure 7), generalized (chb13 seizure 10)",
           "Figure 13: channel-level latent anomaly on real EEG, seed 42, rule-selected", 24)
    + '<div style="flex:1;display:flex;flex-direction:column;gap:6px">'
    + ul([f"Mean AUROC {r('0.547')} [0.499, 0.597]", f"Anatomical prior {r('0.739')}; random 0.500",
          "Only chb15 above its prior; without it 0.486", "Blind, every-channel annotation, approved by the supervisor"], 31, 1.45)
    + '<p style="font-size:31px;line-height:1.3;padding:16px 0px 0px 0px">'
    + f'<b><span style="color:{RED}">→ Objective 3 evaluated: the channel ranking shows the model’s anomaly, not an onset map</span></b></p>'
    + "</div></div>",
    notes="62 focal test seizures. Per-patient dumbbell (old Figure 10): Appendix F3. XAI concordance, not localization.")

# ------------------------------------------------------------------ p23 · Comparison with Other Studies
cmp_rows = [
    ["Study", "Seizure labels of the reviewed patient", "One model for new patients", "Patients and seizures scored", "Scoring", "Result"],
    ["Chung et al., 2026 · CNN", "none (supervised on other patients)", "yes", "CHB-MIT; chb06, chb14, chb16 excluded", "own event rule", "80.1% at 1.13/h (≈ 27/day)"],
    ["Mirzaei &amp; Singh, 2025 · CNN-LSTM", "threshold set with its own seizures", "no", "18 of 24 patients; seizures ≥ 40 s", "own event rule", "91.56% at 0.1/h"],
    ["DynaSD (Ojemann, 2026)", "threshold from labelled iEEG", "yes", "Siena, every patient", "SzCORE", "0.664 at 77.7/day"],
    ["<b>This work · GAE</b>", "<b>none</b>", "<b>yes</b>", "<b>every test patient and seizure, continuous; + 2 external sets</b>", "<b>SzCORE</b>",
     "<b>26/76 at 22.2/day</b> (held-out); 27/48 = 0.562 at 25.7/day under Chung’s exclusion*; Siena <b>0.633</b> at 41.0"],
]
SLIDES["s22"] = main_slide(
    "s22", "Comparison with Other Studies",
    take(f"Same problem = {r('no label')} of the patient, {r('every')} patient and seizure, continuous recordings, event scoring") + "\n"
    + table(cmp_rows, [17, 17, 11, 20, 11, 24], 26, hl=(4,)) + "\n"
    + f'<p style="font-size:23px;line-height:1.25;font-style:italic;color:{GREY}">* after the review: final system, seed 42, secondary analysis under the other study’s protocol · ≈ 27/day computed from 1.13/h</p>\n'
    + f'<p style="font-size:29px;line-height:1.3"><b><span style="color:{GREEN}">Strengths:</span></b> no label of the reviewed patient · every patient and seizure · SzCORE events · external and hospital data</p>\n'
    + f'<p style="font-size:29px;line-height:1.3"><b><span style="color:{ORANGE}">Weaknesses:</span></b> lower sensitivity than the supervised CNN at a similar alarm rate · more false alarms than per-patient tuning</p>\n'
    + arrow("Under the same rules the gap is measured, and its causes are shown (next slide)", 31)
    + "\n" + cite("Chung et al., 2026 · Mirzaei &amp; Singh, 2025 · Ojemann et al., 2026 · EPFL SzCORE benchmark"),
    gap=10,
    notes="Siena supervised entries (Zhu 2023 0.674 at 15.3; EventNet 0.587 at 8.2): Appendix E8. Full protocol table: E9. Never say 'low because unsupervised': give the measured causes (p19, p24).")

# ------------------------------------------------------------------ p24 · Optimization Path and Limits
after_rows = [["Tried after the review", "CHB-MIT test", "Kept?"],
              ["kNN on the same channel features", "+0.047 [+0.013, +0.086] at 27.5 FA/day", f'<span style="color:{GREEN}"><b>improvement</b></span>'],
              ["Artifact veto (hand-made features)", "0.487 at 27.5 → 0.434 at 18.2; chb24 14/16 → 7/16", f'<span style="color:{ORANGE}"><b>no</b></span>'],
              ["Short-seizure branch (8 s smoothing)", "≤ 20 s seizures 7/24 → 4/24", f'<span style="color:{ORANGE}"><b>no</b></span>']]
lim_rows = [["Limit", "Measured cause", "Next"],
            ["Focal, low-amplitude seizures", "1 vs 13 channels; 1.27× vs 2.58×", "GAE + kNN; more patients"],
            ["False alarms", "80–89 % with high-amplitude channels; artifact features AUROC 0.42–0.63", "supervised artifact detector"],
            ["Offsets", "error 24 s (4 seeds)", "multichannel change points"],
            ["8 test patients", "harder than CHB-MIT: 0.565 vs 0.763 per case", "prospective study"]]
SLIDES["s25b"] = main_slide(
    "s25b", "Optimization Path and Limits",
    take(f"Every step was kept only if it helped at a {r('fixed false-alarm rate')}; two ideas after the review did not") + "\n"
    + '<div style="display:flex;flex-direction:row;gap:30px;align-items:start">'
    + '<div style="width:960px;display:flex;flex-direction:column;gap:8px">'
    + img(B["devpath"], "Pooled sensitivity by normal reference and by added component, development patients", 960, 372,
          "Figure 14: development path, 15 patients, 4 seeds, ≤ 25 FA/day · test reached about half (0.336 vs 0.662)", 23)
    + table(after_rows, [38, 46, 16], 25) + "</div>"
    + '<div style="flex:1;display:flex;flex-direction:column;gap:8px">' + table(lim_rows, [28, 42, 30], 25) + "</div></div>\n"
    + arrow("What remains is the signal of focal seizures and artifact-like false alarms", 31),
    notes="Development numbers are optimistic (about 2x). After-review ideas: rules fixed before the runs. Details: Appendix I8 (artifact veto), I9 (short-seizure branch), I7 (false-alarm types). 80 %: CHB-MIT test + chb24 + 3 Siena; 89 %: all 14 Siena patients.")

# ------------------------------------------------------------------ p25 · Deployment (Canva wording)
s23 = (SL / "s23.html").read_text(encoding="utf-8").replace(
    "Sites without labels, GPU or cloud (nearly 80% of people with epilepsy)",
    "Low- and middle-income settings without GPU or cloud (where nearly 80% of people with epilepsy live)")
SLIDES["s23"] = s23

# ------------------------------------------------------------------ p26 · Conclusion
left = ('<div style="width:860px;display:flex;flex-direction:column;gap:6px">'
        f'<p style="font-size:31px;line-height:1.3;color:{BLUE}"><b>Objectives and goals</b></p>'
        + ul([f"<b>Goal:</b> localization without labels → <b><span style=\"color:{GREEN}\">Achieved</span></b>",
              f"<b>Objective 1:</b> anomaly score → <b><span style=\"color:{GREEN}\">Achieved</span></b>",
              f"<b>Objective 2:</b> change points → <b><span style=\"color:{GREEN}\">Achieved and evaluated</span></b>",
              f"<b>Objective 3:</b> channel explanation → <b><span style=\"color:{GREEN}\">Evaluated</span></b>",
              f"<b>Objective 4:</b> review app → <b><span style=\"color:{GREEN}\">Delivered</span></b>"], 28, 1.35)
        + f'<p style="font-size:31px;line-height:1.3;color:{BLUE};padding:8px 0px 0px 0px"><b>Contributions</b></p>'
        + ul(["the patient’s whole recording as the normal reference", "a label-free alarm budget and drift correction",
              "change points on a learned anomaly score", "event-level tests on unseen, external and hospital data",
              "other models and hard cases compared at the same false-alarm rate"], 28, 1.35) + "</div>")
right = ('<div style="flex:1;display:flex;flex-direction:column;gap:4px">'
         f'<p style="font-size:31px;line-height:1.3;color:{BLUE}"><b>Summary of findings</b></p>'
         + f'<p style="font-size:27px;line-height:1.3;color:{RED}"><b>Results</b></p>'
         + ul(["Unseen patients: 26/76 at 22.2 FA/day (held-out, seed 42)",
               "Onset: error 32 → 12s; offset not improved (4 seeds)",
               "Other models: GAE + kNN +0.047 at the same FA/day (after the review)",
               "Hard cases: focal, low-amplitude seizures",
               "New hospital: Siena 0.633 at 41.0 FA/day (per-patient mean, 4 seeds); hospital EEG 4.8 % flagged",
               "Channels: 0.547, below the anatomical prior 0.739",
               "App: 33/76 without labels; 21.68s per hour of EEG"], 27, 1.3)
         + f'<p style="font-size:27px;line-height:1.3;color:{RED}"><b>Discussion</b></p>'
         + ul(["vs DynaSD: similar sensitivity, about half the false alarms",
               "Limits: focal, low-amplitude seizures; artifact-like false alarms"], 27, 1.3)
         + '<p style="font-size:27px;line-height:1.3">→ <b>Next step</b>: GAE + kNN, a supervised artifact detector, more patients, a prospective study</p>'
         + "</div>")
SLIDES["s25"] = main_slide(
    "s25", "Conclusion",
    '<div style="display:flex;flex-direction:column;border:3px dashed #1E2430;border-radius:10px;padding:12px 24px">'
    f'<p style="font-size:32px;line-height:1.35">{r("Label-free triage of finished EEG:")} candidate seizures with onset and offset, without any label of the reviewed patient; the reader still decides</p></div>\n'
    + '<div style="display:flex;flex-direction:row;gap:36px;align-items:start">' + left + right + "</div>",
    notes="Then the 3-minute live demo (chb03 or chb24 ingested beforehand; fallback video Appendix G3), then Thank you.")

# ------------------------------------------------------------------ ToC, Datasets, Evaluation, References
s02 = (SL / "s02.html").read_text(encoding="utf-8")
s02 = s02.replace("Unseen patients, external data and the review app", "Unseen patients, other models, new hospitals")
s02 = s02.replace("Comparison, deployment and limits", "Comparison, optimization and limits")
SLIDES["s02"] = s02

s08 = (SL / "s08.html").read_text(encoding="utf-8")
s08 = s08.replace("<tr><td>External</td><td>Siena, 14 adults</td><td>141.0</td><td>47</td><td>scored once, unchanged</td></tr>",
                  "<tr><td>External</td><td>Siena, 14 adults</td><td>141.0</td><td>47</td><td>scored once, unchanged</td></tr>\n"
                  "<tr><td>Hospital</td><td>2 recordings, Vietnam</td><td>13.2 + 1.25</td><td>no labels</td><td>run once, unchanged; qualitative</td></tr>")
s08 = s08.replace("font-size:34px;line-height:1.25", "font-size:32px;line-height:1.22")
SLIDES["s08"] = s08

s14 = (SL / "s14.html").read_text(encoding="utf-8")
s14 = s14.replace("<tr><td>Application</td><td>8 test</td><td>the app, no labels</td></tr>",
                  "<tr><td>Application</td><td>8 test</td><td>the app, no labels</td></tr>\n"
                  "<tr><td>Channels</td><td>62 focal test seizures</td><td>ranking vs a blind channel annotation</td></tr>\n"
                  "<tr><td>Other models</td><td>every set</td><td>same false-alarm rate, paired bootstrap (after the review)</td></tr>")
s14 = s14.replace("font-size:31px;line-height:1.25", "font-size:28px;line-height:1.2")
SLIDES["s14"] = s14

s26 = (SL / "s26.html").read_text(encoding="utf-8")
chung = ('<p style="font-size:24px;line-height:1.25">Chung, Y. G., Cho, J., Cho, A., Kim, H., &amp; Lim, B. C. (2026). Patient-independent automated pediatric seizure monitoring based on expert-labeled electrographic ictal data as core reference knowledge. <i>Clin. Exp. Pediatr.</i>, 69(8), 665–675. doi:10.3345/cep.2026.01011</p>')
mirz = ('<p style="font-size:24px;line-height:1.25">Mirzaei, E., &amp; Singh, R. (2025). Real-time EEG-based epileptic seizure detection by one-class classification using CNN-LSTM and STFT. <i>IEEE ISBI 2025</i>. doi:10.1109/ISBI60581.2025.10981145</p>')
anchor = '<p style="font-size:24px;line-height:1.25">Dan, J., et al. (2025).'
assert anchor in s26
s26 = s26.replace(anchor, chung + anchor, 1)
anchor2 = '<p style="font-size:24px;line-height:1.25">Ojemann, W. K. S.'
assert anchor2 in s26
s26 = s26.replace(anchor2, mirz + anchor2, 1)
s26 = s26.replace("font-size:24px;line-height:1.25", "font-size:22px;line-height:1.2").replace("gap:11px", "gap:8px")
SLIDES["s26"] = s26

# ------------------------------------------------------------------ Appendix pages: B5, E5 text, E9, E10
SLIDES["aB5"] = app_slide(
    "aB5", "B5 · Graphs and Latent Distance",
    "Sparse graphs separate seizure from background connectivity; the latent distance, not reconstruction, separates seizures from high-amplitude windows",
    img(B["graphs"], "Graph density and seizure-background distance per test patient, fixed threshold vs strongest 20 %", 1400, 500,
        "8 test patients: (a) density, (b) seizure–background distance of mean connectivity")
    + ul(["Strongest 20%: density 0.196 (fixed threshold 0.92–0.97); separation higher in 8/8",
          "Seizure vs high-amplitude windows: latent AUROC 0.966, reconstruction 0.53 (development)",
          f"After the review: connectivity alone 0.106 vs GAE 0.342 at 27.5 FA/day (CHB-MIT test) → the separation is in mean connectivity; detection needs the channel features (I2)"], 29)
    + cite("Report Table 5, Section 3.1, Figure 11; Section 4.2 · after the review: results/v9_e1/"))

e5 = (SL / "aE5.html").read_text(encoding="utf-8")
e5 = e5.replace("misses are short or sit inside the patient’s own activity",
                "misses are focal, low-amplitude seizures or sit inside the patient’s own activity")
SLIDES["aE5"] = e5

e9_rows = [
    ["Study", "Labels of the reviewed patient", "Patient-specific?", "Patients, seizures", "Continuous, scoring", "Reported result"],
    ["Chung 2026", "none (supervised on others)", "no, leave one patient out", "CHB-MIT; chb06, 14, 16 excluded", "not stated; own event rule", "80.1% at 1.13/h"],
    ["Yin &amp; Yin 2026", "yes (recording-level split)", "within case", "CHB-MIT; chb06, 12, 16 excluded", "own rule", "100% at 0.82/h"],
    ["Mirzaei &amp; Singh 2025", "threshold per patient", "yes", "18 of 24; seizures ≥ 40 s", "own event rule", "91.56% at 0.1/h"],
    ["Chung 2024", "yes, tuned per case", "yes", "13 selected cases", "own event rule", "100% events, 0.30/h"],
    ["Ali 2024", "yes", "no, leave one subject out", "CHB-MIT", "≥ 70 % coverage rule", "75.34%, 4.79/h"],
    ["Shyu 2023", "yes", "with vs without test subject", "CHB-MIT", "windows", "F1 69.34% → 37.31%"],
    ["Ojemann 2026 (DynaSD)", "threshold from labelled iEEG", "no", "Siena, every patient", "continuous; SzCORE", "0.664 at 77.7/day"],
    ["Zhu 2023 · EventNet 2024", "supervised on TUH", "no", "Siena, every patient", "continuous; SzCORE", "0.674 at 15.3/day · 0.587 at 8.2/day"],
    ["<b>This work · GAE</b>", "<b>none</b>", "<b>no, one model</b>", "<b>8 unseen, every seizure</b>", "<b>continuous; SzCORE</b>", "<b>26/76 at 22.2/day (held-out)</b>"],
    ["<b>This work</b>, Chung’s exclusion*", "none", "no", "chb06, 14, 16 excluded", "continuous; SzCORE", "27/48 = 0.562 at 25.7/day"],
    ["<b>This work</b>, seizures ≥ 30 s*", "none", "no", "8 unseen, 45 seizures", "continuous; SzCORE", "28/45 = 0.622"],
]
SLIDES["aE9"] = app_slide(
    "aE9", "E9 · Published Results and Protocols",
    "“Same problem” = labels of the reviewed patient, one model for new patients, which patients and seizures, continuous scoring with a false-alarm rate",
    table(e9_rows, [18, 17, 14, 18, 15, 18], 23, hl=(9, 10, 11))
    + f'<p style="font-size:22px;line-height:1.25;font-style:italic;color:{GREY}">* after the review: final system, seed 42, secondary analysis under the other study’s protocol, never the headline · per hour × 24 = per day (computed): 1.13/h ≈ 27, 0.82/h ≈ 20, 0.1/h ≈ 2.4</p>'
    + cite("Chung et al., 2026 · Yin &amp; Yin, 2026 · Mirzaei &amp; Singh, 2025 · Chung et al., 2024 · Ali et al., 2024 · Shyu et al., 2023 · Ojemann et al., 2026 · EPFL SzCORE benchmark · results/v9_e1/ Part C"),
    gap=10)

SLIDES["aE10"] = app_slide(
    "aE10", "E10 · Budget and Duration",
    "Most missed seizures would need a budget far above the patient’s own; duration adds to the difficulty but does not define it",
    '<div style="display:flex;flex-direction:row;gap:40px;align-items:start;justify-content:center">'
    + img(B["fig11"], "Budget a threshold would need to reach each test seizure, with the patient's alarm budget", 900, 415,
          "Budget a threshold would need to reach each seizure (seed 42)")
    + img(B["fig12"], "Seizures detected by duration bin, held-out and final", 740, 415, "Detection by duration (whole 4 s windows)")
    + "</div>"
    + ul(["chb06, chb13, chb16: 5/32 found; their seizures need a median budget of 3.0–4.2 % of the time (cap 2 %)",
          "Under 20 s: 4/18 found; but chb14 (short seizures) 8/8 → hard = focal, low amplitude (p19)"], 29)
    + cite("Report Figures 15–16, Section 4.3 · after the review: results/v9_e4/, results/v9_v1/"))

# ------------------------------------------------------------------ Appendix I · After the review
SLIDES["aI1"] = app_slide(
    "aI1", "I1 · Model Comparison in Full",
    "Same chain after the per-channel score; each model’s budget constant calibrated on the 15 development patients only (after the review)",
    table([["Per-patient mean sensitivity", "GAE", "GAE + kNN", "kNN on the same channel features"],
           ["Development (15), 27.5 FA/day", "0.837", "0.902", "0.919"],
           ["CHB-MIT test (8), 27.5 FA/day", "0.554", "0.601", "0.607"],
           ["CHB-MIT test (8), 44 FA/day", "0.601", "0.646", "0.666"],
           ["chb24, 27.5 FA/day", "0.820", "0.913", "0.830"],
           ["Siena (14), 27.5 FA/day", "0.492", "0.553", "0.595"],
           ["Siena (14), 44 FA/day", "0.642", "0.726", "0.745"]], [40, 18, 18, 24], 28)
    + ul(["Paired patient bootstrap (10,000), CHB-MIT test, 27.5 FA/day: GAE + kNN − GAE +0.047 [+0.013, +0.086]; kNN − GAE +0.053 [−0.020, +0.143]",
          "Siena: GAE + kNN − GAE +0.061 [−0.132, +0.247] (not significant)",
          "Each at its own calibrated point, chb24: GAE + kNN 14/16 at 13.6 FA/day vs GAE 14/16 at 28.4"], 28)
    + cite("results/v9_e1b/, results/v9_e2/paired/ · system stage, after the localizer · GAE and GAE + kNN: 4 seeds"))

SLIDES["aI2"] = app_slide(
    "aI2", "I2 · Five Representations",
    "At the same false-alarm rate, the per-channel spectral and amplitude features carry the signal; connectivity alone is the weakest (after the review)",
    img(B["five"], "Pooled sensitivity at 27.5 false alarms per day for six representations", 1500, 657,
        "CHB-MIT test, detector stage, one global budget, seed 42")
    + cite("results/v9_e1/ · same order statistics, drift correction, budget and scorer for every representation"))

SLIDES["aI3"] = app_slide(
    "aI3", "I3 · GAE vs GAE + kNN on EEG",
    "Seizures that only one of the two models catches, on real EEG, selected by a rule fixed before drawing (after the review)",
    hole(1840, 660, "EEG panels: seizures caught only by GAE + kNN and only by GAE, with both score traces")
    + cite("results/v9_v1/ (part5) · seed 42"),
    notes="Insert figs/eeg_evidence/part5/ panels.")

SLIDES["aI4"] = app_slide(
    "aI4", "I4 · kNN on All 24 CHB-MIT Cases",
    "No training and a leave-one-case-out budget constant: the 8 test patients are harder than CHB-MIT as a whole (after the review)",
    img(B["knn24"], "Sensitivity per CHB-MIT case for the kNN on the same channel features", 1700, 584,
        "kNN on the same channel features, after the localizer; orange = below 0.35")
    + ul(["All 24 cases: per-case mean 0.763 [0.619, 0.888] at 17.7 FA/day; 23 subjects (chb21 = chb01 removed) 0.785",
          "Former development 0.866 · former test 0.565 · below 0.35: chb06, chb12, chb13, chb15, chb16, chb21"], 28)
    + cite("results/v9_e4/"))

SLIDES["aI5"] = app_slide(
    "aI5", "I5 · Hard Seizures on EEG",
    "The median seizure of every CHB-MIT patient: the hard cases are focal and barely above the minute before (after the review)",
    '<div style="display:flex;flex-direction:row;gap:24px">'
    + hole(900, 600, "Median seizure of each development patient (gallery_dev)")
    + hole(900, 600, "Median seizure of each test patient (gallery_test)") + "</div>"
    + ul(["Hard vs other cases, medians: 1 vs 13 channels · amplitude 1.27× vs 2.58× · 36 vs 62 s"], 28)
    + cite("results/v9_v1/ (part1) · real EEG, pipeline filter"),
    notes="Insert figs/eeg_evidence/part1/gallery_dev.png and gallery_test.png; descriptors_by_set_slide.png can go under them.")

SLIDES["aI6"] = app_slide(
    "aI6", "I6 · EEG of Every Test Patient",
    "Per test patient: the best detection, a typical miss and the top false alarm, chosen by fixed rules (after the review)",
    hole(1840, 680, "Contact sheet of the 22 rule-selected panels (8 test patients)")
    + cite("eeg_samples · GAE seed 42"),
    notes="Insert figs/eeg_samples/ (22 panels); split over two pages if they do not read at this size.")

SLIDES["aI7"] = app_slide(
    "aI7", "I7 · False-Alarm Types",
    "Most false alarms are dense activity over many channels or one dominant channel: artifact-like, not seizure-like (after the review)",
    '<div style="display:flex;flex-direction:row;gap:30px;align-items:start">'
    + hole(1180, 600, "Two EEG panels per type and four look-alike true/false pairs (part4)")
    + '<div style="flex:1;display:flex;flex-direction:column;gap:6px">'
    + table([["Type (of typeable false alarms)", "Share"], ["spread over many channels", "47 %"], ["one channel dominating", "32 %"],
             ["frontal-polar", "13 %"], ["high-frequency", "8 %"]], [70, 30], 27)
    + ul(["With a high-amplitude channel: 80 % (CHB-MIT test, chb24, 3 Siena) · 89 % (14 Siena)"], 27)
    + "</div></div>"
    + cite("results/v9_v1/ (part4), results/v9_anatomy/ · GAE seed 42, CHB-MIT test + Siena"))

SLIDES["aI8"] = app_slide(
    "aI8", "I8 · Artifact Veto: Not Adopted",
    "A veto from hand-made artifact features trades seizures for false alarms; rule fixed on development before the run (after the review)",
    table([["Step", "What was done", "Result"],
           ["Candidates", "high-frequency share (muscle), frontal-polar share (eye), spatial extent (movement), one-channel dominance (electrode), event duration", "best development separator: event duration, not an artifact feature"],
           ["Separation", "true vs false alarms on test + Siena", "AUROC 0.42–0.63"],
           ["Applied once", "keep ≥ 95 % of development detections", "CHB-MIT test 0.487 at 27.5 → 0.434 at 18.2; chb24 14/16 → 7/16"],
           ["Decision", "a trade, not a gain; it deletes short seizures", "not adopted → supervised artifact detector (future work)"]], [16, 46, 38], 27)
    + cite("results/v9_e2/ · GAE seed 42"))

SLIDES["aI9"] = app_slide(
    "aI9", "I9 · Short-Seizure Branch: Not Adopted",
    "Shorter smoothing lets short noise peaks compete for the same alarm budget; the limit is the signal, not the post-processing (after the review)",
    table([["Step", "What was done", "Result"],
           ["Idea", "maximum of the 20 s and the 8 s smoothed score", "one fixed configuration, rule fixed before the run"],
           ["CHB-MIT test", "seizures ≤ 20 s", "7/24 → 4/24"],
           ["Decision", "not adopted by the fixed rule", "consistent with p19: focal, low-amplitude seizures"]], [16, 46, 38], 28)
    + cite("results/v9_e3/"))

SLIDES["aI10"] = app_slide(
    "aI10", "I10 · Siena on 14 Patients",
    "All 14 Siena patients reproduce the external run; the higher score has measured causes (after the review)",
    '<div style="display:flex;flex-direction:row;gap:30px;align-items:start">'
    + img(B["siena_pp"], "Siena per patient: seizures detected and false alarms per day", 1150, 530,
          "Siena per patient, seed 42 (report Table 15)")
    + '<div style="flex:1;display:flex;flex-direction:column;gap:6px">'
    + ul(["Matched 20 / 27.5 / 44 FA/day: Siena 0.481 / 0.534 / 0.673; CHB-MIT test 0.318 / 0.355 / 0.366",
          "≤ 20 s: 5/47 vs 24/76; CHB-MIT test with Siena’s duration mix: 0.576 instead of 0.500 (computed)",
          "Without the 6 patients with ≤ 2 seizures: 0.633 → 0.530 (pooled 0.617 → 0.568), 4 seeds",
          "False alarms with a high-amplitude channel: 89 %"], 27)
    + "</div></div>"
    + cite("results/v9_anatomy/siena14/ · report Tables 14–15"))

SLIDES["aI11"] = app_slide(
    "aI11", "I11 · Siena and CHB-MIT on EEG",
    "Typical seizures of both sets and the Siena patients with the most seizures, rule-selected (after the review)",
    '<div style="display:flex;flex-direction:row;gap:24px">'
    + hole(900, 640, "Siena: 4 patients with the most seizures + the shortest seizure (eeg_samples/siena14)")
    + hole(900, 640, "Typical seizure, Siena vs CHB-MIT (part2)") + "</div>"
    + cite("real EEG, pipeline filter · GAE seed 42"))

SLIDES["aI12"] = app_slide(
    "aI12", "I12 · Application Events on EEG",
    "Every detection of the application run and sampled false alarms on real EEG, with screenshots of the same events in SzScan (after the review)",
    '<div style="display:flex;flex-direction:row;gap:24px">'
    + hole(900, 600, "Contact sheets: all 33 detections; top + 2 random false alarms per patient")
    + hole(900, 600, "4 SzScan screenshots (chb03, chb06: detection and false alarm); times match the export") + "</div>"
    + ul(["Application run: 33/76 at 27.9 FA/day; 323 false alarms by the scorer"], 28)
    + cite("eeg_evidence/part3 · results/application_eval_v4/"))

SLIDES["aI13"] = app_slide(
    "aI13", "I13 · Hospital EEG in Detail",
    "Two recordings from a Vietnamese hospital, use approved, no seizure annotation: the system unchanged, read qualitatively (after the review)",
    '<div style="display:flex;flex-direction:row;gap:24px;align-items:start">'
    + hole(1100, 600, "Score timelines with the marked segments; top event and spike panels")
    + '<div style="flex:1;display:flex;flex-direction:column;gap:6px">'
    + ul(["All 18 bipolar pairs buildable; notch 50 Hz; 512 → 256 Hz", "13.2 h: 35 events, 4.8 % flagged (about 38 min, computed)",
          "1.25 h activation: 3 events, none on the 27 marked segments", "Top events: dense fast activity on all channels, like the top false alarms of CHB-MIT and Siena",
          "No names, file names or dates shown"], 27)
    + "</div></div>"
    + cite("GAE seed 42, label-free statistics · qualitative only, no seizure metric"))

# ------------------------------------------------------------------ write, renumber
for sid, html in SLIDES.items():
    (SL / f"{sid}.html").write_text(html, encoding="utf-8")

PILL_RE = re.compile(r'<p style="position:absolute;left:\d+px;bottom:16px;width:\d+px;height:56px;[^"]*">(Introduction|Methodology|Results|Discussion|Conclusion)</p>')
NUM_RE = re.compile(r'(<p style="position:absolute;right:40px;bottom:22px;[^"]*">)(\d+)(</p>)')
changed = set(SLIDES)
for sid in ORDER:
    if sid == "aH3":
        continue
    f = SL / f"{sid}.html"
    s = f.read_text(encoding="utf-8")
    t = NUM_RE.sub(lambda m: f"{m.group(1)}{PAGE[sid]}{m.group(3)}", s)
    if sid in SECTION_OF and PILL_RE.search(t):
        block = "\n".join(PILL_RE.findall(t))
        t = PILL_RE.sub("", t)
        t = t.replace(FOOT, FOOT + "\n" + pills(SECTION_OF[sid]), 1)
        t = re.sub(r"\n{2,}", "\n", t)
    if t != s:
        f.write_text(t, encoding="utf-8")
        changed.add(sid)

deck = json.loads((ROOT / "project/deck.json").read_text(encoding="utf-8"))
deck["order"] = ORDER
deck["sections"] = {
    "main": {"description": "Main talk, pages 1-26 (D9, 30/10: after the reviewer's feedback; demo after page 26)", "start": "s01"},
    "refs": {"description": "References (27-28 in Canva) and Thank you (29)", "start": "s26"},
    "appA": {"description": "Appendix A: data", "start": "aA1"},
    "appB": {"description": "Appendix B: signal and graph", "start": "aB1"},
    "appC": {"description": "Appendix C: model and score", "start": "aC1"},
    "appD": {"description": "Appendix D: evaluation", "start": "aD1"},
    "appE": {"description": "Appendix E: results", "start": "aE1"},
    "appF": {"description": "Appendix F: channel explanation", "start": "aF1"},
    "appG": {"description": "Appendix G: application", "start": "aG1"},
    "appH": {"description": "Appendix H: models explored", "start": "aH1"},
    "appI": {"description": "Appendix I: after the review (model comparison, hard cases, Siena, false alarms, hospital EEG)", "start": "aI1"},
}
(ROOT / "project/deck.json").write_text(json.dumps(deck, indent=1, ensure_ascii=False), encoding="utf-8")
(ROOT / "changed.txt").write_text("\n".join(sorted(changed)), encoding="utf-8")
print(len(changed), "slide files changed;", len(ORDER), "in order")
