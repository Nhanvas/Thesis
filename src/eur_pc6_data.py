#!/usr/bin/env python
"""
eur_pc6_data.py -- EUR_PC6_DATA: the graphs of the edge-type ablation PC6 (Track F, chat D37-F; design
results/eureka_d37f/DESIGN_PC6.md §3, approved by the author 22/11/2026 07:32). Data only (no training, no scoring).
Written before any output.

The record .npz hold one graph per window: CAR -> wPLI + AEC -> A = 0.5 wPLI + 0.5 AEC -> top 20 % of the 153 pairs
(weights kept, diagonal 0; c1b_build_trainset.graph_and_bp). PC6 needs the graph of each measure alone, so the graphs are
recomputed from the raw EDF with the record builders and ONE change: c1b_build_trainset.graph_and_bp is wrapped
(install()) so that per window wPLI and AEC are computed once by the record functions and three graphs are returned,
stacked on axis 1: [0] the record rule (alpha = DEFAULT_ALPHA = 0.5), [1] wPLI only (alpha 1 -> 11a), [2] AEC only
(alpha 0 -> 11b), each graph_construction.apply_topk_threshold(., DEFAULT_KEEP_RATIO) cast to float16 as the record.
  CHB-MIT (DEV + TEST, the defense-time 'earlier' file set): r2_core.features_record -> c1b_build_trainset.build with the
          COMMITTED record statistics (data/processed/{case}_stats.json), one case per pool job (spawn workers: install()
          runs at the start of every job), as EUR_9A's G-feat0
  chb24 + Siena (EXT): r2_core.ext_job -> x1_external.build_subject (label-free statistics; its own process pool, which
          inherits the wrapper installed in the main process), one case at a time, as R0_EXT
Gates (STOP unless PASS):
  G-raw     every CHB-MIT and Siena EDF verified by sha256 against PhysioNet (r2_core.inventory); CHB-MIT checks of R0.1
  G-data    every record .npz = docs/PROVENANCE_V2.md; every external file = R1_SMOKE's pinned sha256 (eur_abl.gate_data)
  G-stack   SMOKE and every case: the builder returned 3 graphs per window (the wrapper ran in the builder's process)
  G-feat0   SMOKE: the first SMOKE_FILES files of SMOKE_CASE, rebuilt (combined graph), = the record .npz
            (r2_core.compare_features, R0's tolerances and scope)
  PROJ      projected wall time from the measured smoke (computed; STOP if > 10.5 h)
  G-struct  every case: file list, window count, file index and every flag of the rebuild = the record .npz exactly
  G-adj     every case: the rebuilt combined graph = the record graph within R0's tolerance (entries differing by > 1e-3
            <= 0.5 % on the chain windows, not signal loss); bp5 / f7 within R0's tolerances (CHB-MIT: compare_features;
            external: the same rules on the x1 keys)
  G-edges   every arm graph finite, diagonal 0, symmetric up to the record's float16 rounding of the cut (pairs kept in
            one direction counted), edges per window recorded
  G-worker  every pool job ran the parent's modules (sha256)
  G-done    every case of DEV + TEST + EXT written, manifest complete
Outputs: WORK/eureka/pc6_data/ (run_meta.json, gates.json, cases.csv, manifest.csv, smoke_feat0.json, projection.json,
jobs.csv, logs/, SUMMARY.md; committed) and WORK/eureka/pc6_data/graphs/{case}_g11.npz (adj_11a, adj_11b float16 [n,18,18]
aligned with the record windows, files, n_windows; no EEG; NOT committed -> the Kaggle dataset thesis-pc6-graphs).
  python src/eur_pc6_data.py [--workers N]
Test mode (synthetic world, build container only): R2_TEST=1 (see src/eur_pc6_data_synthetic_test.py).
"""
import hashlib
import json
import os
import platform
import sys
import time
import traceback
from pathlib import Path

import numpy as np
import pandas as pd

if platform.system() == "Windows" and "resource" not in sys.modules:
    import types
    _r = types.ModuleType("resource")
    _r.RUSAGE_SELF, _r.RUSAGE_CHILDREN = 0, -1
    _r.getrusage = lambda *_: types.SimpleNamespace(ru_maxrss=0)
    sys.modules["resource"] = _r

REPO = Path(os.environ.get("THESIS_REPO", Path(__file__).resolve().parents[1]))
for _p in ("src", "src/dataprep", "src/retrain", "src/phaseB", "src/phaseC"):
    if str(REPO / _p) not in sys.path:
        sys.path.insert(0, str(REPO / _p))

import eur_abl as A                      # noqa: E402  (views, record data gate, case lists, CPU model)
R1, R0 = A.R1, A.R0                      # noqa: E402
import r2_core as RC                     # noqa: E402

log = R1.log
DEV, TEST, EXT = list(A.DEV), list(A.TEST), list(A.EXT)
CHB = DEV + TEST
SMOKE_CASE = os.environ.get("PC6_TEST_SMOKE_CASE", "chb08") if os.environ.get("R2_TEST") else "chb08"
SMOKE_FILES = 2
REFUSE_H = 10.5
ARM_INDEX = {"11a": 1, "11b": 2}
CHAIN_TOL = RC.TOL                       # adj_entry 1e-3, adj_frac 0.005, f7 / bp5 1e-3


def sha16(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def code_shas():
    import c1b_build_trainset as C1B
    import continuous_eval as CE
    import x1_external as X1
    return {n: sha16(p) for n, p in (("eur_pc6_data", __file__), ("eur_abl", A.__file__), ("r2_r1", R1.__file__),
                                     ("r2_core", RC.__file__), ("c1b_build_trainset", C1B.__file__),
                                     ("continuous_eval", CE.__file__), ("x1_external", X1.__file__),
                                     ("graph_construction", CE.GC.__file__))}


# ============================================================================ the one change
def graph3(zw):
    """c1b_build_trainset.graph_and_bp with three graphs per window: the record's computation line for line (CAR, wPLI,
    AEC, combine, top-k, float16) for alpha = DEFAULT_ALPHA, 1 and 0; wPLI and AEC computed once. Returns (adj3
    [n,3,18,18] float16, bp [n,18,5] float32)."""
    import continuous_eval as CE
    GC, FE = CE.GC, CE.FE
    n = zw.shape[0]
    adj = np.empty((n, 3, 18, 18), dtype=np.float16)
    bp = np.empty((n, 18, 5), dtype=np.float32)
    for i in range(n):
        car = GC.apply_car(zw[i])
        w, a = GC.compute_wpli(car), GC.compute_aec(car)
        for j, alpha in enumerate((GC.DEFAULT_ALPHA, 1.0, 0.0)):
            A_ = GC.combine_adjacency(w, a, alpha=alpha)
            adj[i, j] = GC.apply_topk_threshold(A_, keep_ratio=GC.DEFAULT_KEEP_RATIO).astype(np.float16)
        bp[i] = FE.compute_band_powers(zw[i])
    return adj, bp


def install():
    """replaces c1b_build_trainset.graph_and_bp in this process (both builders call it through the module); idempotent.
    PC6_TEST_NO_INSTALL (test mode only) leaves the record function in place (negative path of G-stack)."""
    import c1b_build_trainset as C1B
    if os.environ.get("R2_TEST") and os.environ.get("PC6_TEST_NO_INSTALL"):
        return False
    C1B.graph_and_bp = graph3
    return True


# ============================================================================ per-case work
def split_check(case, z, ref, kind):
    """z: the rebuilt arrays (adj stacked); ref: the record .npz. Returns (row, adj_11a, adj_11b) or raises SystemExit."""
    adj3 = np.asarray(z["adj"])
    if adj3.ndim != 4 or adj3.shape[1:] != (3, 18, 18):
        raise SystemExit(f"G-stack {case}: adj shape {adj3.shape} (the wrapper did not run in the builder)")
    row = dict(case=case, kind=kind, n_windows=int(adj3.shape[0]))
    files_new = [str(x) for x in z["files"]]
    files_ref = [str(x) for x in ref["files"]]
    ok = files_new == files_ref and len(z["file_idx"]) == len(ref["file_idx"])
    flags = [k for k in ("is_ictal", "is_buffer", "is_flag5sd", "is_signal_loss") if k in ref.files and k in z]
    for k in flags + ["file_idx"]:
        eq = ok and np.array_equal(np.asarray(z[k]).astype(np.int64), np.asarray(ref[k]).astype(np.int64))
        row[f"{k}_equal"] = bool(eq)
        ok &= eq
    row["files_equal"], row["struct"] = files_new == files_ref, "PASS" if ok else "FAIL"
    if not ok:
        return row, None, None
    sl = np.asarray(ref["is_signal_loss"], bool)
    ch = ~sl
    c_new, c_ref = adj3[:, 0].astype(np.float32), np.asarray(ref["adj"], np.float32)
    d = (np.abs(c_new - c_ref) > CHAIN_TOL["adj_entry"]) | (np.isnan(c_new) != np.isnan(c_ref))
    row["adj_frac_differing_chain"] = float(d[ch].sum() / max(d[ch].size, 1))
    row["adj_frac_differing_all"] = float(d.sum() / max(d.size, 1))
    row["adj_exact_chain"] = bool(np.array_equal(c_new[ch], c_ref[ch], equal_nan=True))
    for k in ("bp5", "f7"):
        a_, b_ = np.asarray(z[k], np.float64)[ch], np.asarray(ref[k], np.float64)[ch]
        fin = np.isfinite(a_) & np.isfinite(b_)
        row[f"{k}_max_abs"] = float(np.abs(a_ - b_)[fin].max()) if fin.any() else 0.0
        row[f"{k}_finite_mask_diff"] = int((np.isfinite(a_) != np.isfinite(b_)).sum())
    row["adj"] = "PASS" if (row["adj_frac_differing_chain"] <= CHAIN_TOL["adj_frac"] and row["bp5_max_abs"] <= CHAIN_TOL["bp5"]
                            and row["f7_max_abs"] <= CHAIN_TOL["f7"] and row["bp5_finite_mask_diff"] == 0
                            and row["f7_finite_mask_diff"] == 0) else "FAIL"
    iu = np.triu_indices(18, 1)
    rec_set = c_ref[:, iu[0], iu[1]] != 0
    bad_e = []
    for arm, j in ARM_INDEX.items():
        g = adj3[:, j].astype(np.float32)
        up, lo = g[:, iu[0], iu[1]], g[:, iu[1], iu[0]]
        ne = (up != 0).sum(axis=1)
        diag = float(np.abs(g[:, np.arange(18), np.arange(18)]).max()) if len(g) else 0.0
        one_dir = int(((up != 0) != (lo != 0)).any(axis=1).sum())
        fin = bool(np.isfinite(g).all())
        row.update({f"{arm}_edges_mean": float(ne[ch].mean()) if ch.any() else np.nan,
                    f"{arm}_edges_min": int(ne[ch].min()) if ch.any() else 0,
                    f"{arm}_edges_max": int(ne[ch].max()) if ch.any() else 0,
                    f"{arm}_diag_max": diag, f"{arm}_one_direction_windows": one_dir, f"{arm}_finite": fin,
                    f"{arm}_edge_set_differs_from_record_share":
                        float(((up != 0) != rec_set).any(axis=1)[ch].mean()) if ch.any() else np.nan})
        if not fin or diag != 0.0:
            bad_e.append(arm)
    row["edges"] = "PASS" if not bad_e else f"FAIL {bad_e}"
    return row, adj3[:, 1].copy(), adj3[:, 2].copy()


def save_graphs(d, case, a11, b11, files):
    d = Path(d)
    d.mkdir(parents=True, exist_ok=True)
    tmp = d / f".{case}_g11.part.npz"
    np.savez_compressed(tmp, adj_11a=a11, adj_11b=b11, files=np.array(files, dtype=object), n_windows=len(a11))
    tmp.replace(d / f"{case}_g11.npz")
    return d / f"{case}_g11.npz"


def _job_meta(t, **kw):
    return dict(kw, s=round(time.time() - t, 1), shas=code_shas(),
                peak_rss_mb=round(__import__("resource").getrusage(0).ru_maxrss / 1024, 1))


def chb_job(a):
    """one CHB-MIT case (or the smoke: max_files): record builder + committed statistics with the wrapper. gdir = the
    graph folder (passed in: spawn workers do not hold the parent's output-folder state)."""
    case, max_files, logdir, gdir = a
    t = time.time()
    try:
        installed = install()
        stats = RC.committed_stats(case)
        if stats is None:
            raise SystemExit(f"{case}: no committed data/processed/{case}_stats.json")
        d = R1.SCRATCH / "pc6" / ("smoke" if max_files else "chb")
        npz = RC.features_record(case, R0.SCRATCH / "view" / "earlier", stats, d, Path(logdir) / f"{case}_features.log",
                                 max_files=max_files)
        z = dict(np.load(npz, allow_pickle=True))
        ref = np.load(R1.VIEWS / "earlier" / f"{case}.npz", allow_pickle=True)
        if max_files:
            adj3 = np.asarray(z["adj"])
            if adj3.ndim != 4:
                raise SystemExit(f"G-stack {case} (smoke): adj shape {adj3.shape} (the wrapper did not run)")
            tmp = Path(npz).with_name(f"{case}_combined_SMOKE.npz")
            np.savez(tmp, **{k: (adj3[:, 0] if k == "adj" else v) for k, v in z.items()})
            rep = RC.compare_features(tmp, R1.VIEWS / "earlier" / f"{case}.npz", n_files=max_files)
            Path(npz).unlink(missing_ok=True); tmp.unlink(missing_ok=True)
            return _job_meta(t, case=case, job="smoke", feat0=rep, installed=installed, stack=list(adj3.shape),
                             hours=float(len(z["file_idx"]) * 4 / 3600))
        row, a11, b11 = split_check(case, z, ref, "chbmit")
        Path(npz).unlink(missing_ok=True)
        path = None
        if row["struct"] == "PASS":
            path = save_graphs(gdir, case, a11, b11, [str(x) for x in z["files"]])
        return _job_meta(t, case=case, job="chb", row=row, path=str(path) if path else None, installed=installed,
                         hours=float(row["n_windows"] * 4 / 3600))
    except SystemExit as e:
        return dict(case=case, job="chb", error=f"STOP: {e}")
    except Exception:                    # noqa: BLE001
        return dict(case=case, job="chb", error=traceback.format_exc()[-3000:])


def ext_case(case, complete, logdir):
    """one external case in the main process (x1's own pool inherits the wrapper)."""
    t = time.time()
    installed = install()
    inv = pd.read_csv(RC.out_dir() / "inventory.csv")
    hh = inv[(inv.case == case) & inv.file.str.endswith(".edf")].hours
    procs = int(os.environ.get("R2_EXT_PROCS", 0)) or (4 if (float(hh.max()) if len(hh) else 0.0) <= 6 else 2)
    z, meta = RC.ext_job(case, complete, procs, Path(logdir) / f"{case}_ext.log")
    if z is None:
        raise SystemExit(f"{case}: no file with all electrodes (the record has this case)")
    ref = np.load(R1.VIEWS / "ext" / f"{case}_lf.npz", allow_pickle=True)
    row, a11, b11 = split_check(case, z, ref, "external")
    path = save_graphs(R1.out_dir() / "graphs", case, a11, b11, [str(x) for x in z["files"]]) if row["struct"] == "PASS" else None
    return _job_meta(t, case=case, job="ext", row=row, path=str(path) if path else None, installed=installed,
                     procs=procs, hours=float(row["n_windows"] * 4 / 3600))


def _run(fn, specs, workers, what):
    out = []
    if not specs:
        return out
    if workers <= 1:
        R1._init_worker(R1._env())
        it, pool = map(fn, specs), None
    else:
        pool = R1._pool(min(workers, len(specs)))
        it = pool.imap_unordered(fn, specs)
    try:
        for r in it:
            if r.get("error"):
                raise SystemExit(f"{what} {r['case']}: {r['error']}")
            out.append(r)
            log(f"{what} {r['case']} done ({r['s']} s)")
    finally:
        if pool is not None:
            pool.terminate()
    return out


def gate_worker(jobs, label):
    parent = code_shas()
    bad = [(j["case"], j["job"]) for j in jobs if j["shas"] != parent]
    R1.gate(dict(gate=f"G-worker[{label}]", status="PASS" if not bad else "FAIL", jobs=len(jobs), differ=bad[:10],
                 summary=f"{len(jobs)} jobs ran the parent's modules" if not bad else f"{len(bad)} jobs differ"))


def logdir():
    d = R1.out_dir() / "logs"
    d.mkdir(parents=True, exist_ok=True)
    return str(d)


# ============================================================================ main
def main(notebook="EUR_PC6_DATA", repo_commit="local", workers=None):
    R1.OUT_ROOT = R1.WORK / "eureka"
    R1.STATE["tag"] = "pc6_data"
    workers = int(workers or os.environ.get("EUR_WORKERS") or R1.n_workers())
    meta = R1.run_meta("pc6_data", notebook, repo_commit)
    meta.update(eur_pc6_data_sha=sha16(__file__), code_shas=code_shas(), workers=workers, cases_chb=CHB, cases_ext=EXT,
                smoke_case=SMOKE_CASE, **A.cpu_model())
    R1._jdump(R1.out_dir() / "run_meta.json", meta)
    # ---- raw data verified against PhysioNet; record .npz pinned
    R0.R0 = R1.out_dir()
    R0.STATE["tag"] = "inventory"
    inv, cases_df, complete, _ = RC.inventory({"chbmit": CHB + [c for c in EXT if c.startswith("chb")],
                                               "siena": [c for c in EXT if c.startswith("PN")] or None})
    chk = {c["check"]: c["status"] for c in json.loads((RC.out_dir() / "checks.json").read_text())}
    need = ("committed data/summaries = PhysioNet summaries", "CHB-MIT chb01-23: every EDF listed in its summary")
    bad = [n for n in need if chk.get(n) != "PASS"]
    edf = inv[inv.file.str.endswith(".edf")]
    R1.gate(dict(gate="G-raw", status="PASS" if not bad else "FAIL", files=int(len(edf)), failed_checks=bad,
                 from_physionet=int(edf.source.str.startswith("physionet").sum()),
                 summary=f"{len(edf)} EDF verified by sha256 against PhysioNet"))
    src = A.build_views(DEV, TEST, EXT)
    A.gate_data(src)
    # ---- SMOKE: the wrapper in a spawn worker, the combined graph = the record on the first files
    t = time.time()
    gdir = str(R1.out_dir() / "graphs")
    sm = _run(chb_job, [(SMOKE_CASE, SMOKE_FILES, logdir(), gdir)], 1 if workers <= 1 else 2, "smoke")[0]
    R1._jdump(R1.out_dir() / "smoke_feat0.json", sm["feat0"])
    R1.gate(dict(gate="G-stack[smoke]", status="PASS" if sm["stack"][1:] == [3, 18, 18] else "FAIL", stack=sm["stack"],
                 summary=f"builder returned {sm['stack']}"))
    fr = sm["feat0"]
    R1.gate(dict(gate="G-feat0", status=fr["status"], case=SMOKE_CASE, files=SMOKE_FILES,
                 **{k: fr.get(k) for k in ("exact_on_all_windows", "f7_max_abs", "bp5_max_abs", "adj_frac_differing",
                                           "status_chain_windows", "status_all_windows")},
                 summary=f"{SMOKE_CASE} first {SMOKE_FILES} files rebuilt (combined graph) = the record .npz "
                         f"(r2_core.compare_features, scope {RC.GFEAT_SCOPE})"))
    rate = sm["s"] / max(sm["hours"], 1e-9)                                    # s per hour of EEG, one worker
    hours = {c: float(np.load(R1.VIEWS / "earlier" / f"{c}.npz", allow_pickle=True)["is_ictal"].shape[0]) * 4 / 3600
             for c in CHB}
    hours_ext = {c: float(np.load(R1.VIEWS / "ext" / f"{c}_lf.npz", allow_pickle=True)["is_ictal"].shape[0]) * 4 / 3600
                 for c in EXT}
    load = [0.0] * max(1, workers)
    for s_, _ in sorted(((h * rate, c) for c, h in hours.items()), reverse=True):
        load[int(np.argmin(load))] += s_
    ext_s = sum(hours_ext.values()) * rate / 3.0           # x1 runs 2-4 processes per case (computed: rate / 3)
    proj = dict(note="computed: smoke rate (s per hour of EEG, one worker) x hours; CHB-MIT by LPT on the workers; "
                     "external at rate / 3 (x1's 2-4 processes); plus the time already spent",
                rate_s_per_h=round(rate, 1), chb_h=round(max(load) / 3600, 2), ext_h=round(ext_s / 3600, 2),
                elapsed_h=round(R1.hours(), 3), workers=workers)
    proj["projected_total_h"] = round(proj["elapsed_h"] + proj["chb_h"] + proj["ext_h"], 2)
    R1._jdump(R1.out_dir() / "projection.json", proj)
    R1.gate(dict(gate="PROJ", status="PASS" if proj["projected_total_h"] <= REFUSE_H else "FAIL", **proj,
                 summary=f"projected total {proj['projected_total_h']} h (limit {REFUSE_H} h)"))
    R1.phase("smoke", t)
    # ---- CHB-MIT (pool, largest first), then the external set (main process)
    t = time.time()
    jobs = _run(chb_job, [(c, None, logdir(), gdir) for c in sorted(CHB, key=lambda c: -hours[c])], workers, "chb")
    R1.phase("chb", t)
    t = time.time()
    for c in sorted(EXT, key=lambda c: -hours_ext[c]):
        r = ext_case(c, complete, logdir())
        jobs.append(r)
        log(f"ext {c} done ({r['s']} s)")
    R1.phase("ext", t)
    rows = pd.DataFrame([j["row"] for j in jobs])
    rows.to_csv(R1.out_dir() / "cases.csv", index=False)
    stack_bad = [j["case"] for j in jobs if not j.get("installed")]
    R1.gate(dict(gate="G-stack", status="PASS" if not stack_bad else "FAIL", bad=stack_bad,
                 summary=f"{len(jobs)} cases built with three graphs per window"))
    for g, col in (("G-struct", "struct"), ("G-adj", "adj"), ("G-edges", "edges")):
        bad = rows[rows[col] != "PASS"].case.tolist() if col in rows else rows.case.tolist()
        extra = ({"adj_frac_differing_chain_max": float(rows.adj_frac_differing_chain.max()),
                  "cases_exact": int(rows.adj_exact_chain.sum())} if g == "G-adj" and "adj_frac_differing_chain" in rows else {})
        R1.gate(dict(gate=g, status="PASS" if not bad else "FAIL", failed=bad, **extra,
                     summary=f"{len(rows) - len(bad)} of {len(rows)} cases PASS" + (f" {extra}" if extra else "")))
    gate_worker([j for j in jobs if j["job"] == "chb"] + [sm], "pool")
    man = []
    for j in jobs:
        p = Path(j["path"])
        man.append(dict(case=j["case"], file=p.name, bytes=p.stat().st_size,
                        sha256=hashlib.sha256(p.read_bytes()).hexdigest(), n_windows=j["row"]["n_windows"]))
    M = pd.DataFrame(man).sort_values("case")
    M.to_csv(R1.out_dir() / "manifest.csv", index=False)
    missing = sorted(set(CHB + EXT) - set(M.case))
    R1.gate(dict(gate="G-done", status="PASS" if not missing else "FAIL", missing=missing, files=int(len(M)),
                 bytes=int(M.bytes.sum()), summary=f"{len(M)} graph files, {M.bytes.sum() / 1e6:.0f} MB"))
    pd.DataFrame([{k: v for k, v in j.items() if k not in ("row", "shas", "feat0")} for j in jobs + [sm]]).to_csv(
        R1.out_dir() / "jobs.csv", index=False)
    R1.finish_meta(dict(graph_files=int(len(M)), graph_mb=round(float(M.bytes.sum()) / 1e6, 1)))
    (R1.out_dir() / "SUMMARY.md").write_text(
        f"# EUR_PC6_DATA run ({notebook}, commit {repo_commit})\n\nEvery gate PASS (gates.json). Graphs of PC6 (11a wPLI "
        f"only, 11b AEC only; top 20 %) for {len(M)} cases in graphs/ (not committed: Kaggle dataset thesis-pc6-graphs); "
        "manifest.csv = their sha256 (committed); cases.csv = the per-case checks against the record .npz.\n")
    log("EUR_PC6_DATA done")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int)
    a = ap.parse_args()
    main(workers=a.workers)
