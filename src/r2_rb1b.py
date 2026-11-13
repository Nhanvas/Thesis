#!/usr/bin/env python
"""r2_rb1b.py -- stage RB, step RB1b (laptop, Claude Code): why did chb12's z-score statistics change in RB1?

RB1 (results/r2/r0_data/chb12_ref/rb1/) found that adding chb12_27-29 raised chb12's per-channel SD by +0.6 ... +24.6 %
(median +10.1 %), so its 5-SD thresholds rose and 706 windows of the 21 earlier files lost their artifact flag. The chat
had only a hypothesis for the cause (a few sampled windows of chb12_27's first 916 s, 4x the amplitude). This script
measures it (plan §12 row 13/11 08:35; author approval 13/11 08:30). Descriptive; no rule is chosen here.

The record's statistic (`preprocessing.compute_subject_stats`): every 10th non-ictal, non-buffer window, in sorted file
order, filtered by `filter_window`; per channel mean and unbiased SD over all samples of those windows. This script
re-runs that loop with the wrapper `r2_rb` installed and keeps, for every sampled window and channel, the sum and the
sum of squares, so the statistic can be recomputed for any subset of the sampled windows.

Gates (STOP; nothing is interpreted when a gate fails):
  G-in     every summary-listed chb12 EDF + the committed summary present with sha256 = R0's inventory (= PhysioNet).
  G-stats  the statistic recomputed from the stored sums = RB1's `stats/chb12_stats_jobA_21files.json` (21 files) and
           `stats/chb12_stats.json` (24 files), mean and SD, relative <= 1e-6 (float32 storage; R0's G-stats level).
  G-flags  the c1b flag rule (continuous_eval.filter_file, any channel's peak |x| > 5 SD, non-ictal non-buffer) with the
           21-file and the 24-file thresholds = RB1's counts (`diff_chb12.json`: common files earlier / rebuilt, added
           files), exactly.
  G-clip   samples at the EDF digital limits, read by this script's own numpy EDF reader (channels as RB0b: the 19
           electrodes of a referential file, the first occurrence of each of the 18 derivations in a bipolar file) =
           RB0b's committed `C_clipping_channels.csv` and `C_clipping_files.csv` for all 24 files, exactly.
Descriptive outputs (results/r2/r0_data/chb12_ref/rb1b/):
  sampled_windows.csv.gz  one row per sampled window and set (A = 21 files, B = 24 files): file, window, segment,
                          clipped samples, and per channel the share of the set's total sum of squared deviations
  scenarios.csv           per channel SD (uV) of: A; B; B's windows of the 21 earlier files only (the sampling phase
                          shifted by the added files); B's windows of the 3 added files only; B without windows holding a
                          clipped sample; B without chb12_27 before its first seizure; B without both; robust scales of A
                          and B (IQR / 1.349, MAD x 1.4826 over the same samples)
  contributions.csv       per channel: share of B's total squared deviation from the added files, from chb12_27 before its
                          first seizure, from windows with clipped samples
  unflagged_windows.csv   the windows flagged with A's thresholds but not with B's (and the reverse): file, window,
                          max over channels of peak / threshold for A and B
  SUMMARY.md, rb1b.json   gates, versions, runtime
Run (laptop): python src/r2_rb1b.py   [--chbmit-dir DIR] [--summary-dir DIR] [--out DIR]
Test mode (synthetic data, build container only): R2_TEST_RB_REFERENTIAL (src/r2_rb1b_synthetic_test.py).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

SRC = Path(__file__).resolve().parent
REPO = SRC.parent
for _p in (SRC, SRC / "dataprep"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import r2_rb as RB  # noqa: E402

SUBJ = "chb12"
WIN = 1024
TOL_STATS = 1e-6
RB1 = REPO / "results/r2/r0_data/chb12_ref/rb1"
RB0B = REPO / "results/r2/r0_data/chb12_ref/rb0b"
INV = REPO / "results/r2/r0_data/chb/inventory.csv"


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


def stop(msg, out, gates):
    jdump(dict(gates=gates, stopped=msg), Path(out) / "rb1b.json")
    raise SystemExit(f"STOP RB1b: {msg}")


# ------------------------------------------------------------------------------------------- EDF digital reader
def edf_digital(path):
    """(labels, digital_min, digital_max, [int16 arrays]) from the EDF bytes (same reader as src/r2_rb1.py)."""
    path = Path(path)
    with open(path, "rb") as f:
        h = f.read(256)
        hdr = int(h[184:192].decode("ascii").strip())
        n_rec = int(h[236:244].decode("ascii").strip())
        ns = int(h[252:256].decode("ascii").strip())
        sh = f.read(ns * 256)
    if hdr != 256 * (ns + 1):
        raise SystemExit(f"STOP RB1b: {path.name}: unexpected EDF header size")
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
    if len(raw) != n_rec * rec:
        raise SystemExit(f"STOP RB1b: {path.name}: data size mismatch")
    raw = raw.reshape(n_rec, rec)
    sig, o = [], 0
    for s in spr:
        sig.append(raw[:, o:o + s].reshape(-1))
        o += s
    return fld["label"], [int(x) for x in fld["dmin"]], [int(x) for x in fld["dmax"]], sig


def clip_windows(path, referential, common):
    """per-window clipped-sample counts (any used channel) + per-channel rows as RB0b."""
    labels, dmin, dmax, sig = edf_digital(path)
    if referential:
        idx = RB.match_electrodes(labels)
        use = {e: idx[e] for e in RB.electrodes()}
    else:
        up = [l.upper() for l in labels]
        use = {c: up.index(c) for c in common}
    clip, rows = {}, []
    for name, i in use.items():
        x = sig[i]
        c = (x <= dmin[i]) | (x >= dmax[i])
        clip[name] = c
        rows.append(dict(file=path.name, channel=name, digital_min=dmin[i], digital_max=dmax[i], n_samples=int(x.size),
                         clipped_samples=int(c.sum())))
    n_s = min(v.size for v in clip.values())
    n = n_s // WIN
    anyc = np.zeros(n_s, bool)
    for v in clip.values():
        anyc |= v[:n_s]
    per_win = anyc[: n * WIN].reshape(n, WIN).sum(axis=1)
    return per_win, rows


# ------------------------------------------------------------------------------------------- statistics
def sampled_loop(P, files, paths, smap):
    """the loop of preprocessing.compute_subject_stats over `files` (sorted names); returns the sampled windows."""
    rows, S, SS, X = [], [], [], []
    counter = 0
    for fn in sorted(files):
        raw = P.open_edf(paths[fn])
        if raw is None:
            raise SystemExit(f"STOP RB1b: open_edf returned None for {fn} with the wrapper installed")
        n_samples = int(raw.n_times)
        n_seconds = n_samples // P.FS
        n_windows = n_samples // P.WIN_SAMPLES
        sz = smap.get(fn, [])
        labels = P.build_labels(n_seconds, sz)
        buf = P.build_buffer_mask(n_seconds, sz)
        for i in range(n_windows):
            s0, s1 = i * P.WIN_S, i * P.WIN_S + P.WIN_S
            if int(labels[s0:s1].max()) == 1 or bool(buf[s0:s1].any()):
                continue
            counter += 1
            if counter % P.STATS_SUBSAMPLE != 0:
                continue
            w = np.asarray(P.filter_window(raw, i * P.WIN_SAMPLES, i * P.WIN_SAMPLES + P.WIN_SAMPLES), np.float64)
            rows.append(dict(file=fn, window=i, start_s=i * P.WIN_S))
            S.append(w.sum(axis=1))
            SS.append((w * w).sum(axis=1))
            X.append(w.astype(np.float32))
        del raw
    return pd.DataFrame(rows), np.array(S), np.array(SS), np.stack(X) if X else np.zeros((0, 18, WIN), np.float32)


def mean_sd(S, SS, n_per=WIN):
    N = S.shape[0] * n_per
    tot, tot2 = S.sum(axis=0), SS.sum(axis=0)
    mu = tot / N
    var = (tot2 - tot * tot / N) / max(N - 1, 1)
    return mu, np.sqrt(np.maximum(var, 0.0))


def robust_scales(X):
    """per channel IQR / 1.349 and MAD x 1.4826 over every sample of the sampled windows (scale of a normal)."""
    flat = np.transpose(X, (1, 0, 2)).reshape(X.shape[1], -1).astype(np.float64)
    q1, q3 = np.percentile(flat, [25, 75], axis=1)
    med = np.median(flat, axis=1)
    mad = np.median(np.abs(flat - med[:, None]), axis=1)
    return (q3 - q1) / 1.349, mad * 1.4826


# ------------------------------------------------------------------------------------------- main
def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--chbmit-dir", default=None, help="CHB-MIT root (default: continuous_eval.DATASET_DIR)")
    ap.add_argument("--summary-dir", default=None, help="default: data/summaries")
    ap.add_argument("--out", default=str(REPO / "results/r2/r0_data/chb12_ref/rb1b"))
    a = ap.parse_args(argv)
    t0 = time.time()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    if os.environ.get("R2_TEST") and os.environ.get("R2_TEST_RB_REFERENTIAL"):
        RB.REFERENTIAL.clear()
        RB.REFERENTIAL.update(json.loads(os.environ["R2_TEST_RB_REFERENTIAL"]))
    import continuous_eval as CE
    import evaluation_protocol as E
    if a.chbmit_dir:
        CE.DATASET_DIR = Path(a.chbmit_dir)
    if a.summary_dir:
        CE.SUMMARY_DIR = Path(a.summary_dir)
    P = RB._P()
    RB.install()
    common = list(P.COMMON_CHANNELS)
    gates = {}
    import mne
    import scipy
    versions = dict(python=platform.python_version(), numpy=np.__version__, scipy=scipy.__version__,
                    pandas=pd.__version__, mne=mne.__version__)
    log("versions", versions)

    # ---------------------------------------------------------------- G-in
    summ = CE.SUMMARY_DIR / f"{SUBJ}-summary.txt"
    listed = [e["fname"] for e in E.parse_summary_edf_list(summ)]
    inv = pd.read_csv(INV)
    inv = inv[inv.case == SUBJ].set_index("file")
    bad = []
    paths = {fn: CE.edf_path(SUBJ, fn) for fn in listed}
    for fn, p in paths.items():
        if not p.exists():
            bad.append(f"{fn} absent")
        elif fn not in inv.index or sha256(p) != inv.loc[fn, "sha256_physionet"]:
            bad.append(f"{fn} sha256")
    if f"{SUBJ}-summary.txt" not in inv.index or sha256(summ) != inv.loc[f"{SUBJ}-summary.txt", "sha256_physionet"]:
        bad.append("summary sha256")
    if not set(RB.REFERENTIAL) <= set(listed):
        bad.append("referential files not listed")
    gates["G-in"] = dict(status="PASS" if not bad else "FAIL", files=len(listed), bad=bad)
    log("G-in:", gates["G-in"]["status"], bad)
    if bad:
        stop("G-in " + "; ".join(bad), out, gates)
    new = sorted(RB.REFERENTIAL)
    old = sorted(set(listed) - set(new))
    smap = {fn: [tuple(map(int, s)) for s in v] for fn, v in P.parse_summary(summ).items()}

    # ---------------------------------------------------------------- sampled windows A (21 files) and B (24 files)
    t = time.time()
    WA, SA, SSA, XA = sampled_loop(P, old, paths, smap)
    WB, SB, SSB, XB = sampled_loop(P, listed, paths, smap)
    log(f"sampled windows: A {len(WA)}, B {len(WB)} ({time.time() - t:.0f} s)")
    stA = json.loads((RB1 / "stats" / "chb12_stats_jobA_21files.json").read_text())
    stB = json.loads((RB1 / "stats" / "chb12_stats.json").read_text())
    det = {}
    for tag, (S, SS, st) in dict(A=(SA, SSA, stA), B=(SB, SSB, stB)).items():
        mu, sd = mean_sd(S, SS)
        mu32, sd32 = (mu.astype(np.float32) * 1e6).astype(np.float64), (sd.astype(np.float32) * 1e6).astype(np.float64)
        rm = np.abs(mu32 - np.asarray(st["ch_mean_uV"])) / np.asarray(st["ch_std_uV"])     # mean relative to the SD
        rs = np.abs(sd32 - np.asarray(st["ch_std_uV"])) / np.asarray(st["ch_std_uV"])
        det[tag] = dict(mean_max_rel_to_sd=float(rm.max()), sd_max_rel=float(rs.max()))
    ok = all(v["mean_max_rel_to_sd"] <= TOL_STATS and v["sd_max_rel"] <= TOL_STATS for v in det.values())
    gates["G-stats"] = dict(status="PASS" if ok else "FAIL", tolerance=TOL_STATS, **det)
    log("G-stats:", gates["G-stats"])
    if not ok:
        stop("G-stats: the replicated statistic differs from RB1's", out, gates)

    # ---------------------------------------------------------------- clipping per window (all files), G-clip
    t = time.time()
    clipwin, crow = {}, []
    for fn in listed:
        pw, rows = clip_windows(paths[fn], fn in RB.REFERENTIAL, common)
        clipwin[fn] = pw
        crow += rows
    rc = pd.read_csv(RB0B / "C_clipping_channels.csv", dtype={"channel": str})
    rf = pd.read_csv(RB0B / "C_clipping_files.csv")
    mine = pd.DataFrame(crow).set_index(["file", "channel"])
    bad = []
    for r in rc.itertuples():
        k = (r.file, r.channel)
        if k not in mine.index or any(int(mine.loc[k, c]) != int(getattr(r, c)) for c in
                                      ("digital_min", "digital_max", "n_samples", "clipped_samples")):
            bad.append(f"{r.file} {r.channel}")
    if len(mine) != len(rc):
        bad.append(f"channel rows {len(mine)} vs RB0b {len(rc)}")
    for r in rf.itertuples():
        pw = clipwin.get(r.file)
        if pw is None or len(pw) != int(r.windows) or int((pw > 0).sum()) != int(r.windows_any_clipped):
            bad.append(f"file {r.file}")
    if len(rf) != len(listed):
        bad.append("file rows")
    gates["G-clip"] = dict(status="PASS" if not bad else "FAIL", bad=bad[:30])
    log("G-clip:", gates["G-clip"]["status"], f"({time.time() - t:.0f} s)")
    if bad:
        stop("G-clip: differs from RB0b", out, gates)

    # ---------------------------------------------------------------- the c1b flags with A's and B's thresholds, G-flags
    t = time.time()
    thrA = np.asarray(stA["artifact_thresh_uV"], np.float64) * 1e-6
    thrB = np.asarray(stB["artifact_thresh_uV"], np.float64) * 1e-6
    frows = []
    for fn in listed:
        filt, n = CE.filter_file(paths[fn])
        peak = np.abs(filt.astype(np.float64)).max(axis=2)                  # [n, 18]
        secs = n * P.WIN_S
        sz = smap.get(fn, [])
        lab = P.build_labels(secs, sz).reshape(n, P.WIN_S).max(axis=1) == 1
        buf = P.build_buffer_mask(secs, sz).reshape(n, P.WIN_S).any(axis=1)
        base = ~lab & ~buf
        rA, rB = (peak / thrA[None, :]).max(axis=1), (peak / thrB[None, :]).max(axis=1)
        fA, fB = (rA > 1) & base, (rB > 1) & base
        cw = clipwin[fn]
        for i in np.flatnonzero(fA | fB):
            frows.append(dict(file=fn, window=int(i), start_s=int(i * P.WIN_S), added_file=fn in new,
                              flag_A=bool(fA[i]), flag_B=bool(fB[i]), max_peak_over_thr_A=float(rA[i]),
                              max_peak_over_thr_B=float(rB[i]), clipped_samples=int(cw[i]) if i < len(cw) else 0))
        del filt
    F = pd.DataFrame(frows, columns=["file", "window", "start_s", "added_file", "flag_A", "flag_B", "max_peak_over_thr_A",
                                     "max_peak_over_thr_B", "clipped_samples"])
    D = json.loads((RB1 / "diff_chb12.json").read_text())[SUBJ]
    got = dict(common_A=int((F.flag_A & ~F.added_file).sum()), common_B=int((F.flag_B & ~F.added_file).sum()),
               added_B=int((F.flag_B & F.added_file).sum()))
    want = dict(common_A=D["flag5sd_in_common_files"][0], common_B=D["flag5sd_in_common_files"][1],
                added_B=D["flag5sd_in_added_files"])
    ok = got == want
    gates["G-flags"] = dict(status="PASS" if ok else "FAIL", got=got, rb1=want)
    log("G-flags:", gates["G-flags"], f"({time.time() - t:.0f} s)")
    if not ok:
        stop("G-flags: the c1b flag counts differ from RB1's", out, gates)
    F["change"] = np.select([F.flag_A & ~F.flag_B, ~F.flag_A & F.flag_B], ["unflagged with B", "flagged only with B"],
                            "flagged with both")
    F.to_csv(out / "unflagged_windows.csv", index=False)

    # ---------------------------------------------------------------- decomposition (descriptive)
    first27 = min((s[0] for s in smap.get("chb12_27.edf", [])), default=None)

    def tags(W):
        cw = np.array([int(clipwin[f][w]) if w < len(clipwin[f]) else 0 for f, w in zip(W.file, W.window)])
        pre27 = np.array([(f == "chb12_27.edf") and (first27 is not None) and (s + P.WIN_S <= first27)
                          for f, s in zip(W.file, W.start_s)], bool)
        return cw, pre27
    cA, preA = tags(WA)
    cB, preB = tags(WB)
    addB = WB.file.isin(new).to_numpy()
    sdA = mean_sd(SA, SSA)[1] * 1e6
    sc = {"A: 21 earlier files (R0)": (SA, SSA), "B: 24 files (RB1)": (SB, SSB),
          "B: windows of the 21 earlier files only (phase shifted)": (SB[~addB], SSB[~addB]),
          "B: windows of the 3 added files only": (SB[addB], SSB[addB]),
          "B without windows holding a clipped sample": (SB[cB == 0], SSB[cB == 0]),
          "B without chb12_27 before its first seizure": (SB[~preB], SSB[~preB]),
          "B without both": (SB[(cB == 0) & ~preB], SSB[(cB == 0) & ~preB])}
    ch = common
    srows = []
    for name, (S, SS) in sc.items():
        sd = mean_sd(S, SS)[1] * 1e6 if len(S) else np.full(18, np.nan)
        srows.append(dict(scenario=name, kind="SD (record statistic)", sampled_windows=int(len(S)),
                          **{c: float(sd[i]) for i, c in enumerate(ch)},
                          median_change_vs_A=float(np.median(sd / sdA - 1)), max_change_vs_A=float(np.max(sd / sdA - 1))))
    for name, X in (("A: 21 earlier files (R0)", XA), ("B: 24 files (RB1)", XB)):
        iqr, mad = robust_scales(X)
        for kind, v in (("IQR / 1.349", iqr), ("MAD x 1.4826", mad)):
            srows.append(dict(scenario=name, kind=kind, sampled_windows=int(len(X)),
                              **{c: float(v[i] * 1e6) for i, c in enumerate(ch)}))
    Sc = pd.DataFrame(srows)
    for kind in ("IQR / 1.349", "MAD x 1.4826"):
        m = Sc.kind == kind
        a_, b_ = Sc[m].iloc[0][ch].to_numpy(float), Sc[m].iloc[1][ch].to_numpy(float)
        Sc.loc[Sc[m].index[1], ["median_change_vs_A", "max_change_vs_A"]] = [float(np.median(b_ / a_ - 1)),
                                                                              float(np.max(b_ / a_ - 1))]
    Sc.to_csv(out / "scenarios.csv", index=False)
    # per-window shares of B's (and A's) total squared deviation
    wrows = []
    for tag, W, S, SS, cw, pre in (("A", WA, SA, SSA, cA, preA), ("B", WB, SB, SSB, cB, preB)):
        mu = mean_sd(S, SS)[0]
        dev = SS - 2 * mu[None, :] * S + WIN * mu[None, :] ** 2            # sum over the window of (x - mu)^2
        share = dev / dev.sum(axis=0, keepdims=True)
        for k in range(len(W)):
            wrows.append(dict(set=tag, file=W.file.iloc[k], window=int(W.window.iloc[k]), start_s=int(W.start_s.iloc[k]),
                              added_file=W.file.iloc[k] in new, chb12_27_before_first_seizure=bool(pre[k]),
                              clipped_samples=int(cw[k]), share_mean_over_channels=float(share[k].mean()),
                              **{f"share_{c}": float(share[k, i]) for i, c in enumerate(ch)}))
        if tag == "B":
            contrib = {c: dict(added_files=float(share[addB, i].sum()), chb12_27_before_first_seizure=float(share[pre, i].sum()),
                               windows_with_clipped_samples=float(share[cw > 0, i].sum()),
                               share_of_windows_added=float(addB.mean()), share_of_windows_pre27=float(pre.mean()),
                               share_of_windows_clipped=float((cw > 0).mean())) for i, c in enumerate(ch)}
    pd.DataFrame(wrows).to_csv(out / "sampled_windows.csv.gz", index=False)
    C = pd.DataFrame(contrib).T.rename_axis("channel").reset_index()
    C.insert(1, "sd_change_B_vs_A", [float(v) for v in (mean_sd(SB, SSB)[1] * 1e6 / sdA - 1)])
    C.to_csv(out / "contributions.csv", index=False)

    # ---------------------------------------------------------------- summary
    unf = F[F.change == "unflagged with B"]
    res = dict(gates=gates, versions=versions, runtime_s=round(time.time() - t0, 1),
               sampled_windows=dict(A=int(len(WA)), B=int(len(WB)), B_added_files=int(addB.sum()),
                                    B_chb12_27_before_first_seizure=int(preB.sum()), B_with_clipped=int((cB > 0).sum())),
               unflagged_with_B=dict(windows=int(len(unf)), by_file=unf.groupby("file").size().to_dict(),
                                     max_peak_over_thr_A_median=float(unf.max_peak_over_thr_A.median()) if len(unf) else None),
               flagged_only_with_B=int((F.change == "flagged only with B").sum()))
    jdump(res, out / "rb1b.json")
    L = ["# RB1b -- why chb12's statistics changed (descriptive)\n", f"versions {versions}; runtime {res['runtime_s']} s\n",
         "| gate | status |", "|---|---|"] + [f"| {k} | {v['status']} |" for k, v in gates.items()]
    L += ["", f"sampled windows: {res['sampled_windows']}", "",
          "| scenario | kind | windows | median change vs A | max change vs A |", "|---|---|---|---|---|"]
    L += [f"| {r.scenario} | {r.kind} | {r.sampled_windows} | {r.median_change_vs_A:+.2%} | {r.max_change_vs_A:+.2%} |"
          for r in Sc.itertuples() if pd.notna(r.median_change_vs_A)]
    L += ["", "share of B's total squared deviation (median over the 18 channels): "
          f"added files {C.added_files.median():.1%} (of the windows {addB.mean():.1%}), "
          f"chb12_27 before its first seizure {C.chb12_27_before_first_seizure.median():.1%} (windows {preB.mean():.1%}), "
          f"windows with clipped samples {C.windows_with_clipped_samples.median():.1%} (windows {(cB > 0).mean():.1%})",
          "", f"windows unflagged with B: {res['unflagged_with_B']}; flagged only with B: {res['flagged_only_with_B']}"]
    (out / "SUMMARY.md").write_text("\n".join(L) + "\n")
    log("END", json.dumps({k: v["status"] for k, v in gates.items()}), f"runtime {res['runtime_s']} s")
    return res


if __name__ == "__main__":
    main()
