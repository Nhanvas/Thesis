#!/usr/bin/env python
"""
c5_g2.py -- chat C5c (Track C), Step 2c, gate G2 (results/c5_szscan/DESIGN_STEP2.md): SzScan's file engine, run as the
application runs it, gives F2-03's committed L3 result for every recording.

Question: does the application's "each file on its own" mode (SzScan 1.0) reproduce the label-free per-recording
protocol that F2-03 scored once (results/m2l/l3eval/per_file.csv, arm B-MCD-F, seed clean_seed42)?
For every recording of the test patients, chb24 and Siena (the files and seizures of L3, raw EDF verified against
PhysioNet in the session by the same inventory as L3, m2l_run.inventory):
  1. the application's Phase A on the EDF (pipeline_demo.process_file_phase_a: edf_input.load_any, band-pass + notch,
     windows, signal-loss flag, the every-10th sampled windows), into a scratch cache, as the upload worker does;
  2. engine_file.run_file on those caches (the phase_b_file worker's call);
  3. the events scored with L3's own scorer and labels (p2_scalars.score on the window labels of m2l_core.features:
     seizure windows, the 4-h post-seizure buffer for CHB-MIT, signal loss) -> tp, fp, n_ref.
Gate G2 (written before any run): per recording, short, n, valid, events, tp, fp and n_ref equal to the L3 row, q and
top equal within 1e-9 (relative); the recordings = L3's recordings of the set. Nothing is tuned; no label reaches the
engine (labels are used in step 3 only).
Also: G-raw (PhysioNet sha256, via the L3 inventory), G-worker (every job ran the parent's modules, app modules
included), G-sched (memory admission of m2l_sched), a smoke of one 1-h recording compared with its L3 row before the
build (STOP on a difference), PROJ (stop above 10.5 h).

Modes (environment C5G2_SET): chb = the 8 test patients + chb24 (notebook C5_G2_CHB); siena = the 14 Siena patients
(C5_G2_SIENA). Outputs WORK/c5g2/<tag>/: run_meta.json, gates.json, inventory/, per_file.csv (application rows),
g2.csv (row-by-row comparison), jobs.csv, projection.json, SUMMARY.md. No EEG, no cache leaves the session.
"""
import json
import os
import sys
import time
import traceback
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import m2l_core as M                     # noqa: E402
import m2l_run as MR                     # noqa: E402  (inventory, setup, gate_worker, projection: read only)

R1, P, PS = M.R1, M.P, M.PS
log = M.log
L3_ROWS = M.REPO / "results" / "m2l" / "l3eval" / "per_file.csv"
BACKEND = M.REPO / "web_demo" / "backend"
APP_MODULES = ("pipeline_demo", "engine_file", "edf_input")
TOL_REL = 1e-9
# memory model of one job (laptop, C5c 26/11, PN01-1 13.5 h at 512 Hz: Phase A +622 MB, engine +209 MB above a
# process of about 0.94 GB): (BASE + hours x PER_H) x m2l_sched.SAFETY
BASE_MB, PER_H_MB = 1100.0, 70.0


def app_shas():
    if str(BACKEND) not in sys.path:
        sys.path.insert(0, str(BACKEND))
    import importlib
    return {m: M.sha16(importlib.import_module(m).__file__) for m in APP_MODULES}


def labels(n, seizures, kind):
    """m2l_core.features' scorer labels, line for line (seizure windows, CHB-MIT post-seizure buffer)."""
    secs = n * M.WIN
    lab = P.build_labels(secs, seizures).reshape(n, M.WIN).max(axis=1) == 1
    buf = P.build_buffer_mask(secs, seizures).reshape(n, M.WIN).any(axis=1) if kind == "chb" else np.zeros(n, bool)
    return lab, buf


def g2_job(a):
    """one recording through the application: Phase A -> engine_file.run_file -> L3's scorer.
    a = (case, set_name, path, kind, notch, seizures, scratch)"""
    case, set_name, path, kind, notch, seizures, scratch = a
    t = time.time()
    try:
        import m2l_sched as SC
        M.R0._limit_threads()
        if str(BACKEND) not in sys.path:
            sys.path.insert(0, str(BACKEND))
        import pipeline_demo as pdm
        import engine_file as EF
        cache = Path(scratch) / case / Path(path).stem
        cache.mkdir(parents=True, exist_ok=True)
        pa = pdm.process_file_phase_a(str(path), None, cache, mains=float(notch))
        flag = np.load(pa.flag_path)
        filt = np.load(pa.filtered_path, mmap_mode="r")
        res = EF.run_file(filt, flag, np.load(pa.fsamp_path))
        del filt, pa                   # Windows keeps a memory-mapped file locked until the map is closed (C5c 27/11)
        import gc
        gc.collect()
        n = len(flag)
        sl = np.asarray(flag, bool)
        lab, buf = labels(n, seizures, kind)
        z = dict(is_ictal=lab, is_signal_loss=sl, file_idx=np.zeros(n, np.int16), is_buffer=buf)
        ev = [(float(x), float(y)) for x, y in res["events"]]
        tp, fp, nr, h = PS.score(dict(z=z), {0: ev})
        for f in cache.glob("*"):
            f.unlink()
        cache.rmdir()
        return dict(set=set_name, subject=case, file=Path(path).name, q=res["q"], top=res["top"], short=bool(res["short"]),
                    valid=int((~sl).sum()), n=n, events=len(ev), tp=int(tp), fp=int(fp), n_ref=int(nr), nonict_h=h,
                    review_s=float(sum(y - x for x, y in ev)), hours=n * M.WIN / 3600, s=round(time.time() - t, 1),
                    vmhwm_mb=round(SC.vmhwm_mb(), 1), shas={**M.code_shas(), **app_shas()}, case=case)
    except SystemExit as e:
        return dict(case=case, file=Path(path).name, error=f"STOP: {e}")
    except Exception:                    # noqa: BLE001
        return dict(case=case, file=Path(path).name, error=traceback.format_exc()[-3000:])


def l3_rows(cases):
    ref = pd.read_csv(L3_ROWS)
    ref = ref[(ref.seed == "clean_seed42") & (ref.budget == "B-MCD-F") & ref.subject.isin(cases)]
    return {(r.subject, r.file): r for r in ref.itertuples()}


def compare(row, ref):
    """-> list of the fields that differ (empty = equal)."""
    bad = [k for k in ("short", "n", "valid", "events", "tp", "fp", "n_ref")
           if (bool(row[k]) if k == "short" else int(row[k])) != (bool(getattr(ref, k)) if k == "short" else int(getattr(ref, k)))]
    for k in ("q", "top"):
        a, b = float(row[k]), float(getattr(ref, k))
        if not ((np.isnan(a) and np.isnan(b)) or abs(a - b) <= TOL_REL * max(1.0, abs(b))):
            bad.append(k)
    return bad


def setup(tag, notebook, repo_commit, workers):
    """m2l_run.setup with the output root WORK/c5g2 (m2l_run.setup sets WORK/m2l)."""
    R1.OUT_ROOT = R1.WORK / "c5g2"
    workers = int(workers or os.environ.get("C5G2_WORKERS") or R1.n_workers())
    meta = R1.run_meta(tag, notebook, repo_commit)
    meta.update(m2l_code_shas=M.code_shas(), app_shas=app_shas(), workers=workers,
                design="results/c5_szscan/DESIGN_STEP2.md (G2); src/c5_g2.py")
    try:
        meta["cpu_model"] = next((ln.split(":", 1)[1].strip() for ln in open("/proc/cpuinfo")
                                  if ln.startswith("model name")), None)
    except OSError:
        meta["cpu_model"] = None
    R1._jdump(R1.out_dir() / "run_meta.json", meta)
    return workers


def gate_g2(rows, ref, label, out_dir):
    """writes g2.csv first (a FAIL stops the run after the table is written), then the gate."""
    got = {(r["subject"], r["file"]): r for r in rows}
    missing = sorted(set(ref) - set(got))
    extra = sorted(set(got) - set(ref))
    diffs = []
    out = []
    for k, r in sorted(got.items()):
        d = compare(r, ref[k]) if k in ref else ["not in L3"]
        out.append(dict(subject=k[0], file=k[1], equal=not d, differ=" ".join(d),
                        **{f"{f}_app": r[f] for f in ("events", "tp", "fp", "n_ref", "q", "top", "short", "valid", "n")},
                        **({f"{f}_l3": getattr(ref[k], f) for f in ("events", "tp", "fp", "n_ref", "q", "top", "short",
                                                                    "valid", "n")} if k in ref else {})))
        if d:
            diffs.append(f"{k[0]}/{k[1]}: {' '.join(d)}")
    pd.DataFrame(out).to_csv(out_dir / "g2.csv", index=False)
    ok = not diffs and not missing and not extra
    R1.gate(dict(gate=f"G2[{label}]", status="PASS" if ok else "FAIL", recordings=len(got), l3_recordings=len(ref),
                 missing=missing[:20], extra=extra[:20], differ=diffs[:30],
                 summary=f"{len(got) - len(diffs)} / {len(got)} recordings equal to L3; missing {len(missing)}, "
                         f"extra {len(extra)}"))
    return out


def main(notebook="local", repo_commit="local", workers=None):
    which = os.environ.get("C5G2_SET", "chb")
    if which not in ("chb", "siena"):
        raise SystemExit(f"STOP: C5G2_SET = {which}")
    tag = f"c5g2_{which}"
    workers = setup(tag, notebook, repo_commit, workers)
    import m2l_sched as SC
    if which == "chb":
        cases = list(M.TEST) + ["chb24"]
        inv, cases_df, complete, earlier = MR.inventory({"chbmit": list(M.TEST) + ["chb24"]}, cases, MR.CHB_CHECKS)
        files = {c: M.chb_files(c, earlier) for c in M.TEST}
        files["chb24"] = M.ext_files("chb24", complete)
        set_of = {c: "test" for c in M.TEST} | {"chb24": "chb24"}
    else:
        cases = [c for c in M.EXT if c != "chb24"]
        inv, cases_df, complete, earlier = MR.inventory({"siena": None}, cases, [])
        files = {c: M.ext_files(c, complete) for c in cases}
        set_of = {c: "siena" for c in cases}
    ref = l3_rows(cases)
    scratch = M.SCR / "c5g2"
    specs = [(c, set_of[c], str(p), kind, notch, [tuple(s) for s in sz], str(scratch))
             for c in cases for (p, sz, kind, notch) in files[c]]
    hdr = [SC.edf_header(a[2]) for a in specs]
    hours = [h for h, _ in hdr]
    R1.gate(dict(gate="G-files", status="PASS" if {(a[0], Path(a[2]).name) for a in specs} == set(ref) else "FAIL",
                 recordings=len(specs), l3_recordings=len(ref),
                 summary=f"{len(specs)} recordings = L3's {len(ref)} recordings of the set"))
    # smoke: one recording of about 1 h, compared with its L3 row before the build
    t = time.time()
    one = [i for i, h in enumerate(hours) if 0.9 < h < 1.1] or [int(np.argmin(hours))]
    sm = g2_job(specs[one[0]])
    if sm.get("error"):
        raise SystemExit(f"smoke {specs[one[0]][0]} {Path(specs[one[0]][2]).name}: {sm['error']}")
    d = compare(sm, ref[(sm["subject"], sm["file"])])
    R1.gate(dict(gate="G2-smoke", status="PASS" if not d else "FAIL", file=sm["file"], differ=d, seconds=sm["s"],
                 peak_mb=sm["vmhwm_mb"], summary=f"{sm['subject']}/{sm['file']} {'= L3' if not d else 'differs: ' + ' '.join(d)}"))
    rate = dict(rec_s_per_h=sm["s"] / max(sm["hours"], 1e-9) * MR.LOAD_FACTOR, smoke_file=sm["file"],
                smoke_hours=round(sm["hours"], 3), smoke_s=sm["s"], load_factor=MR.LOAD_FACTOR)
    R1._jdump(R1.out_dir() / "smoke.json", rate)
    R1.phase("smoke", t)
    MR.projection(rate, hours, workers)
    est = [(BASE_MB + h * PER_H_MB) * SC.SAFETY for h in hours]
    dur = [h * rate["rec_s_per_h"] for h in hours]
    budget, bsrc = SC.memory_budget_mb()
    log(f"build: memory budget {budget:.0f} MB ({bsrc}); {len(specs)} recordings, largest estimate {max(est):.0f} MB")
    t = time.time()
    rows = SC.run(g2_job, specs, est, dur, workers, budget, "g2")
    R1.phase("build", t)
    out = R1.out_dir()
    pd.DataFrame([{k: v for k, v in r.items() if k != "shas"} for r in rows]).to_csv(out / "per_file.csv", index=False)
    parent = {**M.code_shas(), **app_shas()}
    bad = [(r["subject"], r["file"]) for r in rows if r.get("shas") != parent]
    R1.gate(dict(gate="G-worker[g2]", status="PASS" if not bad else "FAIL", jobs=len(rows), differ=bad[:10],
                 summary=f"{len(rows)} jobs ran the parent's modules (m2l and the application)"))
    SC.gate_sched(rows, budget, "g2")
    cmp_rows = gate_g2(rows, ref, which, out)
    R1.finish_meta(dict(app_shas=app_shas(), l3_rows=str(L3_ROWS.relative_to(M.REPO))))
    n_eq = sum(r["equal"] for r in cmp_rows)
    (out / "SUMMARY.md").write_text(
        f"# {notebook} (commit {repo_commit})\n\nGate G2 ({which}): {n_eq} / {len(cmp_rows)} recordings of the "
        f"application's file engine equal to F2-03's L3 rows (B-MCD-F, seed 42). Details: g2.csv, gates.json.\n",
        encoding="utf-8")
    log(f"{notebook} done: {n_eq} / {len(cmp_rows)} equal")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int)
    ap.add_argument("--notebook", default="local")
    a = ap.parse_args()
    main(a.notebook, workers=a.workers)
