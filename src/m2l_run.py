#!/usr/bin/env python
"""
m2l_run.py -- notebook entry of milestone M2, stream L (chat F2-03; design results/m2l/DESIGN_L2.md, approved by the
author 23/11/2026 14:19). Written before any output. Three modes (environment M2L_MODE):

  L2       development only (15 patients); M2L_S = R (notebook M2L_L2_REC, tag l2_rec) or B (M2L_L2_ROB, tag l2_rob):
           G-raw, G-data, [G-c], SMOKE (G-stats1, G-feat1, rate), R1.0-dev + G-k, G-chain, G-split, PROJ, per-recording
           build (G-struct, G-worker), k per covariance, scoring of the arms S-{LW,MCD}-{F,N,FX}.
  L3SHORT  development segments of M2L_SEGS minutes (tags l3short_a / l3short_b): the chosen arm of
           results/m2l/l2/selection.json (G-sel), its k, the length guard off (MCD needs > 16 valid windows).
  L3EVAL   test, chb24, Siena (tag l3eval): the chosen arm with its k and the minimum length of
           results/m2l/l3short/minlen.json (G-sel); V5 control R1.0-test + GE.
Outputs WORK/m2l/<tag>/ (small files only; no EEG, no .npz): run_meta.json, gates.json, inventory/, data_sha256.csv,
r10/, smoke.json, chain/, k.json, per_subject.csv, errors.csv, per_file.csv, stats_per_recording.csv, struct.csv,
jobs.csv, projection.json, SUMMARY.md. The reading is src/m2l_read.py (committed before the outputs).
Test mode (synthetic world, build container only): R2_TEST=1 (src/m2l_synthetic_test.py).
"""
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import m2l_core as M                     # noqa: E402

A, R1, R0, PS, P3L, P3C, E22, X1, P = M.A, M.R1, M.R0, M.PS, M.P3L, M.P3C, M.E22, M.X1, M.P
log, TAGS, DEV, TEST, EXT = M.log, M.TAGS, M.DEV, M.TEST, M.EXT
SMOKE_CASE, SMOKE_FILES = os.environ.get("M2L_TEST_SMOKE_CASE", "chb08"), 2
REFUSE_H = 10.5
SCORE_FACTOR = 0.08                       # scoring time / build time (computed estimate for PROJ; reported)
LOAD_FACTOR = 1.45                        # L3 PROJ: build time measured in L2 / L2's projection (18,154 s / 12,488 s;
                                          # 16,664 s / 11,434 s), i.e. 4 loaded workers against the 2-worker smoke
TOLS = dict(stats_rel=1e-9, stats_lf_rel=1e-6, split_rel=1e-12)
SEL = M.REPO / "results" / "m2l" / "l2" / "selection.json"
MINLEN = M.REPO / "results" / "m2l" / "l3short" / "minlen.json"


def gate_worker(jobs, label):
    parent = M.code_shas()
    bad = [(j.get("case"), j.get("file"), {k: v for k, v in j["shas"].items() if parent.get(k) != v})
           for j in jobs if j.get("shas") != parent]
    R1.gate(dict(gate=f"G-worker[{label}]", status="PASS" if not bad else "FAIL", jobs=len(jobs), differ=bad[:10],
                 summary=f"{len(jobs)} jobs ran the parent's modules" if not bad else f"{len(bad)} jobs differ"))


def run_pool(fn, specs, workers, what):
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
                raise SystemExit(f"{what} {r.get('case')} {r.get('file', '')}: {r['error']}")
            out.append(r)
    finally:
        if pool is not None:
            pool.terminate()
    log(f"{what}: {len(out)} jobs done")
    return out


# ============================================================================ G-raw
def gate_raw(cases, cases_df, inv, need_checks):
    chk = json.loads((R0.out_dir() / "checks.json").read_text())
    got = {c["check"]: c for c in chk}
    bad = [n for n in need_checks if got.get(n, {}).get("status") != "PASS"]
    miss = sorted(set(cases) - set(cases_df.case))
    edf = inv[inv.file.str.endswith(".edf")]
    R1.gate(dict(gate="G-raw", status="PASS" if not bad and not miss else "FAIL", files=int(len(edf)),
                 from_physionet=int(edf.source.str.startswith("physionet").sum()), failed_checks=bad, cases_missing=miss,
                 summary=f"{len(edf)} EDF verified by sha256 against PhysioNet; checks {need_checks}"))


# ============================================================================ SMOKE (L2)
def smoke(S, cc, earlier, workers):
    t = time.time()
    files = M.chb_files(SMOKE_CASE, earlier)
    rep = {}
    # G-stats1 (a): per-recording statistics = an independent loop over preprocessing.filter_window (mne raw)
    path, sz, kind, notch = files[0]
    data = X1.load_18(Path(path), kind)
    n = data.shape[1] // M.WS
    Xm = M.sampled(data, notch, n)
    raw = P.open_edf(path)
    Xi = np.concatenate([P.filter_window(raw, int(i) * M.WS, (int(i) + 1) * M.WS) for i in M.sample_index(n)], axis=1)
    worst = 0.0
    for kind_s in ("R", "B"):
        cck = cc if cc is not None else np.ones(18)
        a, b = M.stats_of(Xm, kind_s, cck), M.stats_of(Xi, kind_s, cck)
        for u, v in zip(a, b):
            worst = max(worst, float(np.max(np.abs(u - v) / np.maximum(np.abs(b[1]), 1e-30))))
    rep["a_max_rel_to_scale"] = worst
    # G-stats1 (b): pooled with one counter (sorted files) = EUR_9A's committed label-free statistics (record function)
    datas = [X1.load_18(Path(p), k_) for p, _, k_, _ in sorted(files, key=lambda f: Path(f[0]).name)]
    mu, sd = M.pooled_record_stats([d for d in datas if d is not None], 60.0)
    ref_f = M.REPO / "results" / "eureka_d31f" / "9a" / "stats_lf" / f"{SMOKE_CASE}_stats.json"
    if ref_f.exists():
        ref = json.loads(ref_f.read_text())
        rmu, rsd = np.asarray(ref["ch_mean_uV"], float) * 1e-6, np.asarray(ref["ch_std_uV"], float) * 1e-6
        rep["b_reference"] = str(ref_f.relative_to(M.REPO))
    else:                                    # synthetic world: the record function itself
        rm, rs = P.compute_subject_stats(SMOKE_CASE, Path(earlier) / "chbmit", {})
        rmu, rsd = np.asarray(rm, float), np.asarray(rs, float)
        rep["b_reference"] = "preprocessing.compute_subject_stats(case, view, {}) (test mode)"
    rep["b_sd_max_rel"] = float(np.max(np.abs(sd - rsd) / rsd))
    rep["b_mean_max_rel_to_sd"] = float(np.max(np.abs(mu - rmu) / rsd))
    ok = (rep["a_max_rel_to_scale"] <= TOLS["stats_rel"] and rep["b_sd_max_rel"] <= TOLS["stats_lf_rel"]
          and rep["b_mean_max_rel_to_sd"] <= TOLS["stats_lf_rel"])
    R1.gate(dict(gate="G-stats1", status="PASS" if ok else "FAIL", case=SMOKE_CASE, **rep,
                 summary=f"{SMOKE_CASE}: per-recording statistics = independent loop (max {worst:.1e}); pooled = "
                         f"label-free record statistics (SD {rep['b_sd_max_rel']:.1e}, mean {rep['b_mean_max_rel_to_sd']:.1e})"))
    # G-feat1: the per-recording builder with the committed record statistics = the earlier .npz (first 2 files)
    st = R0.committed_stats(SMOKE_CASE)
    if st is None:
        raise SystemExit(f"STOP: no committed data/processed/{SMOKE_CASE}_stats.json")
    rmu = np.asarray(st["ch_mean_uV"], np.float64) * 1e-6
    rsd = np.asarray(st["ch_std_uV"], np.float64) * 1e-6
    thr = np.asarray(st["artifact_thresh_uV"], np.float64) * 1e-6
    parts, names = [], []
    for fi, (p, s_, k_, nt) in enumerate(files[:SMOKE_FILES]):
        d = X1.load_18(Path(p), k_)
        r = M.features(d, nt, s_, (rmu, rsd), buffer=True, flag_thr=thr)
        r["file_idx"] = np.full(r["n"], fi, np.int16)
        parts.append(r)
        names.append(Path(p).name)
    npz = M.SCR / "smoke" / f"{SMOKE_CASE}_SMOKE.npz"
    npz.parent.mkdir(parents=True, exist_ok=True)
    keys = ("adj", "bp5", "f7", "is_ictal", "is_buffer", "is_flag5sd", "is_signal_loss", "file_idx")
    np.savez(npz, files=np.array(names, dtype=object), **{k: np.concatenate([q[k] for q in parts]) for k in keys})
    fr = R0.compare_features(npz, R0.locate_earlier(SMOKE_CASE), n_files=SMOKE_FILES)
    R1._jdump(R1.out_dir() / "smoke_feat1.json", fr)
    R1.gate(dict(gate="G-feat1", status=fr["status"], case=SMOKE_CASE, files=SMOKE_FILES,
                 **{k: fr.get(k) for k in ("exact_on_all_windows", "f7_max_abs", "bp5_max_abs", "adj_frac_differing")},
                 summary=f"{SMOKE_CASE} first {SMOKE_FILES} files, per-recording builder with the committed statistics "
                         f"= earlier .npz (r2_core.compare_features)"))
    # rate: the per-recording job on the first 2 files (S, both covariances, 4 seeds)
    specs = [(SMOKE_CASE, fi, str(p), k_, nt, s_, S, cc, None, M.SCR / "smoke" / f"rec_{fi}.npz",
              dict(min_valid=M.MIN_GUARD, min_n=0), M.COVS) for fi, (p, s_, k_, nt) in enumerate(files[:SMOKE_FILES])]
    jobs = run_pool(M.rec_job, specs, min(workers, len(specs)), "smoke rec")
    gate_worker(jobs, "smoke")
    h = sum(j["hours"] for j in jobs)
    rate = dict(rec_s_per_h=sum(j["s"] for j in jobs) / max(h, 1e-9), smoke_hours=round(h, 3),
                smoke_s=round(time.time() - t, 1), timing=[{k: j.get(k) for k in ("file", "s", "gae_s", "LW_s", "MCD_s")}
                                                          for j in jobs])
    R1._jdump(R1.out_dir() / "smoke.json", dict(rep, **rate))
    R1.phase("smoke", t)
    return rate


# ============================================================================ G-chain / G-split (L2)
def chain_and_split(cases):
    """G-chain: the m2l detection and scoring at the PATIENT unit on V5's stored distances (R1.0) = the record rows of
    p3c_freeze (budget L2f) exactly. G-split: the one-file scoring of the same events summed per patient = the patient
    counts (the bookkeeping of the unit change)."""
    t = time.time()
    rows, errs, split_bad, n_split = [], [], [], 0
    for c in cases:
        ctx, _ = R1.ctx_from_store(c, "earlier", "r10")
        pctx = M.patient_ctx(ctx["z"])
        for tag in TAGS:
            x, smm = M.series(ctx, tag)
            k = M.K_RECORD * (1.05 if M.TEST_MODE and os.environ.get("M2L_TEST_CHAIN_SHIFT") else 1.0)  # NEG test only
            q = P3L.q_of(smm, k)
            top, stages, pairs = M.detect(ctx, x, q, 0.005, P3C.CAP)
            M.score_rows(pctx, c, tag, "L2f", top, stages, pairs, rows, errs)
            if tag == TAGS[0]:
                ev = stages["cpd"]
                tot = np.zeros(3, np.int64)
                hsum = 0.0
                for f in np.unique(pctx["fidx"]):
                    m = pctx["fidx"] == f
                    fz = {k: np.asarray(v)[m] for k, v in pctx["z"].items()}
                    fz["file_idx"] = np.zeros(int(m.sum()), np.int16)
                    tp, fp, nr, h = PS.score(dict(z=fz), {0: ev.get(f, [])})
                    tot += (tp, fp, nr)
                    hsum += h
                ptp, pfp, pnr, ph = PS.score(pctx, ev)
                n_split += 1
                if tuple(tot) != (ptp, pfp, pnr) or abs(hsum - ph) > TOLS["split_rel"] * max(ph, 1.0):
                    split_bad.append(dict(case=c, files_sum=[int(v) for v in tot] + [hsum], patient=[ptp, pfp, pnr, ph]))
    o = R1.out_dir() / "chain"
    o.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(o / "chain_rows.csv", index=False)
    pd.DataFrame(errs).to_csv(o / "chain_errors.csv", index=False)
    ref = pd.read_csv(M.REPO / "results" / "p3c_freeze" / "per_subject.csv")
    ref = ref[ref.subject.isin(cases) & (ref.budget == "L2f")]
    n, bad = R1._cmp_rows(rows, ref, ["subject", "seed", "budget", "stage"], R1.ROW_INT + ["review_s", "rec_s"],
                          ["top", "nonict_h"])
    eref = pd.read_csv(M.REPO / "results" / "p3c_freeze" / "errors.csv")
    ne, ebad = R1._cmp_errors(errs, eref[eref.subject.isin(cases) & (eref.budget == "L2f")],
                              ["subject", "seed", "budget"], R1.ERR_COLS)
    R1.gate(dict(gate="G-chain", status="PASS" if not bad and not ebad and n == len(ref) else "FAIL", rows=n,
                 rows_ref=int(len(ref)), error_pairs=ne, mismatches=bad[:30], error_mismatches=ebad[:10],
                 summary=f"m2l patient-unit path on V5's distances: {n} rows, {ne} error pairs = p3c_freeze L2f; "
                         f"{len(bad) + len(ebad)} differ"))
    R1.gate(dict(gate="G-split", status="PASS" if not split_bad else "FAIL", patients=n_split, differ=split_bad[:10],
                 summary=f"{n_split} patients: one-file SzCORE counts summed = patient counts (V5 seed 42, cpd)"))
    R1.phase("chain_split", t)


# ============================================================================ build, struct, k, scoring
def projection(rate, hours, workers, extra_s=0.0):
    load = [0.0] * max(1, workers)
    for h in sorted(hours, reverse=True):
        i = int(np.argmin(load))
        load[i] += h * rate["rec_s_per_h"]
    build_h = max(load) / 3600
    proj = dict(note="computed estimate: smoke rate x hours, LPT on workers; scoring = SCORE_FACTOR x build",
                elapsed_h=round(R1.hours(), 3), build_h=round(build_h, 3), score_h=round(SCORE_FACTOR * build_h, 3),
                extra_h=round(extra_s / 3600, 3), workers=workers, rec_s_per_h=round(rate["rec_s_per_h"], 2),
                hours_of_eeg=round(float(sum(hours)), 2))
    proj["projected_total_h"] = round(proj["elapsed_h"] + build_h * (1 + SCORE_FACTOR) + proj["extra_h"], 2)
    R1._jdump(R1.out_dir() / "projection.json", proj)
    R1.gate(dict(gate="PROJ", status="PASS" if proj["projected_total_h"] <= REFUSE_H else "FAIL", **proj,
                 summary=f"projected total {proj['projected_total_h']} h (limit {REFUSE_H} h)"))


def rec_specs(case, files, S, cc, guard, covs, segs=None):
    specs = []
    for fi, (p, sz, kind, notch) in enumerate(files):
        if segs is None:
            specs.append((case, fi, str(p), kind, notch, sz, S, cc, None,
                          M.SCR / "rec" / case / f"{fi:03d}.npz", guard, covs))
        else:
            n = None
            for L in segs:
                if n is None:
                    import mne
                    raw = mne.io.read_raw_edf(str(p), preload=False, verbose=False)
                    n = int(raw.n_times // (raw.info["sfreq"] * M.WIN))
                for si, (a_w, b_w) in enumerate(M.segment_cuts(n, sz, L)):
                    specs.append((f"{case}@{L}", fi, str(p), kind, notch, sz, S, cc, (a_w, b_w),
                                  M.SCR / "seg" / str(L) / case / f"{fi:03d}_{si:03d}.npz", guard, covs))
    return specs


def run_pool_multi(specs, workers, what):
    """rec_job_multi jobs; the per-segment results are flattened (each keeps the job's module shas)."""
    out = run_pool(M.rec_job_multi, specs, workers, what)
    return out, [m for r in out for m in r["multi"]]


def edf_windows(path):
    import mne
    raw = mne.io.read_raw_edf(str(path), preload=False, verbose=False)
    return int(raw.n_times // (raw.info["sfreq"] * M.WIN)), float(raw.n_times / raw.info["sfreq"] / 3600)


def multi_specs(case, files, S, cc, guard, covs, segs):
    specs, hours = [], []
    for fi, (p, sz, kind, notch) in enumerate(files):
        n, h = edf_windows(p)
        lst = []
        for L in segs:
            for si, (a_w, b_w) in enumerate(M.segment_cuts(n, sz, L)):
                lst.append((f"{case}@{L}", (a_w, b_w), M.SCR / "seg" / str(L) / case / f"{fi:03d}_{si:03d}.npz"))
        specs.append((case, fi, str(p), kind, notch, sz, S, cc, lst, guard, covs))
        hours.append(h)
    return specs, hours


def pick_smoke(specs, hours):
    """a 1-h recording that the record does not skip by design (else the longest such file: synthetic world)."""
    skip = {f for fs in R0.SKIPPED_BY_DESIGN.values() for f in fs}
    ok = [i for i, a in enumerate(specs) if Path(a[2]).name not in skip]
    one = [i for i in ok if 0.9 < hours[i] < 1.1]
    return one[0] if one else max(ok, key=lambda i: hours[i])


def l3_smoke_proj(fn, spec, hours, workers, what):
    """L3 PROJ: one job of the build measured here (one worker), rate x LOAD_FACTOR, LPT over the files."""
    t = time.time()
    r = run_pool(fn, [spec], 1, f"smoke {what}")[0]
    h = r.get("hours") or 1e-9
    rate = dict(rec_s_per_h=r["s"] / h * LOAD_FACTOR, smoke_file=r.get("file"), smoke_hours=round(h, 3),
                smoke_s=r["s"], load_factor=LOAD_FACTOR)
    R1._jdump(R1.out_dir() / "smoke.json", rate)
    R1.phase("smoke", t)
    projection(rate, hours, workers)
    return r


def struct_gate(jobs_by_case, ref_kind, label):
    """G-struct: per patient, the per-recording bookkeeping concatenated = the reference .npz (exact)."""
    rows = []
    for case, js in sorted(jobs_by_case.items()):
        base = case.split("@")[0]
        z, recs, jj = M.load_recs(js)
        if ref_kind == "ext":
            Rz, _ = R1.load_case(base, "ext")
            keys = ("is_ictal", "is_signal_loss")
        else:
            Rz = np.load(R1.VIEWS / "earlier" / f"{base}.npz", allow_pickle=True)
            keys = ("is_ictal", "is_buffer", "is_signal_loss")
        files = list(dict.fromkeys(j["file"] for j in jj))
        rep = dict(case=case, files_equal=files == [str(x) for x in Rz["files"]],
                   n=int(len(z["is_ictal"])), n_ref=int(len(Rz["is_ictal"])))
        ok = rep["files_equal"] and rep["n"] == rep["n_ref"]
        for k in keys:
            eq = ok and np.array_equal(np.asarray(z[k]).astype(np.int64), np.asarray(Rz[k]).astype(np.int64))
            rep[f"{k}_equal"] = bool(eq)
            ok &= eq
        if ok:                                   # file_idx: recordings (or a recording's segments) in file order
            fi_rec = np.concatenate([np.full(int(r["n"]), j["fi"]) for r, j in zip(recs, jj)])
            fi_ref = np.asarray(Rz["file_idx"]).astype(int)
            rank = {f: i for i, f in enumerate(sorted(set(fi_rec)))}
            eq = np.array_equal(np.array([rank[f] for f in fi_rec]), fi_ref)
            rep["file_idx_equal"] = bool(eq)
            ok &= eq
        rep["status"] = "PASS" if ok else "FAIL"
        rows.append(rep)
    df = pd.DataFrame(rows)
    df.to_csv(R1.out_dir() / f"struct_{label}.csv", index=False)
    bad = df[df.status != "PASS"].case.tolist()
    R1.gate(dict(gate=f"G-struct[{label}]", status="PASS" if not bad else "FAIL", cases=int(len(df)), failed=bad,
                 summary=f"{len(df)} patients: recordings, windows, labels, signal loss, file order = reference"))


def calibrate_k(jobs_by_case, covs, cases):
    ks = {}
    for cov in covs:
        sms = []
        for c in cases:
            _, recs, _ = M.load_recs(jobs_by_case[c])
            sms.append(M.smm_patient(recs, cov))
        ks[cov] = float(P3L.calibrate(sms))
    return ks


def score_all(jobs_by_case, set_of, S, ks, floors, covs, workers, label):
    specs = [(c, set_of[c], S, ks, js, floors, covs) for c, js in jobs_by_case.items()]
    specs.sort(key=lambda a: -sum(j.get("n", 0) for j in a[4] if not j["skipped"]))
    res = run_pool(M.score_job, specs, workers, f"score[{label}]")
    gate_worker(res, f"score_{label}")
    return res


def write_outputs(jobs, res, suffix=""):
    o = R1.out_dir()
    pd.DataFrame([r for x in res for r in x["rows"]]).to_csv(o / f"per_subject{suffix}.csv", index=False)
    pd.DataFrame([r for x in res for r in x["errs"]]).to_csv(o / f"errors{suffix}.csv", index=False)
    pd.DataFrame([r for x in res for r in x["frows"]]).to_csv(o / f"per_file{suffix}.csv", index=False)
    st = []
    for j in jobs:
        if j["skipped"]:
            continue
        d = np.load(j["npz"])
        for ch in range(len(d["mu"])):
            st.append(dict(case=j["case"], file=j["file"], seg=json.dumps(j.get("seg")), channel=P.COMMON_CHANNELS[ch],
                           centre_uV=float(d["mu"][ch]) * 1e6, scale_uV=float(d["sd"][ch]) * 1e6))
    pd.DataFrame(st).to_csv(o / f"stats_per_recording{suffix}.csv", index=False)
    pd.DataFrame([{k: v for k, v in j.items() if k not in ("shas", "npz")} for j in jobs]).to_csv(
        o / f"jobs{suffix}.csv", index=False)


def group(jobs):
    out = {}
    for j in jobs:
        out.setdefault(j["case"], []).append(j)
    return out


def setup(tag, notebook, repo_commit, workers):
    R1.OUT_ROOT = R1.WORK / "m2l"
    workers = int(workers or os.environ.get("M2L_WORKERS") or R1.n_workers())
    meta = R1.run_meta(tag, notebook, repo_commit)
    meta.update(m2l_code_shas=M.code_shas(), workers=workers, design="results/m2l/DESIGN_L2.md")
    try:
        meta["cpu_model"] = next((ln.split(":", 1)[1].strip() for ln in open("/proc/cpuinfo") if ln.startswith("model name")), None)
    except OSError:
        meta["cpu_model"] = None
    R1._jdump(R1.out_dir() / "run_meta.json", meta)
    return workers


def inventory(dbs, cases, need):
    R0.R0 = R1.out_dir()
    R0.STATE["tag"] = "inventory"
    inv, cases_df, complete, earlier = R0.inventory(dbs)
    gate_raw(cases, cases_df, inv, need)
    return inv, cases_df, complete, earlier


CHB_CHECKS = ["committed data/summaries = PhysioNet summaries", "CHB-MIT chb01-23: every EDF listed in its summary"]


def read_selection():
    if not SEL.exists():
        R1.gate(dict(gate="G-sel", status="FAIL", summary=f"{SEL.relative_to(M.REPO)} missing (read L2 first)"))
    s = json.loads(SEL.read_text())
    return s


# ============================================================================ modes
def main_l2(notebook, repo_commit, workers=None):
    S = os.environ.get("M2L_S", "R")
    if S not in M.S_KINDS:
        raise SystemExit(f"STOP: M2L_S = {S}")
    workers = setup("l2_rec" if S == "R" else "l2_rob", notebook, repo_commit, workers)
    inv, cases_df, complete, earlier = inventory({"chbmit": DEV}, DEV, CHB_CHECKS)
    src = A.build_views(DEV, [], [])
    A.gate_data(src)
    cc = M.gate_c() if S == "B" else None
    rate = smoke(S, cc, earlier, workers)
    t = time.time()
    R1.r10(DEV, [], [], workers=workers, with_k=True)
    R1.phase("r10", t)
    chain_and_split(DEV)
    files = {c: M.chb_files(c, earlier) for c in DEV}
    hours = []
    for c in DEV:
        hh = cases_df.set_index("case").earlier_hours_used_windows[c]
        hours += [hh / max(len(files[c]), 1)] * len(files[c])
    projection(rate, hours, workers)
    t = time.time()
    specs = [s for c in DEV for s in rec_specs(c, files[c], S, cc, dict(min_valid=M.MIN_GUARD, min_n=0), M.COVS)]
    specs.sort(key=lambda a: -Path(a[2]).stat().st_size)
    jobs = run_pool(M.rec_job, specs, workers, "rec")
    gate_worker(jobs, "build")
    R1.phase("build", t)
    by = group(jobs)
    struct_gate(by, "earlier", "dev")
    ks = calibrate_k(by, M.COVS, DEV)
    R1._jdump(R1.out_dir() / "k.json", dict(S=S, k=ks, rule="p3_levers.calibrate, seed 42, development patients, "
                                            "per-recording series concatenated per patient", k_record=M.K_RECORD))
    t = time.time()
    res = score_all(by, {c: "development" for c in DEV}, S, ks, tuple(M.FLOORS), M.COVS, workers, "dev")
    R1.phase("score", t)
    write_outputs(jobs, res)
    R1.finish_meta(dict(k=ks, S=S))
    (R1.out_dir() / "SUMMARY.md").write_text(
        f"# {notebook} (commit {repo_commit})\n\nEvery gate PASS (gates.json). Per-recording protocol, scale {S}, "
        f"covariances {M.COVS}, budgets {list(M.FLOORS)}; k {ks}. No reading here: src/m2l_read.py.\n")
    log(f"{notebook} done")


def main_l3short(notebook, repo_commit, workers=None):
    segs = os.environ.get("M2L_SEGS", "5,10")
    if M.TEST_MODE and os.environ.get("M2L_TEST_SEGS"):          # synthetic world only (4-6 min files)
        segs = os.environ["M2L_TEST_SEGS"]
    segs = [int(v) for v in segs.split(",")]
    tag = os.environ.get("M2L_TAG", "l3short")
    workers = setup(tag, notebook, repo_commit, workers)
    sel = read_selection()
    R1.gate(dict(gate="G-sel", status="PASS", selection=sel, sha16=M.sha16(SEL),
                 summary=f"chosen arm {sel['arm']} (k {sel['k']}) from {SEL.relative_to(M.REPO)}"))
    inv, cases_df, complete, earlier = inventory({"chbmit": DEV}, DEV, CHB_CHECKS)
    src = A.build_views(DEV, [], [])
    A.gate_data(src)
    S, cov, fl = sel["S"], sel["cov"], sel["floor"]
    cc = M.gate_c() if S == "B" else None
    t = time.time()
    R1.r10(DEV, [], [], workers=workers, with_k=False)
    R1.phase("r10", t)
    files = {c: M.chb_files(c, earlier) for c in DEV}
    specs, hours = [], []
    for c in DEV:
        sp_, h_ = multi_specs(c, files[c], S, cc, dict(min_valid=17, min_n=0), (cov,), segs)
        specs += sp_
        hours += h_
    order = sorted(range(len(specs)), key=lambda i: -hours[i])
    specs, hours = [specs[i] for i in order], [hours[i] for i in order]
    l3_smoke_proj(M.rec_job_multi, specs[pick_smoke(specs, hours)], hours, workers, "seg")
    t = time.time()
    raw_jobs, jobs = run_pool_multi(specs, workers, "rec[seg]")
    gate_worker(raw_jobs, "build")
    R1.phase("build", t)
    by = group(jobs)
    struct_gate(by, "earlier", "seg")
    ks = {cov: float(sel["k"])}
    res = score_all(by, {c: "development" for c in by}, S, ks, (fl, "FX"), (cov,), workers, "seg")
    for x in res:
        L = int(x["case"].split("@")[1])
        for r in x["rows"] + x["errs"] + x["frows"]:
            r["subject"] = r["subject"].split("@")[0]
            r["seg_min"] = L
    write_outputs(jobs, res)
    R1.finish_meta(dict(segments_min=segs, selection=sel))
    (R1.out_dir() / "SUMMARY.md").write_text(
        f"# {notebook} (commit {repo_commit})\n\nEvery gate PASS. Development segments of {segs} min, arm "
        f"{sel['arm']}, k {sel['k']}. No reading here: src/m2l_read.py --l3short.\n")
    log(f"{notebook} done")


def main_l3eval(notebook, repo_commit, workers=None):
    workers = setup("l3eval", notebook, repo_commit, workers)
    sel = read_selection()
    if not MINLEN.exists():
        R1.gate(dict(gate="G-sel", status="FAIL", summary=f"{MINLEN.relative_to(M.REPO)} missing (read L3-short first)"))
    ml = json.loads(MINLEN.read_text())
    R1.gate(dict(gate="G-sel", status="PASS", selection=sel, minlen=ml, sha16=[M.sha16(SEL), M.sha16(MINLEN)],
                 summary=f"arm {sel['arm']} (k {sel['k']}), minimum length {ml['minutes']} min"))
    inv, cases_df, complete, earlier = inventory({"chbmit": TEST + ["chb24"], "siena": None}, TEST + EXT,
                                                 CHB_CHECKS)
    src = A.build_views([], TEST, EXT)
    A.gate_data(src)
    S, cov, fl = sel["S"], sel["cov"], sel["floor"]
    cc = M.gate_c() if S == "B" else None
    t = time.time()
    R1.r10([], TEST, EXT, workers=workers, with_k=False)
    R1.phase("r10", t)
    guard = dict(min_valid=17, min_n=int(ml["minutes"] * 60 // M.WIN))
    files = {c: M.chb_files(c, earlier) for c in TEST}
    files.update({c: M.ext_files(c, complete) for c in EXT})
    specs = [s for c in TEST + EXT for s in rec_specs(c, files[c], S, cc, guard, (cov,))]
    specs.sort(key=lambda a: -Path(a[2]).stat().st_size)
    hours = [edf_windows(a[2])[1] for a in specs]
    sm = dict(zip(range(12), specs[pick_smoke(specs, hours)]))
    sm[9] = M.SCR / "smoke" / "rec.npz"
    l3_smoke_proj(M.rec_job, tuple(sm[i] for i in range(12)), hours, workers, "eval")
    t = time.time()
    jobs = run_pool(M.rec_job, specs, workers, "rec")
    gate_worker(jobs, "build")
    R1.phase("build", t)
    by = group(jobs)
    struct_gate({c: by[c] for c in TEST}, "earlier", "test")
    struct_gate({c: by[c] for c in EXT}, "ext", "ext")
    set_of = {c: "test" for c in TEST} | {"chb24": "chb24"} | {c: "siena" for c in EXT if c != "chb24"}
    res = score_all(by, set_of, S, {cov: float(sel["k"])}, (fl, "FX"), (cov,), workers, "eval")
    write_outputs(jobs, res)
    R1.finish_meta(dict(selection=sel, minlen=ml))
    (R1.out_dir() / "SUMMARY.md").write_text(
        f"# {notebook} (commit {repo_commit})\n\nEvery gate PASS. SzScan 1.0 protocol (arm {sel['arm']}, k {sel['k']}, "
        f"minimum length {ml['minutes']} min) on test, chb24 and Siena; V5 control in r10/. Reading: src/m2l_read.py --l3.\n")
    log(f"{notebook} done")


def main(notebook, repo_commit="local", workers=None):
    mode = os.environ.get("M2L_MODE", "L2")
    {"L2": main_l2, "L3SHORT": main_l3short, "L3EVAL": main_l3eval}[mode](notebook, repo_commit, workers)


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int)
    ap.add_argument("--notebook", default="local")
    a = ap.parse_args()
    main(a.notebook, workers=a.workers)
