"""D4g main-slide fixes: ToC (p2), EEG and the Review Burden (p4), Thesis Goals (p6), Conclusion (p25)."""
from lib import *

S = {}

# ---------------------------------------------------------------- p2 Table of Content
rows = [("01.", "Introduction", "Epilepsy, EEG review and the research gap"),
        ("02.", "Methodology", "From raw EEG to seizure onset and offset"),
        ("03.", "Results", "Unseen patients, external data and the review app"),
        ("04.", "Discussion", "Comparison, deployment and limits"),
        ("05.", "Conclusion", "Goals achieved and next steps")]
items = "\n".join(
    f'<div style="display:flex;flex-direction:row;align-items:center;gap:28px;border-bottom:2px solid #C9D9EA;padding:26px 0px">'
    f'<p style="width:110px;font-family:{FH};font-size:52px;font-weight:700;color:{BLUE}">{n}</p>'
    f'<p style="width:330px;font-family:{FH};font-size:44px;color:{INK}">{t}</p>'
    f'<p style="flex:1;font-size:38px;color:{INK}">{d}</p></div>' for n, t, d in rows)
S["p02_toc"] = section("p02_toc", "Table of Content",
    f'<div style="display:flex;flex-direction:column;gap:6px;padding:20px 80px 0px 80px">{items}</div>', 2,
    notes="Section lines: one short summary of what each part covers.")

# ---------------------------------------------------------------- p4 EEG and the Review Burden
def step(n, name, eeg, burden):
    return (f'<div style="flex:1;display:flex;flex-direction:column;gap:10px">'
            f'<p style="font-family:{FH};font-size:32px;font-weight:600;color:#FFFFFF;background:{BLUE};'
            f'border-radius:10px;padding:6px 18px">{n} · {name}</p>'
            f'<p style="font-size:28px;line-height:1.3;color:{INK}">{eeg}</p>'
            f'<p style="font-size:28px;line-height:1.3;color:{ORANGE}"><b>Challenge:</b> {burden}</p></div>')

arrow = f'<p style="width:44px;font-size:44px;color:{BLUE};padding:4px 0px 0px 0px">→</p>'
grp1 = (f'<div style="width:900px;display:flex;flex-direction:column;gap:14px">'
        f'<div style="height:356px;display:flex;flex-direction:row;justify-content:center;align-items:center">{img("eeg_cap", "Scalp electrodes on the head and the EEG reading on a monitor", 620, 356)}</div>'
        f'<div style="display:flex;flex-direction:row;gap:10px">'
        + step(1, "Record", "Long-term scalp EEG is the clinical standard: non-invasive, it records brain electrical activity directly.",
               "recordings run for days: 1 in 3 first seizures appeared only after 24 h.")
        + arrow
        + step(2, "Read", "The reader goes through the whole recording before the report is finalized.",
               "time-consuming and labour-intensive: reading time grows with the recording’s length.")
        + "</div></div>")
grp2 = (f'<div style="width:900px;display:flex;flex-direction:column;gap:14px">'
        f'<div style="height:356px;display:flex;flex-direction:row;justify-content:center;align-items:center">{img("eeg_onset", "EEG trace from preictal to postictal with the seizure onset marked in red", 900, 338)}</div>'
        f'<div style="display:flex;flex-direction:row;gap:10px">'
        + step(3, "Mark", "Each seizure is marked with its onset, offset and the channels involved.",
               "artifacts can mimic or hide seizures; experts agree only moderately (κ&#160;=&#160;0.58).")
        + arrow
        + step(4, "Decide", "The marks support diagnosis, seizure classification and pre-surgical evaluation.",
               "the marks must be accurate, yet they come only after the recording has ended.")
        + "</div></div>")
body = (f'<div style="display:flex;flex-direction:row;gap:14px">{grp1}'
        f'<p style="width:44px;font-size:44px;color:{BLUE};padding:374px 0px 0px 0px">→</p>{grp2}</div>'
        f'<p style="font-size:30px;font-weight:700;line-height:1.3">→ Need: {span("review triage", RED)}. '
        f'Candidate seizure intervals with onset and offset, for the reader to confirm.</p>')
S["p04_eeg"] = section("p04_eeg", "EEG and the Review Burden", body, 4, nav="Introduction",
    cite="Timpte et al., 2023 · Tatum et al., 2022 (ILAE–IFCN guideline) · Tatum et al., 2011 · Halford et al., 2015 (8 experts, ICU EEG)",
    notes="Follow the EEG from recording to decision; at each step say what EEG gives and what makes it hard. "
          "1 in 3 first seizures after 24 h: Timpte 2023 (19 patients, 72 h video-EEG). Whole file reviewed before the report: "
          "ILAE-IFCN guideline (Tatum 2022), which also lists differential diagnosis, classification and presurgical evaluation. "
          "Artifacts mimic or obscure: Tatum 2011. kappa 0.58: Halford 2015, 8 board-certified experts, thirty 1-h ICU EEG segments.")

# ---------------------------------------------------------------- p6 Thesis Goals
def tag(text, reg):
    c = BLUE if reg else MUTED
    bg = "#DCEBF8" if reg else "#EEF1F4"
    return (f'<p style="font-size:24px;font-weight:700;color:{c};background:{bg};border-radius:16px;'
            f'padding:2px 14px">{text}</p>')

def goal(n, title, line, reg):
    t = "Registered objective " + str(n) if reg else "Added goal"
    return (f'<div style="display:flex;flex-direction:column;gap:4px">'
            f'<div style="display:flex;flex-direction:row;align-items:center;gap:16px">'
            f'<p style="font-size:34px;font-weight:700">{span("Goal " + str(n) + ":", RED)} {title}</p>{tag(t, reg)}</div>'
            f'<p style="font-size:31px;padding:0px 0px 0px 24px">→ {line}</p></div>')

left = (f'<div style="flex:1;display:flex;flex-direction:column;gap:34px">'
        f'<div style="display:flex;flex-direction:row;align-items:center;gap:16px">'
        f'<p style="font-size:34px;font-weight:700">{span("Aim:", RED)} localize seizure onset and offset without labels</p>'
        f'{tag("Registered goal", True)}</div>'
        + goal(1, "An unsupervised anomaly score", "Built from the spatial-temporal connectivity of multi-channel scalp EEG", True)
        + goal(2, "Onset and offset localization", "by non-parametric change point detection on that score", True)
        + goal(3, "A channel-level explanation", "tested against a blind channel annotation", False)
        + goal(4, "A review application", "that runs the whole system on complete recordings", False)
        + "</div>")
reqs = ["No seizure label of the reviewed patient", "Events with onset and offset", "One model for every new patient",
        "Bounded review load", "Settings fixed before testing", "Ordinary CPU, data stay in the hospital",
        "Every number traceable to a result file"]
right = (f'<div style="width:500px;display:flex;flex-direction:column;gap:10px;border:3px dashed {INK};border-radius:10px;padding:18px 22px">'
         f'<p style="font-size:30px;font-weight:700">Design requirements:</p>'
         f'<ul style="font-size:29px;line-height:1.45">' + "".join(f"<li>{r}</li>" for r in reqs) + "</ul></div>")
S["p06_goals"] = section("p06_goals", "Thesis Goals",
    f'<div style="display:flex;flex-direction:row;gap:40px;padding:10px 0px 0px 0px">{left}{right}</div>', 6, nav="Introduction",
    notes="Aim and Goals 1-2 are the goal and the two objectives of the signed registration form; Goals 3-4 were added. "
          "The conclusion closes each of them with the same labels.")

# ---------------------------------------------------------------- p25 Conclusion
key = (f'<p style="font-size:30px;line-height:1.35;border:3px dashed {INK};border-radius:10px;padding:12px 20px">'
       f'{span("Label-free triage of finished EEG recordings:", RED, True)} without any label of the reviewed patient, '
       f'the system found about a third of unseen seizures at about 22 false alarms per day and placed their onsets. '
       f'It points the reader to candidates; it does not replace reading.</p>')
A, EV, DL = span("Achieved", GREEN, True), span("Evaluated", ORANGE, True), span("Delivered", GREEN, True)
trows = [
    ["<b>Aim</b> (registered): onset and offset without labels", A, "A label-free pipeline from raw EEG to events with onset and offset"],
    ["<b>Goal 1</b> (registered objective 1): unsupervised anomaly score", A, "Held-out 26 / 76 at 22.2 false alarms per day (seed 42); Siena 0.633 at 41.0 (4 seeds)"],
    ["<b>Goal 2</b> (registered objective 2): change point localization", span("Achieved and evaluated", GREEN, True),
     "Onset error 32 → 12 s (4 seeds); the offset remains a limitation"],
    ["<b>Goal 3</b> (added): channel-level explanation", EV, "0.547 against a blind annotation, below an anatomical prior (0.739)"],
    ["<b>Goal 4</b> (added): review application", DL, "33 / 76 without labels; 21.68 s per hour of EEG"],
]
tbl = table(["Registered aim and goals", "Outcome", "Evidence"], trows, [38, 18, 44], fs=26)
lim = (f'<div style="display:flex;flex-direction:column;gap:4px">'
       f'<p style="font-size:27px;line-height:1.3">{span("Limits:", ORANGE, True)} short seizures (&lt; 20 s), seizures below the patient’s own high-amplitude activity, late offsets, only 8 test patients.</p>'
       f'<p style="font-size:27px;line-height:1.3">{span("Next:", BLUE, True)} shorter or overlapping windows, a representation that separates seizures from high-amplitude states, multichannel change points, a prospective study on new patients.</p></div>')
contrib = ["the patient’s whole recording as the normal reference", "a label-free alarm budget and drift correction",
           "change points on a learned anomaly score", "event-level tests on unseen and external patients"]
cdiv = (f'<div style="display:flex;flex-direction:row;align-items:start;gap:20px">'
        f'<p style="width:220px;font-size:28px;font-weight:700">Contributions:</p>'
        f'<ul style="flex:1;font-size:27px;line-height:1.35">' + "".join(f"<li>{c}</li>" for c in contrib[:2]) + "</ul>"
        f'<ul style="flex:1;font-size:27px;line-height:1.35">' + "".join(f"<li>{c}</li>" for c in contrib[2:]) + "</ul></div>")
S["p25_conc"] = section("p25_conc", "Conclusion", key + tbl + lim + cdiv, 25, nav="Conclusion", gap=14,
    notes="Answer first, then the registered aim and goals with the same labels as slide 6, then limits and next steps. "
          "If asked whether Goal 3 was met: as in the report, not as a localization aid (0.547 below the prior 0.739).")
