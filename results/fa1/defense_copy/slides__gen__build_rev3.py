#!/usr/bin/env python
"""build2.py -- rev 3 main deck (22 content slides + title, outline, references, thank you).

  python build2.py preview    -> preview2/<id>.png (plain browser: no auto-shrink, like PPTX/Canva) + overflow check
  python build2.py artifact   -> artifact/project/slides/<id>.html with /_blob/ urls

Style (approved on the pilot, 18/10): white page, Arial only, blue section label + navy title, blue footer band
with the two logos and page number, citation line above it, italic figure captions, short key phrases.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
A = "assets/"
IMG = {  # key: (blob, local file)
    "iu": ("/_blob/ef32852ca25cc4586aaf4e2a696b0b00", A + "logos/iu.png"),
    "bme": ("/_blob/fd5e7b707ff01f31c15f39db075966d9", A + "logos/bme.png"),
    "li3": ("/_blob/2ac756e4a7cbd84312f2b3b5ad56fb53", A + "li2022_fig3.png"),
    "bior": ("/_blob/a05c4bdc6d27d4d5bad0baed651f89cb", A + "biorender_eeg_generalized.png"),
    "moura": ("/_blob/7fda413f173008f443d057d298911e67", A + "moura2014_fig2A.png"),
    "montage": ("/_blob/72e67f5faf9d687d083732c5408d9475", A + "report_fig04_montage.png"),
    "prep": ("/_blob/ce08ba12afc59c2eeac9415ccd2d7770", A + "report_fig05_preproc.png"),
    "graphcd": ("/_blob/59a89d174fd5c67ff4bd08a5dd27f186", A + "report_fig07cd_graph.png"),
    "kipf": ("/_blob/d4b21d600bb4369446259bb782d24020", A + "kipf2016_gae.png"),
    "drift": ("/_blob/a6b467f27726bb3b946708209268cb3e", A + "report_fig08_drift.png"),
    "p11": ("/_blob/c03c533087fefc7a0ab8ba899bb3d304", A + "P11_example.png"),
    "szcore": ("/_blob/fdce1b2d4f597e2911e3196d0475a958", A + "szcore_fig3.png"),
    "p13s": ("/_blob/c10de73464114187fdfa16ccc851f312", A + "P13_sparsity.png"),
    "p13l": ("/_blob/791ff54574b772319ce4b0ead7dbe480", A + "P13_gae_loss.png"),
    "p14": ("/_blob/6052168e60c80e90bfc4a04e6d66cfc2", A + "P14_development.png"),
    "p15": ("/_blob/50db665bace0bb37f52ea4b4dbb65660", A + "P15_test_per_patient.png"),
    "p16": ("/_blob/f8a5ef4327a971f6505819072addfd06", A + "P16_boundaries.png"),
    "p17": ("/_blob/a53ce88895ce8b1af2b0898a41903d28", A + "P17_siena.png"),
    "p18": ("/_blob/3979955d0e4fbe0bb47bccb07fa97062", A + "P18_channel.png"),
    "p20b": ("/_blob/57753e78f2b3291891232fdd675fed2e", A + "P20_budget.png"),
    "p20d": ("/_blob/0ae9a91f269ae8c81b4b4fa98cfb6e78", A + "P20_duration.png"),
    "app": ("/_blob/5feaefc5dd86241fd300554ffe630645", A + "report_fig15b_app.png"),
    "pipe": ("/_blob/6c1ab0c101bcd65da14b29b1af483de2", A + "P07_pipeline.png"),
    "gbd": ("/_blob/bd5e40a968be5a722850ec47054cc482", A + "gbd_map.png"),
    "focal": ("/_blob/73f91824a01563e6b4fd574e26411797", A + "biorender_focal.png"),
    "d10": ("/_blob/550d97d9868f35f173253df75582bc32", A + "D10_graph.png"),
    "d11": ("/_blob/c01af35e548d498feec24b73f3924866", A + "D11_gae.png"),
    "d12": ("/_blob/12e1a657655a7af4ac76d6ed63f68fb1", A + "D12_score.png"),
    "B02": ("/_blob/f982a3d29fbe63f13b652247273e65e0", A + "bk/B02_latent.png"),
    "B03": ("/_blob/c805037e417de62c3e24a9c4f6fba50b", A + "bk/B03_history.png"),
    "B04": ("/_blob/5b6852fae48a4d57018d1740b268957f", A + "bk/B04_not_adopted.png"),
    "B05": ("/_blob/84852dcf508112be34476447ec7e1cff", A + "bk/B05_event_view.png"),
    "B06": ("/_blob/a73f261354621436e5456b533e3e4621", A + "bk/B06_budgets.png"),
    "B07": ("/_blob/fe01221d49b5ce348e2b91d972d74491", A + "bk/B07_cpd.png"),
    "B10": ("/_blob/9fec23cde1c421e6ab5e5cc51ea31ed2", A + "bk/B10_protocol.png"),
    "B11": ("/_blob/2a53884c8ea20383654cc520af2c8f35", A + "bk/B11_metrics_low.png"),
    "B12": ("/_blob/c13ada9065cb9e7e872d1c28542b1b12", A + "bk/B12_uncertainty.png"),
    "B14": ("/_blob/2323005f3d50e2afcc74301681104789", A + "bk/B14_miss_fa.png"),
    "B15": ("/_blob/d8a2d2dc182571787bd04888464d5576", A + "bk/B15_boundaries.png"),
    "B16": ("/_blob/00040739f11a8f515cadf8fced60f2d9", A + "bk/B16_labelstep.png"),
    "B18": ("/_blob/9f76d4d473f5a9158c11014b58df69af", A + "bk/B18_siena_budget.png"),
    "B20": ("/_blob/91264d49061f4901c68fdcf15a6ca948", A + "bk/B20_channels.png"),
    "B21": ("/_blob/51a7ae1ba758afc0a8de3b2e47b3299b", A + "bk/B21_labelfree.png"),
    "B22": ("/_blob/38ca2b5bde30f23672318348362e9557", A + "bk/B22_timing.png"),
    "d13": ("/_blob/324d936bb7dce6961ff3dcb1046c753c", A + "D13_app.png"),
    # tool logos (Simple Icons, CC0) already in the asset store from v4
    "react": ("/_blob/bf40933afe0f6699ac099446852b9218", ""), "vite": ("/_blob/96b6a11aa2d00bf4146e28f59fe1cc94", ""),
    "tailwind": ("/_blob/7aa9dcc49f20c0e4548f578f68768285", ""), "python": ("/_blob/e4a981bd85cc748898b8bb8cbc1d536a", ""),
    "fastapi": ("/_blob/e6ea4a7889ab3f3a47f7037468914b72", ""), "pytorch": ("/_blob/4073e32f9d1730aafe0e6bd008ffbcff", ""),
    "pyg": ("/_blob/3b68aa6f1098dfed7fcbbaec6828a5e5", ""), "sklearn": ("/_blob/edab61d0ea8988611d232b0cce7ca52c", ""),
    "numpy": ("/_blob/922387aac634ec4ad4036853827c6dd5", ""), "sqlite": ("/_blob/9807f17769fc30462a47889630faf26e", ""),
}
NAVY, BLUE, TEXT, GREY, RED, ORANGE, GREEN = "#1B2A4A", "#1F6FB2", "#1E2430", "#5F6B7A", "#C62828", "#C8641E", "#1B7F5B"
FONT = "Arial, sans-serif"
MODE = "artifact"


def img(k):
    b, l = IMG[k]
    return l if (MODE == "preview" and l) else b


def kw(t, c=BLUE):
    return f'<span style="color:{c}"><b>{t}</b></span>'


def cap(t, w=None):
    ws = f"width:{w}px;" if w else ""
    return f'<p style="{ws}font-size:22px;line-height:1.3;font-style:italic;color:{GREY}">{t}</p>'


def ul(items, size=28, gap=12, w=None):
    ws = f"width:{w}px;" if w else ""
    lis = "".join(f"<li>{i}</li>" for i in items)
    return f'<ul style="{ws}font-size:{size}px;line-height:1.35;display:flex;flex-direction:column;gap:{gap}px">{lis}</ul>'


def im(k, w, h, alt):
    src = img(k)
    if not src:   # image still to be supplied by the author: empty frame, kept size
        return (f'<img alt="{alt}" style="width:{w}px;height:{h}px;object-fit:contain;background:#EEF2F7;'
                f'border:2px dashed #9AA5B1">')
    return f'<img src="{src}" alt="{alt}" style="width:{w}px;height:{h}px;object-fit:contain">'


def take(t):
    return f'<p style="font-size:31px;line-height:1.3;font-weight:700;color:{NAVY}">{t}</p>'


def pg(sid):
    return ORDER.index(sid) + 1


def frame(sid, section, title, body, cite, page, notes="", badge=""):
    page = pg(sid)
    b = (f'<p style="font-size:30px;font-weight:700;color:{BLUE};white-space:nowrap">{badge}</p>' if badge else "")
    return f"""<section id="{sid}" data-transition="fade" style="background:#FFFFFF;color:{TEXT};font-family:{FONT};padding:44px 96px 150px;display:flex;flex-direction:column;gap:18px">
<div style="position:absolute;left:0;bottom:0;width:1920px;height:76px;background:linear-gradient(90deg, #E3EEF8 0%, #6FA6D6 45%, #1F5FA8 100%)"></div>
<div style="display:flex;flex-direction:column;gap:6px"><p style="font-size:28px;font-weight:700;letter-spacing:1px;color:{BLUE}">{section}</p><div style="display:flex;flex-direction:row;align-items:center;gap:24px"><h2 style="font-family:{FONT};font-size:54px;font-weight:700;line-height:1.1;color:{NAVY}">{title}</h2><div style="flex:1"></div>{b}</div></div>
{body}
<img src="{img('iu')}" alt="International University logo" style="position:absolute;left:96px;bottom:10px;width:56px;height:56px;object-fit:contain">
<img src="{img('bme')}" alt="School of Biomedical Engineering logo" style="position:absolute;left:162px;bottom:10px;width:56px;height:56px;object-fit:contain">
<p style="position:absolute;left:96px;bottom:90px;width:1600px;font-size:22px;color:{GREY}">{cite}</p>
<p style="position:absolute;right:96px;bottom:20px;width:120px;font-size:26px;font-weight:700;color:#FFFFFF;text-align:right">{page}</p>
<aside>{notes}</aside>
</section>
"""


def table(head, rows, widths, size=25, center_from=1):
    th = "".join(f'<th style="width:{w}%">{h}</th>' for h, w in zip(head, widths))
    trs = ""
    for i, r in enumerate(rows):
        bg = r[-1] if isinstance(r[-1], dict) else None
        cells = r[:-1] if bg else r
        style = (bg or {}).get("bg", "#F2F6FB" if i % 2 else "#FFFFFF")
        tds = "".join(f'<td style="text-align:{"center" if j >= center_from else "left"}">{c}</td>' for j, c in enumerate(cells))
        trs += f'<tr style="background:{style}">{tds}</tr>'
    return (f'<table style="font-size:{size}px;color:{TEXT}"><tr style="background:#1F5FA8;color:#FFFFFF">{th}</tr>{trs}</table>')


# ====================================================================== slides
S = {}

S["t01"] = lambda: f"""<section id="t01" style="background:linear-gradient(135deg, #2F7DC4 0%, #1F5FA8 50%, #13315C 100%);color:#FFFFFF;font-family:{FONT};padding:96px 220px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:30px">
<img src="{img('iu')}" alt="International University logo" style="position:absolute;left:96px;top:64px;width:150px;height:150px;object-fit:contain">
<img src="{img('bme')}" alt="School of Biomedical Engineering logo" style="position:absolute;right:96px;top:64px;width:150px;height:150px;object-fit:contain">
<p style="font-size:28px;font-weight:700;line-height:1.35;text-align:center;letter-spacing:1px;color:#E3EEF8">INTERNATIONAL UNIVERSITY – VNU-HCM<br>SCHOOL OF BIOMEDICAL ENGINEERING</p>
<p style="font-size:30px;font-weight:700;color:#FFFFFF">THESIS DEFENSE</p>
<h1 style="font-family:{FONT};font-size:64px;font-weight:700;line-height:1.15;text-align:center;color:#FFFFFF">Unsupervised Epileptic Seizure Temporal Localization in Scalp EEG using Graph Autoencoder and Change Point Detection</h1>
<div style="display:flex;flex-direction:row;gap:80px">
<p style="font-size:28px;line-height:1.4;color:#E3EEF8"><b>Student</b><br>Nguyen Quoc Trung Nhan · BEBEIU22184</p>
<p style="font-size:28px;line-height:1.4;color:#E3EEF8"><b>Advisor</b><br>Assoc. Prof. Ha Thi Thanh Huong</p>
<p style="font-size:28px;line-height:1.4;color:#E3EEF8"><b>Reviewer</b><br>Dr. Ngo Thi Lua</p>
</div>
<p style="font-size:26px;color:#C9DDF2">Ho Chi Minh City · November 2026</p>
<aside>0:15. Greet the committee; name and title only.</aside>
</section>
"""


def t02():
    rows = [("1", "Introduction", "Epilepsy · EEG review burden · Related work and gap · Goals"),
            ("2", "Methodology", "Study design · Datasets · Preprocessing · Graph and node features · Graph autoencoder · Anomaly score · Detection and localization · Evaluation"),
            ("3", "Results", "Graphs and training · Development · Test patients · Onset and offset · External validation · Channel explanation · Review application"),
            ("4", "Discussion", "Comparison with other studies · Deployment and impact · What limits performance"),
            ("5", "Conclusion", "Goals met · Contributions")]
    trs = "".join(f'<tr style="background:{"#F2F6FB" if i % 2 else "#FFFFFF"}"><td style="text-align:center"><b>{n}</b></td><td><b>{t}</b></td><td>{s}</td></tr>'
                  for i, (n, t, s) in enumerate(rows))
    body = (f'<table style="font-size:31px;line-height:1.5;color:{TEXT}"><tr style="background:#1F5FA8;color:#FFFFFF"><th style="width:6%">#</th>'
            f'<th style="width:22%">Section</th><th style="width:72%">Contents</th></tr>{trs}</table>')
    return frame("t02", "OUTLINE", "Table of Contents", body, "", 2, "0:15. One sentence: why, how, what came out, what it means.")


S["t02"] = t02


def m01():
    body = f"""<div style="display:flex;flex-direction:row;gap:48px">
<div style="width:820px;display:flex;flex-direction:column;gap:12px">
<p style="font-size:30px;font-weight:700;color:{NAVY}">A common chronic disease</p>
{ul([f"About {kw('50 million', RED)} people worldwide; nearly {kw('80 %')} in low- and middle-income countries", f"Up to {kw('70 %', RED)} could be seizure-free with the right medicine", f"Vietnam: about {kw('5.5 per 1,000', RED)} in urban Ho Chi Minh City"], 27, 8)}
{im('gbd', 820, 293, 'World map of epilepsy prevalence per 100 000 population by country, 2016')}
{cap('Epilepsy prevalence per 100 000 population by country, 2016. GBD 2016 Epilepsy Collaborators, 2019 (CC BY 4.0).')}
</div>
<div style="flex:1;display:flex;flex-direction:column;gap:12px">
<p style="font-size:30px;font-weight:700;color:{NAVY}">What a seizure is</p>
{ul([f"{kw('Excessive electrical discharges')} in a group of brain cells", f"{kw('Focal')} onset: networks of one hemisphere; can spread to both", f"{kw('Generalized')} onset: both hemispheres engaged rapidly"], 27, 8)}
{im('focal', 840, 350, 'EEG cap and eight electrode traces: rhythmic seizure activity on the left-hemisphere electrodes only, right hemisphere unchanged')}
{cap('Focal seizure on scalp EEG: rhythmic activity on the left-hemisphere electrodes only (schematic). Created with BioRender.com.')}
</div>
</div>
<p style="font-size:29px;line-height:1.35;font-weight:700;color:{NAVY};border-left:6px solid {RED};padding:4px 0px 4px 20px">→ A seizure arises in and spreads through {kw('brain networks', RED)}: it shows on several channels together.</p>"""
    return frame("m01", "1. INTRODUCTION", "Epilepsy", body, "World Health Organization, 2024 · GBD 2016 Epilepsy Collaborators, 2019 · Phạm &amp; Vũ, 2023 · Fisher et al., 2017", 3,
                 "0:40. Burden first (left), then what a seizure is (right). Focal and generalized are the ILAE 2017 onset types. The takeaway plants the graph idea: look at many channels together.")


S["m01"] = m01


def m02():
    body = f"""<div style="display:flex;flex-direction:row;gap:44px">
<div style="width:820px;display:flex;flex-direction:column;gap:18px">
{ul([f"Scalp {kw('EEG')}: clinical standard; each electrode records the potential under it", f"Recordings last {kw('days')}: 1 in 3 first seizures appeared only after 24 h of video-EEG", f"A reader scrolls the whole recording to mark every {kw('onset and offset')}; readers disagree on timing"], 28, 14)}
<div style="display:flex;flex-direction:column;gap:6px;background:#FFF4E5;border-left:8px solid {ORANGE};padding:16px 22px">
<p style="font-size:27px;font-weight:700;color:{ORANGE}">Evidence of the review burden</p>
<p style="font-size:26px;line-height:1.35">Conventional visual review: about {kw('38 min per 24 h', ORANGE)} of continuous EEG (118 recordings, 2,092 h, hospitalised adults; Moura et al., 2014).</p>
<p style="font-size:26px;line-height:1.35;font-style:italic">“CEEG review is very demanding and time consuming.” (Koren et al., 2018)</p>
</div>
<p style="font-size:30px;line-height:1.35;font-weight:700;color:{NAVY};border-left:6px solid {RED};padding:6px 0px 6px 20px">→ Need: {kw('review triage', RED)}. Candidate seizure intervals with onset and offset, for the reader to confirm.</p>
</div>
<div style="flex:1;display:flex;flex-direction:column;justify-content:center;gap:6px">
{im('bior', 860, 366, 'A person wearing an EEG cap, and eight electrode traces that change from background to a generalized seizure on both hemispheres')}
{cap('Scalp EEG: each electrode records the potential under it; here a generalized seizure on both hemispheres (schematic). Created with BioRender.com.')}
</div>
</div>"""
    return frame("m02", "1. INTRODUCTION", "EEG and the Review Burden", body,
                 "Moura et al., 2014 · Koren et al., 2018 · Timpte et al., 2023 · Shama &amp; Venkataraman, 2026", 4,
                 "0:40. Why recordings are long (right, bottom), what the reader does, how long it takes (evidence box). Reading time grows with the length of the recording, not with the number of seizures. Triage of a FINISHED recording, not a real-time alarm.")


S["m02"] = m02


def m03():
    rows = [("Shyu et al., 2023 · CNN", "yes (supervised)", "—", "window class", "F1 69 % → 37 % on unseen patients"),
            ("Yıldız et al., 2022 · VAE", "no", "windows of the same patients", "window score", "same patients, windows"),
            ("Ho &amp; Armanfard, 2023 · graph SSL", "no", "seizure-free corpus", "channel / clip", "channels, clips"),
            ("Ojemann et al., 2026 · DynaSD", "threshold from labelled iEEG", "first minutes of the recording", "events", "Siena, SzCORE events")]
    body = f"""{table(['Study', 'Labels used', '“Normal” learned from', 'Output', 'Evaluation'], rows, [27, 17, 21, 13, 22], 27, 1)}
<div style="display:flex;flex-direction:row;gap:40px">
<div style="width:820px;display:flex;flex-direction:column;gap:8px"><p style="font-size:28px;font-weight:700;color:{ORANGE}">Gaps for a new patient</p>
{ul(["“Normal” from other patients or a short baseline", "Threshold and drift set with labels", "Window or channel scores: no onset / offset", "Rarely scored per event on unseen patients"], 29, 10)}</div>
<div style="flex:1;display:flex;flex-direction:column;justify-content:center"><p style="font-size:30px;line-height:1.35;font-weight:700;color:{NAVY};background:#E8F1FA;border-left:8px solid {BLUE};padding:20px 24px">Research question: can a learned anomaly score place seizure {kw('onsets and offsets')} in a new patient’s recording, without any {kw('seizure label', RED)} of that patient?</p></div>
</div>"""
    return frame("m03", "1. INTRODUCTION", "Related Work and Gap", body,
                 "Shyu et al., 2023 · Yıldız et al., 2022 · Ho &amp; Armanfard, 2023 · Ojemann et al., 2026 · Report Table 1", 5,
                 "0:50. Supervised needs labels and drops on new patients; unsupervised stops at window scores. The question is the novelty: label-free events with onset and offset, scored per event on unseen patients.")


S["m03"] = m03


def m04():
    goals = [("1", "Anomaly score", "unsupervised, from the spatial-temporal connectivity of multi-channel scalp EEG", "Registered objective 1", GREEN),
             ("2", "Onset and offset", "non-parametric change point detection on the ensemble anomaly score", "Registered objective 2", GREEN),
             ("3", "Channel explanation", "checked against a blind channel annotation", "Added", GREY),
             ("4", "Review application", "runs the whole system locally on complete recordings", "Added", GREY)]
    g = "".join(f'<div style="display:flex;flex-direction:row;gap:20px;align-items:start"><p style="width:60px;height:60px;font-size:34px;font-weight:700;color:#FFFFFF;background:{BLUE};border-radius:50%;text-align:center;line-height:1.75">{n}</p>'
                f'<div style="flex:1;display:flex;flex-direction:column;gap:4px"><p style="font-size:23px;font-weight:700;color:{c}">{tag}</p><p style="font-size:30px;line-height:1.35">{kw(t)}: {d}</p></div></div>' for n, t, d, tag, c in goals)
    body = f"""<div style="display:flex;flex-direction:row;gap:60px">
<div style="width:1040px;display:flex;flex-direction:column;gap:24px"><p style="font-size:31px;font-weight:700;color:{NAVY}">Four goals <span style="font-weight:400;color:{GREY}">· aim: localize seizure onset and offset without labels</span></p>{g}</div>
<div style="flex:1;display:flex;flex-direction:column;gap:14px;background:#F2F6FB;padding:28px 32px"><p style="font-size:30px;font-weight:700;color:{NAVY}">Design requirements</p>
{ul(["No seizure label of the reviewed patient", "Events with onset and offset", "One model for every new patient", "Bounded review load", "Settings fixed before testing", "Ordinary CPU; data stay in the hospital", "Every number traceable to a result file"], 28, 16)}</div>
</div>"""
    return frame("m04", "1. INTRODUCTION", "Thesis Goals", body, "Report Section 1.4 and Table 2", 6,
                 "0:30. The signed registration form has one aim and two objectives = Goals 1 and 2; Goals 3 and 4 were added. Goal 1 spatial = graph of each window; temporal = coupling over each 4 s window and processing of the score along time.")


S["m04"] = m04


def m05():
    body = f"""{im('pipe', 1658, 700, 'Processing pipeline: preprocessing and graph construction, graph autoencoder, ensemble anomaly score, detection and change point localization, connected in one flow')}
{cap('Processing pipeline (report Fig. 6, redrawn horizontally): one flow from the raw recording to seizure events with onset and offset.')}"""
    return frame("m05", "2. METHODOLOGY", "Study Design Overview", body, "", 7,
                 "0:30. Follow the arrows once: graph per window, autoencoder, score, events. Orange = fitted once on training patients; P = estimated per patient from its own recording, without labels; dashed = training only.")


S["m05"] = m05


def m06():
    rows = [("Training", "12 CHB-MIT", "566.43", "93", "train the autoencoder; design"),
            ("Validation", "3 CHB-MIT", "115.82", "13", "monitor training; design"),
            ("Test", "8 CHB-MIT", "279.39", "76", "held-out and final evaluation"),
            ("External", "chb24 (added after the 23)", "21.3", "16", "scored once, unchanged"),
            ("External", "Siena, 14 adults", "141.0", "47", "scored once, unchanged")]
    body = f"""<div style="display:flex;flex-direction:row;gap:40px">
<div style="flex:1;display:flex;flex-direction:column;gap:8px"><p style="font-size:30px;font-weight:700;color:{NAVY}">CHB-MIT <span style="color:{GREY};font-weight:400">· Boston Children’s Hospital, PhysioNet</span></p>
{ul(["24 cases of children: 23 original + chb24 added later", "256 Hz · 10–20 system, 18 bipolar derivations", "Long continuous recordings; every seizure has onset and offset"], 26, 6)}</div>
<div style="flex:1;display:flex;flex-direction:column;gap:8px"><p style="font-size:30px;font-weight:700;color:{NAVY}">Siena Scalp EEG <span style="color:{GREY};font-weight:400">· University of Siena, PhysioNet</span></p>
{ul(["14 adults (8 men 25–71 y, 6 women 20–58 y); another hospital", "512 Hz → 256 Hz · referential → 18 bipolar · notch 50 Hz", "Seizure times read with the SzCORE converter"], 26, 6)}</div>
</div>
<div style="display:flex;flex-direction:row;gap:36px;align-items:start">
<div style="width:1300px;display:flex;flex-direction:column;gap:8px">
{table(['Set', 'Patients', 'Hours', 'Seizures', 'Used for'], rows, [14, 28, 11, 11, 36], 25, 2)}
<p style="font-size:24px;color:{TEXT}">Split {kw('by patient')} before any training (chb01 and chb21 are one child: both in training).</p></div>
<div style="flex:1;display:flex;flex-direction:column;gap:4px">{im('montage', 380, 360, '10-20 electrode layout with the 18 bipolar derivations drawn as arrows')}{cap('18 bipolar derivations (report Fig. 4).')}</div>
</div>"""
    return frame("m06", "2. METHODOLOGY", "Datasets", body, "Shoeb, 2010 · Detti et al., 2020 · EPFL ESL epilepsy2bids · Report Table 4", 8,
                 "0:40. Test patients were never used to train; chb24 was added to the archive after the original 23 and kept out of every design step; Siena is another hospital and adults. Hours: summary files (scored hours slightly lower, Appendix A).")


S["m06"] = m06


def m07():
    body = f"""<div style="display:flex;flex-direction:row;gap:44px">
<div style="width:1000px;display:flex;flex-direction:column;gap:6px">{im('prep', 1000, 666, 'EEG of chb10 before and after filtering and z-scoring, and the power spectrum of P7-O1 with the 60 Hz peak removed')}
{cap('chb10: (a) raw, (b) filtered and z-scored, (c) spectrum of P7-O1, 60 Hz peak removed. Report Fig. 5.')}</div>
<div style="flex:1;display:flex;flex-direction:column;gap:12px">
{"".join(f'<div style="display:flex;flex-direction:column;gap:2px;background:#F2F6FB;border-left:6px solid {BLUE};padding:10px 18px"><p style="font-size:26px"><b style="color:{BLUE}">{n}.</b> {a}</p><p style="font-size:22px;color:{GREY}">→ {b}</p></div>' for n, a, b in [
 (1, f"Band-pass {kw('0.5–60 Hz')}, 4th order, zero phase", "removes slow drift and fast noise without shifting the waveform"),
 (2, f"Notch {kw('60 Hz')} (Siena 50 Hz)", "removes power-line interference"),
 (3, f"Non-overlapping {kw('4 s windows')} (1,024 samples)", "one graph per window"),
 (4, f"Per-patient {kw('channel z-score')}", "one scale across channels and recordings")])}
<p style="font-size:23px;color:{GREY}">Files missing a derivation skipped (3 chb12 files).</p>
<p style="font-size:24px;line-height:1.35;color:{ORANGE}">CHB-MIT z-score statistics exclude annotated seizures: the only step that touches labels; its effect is measured (B13).</p>
</div></div>"""
    return frame("m07", "2. METHODOLOGY", "Preprocessing", body, "Report Section 2.1.3", 9,
                 "0:30. Waveforms keep their shape; only the scale changes. Disclose the z-score statistics: application run with label-free statistics gives 33 instead of 37 of 76.")


S["m07"] = m07


def keyline(t, c=RED):
    return (f'<p style="font-size:29px;line-height:1.35;font-weight:700;color:{NAVY};border-left:6px solid {c};'
            f'padding:4px 0px 4px 20px">{t}</p>')


def m08():
    body = f"""{im('d10', 1728, 650, 'One 4 s window: edges from wPLI and AEC coupling after common average reference, strongest 20 percent kept; node features of 18 adjacency-row values, 5 relative band powers and 7 absolute features')}
{keyline(f"→ One graph per 4 s window: {kw('edges')} = coupling; {kw('nodes')} = each channel’s own activity, {kw('amplitude', ORANGE)} included.")}"""
    return frame("m08", "2. METHODOLOGY", "Graph Construction and Node Features", body,
                 "Nunez et al., 1997 · Vinck et al., 2011 · Bruns et al., 2000 · Welch, 1967 · Report Section 2.3, Fig. 7", 10,
                 f"0:45. Top row = edges; bottom row = node features. CAR only before the coupling. Strongest 20 % gives the same density in every state. The 7 absolute features were added because relative features erase the amplitude rise: first large gain (slide {pg('m14')}).")


S["m08"] = m08


def m09():
    body = f"""{im('d11', 1728, 630, 'Graph autoencoder of this thesis: two graph convolution layers 30 to 64 to 16, latent 18 by 16, inner-product adjacency decoder and MLP feature decoder used only in training, loss MSE of adjacency plus 0.1 MSE of features')}
{keyline(f"→ Learns normal coupling from {kw('seizure-free')} windows of the 12 training patients; {kw('3,964', RED)} parameters run on a CPU.")}"""
    return frame("m09", "2. METHODOLOGY", "Graph Autoencoder", body, "Kipf &amp; Welling, 2016, 2017 · Report Section 2.4, Table 21", 11,
                 "0:45. Why an autoencoder: a new patient has no labelled seizures, so learn normal coupling. Two GCN layers: each channel mixes in its graph neighbours. Decoders exist only to train the encoder; only Z is used afterwards. Adam 1e-3, cosine, 200 epochs, batch 32; validation loss on 3 patients; 4 seeds, 42 is the main one.")


S["m09"] = m09


def m10():
    body = f"""{im('d12', 1728, 650, 'Ensemble anomaly score: per channel squared Mahalanobis distance of the latent from the patient own recording and robust z; four members across channels; drift correction per file shown on chb03; percentile and mean give the ensemble score')}
{keyline(f"Key idea: “normal” = the patient’s {kw('own whole recording')}, so no label is needed; the cost is {kw('no real-time use', ORANGE)}.", BLUE)}"""
    return frame("m10", "2. METHODOLOGY", "Ensemble Anomaly Score", body,
                 "Ledoit &amp; Wolf, 2004 · Leys et al., 2013 · Report Sections 2.5.2–2.5.4, Fig. 8", 12,
                 "0:50. Top row per channel: distance from the patient's own normal, robust z. Bottom: four spatial members (a seizure raises several channels, a bad electrode one); drift correction per file (real chb03 member: level jumps between files are removed, seizures stay); percentile and mean = one score. Short baselines fit one state only (backup).")


S["m10"] = m10


def m11():
    body = f"""<div style="display:flex;flex-direction:row;gap:44px">
<div style="width:980px;display:flex;flex-direction:column;gap:6px">{im('p11', 980, 600, 'Ensemble anomaly score around one chb03 seizure with the patient threshold, the detector event and the localized event')}
{cap('Illustration on one recorded seizure (chb03): score, threshold, detector event and localized event. Data of report Fig. 14a.')}</div>
<div style="flex:1;display:flex;flex-direction:column;gap:14px">
<p style="font-size:29px;font-weight:700;color:{NAVY}">Detection</p>
{ul(["Smooth 20 s (5 windows)", f"Per-patient {kw('alarm budget')}: p = clip(q, 0.5 %, 2 %)", "q from the score itself, no labels", "Above the threshold → events; merge &lt; 90 s"], 27, 8)}
<p style="font-size:29px;font-weight:700;color:{NAVY}">Localization</p>
{ul([f"{kw('Kernel change points')} (rbf) on event ± 60 s", "Exactly 2 change points → onset, offset", "No penalty to tune"], 27, 8)}
</div></div>"""
    return frame("m11", "2. METHODOLOGY", "Detection and Localization", body, "Arlot et al., 2012 · Truong et al., 2020", 13,
                 "0:35. Change points as the detector also fire at the END of every high state (0.213 vs 0.479, backup); so the threshold finds events and change points place their boundaries. k = 4.0677 is in the backup.")


S["m11"] = m11


def m12():
    rows = [("Development", "15 CHB-MIT", "every design choice"), ("Held-out", "8 test", "main estimate, scored once"),
            ("Final", "8 test", "+ per-patient budget: test-informed"), ("External", "chb24, Siena", "scored once, unchanged"),
            ("Application", "8 test", "the app, no labels")]
    body = f"""<div style="display:flex;flex-direction:row;gap:44px">
<div style="width:860px;display:flex;flex-direction:column;gap:6px">{im('szcore', 860, 422, 'Event-based scoring: tolerance before and after the reference seizure, merging of nearby detections, a detection outside is a false positive')}
{cap('Event-based scoring: tolerance, merging, false alarm. Dan et al., 2025 (SzCORE), Fig. 3.')}
{ul(["Hit: overlap with the seizure widened 30 s before, 60 s after", "Merge events &lt; 90 s apart; split events &gt; 5 min"], 27, 8)}</div>
<div style="flex:1;display:flex;flex-direction:column;gap:14px">
{ul([f"Sensitivity, precision, F1, {kw('false alarms per day')}", f"Pooled and {kw('per-patient mean')} (SzCORE official)", "Seed 42 + 4-seed mean; patient bootstrap"], 27, 8)}
{table(['Evaluation', 'Patients', 'Role'], rows, [30, 26, 44], 24, 3)}
</div></div>"""
    return frame("m12", "2. METHODOLOGY", "Evaluation", body, "Dan et al., 2025 · EPFL ESL SzCORE benchmark · Efron, 1979", 14,
                 "0:35. Specificity is undefined per event, so false alarms per day replace it. Every number later carries set, seed and aggregate.")


S["m12"] = m12


def m13():
    body = f"""<div style="display:flex;flex-direction:row;gap:30px">
<div style="width:1000px;display:flex;flex-direction:column;gap:4px">{im('p13s', 1000, 470, 'Graph density and seizure-background separation per test patient for a fixed threshold and for the strongest 20 percent of edges')}
{cap('8 test patients. Report Fig. 11.')}</div>
<div style="flex:1;display:flex;flex-direction:column;gap:4px">{im('p13l', 680, 460, 'Training and validation loss of the graph autoencoder over 200 epochs for four seeds')}
{cap('Autoencoder loss, 4 seeds (bold: seed 42).')}</div></div>
{ul([f"Strongest 20 %: density {kw('0.196')} for every patient (fixed threshold: 0.92–0.97); separation higher in {kw('8 / 8')} test patients", f"Loss converges in all 4 seeds; validation stays flat → {kw('no overfitting')}", f"Latent distance separates seizures from high-amplitude windows: AUROC {kw('0.966', RED)} vs reconstruction error 0.53 (development)"], 27, 8)}"""
    return frame("m13", "3. RESULTS", "Graphs and Training", body, "Report Section 3.1, Table 5, Section 4.2", 15,
                 "0:30. Validation loss is higher than training because it is other patients, not because of overfitting: it does not rise.")


S["m13"] = m13


def m14():
    body = f"""{take(f"The patient’s own recording, the 7 absolute features and drift correction gave the largest gains.")}
{im('p14', 1728, 664, 'Pooled sensitivity on the development patients for five normal references and for each added component, from 0.330 to 0.670')}
<p style="font-size:24px;color:{GREY}">15 development patients, 4 seeds, pooled sensitivity at ≤ 25 false alarms per day. Development is optimistic: the held-out test reached about half (0.336 vs 0.662).</p>"""
    return frame("m14", "3. RESULTS", "Development and Ablation", body, "Report Tables 6, 9, 10", 16,
                 "0:35. (a) is the reference choice; (b) adds one component at a time. Designs tried and rejected: backup.")


S["m14"] = m14


def m15():
    rows = [("Seizures detected", "26 / 76", "37 / 76"), ("Sensitivity", "0.342 / 0.508", "0.487 / 0.577"),
            ("Precision", "0.092 / 0.108", "0.104 / 0.118"), ("F1 score", "0.145 / 0.174", "0.172 / 0.190"),
            ("False alarms per day", "22.2 / 21.8", "27.5 / 26.8")]
    body = f"""{take(f"Held-out: {kw('26 of 76', RED)} unseen seizures at {kw('22.2', RED)} false alarms per day; the final gain is {kw('one patient', RED)}.")}
<div style="display:flex;flex-direction:row;gap:40px">
<div style="width:760px;display:flex;flex-direction:column;gap:14px">
{table(['Seed 42', 'Held-out', 'Final (test-informed)'], rows, [40, 30, 30], 26, 1)}
<p style="font-size:22px;line-height:1.35;color:{GREY}">Pooled / per-patient mean, after the localizer. Held-out, 4 seeds: 0.336 ± 0.008; patient bootstrap [0.133, 0.670].</p>
{ul([f"{kw('Held-out')}: designed on development, scored once", f"{kw('Final', ORANGE)}: + per-patient budget, designed with test information"], 26, 8)}
</div>
<div style="flex:1;display:flex;flex-direction:column;gap:6px">
{im('p15', 864, 590, 'Per test patient, seizures detected and false alarms per day for the held-out and final evaluations; chb15 boxed in red, 0 to 11 of 20')}
{cap('8 test patients, seed 42. Red: chb15, the only patient whose detections changed.')}
</div></div>"""
    return frame("m15", "3. RESULTS", "Test Patients", body, "Dan et al., 2025 · Efron, 1979 · Report Tables 11, 12", 17,
                 "0:55. Lead with held-out. The interval of the final gain starts at zero. Why precision is low: seizures are 0.4 % of the time. Why modest: slide " + str(pg("m21")) + ".", "→ Goal 1")


S["m15"] = m15


def m16():
    body = f"""{take(f"Change points cut the onset error from {kw('32 s to 12 s', RED)}; the offset is not improved.")}
{im('p16', 1728, 576, 'Signed onset and offset errors of the detector boundaries and of the change point localizer, final system, four seeds')}
{cap('Final system, 146 matched seizure–seed pairs (4 seeds); red line = annotated boundary. Report Fig. 13.')}
{ul(["Median absolute error, final: onset 32 → 12 s · offset 20 → 24 s; held-out: onset 28 → 8 s · offset 16 → 20 s", "A simple contiguous-run rule gives 16 s offsets → multichannel change points are the next step"], 26, 6)}"""
    return frame("m16", "3. RESULTS", "Onset and Offset", body, "Arlot et al., 2012 · Report Table 13", 18,
                 "0:30. Always say 4 seeds for 12 s. Offsets end late (+16 s median bias).", "→ Goal 2")


S["m16"] = m16


def m17():
    body = f"""{take(f"On data never used in design, the system transferred from children to {kw('adults')} of another hospital.")}
<div style="display:flex;flex-direction:row;gap:40px">
<div style="width:1080px;display:flex;flex-direction:column;gap:6px">{im('p17', 1080, 600, 'Siena per patient: seizures detected and false alarms per day; PN05 has none of three detected; PN06, PN07 and PN16 exceed 70 false alarms per day')}
{cap('Siena, 14 adults, seed 42. Red: missed patient and &gt; 70 false alarms per day.')}</div>
<div style="flex:1;display:flex;flex-direction:column;gap:18px">
<p style="font-size:28px;line-height:1.35"><b>chb24</b> (child, never used):<br>{kw('14 / 16', RED)} at 29.5 false alarms/day</p>
<p style="font-size:28px;line-height:1.35"><b>Siena</b> (adults):<br>per-patient mean {kw('0.633 ± 0.079', RED)} at {kw('41.0', RED)} /day (4 seeds)</p>
<p style="font-size:26px;line-height:1.35;color:{ORANGE}">False alarms concentrate in patients with large budgets (PN06, PN07, PN16)</p>
</div></div>"""
    return frame("m17", "3. RESULTS", "External Validation", body, "Detti et al., 2020 · Report Tables 14, 15", 19,
                 "0:40. Run once with no change. Seed 42 Siena: 33 of 47. Comparison with other methods: slide " + str(pg("m20")) + ".")


S["m17"] = m17


def m18():
    body = f"""{take(f"The channel ranking agrees with a blind annotation only slightly above chance, below an anatomical prior.")}
<div style="display:flex;flex-direction:row;gap:40px">
<div style="width:940px;display:flex;flex-direction:column;gap:6px">{im('p18', 940, 640, 'Per test patient, channel ranking AUROC of the model and of an anatomical prior; only chb15 is above its prior')}
{cap('62 focal test seizures, seed 42; number of seizures in brackets. Report Table 24.')}</div>
<div style="flex:1;display:flex;flex-direction:column;gap:18px">
{ul([f"Mean AUROC {kw('0.547', RED)} [0.499, 0.597]", f"Anatomical prior {kw('0.739')}; random 0.500", "Only chb15 above its prior; without it 0.486", "Blind, every-channel annotation, approved by the supervisor"], 27, 12)}
<p style="font-size:27px;line-height:1.35;color:{ORANGE}"><b>→ Goal 3 not met.</b> The app shows the model’s channel anomaly, not an onset map.</p>
</div></div>"""
    return frame("m18", "3. RESULTS", "Channel-Level Explanation", body, "Report Section 3.5, Table 16", 20,
                 "0:30. A pre-registered negative, reported as it came out. It decided the neutral title of the app panel.", "→ Goal 3")


def logo(k, alt):
    return f'<img src="{img(k)}" alt="{alt}" style="width:46px;height:46px;object-fit:contain">'


S["m18"] = m18


def m19():
    body = f"""<div style="display:flex;flex-direction:row;gap:36px">
<div style="width:900px;display:flex;flex-direction:column;gap:4px">{im('d13', 900, 661, 'SzScan architecture on one hospital workstation: React browser, FastAPI server running the frozen thesis code in three stages on the CPU, SQLite and a disk cache')}</div>
<div style="flex:1;display:flex;flex-direction:column;gap:8px">
{im('app', 790, 529, 'SzScan review screen: timeline of the anomaly score, EEG around a detected event, and the channel-level anomaly panel')}
{cap('SzScan, chb03, event 1: EEG around the event and the channel panel. Report Fig. 15b.')}
{ul([f"8 test patients, 231 files, no labels: {kw('33 / 76', RED)} at 27.9 false alarms/day (per-patient mean 0.528)", f"{kw('21.68 s', RED)} per hour of EEG on a laptop CPU, about 9 min per recorded day"], 25, 8)}
</div></div>"""
    return frame("m19", "3. RESULTS", "Review Application SzScan", body, "Report Sections 2.9, 3.6 · Logos: Simple Icons (CC0)", 0,
                 "0:30 + live demo 1:30 (chb03, Recording 1, Event 1). The app reruns the frozen thesis code from the raw EDF and never reads a label. If the app is silent for 10 s, play the backup video. 33 vs 37 = label-free normalisation (backup). Do not say firewalled.", "→ Goal 4")


S["m19"] = m19


def m20():
    rows = [("<b>This work</b>", "none of the patient", "0.633", "0.160", "0.226", "41.0", {"bg": "#E3F1E8"}),
            ("DynaSD (Ojemann, 2026)", "threshold: labelled iEEG", "0.664", "0.126", "0.170", "77.7"),
            ("Transformer (Zhu, 2023)", "supervised, TUH", "0.674", "0.484", "0.479", "15.3"),
            ("EventNet (2024)", "supervised, TUH", "0.587", "0.578", "0.526", "8.2")]
    body = f"""{take(f"Same data and rules: similar sensitivity to the only label-free method at {kw('half its false alarms', RED)}; supervised methods raise fewer.")}
<div style="display:flex;flex-direction:row;gap:40px">
<div style="width:1060px;display:flex;flex-direction:column;gap:8px">
<p style="font-size:27px;font-weight:700;color:{NAVY}">Siena, SzCORE benchmark (per-patient mean)</p>
{table(['Method', 'Labels', 'Sens.', 'Prec.', 'F1', 'FA/day'], rows, [30, 28, 10, 10, 10, 12], 25, 2)}
<p style="font-size:22px;color:{GREY}">Entries trained on Siena excluded. This work: 4 seeds, own implementation of the scoring rules. Full table: backup.</p></div>
<div style="flex:1;display:flex;flex-direction:column;gap:10px">
<p style="font-size:27px;font-weight:700;color:{NAVY}">Why CHB-MIT papers report 90–100 %</p>
{ul(["Labels; often the same patients; windows", "Supervised, unseen patients: F1 69 % → 37 % (Shyu, 2023)", "Supervised, per event, leave-one-out: 75 % at ~115 FA/day (Ali, 2024)", "SzCORE challenge leader: 37 % at ~1 FA/day (Dan, 2026)"], 25, 8)}
</div></div>"""
    return frame("m20", "4. DISCUSSION", "Comparison with Other Studies", body,
                 "EPFL ESL SzCORE benchmark, 2024/2026 · Shyu et al., 2023 · Ali et al., 2024 · Dan et al., 2026", 22,
                 "0:40. Like-for-like only on Siena. The cost of no labels is more false alarms than supervised methods trained elsewhere. Never call it state of the art.")


S["m20"] = m20


def m20b():
    B = lambda x: f'<b style="color:{GREEN}">{x}</b>'
    rows = [("Patient data protection · societal", "30 %", "2", B("5"), "4"),
            ("Cost to the hospital · economic", "25 %", "3", B("4"), "2"),
            ("Processing time before review · technical", "20 %", "5", B("4"), "2"),
            ("Hardware and energy · environmental", "15 %", "2", B("4"), "3"),
            ("Maintenance and scaling · global", "10 %", "5", B("3"), "2"),
            ("<b>Weighted total</b>", "", "3.15", B("4.20 ✔"), "2.75", {"bg": "#E3F1E8"})]
    day = (f'<div style="width:720px;height:44px;background:#DCE6F2;position:relative;display:flex;flex-direction:row">'
           f'<div style="width:16px;height:44px;background:{RED}"></div></div>')
    body = f"""{take(f"Processing on the hospital’s own workstation keeps a child’s EEG {kw('on site')}; the reviewer starts from about {kw('31 minutes', RED)} of candidates per recorded day.")}
<div style="display:flex;flex-direction:row;gap:44px">
<div style="width:960px;display:flex;flex-direction:column;gap:8px">
<p style="font-size:27px;font-weight:700;color:{NAVY}">Deployment decision matrix (scores 1–5)</p>
{table(['Criterion', 'Weight', 'Cloud service', 'On-premise workstation', 'Bedside device'], rows, [40, 11, 15, 19, 15], 24, 1)}
<p style="font-size:22px;color:{GREY}">Weights set by engineering judgment. Report Table 8.</p></div>
<div style="flex:1;display:flex;flex-direction:column;gap:12px">
<p style="font-size:27px;font-weight:700;color:{NAVY}">One recorded day (24 h)</p>
{day}
<p style="font-size:24px;line-height:1.3"><span style="color:{RED}"><b>2.2 %</b></span> flagged ≈ 31 min to review first · prepared in ≈ 9 min on a laptop CPU</p>
<p style="font-size:27px;font-weight:700;color:{GREEN}">Who benefits</p>
{ul(["Patients whose recordings wait longest for a reader", "Sites without labels, GPU or cloud: where nearly 80 % of people with epilepsy live"], 24, 6)}
<p style="font-size:27px;font-weight:700;color:{ORANGE}">Who bears the risk</p>
{ul(["Patients with missed seizures: the reviewer must still read everything", "The reviewer: 27.5 false alarms per day (final, seed 42)"], 24, 6)}
</div></div>"""
    return frame("m20b", "4. DISCUSSION", "Deployment and Impact", body,
                 "Report Sections 2.9.1, 4.6 · World Health Organization, 2024", 0,
                 "0:40. Data protection weighs most because this is a child's EEG. Proof of concept on public data: clinical use needs a prospective study and regulatory review. Energy was not measured; the environmental score is qualitative.")


S["m20b"] = m20b


def m21():
    rows = [("Sensitivity: short seizures", "4 / 18 under 20 s; 4 s windows + 20 s smoothing", "shorter or overlapping windows, retrain"),
            ("Sensitivity: seizures under the patient’s own activity", "chb06, chb13, chb16: 5 of 32 found; need 3–4 % budget", "representation that separates seizures from high-amplitude states"),
            ("False alarms", "62–91 % of top non-seizure windows are high amplitude", "supervised second stage when labels exist"),
            ("Offsets; 8 test patients", "offsets late by 16 s; wide bootstrap", "multichannel change points; new patients, prospective study")]
    body = f"""<div style="display:flex;flex-direction:row;gap:30px">
<div style="width:960px;display:flex;flex-direction:column;gap:2px">{im('p20b', 960, 400, 'Alarm budget needed per test seizure; seizures of chb06, chb13 and chb16 need more than the 2 percent cap')}
{cap('Budget a threshold would need to reach each seizure (seed 42). Report Fig. 16.')}</div>
<div style="flex:1;display:flex;flex-direction:column;gap:2px">{im('p20d', 720, 390, 'Seizures detected by duration; only 4 of 18 seizures shorter than 20 s')}
{cap('Detection by duration. Report Fig. 12.')}</div></div>
{table(['Limit', 'Measured cause', 'Next step'], rows, [27, 38, 35], 23, 9)}"""
    return frame("m21", "4. DISCUSSION", "What Limits Performance", body, "Report Sections 4.3, 4.5", 23,
                 "0:40. Missed seizures are a ranking problem inside the patient, not a threshold problem: a 2 % budget for all costs four times the alarms (backup).")


S["m21"] = m21


def m22():
    goals = [("✓ Met", GREEN, "1 · Anomaly score", "26 / 76", "at 22.2 false alarms/day (held-out, seed 42); Siena 0.633 at 41.0 (4 seeds)"),
             ("~ Partly", ORANGE, "2 · Onset and offset", "32 → 12 s", "onset error with change points; offset not improved"),
             ("✗ Not met", RED, "3 · Channel explanation", "0.547", "below the anatomical prior 0.739"),
             ("✓ Met", GREEN, "4 · Review application", "21.68 s", "per hour of EEG, no labels; 33 / 76")]
    g = "".join(f'<div style="flex:1;display:flex;flex-direction:column;gap:6px;background:#F7F9FC;border-top:6px solid {c};padding:16px 20px">'
                f'<p style="font-size:24px;font-weight:700;color:{c}">{st}</p><p style="font-size:26px;font-weight:700;color:{NAVY}">{t}</p>'
                f'<p style="font-size:44px;font-weight:700;color:{c}">{v}</p><p style="font-size:22px;line-height:1.3">{d}</p></div>' for st, c, t, v, d in goals)
    contrib = [("Own recording as the reference", "each patient’s whole recording defines its normal, read per channel"),
               ("Label-free threshold and drift", "a per-patient alarm budget and a ±15 min drift correction, without labels"),
               ("Change points on a learned score", "onset and offset of every event, not only window scores"),
               ("Tested like a reviewer sees it", "every event on unseen and external patients; a local app that reads no label")]
    c = "".join(f'<div style="width:810px;display:flex;flex-direction:row;gap:14px;align-items:start"><p style="width:44px;height:44px;font-size:24px;font-weight:700;color:#FFFFFF;background:{BLUE};border-radius:50%;text-align:center;line-height:1.85">{k + 1}</p>'
                f'<p style="flex:1;font-size:24px;line-height:1.3"><b style="color:{NAVY}">{a}</b>: {b}</p></div>' for k, (a, b) in enumerate(contrib))
    body = f"""<p style="font-size:30px;line-height:1.35;font-weight:700;color:{NAVY};background:#E8F1FA;border-left:8px solid {BLUE};padding:14px 22px">{kw('Label-free triage of finished EEG recordings', RED)}: without any label of the reviewed patient, the system found about a third of unseen seizures at about 22 false alarms per day and placed their onsets. It points the reader to candidates; it does not replace reading.</p>
<div style="display:flex;flex-direction:row;gap:20px">{g}</div>
<p style="font-size:28px;font-weight:700;color:{NAVY}">Contributions</p>
<div style="display:flex;flex-direction:row;flex-wrap:wrap;gap:14px 60px">{c}</div>"""
    return frame("m22", "5. CONCLUSION", "Conclusion", body, "", 24, "0:50. Answer the research question first, then each goal (held-out first; seed 42), then the four contributions against the gaps of slide 5.")


S["m22"] = m22

REFS = [
    "Ali, E., Angelova, M., &amp; Karmakar, C. (2024). Epileptic seizure detection using CHB-MIT dataset: The overlooked perspectives. <i>R. Soc. Open Sci.</i>, 11(5), 230601.",
    "Arlot, S., Celisse, A., &amp; Harchaoui, Z. (2012). A kernel multiple change-point algorithm via model selection. arXiv:1202.3878.",
    "BioRender.com. EEG recording of seizure (focal; generalized), templates by M. Nashed.",
    "Bruns, A., Eckhorn, R., Jokeit, H., &amp; Ebner, A. (2000). Amplitude envelope correlation detects coupling among incoherent brain signals. <i>NeuroReport</i>, 11(7).",
    "Dan, J., et al. (2025). SzCORE: Seizure Community Open-Source Research Evaluation framework. <i>Epilepsia</i>, 66(S3), 14–24 (arXiv:2402.13005).",
    "Dan, J., Shahbazinia, A., Kechris, C., &amp; Atienza, D. (2026). Quantifying the generalization gap in seizure detection. arXiv:2505.18191.",
    "Detti, P., Vatti, G., &amp; Zabalo Manrique De Lara, G. (2020). EEG synchronization analysis for seizure prediction. <i>Processes</i>, 8(7), 846.",
    "Efron, B. (1979). Bootstrap methods: Another look at the jackknife. <i>Ann. Stat.</i>, 7(1).",
    "EPFL Embedded Systems Laboratory. (2024/2026). SzCORE seizure detection benchmark (c57da2f); epilepsy2bids (d3fb175). github.com/esl-epfl",
    "Ho, T. K. K., &amp; Armanfard, N. (2023). Self-supervised learning for anomalous channel detection in EEG graphs. arXiv:2208.07448.",
    "Kipf, T. N., &amp; Welling, M. (2016). Variational graph auto-encoders. arXiv:1611.07308; (2017) Semi-supervised classification with GCNs. arXiv:1609.02907.",
    "Leys, C., Ley, C., Klein, O., Bernard, P., &amp; Licata, L. (2013). Detecting outliers: do not use standard deviation around the mean, use absolute deviation around the median. <i>J. Exp. Soc. Psychol.</i>, 49(4), 764–766.",
    "Ledoit, O., &amp; Wolf, M. (2004). A well-conditioned estimator for large-dimensional covariance matrices. <i>J. Multivar. Anal.</i>, 88(2), 365–411.",
    "Fisher, R. S., et al. (2017). Operational classification of seizure types by the ILAE. <i>Epilepsia</i>, 58(4), 522–530.",
    "GBD 2016 Epilepsy Collaborators. (2019). Global, regional, and national burden of epilepsy, 1990–2016. <i>Lancet Neurol.</i>, 18(4), 357–375.",
    "Koren, J. P., et al. (2018). Automated long-term EEG review: fast and precise analysis in critical care patients. <i>Front. Neurol.</i>, 9, 454.",
    "Moura, L. M. V. R., et al. (2014). Spectrogram screening of adult EEGs is sensitive and efficient. <i>Neurology</i>, 83(1), 56–64.",
    "Nunez, P. L., et al. (1997). EEG coherency. <i>Electroencephalogr. Clin. Neurophysiol.</i>, 103(5), 499–515.",
    "Ojemann, W. K. S., et al. (2026). Unsupervised seizure annotation and detection with neural dynamic divergence. <i>Neurology</i>.",
    "Phạm, H. Đ., &amp; Vũ, A. N. (2023). Tỷ lệ hiện mắc và khoảng trống điều trị động kinh tại nội thành TP. Hồ Chí Minh. <i>Tạp chí Y học Việt Nam</i>, 520(1B).",
    "Shama, D. M., &amp; Venkataraman, A. (2026). Bayesian uncertainty-aware deep learning with noisy labels. <i>PLOS One</i>, 21(6), e0352191.",
    "Shoeb, A. (2010). <i>CHB-MIT Scalp EEG Database</i>. PhysioNet. doi:10.13026/C2K01R",
    "Shyu, K.-K., et al. (2023). Less parameterization inception-based end to end CNN model for EEG seizure detection. <i>IEEE Access</i>, 11, 49172–49182.",
    "Timpte, K., et al. (2023). Assessing 72 h vs. 24 h of long-term video-EEG monitoring. <i>Front. Neurol.</i>, 14, 1281652.",
    "Truong, C., Oudre, L., &amp; Vayatis, N. (2020). Selective review of offline change point detection methods. <i>Signal Process.</i>, 167, 107299.",
    "Vinck, M., et al. (2011). An improved index of phase-synchronization for electrophysiological data. <i>NeuroImage</i>, 55(4), 1548–1565.",
    "Welch, P. (1967). The use of FFT for the estimation of power spectra. <i>IEEE Trans. Audio Electroacoust.</i>, 15(2), 70–73.",
    "World Health Organization. (2024). <i>Epilepsy</i> [fact sheet].",
    "Yıldız, İ., Garner, R., Lai, M., &amp; Duncan, D. (2022). Unsupervised seizure identification on EEG. <i>Comput. Methods Programs Biomed.</i>, 215, 106604.",
    "Chung, Y. G., Cho, A., Kim, H., &amp; Kim, K. J. (2024). Single-channel seizure detection with clinical confirmation of seizure locations using CHB-MIT dataset. <i>Front. Neurol.</i>, 15, 1389731.",
    "Chung, Y. G., Cho, J., Cho, A., Kim, H., &amp; Lim, B. C. (2026). Patient-independent automated pediatric seizure monitoring. <i>Clin. Exp. Pediatr.</i>, 69(8), 665–675.",
    "Mirzaei, E., &amp; Singh, R. (2025). Real-time EEG-based epileptic seizure detection by one-class classification using CNN-LSTM and STFT. IEEE ISBI 2025.",
    "Yin, H., &amp; Yin, X. (2026). Montage-guided fusion network for long-term scalp EEG seizure detection. <i>Front. Neuroinform.</i>, 20, 1942480.",
    "Zhu, P., et al. (2024). A novel SE-TCN-BiGRU hybrid network for automatic seizure detection. <i>IEEE Access</i>, 12, 127328.",
    "Tool logos: Simple Icons (CC0); trademarks belong to their owners.",
]


def refs(sid, part, items, page):
    ps = "".join(f'<p style="font-size:20.5px;line-height:1.22">{r}</p>' for r in items)
    return frame(sid, "REFERENCES", f"References ({part}/2)", f'<div style="display:flex;flex-direction:column;gap:6px">{ps}</div>', "", page, "Works cited on the main and backup slides.")


REFS = sorted(REFS[:-1], key=lambda r: r.replace("BioRender", "Biorender").lower()) + REFS[-1:]
S["ref1"] = lambda: refs("ref1", 1, REFS[:18], 25)
S["ref2"] = lambda: refs("ref2", 2, REFS[18:], 26)
S["t99"] = lambda: f"""<section id="t99" data-transition="fade" style="background:linear-gradient(135deg, #2F7DC4 0%, #1F5FA8 50%, #13315C 100%);color:#FFFFFF;font-family:{FONT};padding:128px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:32px">
<img src="{img('iu')}" alt="International University logo" style="position:absolute;left:96px;top:64px;width:130px;height:130px;object-fit:contain">
<img src="{img('bme')}" alt="School of Biomedical Engineering logo" style="position:absolute;right:96px;top:64px;width:130px;height:130px;object-fit:contain">
<h1 style="font-family:{FONT};font-size:96px;font-weight:700;line-height:1.1;text-align:center;color:#FFFFFF">Thank you for your attention</h1>
<p style="font-size:36px;color:#E3EEF8">Questions and discussion</p>
<p style="position:absolute;right:96px;bottom:34px;width:100px;font-size:26px;color:#C9DDF2;text-align:right">{pg('t99')}</p>
<aside>Thank the committee; open for questions.</aside>
</section>
"""

# ====================================================================== backup slides (rev 3, 19/10)
TEAL = "#146F70"


def bq(q):
    return f'<p style="font-size:26px;font-style:italic;color:{GREY}">Q: {q}</p>'


def ans(t):
    return (f'<p style="font-size:29px;line-height:1.35;font-weight:700;color:{NAVY};border-left:6px solid {TEAL};'
            f'padding:4px 0px 4px 20px">{t}</p>')


def fig(k, alt, w=1728, h=600):
    return f'<div style="display:flex;flex-direction:row;justify-content:center">{im(k, w, h, alt)}</div>'


def bk(sid, n, title, q, body, cite, notes):
    return frame(sid, f"BACKUP · B{n}", title, bq(q) + body, cite, 0, notes)


def card(head, items, c=BLUE, bg="#F2F6FB", w=None, size=25):
    ws = f"width:{w}px;" if w else "flex:1;"
    return (f'<div style="{ws}display:flex;flex-direction:column;gap:10px;background:{bg};border-top:6px solid {c};padding:18px 22px">'
            f'<p style="font-size:27px;font-weight:700;color:{c}">{head}</p>{ul(items, size, 6)}</div>')


def b01():
    body = f"""{ans("Every setting was fixed on the 15 development patients before the test patients were scored; only the per-patient budget used test information, and it is reported apart.")}
<div style="display:flex;flex-direction:row;gap:24px">
{card("Fixed design constants", ["4 s windows · 0.5–60 Hz, notch", "A = 0.5 wPLI + 0.5 AEC, strongest 20 %", "GCN 30 → 64 → 16 · λ = 0.1", "drift ±15 min · smoothing 20 s · merge 90 s", "budget k = 4.0677, limits 0.5–2 %", "localizer: event ± 60 s, 2 change points"], NAVY)}
{card("Learned once (12 training patients)", ["GAE weights: 3,964 parameters", "seizure-free windows only", "scaling of the 7 absolute features", "200 epochs, last epoch kept"], ORANGE, "#FFF4E5")}
{card("Per patient, own recording, no labels", ["channel z-score statistics*", "μ<sub>c</sub>, Σ<sub>c</sub> (Ledoit–Wolf) · median, MAD", "running medians · percentiles", "budget q<sub>i</sub> from the score", "change points of each event"], TEAL, "#E3F1F0")}
</div>
<p style="font-size:23px;color:{GREY}">* CHB-MIT statistics exclude annotated seizures (the only label-dependent step, B13). Held-out = all fixed; final = + per-patient budget, designed with test information.</p>"""
    return bk("b01", 1, "Settings Fixed Before Testing", "Was anything tuned on the test patients?", body,
              "Report Sections 2.1–2.6, 2.8.2, Table 21",
              "Answer: no setting was tuned on test for the held-out evaluation; the per-patient budget of the final system was designed after the held-out look and is labelled test-informed. Development optimism is about 2× (B11).")


def b02():
    body = f"""{ans("The latent distance separates seizures from the patient’s own high-amplitude windows; the reconstruction error does not.")}
{fig('B02', 'GAE encoder to latent Z; reconstruction error AUROC 0.527 to 0.534, latent distance 0.966, per-channel readout 0.622 versus graph mean 0.553', 1728, 560)}
<p style="font-size:24px;line-height:1.35">Why a graph: a seizure changes how channels <b>interact</b>. Why an autoencoder: a new patient has <b>no labels</b>, so the model learns normal coupling. The reference matters most: a feature density with the same reference reached 0.596.</p>"""
    return bk("b02", 2, "Why a Graph Autoencoder", "Why a graph autoencoder and not a simpler model?", body,
              "Report Section 4.2 · Kipf &amp; Welling, 2016",
              "AUROC on development: seizure windows versus high-amplitude non-seizure windows. 0.622 vs 0.553 = channel vs graph-mean latent, 2 seeds. A full feature-only system with all later steps was not built: future work.")


def b03():
    body = f"""{ans("CHB-MIT gives long continuous scalp recordings with every onset and offset; Siena adds adults from another hospital and a public benchmark on the same data.")}
<div style="display:flex;flex-direction:row;gap:24px">
{card("CHB-MIT (development + test)", ["Long continuous recordings, 18 bipolar channels", "Every seizure has onset and offset", "Widely used → results can be placed", "Children: 23 cases + chb24"], BLUE)}
{card("Siena (external)", ["Another hospital, 14 adults", "Part of the SzCORE benchmark", "→ the only like-for-like comparison", "Run once, no change"], TEAL, "#E3F1F0")}
{card("Next data", ["TUH corpus: larger, many sites → future work", "A prospective hospital study before any clinical use"], ORANGE, "#FFF4E5")}
</div>
<p style="font-size:23px;color:{GREY}">Both datasets are public and anonymised on PhysioNet; no new recording was made. Split by patient before any training.</p>"""
    return bk("b03", 3, "Dataset Choice", "Why CHB-MIT and Siena?", body,
              "Shoeb, 2010 · Detti et al., 2020 · EPFL ESL SzCORE benchmark",
              "Hours and seizures per set: slide 8. 5 missing CHB-MIT files (0.7 % of hours) were seizure-free (report App. A).")


def b04():
    f = lambda a, b: (f'<div style="display:flex;flex-direction:column;gap:6px;background:#F2F6FB;padding:16px 22px;border-left:6px solid {BLUE}">'
                      f'<p style="font-size:26px;font-weight:700;color:{NAVY}">{a}</p><p style="font-size:30px">{b}</p></div>')
    body = f"""{ans("All metrics are counted per seizure event with the SzCORE rules, per recording, then summed per patient.")}
<div style="display:flex;flex-direction:row;gap:30px">
<div style="width:900px;display:flex;flex-direction:column;gap:14px">
{f("Sensitivity", "TP / (TP + FN)")}{f("Precision", "TP / (TP + FP)")}{f("F1", "2 TP / (2 TP + FP + FN)")}{f("False alarms per day", "FP / non-seizure hours × 24")}
</div>
<div style="flex:1;display:flex;flex-direction:column;gap:14px">
<p style="font-size:27px;font-weight:700;color:{NAVY}">Worked example: held-out, seed 42</p>
{ul(["TP 26 · FN 50 · FP 257", "Sensitivity 26 / 76 = 0.342", "Precision 26 / 283 = 0.092", "F1 52 / 359 = 0.145", "257 / 277.6 h × 24 = 22.2 per day"], 27, 8)}
<p style="font-size:24px;line-height:1.35"><b>Pooled</b>: counts summed over patients. <b>Per-patient mean</b>: metric per patient, then the mean (SzCORE official).</p>
<p style="font-size:24px;line-height:1.35">Specificity is undefined per event, so false alarms per day replace it.</p>
</div></div>"""
    return bk("b04", 4, "Metric Formulas", "How are the metrics computed?", body,
              "Dan et al., 2025 · Report Section 2.8.1",
              "TP: an event overlapping the seizure widened 30 s before and 60 s after; events < 90 s apart merged, > 5 min split. Counts come from the scorer, never from a hand formula; the example reproduces Table 11.")


def b05():
    body = f"""{ans("A window metric ranks thousands of 4 s windows; the reviewer needs seizure events with onset, offset and a false-alarm rate.")}
{fig('B05', 'One hour of chb03: 900 window scores with 14 seizure windows, and the same hour as one event overlapping the annotated seizure', 1728, 580)}
<p style="font-size:24px">Window gains did not carry over to events, so every design choice was judged on events.</p>"""
    return bk("b05", 5, "Why Event Metrics", "Why event metrics and not window AUROC?", body,
              "Dan et al., 2025 · Ali et al., 2024 · data of report Fig. 8 (chb03, seed 42)",
              "Window AUROC is used only for mechanism checks (0.966 vs 0.53 on slide 15). Seizures are 0.4 % of test time, so a window ranking says little about how many seizures a reviewer would see.")


def b06():
    body = f"""{ans("The budget is read from the score itself: it moves review time between patients without enlarging it on average.")}
<div style="display:flex;flex-direction:row;gap:30px;align-items:center">
<div style="width:700px;display:flex;flex-direction:column;gap:12px;background:#F2F6FB;padding:20px 24px">
<p style="font-size:30px">p<sub>i</sub> = min(max(q<sub>i</sub>, 0.5 %), 2 %)</p>
<p style="font-size:26px;line-height:1.35">q<sub>i</sub> = share of the patient’s windows where the smoothed mean robust z of the 4 members exceeds <b>k = 4.0677</b></p>
<p style="font-size:24px;line-height:1.35;color:{GREY}">k calibrated once on the 15 development patients so that the median q<sub>i</sub> = 0.5 %; largest development budget 1.1 %</p>
</div>
<div style="flex:1">{im('B06', 960, 420, 'Alarm budget per test patient: chb15 at the 2 percent cap, others between 0.50 and 0.82 percent')}</div></div>
<p style="font-size:24px;color:{ORANGE}">Only chb15 reached the cap, so the whole final gain (0 → 11 of 20) is one patient: test-informed.</p>"""
    return bk("b06", 6, "Alarm Budget", "How is the threshold set without labels?", body,
              "Report Section 2.6.2, Eq. 10, Table 12",
              "Floor 0.5 % = the held-out budget (≈ 7.2 min per day). One 2 % budget for all patients reached chb15 but cost about 4× the alarms on development (95.1 vs 23.8 per day, B8).")


def b07():
    body = f"""{ans("Change points place the boundaries; used as the detector they also fire when a high-amplitude state ends (0.213 vs 0.479, development).")}
<div style="display:flex;flex-direction:row;gap:30px;align-items:center">
<div style="width:1080px">{im('B07', 1080, 620, 'chb03 seizure: detector event from the smoothed score and the event after two change points on the unsmoothed score within event plus or minus 60 seconds')}</div>
<div style="flex:1;display:flex;flex-direction:column;gap:14px">
{ul(["Search window: event ± 60 s", "Exactly 2 change points → onset, offset", "rbf kernel, bandwidth from the data: no penalty to tune", "Input: the unsmoothed score (smoothing blurs boundaries)"], 26, 10)}
</div></div>"""
    return bk("b07", 7, "Change Points: Localizer", "Why not detect seizures with change points?", body,
              "Arlot et al., 2012 · Truong et al., 2020 · Report Tables 7, 10",
              "0.213 vs 0.479: change-point segmentation vs threshold detector on the earlier score, development. A change point is a change in either direction; the threshold finds rises.")


def b08():
    body = f"""{ans("Every alternative was scored with the same rule on the development patients; none gave a gain worth its cost.")}
{fig('B04', 'Designs evaluated and not adopted: normal reference, readout, drift, detection and localization alternatives against the kept design', 1728, 640)}"""
    return bk("b08", 8, "Designs Not Adopted", "What else did you try?", body, "Report Table 10",
              "Fine-tuning per patient: +0.006 (2 seeds) without lowering non-seizure scores. One 2 % budget: 0.803 but 95.1 false alarms per day. Multichannel change points: offset 8 vs 16 s but lower sensitivity.")


def b09():
    body = f"""{ans("Before this system, an earlier GAE pipeline and its extensions were tested and dropped; every step is kept in the experiment record.")}
{fig('B03', 'Four stages: first pipeline with an LSTM branch, earlier three-readout system, levers tried, and the rebuilt system of this thesis', 1728, 500)}
<p style="font-size:23px;color:{GREY}">Stages 1–3 are from the experiment record (validation-gated, earlier protocol); only stage 4 is reported as the thesis system.</p>"""
    return bk("b09", 9, "Earlier Explorations", "Did you try other models, e.g. temporal or directed graphs?", body,
              "Experiment record · Report Section 2.8.2",
              "LSTM branch: training code lost, outputs not reproducible → dropped. Transfer-entropy (directed) edges helped single patients but not the event result. Say 'from the experiment record' if asked for the source.")


def b10():
    body = f"""{ans("The earlier 0.618 came from a timeline rebuilt from the annotations; on the continuous recording the same system gave 0.303 at 73.3 false alarms per day.")}
{fig('B10', 'Schematic: continuous recording with high-amplitude windows versus a timeline rebuilt from annotations with those windows replaced', 1728, 520)}
<p style="font-size:23px;color:{GREY}">Schematic. The rebuilt timeline removed the high-amplitude windows that cause most false alarms, so it overestimated; every result of this thesis uses the continuous recording.</p>"""
    return bk("b10", 10, "Earlier Evaluation Protocol", "Why is the result lower than the midterm number?", body,
              "Report Section 2.8.2",
              "Same earlier system, same operating point. This is why the whole system was rebuilt and evaluated only on continuous recordings.")


def b11():
    body = f"""{ans("Precision and F1 are low because false alarms outnumber seizures; most false alarms are the patient’s own high-amplitude states, not seizures nearby.")}
{fig('B11', 'Held-out and final counts of detected, missed and false alarms with precision and F1, and the high-amplitude share of the top non-seizure windows per test patient', 1728, 560)}
<p style="font-size:24px;line-height:1.35">Seizures are 0.4 % of test time. Development was about twice the test (0.662 → 0.336, 4 seeds). Misses: short seizures and seizures below the patient’s own activity (slide 24).</p>"""
    return bk("b11", 11, "Why the Metrics Are Low", "Why are sensitivity, precision and F1 so low?", body,
              "Report Sections 3.3, 4.1, 4.3, Table 11",
              "The low values answer the gap honestly: no label of the patient, unseen patients, every event counted. Supervised methods trained elsewhere raise fewer alarms (slide 22). ≤ 11 % of these windows lie within 10 min of a seizure.")


def b12():
    body = f"""{ans("Seeds change the held-out result by at most one seizure; the patient bootstrap is wide, so the uncertainty is the 8 patients, not the model.")}
{fig('B12', 'Four seeds of held-out and final pooled sensitivity with the patient bootstrap interval 0.133 to 0.670, and the final gain +0.141 with interval 0.000 to 0.333', 1728, 540)}
<p style="font-size:24px">The interval of the final gain starts at zero: the gain is one patient (chb15).</p>"""
    return bk("b12", 12, "Seeds and Intervals", "How stable and how certain are the results?", body,
              "Efron, 1979 · Report Table 11",
              "Held-out 4 seeds 0.336 ± 0.008 (seed 42: 0.342). Bootstrap: 10,000 patient resamples, 4-seed mean. Seed SD is not uncertainty.")


def b13():
    body = f"""{ans("One step used labels: CHB-MIT z-score statistics exclude annotated seizures. With label-free statistics (the application), 33 instead of 37 of 76 were found.")}
{fig('B16', 'Per test patient, detected seizures and false alarms for the final system and the application with label-free statistics; one fewer in chb03, chb06, chb15 and chb16', 1728, 560)}
<p style="font-size:24px">The external tests and the application already used label-free statistics.</p>"""
    return bk("b13", 13, "One Label-Dependent Step", "Is any part of the pipeline label-dependent?", body,
              "Report Sections 2.1.3, 3.6, Table 17",
              "Effect measured: 37 → 33 of 76, 318 → 323 false alarms. Disclosed in the report.")


def b14():
    body = f"""{ans("The missed seizure lasts two 4 s windows, shorter than the 20 s smoothing; the false alarm is 132 s of high-amplitude activity far from any seizure.")}
{fig('B14', 'Left: shortest missed seizure of chb16, EEG and score below the threshold. Right: highest-scoring false alarm of chb03, EEG and score above the threshold', 1728, 620)}"""
    return bk("b14", 14, "A Missed Seizure and a False Alarm", "Can you show a miss and a false alarm?", body,
              "Report Fig. 14c–d (selected by fixed rules)",
              "The figure alone cannot show what caused the false alarm (high amplitude is not the same as artifact). chb06 and chb16 seizures last 6–20 s.")


def b15():
    body = f"""{ans("Change points cut the onset error on every set; the offset improves on development and chb24 only.")}
{fig('B15', 'Median absolute onset and offset errors of the detector and the localizer on development, held-out test, final test, chb24 and Siena', 1728, 600)}"""
    return bk("b15", 15, "Onset and Offset on Every Set", "Are the boundaries better on other data too?", body,
              "Report Table 13",
              "Medians over the matched pairs of 4 seeds (n = 247, 103, 146, 53, 116). A contiguous-run offset gives 16 s on the final test: the next step is multichannel change points.")


def b16():
    body = f"""{ans("Seven Siena patients with budgets above 1.7 % hold 197 of the 257 false alarms (seed 42).")}
<div style="display:flex;flex-direction:row;gap:30px;align-items:center">
<div style="width:1060px">{im('B18', 1060, 600, 'Siena per patient: false alarms per day against the label-free budget; patients above 1.7 percent hold most false alarms')}</div>
<div style="flex:1;display:flex;flex-direction:column;gap:14px">
{ul(["10 of 14 patients: ≥ two thirds of seizures found", "PN05: 0 of 3 found", "PN06, PN07, PN16: > 70 per day", "Adults and another hospital, model trained on children"], 26, 10)}
</div></div>"""
    return bk("b16", 16, "Siena False Alarms", "Where do the external false alarms come from?", body,
              "Report Section 3.4.3, Table 15",
              "Point size = number of seizures. Per-patient mean 0.633 at 41.0 per day (4 seeds).")


def b17():
    rows = [("SeizUnet", "TUH, SeizeIT2", "0.287", "0.490", "0.207", "3.5"), ("IctalTrace V4", "TUH", "0.279", "0.358", "0.301", "6.9"),
            ("BrainGoBrr", "TUH", "0.129", "0.210", "0.047", "6.9"), ("He random forest", "CHB-MIT", "0.168", "0.302", "0.091", "8.1"),
            ("EventNet 2024", "TUH", "0.587", "0.578", "0.526", "8.2"), ("Zhu Transformer 2023", "TUH", "0.674", "0.484", "0.479", "15.3"),
            ("<b>This work</b> (no label of the patient)", "CHB-MIT, seizure-free", "<b>0.633</b>", "<b>0.160</b>", "<b>0.226</b>", "<b>41.0</b>", {"bg": "#E3F1E8"}),
            ("DynaSD (threshold: labelled iEEG)", "CHB-MIT subset, iEEG", "0.664", "0.126", "0.170", "77.7"),
            ("Self-GNN, Tang 2021", "TUH", "0.824", "0.151", "0.198", "112.5"), ("EEGWaveNet 2021", "CHB-MIT", "0.858", "0.072", "0.127", "145.5"),
            ("Velland 2025", "TUH", "1.000", "0.037", "0.071", "274.2"), ("Gotman 1982 (rules)", "none", "0.986", "0.036", "0.067", "286.1")]
    body = f"""{ans("Among methods not trained on Siena, this work sits between the supervised low-alarm entries and the high-sensitivity entries that need over 100 alarms per day.")}
{table(['Entry', 'Training data', 'Sens.', 'Prec.', 'F1', 'FA/day'], rows, [34, 24, 10, 10, 10, 12], 22, 2)}
<p style="font-size:21px;color:{GREY}">Siena, 14 patients, SzCORE event scoring, per-patient mean, sorted by false alarms per day. Entries trained on Siena excluded. This work: 4 seeds, own implementation of the scoring rules.</p>"""
    return bk("b17", 17, "Siena Benchmark in Full", "How does it compare with every benchmark entry?", body,
              "EPFL ESL SzCORE benchmark, 2024/2026 (commit c57da2f) · Report Table 18",
              "Six entries declare Siena as training data and are excluded, including SeizureTransformer. Never call this state of the art.")


def b18():
    rows = [("Chung et al., 2024", "supervised, per patient", "13 selected cases, threshold per case", "100 % at 0.30 /h"),
            ("Zhu et al., 2024", "supervised", "segments; patient-specific → cross-patient", "98.77 % → 93.78 % accuracy"),
            ("Shyu et al., 2023", "supervised", "within → across subjects", "F1 69 % → 37 %"),
            ("Ali et al., 2024", "supervised", "leave-one-subject-out, ≥ 70 % coverage rule", "75.34 % at 4.79 /h"),
            ("Mirzaei &amp; Singh, 2025", "one-class, per patient", "18 of 24 patients, seizures ≥ 40 s", "91.56 % at 0.1 /h"),
            ("Chung et al., 2026", "supervised", "excludes chb06, chb14, chb16", "80.1 % at 1.13 /h"),
            ("Yin &amp; Yin, 2026", "supervised", "excludes chb06, chb12, chb16", "100 % at 0.82 /h"),
            ("Yıldız et al., 2022", "unsupervised VAE", "windows of the same patients", "AUC 0.68"),
            ("<b>This work</b>", "no label of the patient", "8 unseen patients, all seizures, SzCORE events", "<b>0.342 at 22.2 /day</b> (held-out)", {"bg": "#E3F1E8"})]
    body = f"""{ans("Published CHB-MIT numbers use labels, exclude short-seizure patients or tune per patient, so they cannot share a table with an unseen-patient, every-event result.")}
{table(['Study', 'Labels', 'Protocol', 'Reported'], rows, [20, 20, 36, 24], 22, 9)}
<p style="font-size:21px;color:{GREY}">Shown with each protocol, not as a ranking. The same patients they exclude (chb06, chb16) are the ones this work misses.</p>"""
    return bk("b18", 18, "Published CHB-MIT Results", "Papers report 90–100 % on CHB-MIT. Why is yours lower?", body,
              "Chung et al., 2024, 2026 · Zhu et al., 2024 · Shyu et al., 2023 · Ali et al., 2024 · Mirzaei &amp; Singh, 2025 · Yin &amp; Yin, 2026 · Yıldız et al., 2022",
              "Per hour vs per day: 0.30 /h ≈ 7 per day; 4.79 /h ≈ 115 per day (computed). Only Siena gives a like-for-like comparison (slide 22, B17).")


def b19():
    body = f"""{ans("A blind, every-channel annotation of the 76 test seizures: labels concentrate on temporal and frontopolar channels, so an anatomical prior is a strong baseline (0.739).")}
<div style="display:flex;flex-direction:row;gap:30px;align-items:center">
<div style="width:1100px">{im('B20', 1100, 470, 'Times each channel was annotated across 62 focal seizures; frontopolar channels 116 of 282 labels; five channels never annotated')}</div>
<div style="flex:1;display:flex;flex-direction:column;gap:12px">
{ul(["Annotated by the author, blind to the model output", "Every channel of every seizure; approved by the supervisor", "62 focal + 14 generalized; 1–10 channels each", "Metric: AUROC of the channel ranking per seizure"], 25, 10)}
</div></div>
<p style="font-size:24px">The model ranked channels at 0.547: the channel panel of the app shows the model’s anomaly, not an onset map.</p>"""
    return bk("b19", 19, "Channel Annotation", "How was the channel explanation tested?", body,
              "Report Section 2.7, 3.5, Appendix D",
              "Pre-registered negative, same for both readouts. Not a seizure-onset-zone claim: scalp EEG has no surgical ground truth here.")


def b20():
    body = f"""{ans("The application never reads a label: automated tests guard every label path, and on chb03 it reproduces the thesis system.")}
{fig('B21', 'Raw EDF to frozen pipeline to AI events; annotations and thesis scores are never read; 15 automated tests; identity on chb03 7 of 7 with 22 false alarms', 1728, 520)}
<p style="font-size:24px">With the thesis statistics it gives 7 / 7 at 22 false alarms on chb03; with its own label-free statistics 6 / 7 at 20.</p>"""
    return bk("b20", 20, "No Labels in the Application", "How do you know the app uses no labels?", body,
              "Report Section 3.6, Appendix E",
              "Server code imports no network library, fonts are local; the evaluation run used outbound proxies pointed to an unreachable address. Do not say 'firewalled'.")


def b21():
    body = f"""{ans("21.68 s per hour of EEG on a laptop CPU; graph construction takes most of the time.")}
{fig('B22', 'Processing time per stage for chb16, 19 files, three runs: 463.9, 410.3 and 411.9 seconds', 1600, 560)}
<p style="font-size:24px">Intel i5-8250U, 16 GB, no GPU · median of 3 runs on chb16 (19.0 h) · ≈ 9 min per recorded day.</p>"""
    return bk("b21", 21, "Processing Time", "How fast is it, and on what hardware?", body, "Report Section 3.6, Table 25",
              "The full application run took 5,862 s for 279.39 h overall, with background load; the controlled timing is 21.68 s per hour.")


def b22():
    rows = [("<b>Goal</b>: unsupervised framework for temporal localization (onset and offset)", "Graph autoencoder → one score → events → change points; no label of the patient", "7–14"),
            ("<b>Objective 1</b>: unsupervised anomaly scoring with spatial-temporal features", "Per-window connectivity graphs, channel latent, ensemble score", "10–12, 16–17"),
            ("<b>Objective 2</b>: temporal localization, non-parametric change point detection", "Kernel change points (rbf), 2 per event; onset 32 → 12 s", "13, 18"),
            ("<b>Literature focus</b>: threshold calibration and baseline drift", "Per-patient alarm budget; ±15 min drift correction", "12–13, B6"),
            ("<b>Evaluation</b>: event level on CHB-MIT", "SzCORE events, 8 unseen patients, + chb24 and Siena", "14, 17–19")]
    body = f"""{ans("Every item of the signed registration form is delivered; channel explanation and the application were added.")}
{table(['Registration form', 'Delivered', 'Slides'], rows, [40, 44, 16], 23, 2)}
<p style="font-size:23px;color:{GREY}">Objective 1 asks for “spatial-temporal features”: spatial = the graph of each window; temporal = coupling over each 4 s window and the processing of the score along time.</p>"""
    return bk("b22", 22, "Registered vs Delivered", "Does the work meet the registration form?", body, "Thesis registration form · Report Section 1.4",
              "Added goals: 3 channel explanation (not met, reported), 4 review application (met).")


def b23():
    body = f"""{ans("Fallback if the live demo fails: the same steps on chb03, recorded from the final build.")}
<div style="display:flex;flex-direction:row;justify-content:center"><div style="width:1400px;height:600px;background:#EEF2F7;border:2px dashed #9AA5B1;display:flex;align-items:center;justify-content:center"><p style="font-size:30px;color:{GREY}">Demo video (insert in Canva)</p></div></div>"""
    return bk("b23", 23, "Demo Recording", "What if the live demo fails?", body, "", "Play from the start; same order as the live demo: patient list → chb03 → event 1 → EEG → channel panel → Accept.")


for _f in (b01, b02, b03, b04, b05, b06, b07, b08, b09, b10, b11, b12, b13, b14, b15, b16, b17, b18, b19, b20, b21, b22, b23):
    S[_f.__name__] = _f


ORDER = ["t01", "t02", "m01", "m02", "m03", "m04", "m05", "m06", "m07", "m08", "m09", "m10", "m11", "m12",
         "m13", "m14", "m15", "m16", "m17", "m18", "m19", "m20", "m20b", "m21", "m22", "ref1", "ref2", "t99"] + [f"b{i:02d}" for i in range(1, 24)]

if __name__ == "__main__":
    MODE = sys.argv[1]
    only = sys.argv[2:] or ORDER
    if MODE == "preview":
        out = HERE / "preview2"; out.mkdir(exist_ok=True)
        css = ("body{margin:0;background:#888} section{position:relative;width:1920px;height:1080px;box-sizing:border-box;"
               "overflow:hidden;margin-bottom:20px} p,h1,h2,h3,ul{margin:0} ul{padding-left:36px} aside{display:none}"
               "td,th{padding:0.35em 0.6em;border:1px solid #C9D3E0} table{border-collapse:collapse;width:100%}")
        html = "<html><head><meta charset='utf-8'><style>" + css + "</style></head><body>" + "".join(S[k]() for k in only) + "</body></html>"
        (HERE / "preview2.html").write_text(html, encoding="utf-8")
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            b = pw.chromium.launch(); pg = b.new_page(viewport={"width": 1920, "height": 1080})
            pg.goto((HERE / "preview2.html").as_uri()); pg.wait_for_timeout(800)
            for sid in only:
                pg.locator(f"#{sid}").screenshot(path=str(out / f"{sid}.png"))
                over = pg.evaluate(f"""() => [...document.querySelectorAll('#{sid} p, #{sid} li, #{sid} h1, #{sid} h2, #{sid} table, #{sid} img')]
                    .filter(e => !(e.style.position==='absolute'))
                    .filter(e => e.scrollHeight > e.clientHeight + 2 || e.getBoundingClientRect().bottom > 960)
                    .map(e => (e.tagName + ':' + (e.textContent||e.alt||'').slice(0,40)) + ' | b=' + Math.round(e.getBoundingClientRect().bottom))""")
                if over:
                    print(sid, "TOO LOW/OVERFLOW:", over)
            b.close()
        print("preview done")
    else:
        d = HERE / "artifact" / "project" / "slides"; d.mkdir(parents=True, exist_ok=True)
        for sid in only:
            (d / f"{sid}.html").write_text(S[sid](), encoding="utf-8")
        print("written", len(only))
