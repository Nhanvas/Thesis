"""Crop the author's figures from the Canva deck v2 (Thesis_final_slide.pdf, 21/10) for the rebuilt deck.
raw = the embedded image itself (uncropped placement); clip = render of the page area (scale 2)."""
import pymupdf, os
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
doc = pymupdf.open(os.path.join(ROOT, "v2.pdf"))
C = {  # name: (page, mode, xref or rect)
 "logo_vnu": (1, "raw", 85), "logo_bme": (1, "raw", 86),
 "ep_brain": (3, "raw", 96), "ep_person": (3, "raw", 97),
 "m07_pipe": (7, "raw", 120), "m08_mont": (8, "raw", 126),
 "m09_pre": (9, "raw", 132), "m10_graph": (10, "raw", 138),
 "m11_gae": (11, "raw", 146), "m12_score": (12, "raw", 153),
 "m13_det": (13, "raw", 159), "m14_ev": (14, "raw", 165),
 "m15_den": (15, "raw", 1452), "m15_loss": (15, "raw", 173),
 "m16_dev": (16, "raw", 178), "m17_test": (17, "raw", 184),
 "m18_bound": (18, "raw", 190), "m19_ext": (19, "raw", 196),
 "m20_chan": (20, "raw", 202), "m21_app": (21, "raw", 211),
 "m21_shot": (21, "raw", 208), "m24_budget": (24, "raw", 232), "m24_dur": (24, "raw", 233),
 "a32_why": (32, "raw", 274), "a41_cpd": (41, "raw", 327),
 "a42_event": (42, "raw", 333), "a43_budget": (43, "raw", 338),
 "a44_notadopt": (44, "raw", 343), "a45_proto": (45, "raw", 348),
 "a46_low": (46, "raw", 353), "a47_seeds": (47, "raw", 358),
 "a48_label": (48, "raw", 363), "a50_gallery": (50, "raw", 374),
 "a51_onoff": (51, "raw", 378), "a59_map": (59, "raw", 413),
 "a60_flow": (60, "raw", 418), "a63_arch": (63, "raw", 432),
 "a64_demo": (64, "raw", 436), "a65_time": (65, "raw", 441),
}
os.makedirs(os.path.join(ROOT, "crop"), exist_ok=True)
for name, (pn, mode, arg) in C.items():
    out = os.path.join(ROOT, "crop", name + ".png")
    if mode == "raw":
        pix = pymupdf.Pixmap(doc, arg)
        info = doc.extract_image(arg)
        if info.get("smask"):
            pix = pymupdf.Pixmap(pix, pymupdf.Pixmap(doc, info["smask"]))
        if pix.n - pix.alpha >= 4:
            pix = pymupdf.Pixmap(pymupdf.csRGB, pix)
        pix.save(out)
    else:
        r = pymupdf.Rect(arg) & pymupdf.Rect(0, 0, 1440, 744)
        doc[pn - 1].get_pixmap(clip=r, matrix=pymupdf.Matrix(2, 2)).save(out)
    p = pymupdf.Pixmap(out); print(name, p.width, p.height)

# title / thank-you background: the page with its text removed
for pn, name in ((1, "title_bg"), (28, "thanks_bg")):
    d2 = pymupdf.open(os.path.join(ROOT, "v2.pdf")); pg = d2[pn - 1]
    for b in pg.get_text("dict")["blocks"]:
        if b["type"] == 0:
            pg.add_redact_annot(b["bbox"])
    if pn == 1:
        print([ (round(d["rect"].x0),round(d["rect"].y0),round(d["rect"].x1),round(d["rect"].y1)) for d in pg.get_drawings()][:5])
        pg.add_redact_annot(pymupdf.Rect(570, 215, 870, 302))
    pg.apply_redactions(images=pymupdf.PDF_REDACT_IMAGE_NONE, graphics=2)
    pg.get_pixmap(matrix=pymupdf.Matrix(1920/1440, 1920/1440)).save(os.path.join(ROOT, "crop", name + ".png"))
    print(name)
