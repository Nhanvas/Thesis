#!/usr/bin/env python
"""
eur_9a.py -- EUR_9A: the V5 system with LABEL-FREE z-score statistics on CHB-MIT (Track F, chat D31-F; design
results/eureka_d31f/STEP1_DESIGN.md §3, approved by the author 19/11/2026 20:35). Inference only. Written before any
output.

Question. V5's only label use in its input is the per-patient z-score statistics of CHB-MIT: the record code
preprocessing.compute_subject_stats skips ictal and buffer windows (summary seizure times). The external sets (chb24,
Siena) and the review application already use every 10th window of the whole recording. EUR_9A gives the completely
label-free CHB-MIT number with the same rigour as V5: 4 seeds, k recalibrated by V5's own rule, paired with V5.

One change, everything else the record code:
  statistics   preprocessing.compute_subject_stats(case, raw, {}) -- the record function with an EMPTY seizure map, so
               no window is skipped (every 10th 4-s window of every file, Welford mean / SD); artifact threshold
               5 x SD (only the descriptive is_flag5sd flag uses it; the chain does not)
  features     r2_core.features_record -> c1b_build_trainset.build (the record builder) with those statistics, on the
               defense-time file set (r2_core 'earlier' view: complete minus chb11_12-15, chb21_11), raw EDF verified
               against PhysioNet's SHA256SUMS in this session (r2_core.inventory)
  scoring      r2_r1.r13 (committed checkpoints data/models_v2/gae_v2_clean_seed{42,1,2,3}; distances by
               x1_external.model_outputs; k by p3_levers.calibrate on the 15 development patients, seed 42;
               p3c_freeze.run_budget for the 4 arms) -> r13/lf; the same distances at the record's k -> r13/lf_krec
  control      r2_r1.r10 (V5 = the record rows, gates R1.0-dev / R1.0-test / G-k)

Gates (STOP unless PASS):
  G-raw     every CHB-MIT EDF and summary of the 23 cases verified by sha256 against PhysioNet (r2_core.inventory);
            committed data/summaries = PhysioNet's; the files skipped by design = chb12_27-29
  G-data    every earlier .npz = docs/PROVENANCE_V2.md (eur_abl.gate_data)
  G-stats0  SMOKE: the record statistics (seizure map from the committed summary) recomputed here on chb08 = the
            committed data/processed/chb08_stats.json (mean and SD, relative <= 1e-6): the statistics code and the
            verified raw data reproduce the record
  G-feat0   SMOKE: the record builder with the committed statistics on chb08's first 2 files = the earlier .npz
            (r2_core.compare_features, R0's tolerances and scope)
  R1.0-dev / R1.0-test / G-k   r2_r1.r10 unchanged
  PROJ      projected wall time from the measured smoke and R1.0 (computed; STOP if > 10.5 h)
  G-struct  every label-free .npz = its earlier .npz in file list, window count, file_idx, is_ictal, is_buffer,
            is_signal_loss (exact; these do not depend on the statistics); feature arrays of equal shape
  G-worker  every pool job ran the same eur_9a.py / r2_core.py / record modules as the parent (sha256)
Outputs (WORK/eureka/9a/, small files only; no EEG, no .npz): run_meta.json, gates.json, inventory/, data_sha256.csv,
smoke/, r10/, r13/lf/, r13/lf_krec/, stats_lf/{case}_stats.json, stats_change.csv, struct.csv, jobs.csv, logs/,
projection.json, SUMMARY.md. The reading is done by src/eur_9a_aggregate.py (committed first).
  python src/eur_9a.py [--workers N]
Test mode (synthetic world, build container only): R2_TEST=1 (see src/eur_9a_synthetic_test.py).
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

import eur_abl as A                      # noqa: E402  (views and G-data of the earlier .npz; imports r2_r1 + its guard)

R1, R0, PS = A.R1, A.R0, A.PS
log = R1.log
TAGS, DEV, TEST = A.TAGS, A.DEV, A.TEST
CASES = DEV + TEST                                   # the 23 thesis cases (15 development + 8 test)
SMOKE_CASE, SMOKE_FILES = "chb08", 2
REFUSE_H = 10.5
TEST_MODE = A.TEST_MODE
if TEST_MODE and os.environ.get("EUR9A_TEST_SMOKE_CASE"):            # synthetic world only
    SMOKE_CASE = os.environ["EUR9A_TEST_SMOKE_CASE"]
STATE = R1.STATE
RULE = ("preprocessing.compute_subject_stats(case, raw, {}): the record function with an empty seizure map -> every "
        "10th 4-s window of every file, no ictal / buffer exclusion; artifact threshold = 5 x SD")
STRUCT_KEYS = ("file_idx", "is_ictal", "is_buffer", "is_signal_loss")


def sha16(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def code_shas():
    import preprocessing as P
    import continuous_eval as CE
    import c1b_build_trainset as C1B
    return {n: sha16(p) for n, p in (("eur_9a", __file__), ("eur_abl", A.__file__), ("r2_r1", R1.__file__),
                                     ("r2_core", R0.__file__), ("preprocessing", P.__file__),
                                     ("continuous_eval", CE.__file__), ("c1b_build_trainset", C1B.__file__))}


def raw_view():
    return R0.SCRATCH / "view" / "earlier"


def logdir():
    d = R1.out_dir() / "logs"
    d.mkdir(parents=True, exist_ok=True)
    return str(d)


def _job_meta(t, **kw):
    return dict(kw, s=round(time.time() - t, 1), shas=code_shas(),
                peak_rss_mb=round(__import__("resource").getrusage(0).ru_maxrss / 1024, 1))


# ============================================================================ pool jobs
def stats_job(a):
    """statistics of one case on the earlier view: kind 'record' (seizure map from the committed summary = the record)
    or 'lf' (empty map). Returns mean / SD in volts (float32, as the record function returns them)."""
    case, kind, logdir = a
    t = time.time()
    try:
        import preprocessing as P
        R0._limit_threads()
        smap = P.parse_summary(R0.summary_path(raw_view(), case)) if kind == "record" else {}
        with R0._captured(Path(logdir) / f"{case}_{kind}_stats.log"):
            m, s = P.compute_subject_stats(case, raw_view() / "chbmit", smap)
        return _job_meta(t, case=case, job=f"stats_{kind}", mean=np.asarray(m).tolist(), std=np.asarray(s).tolist(),
                         mean_dtype=str(np.asarray(m).dtype))
    except SystemExit as e:
        return dict(case=case, job=f"stats_{kind}", error=f"STOP: {e}")
    except Exception:                    # noqa: BLE001
        return dict(case=case, job=f"stats_{kind}", error=traceback.format_exc()[-3000:])


def stats_dict(case, m, s, extra=None):
    """the keys of data/processed/{case}_stats.json, built as r2_core.stats_record builds them (float32 x 1e6)."""
    import preprocessing as P
    m, s = np.asarray(m, np.float32), np.asarray(s, np.float32)
    thr = P.ARTIFACT_SD_MULTIPLIER * s
    return {"subject_id": case, "n_interictal": None, "n_ictal": None, "n_rejected": None, "ratio": None,
            "ch_mean_uV": (m * 1e6).tolist(), "ch_std_uV": (s * 1e6).tolist(), "artifact_thresh_uV": (thr * 1e6).tolist(),
            "eur_9a": dict(rule=RULE, counts="not computed (count_windows is not used by the feature builder)",
                           **(extra or {}))}


def feat_job(a):
    """features of one case with given statistics (record builder); kind 'lf' -> R1.VIEWS/new/{case}.npz (the view
    r2_r1.r13 scores); kind 'feat0' (smoke) -> SCRATCH/eur9a/feat0/."""
    case, kind, stats, max_files, logdir = a
    t = time.time()
    try:
        d = R1.SCRATCH / "eur9a" / kind
        npz = R0.features_record(case, raw_view(), stats, d, Path(logdir) / f"{case}_{kind}_features.log",
                                 max_files=max_files)
        res = dict(case=case, job=f"feat_{kind}", npz=str(npz))
        if kind == "lf":
            dst = R1.VIEWS / "new" / f"{case}.npz"
            dst.parent.mkdir(parents=True, exist_ok=True)
            if dst.exists() or dst.is_symlink():
                dst.unlink()
            Path(npz).replace(dst)
            res.update(npz=str(dst), struct=struct_compare(case, dst))
        with np.load(res["npz"], allow_pickle=True) as z:
            res["hours"] = float(len(z["is_ictal"]) * PS.WIN / 3600)
        return _job_meta(t, **res)
    except SystemExit as e:
        return dict(case=case, job=f"feat_{kind}", error=f"STOP: {e}")
    except Exception:                    # noqa: BLE001
        return dict(case=case, job=f"feat_{kind}", error=traceback.format_exc()[-3000:])


def struct_compare(case, new_npz):
    """G-struct on one case: the label-free build vs the earlier .npz (what must not depend on the statistics: exact),
    plus descriptive feature differences."""
    N = np.load(new_npz, allow_pickle=True)
    Rz = np.load(R1.VIEWS / "earlier" / f"{case}.npz", allow_pickle=True)
    rep = dict(case=case, files_equal=[str(x) for x in N["files"]] == [str(x) for x in Rz["files"]],
               n_windows=int(len(N["file_idx"])), n_windows_ref=int(len(Rz["file_idx"])))
    ok = rep["files_equal"] and rep["n_windows"] == rep["n_windows_ref"]
    for k in STRUCT_KEYS:
        eq = ok and np.array_equal(np.asarray(N[k]).astype(np.int64), np.asarray(Rz[k]).astype(np.int64))
        rep[f"{k}_equal"] = bool(eq)
        ok &= eq
    for k in ("adj", "bp5", "f7"):
        eq = tuple(N[k].shape) == tuple(Rz[k].shape)
        rep[f"{k}_shape_equal"] = bool(eq)
        ok &= eq
    if ok:
        sl = np.asarray(N["is_signal_loss"], bool)
        for k in ("f7", "bp5"):
            a, b = np.asarray(N[k], np.float64)[~sl], np.asarray(Rz[k], np.float64)[~sl]
            fin = np.isfinite(a) & np.isfinite(b)
            rep[f"{k}_maxabs_diff"] = float(np.abs(a - b)[fin].max()) if fin.any() else 0.0
        an, ar = N["adj"], Rz["adj"]
        nd, tot = 0, 0
        for s in range(0, len(an), 8192):
            x, y = an[s:s + 8192][~sl[s:s + 8192]].astype(np.float32), ar[s:s + 8192][~sl[s:s + 8192]].astype(np.float32)
            nd += int(((np.abs(x - y) > R0.TOL["adj_entry"]) & ~(np.isnan(x) & np.isnan(y))).sum())
            tot += x.size
        rep["adj_frac_entries_differing"] = nd / max(tot, 1)
        rep["flag5sd_windows"] = int(np.asarray(N["is_flag5sd"]).sum())
        rep["flag5sd_windows_ref"] = int(np.asarray(Rz["is_flag5sd"]).sum())
    rep["status"] = "PASS" if ok else "FAIL"
    return rep


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
    bad = [(j["case"], j["job"], {k: v for k, v in j["shas"].items() if parent.get(k) != v})
           for j in jobs if j["shas"] != parent]
    R1.gate(dict(gate=f"G-worker[{label}]", status="PASS" if not bad else "FAIL", jobs=len(jobs), differ=bad[:10],
                 summary=f"{len(jobs)} jobs ran the parent's modules" if not bad else f"{len(bad)} jobs differ"))


# ============================================================================ phases
def gate_raw(cases_df, inv):
    chk = json.loads((R0.out_dir() / "checks.json").read_text())
    need = ("committed data/summaries = PhysioNet summaries", "CHB-MIT files skipped by design (missing common channel)",
            "CHB-MIT chb01-23: every EDF listed in its summary")
    got = {c["check"]: c for c in chk}
    bad = [n for n in need if got.get(n, {}).get("status") != "PASS"]
    miss = sorted(set(CASES) - set(cases_df.case))
    edf = inv[inv.file.str.endswith(".edf")]
    R1.gate(dict(gate="G-raw", status="PASS" if not bad and not miss else "FAIL", files=int(len(edf)),
                 from_physionet=int(edf.source.str.startswith("physionet").sum()), failed_checks=bad, cases_missing=miss,
                 earlier_hours=round(float(cases_df[cases_df.case.isin(CASES)].earlier_hours_used_windows.sum()), 2),
                 summary=f"{len(edf)} EDF verified by sha256 against PhysioNet "
                         f"({int(edf.source.str.startswith('physionet').sum())} downloaded); checks {list(need)}"))


def smoke(workers):
    """G-stats0 and G-feat0 on SMOKE_CASE, in parallel; returns the measured rates (s per hour of EEG, one worker)."""
    t = time.time()
    committed = R0.committed_stats(SMOKE_CASE)
    if committed is None:
        raise SystemExit(f"STOP: no committed data/processed/{SMOKE_CASE}_stats.json")
    jobs = []
    pool = R1._pool(2) if workers > 1 else None
    try:
        if pool is None:
            R1._init_worker(R1._env())
            r_st = stats_job((SMOKE_CASE, "record", logdir()))
            r_ft = feat_job((SMOKE_CASE, "feat0", committed, SMOKE_FILES, logdir()))
        else:
            f1 = pool.apply_async(stats_job, ((SMOKE_CASE, "record", logdir()),))
            f2 = pool.apply_async(feat_job, ((SMOKE_CASE, "feat0", committed, SMOKE_FILES, logdir()),))
            r_st, r_ft = f1.get(), f2.get()
    finally:
        if pool is not None:
            pool.terminate()
    for r in (r_st, r_ft):
        if r.get("error"):
            raise SystemExit(f"smoke {r['case']} {r['job']}: {r['error']}")
        jobs.append(r)
    new = stats_dict(SMOKE_CASE, r_st["mean"], r_st["std"])
    rep = {}
    for k in ("ch_mean_uV", "ch_std_uV"):
        a, b = np.asarray(new[k], float), np.asarray(committed[k], float)
        rep[f"{k}_max_rel"] = float(np.max(np.abs(a - b) / np.maximum(np.abs(b), 1e-30)))
    ok = all(v <= R0.TOL["stats_rel"] for v in rep.values())
    R1.gate(dict(gate="G-stats0", status="PASS" if ok else "FAIL", case=SMOKE_CASE, **rep,
                 summary=f"{SMOKE_CASE}: record statistics recomputed = committed stats.json "
                         f"(max relative {max(rep.values()):.1e}; tolerance {R0.TOL['stats_rel']})"))
    fr = R0.compare_features(r_ft["npz"], R0.locate_earlier(SMOKE_CASE), n_files=SMOKE_FILES)
    R1._jdump(R1.out_dir() / "smoke_feat0.json", fr)
    R1.gate(dict(gate="G-feat0", status=fr["status"], case=SMOKE_CASE, files=SMOKE_FILES,
                 **{k: fr.get(k) for k in ("exact_on_all_windows", "f7_max_abs", "bp5_max_abs", "adj_frac_differing",
                                           "status_chain_windows", "status_all_windows")},
                 summary=f"{SMOKE_CASE} first {SMOKE_FILES} files with the committed statistics = earlier .npz "
                         f"(r2_core.compare_features, scope {R0.GFEAT_SCOPE})"))
    gate_worker(jobs, "smoke")
    eeg_case = float(R1.load_case(SMOKE_CASE, "earlier")[0]["is_ictal"].shape[0]) * PS.WIN / 3600
    rates = dict(stats_s_per_h=r_st["s"] / eeg_case, feat_s_per_h=r_ft["s"] / max(r_ft["hours"], 1e-9),
                 smoke_s=round(time.time() - t, 1), smoke_case_h=round(eeg_case, 3), feat0_h=round(r_ft["hours"], 3))
    R1.phase("smoke", t)
    pd.DataFrame([{k: v for k, v in j.items() if k not in ("mean", "std")} for j in jobs]).to_csv(
        R1.out_dir() / "smoke_jobs.csv", index=False)
    return rates


def projection(rates, hours_by_case, r10_s, workers):
    """computed estimate: LPT schedule of the 23 label-free builds (stats + features at the smoke rates) on the
    workers, plus r13 + rescore = 1.2 x the measured R1.0 time, plus the time already spent."""
    per = sorted(((h * (rates["stats_s_per_h"] + rates["feat_s_per_h"]), c) for c, h in hours_by_case.items()),
                 reverse=True)
    load = [0.0] * max(1, workers)
    for s, _ in per:
        i = int(np.argmin(load))
        load[i] += s
    build_s = max(load)
    proj = dict(note="computed estimate (smoke rates x hours, LPT on workers; r13 + rescore = 1.2 x measured R1.0)",
                elapsed_h=round(R1.hours(), 3), build_h=round(build_s / 3600, 3), r10_measured_h=round(r10_s / 3600, 3),
                r13_h=round(1.2 * r10_s / 3600, 3), workers=workers, **{k: round(v, 3) for k, v in rates.items()})
    proj["projected_total_h"] = round(proj["elapsed_h"] + proj["build_h"] + proj["r13_h"], 2)
    R1._jdump(R1.out_dir() / "projection.json", proj)
    R1.gate(dict(gate="PROJ", status="PASS" if proj["projected_total_h"] <= REFUSE_H else "FAIL", **proj,
                 summary=f"projected total {proj['projected_total_h']} h (limit {REFUSE_H} h)"))


def build_lf(workers, hours_by_case):
    """label-free statistics, then the features, per case (one pool, largest first)."""
    t = time.time()
    order = sorted(CASES, key=lambda c: -hours_by_case[c])
    st = {r["case"]: r for r in _run(stats_job, [(c, "lf", logdir()) for c in order], workers, "stats[lf]")}
    sd_dir = R1.out_dir() / "stats_lf"
    sd_dir.mkdir(parents=True, exist_ok=True)
    stats, rows = {}, []
    for c in order:
        stats[c] = stats_dict(c, st[c]["mean"], st[c]["std"], dict(stats_s=st[c]["s"]))
        (sd_dir / f"{c}_stats.json").write_text(json.dumps(stats[c], indent=1))
        rec = R0.committed_stats(c)
        mo, so = np.asarray(rec["ch_mean_uV"], float), np.asarray(rec["ch_std_uV"], float)
        mn, sn = np.asarray(stats[c]["ch_mean_uV"], float), np.asarray(stats[c]["ch_std_uV"], float)
        for ch in range(len(so)):
            rows.append(dict(case=c, channel=ch, mean_record_uV=mo[ch], mean_lf_uV=mn[ch], std_record_uV=so[ch],
                             std_lf_uV=sn[ch], std_rel_change=(sn[ch] - so[ch]) / so[ch],
                             mean_shift_in_record_sd=(mn[ch] - mo[ch]) / so[ch]))
    pd.DataFrame(rows).to_csv(R1.out_dir() / "stats_change.csv", index=False)
    R1.phase("stats_lf", t)
    t = time.time()
    ft = _run(feat_job, [(c, "lf", stats[c], None, logdir()) for c in order], workers, "features[lf]")
    R1.phase("features_lf", t)
    struct = pd.DataFrame([r["struct"] for r in ft])
    struct.to_csv(R1.out_dir() / "struct.csv", index=False)
    bad = struct[struct.status != "PASS"].case.tolist()
    R1.gate(dict(gate="G-struct", status="PASS" if not bad and len(struct) == len(CASES) else "FAIL",
                 cases=int(len(struct)), failed=bad,
                 summary=f"{len(struct)} label-free builds: file list, windows, file_idx, is_ictal, is_buffer, "
                         f"is_signal_loss = earlier .npz; {len(bad)} differ"))
    jobs = list(st.values()) + ft
    gate_worker(jobs, "build")
    return jobs


def main(notebook="EUR_9A", repo_commit="local", workers=None):
    R1.OUT_ROOT = R1.WORK / "eureka"
    workers = int(workers or os.environ.get("EUR_WORKERS") or R1.n_workers())
    meta = R1.run_meta("9a", notebook, repo_commit)
    meta.update(eur_9a_sha=sha16(__file__), code_shas=code_shas(), workers=workers, rule=RULE, cases=CASES,
                smoke_case=SMOKE_CASE)
    R1._jdump(R1.out_dir() / "run_meta.json", meta)
    # ---- raw data verified against PhysioNet; earlier .npz pinned
    R0.R0 = R1.out_dir()
    R0.STATE["tag"] = "inventory"
    inv, cases_df, complete, earlier = R0.inventory({"chbmit": CASES})
    gate_raw(cases_df, inv)
    src = A.build_views(DEV, TEST, [])
    A.gate_data(src)
    hours_by_case = {c: float(cases_df.set_index("case").earlier_hours_used_windows[c]) for c in CASES}
    # ---- SMOKE (the small check before the full run)
    rates = smoke(workers)
    # ---- V5 control = the record (R1.0, G-k)
    t = time.time()
    R1.r10(DEV, TEST, [], workers=workers, with_k=True)
    r10_s = time.time() - t
    R1.phase("r10", t)
    projection(rates, hours_by_case, r10_s, workers)
    # ---- label-free build, then scoring (k recalibrated; and at the record's k)
    jobs = build_lf(workers, hours_by_case)
    t = time.time()
    k_lf, _, dres = R1.r13(DEV, TEST, [], R1.REPO / "data" / "models_v2", "lf", workers)
    R1.rescore([(c, "new") for c in CASES], "lf", "lf_krec", A.K_RECORD, workers)
    R1.phase("r13_lf", t)
    pd.DataFrame([{k: v for k, v in j.items() if k not in ("mean", "std", "shas", "struct")} for j in jobs]).to_csv(
        R1.out_dir() / "jobs.csv", index=False)
    R1.finish_meta(dict(k_lf=k_lf, k_record=A.K_RECORD))
    (R1.out_dir() / "SUMMARY.md").write_text(
        f"# EUR_9A run ({notebook}, commit {repo_commit})\n\nEvery gate PASS (gates.json). V5 with label-free z-score "
        f"statistics on the 23 CHB-MIT cases ({RULE}). Rows: r13/lf (k recalibrated), r13/lf_krec (record k), r10 (V5).\n"
        "No reading here: src/eur_9a_aggregate.py makes the tables (committed before this run).\n")
    log("EUR_9A done")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int)
    a = ap.parse_args()
    main(workers=a.workers)
