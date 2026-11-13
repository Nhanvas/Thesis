#!/usr/bin/env python
"""Build the v4 main slides (1-19 + References + Thank you) of the defense deck as Slides-type files.
Writes <root>/project/slides/<id>.html and <root>/project/deck.json. Content per SLIDE_OUTLINE rev 2.1 + DECK_BRIEF rev 2."""
import json
import sys
from pathlib import Path

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/home/claude/deck_v4/root")
OLD = Path(sys.argv[2] if len(sys.argv) > 2 else
           "/tmp/claude-0/-home-claude/5a2f1417-d484-511d-89d5-fc48a62fa10a/scratchpad/artifact-files/"
           "c59e9fc9-613c-480d-aafa-01d9bba4a47c/project")
(ROOT / "project/slides").mkdir(parents=True, exist_ok=True)

INK, PD, PU, TEAL, TEAL_L = "#211C29", "#3D2A4D", "#8C5AA6", "#146F70", "#E3F1F0"
OR, OR_D, OR_L, GREY, BG, BG2, MUT = "#C8693A", "#A8522A", "#FBEFE8", "#8A7F96", "#FAF8FB", "#F3EFF6", "#5E566A"
YEL, YEL_B = "#FFF3C4", "#E2B93B"
FONT = "'IBM Plex Sans', Arial, sans-serif"
A = dict(  # asset urls (deck asset store)
    iu="/_blob/ef32852ca25cc4586aaf4e2a696b0b00", bme="/_blob/fd5e7b707ff01f31c15f39db075966d9",
    raster="/_blob/ade731ef2aba076218e654d9272068fd", f1="/_blob/e781cc2a99d76cb25ac7ff0069c74e69",
    strip="/_blob/dbaefc3e7559d0cc9d2dd33f1e2a0842", montage="/_blob/9e3ba26dcc629d63e49d6aba4a5bdcc4",
    cloud="/_blob/fdf3f4ad70bcc18d4d66a2b4006e03a1", net="/_blob/f76a690de2a20c54ffa30a27d6e27459",
    ae="/_blob/8e8e6c894cfae4ec3130312b045e36a9", cp="/_blob/59fd5787eaac13c2197ee65f4534159f",
    f2="/_blob/8f1f0bbb621b455b7c1d4c49fe6a28bd", gae="/_blob/290a110bbc506138765424a89ab3ee9f",
    ellipse="/_blob/78b87162163fb11ad0b03021d94ff4f1", f4="/_blob/816779c071b9f0940a10875abb0ca6ad",
    f8="/_blob/5e2c9d4065aa6d24b953b877b8cab32b", f5="/_blob/3ae0cb655b34d2cc7a9fd6aa4d112342",
    shot="/_blob/68697e9eba0cb82cfbb2682a7c19eae8",
    R1="/_blob/2b36d5832ac5d2ca3e75e21a9d0dc5dd", R3="/_blob/28f00f3e61866bae05a57475b933d14d",
    R7="/_blob/13ca1d8dc1c6ca745c904267de7f1f90", R9="/_blob/38db4cf6b15cdb0c4088d8b652655610",
    R11="/_blob/ac6dc1910e124f6a53debebfeb4b9113", R12="/_blob/a4417cfab5276ec567276d9d6a9967d6",
)
SEC = f"background:{BG};color:{INK};font-family:{FONT};padding:56px 96px 140px;display:flex;flex-direction:column;gap:22px"


def header(label, title, take=None, take_col=TEAL, badge=None, badge_col=TEAL):
    b = ""
    if badge:
        bg = TEAL_L if badge_col == TEAL else OR_L
        b = (f'<p style="font-size:24px;font-weight:600;color:{badge_col};background:{bg};border-radius:24px;'
             f'padding:6px 18px;white-space:nowrap">{badge}</p>')
    lab = (f'<p style="font-size:24px;font-weight:600;letter-spacing:2px;color:{PU}">{label}</p>' if label else "")
    tk = (f'<p style="font-size:31px;font-weight:600;line-height:1.3;color:{take_col}">{take}</p>' if take else "")
    return (f'<div style="display:flex;flex-direction:column;gap:4px">{lab}'
            f'<div style="display:flex;flex-direction:row;align-items:center;gap:24px">'
            f'<h2 style="font-size:56px;font-weight:700;line-height:1.1;color:{PD}">{title}</h2><div style="flex:1"></div>{b}</div>'
            f'{tk}</div>')


def footer(page, cite=""):
    c = (f'<p style="position:absolute;left:232px;bottom:52px;width:1380px;font-size:24px;color:{GREY}">{cite}</p>'
         if cite else "")
    return (f'<hr style="position:absolute;left:96px;bottom:118px;width:1728px;border-top:1px solid #E4DCEC">'
            f'<img src="{A["iu"]}" alt="International University logo" style="position:absolute;left:96px;bottom:40px;width:56px;height:56px;object-fit:contain">'
            f'<img src="{A["bme"]}" alt="School of Biomedical Engineering logo" style="position:absolute;left:162px;bottom:40px;width:56px;height:56px;object-fit:contain">'
            f'{c}<p style="position:absolute;right:96px;bottom:52px;width:100px;font-size:24px;color:{GREY};text-align:right">{page}</p>')


def img(key, w, h, alt, bg="#FFFFFF", border=True, extra=""):
    bd = "border:1px solid #E4DCEC;" if border else ""
    return (f'<img src="{A[key]}" alt="{alt}" style="width:{w}px;height:{h}px;object-fit:contain;background:{bg};'
            f'{bd}border-radius:12px{extra}">')


def p(text, size=27, col=INK, weight=None, extra=""):
    w = f"font-weight:{weight};" if weight else ""
    return f'<p style="font-size:{size}px;line-height:1.35;color:{col};{w}{extra}">{text}</p>'


def box(text, bg, bar, size=27, col=INK):
    return (f'<p style="font-size:{size}px;line-height:1.35;color:{col};background:{bg};border-left:8px solid {bar};'
            f'border-radius:6px;padding:14px 20px">{text}</p>')


def kw(t, c=TEAL):
    return f'<span style="color:{c}"><b>{t}</b></span>'


def section(sid, body, notes, transition=True, style=SEC):
    tr = ' data-transition="fade"' if transition else ""
    return f'<section id="{sid}"{tr} style="{style}">\n{body}\n<aside>{notes}</aside>\n</section>\n'


S = {}

# 1 · Title: v3 s01 kept as it is (title, both logos, student / advisor / reviewer)
S["s01"] = (OLD / "slides/s01.html").read_text(encoding="utf-8").replace(
    "~0:10. Greet the committee, name and title only.", "0:15 · Greet the committee; name and title only.")

# 2 · Outline
rows = [("1", "Background", "Why do seizures need a review aid?"),
        ("2", "Method", "How can a model find seizures without labels?"),
        ("3", "Results", "Does it work on unseen patients?"),
        ("4", "Application", "Can a clinician use it?"),
        ("5", "Conclusion", "What was achieved?")]
r = "".join(
    f'<div style="display:flex;flex-direction:row;align-items:center;gap:36px;background:{BG2 if i % 2 == 0 else "#FFFFFF"};'
    f'border-radius:14px;padding:18px 32px"><p style="width:80px;font-size:60px;font-weight:700;color:{PU}">{n}</p>'
    f'<p style="width:420px;font-size:38px;font-weight:600;color:{PD}">{s}</p>'
    f'<p style="flex:1;font-size:30px;font-style:italic;color:{MUT}">{q}</p></div>'
    for i, (n, s, q) in enumerate(rows))
S["s02"] = section("s02", header(None, "Outline") + f'<div style="display:flex;flex-direction:column;gap:14px">{r}</div>'
                   + footer(2), "0:15 · The talk follows the clinical problem, then the method, then the evidence and the tool.")

# 3 · Epilepsy
S["s03"] = section("s03",
    header("1. BACKGROUND", "Epilepsy",
           "A seizure is a network event: synchronous activity that spreads across brain regions.")
    + '<div style="display:flex;flex-direction:row;gap:48px;align-items:center">'
    + '<div style="width:960px;display:flex;flex-direction:column;gap:10px">'
    + img("raster", 960, 417, "Schematic spike trains: neurons firing independently in normal activity and synchronously during a seizure, with their summed activity below")
    + p("When many neurons fire together, their summed activity becomes large and rhythmic enough to be recorded on the scalp.", 24, MUT)
    + '</div><div style="flex:1;display:flex;flex-direction:column;gap:22px">'
    + p(f"Epilepsy is a chronic brain disease that affects about {kw('50 million')} people worldwide; in urban Ho Chi Minh City, about {kw('5.5 in 1,000')} people live with it.", 29)
    + p(f"A seizure results from {kw('excessive electrical discharges', OR_D)} in a group of brain cells; as it spreads, it changes how brain regions {kw('interact')}, not only what one region does.", 29)
    + box(f"Up to {kw('70%')} of patients could become seizure-free with the right medicine, once their seizures are correctly identified.", TEAL_L, TEAL, 28)
    + '</div></div>' + footer(3, "WHO 2024 · Phạm &amp; Vũ 2023 · Li et al. 2022"),
    "0:40 · Start from the patient. Plant the idea that a seizure changes how regions interact; it returns on slide 9 as the reason for a graph.")

# 4 · Scalp EEG review
S["s04"] = section("s04",
    header("1. BACKGROUND", "Scalp EEG Review", "Seizures are found by eye in recordings that last for days.")
    + '<div style="display:flex;flex-direction:row;gap:40px">'
    + '<div style="width:900px;display:flex;flex-direction:column;gap:8px">'
    + img("f1", 900, 360, "One scalp EEG channel around a seizure, with background and ictal close-ups")
    + p("Example scalp EEG around a seizure (public dataset): the seizure runs from an onset to an offset.", 24, MUT)
    + '</div><div style="flex:1;display:flex;flex-direction:column;gap:16px">'
    + f'<div style="display:flex;flex-direction:row;gap:14px;align-items:start"><x-icon name="CheckCircle" style="color:{TEAL};width:44px;height:44px"></x-icon>'
    + p(f"Scalp EEG is the clinical standard for seeing seizures: it is {kw('non-invasive')}, records brain electrical activity directly and can run for days.", 27)
    + '</div>'
    + f'<div style="display:flex;flex-direction:row;gap:14px;align-items:start"><x-icon name="Warning" style="color:{OR};width:44px;height:44px"></x-icon>'
    + p(f"A trained reader scrolls every page to mark each onset and offset: reading one day of continuous EEG takes an expert about {kw('38 minutes', OR_D)}, and readers do not always agree.", 27)
    + '</div></div></div>'
    + img("strip", 1728, 130, "Schematic multi-day EEG strip with two brief seizures highlighted in orange")
    + box(f"→ Need: {kw('review triage')}: point the reader to candidate seizure intervals in a finished recording, not a real-time alarm.", TEAL_L, TEAL, 28)
    + footer(4, "Moura et al. 2014 · Shama &amp; Venkataraman 2026"),
    "0:45 · The clinician's pain point. Reading time grows with the length of the recording, not with the number of seizures. Say 'post-hoc triage, not a real-time alarm' clearly.")

# 5 · Automated detection + research question
xs = ["normal is taken from other patients or the first minutes",
      "thresholds and drift are tuned with labels",
      "the output is a window, clip or channel score, with no onset or offset",
      "tests use windows of patients seen in training"]
xl = "".join(f'<p style="font-size:25px;line-height:1.3;color:{OR_D}">✗ {t}</p>' for t in xs)
chip = f'font-size:24px;background:#FFFFFF;border:2px solid #CFC3DA;border-radius:10px;padding:6px 12px'
S["s05"] = section("s05",
    header("1. BACKGROUND", "Automated Detection",
           "Supervised models need labels; unsupervised scores stop short of seizure events.")
    + '<div style="display:flex;flex-direction:row;gap:36px">'
    + f'<div style="width:760px;display:flex;flex-direction:column;gap:14px;background:{BG2};border-radius:16px;padding:24px 28px">'
    + f'<h3 style="font-size:32px;font-weight:600;color:#5A3B75">Supervised</h3>'
    + f'<div style="display:flex;flex-direction:row;align-items:center;gap:10px"><p style="{chip}">labelled EEG</p>'
    + f'<x-shape kind="arrow-right" style="width:36px;height:20px;background:{GREY}"></x-shape><p style="{chip}">classifier</p>'
    + f'<x-shape kind="arrow-right" style="width:36px;height:20px;background:{GREY}"></x-shape><p style="{chip}">seizure / not</p></div>'
    + p("It learns what a seizure looks like from annotated seizures.", 26)
    + f'<p style="font-size:25px;line-height:1.3;color:{OR_D}">✗ It needs annotated seizures and loses accuracy on new patients: F1 69% → 37% across subjects.</p>'
    + '</div>'
    + f'<div style="flex:1;display:flex;flex-direction:column;gap:10px;background:{TEAL_L};border-radius:16px;padding:24px 28px">'
    + f'<div style="display:flex;flex-direction:row;align-items:center;gap:18px"><h3 style="font-size:32px;font-weight:600;color:{TEAL}">Unsupervised</h3><div style="flex:1"></div>'
    + img("cloud", 150, 90, "A cloud of normal points with one outlier", border=False) + '</div>'
    + p("It learns normal EEG and flags departures, so it works on a new patient from day one, but:", 26)
    + xl + '</div></div>'
    + f'<div style="display:flex;flex-direction:column;gap:4px;background:{PD};border-radius:14px;padding:18px 28px">'
    + f'<p style="font-size:24px;font-weight:600;letter-spacing:2px;color:#D9C3EA">RESEARCH QUESTION</p>'
    + f'<p style="font-size:31px;font-weight:600;line-height:1.3;color:{BG}">Can a learned anomaly score place seizure <span style="color:#F2B58E">onsets and offsets</span> in a new patient’s recording, without any seizure label of that patient?</p></div>'
    + footer(5, "Shyu et al. 2023 · Ojemann et al. 2026 · Mirzaei &amp; Singh 2025 · Ho &amp; Armanfard 2023 · Yıldız et al. 2022"),
    "0:50 · Each ✗ becomes one step of the pipeline. The F1 drop is Shyu 2023, within vs across subjects; never compare other studies' CHB-MIT accuracies with ours (B20).")

# 6 · Our study
card = lambda tag, col, bg, t1, t2: (
    f'<div style="display:flex;flex-direction:column;gap:8px;background:{bg};border-radius:16px;padding:22px 28px">'
    f'<p style="font-size:24px;font-weight:600;letter-spacing:1px;color:{col}">{tag}</p>'
    f'<p style="font-size:31px;font-weight:600;line-height:1.25">{t1}</p>'
    f'<p style="font-size:26px;line-height:1.35;color:#3E3848">{t2}</p></div>')
pill = lambda t: f'<p style="font-size:24px;border:2px solid #CFC3DA;border-radius:30px;padding:6px 20px;background:#FFFFFF">{t}</p>'
S["s06"] = section("s06",
    f'<div style="display:flex;flex-direction:row;align-items:center;gap:20px"><x-icon name="Lightbulb" style="color:{YEL_B};width:72px;height:72px"></x-icon>'
    + f'<h2 style="font-size:56px;font-weight:700;line-height:1.1;color:{PD}">Our Study</h2></div>'
    + p(f"{kw('Label-free triage')} of finished scalp EEG recordings, with seizure onsets and offsets.", 31, TEAL, 600)
    + '<div style="display:grid;grid-template-columns:1fr 1fr;gap:22px">'
    + card("OBJECTIVE 1 · REGISTERED", TEAL, TEAL_L, "An unsupervised anomaly score",
           "built from the spatial-temporal connectivity of multi-channel scalp EEG")
    + card("OBJECTIVE 2 · REGISTERED", TEAL, TEAL_L, "Onset and offset localization",
           "by non-parametric change point detection on that score")
    + card("GOAL 3 · ADDED", PU, BG2, "A channel-level explanation", "tested against a blind channel annotation")
    + card("GOAL 4 · ADDED", PU, BG2, "A review application", "that runs the whole system on complete recordings")
    + '</div><div style="display:flex;flex-direction:row;gap:14px;align-items:center;flex-wrap:wrap">'
    + p("Constraints", 26, MUT, 600) + pill("no label of the reviewed patient") + pill("events with onset and offset")
    + pill("settings fixed before testing") + pill("ordinary CPU, data stays in the hospital") + '</div>'
    + footer(6),
    "0:30 · Read Objective 1 as in the registration form, then: spatial = the graph of each window; temporal = coupling over each window and the processing of the score along time.")

# 7 · Data & evaluation
split = lambda tag, col, bg, t1, t2: (
    f'<div style="flex:1;display:flex;flex-direction:column;gap:8px;background:{bg};border-top:8px solid {col};border-radius:12px;padding:18px 22px">'
    f'<p style="font-size:24px;font-weight:600;color:{col}">{tag}</p><p style="font-size:29px;font-weight:600;line-height:1.25">{t1}</p>'
    f'<p style="font-size:25px;line-height:1.35;color:#3E3848">{t2}</p></div>')
arrow = f'<x-shape kind="arrow-right" style="width:48px;height:28px;background:{GREY};align-self:center"></x-shape>'
S["s07"] = section("s07",
    header("2. METHOD", "Data &amp; Evaluation", "Test patients are never seen during design; scoring counts seizure events.")
    + '<div style="display:flex;flex-direction:row;gap:28px;align-items:center">'
    + '<div style="width:300px;display:flex;flex-direction:column;align-items:center;gap:6px">'
    + img("montage", 290, 270, "10–20 electrode positions linked into 18 bipolar channels", border=False)
    + p("18 bipolar channels · 256 Hz · 4 s windows", 24, MUT, extra="text-align:center") + '</div>'
    + '<div style="flex:1;display:flex;flex-direction:row;gap:12px;align-items:stretch">'
    + split("DEVELOPMENT", PU, BG2, "CHB-MIT · 15 children", "12 train the autoencoder, 3 validate; every design choice is made here")
    + arrow + split("TEST", TEAL, TEAL_L, "8 unseen children", "76 seizures in 279.39 h, scored after the design was fixed")
    + arrow + split("EXTERNAL", OR_D, OR_L, "chb24 + Siena", "1 child (16 seizures) and 14 adults from another hospital (47 seizures, 141.0 h); run once")
    + '</div></div>'
    + '<div style="display:flex;flex-direction:row;gap:40px;align-items:center">'
    + '<div style="position:relative;width:900px;height:150px">'
    + f'<hr style="position:absolute;left:0;top:74px;width:900px;border-top:3px solid {GREY}">'
    + f'<div style="position:absolute;left:220px;top:30px;width:500px;height:90px;border:3px dashed {TEAL};border-radius:10px"></div>'
    + f'<p style="position:absolute;left:340px;top:42px;width:260px;height:66px;font-size:26px;font-weight:600;line-height:2.5;text-align:center;color:{BG};background:{PD};border-radius:6px">seizure</p>'
    + f'<p style="position:absolute;left:220px;top:122px;width:120px;font-size:24px;color:{TEAL};text-align:center">−30 s</p>'
    + f'<p style="position:absolute;left:600px;top:122px;width:120px;font-size:24px;color:{TEAL};text-align:center">+60 s</p>'
    + f'<div style="position:absolute;left:630px;top:4px;width:180px;height:20px;background:{OR};border-radius:4px"></div>'
    + f'<p style="position:absolute;left:740px;top:0;width:160px;font-size:24px;color:{OR_D}">detection</p></div>'
    + '<div style="flex:1;display:flex;flex-direction:column;gap:10px">'
    + p(f"A detection counts if it overlaps the seizure widened by 30 s before and 60 s after ({kw('SzCORE')}), on the {kw('continuous')} recordings.", 26)
    + p(f"Reported: sensitivity, {kw('false alarms per day')}, onset and offset error; pooled and per-patient mean.", 26)
    + '</div></div>'
    + footer(7, "Shoeb 2010 · Detti et al. 2020 · Dan et al. 2025 · ACNS 2006"),
    "0:35 · This answers the fourth gap. Detections closer than 90 s are merged; the per-patient mean is the official SzCORE aggregate. Formulas: B2.")

# 8 · Pipeline overview
steps = [("1 · Graph", "net", "A seizure changes how channels interact."),
         ("2 · Autoencoder", "ae", "A new patient has no labelled seizures, so the model learns normal coupling."),
         ("3 · Anomaly score", "cloud", "Every patient has their own normal."),
         ("4 · Alarm budget", None, "The reader needs a bounded workload."),
         ("5 · Change points", "cp", "The reader needs an onset and an offset.")]
cards = []
for i, (t, k, why) in enumerate(steps):
    vis = (img(k, 240, 150, t, border=False) if k else
           f'<x-icon name="Clock" style="color:{TEAL};width:110px;height:110px"></x-icon>')
    cards.append(f'<div style="flex:1;display:flex;flex-direction:column;align-items:center;gap:10px;background:#FFFFFF;'
                 f'border:1px solid #E4DCEC;border-radius:16px;padding:18px 16px"><div style="height:150px;display:flex;'
                 f'flex-direction:column;justify-content:center">{vis}</div>'
                 f'<p style="font-size:29px;font-weight:600;color:{TEAL};text-align:center">{t}</p>'
                 f'<p style="font-size:24px;line-height:1.3;color:#3E3848;text-align:center">because {why[0].lower() + why[1:]}</p></div>')
    if i < 4:
        cards.append(f'<x-shape kind="arrow-right" style="width:36px;height:22px;background:{GREY};align-self:center"></x-shape>')
S["s08"] = section("s08",
    header("2. METHOD", "Pipeline Overview")
    + f'<p style="font-size:31px;font-weight:600;line-height:1.3;color:{INK};background:{YEL};border:2px solid {YEL_B};border-radius:12px;padding:14px 24px">Key idea: each moment is compared with the {kw("patient’s own whole recording")}, so no seizure label is needed.</p>'
    + f'<div style="display:flex;flex-direction:row;gap:12px;align-items:stretch">{"".join(cards)}</div>'
    + '<div style="display:flex;flex-direction:row;gap:20px">'
    + f'<p style="flex:1;font-size:25px;line-height:1.35;background:{BG2};border-radius:10px;padding:12px 18px"><b>Fitted once</b> on development patients: graph rules and autoencoder.</p>'
    + f'<p style="flex:1;font-size:25px;line-height:1.35;background:{TEAL_L};border-radius:10px;padding:12px 18px"><b>Estimated per patient</b> from the whole recording, without labels: normal reference, drift and alarm budget.</p>'
    + '</div>' + footer(8),
    "0:30 · One sentence per block, each the answer to a gap of slide 5. The next three slides open blocks 1–2, 3 and 4–5.")

# 9 · Graph & autoencoder
S["s09"] = section("s09",
    header("2. METHOD", "Graph &amp; Autoencoder",
           "Each 4 s window becomes a sparse connectivity graph; a small GAE learns normal coupling.")
    + '<div style="display:flex;flex-direction:row;gap:36px">'
    + '<div style="width:846px;display:flex;flex-direction:column;gap:12px">'
    + img("f2", 846, 400, "Coupling matrix of one 4 s window between the 18 channels, and the sparse graph keeping its strongest edges")
    + p(f"Coupling of each channel pair = phase lag ({kw('wPLI')}) + amplitude envelope ({kw('AEC')}), after a common average reference. Keeping the strongest {kw('20%')} of 153 pairs gives every window the same density.", 25)
    + '</div><div style="flex:1;display:flex;flex-direction:column;gap:12px">'
    + img("gae", 846, 400, "Graph autoencoder: two graph convolutions compress each channel to a 16-number code that two decoders use to rebuild the coupling and the features")
    + p(f"Each channel enters with 30 features (coupling row, band powers, amplitude); two graph convolutions compress it to a {kw('16-number code')}. {kw('3,964')} parameters, trained on seizure-free EEG of 12 patients, run on a CPU.", 25)
    + '</div></div>'
    + footer(9, "Kipf &amp; Welling 2016 · Vinck et al. 2011 · Bruns et al. 2000"),
    "0:40 · Why a graph: slide 3. Why an autoencoder: no labels for a new patient. The decoders only train the model; the 16-number code of each channel is what the score uses.")

# 10 · Patient's own normal
S["s10"] = section("s10",
    header("2. METHOD", "Patient’s Own Normal",
           "Distance from the patient’s own whole recording separates seizures best.")
    + '<div style="display:flex;flex-direction:row;gap:36px">'
    + '<div style="width:690px;display:flex;flex-direction:column;gap:14px">'
    + img("ellipse", 690, 300, "Schematic latent space: the reference of the whole recording contains the patient's normal high-amplitude state; a reference from other patients misses it; a seizure lies far from both")
    + p(f"Per channel, a code’s {kw('distance')} from that channel’s distribution over the whole recording gives its anomaly.", 25)
    + p(f"Four spatial scales, each corrected for {kw('drift')} with a ±15 min running median per file, are averaged into {kw('one score')}.", 25)
    + f'<p style="font-size:25px;line-height:1.35;color:{OR_D}">Trade-off: it needs the finished recording, so it is not real time.</p>'
    + '</div>' + img("R9", 1002, 439, "Pooled sensitivity on development patients for each normal reference: whole recording highest in both comparisons", border=False, bg="transparent")
    + '</div>' + footer(10, "Ledoit &amp; Wolf 2004 · Ojemann et al. 2026"),
    "0:45 · The key idea of the thesis. A short baseline describes one state, so every other state looks anomalous; sensitivity rises with baseline length. Scales = 6th, 9th, 12th largest channel and the mean (B8).")

# 11 · Events & boundaries
step = lambda n, t, body: (f'<div style="display:flex;flex-direction:column;gap:8px;background:#FFFFFF;border:1px solid #E4DCEC;border-radius:14px;padding:18px 22px">'
                           f'<p style="font-size:29px;font-weight:600;color:{TEAL}">{n} · {t}</p>{p(body, 25)}</div>')
S["s11"] = section("s11",
    header("2. METHOD", "Events &amp; Boundaries",
           "A label-free budget finds events; change points place onset and offset.")
    + '<div style="display:flex;flex-direction:row;gap:36px">'
    + img("f4", 1060, 560, "First seizure of chb03: EEG around the event and the anomaly score with threshold, detector event, localized event and annotated seizure")
    + '<div style="flex:1;display:flex;flex-direction:column;gap:18px">'
    + step(4, "Alarm budget", f"The score is smoothed over 20 s, and each patient’s highest share of time is flagged: {kw('0.5% to 2%')}, estimated from the score itself; events closer than 90 s merge.")
    + step(5, "Change points", f"Within ±60 s of each event, kernel change point detection splits the score at {kw('2 points')} (before, during, after), which gives the onset and offset with no penalty to tune.")
    + '</div></div>' + footer(11, "Arlot et al. 2012 · Truong et al. 2020"),
    "0:35 · Walk the example: threshold → detector event → localized event, next to the annotated seizure. Budget equation: B9. Why not detect with change points: B10.")

# 12 · Development path
S["s12"] = section("s12",
    header("3. RESULTS", "Development Path", "Each design step removed one cause of false alarms.", badge="→ Objective 1")
    + '<div style="display:flex;flex-direction:row;justify-content:center">' + img("R1", 1560, 683, "Development step chart: pooled sensitivity 0.330, 0.489, 0.612, 0.681, 0.670, with the held-out test value 0.336", border=False, bg="transparent") + '</div>'
    + footer(12),
    "0:30 · Read the steps with the causes. The orange point: on the held-out test patients the same system reached about half, so development numbers are optimistic (record: about 2×). Designs not adopted: B11.")

# 13 · Unseen patients
res = lambda tag, col, bg, n, fa, sens, note="": (
    f'<div style="display:flex;flex-direction:column;gap:6px;background:{bg};border-left:8px solid {col};border-radius:10px;padding:16px 22px">'
    f'<p style="font-size:24px;font-weight:600;letter-spacing:1px;color:{col}">{tag}</p>'
    f'<p style="font-size:48px;font-weight:700;line-height:1.1;color:{INK}">{n} <span style="color:{MUT}">/ 76</span></p>'
    f'<p style="font-size:26px;line-height:1.3">{fa} false alarms per day</p><p style="font-size:24px;line-height:1.3;color:{MUT}">{sens}</p>{note}</div>')
S["s13"] = section("s13",
    header("3. RESULTS", "Unseen Patients",
           "About a third of unseen seizures are found; the final gain is one patient.", badge="→ Objective 1")
    + '<div style="display:flex;flex-direction:row;gap:30px">'
    + '<div style="width:470px;display:flex;flex-direction:column;gap:16px">'
    + res("HELD-OUT · MAIN ESTIMATE", TEAL, TEAL_L, 26, "22.2", "pooled 0.342 · per-patient mean 0.508")
    + res("FINAL · TEST-INFORMED", OR_D, OR_L, 37, "27.5", "pooled 0.487 · per-patient mean 0.577")
    + p("Seed 42, after the localizer. Patient bootstrap, held-out pooled (4 seeds): 0.336 [0.133, 0.670].", 24, MUT)
    + '</div>' + img("R3", 1228, 537, "Per test patient: seizures detected and false alarms per day, held-out evaluation and final system; chb15 circled", border=False, bg="transparent")
    + '</div>' + footer(13, "Efron 1979"),
    "0:55 · Lead with held-out. The final system adds the per-patient budget, designed after the held-out run; its whole gain is chb15 (0 → 11 of 20) at more false alarms. Never say 0.498 next to 0.342. Seeds and bootstrap: B13; label-dependent step: B14.")

# 14 · Onset & offset
big = lambda lab, a, b, col: (f'<div style="display:flex;flex-direction:column;gap:4px"><p style="font-size:26px;font-weight:600;letter-spacing:2px;color:{MUT}">{lab}</p>'
                              f'<p style="font-size:72px;font-weight:700;line-height:1.1;color:{col}">{a} → {b}</p></div>')
S["s14"] = section("s14",
    header("3. RESULTS", "Onset &amp; Offset", "Change points sharpen onsets, not offsets.", badge="→ Objective 2")
    + '<div style="display:flex;flex-direction:row;gap:44px;align-items:center">'
    + img("f8", 1150, 520, "Signed onset and offset errors of matched test seizures: detector boundaries versus change point localizer")
    + '<div style="flex:1;display:flex;flex-direction:column;gap:22px">'
    + big("ONSET", "32 s", "12 s", TEAL) + big("OFFSET", "20 s", "24 s", OR_D)
    + p("Median absolute error, detector → localizer; final system, 4 seeds, 146 matched seizures.", 24, MUT)
    + p("Held-out: onset 28 → 8 s, offset 16 → 20 s.", 24, MUT)
    + '</div></div>' + footer(14),
    "0:30 · About three 4 s windows at onset. The offset is not improved; a contiguous-run rule does as well (B17). 12 s is a 4-seed median, not seed 42.")

# 15 · External data
th = 'font-size:24px;color:#FFFFFF;background:#3D2A4D'
S["s15"] = section("s15",
    header("3. RESULTS", "External Data",
           "The unchanged system transfers to adults at about half the false alarms of the other label-free method.")
    + '<div style="display:flex;flex-direction:row;gap:32px">'
    + img("R11", 1040, 455, "Siena per patient: seizures detected and false alarms per day, seed 42", border=False, bg="transparent")
    + '<div style="flex:1;display:flex;flex-direction:column;gap:14px">'
    + p(f"{kw('chb24')}, a new child: {kw('14 / 16')} at 29.5 false alarms per day (seed 42).", 25)
    + p(f"{kw('Siena')}, 14 adults from another hospital: per-patient mean {kw('0.633 ± 0.079')} at 41.0 per day (4 seeds). Run once, unchanged.", 25)
    + '<table style="font-family:\'IBM Plex Sans\', Arial, sans-serif;font-size:24px;color:#211C29">'
    + '<tr style="background:#3D2A4D"><th style="width:36%;color:#FFFFFF">Siena benchmark</th><th style="width:24%;color:#FFFFFF">Labels</th><th style="width:20%;color:#FFFFFF;text-align:right">Sens.</th><th style="width:20%;color:#FFFFFF;text-align:right">FP/day</th></tr>'
    + f'<tr style="background:{TEAL_L}"><td style="color:{TEAL}"><b>This work</b></td><td>none</td><td style="text-align:right">0.633</td><td style="text-align:right">41.0</td></tr>'
    + '<tr><td>DynaSD</td><td>none</td><td style="text-align:right">0.664</td><td style="text-align:right">77.7</td></tr>'
    + f'<tr style="background:{BG2}"><td>Zhu 2023</td><td>supervised</td><td style="text-align:right">0.674</td><td style="text-align:right">15.3</td></tr>'
    + '<tr><td>EventNet</td><td>supervised</td><td style="text-align:right">0.587</td><td style="text-align:right">8.2</td></tr></table>'
    + f'<p style="font-size:24px;line-height:1.3;color:{OR_D}">Supervised entries still raise fewer false alarms: the cost of learning without labels.</p>'
    + '</div></div>' + footer(15, "EPFL ESL 2024/2026 · Ojemann et al. 2026 · Detti et al. 2020"),
    "0:40 · SzCORE benchmark on Siena, per-patient mean, entries trained on Siena excluded; our scorer implements the same rules. DynaSD's threshold came from labelled intracranial EEG. Full table: B19; per-patient false alarms: B18.")

# 16 · Limitations
chip_o = lambda t: f'<p style="font-size:24px;color:{OR_D};background:{OR_L};border-radius:24px;padding:6px 18px">{t}</p>'
S["s16"] = section("s16",
    header("3. RESULTS", "Limitations",
           "Misses rank below the patient’s own activity; channel ranking is not an onset map.", take_col=OR_D,
           badge="→ Goal 3 ✗", badge_col=OR_D)
    + '<div style="display:flex;flex-direction:row;gap:36px">'
    + '<div style="width:1060px;display:flex;flex-direction:column;gap:12px">'
    + img("f5", 1060, 420, "Test seizures by duration: annotated, detected in the held-out evaluation and by the final system")
    + p(f"Only {kw('4 of 18', OR_D)} seizures shorter than 20 s (whole 4 s windows) were detected. Missed seizures share three traits:", 25)
    + '<div style="display:flex;flex-direction:row;gap:12px;flex-wrap:wrap">'
    + chip_o("too short") + chip_o("few channels (generalized)") + chip_o("below own high-amplitude states") + '</div></div>'
    + '<div style="flex:1;display:flex;flex-direction:column;gap:10px">'
    + img("R7", 632, 533, "Channel ranking AUROC: random 0.500, this model 0.547, anatomical prior 0.739", border=False, bg="transparent")
    + p("The most anomalous channels barely match a blind annotation and rank below a fixed anatomical rule.", 24, MUT)
    + '</div></div>' + footer(16),
    "0:35 · Missed patients chb06, chb13, chb16 would need 3–4% of time flagged, above the 2% cap (B15). Channel: 0.547 [0.499, 0.597], 62 focal seizures, seed 42; without chb15 0.486 (B21). The app shows the model's anomaly per channel, not an onset map.")

# 17 · SzScan: deployment scores (R12) + 3-layer tool diagram with logos (v3 s20 markup)
old20 = (OLD / "slides/s20.html").read_text(encoding="utf-8")
arch = old20[old20.index('<div style="flex:1;display:flex;flex-direction:column;gap:10px;border:3px dashed #146F70'):old20.index('<p style="position:absolute;right:190px')]
S["s17"] = section("s17",
    header("4. APPLICATION", "SzScan",
           "One hospital workstation reruns the whole system from raw EEG, without labels.", badge="→ Goal 4")
    + '<div style="display:flex;flex-direction:row;gap:36px">'
    + '<div style="width:640px;display:flex;flex-direction:column;gap:10px">'
    + p("Where should it run? Three options scored on five criteria:", 26, PD, 600)
    + img("R12", 640, 540, "Weighted deployment scores: on-premise workstation 4.20, cloud service 3.15, bedside device 2.75", border=False, bg="transparent")
    + '</div>' + arch
    + '</div>'
    + p(f"A child’s EEG never leaves the hospital, and {kw('15 automated tests')} block every label path in the application.", 25)
    + footer(17, "Logos: Simple Icons (CC0) · icons: Health Icons (MIT)"),
    "0:30 · The workstation wins the heaviest criterion, data protection; equal weights keep the order (C4-1, answer only). Do not say 'firewalled' (C4-4). Guards: B23.")

# 18 · Live demo
S["s18"] = section("s18",
    header("4. APPLICATION", "Live Demo", "The application runs the whole system on every test patient, without labels.")
    + '<div style="display:flex;flex-direction:row;gap:36px;align-items:center">'
    + img("shot", 1120, 600, "SzScan analysis screen for chb03: score timeline, EEG around event 1 and the channel panel")
    + '<div style="flex:1;display:flex;flex-direction:column;gap:20px">'
    + p("Run on the 8 test patients from an empty database, every event exported before review:", 26)
    + f'<p style="font-size:56px;font-weight:700;line-height:1.1;color:{TEAL}">33 / 76</p>'
    + p("27.9 false alarms per day; per-patient mean 0.528 at 26.9 (seed 42)", 25, MUT)
    + f'<p style="font-size:56px;font-weight:700;line-height:1.1;color:{TEAL}">21.68 s</p>'
    + p("per hour of EEG on a laptop CPU, so one recorded day takes about 9 min", 25, MUT)
    + '</div></div>' + footer(18),
    "1:45 incl. demo 1:30 on chb03 (ingested the evening before): patient list → timeline → event 1 → EEG around onset/offset → channel panel → Accept + comment. App silent for 10 s → recording (B26). 33 vs 37: label-free normalization statistics (B14).")

# 19 · Conclusion
obj = lambda ok, t: (f'<div style="display:flex;flex-direction:row;gap:12px;align-items:center">'
                     f'<p style="width:44px;font-size:34px;font-weight:700;color:{TEAL if ok else OR_D}">{"✓" if ok else "✗"}</p>'
                     f'<p style="flex:1;font-size:25px;line-height:1.3">{t}</p></div>')
S["s19"] = section("s19",
    header("5. CONCLUSION", "Conclusion")
    + f'<div style="display:flex;flex-direction:row"><p style="font-size:34px;font-weight:700;color:{INK};background:{YEL};border:2px solid {YEL_B};border-radius:12px;padding:10px 24px">Label-free triage of finished EEG recordings</p></div>'
    + box("<b>Yes, in part.</b> Without any label of the reviewed patient, the score found about a third of unseen seizures at ~22 false alarms per day, placed onsets with change points and transferred to adults: a triage aid, not a replacement for reading.", TEAL_L, TEAL, 27)
    + '<div style="display:flex;flex-direction:row;gap:40px">'
    + '<div style="flex:1;display:flex;flex-direction:column;gap:8px">'
    + p("Objectives and goals", 26, PU, 600)
    + obj(True, "1 · Anomaly score: held-out 26 / 76 at 22.2 per day")
    + obj(True, "2 · Onsets 32 → 12 s; offsets not improved")
    + obj(False, "3 · Channel explanation: 0.547, below the prior 0.739")
    + obj(True, "4 · Application: 33 / 76 without labels, 21.68 s per hour")
    + '</div><div style="flex:1;display:flex;flex-direction:column;gap:8px">'
    + p("Contributions", 26, PU, 600)
    + p("• the patient’s whole recording as the normal reference", 25)
    + p("• a label-free alarm budget and drift correction", 25)
    + p("• change points on a learned anomaly score", 25)
    + p("• event-level tests on unseen and external patients", 25)
    + '</div></div>'
    + p("Next: shorter windows for short seizures, multichannel change points for offsets, a prospective study.", 24, MUT)
    + footer(19),
    "0:50 · Read the answer box first, then tick the objectives. Each contribution has its limit: not real time; the per-patient budget is test-informed; offsets not improved; only 8 test patients (C7-7).")

# References (2 pages)
refs = [
    "American Clinical Neurophysiology Society. (2006). Guideline 6: A proposal for standard montages to be used in clinical EEG. <i>J. Clin. Neurophysiol.</i>, 23(2), 111–117.",
    "Arlot, S., Celisse, A., &amp; Harchaoui, Z. (2012). A kernel multiple change-point algorithm via model selection. arXiv:1202.3878.",
    "Bruns, A., Eckhorn, R., Jokeit, H., &amp; Ebner, A. (2000). Amplitude envelope correlation detects coupling among incoherent brain signals. <i>NeuroReport</i>, 11(7).",
    "Dan, J., et al. (2025). SzCORE: Seizure Community Open-Source Research Evaluation framework for the validation of EEG-based automated seizure detection algorithms. <i>Epilepsia</i>, 66(S3), 14–24.",
    "Detti, P., Vatti, G., &amp; Zabalo Manrique De Lara, G. (2020). EEG synchronization analysis for seizure prediction: A study on data of noninvasive recordings. <i>Processes</i>, 8(7), 846.",
    "Efron, B. (1979). Bootstrap methods: Another look at the jackknife. <i>The Annals of Statistics</i>, 7(1).",
    "EPFL Embedded Systems Laboratory. (2024/2026). <i>SzCORE seizure detection benchmark</i> (commit c57da2f). github.com/esl-epfl/szcore",
    "Ho, T. K. K., &amp; Armanfard, N. (2023). Self-supervised learning for anomalous channel detection in EEG graphs: Application to seizure analysis. arXiv:2208.07448.",
    "Kipf, T. N., &amp; Welling, M. (2016). Variational graph auto-encoders. arXiv:1611.07308.",
    "Ledoit, O., &amp; Wolf, M. (2004). A well-conditioned estimator for large-dimensional covariance matrices. <i>J. Multivariate Analysis</i>, 88(2), 365–411.",
    "Li, Z., Hwang, K., Li, K., Wu, J., &amp; Ji, T. (2022). Graph-generative neural network for EEG-based epileptic seizure detection via discovery of dynamic brain functional connectivity. <i>Scientific Reports</i>, 12, 18998.",
    "Mirzaei, E., &amp; Singh, R. (2025). Real-time EEG-based epileptic seizure detection by one-class classification using CNN-LSTM and STFT. <i>IEEE ISBI 2025</i>, 1–4.",
    "Moura, L. M. V. R., Shafi, M. M., Ng, M., Pati, S., Cash, S. S., Cole, A. J., Hoch, D. B., Rosenthal, E. S., &amp; Westover, M. B. (2014). Spectrogram screening of adult EEGs is sensitive and efficient. <i>Neurology</i>, 83(1), 56–64.",
    "Ojemann, W. K. S., et al. (2026). Unsupervised seizure annotation and detection with neural dynamic divergence. <i>Neurology</i>. doi:10.64898/2026.02.15.26346325",
    "Phạm, H. Đ., &amp; Vũ, A. N. (2023). Tỷ lệ hiện mắc và khoảng trống điều trị động kinh tại nội thành, Thành phố Hồ Chí Minh [Epilepsy prevalence and treatment gap in urban Ho Chi Minh City]. <i>Tạp chí Y học Việt Nam</i>, 520(1B). doi:10.51298/vmj.v520i1B.3872",
    "Shama, D. M., &amp; Venkataraman, A. (2026). Bayesian uncertainty-aware deep learning with noisy labels: Tackling annotation ambiguity in EEG seizure detection. <i>PLOS One</i>, 21(6), e0352191.",
    "Shoeb, A. (2010). <i>CHB-MIT Scalp EEG Database</i> [Data set]. PhysioNet. doi:10.13026/C2K01R",
    "Shyu, K.-K., et al. (2023). Less parameterization inception-based end to end CNN model for EEG seizure detection. <i>IEEE Access</i>, 11, 49172–49182.",
    "Truong, C., Oudre, L., &amp; Vayatis, N. (2020). Selective review of offline change point detection methods. <i>Signal Processing</i>, 167, 107299.",
    "Vinck, M., et al. (2011). An improved index of phase-synchronization for electrophysiological data in the presence of volume-conduction, noise and sample-size bias. <i>NeuroImage</i>, 55(4), 1548–1565.",
    "World Health Organization. (2024). <i>Epilepsy</i> [fact sheet]. who.int",
    "Yıldız, İ., Garner, R., Lai, M., &amp; Duncan, D. (2022). Unsupervised seizure identification on EEG. <i>Comput. Methods Programs Biomed.</i>, 215, 106604.",
]
RSEC = f"background:{BG};color:{INK};font-family:{FONT};padding:56px 96px 140px;display:flex;flex-direction:column;gap:8px"
for k, (sid, chunk, page) in enumerate((("ref1", refs[:11], 20), ("ref2", refs[11:], 21))):
    body = header(None, f"References ({k + 1}/2)") + "".join(
        f'<p style="font-size:24px;line-height:1.25">{t}</p>' for t in chunk)
    if k == 1:
        body += f'<p style="font-size:24px;line-height:1.25;color:{MUT}">Icons: Health Icons (MIT licence). Tool logos: Simple Icons (CC0); trademarks belong to their owners.</p>'
    S[sid] = section(sid, body + footer(page), "Works cited on the slides only.", transition=False, style=RSEC)

# Thank you (v3 s23), page number 22
S["s23"] = (OLD / "slides/s23.html").read_text(encoding="utf-8").replace(">23</p>", ">22</p>")
if "<aside>" not in S["s23"]:
    S["s23"] = S["s23"].replace("</section>", "<aside>0:05 · Thank the committee; open for questions.</aside>\n</section>")

for sid, html in S.items():
    (ROOT / f"project/slides/{sid}.html").write_text(html, encoding="utf-8")

deck = json.loads((OLD / "deck.json").read_text(encoding="utf-8"))
backups = [x for x in deck["order"] if x.startswith("b") or x == "demo"]
deck["title"] = "Thesis Defense Slides v4"
deck["order"] = [f"s{i:02d}" for i in range(1, 20)] + ["ref1", "ref2", "s23"] + backups
deck["sections"] = {
    "title": {"description": "Title and outline", "start": "s01"},
    "background": {"description": "1. Background: epilepsy, scalp EEG review and the gap in automated detection", "start": "s03"},
    "study": {"description": "Our study: objectives and constraints", "start": "s06"},
    "method": {"description": "2. Method: data, pipeline, graph and autoencoder, patient's own normal, events", "start": "s07"},
    "results": {"description": "3. Results: development path, unseen patients, boundaries, external data, limitations", "start": "s12"},
    "application": {"description": "4. Application: SzScan and the live demo", "start": "s17"},
    "conclusion": {"description": "5. Conclusion, references and thanks", "start": "s19"},
    "backup": {"description": "Backup slides for questions", "start": backups[0]},
}
(ROOT / "project/deck.json").write_text(json.dumps(deck, ensure_ascii=False), encoding="utf-8")
print("written:", sorted(S), "| order:", len(deck["order"]))
