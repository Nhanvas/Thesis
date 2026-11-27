#!/usr/bin/env python
"""
c5_step3_report.py -- chat C5c (Track C), Step 3: the exploratory expert review read into counts
(results/c5_szscan/step3/PROTOCOL_STEP3.md §7). Run after the session, once the answers are downloaded.

Inputs (private folder): key.csv (c5_step3_clips.py) and c5_review_answers.csv (the review page). Every clip of the key
must have an answer with a class; otherwise STOP (an unanswered clip is reported, never guessed).
Outputs:
  public  results/c5_szscan/step3/REVIEW.md  counts by set (hospital: flagged highest / flagged random / control;
          anchors by category), "show me" answers, median confidence and seconds per clip; the anchors' public
          identity (dataset, patient, file, seizure or event time) with her class -- no hospital time, file or field
          results/c5_szscan/step3/anchors.csv
  private <private folder>/REVIEW_PRIVATE.md   every clip with its key and her answer (laptop only)
Level: "exploratory expert review" -- one reader, two recordings; counts only, no sensitivity (integrity rule 10).

Run: PYTHONUTF8=1 python src/c5_step3_report.py --private F:/Study/Thesis/Eureka/C5_review --answers F:/Study/Thesis/Eureka/C5_review/c5_review_answers.csv
"""
import argparse
import csv
from collections import Counter
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
PUB = ROOT / "results" / "c5_szscan" / "step3"
HOSP_SETS = ["flagged, highest score", "flagged, random", "control"]
ANCH_SETS = ["seizure found", "seizure missed", "false alarm"]


def read(p):
    with open(p, newline="", encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--private", required=True, help="the private folder of c5_step3_clips.py")
    ap.add_argument("--answers", required=True)
    ap.add_argument("--public", default=str(PUB))
    a = ap.parse_args(argv)
    key = {r["clip"]: r for r in read(Path(a.private) / "key.csv")}
    ans = {r["clip"]: r for r in read(a.answers)}
    missing = sorted(c for c in key if not ans.get(c, {}).get("class"))
    if missing:
        raise SystemExit(f"STOP: clips without a class: {missing} -- ask the reader or report them as unanswered")
    rows = [dict(key[c], **{f"a_{k}": v for k, v in ans[c].items()}) for c in sorted(key)]
    classes = sorted({r["a_class"] for r in rows})
    L = ["# SzScan — exploratory expert review (chat C5c, Step 3)", "",
         "One epileptologist rated blinded 60-s clips (18 bipolar derivations, µV, filter shown; no score or event "
         "shading) from two hospital recordings and annotated public anchors, by the rules of `PROTOCOL_STEP3.md` "
         "(written and committed before selection). **Level: exploratory expert review** — one reader, two "
         "recordings, counts only; not a measure of sensitivity or of clinical validity.", "",
         "## Hospital clips: her class by set", "",
         "| class | " + " | ".join(HOSP_SETS) + " |", "|---|" + "---|" * len(HOSP_SETS)]
    by = {s: [r for r in rows if r["source"] == "hospital" and r["set"] == s] for s in HOSP_SETS}
    for c in classes:
        L.append(f"| {c} | " + " | ".join(str(sum(r["a_class"] == c for r in by[s])) for s in HOSP_SETS) + " |")
    L.append("| **clips** | " + " | ".join(str(len(by[s])) for s in HOSP_SETS) + " |")
    L += ["", "| \"Would you want the system to show you this segment?\" | " + " | ".join(HOSP_SETS) + " |",
          "|---|" + "---|" * len(HOSP_SETS)]
    for k, lab in (("yes", "yes"), ("no", "no"), ("unsure", "not sure")):
        L.append(f"| {lab} | " + " | ".join(str(sum(r["a_show_me"] == k for r in by[s])) for s in HOSP_SETS) + " |")

    def med(xs):
        xs = [float(x) for x in xs if str(x).strip() not in ("", "nan")]
        return f"{np.median(xs):.1f}" if xs else "—"
    L += ["", "| set | median confidence (1–5) | median seconds per clip |", "|---|---|---|"]
    for s in HOSP_SETS:
        L.append(f"| hospital — {s} | {med(r['a_confidence'] for r in by[s])} | {med(r['a_seconds'] for r in by[s])} |")
    anc = [r for r in rows if r["source"] == "anchor"]
    L += ["", "## Anchor clips (annotated public data): her class against the annotation", "",
          "| clip | category | dataset | patient | file | onset / offset (s) | her class | confidence | show me |",
          "|---|---|---|---|---|---|---|---|---|"]
    for r in sorted(anc, key=lambda r: (ANCH_SETS.index(r["set"]), r["dataset"], r["study"])):
        L.append(f"| {r['clip']} | {r['set']} | {r['dataset']} | {r['study']} | {r['file']} | "
                 f"{r['event_or_seizure_onset_s']} / {r['event_or_seizure_offset_s']} | {r['a_class']} | "
                 f"{r['a_confidence']} | {r['a_show_me']} |")
    L += ["", "| set | median confidence (1–5) | median seconds per clip |", "|---|---|---|"]
    for s in ANCH_SETS:
        rs = [r for r in anc if r["set"] == s]
        L.append(f"| anchors — {s} | {med(r['a_confidence'] for r in rs)} | {med(r['a_seconds'] for r in rs)} |")
    L += ["", f"Clips with the gain halved: {sum(r['a_gain_halved'] == 'yes' for r in rows)} of {len(rows)}. "
          f"Classes used: {dict(Counter(r['a_class'] for r in rows))}.", "",
          "Wording: \"in an exploratory review by one epileptologist, of the N flagged hospital segments she classed "
          "k as …\" — never a rate, never \"validated\"; her comments only as she approved them."]
    pub = Path(a.public)
    pub.mkdir(parents=True, exist_ok=True)
    (pub / "REVIEW.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    with open(pub / "anchors.csv", "w", newline="", encoding="utf-8") as fh:
        cols = ["clip", "set", "dataset", "study", "file", "clip_start_s", "event_or_seizure_onset_s",
                "event_or_seizure_offset_s", "peak_score", "a_class", "a_confidence", "a_show_me", "a_seconds"]
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(anc)
    P = ["# Step 3 review — every clip (PRIVATE, laptop only; never commit)", "",
         "| clip | source | set | study | file | clip start s | peak score | class | confidence | show me | s | comment |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        P.append(f"| {r['clip']} | {r['source']} | {r['set']} | {r['study']} | {r['file']} | {r['clip_start_s']} | "
                 f"{r['peak_score']} | {r['a_class']} | {r['a_confidence']} | {r['a_show_me']} | {r['a_seconds']} | "
                 f"{r['a_comment']} |")
    (Path(a.private) / "REVIEW_PRIVATE.md").write_text("\n".join(P) + "\n", encoding="utf-8")
    print(f"REVIEW.md written ({len(rows)} clips; hospital {sum(len(v) for v in by.values())}, anchors {len(anc)})")


if __name__ == "__main__":
    main()
