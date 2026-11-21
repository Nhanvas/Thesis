#!/usr/bin/env python
"""
fa15_diag_laptop.py -- F-A1.5 diagnostic T1 (chat D35-F, approved by the author 21/11 13:30; design in
results/fa15/DESIGN_D35F.md §6, written before this runs). LAPTOP ONLY (the machine that made the V9-X6 record).

Question: do the files where the F-A1.5 data run (Kaggle) differs from the V9-X6 record differ because of the platform
(laptop vs Kaggle arithmetic), or because the record was made in a software state that no longer reproduces?
Method: V9-X6's OWN code path (src/v9_x6_asr.py: whole_file_filtered, run_asr with its current 60-s chunking, Measure 1
in process_one), unchanged, on this laptop, one OS process per file (V9-X6's memory rule); its part files are written to
results/fa15/diag_laptop/parts/ (V6.PARTS redirected), never to results/v9_x6/_parts/. Files: the 10 that differ
(chb03_01, chb03_02, chb15_10, chb15_20, chb15_62, chb16_11, chb16_16, chb16_18, chb24_14 in FA15_DATA_A; chb06_01 in
the smoke) + 2 controls that matched bit for bit (chb03_03, chb16_17).
Reading (per file, max |difference| over V9-X6's quantities; 1e-9 = equal): laptop now vs the record; laptop now vs
Kaggle (results/fa15/a/measure, smoke/measure). laptop = record != Kaggle -> platform; laptop = Kaggle != record -> the
record's state does not reproduce; neither -> both. Controls must equal the record (else the laptop itself changed).
Outputs (small, committed): results/fa15/diag_laptop/compare.csv, env.json (versions, CPU, BLAS), parts/*.json, SUMMARY.md.
Runtime (computed from V9-X6's measured 135 s per hour of EEG on this laptop): 15 h of EEG ≈ 35 min.
  python src/fa15_diag_laptop.py --run          (all files; resumable: a file whose part exists is skipped)
  python src/fa15_diag_laptop.py --one SUBJ FILE (one file, one process: what --run shells out to)
Test (synthetic, build container): FA15_DIAG_TEST=1 with FA15_DIAG_DATASET / FA15_DIAG_THR (see the D35-F test).
"""
import argparse
import hashlib
import importlib.metadata as ilm
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
for _p in (ROOT / "src", ROOT / "src" / "dataprep"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))
import preprocessing as P                # noqa: E402  (record, read only)
import v9_x6_asr as V6                   # noqa: E402  (record, read only; only PARTS / DATASET_DIR redirected)

TEST = bool(os.environ.get("FA15_DIAG_TEST"))
OUT = Path(os.environ.get("FA15_DIAG_OUT", ROOT / "results" / "fa15" / "diag_laptop"))
V6.PARTS = OUT / "parts"
if TEST:
    V6.DATASET_DIR = Path(os.environ["FA15_DIAG_DATASET"])
DIFFER = [("chb03", "chb03_01.edf"), ("chb03", "chb03_02.edf"), ("chb15", "chb15_10.edf"), ("chb15", "chb15_20.edf"),
          ("chb15", "chb15_62.edf"), ("chb16", "chb16_11.edf"), ("chb16", "chb16_16.edf"), ("chb16", "chb16_18.edf"),
          ("chb24", "chb24_14.edf"), ("chb06", "chb06_01.edf")]
CONTROL = [("chb03", "chb03_03.edf"), ("chb16", "chb16_17.edf")]
TOL = 1e-9
QTY = ("share_seizure", "share_preictal60", "contrast_before", "contrast_after", "highamp_share",
       "background_share_sorted")
CODE_SHA = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()[:16]


def targets():
    if TEST:
        return [tuple(x) for x in json.loads(os.environ["FA15_DIAG_TARGETS"])]
    return DIFFER + CONTROL


def env():
    v = {"python": platform.python_version()}
    for k in ("numpy", "scipy", "pandas", "mne", "asrpy"):
        try:
            v[k] = ilm.version(k)
        except ilm.PackageNotFoundError:
            v[k] = None
    try:
        b = np.show_config(mode="dicts")["Build Dependencies"]["blas"]
        blas = f"{b.get('name')} {b.get('version')}"
    except Exception:                    # noqa: BLE001
        blas = None
    return dict(versions=v, platform=platform.platform(), cpu=platform.processor(),
                cpu_id=os.environ.get("PROCESSOR_IDENTIFIER"), cpu_count=os.cpu_count(), blas=blas,
                code_sha=CODE_SHA, v9_x6_sha=hashlib.sha256((ROOT / "src" / "v9_x6_asr.py").read_bytes()).hexdigest()[:16],
                mem_split_chunk_s=V6.MEM_SPLIT_CHUNK_S)


def seizures_of(subj, fname):
    summ = (ROOT / "data" / "summaries" / f"{subj}-summary.txt")
    if subj == "chb24" or not summ.exists():
        summ = V6.DATASET_DIR / subj / f"{subj}-summary.txt"
    return P.parse_summary(summ)[fname]


def threshold(subj):
    if TEST:
        return np.asarray(json.loads(os.environ["FA15_DIAG_THR"])[subj], float)
    return V6.subject_threshold(subj)                    # V9-X6's own: data/processed stats / chb24 xcache


def one(subj, fname):
    V6.process_one(subj, fname, seizures_of(subj, fname), 20, threshold(subj))


def frames_from_part(d, s, f):
    sz = pd.DataFrame([dict(subject=s, file=f, **r) for r in d["seizures"]])
    h = d["highamp"]
    hi = pd.DataFrame(dict(subject=s, file=f, win_idx=h["win_idx"], share=h["share"]))
    bg = pd.DataFrame(dict(subject=s, file=f, share=d["background"]["share"]))
    return sz, hi, bg


def frames_from_fa15(m, s, f):
    sz = pd.DataFrame(m["seizures"])
    h = m["highamp"]
    return sz, pd.DataFrame(dict(subject=s, file=f, win_idx=h["win_idx"], share=h["share"])), \
        pd.DataFrame(dict(subject=s, file=f, share=m["background"]["share"]))


def record_frames(s, f):
    d = ROOT / "results" / "v9_x6"
    sz = pd.read_csv(d / "seizures.csv", float_precision="round_trip")
    hi = pd.read_csv(d / "highamp_windows.csv", float_precision="round_trip")
    bg = pd.read_csv(d / "background_windows.csv", float_precision="round_trip")
    pick = lambda x: x[(x.cutoff == 20) & (x.subject == s) & (x.file == f)]  # noqa: E731
    return pick(sz), pick(hi), pick(bg)


def kaggle_frames(s, f):
    for tag in ("a", "b1", "b2", "smoke"):
        p = ROOT / "results" / "fa15" / tag / "measure" / f"{s}__{f}.json"
        if p.exists() and json.loads(p.read_text()):
            return tag, frames_from_fa15(json.loads(p.read_text()), s, f)
    return None, None


def compare(A, B):
    """max |A - B| per quantity (seizure rows by index; high-amplitude windows on common indices + count of windows in
    one set only; background shares as sorted lists) -- the comparison of fa15_asr.compare_file."""
    sa, ha, ba = A
    sb, hb, bb = B
    w = {}
    a, b = sa.set_index("seizure_idx"), sb.set_index("seizure_idx")
    for q in QTY[:4]:
        w[q] = float(np.nanmax(np.abs(a[q].to_numpy(float) - b[q].reindex(a.index).to_numpy(float)))) if len(a) else np.inf
    ha, hb = ha.set_index("win_idx"), hb.set_index("win_idx")
    com = ha.index.intersection(hb.index)
    w["highamp_share"] = float(np.nanmax(np.abs(ha.share[com].to_numpy(float) - hb.share[com].to_numpy(float)))) if len(com) else 0.0
    ga, gb = np.sort(ba.share.to_numpy(float)), np.sort(bb.share.to_numpy(float))
    w["background_share_sorted"] = float(np.nanmax(np.abs(ga - gb))) if len(ga) == len(gb) and len(ga) else \
        (0.0 if len(ga) == len(gb) else np.inf)
    only = len(ha.index.symmetric_difference(hb.index))
    return w, only, len(a) == len(b)


def run():
    OUT.mkdir(parents=True, exist_ok=True)
    e = env()
    (OUT / "env.json").write_text(json.dumps(e, indent=1), encoding="utf-8")
    if not e["versions"].get("asrpy"):
        raise SystemExit("STOP: asrpy is not installed in this Python (V9-X6 ran with asrpy 0.0.8)")
    t0 = time.time()
    for s, f in targets():
        if V6.part_path(s, f, 20).exists():
            print(f"{s}/{f}: part exists, skipped", flush=True)
            continue
        t = time.time()
        r = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--one", s, f], cwd=str(ROOT))
        if r.returncode != 0:
            raise SystemExit(f"STOP: {s}/{f} failed (exit {r.returncode})")
        print(f"{s}/{f}: {time.time() - t:.0f} s", flush=True)
    rows = []
    for s, f in targets():
        lap = frames_from_part(json.loads(V6.part_path(s, f, 20).read_text(encoding="utf-8")), s, f)
        w_rec, o_rec, n_rec = compare(lap, record_frames(s, f))
        tag, kf = kaggle_frames(s, f)
        w_kag, o_kag, n_kag = compare(lap, kf) if kf is not None else ({q: np.nan for q in QTY}, 0, True)
        m_rec, m_kag = max(w_rec.values()), max(w_kag.values())
        eq_rec = m_rec <= TOL and o_rec == 0 and n_rec
        eq_kag = kf is not None and m_kag <= TOL and o_kag == 0 and n_kag
        role = "control" if (s, f) in CONTROL else "differs"
        rows.append(dict(subject=s, file=f, role=role, kaggle_run=tag, max_vs_record=m_rec, highamp_only_record=o_rec,
                         equal_record=eq_rec, max_vs_kaggle=m_kag, highamp_only_kaggle=o_kag, equal_kaggle=eq_kag,
                         reading=("platform" if eq_rec and not eq_kag else "record state" if eq_kag and not eq_rec
                                  else "same" if eq_rec and eq_kag else "both")))
    d = pd.DataFrame(rows)
    d.to_csv(OUT / "compare.csv", index=False)
    ctrl_ok = bool(d[d.role == "control"].equal_record.all())
    L = ["# F-A1.5 T1 -- V9-X6's ASR re-run on the laptop (fa15_diag_laptop " + CODE_SHA + ")", "",
         f"Environment: {json.dumps(e['versions'])}; CPU {e['cpu']} / {e['cpu_id']}; BLAS {e['blas']}; "
         f"V9-X6 chunk {e['mem_split_chunk_s']} s. Runtime {time.time() - t0:.0f} s.", "",
         f"Controls equal to the record: {'yes' if ctrl_ok else 'NO -- the laptop itself no longer reproduces'}.", "",
         "Reading per file: platform = laptop equals the record, not Kaggle; record state = laptop equals Kaggle, not the "
         "record; both = equals neither; same = equals both.", "", "```",
         d[["subject", "file", "role", "max_vs_record", "max_vs_kaggle", "reading"]].to_string(index=False), "```"]
    (OUT / "SUMMARY.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L), flush=True)
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--one", nargs=2)
    a = ap.parse_args()
    if a.one:
        one(*a.one)
        return 0
    if a.run:
        return run()
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
