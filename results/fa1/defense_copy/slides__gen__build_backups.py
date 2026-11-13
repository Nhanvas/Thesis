#!/usr/bin/env python
"""Build backup slides B1-B26 (ids b01-b26) of the defense deck v4, per SLIDE_OUTLINE rev 2.1 §4 and DECK_BRIEF A4/A15/A19.
Each backup = keyword title + one answer line (<= 2 sentences) + one figure, diagram or table. Question in the notes.
Reuses the bodies of eight v3 backups (read from the files saved from the artifact)."""
import json
import re
import sys
from pathlib import Path

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/home/claude/deck_v4/root_b")
OLD = Path(sys.argv[2] if len(sys.argv) > 2 else
           "/tmp/claude-0/-home-claude/5a2f1417-d484-511d-89d5-fc48a62fa10a/scratchpad/artifact-files/"
           "c59e9fc9-613c-480d-aafa-01d9bba4a47c/project")
(ROOT / "project/slides").mkdir(parents=True, exist_ok=True)

INK, PD, PU, TEAL, TEAL_L = "#211C29", "#3D2A4D", "#8C5AA6", "#146F70", "#E3F1F0"
OR, OR_D, OR_L, GREY, BG, BG2, MUT = "#C8693A", "#A8522A", "#FBEFE8", "#8A7F96", "#FAF8FB", "#F3EFF6", "#5E566A"
FONT = "'IBM Plex Sans', Arial, sans-serif"
A = dict(iu="/_blob/ef32852ca25cc4586aaf4e2a696b0b00", bme="/_blob/fd5e7b707ff01f31c15f39db075966d9",
         f9="/_blob/2d4d5bcd3e8f6613264899019da0ef2b", gae="/_blob/290a110bbc506138765424a89ab3ee9f",
         f3="/_blob/5a21c52b9d05d21240c137ba9d7c399c", f6="/_blob/9344dc1719ef6505bb0e7f140f1c2ec9",
         f5="/_blob/3ae0cb655b34d2cc7a9fd6aa4d112342", f8="/_blob/5e2c9d4065aa6d24b953b877b8cab32b",
         R2="/_blob/1126984f7f99a953725552230c72b884", R7b="/_blob/a81e63d8710db67b5d6a7084e025f11a",
         R8="/_blob/a2e0c6cb916b3f3f11f4a854f0d89efc", R9="/_blob/38db4cf6b15cdb0c4088d8b652655610",
         R10="/_blob/14bbafe5affa8b401aecc032e85fb099", R11="/_blob/ac6dc1910e124f6a53debebfeb4b9113",
         R12="/_blob/a4417cfab5276ec567276d9d6a9967d6", R13="/_blob/663b159f369f7bc4bce59cf4c36c3b3f")
SEC = f"background:{BG};color:{INK};font-family:{FONT};padding:56px 96px 140px;display:flex;flex-direction:column;gap:20px"
FIRST_PAGE = 23  # main slides end with Thank you on page 22


def header(code, title, answer):
    return (f'<div style="display:flex;flex-direction:column;gap:4px">'
            f'<div style="display:flex;flex-direction:row;align-items:center;gap:14px">'
            f'<p style="font-size:24px;font-weight:600;letter-spacing:2px;color:{PU}">BACKUP</p>'
            f'<p style="font-size:24px;font-weight:600;color:{PD};background:#E7D6F3;border-radius:20px;padding:2px 14px">{code}</p></div>'
            f'<h2 style="font-size:52px;font-weight:700;line-height:1.1;color:{PD}">{title}</h2>'
            f'<p style="font-size:28px;font-weight:500;line-height:1.3;color:{TEAL}">{answer}</p></div>')


def footer(page, cite=""):
    c = (f'<p style="position:absolute;left:232px;bottom:52px;width:1380px;font-size:24px;color:{GREY}">{cite}</p>' if cite else "")
    return (f'<hr style="position:absolute;left:96px;bottom:118px;width:1728px;border-top:1px solid #E4DCEC">'
            f'<img src="{A["iu"]}" alt="International University logo" style="position:absolute;left:96px;bottom:40px;width:56px;height:56px;object-fit:contain">'
            f'<img src="{A["bme"]}" alt="School of Biomedical Engineering logo" style="position:absolute;left:162px;bottom:40px;width:56px;height:56px;object-fit:contain">'
            f'{c}<p style="position:absolute;right:96px;bottom:52px;width:100px;font-size:24px;color:{GREY};text-align:right">{page}</p>')


def img(key, w, h, alt, plain=False):
    st = "background:transparent" if plain else "background:#FFFFFF;border:1px solid #E4DCEC;border-radius:12px"
    return f'<img src="{A[key]}" alt="{alt}" style="width:{w}px;height:{h}px;object-fit:contain;{st}">'


def p(t, size=26, col=INK, w=None):
    ww = f"font-weight:{w};" if w else ""
    return f'<p style="font-size:{size}px;line-height:1.35;color:{col};{ww}">{t}</p>'


def kw(t, c=TEAL):
    return f'<span style="color:{c}"><b>{t}</b></span>'


def card(title, body, col=TEAL, bg="#FFFFFF"):
    return (f'<div style="flex:1;display:flex;flex-direction:column;gap:8px;background:{bg};border:2px solid #E4DCEC;'
            f'border-top:10px solid {col};border-radius:12px;padding:18px 22px">'
            f'<p style="font-size:28px;font-weight:600;color:{col}">{title}</p>{body}</div>')


def center(html):
    return f'<div style="display:flex;flex-direction:row;justify-content:center">{html}</div>'


def old_body(old_id, max_img_h=None, drop=()):
    """Inner content of a v3 backup: header bar, pinned footers and notes removed; layout kept in a wrapper div."""
    t = (OLD / f"slides/{old_id}.html").read_text(encoding="utf-8")
    sec_style = re.search(r'<section id="[^"]+" style="([^"]+)"', t).group(1)
    lay = ";".join(x for x in sec_style.split(";") if x.split(":")[0].strip() in ("flex-direction", "gap", "align-items", "justify-content"))
    inner = t[t.index(">", t.index("<section")) + 1: t.rindex("</section>")]
    inner = re.sub(r'<div style="position:absolute;left:0;top:0;width:1920px;height:120px.*?</h2></div>', "", inner, flags=re.S)
    inner = re.sub(r'<p style="position:absolute;[^"]*">.*?</p>', "", inner, flags=re.S)
    inner = re.sub(r"<aside>.*?</aside>", "", inner, flags=re.S)
    inner = inner.replace("align-self:center;", "")
    for a, b in drop:
        assert a in inner, (old_id, a[:40])
        inner = inner.replace(a, b)
    if max_img_h:
        inner = re.sub(r"(<img [^>]*?height:)(\d+)px", lambda m: m.group(1) + f"{min(int(m.group(2)), max_img_h)}px", inner)
    return f'<div style="flex:1;display:flex;{lay}">{inner.strip()}</div>'


B = []  # (title, answer, body, cite, question)

# B1 Settings fixed
li = lambda items: '<ul style="font-size:24px;line-height:1.4">' + "".join(f"<li>{x}</li>" for x in items) + "</ul>"
B.append(("Settings Fixed",
          "Every setting was fixed on development patients, or estimated per patient without labels, before the test patients were scored.",
          '<div style="display:flex;flex-direction:row;gap:24px">'
          + card("Fixed rules", li(["0.5–60 Hz, 60 Hz notch (Siena 50 Hz)", "4 s windows, no overlap",
                                    "common average reference; 0.5 wPLI + 0.5 AEC; strongest 20% of edges",
                                    "6th / 9th / 12th largest + mean", "±15 min running median", "20 s smoothing; merge 90 s",
                                    "rbf kernel, 2 change points, ±60 s"]), GREY)
          + card("Learned once (development)", li(["autoencoder 30 → 64 → 16, 3,964 parameters", "seeds 42 (main), 1, 2, 3",
                                                   "scaling of the 7 amplitude features",
                                                   "k = 4.0677, set so the median budget is 0.5%", "budget floor 0.5%, cap 2%"]), PU)
          + card("Per patient, no labels", li(["Ledoit–Wolf covariance per channel", "robust z (median, MAD)",
                                               "percentile ranks of the four members", "alarm budget from the score"]), TEAL)
          + '</div>'
          + p(f"One disclosed exception: on CHB-MIT the channel z-score statistics excluded annotated seizures and the 4 h after them; the external sets and the application use the whole recording ({kw('B14')}).", 25, MUT),
          "Report Table 21, Appendix B", "How were the parameters chosen? Was anything tuned on the test patients?"))

# B2 Event scoring
fbox = lambda name, f: (f'<div style="display:flex;flex-direction:column;gap:2px;background:#FFFFFF;border:1px solid #E4DCEC;border-radius:10px;padding:12px 18px">'
                        f'<p style="font-size:24px;color:{MUT}">{name}</p><p style="font-size:30px;font-weight:600;color:{PD}">{f}</p></div>')
B.append(("Event Scoring",
          "A detection counts when it overlaps the seizure widened by 30 s before and 60 s after; detections closer than 90 s merge.",
          '<div style="display:flex;flex-direction:row;gap:40px">' + img("f9", 860, 640, "Event scoring rules: overlap within tolerance counts, detections under 90 s apart merge, a detection outside tolerance is a false alarm")
          + '<div style="flex:1;display:flex;flex-direction:column;gap:12px">'
          + fbox("Sensitivity", "TP / (TP + FN)") + fbox("Precision", "TP / (TP + FP)") + fbox("F1", "2 TP / (2 TP + FP + FN)")
          + fbox("False alarms per day", "FP / non-seizure hours × 24")
          + p(f"Each recording is scored alone and counts are summed per patient: {kw('pooled')} uses the summed counts, the {kw('per-patient mean')} is the official SzCORE aggregate.", 24, MUT)
          + '</div></div>', "Report Figure 9, Section 2.8.1 · Dan et al. 2025", "How is a detection counted? What are the formulas?"))

# B3 Data accounting
chips = lambda ids, col, bg: "".join(f'<p style="font-size:24px;color:{col};background:{bg};border-radius:8px;padding:4px 10px">{i}</p>' for i in ids)
row = lambda tag, col, bg, ids, txt: (f'<div style="display:flex;flex-direction:row;align-items:center;gap:18px">'
                                      f'<p style="width:220px;font-size:26px;font-weight:600;color:{col}">{tag}</p>'
                                      f'<div style="width:880px;display:flex;flex-direction:row;flex-wrap:wrap;gap:8px">{chips(ids, col, bg)}</div>'
                                      f'<p style="flex:1;font-size:25px;line-height:1.3">{txt}</p></div>')
B.append(("Data Accounting",
          "Patients were split before any design step: 12 train, 3 validate, 8 are tested; chb24 and Siena were scored once.",
          '<div style="display:flex;flex-direction:column;gap:16px">'
          + row("Training", PU, BG2, ["chb01", "chb02", "chb04", "chb05", "chb07", "chb08", "chb09", "chb12", "chb19", "chb20", "chb21", "chb23"], "566.43 h · 93 seizures")
          + row("Validation", PU, BG2, ["chb10", "chb11", "chb22"], "115.82 h · 13 seizures")
          + row("Test", TEAL, TEAL_L, ["chb03", "chb06", "chb13", "chb14", "chb15", "chb16", "chb17", "chb18"], "279.39 h · 76 seizures")
          + row("External", OR_D, OR_L, ["chb24", "Siena PN00–PN17 (14 adults)"], "chb24 21.3 h · 16 seizures; Siena 141.0 h · 47 seizures")
          + '</div>'
          + p(f"Hours as listed in the CHB-MIT summary files. chb12_27/28/29 were skipped (missing one of the 18 channels, 13 seizures); five seizure-free files absent from the local copy (5.0 h). Siena hours come from the EDF signal; PhysioNet's table lists about 128 h.", 24, MUT),
          "Report Table 4, Appendix A · Shoeb 2010 · Detti et al. 2020", "How many hours and seizures? Which files were skipped?"))

# B4 Earlier protocol (v3 b12)
B.append(("Earlier Protocol",
          "The midterm number came from a timeline rebuilt without high-amplitude windows; on the continuous recordings the same system dropped to 0.303.",
          old_body("b12"), "Report Section 2.8.2", "Why did the midterm number (0.618) drop?"))

# B5 Sparsification (v3 b11)
B.append(("Sparsification",
          "Keeping the strongest 20% of edges gives every patient and state the same sparse graph and separates seizures better.",
          old_body("b11", max_img_h=560), "Report Table 5, Figure 11", "Why keep the top 20% of edges?"))

# B6 Autoencoder details
B.append(("Autoencoder Details",
          "With the same own-recording reference, a feature model reached 0.596 and the channel-level latent 0.612: the reference matters most.",
          '<div style="display:flex;flex-direction:row;gap:36px">' + img("gae", 1000, 520, "Graph autoencoder: two graph convolutions compress each channel to a 16-number code; two decoders rebuild the coupling and the features")
          + '<div style="flex:1;display:flex;flex-direction:column;gap:14px">'
          + p(f"Encoder: two graph convolutions {kw('30 → 64 → 16')}; decoders rebuild the coupling (ZZᵀ) and 12 features (16 → 32 → 12), weight λ = 0.1.", 25)
          + p("Adam 1 × 10⁻³, cosine annealing, 200 epochs, batch 32, on seizure-free windows of the 12 training patients.", 25)
          + p(f"{kw('3,964')} parameters = 1,984 + 1,040 + 940.", 25)
          + p(f"The latent distance separates seizures from high-amplitude windows (AUROC {kw('0.966')}), where reconstruction error does not ({kw('0.527–0.534', OR_D)}).", 25)
          + '</div></div>', "Report Section 2.4, Appendix B · Kipf &amp; Welling 2016", "Architecture, loss, training? Is the autoencoder needed at all?"))

# B7 Normal reference
opt = lambda t, a, b, c, col: card(t, p(a, 24) + p(b, 24) + p(c, 24, col), col)
B.append(("Normal Reference",
          "Only a reference that contains the patient’s own high-amplitude activity can rank seizures above it; the price is a finished recording.",
          '<div style="display:flex;flex-direction:row;gap:30px">' + img("R9", 1080, 473, "Pooled sensitivity per normal reference on development patients", plain=True)
          + '<div style="flex:1;display:flex;flex-direction:column;gap:12px">'
          + opt("Other patients", "no labels needed", "misses the patient's own states", "real time: yes", GREY)
          + opt("First minutes of a file", "no labels needed", "one state per file", "real time: yes", GREY)
          + opt("Whole recording", "no labels needed", "covers every state", "real time: no", TEAL)
          + '</div></div>', "Report Table 6 · Ojemann et al. 2026", "Why the whole recording as the normal reference?"))

# B8 Drift correction
B.append(("Drift Correction",
          "The score level jumps between recording files; a ±15 min running median inside each file removes the jump (0.612 → 0.681).",
          center(img("f3", 1500, 560, "Channel score of chb03 over three files, before and after subtracting the running median"))
          + p("84.5% of the highest 2% non-seizure windows lay in the top-quartile files. Only the level is removed: correcting the spread too lowered development sensitivity to 0.596.", 24, MUT),
          "Report Figure 8, Section 2.5.3, Table 10", "What is the drift and what does the correction do?"))

# B9 Alarm budget
B.append(("Alarm Budget",
          "Each patient’s budget comes from its own score: the share of time when the four members are far from normal together.",
          '<div style="display:flex;flex-direction:row;gap:30px;align-items:center">'
          + '<div style="width:640px;display:flex;flex-direction:column;gap:14px">'
          + f'<p style="font-size:34px;font-weight:600;line-height:1.4;color:{PD};background:#FFFFFF;border:1px solid #E4DCEC;border-radius:12px;padding:16px 20px">pᵢ = min(max(qᵢ, 0.5%), 2%)<br>qᵢ = share of windows with r̄ᵢ(t) &gt; k</p>'
          + p(f"r̄ᵢ(t): smoothed mean robust z of the four members. {kw('k = 4.0677')}, fixed once on the development patients (seed 42) so the median budget is 0.5%; the largest development budget was 0.011.", 24)
          + '</div>' + img("f6", 1060, 520, "Alarm budget each test seizure would need, per patient, with the 0.5% floor and 2% cap, seed 42")
          + '</div>', "Report Equation 10, Section 2.6.2, Figure 16", "How is the budget chosen without labels?"))

# B10 Change points as detector (v3 b06)
B.append(("Change Points as Detector",
          "Change points also fire at the end of every normal high state, so they place boundaries but do not detect (0.213 vs 0.479).",
          old_body("b06"),
          "Report Table 7 · Arlot et al. 2012", "Why not detect seizures with change point detection directly?"))

# B11 Designs not adopted (v3 b04)
B.append(("Designs Not Adopted",
          "Each alternative was judged under the same rule on the same development patients, and the failures are reported.",
          old_body("b04", drop=((f'<p style="font-size:30px;font-weight:600;line-height:1.3;color:#0F4F50;background:#E3F1F0;border-left:8px solid #146F70;border-radius:6px;padding:14px 22px">Each choice was judged under the same rule on the same patients; failures are reported.</p>', ""),)),
          "Report Table 10, Section 4.2", "What else was tried?"))

# B12 Against earlier systems
B.append(("Against Earlier Systems",
          "On the same continuous test recordings, the final system detects more seizures than the midterm system at well under half its false alarms.",
          center(img("R2", 1530, 670, "Test patients: sensitivity against false alarms per day for the earlier systems, the held-out evaluation, the final system and the application", plain=True)),
          "Report Sections 2.8.2, 3.3.1", "How much did the system improve over the midterm system?"))

# B13 Seeds & intervals
B.append(("Seeds &amp; Intervals",
          "Seeds change the held-out result by at most one seizure, while the patient bootstrap is wide: the uncertainty comes from the patients.",
          center(img("R10", 1530, 670, "Four seeds as dots and 95% patient bootstrap intervals, held-out and final; differences final minus held-out", plain=True)),
          "Report Table 11 · Efron 1979", "How stable are the results? How uncertain?"))

# B14 One label-dependent step
B.append(("One Label-Dependent Step",
          "Only the CHB-MIT z-score statistics excluded annotated seizures; with label-free statistics the application found one seizure fewer in four patients.",
          center(img("R8", 1530, 670, "Per test patient: seizures detected by the application with label-free statistics and by the final system", plain=True)),
          "Report Section 2.1.3, Table 17", "Is anything in the pipeline label-dependent?"))

# B15 Missed seizures
B.append(("Missed Seizures",
          "chb06, chb13 and chb16 hold 32 seizures, of which 5 were detected; each would need 3–4% of its time flagged, above the 2% cap.",
          '<div style="display:flex;flex-direction:row;gap:24px">'
          + card("Too short · chb16", p("Seizures of 6–14 s fill two to four 4 s windows, which the 20 s smoothing dilutes.", 25), OR_D, OR_L)
          + card("Few channels · chb06", p("All seizures are generalized and 12–20 s long; at the peak only 1.4 channels exceed z 3, against 6.3–15.4 in well-detected patients.", 25), OR_D, OR_L)
          + card("Below own activity · chb13", p("The patient's own high-amplitude states fill the top of the score: 89% of its highest 0.5% non-seizure windows are high amplitude.", 25), OR_D, OR_L)
          + '</div>'
          + p("Budget each patient would need (median over its seizures, seed 42): chb06 4.2%, chb13 3.0%, chb16 3.4%; well-detected patients ≤ 0.25% (B9).", 25, MUT),
          "Report Section 4.3, Figure 16", "Why were chb06, chb13 and chb16 missed?"))

# B16 Short seizures
B.append(("Short Seizures",
          "Short seizures are the main miss: 4 of 18 seizures shorter than 20 s were detected (18 by whole windows, 23 by annotation).",
          center(img("f5", 1500, 600, "Test seizures by duration: annotated, detected in the held-out evaluation and by the final system")),
          "Report Figure 12, Section 3.3.3", "How do short seizures fare?"))

# B17 Boundaries in full
tr = lambda cells, bg="": (f'<tr{" style=" + chr(34) + "background:" + bg + chr(34) if bg else ""}>' + "".join(f'<td style="text-align:{"left" if i == 0 else "right"}">{c}</td>' for i, c in enumerate(cells)) + "</tr>")
B.append(("Boundaries in Full",
          "Change points sharpen the onset on every set; the offset is not improved, and a contiguous-run rule does as well.",
          '<div style="display:flex;flex-direction:row;gap:30px">' + img("f8", 900, 420, "Signed onset and offset errors, detector versus localizer, final system, 4 seeds")
          + '<table style="font-family:\'IBM Plex Sans\', Arial, sans-serif;font-size:24px;color:#211C29">'
          + '<tr style="background:#3D2A4D"><th style="width:34%;color:#FFFFFF">Set (pairs)</th><th style="width:33%;color:#FFFFFF;text-align:right">Detector on / off</th><th style="width:33%;color:#FFFFFF;text-align:right">Localizer on / off</th></tr>'
          + tr(["Development (247)", "16 / 24 s", "4 / 16 s"]) + tr(["Held-out (103)", "28 / 16 s", "8 / 20 s"], BG2)
          + tr(["Final (146)", "32 / 20 s", "12 / 24 s"], TEAL_L) + tr(["chb24 (53)", "12 / 8 s", "4 / 4 s"]) + tr(["Siena (116)", "36 / 28 s", "20 / 28 s"], BG2)
          + '</table></div>' + p("Median absolute error over matched seizure-seed pairs of the four seeds.", 24, MUT),
          "Report Table 13, Figure 13", "Boundary errors on every set?"))

# B18 Siena per patient
B.append(("Siena per Patient",
          "Seven patients with a budget above 1.7% hold 197 of the 257 false alarms, five at the 2% cap; only PN05 has no detected seizure.",
          center(img("R11", 1530, 670, "Siena per patient: seizures detected and false alarms per day, seed 42", plain=True)),
          "Report Table 15, Section 3.4.3 · Detti et al. 2020", "Where do the external false alarms come from?"))

# B19 Benchmark in full (v3 b07, a table: A19)
B.append(("Benchmark in Full",
          "On Siena, every entry not trained on Siena is listed under the same SzCORE rules; supervised entries reach fewer false alarms.",
          old_body("b07"), "Report Table 18 · EPFL ESL 2024/2026; Chung et al. 2026; Yin &amp; Yin 2026",
          "Full benchmark table and protocols? Why no CHB-MIT comparison?"))

# B20 Prior work (v3 b13)
B.append(("Prior Work",
          "Published CHB-MIT numbers differ in labels, patients and scoring; they position the work, not rank it.",
          old_body("b13", drop=(("width:1760px", "width:1728px"),)), "Report Table 1", "How does this compare with papers on CHB-MIT?"))

# B21 Channel explanation
B.append(("Channel Explanation",
          "Only chb15 ranks above its anatomical prior; without chb15 the mean AUROC is 0.486, at chance.",
          '<div style="display:flex;flex-direction:row;gap:30px">' + img("R7b", 1180, 516, "Per test patient: channel ranking AUROC of the model and of the anatomical prior", plain=True)
          + '<div style="flex:1;display:flex;flex-direction:column;gap:14px">'
          + card("Blind annotation", p("Every channel of the 76 test seizures was marked by the author, blind to the model, and approved by the supervisor.", 24)
                 + p(f"{kw('62 focal')} seizures (1–10 channels, mean 4.55) and {kw('14 generalized', OR_D)}.", 24), PU)
          + p("Mean AUROC 0.547 [0.499, 0.597], below the prior 0.739 (seed 42).", 24, MUT)
          + '</div></div>', "Report Section 3.5, Appendix D", "How was the annotation made? How does each patient fare?"))

# B22 Deployment matrix (v3 b08) + R12
B.append(("Deployment Matrix",
          "The on-premise workstation wins the heaviest criterion, data protection, and ranks first overall.",
          old_body("b08", drop=(("width:1760px", "width:1728px"),)), "Report Table 8, Section 2.9.1", "Why on-premise? How were the weights set?"))

# B23 No labels in the app (v3 b09)
B.append(("No Labels in the App",
          "The application recomputes everything from the raw EDF; on chb03 it found 7 / 7 with the evaluation statistics and 6 / 7 with its own.",
          old_body("b09", max_img_h=600), "Report Figure 10, Section 2.9.2, Appendix E", "How do you know the application uses no labels?"))

# B24 Processing time
B.append(("Processing Time",
          "One hour of EEG takes 21.68 s on a laptop CPU without a GPU, so a recorded day takes about 9 min.",
          center(img("R13", 1440, 630, "Processing time per stage for 19 hours of EEG on a laptop CPU", plain=True))
          + p("The whole test set (279.39 h) took 5,862 s; per patient 11.79–25.40 s per hour, depending on the laptop's background load.", 24, MUT),
          "Report Table 25, Section 3.6", "How fast is it, on what hardware?"))

# B25 Registered vs delivered
reg = [("Goal", "unsupervised framework for temporal seizure localization (onset and offset)", "label-free pipeline → events with onset and offset (slides 8, 11)", True),
       ("Objective 1", "unsupervised anomaly scoring from spatial-temporal features", "GAE on per-window connectivity graphs → one ensemble score (slides 9–10, 12–13)", True),
       ("Objective 2", "localization by non-parametric change point detection on the ensemble score", "kernel change points: onset 32 → 12 s; offset not improved (slide 14)", True),
       ("Literature focus", "gaps in threshold calibration and baseline drifts", "per-patient alarm budget (B9) and drift correction (B8)", True),
       ("Validation", "event-level localization on CHB-MIT", "SzCORE events on 8 unseen patients, plus chb24 and Siena (slides 13, 15)", True)]
rows = "".join(
    f'<div style="display:flex;flex-direction:row;align-items:center;gap:16px">'
    f'<div style="width:640px;display:flex;flex-direction:column;gap:2px;background:{BG2};border-radius:10px;padding:10px 16px">'
    f'<p style="font-size:24px;font-weight:600;color:{PU}">{t}</p><p style="font-size:24px;line-height:1.3">{a}</p></div>'
    f'<x-shape kind="arrow-right" style="width:48px;height:26px;background:{GREY}"></x-shape>'
    f'<div style="flex:1;display:flex;flex-direction:row;align-items:center;gap:12px;background:{TEAL_L};border-radius:10px;padding:10px 16px">'
    f'<p style="font-size:34px;font-weight:700;color:{TEAL}">✓</p><p style="flex:1;font-size:24px;line-height:1.3">{b}</p></div></div>'
    for t, a, b, ok in reg)
B.append(("Registered vs Delivered",
          "Every item of the signed registration form is delivered; the channel explanation and the application were added.",
          f'<div style="display:flex;flex-direction:column;gap:10px">{rows}</div>'
          + p("Added goals: channel explanation not met (0.547 below the prior 0.739); review application delivered (33 / 76 without labels).", 24, MUT),
          "Thesis registration form (signed)", "Does the work meet the registration form?"))

# B26 Demo recording
B.append(("Demo Recording",
          "Fallback if the live application does not respond within 10 s.",
          f'<div style="flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;border:2px dashed #9A8FA8;border-radius:12px;background:#1E1A24">'
          f'<p style="font-size:28px;line-height:1.4;color:#EFE6F5;text-align:center">Screen recording, 1:30: chb03 patient list → timeline → event 1 → EEG around onset and offset → channel panel → Accept<br>(insert the video here in Canva)</p></div>',
          "◀ back to slide 18", "(fallback for the live demo)"))

# B27 Future work
fut = [("Short seizures missed (4 of 18 under 20 s)", "shorter or overlapping windows, with the autoencoder retrained"),
       ("Offsets not improved (24 s)", "multichannel change points, tested on new patients"),
       ("Channel ranking below the anatomical prior (0.547 vs 0.739)", "other per-channel readouts against the same blind annotation"),
       ("Label-dependent z-score statistics on CHB-MIT (33 vs 37 / 76)", "label-free statistics everywhere, as in the application and external sets"),
       ("More false alarms than supervised methods", "a supervised second stage on top of the label-free score"),
       ("Eight test patients; finished recordings only", "an independent reproduction, then a prospective hospital study")]
frows = "".join(
    f'<div style="display:flex;flex-direction:row;align-items:center;gap:16px">'
    f'<p style="width:720px;font-size:25px;line-height:1.3;color:{OR_D};background:{OR_L};border-radius:10px;padding:10px 16px">{a}</p>'
    f'<x-shape kind="arrow-right" style="width:48px;height:26px;background:{GREY}"></x-shape>'
    f'<p style="flex:1;font-size:25px;line-height:1.3;color:{INK};background:{TEAL_L};border-radius:10px;padding:10px 16px">{b}</p></div>'
    for a, b in fut)
B.append(("Future Work",
          "Each limitation points to one next step, always tested on new patients rather than on the used test set.",
          f'<div style="display:flex;flex-direction:row;gap:16px"><p style="width:720px;font-size:24px;font-weight:600;letter-spacing:1px;color:{OR_D}">LIMITATION</p>'
          f'<div style="width:48px"></div><p style="flex:1;font-size:24px;font-weight:600;letter-spacing:1px;color:{TEAL}">NEXT STEP</p></div>'
          f'<div style="display:flex;flex-direction:column;gap:12px">{frows}</div>',
          "Report Section 4.5", "What would you do next? What are the main limitations?"))

# B28 Dataset choice
dcard = lambda icon, title, col, bg, lines: (
    f'<div style="flex:1;display:flex;flex-direction:column;gap:10px;background:{bg};border-radius:14px;padding:22px 24px">'
    f'<div style="display:flex;flex-direction:row;align-items:center;gap:14px"><x-icon name="{icon}" style="color:{col};width:52px;height:52px"></x-icon>'
    f'<p style="font-size:30px;font-weight:600;color:{col}">{title}</p></div>' + "".join(p(x, 25) for x in lines) + '</div>')
B.append(("Dataset Choice",
          "CHB-MIT gives long continuous recordings of children and is named in the registration form; Siena adds adults from another hospital.",
          '<div style="display:flex;flex-direction:row;gap:24px">'
          + dcard("Database", "CHB-MIT", TEAL, TEAL_L, ["Long-term scalp EEG of children, recorded continuously over days.",
                                                         "Public on PhysioNet and used by the SzCORE standard, so the scoring is comparable.",
                                                         "Named in the registration form for event-level evaluation."])
          + dcard("Globe", "Siena", OR_D, OR_L, ["14 adults recorded at another hospital, in another country.",
                                                   "Part of the public SzCORE benchmark, so the comparison uses the same data and rules.",
                                                   "Scored once, with the system unchanged."])
          + dcard("Lock", "Ethics", PU, BG2, ["Both datasets are public and de-identified; no new recording and no patient contact.",
                                               "Recording dates are anonymised and never shown."])
          + '</div>'
          + p("chb24 is one more CHB-MIT child kept outside the split and scored once (16 seizures, 21.3 h).", 25, MUT),
          "Shoeb 2010 · Detti et al. 2020 · Dan et al. 2025", "Why CHB-MIT? Why Siena? Any ethics concerns?"))

assert len(B) == 28
ids = [f"b{i:02d}" for i in range(1, 29)]
for i, (sid, (title, ans, body, cite, q)) in enumerate(zip(ids, B)):
    html = (f'<section id="{sid}" style="{SEC}">\n' + header(f"B{i + 1}", title, ans) + body + footer(FIRST_PAGE + i, cite)
            + f"\n<aside>Q: {q}</aside>\n</section>\n")
    (ROOT / f"project/slides/{sid}.html").write_text(html, encoding="utf-8")

deck = json.loads((OLD / "deck.json").read_text(encoding="utf-8"))
deck["order"] = [x for x in deck["order"] if not (x.startswith("b") or x == "demo")] + ids
deck["sections"]["backup"] = {"description": "Backup slides B1–B28: one question, one figure or diagram each", "start": "b01"}
(ROOT / "project/deck.json").write_text(json.dumps(deck, ensure_ascii=False), encoding="utf-8")
print("backups:", len(ids), "| order:", len(deck["order"]), deck["order"][-3:])
