#!/usr/bin/env python
"""
attribution_v8.py -- channel attribution of the FINAL system (P3 frozen), ATTRIBUTION_SPEC Amendment A5.

PRE-REGISTRATION (A5, written 2026-10-08 before any number of this script exists)
---------------------------------------------------------------------------------
Why. The final system (tag p3-frozen) no longer uses the reconstruction readout that A4 scored. Its
anomaly score is built from a per-channel quantity: the per-patient LedoitWolf Mahalanobis distance of
each channel's 16-d GAE v2 node latent, robust-z per channel. That per-channel z is what the system
ranks (order statistics 6/9/12 and the mean are taken over it) and what the rebuilt web demo shows.
A5 scores THAT quantity against the same final channel annotation, with the A4 method unchanged.

Score (one construction, fixed now).
  D_i(w)  = results/p2_test/{subj}.npz  clean_seed{N}_d[:, i]  (per-channel LW distance, fitted on all
            dumped windows of the patient, label-free; the look-#6/#7 cache)
  z_i(w)  = (D_i(w) - median_w D_i) / (MAD_w D_i + 1e-9), over all dumped windows of the patient
            (identical to e16_recording_baseline.rz inside s_from_d: the system's per-channel z,
            before the order statistic and before the +-15 min drift correction)
  s_i     = p95 over the seizure's dumped windows of |z_i(w)|   (A4 aggregation, unchanged)
  Seizure windows = windows of the labelled file with start in [floor(onset/4), ceil(offset/4)),
  onset/offset from results/attribution_v6/seizure_blocks.csv (the A4 alignment, edf_file + onset_s).
Primary: seed 42, p95. Labels, L1 / L2 / L3, D7, Holm over {L2, L3}, bootstrap and permutation settings,
descriptive panels (without chb15, n_win >= 3, mean aggregation, seeds 1/2/3, per subject) and the
interpretation table of spec 4.7 are those of A4, executed by attribution_pipeline.cmd_eval7 itself;
in the sentences of 4.7 "reconstruction anomaly" reads "latent anomaly".
Not done (and never added after seeing a result): any other per-channel quantity, the drift-corrected
variant, another aggregation, another seed as primary, any channel or seizure subset as primary.
Reporting. One run, reported as is, whatever the outcome. The A4 result stays in the thesis as the
attribution of the earlier reconstruction readout; A5 is the attribution of the final system. Not a
detection look (no event metric); it reuses the 76 test annotations already used by A4 and is logged in
PERF_PHASE_RECORD section 3 as an attribution read.

Gates (hard stop before any metric):
  G1 every one of the 76 label rows maps to one file of data/testset_v2 and its window span is all
     is_ictal; the union of the 76 spans equals every is_ictal window of each subject.
  G2 cache: idx strictly increasing, len(idx) == rows of every clean_seed{N}_d, 18 channels.
  G3 the annotation gate G-L1 of A4 (load_labels7 refuses without the author's order confirmation).

Run:  python src/attribution_v8.py --write-amendment     (appends A5 to docs/ATTRIBUTION_SPEC.md once)
      python src/attribution_v8.py                       (estimated 2-8 min CPU, not measured)
Outputs: results/attribution_v8/{alignment.csv, attribution_scores.csv, attribution_perseizure.csv,
         attribution_summary.csv, attribution_tests.csv, SUMMARY.md}
"""
import argparse
import contextlib
import csv
import io
import math
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT / "src", ROOT / "src" / "retrain", ROOT / "src" / "phaseB", ROOT / "src" / "phaseC",
          ROOT / "src" / "dataprep"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
import attribution_pipeline as AP  # noqa: E402

TEST = ["chb03", "chb06", "chb13", "chb14", "chb15", "chb16", "chb17", "chb18"]
SEEDS = [42, 1, 2, 3]
WIN = 4
OUT8 = ROOT / "results" / "attribution_v8"
TESTSET = ROOT / "data" / "testset_v2"
P2TEST = ROOT / "results" / "p2_test"
BLOCKS = ROOT / "results" / "attribution_v6" / "seizure_blocks.csv"
SPEC = ROOT / "docs" / "ATTRIBUTION_SPEC.md"
A5_MARK = "### A5 (2026-10-08)"


def die(msg):
    print(f"\n[STOP] {msg}\n", file=sys.stderr)
    sys.exit(1)


def rz(x):
    m = np.median(x)
    return (x - m) / (np.median(np.abs(x - m)) + 1e-9)


def write_amendment():
    txt = SPEC.read_text(encoding="utf-8")
    if A5_MARK in txt:
        print("A5 already in the spec, nothing written"); return
    doc = __doc__.split("PRE-REGISTRATION (A5")[1].split("Gates (hard stop")[0]
    block = (f"\n\n{A5_MARK} -- attribution of the final system. Written before any A5 number.\n"
             "Script: `src/attribution_v8.py` (its docstring is the full text).\n```\n"
             "PRE-REGISTRATION (A5" + doc.rstrip() + "\n```\n")
    SPEC.write_text(txt.rstrip("\n") + block, encoding="utf-8")
    print(f"A5 appended to {SPEC}")


def align():
    blocks = [r for r in csv.DictReader(open(BLOCKS)) if r["subject"] in TEST]
    if len(blocks) != 76:
        die(f"{BLOCKS}: {len(blocks)} test seizures, expected 76")
    rows, spans = [], {}
    for s in TEST:
        z = np.load(TESTSET / f"{s}.npz", allow_pickle=True)
        files = [Path(str(f)).name for f in z["files"]]
        fidx = z["file_idx"].astype(int)
        ict = z["is_ictal"].astype(bool)
        covered = np.zeros(len(ict), bool)
        for b in (r for r in blocks if r["subject"] == s):
            name = Path(b["edf_file"]).name
            if name not in files:
                die(f"G1 {s} seizure {b['seizure_idx']}: {name} not in testset_v2 files")
            fi = files.index(name)
            w0 = np.flatnonzero(fidx == fi)
            a = int(math.floor(float(b["onset_s"]) / WIN))
            e = int(math.ceil(float(b["offset_s"]) / WIN))
            if e > len(w0):
                die(f"G1 {s} seizure {b['seizure_idx']}: span beyond the file")
            ww = w0[a:e]
            if not ict[ww].all():
                die(f"G1 {s} seizure {b['seizure_idx']}: {int((~ict[ww]).sum())} of {len(ww)} span windows not is_ictal")
            covered[ww] = True
            spans[(s, int(b["seizure_idx"]))] = ww
            rows.append(dict(subject=s, seizure_idx=int(b["seizure_idx"]), edf_file=name,
                             onset_s=b["onset_s"], offset_s=b["offset_s"], n_windows_v2=len(ww),
                             n_windows_v1=b["n_windows"]))
        if (ict & ~covered).any():
            die(f"G1 {s}: {int((ict & ~covered).sum())} is_ictal windows not covered by any labelled seizure")
    return rows, spans


def scores(spans):
    out, nw = [], {}
    for s in TEST:
        c = np.load(P2TEST / f"{s}.npz")
        idx = c["idx"]
        if not (np.diff(idx) > 0).all():
            die(f"G2 {s}: idx not strictly increasing")
        pos = {int(w): i for i, w in enumerate(idx)}
        for seed in SEEDS:
            D = c[f"clean_seed{seed}_d"].astype(np.float64)
            if D.shape != (len(idx), 18):
                die(f"G2 {s} seed {seed}: d shape {D.shape} vs idx {len(idx)}")
            Zc = np.column_stack([rz(D[:, j]) for j in range(18)])
            for (ss, k), ww in spans.items():
                if ss != s:
                    continue
                rr = [pos[int(w)] for w in ww if int(w) in pos]
                if not rr:
                    die(f"{s} seizure {k}: no dumped window (all signal loss)")
                nw[(s, k)] = len(rr)
                a = np.abs(Zc[rr])
                for agg, vec in (("p95", np.percentile(a, 95, axis=0)), ("mean", a.mean(axis=0))):
                    out.append(((seed, agg, s, k), vec))
    S = {k: v for k, v in out}
    if len(S) != 76 * len(SEEDS) * 2:
        die(f"expected {76 * len(SEEDS) * 2} score vectors, got {len(S)}")
    return S, nw


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write-amendment", action="store_true")
    a = ap.parse_args()
    if a.write_amendment:
        write_amendment(); return
    if A5_MARK not in SPEC.read_text(encoding="utf-8"):
        die("A5 is not in docs/ATTRIBUTION_SPEC.md: run --write-amendment and commit before scoring")
    t0 = time.time()
    OUT8.mkdir(parents=True, exist_ok=True)
    rows, spans = align()
    S, nw = scores(spans)
    for r in rows:
        r["n_windows_scored"] = nw[(r["subject"], r["seizure_idx"])]
    AP.write_csv(OUT8 / "alignment.csv", rows)
    AP.write_csv(OUT8 / "attribution_scores.csv",
                 [dict(seed=k[0], agg=k[1], subject=k[2], seizure_idx=k[3], ch_idx=i, ch_name=AP.CH[i],
                       score=round(float(v[i]), 6)) for k, v in sorted(S.items()) for i in range(18)])
    print("G1 alignment and G2 cache passed")

    orig_labels = AP.load_labels7

    def labels_v2():
        lab = orig_labels()                        # G3: refuses without the A4 order confirmation
        for k in lab:
            lab[k]["nw"] = nw[k]
        return lab

    AP.load_scores = lambda seed=None, agg=None: S
    AP.load_labels7 = labels_v2
    AP.OUT7 = OUT8
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        AP.cmd_eval7(None)
    log = buf.getvalue()
    print(log)
    (OUT8 / "SUMMARY.md").write_text(
        "# Attribution A5 -- final system (per-channel latent anomaly), seed 42 primary\n\n"
        "Pre-registered in ATTRIBUTION_SPEC A5 and the docstring of src/attribution_v8.py. Method, labels and "
        "tests of A4; only the per-channel score changes. Gates G1, G2, G3 passed.\n\n```\n" + log
        + f"```\n\nElapsed {time.time()-t0:.0f} s.\n", encoding="utf-8")
    print(f"wrote {OUT8 / 'SUMMARY.md'}  ({time.time()-t0:.0f} s)")


if __name__ == "__main__":
    main()
