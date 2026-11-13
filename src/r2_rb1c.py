#!/usr/bin/env python
"""r2_rb1c.py -- stage RB, step RB1c (laptop, Claude Code): how robust is the record's z-score statistic, in every case?

RB1b (results/r2/r0_data/chb12_ref/rb1b/) measured that chb12's SD rose by up to +25 % because 23 sampled windows of
chb12_27 (0-700 s, 14 of them with samples at the EDF digital limits) hold ~19 % of the total squared deviation; without
them, or without the windows holding a clipped sample, the SD returns to the earlier value, and the robust scales (IQR,
MAD) move by +0.2 %. Before the author chooses how the statistic is computed (plan §12 13/11 09:30; approval 13/11 09:10),
this script measures, descriptively, in every CHB-MIT case (24) and every Siena patient (14):
  - the record statistic (CHB-MIT: `preprocessing.compute_subject_stats`, every 10th non-ictal non-buffer window, in
    sorted file order, the wrapper `r2_rb` installed so chb12 has 24 files; Siena: `x1_external.labelfree_stats`, every
    10th window of the whole recording) re-run with the sums of every sampled window kept;
  - the same statistic without the sampled windows that hold a sample at the EDF digital limits ("no-clip");
  - the robust scales MAD x 1.4826 and IQR / 1.349 over the same samples (scale of a normal distribution);
  - how concentrated the statistic is (share of the total squared deviation in the top 1 % of the sampled windows, per
    file, the 10 largest windows of every case);
  - CHB-MIT only (the flag exists only there): the c1b 5-SD flag (`continuous_eval.filter_file`, any channel's peak |x|
    above the threshold, non-ictal non-buffer windows) for every window, with the record threshold and with each
    alternative scale at multipliers 3 ... 20, the multiplier that would keep the record's flag count, and the clean
    (training) windows (non-ictal, non-buffer, not signal-loss, not flagged).
Gates (STOP; nothing is interpreted when a gate fails):
  G-in     CHB-MIT: the EDFs present in every case folder = the files of R0's inventory for that case, sha256 = PhysioNet,
           + the committed summary; Siena: every EDF of x1_external.subject_files with sha256 = the ext inventory.
  G-stats  CHB-MIT: the record statistic recomputed from the sums = the committed statistics (R0: stats_earlier for 21
           cases, which are sha-equal to the R0 dataset pin; chb11 / chb21 = stats_earlier x R0's committed relative
           change; chb12 = RB1's 24-file statistics), mean (relative to the SD) and SD relative <= 1e-6.
           Siena: = x1_external.labelfree_stats run on the same files (the record code), same tolerance; and the window
           count = R0's committed external_cases.csv.
  G-flags  CHB-MIT: flagged and clean window counts with the record thresholds = R0's committed counts
           (results/r2/r1_system/run/data_gate.json; chb12 = RB1's diff_chb12.json). chb24 has no committed flag count
           (its thesis-convention build used another builder): computed, not gated (stated in the summary).
Outputs (results/r2/r0_data/rb1c/): cases.csv, channels.csv, flag_grid.csv, files.csv, top_windows.csv, SUMMARY.md,
rb1c.json (gates, versions, runtime). Small; no EEG, no patient data beyond public file names.
Run (laptop): python src/r2_rb1c.py [--chbmit-dir DIR] [--siena-dir DIR] [--summary-dir DIR] [--out DIR] [--procs N]
              [--cases chb01,PN00,...]
Test mode (synthetic data, build container only): src/r2_rb1c_synthetic_test.py.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import sys
import time
import multiprocessing as mp
import traceback
from pathlib import Path

import numpy as np
import pandas as pd

SRC = Path(__file__).resolve().parent
REPO = SRC.parent
for _p in (SRC, SRC / "dataprep"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

WIN = 1024
TOL = 1e-6
CHB = [f"chb{i:02d}" for i in range(1, 25)]
TRAIN = ["chb01", "chb02", "chb04", "chb05", "chb07", "chb08", "chb09", "chb12", "chb19", "chb20", "chb21", "chb23"]
VAL = ["chb10", "chb11", "chb22"]
TEST = ["chb03", "chb06", "chb13", "chb14", "chb15", "chb16", "chb17", "chb18"]
MULTS = [3, 4, 5, 6, 7, 8, 10, 15, 20]
SCALES = ("record", "noclip", "mad", "iqr")
R0 = REPO / "results/r2/r0_data"
INV_CHB, INV_EXT = R0 / "chb/inventory.csv", R0 / "ext/inventory.csv"
STATS_EARLIER = R0 / "chb/stats_earlier"
DIFF_1121 = R0 / "chb/diff_chb11_chb21.json"
RB1 = R0 / "chb12_ref/rb1"
DATA_GATE = REPO / "results/r2/r1_system/run/data_gate.json"
EXT_CASES = R0 / "ext/external_cases.csv"
CFG = {}


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


def jdump(obj, path):
    Path(path).write_text(json.dumps(obj, indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o)))


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""):
            h.update(b)
    return h.hexdigest()


def role(case):
    return ("train" if case in TRAIN else "validation" if case in VAL else "test" if case in TEST
            else "chb24 (extra test)" if case == "chb24" else "Siena (external)")


# ------------------------------------------------------------------------------------------- references
def ref_stats(case):
    """the committed record statistic of a CHB-MIT case (dict with ch_mean_uV, ch_std_uV, artifact_thresh_uV)."""
    if case == "chb12":
        return json.loads((RB1 / "stats" / "chb12_stats.json").read_text())
    st = json.loads((STATS_EARLIER / f"{case}_stats.json").read_text())
    if case in ("chb11", "chb21"):
        rel = json.loads(DIFF_1121.read_text())[case]["stats_rel_change"]
        sd0, mu0 = np.asarray(st["ch_std_uV"], float), np.asarray(st["ch_mean_uV"], float)
        sd = sd0 * (1 + np.asarray(rel["ch_std_uV (relative change)"]["per_channel"], float))
        mu = mu0 + np.asarray(rel["ch_mean_uV (change / earlier SD)"]["per_channel"], float) * sd0
        thr = np.asarray(st["artifact_thresh_uV"], float) * (1 + np.asarray(rel["artifact_thresh_uV (relative change)"]["per_channel"], float))
        st = dict(st, ch_mean_uV=mu.tolist(), ch_std_uV=sd.tolist(), artifact_thresh_uV=thr.tolist())
    return st


def ref_counts(case):
    """committed flagged / clean window counts with the record thresholds (None for chb24)."""
    if case == "chb12":
        d = json.loads((RB1 / "diff_chb12.json").read_text())["chb12"]
        return dict(flag5sd=int(d["flag5sd_in_common_files"][1] + d["flag5sd_in_added_files"]),
                    clean=int(d["clean_windows"][1]))
    det = json.loads(DATA_GATE.read_text())["detail"].get(case, {}).get("counts", {})
    if "flag5sd" not in det:
        return None
    return dict(flag5sd=int(det["flag5sd"]), clean=int(det["clean"]))


# ------------------------------------------------------------------------------------------- EDF digital reader
def edf_digital(path):
    """(labels, digital_min, digital_max, samples per record, n_records, [int16 arrays]) from the EDF bytes."""
    path = Path(path)
    with open(path, "rb") as f:
        h = f.read(256)
        hdr = int(h[184:192].decode("ascii").strip())
        n_rec = int(h[236:244].decode("ascii").strip())
        dur = float(h[244:252].decode("ascii").strip())
        ns = int(h[252:256].decode("ascii").strip())
        sh = f.read(ns * 256)
    if hdr != 256 * (ns + 1):
        raise SystemExit(f"STOP RB1c: {path.name}: unexpected EDF header size")
    widths = [("label", 16), ("transducer", 80), ("dim", 8), ("pmin", 8), ("pmax", 8), ("dmin", 8), ("dmax", 8),
              ("prefilter", 80), ("spr", 8), ("reserved", 32)]
    fld, pos = {}, 0
    for name, w in widths:
        fld[name] = [sh[pos + i * w: pos + (i + 1) * w].decode("ascii", "replace").strip() for i in range(ns)]
        pos += ns * w
    spr = [int(x) for x in fld["spr"]]
    raw = np.fromfile(path, dtype="<i2", offset=hdr)
    rec = sum(spr)
    if n_rec < 0:
        n_rec = len(raw) // rec
    if len(raw) < n_rec * rec:
        raise SystemExit(f"STOP RB1c: {path.name}: data size mismatch")
    raw = raw[: n_rec * rec].reshape(n_rec, rec)
    sig, o = [], 0
    for s in spr:
        sig.append(raw[:, o:o + s].reshape(-1))
        o += s
    return fld["label"], [int(x) for x in fld["dmin"]], [int(x) for x in fld["dmax"]], spr, dur, sig


def clip_per_window(path, kind):
    """clipped samples (any used channel at its digital limit) per 4 s window. CHB-MIT bipolar: the first occurrence
    of each of the 18 derivations; chb12_27-29: the 19 electrodes (r2_rb.match_electrodes); Siena: the 19 electrodes
    of x1_external.load_18 (same name normalisation), windows of 4 s at the native rate."""
    import r2_rb as RB
    labels, dmin, dmax, spr, dur, sig = edf_digital(path)
    if kind == "siena":
        import x1_external as X1
        names = {}
        for i, ch in enumerate(labels):
            n = ch.upper().replace("EEG", "").strip().replace(" ", "")
            names.setdefault(X1.SIENA_MAP.get(n, n), i)
        need = sorted({e for pair in X1.BIPOLAR for e in pair})
        miss = [e for e in need if e not in names]
        if miss:
            raise SystemExit(f"STOP RB1c: {path.name}: electrodes {miss} not found by the digital reader")
        use = [names[e] for e in need]
    elif path.name in RB.REFERENTIAL:
        idx = RB.match_electrodes(labels)
        use = [idx[e] for e in RB.electrodes()]
    else:
        P = RB._P()
        up = [l.upper().strip() for l in labels]
        try:
            use = [up.index(c) for c in P.COMMON_CHANNELS]
        except ValueError as ex:
            raise SystemExit(f"STOP RB1c: {path.name}: {ex}")
    fs = {round(spr[i] / dur) for i in use}
    if len(fs) != 1:
        raise SystemExit(f"STOP RB1c: {path.name}: channels at different rates {fs}")
    w = int(fs.pop()) * 4
    n_s = min(sig[i].size for i in use)
    anyc = np.zeros(n_s, bool)
    for i in use:
        anyc |= (sig[i][:n_s] <= dmin[i]) | (sig[i][:n_s] >= dmax[i])
    n = n_s // w
    return anyc[: n * w].reshape(n, w).sum(axis=1)


# ------------------------------------------------------------------------------------------- per-case measurement
def init_worker(cfg):
    CFG.update(cfg)
    import r2_rb as RB
    if cfg.get("test_referential"):
        RB.REFERENTIAL.clear()
        RB.REFERENTIAL.update(cfg["test_referential"])
    import continuous_eval as CE
    CE.DATASET_DIR = Path(cfg["chbmit_dir"])
    CE.SUMMARY_DIR = Path(cfg["summary_dir"])
    RB.install()


def scales_from(S, SS, X, clipped):
    """per channel (uV): record mean / SD from the sums; no-clip SD; MAD x 1.4826; IQR / 1.349."""
    def msd(S_, SS_):
        N = S_.shape[0] * WIN
        tot, tot2 = S_.sum(axis=0), SS_.sum(axis=0)
        mu = tot / N
        return mu, np.sqrt(np.maximum((tot2 - tot * tot / N) / max(N - 1, 1), 0.0))
    mu, sd = msd(S, SS)
    keep = clipped == 0
    sd_nc = msd(S[keep], SS[keep])[1] if keep.any() else np.full(S.shape[1], np.nan)
    mad, iqr = np.empty(S.shape[1]), np.empty(S.shape[1])
    for c in range(S.shape[1]):
        v = X[:, c, :].astype(np.float64).ravel()
        med = np.median(v)
        mad[c] = np.median(np.abs(v - med)) * 1.4826
        q1, q3 = np.percentile(v, [25, 75])
        iqr[c] = (q3 - q1) / 1.349
    dev = SS - 2 * mu[None, :] * S + WIN * mu[None, :] ** 2              # per window and channel: sum of (x - mu)^2
    share = dev / dev.sum(axis=0, keepdims=True)
    return dict(mean=mu * 1e6, record=sd * 1e6, noclip=sd_nc * 1e6, mad=mad * 1e6, iqr=iqr * 1e6), share


def chb_case(case):
    import r2_rb as RB
    P = RB._P()
    import continuous_eval as CE
    t0 = time.time()
    inv = pd.concat([pd.read_csv(INV_CHB), pd.read_csv(INV_EXT)])
    inv = inv[(inv.db == "chbmit") & (inv.case == case)].drop_duplicates("file").set_index("file")
    cdir = CE.DATASET_DIR / case
    files = sorted(p.name for p in cdir.glob("*.edf"))
    bad = []
    want = sorted(f for f in inv.index if f.endswith(".edf"))
    if files != want:
        bad.append(f"files present {len(files)} vs inventory {len(want)}: "
                   f"{sorted(set(files) ^ set(want))[:6]}")
    for f in files:
        if f in inv.index and sha256(cdir / f) != inv.loc[f, "sha256_physionet"]:
            bad.append(f"{f} sha256")
    summ = CE.SUMMARY_DIR / f"{case}-summary.txt"          # r2_core.summary_path: the committed copy, else the
    if not summ.exists():                                     # case folder's (chb24 has no committed summary)
        summ = cdir / f"{case}-summary.txt"
    if not summ.exists() or sha256(summ) != inv.loc[f"{case}-summary.txt", "sha256_physionet"]:
        bad.append("summary sha256")
    if bad:
        return dict(case=case, stop=f"G-in {case}: " + "; ".join(bad))
    smap = P.parse_summary(summ)
    # ---- the record loop (compute_subject_stats) with the sums kept
    rows, S, SS, X, skipped, counter = [], [], [], [], [], 0
    for fn in files:
        raw = P.open_edf(cdir / fn)
        if raw is None:
            skipped.append(fn)
            continue
        n_seconds = int(raw.n_times) // P.FS
        n_windows = int(raw.n_times) // P.WIN_SAMPLES
        sz = smap.get(fn, [])
        lab, buf = P.build_labels(n_seconds, sz), P.build_buffer_mask(n_seconds, sz)
        for i in range(n_windows):
            s0, s1 = i * P.WIN_S, i * P.WIN_S + P.WIN_S
            if int(lab[s0:s1].max()) == 1 or bool(buf[s0:s1].any()):
                continue
            counter += 1
            if counter % P.STATS_SUBSAMPLE != 0:
                continue
            w = np.asarray(P.filter_window(raw, i * P.WIN_SAMPLES, (i + 1) * P.WIN_SAMPLES), np.float64)
            rows.append((fn, i))
            S.append(w.sum(axis=1)); SS.append((w * w).sum(axis=1)); X.append(w.astype(np.float32))
        del raw
    if skipped:
        return dict(case=case, stop=f"G-in {case}: open_edf returned None for {skipped} (wrapper installed)")
    S, SS, X = np.array(S), np.array(SS), np.stack(X)
    t_stats = time.time() - t0
    # ---- clipping per window
    clip = {fn: clip_per_window(cdir / fn, "chb") for fn in files}
    cl = np.array([int(clip[f][i]) if i < len(clip[f]) else 0 for f, i in rows])
    sc, share = scales_from(S, SS, X, cl)
    del X
    st = ref_stats(case)
    rm = np.abs(sc["mean"] - np.asarray(st["ch_mean_uV"])) / np.asarray(st["ch_std_uV"])
    rs = np.abs(sc["record"] - np.asarray(st["ch_std_uV"])) / np.asarray(st["ch_std_uV"])
    g_stats = dict(status="PASS" if rm.max() <= TOL and rs.max() <= TOL else "FAIL",
                   mean_max_rel_to_sd=float(rm.max()), sd_max_rel=float(rs.max()))
    if g_stats["status"] != "PASS":
        return dict(case=case, stop=f"G-stats {case}: {g_stats}")
    # ---- flags (c1b rule) over every window
    thr_rec = np.asarray(st["artifact_thresh_uV"], np.float64) * 1e-6
    scale = {"record": thr_rec / 5.0, **{k: sc[k] * 1e-6 for k in ("noclip", "mad", "iqr")}}
    R = {k: [] for k in SCALES}
    base_l, ict_l, sl_l, rec_flag = [], [], [], []
    for fn in files:
        filt, n = CE.filter_file(cdir / fn)
        peak = np.abs(filt.astype(np.float64)).max(axis=2)                       # [n, 18]
        del filt
        secs = n * P.WIN_S
        sz = smap.get(fn, [])
        lab = P.build_labels(secs, sz).reshape(n, P.WIN_S).max(axis=1) == 1
        buf = P.build_buffer_mask(secs, sz).reshape(n, P.WIN_S).any(axis=1)
        raw = P.open_edf(cdir / fn)
        sl_l.append(CE.compute_signal_loss_flags(raw, n))
        del raw
        base_l.append(~lab & ~buf); ict_l.append(lab)
        rec_flag.append((peak > thr_rec[None, :]).any(axis=1) & ~lab & ~buf)
        for k in SCALES:
            R[k].append((peak / scale[k][None, :]).max(axis=1))
    base, ict, sl, recf = (np.concatenate(v) for v in (base_l, ict_l, sl_l, rec_flag))
    R = {k: np.concatenate(v) for k, v in R.items()}
    got = dict(flag5sd=int(recf.sum()), clean=int((base & ~sl & ~recf).sum()))
    ref = ref_counts(case)
    if ref is None:
        g_flags = dict(status="NOT GATED", got=got, note="no committed flag count for this case")
    else:
        g_flags = dict(status="PASS" if got == ref else "FAIL", got=got, ref=ref)
        if got != ref:
            return dict(case=case, stop=f"G-flags {case}: {g_flags}")
    # ---- descriptive tables
    grid, n_rec = [], int(recf.sum())
    for k in SCALES:
        r = R[k][base]
        for m in MULTS:
            f = r > m
            grid.append(dict(case=case, scale=k, multiplier=m, flagged=int(f.sum()), share_of_base=float(f.mean()),
                             clean=int((base & ~sl & (R[k] <= m)).sum()),
                             overlap_with_record=float((f & recf[base]).sum() / max(n_rec, 1))))
    out = finish(case, "chbmit", rows, S, cl, sc, share, len(files), skipped)
    base_n = int(base.sum())
    eq = {}
    for k in ("noclip", "mad", "iqr"):
        r = np.sort(R[k][base])[::-1]
        eq[k] = float(r[n_rec - 1]) if 0 < n_rec <= len(r) else float("nan")       # flag count = record's at > ~this
    out["case_row"].update(
        windows=int(len(base)), base_windows=base_n, ictal_windows=int(ict.sum()), signal_loss_windows=int(sl.sum()),
        flagged_record=n_rec, flagged_record_share=n_rec / max(base_n, 1), clean_record=got["clean"],
        ictal_over_record_threshold=float((R["record"][ict] > 5).mean()) if ict.any() else float("nan"),
        **{f"flagged_{k}_x5": int((R[k][base] > 5).sum()) for k in ("noclip", "mad", "iqr")},
        **{f"clean_{k}_x5": int((base & ~sl & (R[k] <= 5)).sum()) for k in ("noclip", "mad", "iqr")},
        **{f"multiplier_same_count_{k}": eq[k] for k in ("noclip", "mad", "iqr")})
    out.update(grid=grid, gates={"G-stats": g_stats, "G-flags": g_flags, "G-in": dict(status="PASS", files=len(files))},
               runtime_s=round(time.time() - t0, 1), stats_s=round(t_stats, 1))
    return out


def siena_case(case):
    import r2_rb as RB
    P = RB._P()
    import x1_external as X1
    t0 = time.time()
    files, meta = X1.subject_files(CFG["siena_dir"], case)
    inv = pd.read_csv(INV_EXT)
    inv = inv[(inv.db == "siena") & (inv.case == case)].set_index("file")
    bad = []
    if sorted(p.name for p, _ in files) != sorted(f for f in inv.index if f.endswith(".edf")):
        bad.append("file list differs from the ext inventory")
    for p, _ in files:
        if p.name not in inv.index or sha256(p) != inv.loc[p.name, "sha256_physionet"]:
            bad.append(f"{p.name} sha256")
    if bad:
        return dict(case=case, stop=f"G-in {case}: " + "; ".join(bad))
    rows, S, SS, X, cnt, n_win = [], [], [], [], 0, 0
    for p, _ in files:
        data = X1.load_18(p, meta["kind"])
        if data is None:
            return dict(case=case, stop=f"G-in {case}: load_18 returned None for {p.name}")
        nw = data.shape[1] // P.WIN_SAMPLES
        n_win += nw
        for i in range(nw):
            cnt += 1
            if cnt % P.STATS_SUBSAMPLE == 0:
                w = np.asarray(X1.window_padded(data, i, meta["notch"]), np.float64)
                rows.append((p.name, i))
                S.append(w.sum(axis=1)); SS.append((w * w).sum(axis=1)); X.append(w.astype(np.float32))
        del data
    S, SS, X = np.array(S), np.array(SS), np.stack(X)
    clip = {p.name: clip_per_window(p, "siena") for p, _ in files}
    cl = np.array([int(clip[f][i]) if i < len(clip[f]) else 0 for f, i in rows])
    sc, share = scales_from(S, SS, X, cl)
    del X
    mu_r, sd_r = X1.labelfree_stats(files, meta["kind"], meta["notch"])                 # the record code
    rm = np.abs(sc["mean"] - mu_r * 1e6) / (sd_r * 1e6)
    rs = np.abs(sc["record"] - sd_r * 1e6) / (sd_r * 1e6)
    ec = pd.read_csv(EXT_CASES).set_index("case")
    win_ok = case in ec.index and int(ec.loc[case, "windows"]) == n_win
    g_stats = dict(status="PASS" if rm.max() <= TOL and rs.max() <= TOL and win_ok else "FAIL",
                   mean_max_rel_to_sd=float(rm.max()), sd_max_rel=float(rs.max()), windows=n_win,
                   windows_r0=int(ec.loc[case, "windows"]) if case in ec.index else None)
    if g_stats["status"] != "PASS":
        return dict(case=case, stop=f"G-stats {case}: {g_stats}")
    out = finish(case, "siena", rows, S, cl, sc, share, len(files), [])
    out["case_row"].update(windows=n_win)
    out.update(grid=[], gates={"G-in": dict(status="PASS", files=len(files)), "G-stats": g_stats},
               runtime_s=round(time.time() - t0, 1))
    return out


def finish(case, db, rows, S, cl, sc, share, n_files, skipped):
    """case, channel, file and top-window rows shared by both datasets."""
    ch = list(__import__("r2_rb")._P().COMMON_CHANNELS)
    W = pd.DataFrame(rows, columns=["file", "window"])
    W["clipped_samples"] = cl
    W["share"] = share.mean(axis=1)
    n = len(W)
    top = max(1, int(np.ceil(0.01 * n)))
    srt = np.sort(share, axis=0)[::-1]
    chan = [dict(case=case, channel=c, mean_uV=sc["mean"][i], sd_record_uV=sc["record"][i], sd_noclip_uV=sc["noclip"][i],
                 mad_uV=sc["mad"][i], iqr_uV=sc["iqr"][i], noclip_vs_record=sc["noclip"][i] / sc["record"][i] - 1,
                 mad_over_sd=sc["mad"][i] / sc["record"][i], iqr_over_sd=sc["iqr"][i] / sc["record"][i],
                 top1pct_share=float(srt[:top, i].sum()), clipped_windows_share=float(share[cl > 0, i].sum()))
            for i, c in enumerate(ch)]
    C = pd.DataFrame(chan)
    F = (W.groupby("file").agg(sampled_windows=("window", "size"), clipped_windows=("clipped_samples", lambda v: int((v > 0).sum())),
                               share_of_deviation=("share", "sum")).reset_index())
    F["share_of_windows"] = F.sampled_windows / n
    F["ratio"] = F.share_of_deviation / F.share_of_windows
    F.insert(0, "case", case)
    T = W.nlargest(10, "share").assign(case=case, start_s=lambda d: d.window * 4)[
        ["case", "file", "window", "start_s", "clipped_samples", "share"]]
    case_row = dict(
        case=case, dataset=db, role=role(case), files=n_files, sampled_windows=n,
        sampled_with_clipped=int((cl > 0).sum()),
        noclip_vs_record_median=float(C.noclip_vs_record.median()), noclip_vs_record_min=float(C.noclip_vs_record.min()),
        noclip_vs_record_max=float(C.noclip_vs_record.max()),
        mad_over_sd_median=float(C.mad_over_sd.median()), mad_over_sd_min=float(C.mad_over_sd.min()),
        mad_over_sd_max=float(C.mad_over_sd.max()), iqr_over_sd_median=float(C.iqr_over_sd.median()),
        top1pct_share_median=float(C.top1pct_share.median()), top1pct_share_max=float(C.top1pct_share.max()),
        clipped_windows_share_median=float(C.clipped_windows_share.median()),
        top_file=str(F.sort_values("ratio").iloc[-1].file), top_file_ratio=float(F.ratio.max()))
    return dict(case=case, case_row=case_row, channels=chan, files=F.to_dict("records"), top=T.to_dict("records"))


def run_case(case):
    """one case; a finished case is cached (out/_cache, keyed by this script's sha256) so a re-run after a STOP
    resumes; the cache is removed when the run ends with every gate PASS."""
    import pickle
    cache = Path(CFG["out"]) / "_cache" / f"{case}.pkl"
    if cache.exists():
        r = pickle.loads(cache.read_bytes())
        if r.get("code_sha") == CFG["code_sha"]:
            r["reused"] = True
            return r
    try:
        r = chb_case(case) if case.startswith("chb") else siena_case(case)
        if "stop" not in r:
            r["code_sha"] = CFG["code_sha"]
            cache.parent.mkdir(exist_ok=True)
            tmp = cache.with_suffix(".tmp")
            tmp.write_bytes(pickle.dumps(r))
            os.replace(tmp, cache)
        return r
    except SystemExit as ex:
        return dict(case=case, stop=str(ex))
    except Exception:                                                  # noqa: BLE001 -- a traceback is a STOP too
        return dict(case=case, stop=f"{case}: exception\n{traceback.format_exc()}")


# ------------------------------------------------------------------------------------------- main
def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--chbmit-dir", default=None, help="default: continuous_eval.DATASET_DIR (F:/Study/Thesis/Dataset/CHB-MIT)")
    ap.add_argument("--siena-dir", default="F:/Study/Thesis/Dataset/siena")
    ap.add_argument("--summary-dir", default=str(REPO / "data" / "summaries"))
    ap.add_argument("--out", default=str(R0 / "rb1c"))
    ap.add_argument("--procs", type=int, default=2)
    ap.add_argument("--cases", default=None, help="comma list (default: chb01-chb24 + the 14 Siena patients)")
    a = ap.parse_args(argv)
    t0 = time.time()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    import continuous_eval as CE
    cfg = dict(chbmit_dir=str(a.chbmit_dir or CE.DATASET_DIR), summary_dir=a.summary_dir, siena_dir=a.siena_dir,
               out=str(out), code_sha=sha256(Path(__file__)))
    if os.environ.get("R2_TEST") and os.environ.get("R2_TEST_RB_REFERENTIAL"):
        cfg["test_referential"] = json.loads(os.environ["R2_TEST_RB_REFERENTIAL"])
    siena = sorted(pd.read_csv(EXT_CASES).case.loc[lambda s: s.str.startswith("PN")])
    cases = a.cases.split(",") if a.cases else CHB + siena
    import mne
    import scipy
    versions = dict(python=platform.python_version(), numpy=np.__version__, scipy=scipy.__version__,
                    pandas=pd.__version__, mne=mne.__version__)
    log("versions", versions, "cases", len(cases), "procs", a.procs)
    # largest cases first (chb04 ~156 h), so the pool ends together
    hours = pd.read_csv(INV_CHB).groupby("case").hours.sum().to_dict()
    order = sorted(cases, key=lambda c: -hours.get(c, 10.0))
    res = {}
    ctx = mp.get_context("spawn")                     # Windows' start method, also in the Linux test
    with ctx.Pool(a.procs, initializer=init_worker, initargs=(cfg,), maxtasksperchild=1) as pool:
        for r in pool.imap_unordered(run_case, order):
            res[r["case"]] = r
            if "stop" in r:
                log("STOP", r["stop"])
                pool.terminate()
                break
            log(f"{r['case']}: {json.dumps({k: v['status'] for k, v in r['gates'].items()})} ({r['runtime_s']} s"
                + (", reused from the cache)" if r.get("reused") else ")"))
    stops = [r["stop"] for r in res.values() if "stop" in r]
    gates = {c: r.get("gates", {}) for c, r in res.items() if "gates" in r}
    if stops:
        jdump(dict(stopped=stops, gates=gates, versions=versions), out / "rb1c.json")
        raise SystemExit(f"STOP RB1c: {stops[0]}")
    done = [c for c in cases if c in res]
    Cs = pd.DataFrame([res[c]["case_row"] for c in done])
    Cs.to_csv(out / "cases.csv", index=False)
    pd.DataFrame([x for c in done for x in res[c]["channels"]]).to_csv(out / "channels.csv", index=False)
    pd.DataFrame([x for c in done for x in res[c]["grid"]]).to_csv(out / "flag_grid.csv", index=False)
    pd.DataFrame([x for c in done for x in res[c]["files"]]).to_csv(out / "files.csv", index=False)
    pd.DataFrame([x for c in done for x in res[c]["top"]]).to_csv(out / "top_windows.csv", index=False)
    summary = dict(versions=versions, runtime_s=round(time.time() - t0, 1), procs=a.procs, cases=done,
                   code_sha=cfg["code_sha"], reused=[c for c in done if res[c].get("reused")],
                   case_runtime_s={c: res[c]["runtime_s"] for c in done},
                   gates=gates, not_gated=[c for c, g in gates.items() if g.get("G-flags", {}).get("status") == "NOT GATED"])
    jdump(summary, out / "rb1c.json")
    write_summary(out, Cs, summary)
    shutil.rmtree(out / "_cache", ignore_errors=True)
    log("END", f"{len(done)} cases, every gate PASS", f"runtime {summary['runtime_s']} s")
    return summary


def write_summary(out, Cs, summary):
    pct = lambda v: f"{v:+.1%}" if pd.notna(v) else "-"
    L = ["# RB1c -- robustness of the z-score statistic, every case (descriptive)\n",
         f"versions {summary['versions']}; runtime {summary['runtime_s']} s; procs {summary['procs']}; "
         f"cases reused from an earlier run's cache: {summary['reused'] or 'none'}\n",
         f"gates: every case PASS (G-in, G-stats; G-flags on CHB-MIT). Not gated: {summary['not_gated']} "
         "(no committed flag count).\n",
         "| case | role | sampled | with clipped | no-clip SD vs record (median / largest change over ch) | MAD/SD (median) | "
         "top 1 % windows' share of deviation (median ch) | flagged record (share of base) | flagged x5: no-clip / MAD / IQR | "
         "multiplier for the record count: MAD / IQR | clean record -> no-clip / MAD |", "|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in Cs.itertuples():
        chb = r.dataset == "chbmit"
        L.append(f"| {r.case} | {r.role} | {r.sampled_windows} | {r.sampled_with_clipped} | "
                 f"{pct(r.noclip_vs_record_median)} / {pct(r.noclip_vs_record_min) if r.noclip_vs_record_median < 0 else pct(r.noclip_vs_record_max)} | "
                 f"{r.mad_over_sd_median:.2f} | {r.top1pct_share_median:.1%} | "
                 + (f"{int(r.flagged_record)} ({r.flagged_record_share:.1%}) | {int(r.flagged_noclip_x5)} / "
                    f"{int(r.flagged_mad_x5)} / {int(r.flagged_iqr_x5)} | {r.multiplier_same_count_mad:.2f} / "
                    f"{r.multiplier_same_count_iqr:.2f} | {int(r.clean_record)} -> {int(r.clean_noclip_x5)} / "
                    f"{int(r.clean_mad_x5)} |" if chb else "- | - | - | - |"))
    L += ["", "No-clip: the record statistic without the sampled windows that hold a sample at the EDF digital limits. "
          "MAD and IQR are scaled to a normal SD (x 1.4826, / 1.349). Flags: c1b rule on non-ictal non-buffer windows "
          "(base). Multiplier for the record count: the threshold multiple of that scale that would flag as many base "
          "windows as the record rule. Siena has no flag in its pipeline (statistics only)."]
    (out / "SUMMARY.md").write_text("\n".join(L) + "\n")


if __name__ == "__main__":
    main()
