#!/usr/bin/env python
"""
r2_diag.py -- independent track, stage R0: diagnosis of a G-feat failure (chat D14b-F, 07/11; plan §12 07/11 12:49).
R0_CHB v2 stopped at chb17 (G-stats PASS; flags, file_idx and file list exact; f7 one cell non-finite in one file only,
bp5 3.84, adjacency 0.92 %). This module rebuilds ONE case on the earlier view with the record code, unchanged
(r2_core.features_record with the committed stats.json, which G-stats proved equal), and localizes every difference
against the record .npz. Descriptive only: it changes no data, no gate and no tolerance.

  localize      one row per window (file, window in file, the four flags, per-feature max |diff|, non-finite flips,
                adjacency entries differing, zgamma); every non-finite flip cell (window, channel, feature, both
                values); per-file table; G-feat read on all windows / on the chain windows (not is_signal_loss) / on the
                signal-loss windows, with r2_core.compare_features (the v3 gate code).
  raw_evidence  for every file holding a signal-loss window or a window beyond tolerance: per window the raw (unfiltered)
                SD (max and min over the 18 channels, V), the filtered max |x| (V), the recomputed signal-loss rule
                (= continuous_eval.compute_signal_loss_flags on the same samples) vs the stored flag.
  conditioning  same files: (1) the record filter (continuous_eval.filter_file: whole-file sosfiltfilt + notch filtfilt)
                replicated in 4 lines and checked bit-equal on this file (else the test is not read); features of every
                window recomputed with the record functions (c1b.f7, c1b.graph_and_bp) and checked equal to the build;
                (2) the raw data scaled by (1 + 2**-40) (a relative change of 9.1e-13, far below any EEG meaning) and the
                features recomputed. A window whose features move by O(1) under that change has features set by
                floating-point rounding, not by the signal ("numerically undefined", record chb17b_69_inspect.txt).
  scan          every earlier .npz attached (v9-x3-fold1/3): windows, signal-loss windows, files holding them, non-finite
                f7 / bp5 / adj / zgamma cells inside and outside signal-loss windows.
Outputs: WORK/r2/r0_data/<tag>/ (windows_all.csv.gz, windows_listed.csv, cells_nonfinite.csv, per_file.csv,
evidence_windows.csv, conditioning.csv, conditioning_summary.csv, reference_scan.csv, gfeat.json, summary.json,
SUMMARY.md, run_meta.json, logs/).
"""
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

import r2_core as R

F7_NAMES = ["logbp_0.5-4", "logbp_4-8", "logbp_8-13", "logbp_13-30", "logbp_30-60", "log_line_length", "slog1p_kurtosis"]
BP5_NAMES = ["delta", "theta", "alpha", "beta", "gamma"]
SCALE = 1.0 + 2.0 ** -40
NEIGHBOURS = 3                        # windows listed on each side of a signal-loss or beyond-tolerance window


def _local_index(fidx):
    out = np.empty(len(fidx), np.int64)
    for f in np.unique(fidx):
        m = np.flatnonzero(fidx == f)
        out[m] = np.arange(len(m))
    return out


def _dist_to(mask, fidx):
    """windows to the nearest True of mask in the same file (inf if the file has none)."""
    out = np.full(len(mask), np.inf)
    for f in np.unique(fidx):
        m = np.flatnonzero(fidx == f)
        pos = np.flatnonzero(mask[m])
        if not len(pos):
            continue
        j = np.arange(len(m))
        k = np.searchsorted(pos, j)
        right = np.where(k < len(pos), pos[np.minimum(k, len(pos) - 1)] - j, np.inf)
        left = np.where(k > 0, j - pos[np.maximum(k - 1, 0)], np.inf)
        out[m] = np.minimum(left, right)
    return out


def _fmt(v):
    if isinstance(v, (float, np.floating)):
        return f"{v:.4g}"
    return str(v)


def md_table(df):
    """markdown table without the optional tabulate package."""
    if df is None or not len(df):
        return "(none)"
    cols = [str(c) for c in df.columns]
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    lines += ["| " + " | ".join(_fmt(v) for v in r) + " |" for r in df.itertuples(index=False)]
    return "\n".join(lines)


def rebuild(case, earlier, logs):
    """the case on the earlier view with the record code and the COMMITTED stats.json (= the v2 G-stats input, proven
    equal); returns (npz path, seconds)."""
    t = time.time()
    st = R.committed_stats(case)
    if st is None:
        raise SystemExit(f"STOP diag: no committed stats.json for {case}")
    npz = R.features_record(case, earlier, st, R.SCRATCH / "diag", Path(logs) / f"{case}_diag_features.log")
    return npz, round(time.time() - t, 1)


def localize(case, new_npz, ref_npz, out):
    rep, W = R.compare_features(new_npz, ref_npz, return_windows=True)
    N = np.load(new_npz, allow_pickle=True)
    Rf = np.load(ref_npz, allow_pickle=True)
    if W is None:
        R._jdump(out / "gfeat.json", rep)
        raise SystemExit(f"STOP diag: {case} not exact on all windows (files / count / flags / file_idx): {rep}")
    files = [str(x) for x in N["files"]]
    fidx = N["file_idx"].astype(int)
    sl = N["is_signal_loss"].astype(bool)
    over = np.zeros(len(fidx), bool)
    for k in ("f7", "bp5"):
        over |= (W[f"{k}_maxabs"] > R.TOL[k]) | (W[f"{k}_finite_flips"] > 0)
    over |= W["adj_entries_differing"] > 0
    df = pd.DataFrame(dict(case=case, file=[files[i] for i in fidx], file_idx=fidx, window_in_file=_local_index(fidx),
                           window=np.arange(len(fidx)), is_ictal=N["is_ictal"].astype(bool), is_buffer=N["is_buffer"].astype(bool),
                           is_flag5sd=N["is_flag5sd"].astype(bool), is_signal_loss=sl,
                           f7_max_abs=W["f7_maxabs"], f7_finite_flips=W["f7_finite_flips"],
                           bp5_max_abs=W["bp5_maxabs"], bp5_finite_flips=W["bp5_finite_flips"],
                           adj_entries_differing=W["adj_entries_differing"],
                           zgamma_raw_abs=W.get("zgamma_raw_maxabs", np.zeros(len(fidx))),
                           zgamma_raw_finite_flips=W.get("zgamma_raw_finite_flips", np.zeros(len(fidx), int)),
                           beyond_tolerance=over, windows_to_signal_loss=_dist_to(sl, fidx),
                           windows_to_beyond_tolerance=_dist_to(over, fidx)))
    df.to_csv(out / "windows_all.csv.gz", index=False, float_format="%.6g")
    listed = df[df.is_signal_loss | df.beyond_tolerance | (df.windows_to_signal_loss <= NEIGHBOURS)
                | (df.windows_to_beyond_tolerance <= NEIGHBOURS)]
    listed.to_csv(out / "windows_listed.csv", index=False, float_format="%.6g")
    # every cell whose finiteness differs (new vs record)
    cells = []
    for k, names in (("f7", F7_NAMES), ("bp5", BP5_NAMES)):
        a = np.asarray(N[k], np.float64)
        b = np.asarray(Rf[k], np.float64)
        for w, ch, j in zip(*np.nonzero(np.isfinite(a) != np.isfinite(b))):
            cells.append(dict(array=k, window=int(w), file=files[fidx[w]], window_in_file=int(df.window_in_file[w]),
                              is_signal_loss=bool(sl[w]), channel=int(ch), feature=names[j], new=float(a[w, ch, j]),
                              record=float(b[w, ch, j])))
    pd.DataFrame(cells, columns=["array", "window", "file", "window_in_file", "is_signal_loss", "channel", "feature",
                                 "new", "record"]).to_csv(out / "cells_nonfinite.csv", index=False)
    # which f7 feature carries the largest difference, per beyond-tolerance window (first 2000 listed)
    a = np.asarray(N["f7"], np.float64)
    b = np.asarray(Rf["f7"], np.float64)
    worst = []
    for w in np.flatnonzero(over)[:2000]:
        d = np.where(np.isfinite(a[w]) & np.isfinite(b[w]), np.abs(a[w] - b[w]), np.inf)
        ch, j = np.unravel_index(int(np.argmax(d)), d.shape)
        worst.append(dict(window=int(w), f7_worst_channel=int(ch), f7_worst_feature=F7_NAMES[j]))
    if worst:
        listed = listed.merge(pd.DataFrame(worst), on="window", how="left")
        listed.to_csv(out / "windows_listed.csv", index=False, float_format="%.6g")
    # per file
    rows = []
    for f, g in df.groupby("file", sort=False):
        s, o = g.is_signal_loss, g.beyond_tolerance
        rows.append(dict(file=f, windows=len(g), signal_loss=int(s.sum()), beyond_tol=int(o.sum()),
                         beyond_tol_in_signal_loss=int((o & s).sum()), beyond_tol_outside_signal_loss=int((o & ~s).sum()),
                         signal_loss_equal_within_tol=int((s & ~o).sum()),
                         f7_max_abs_outside_sl=float(g.f7_max_abs[~s].max()) if (~s).any() else 0.0,
                         bp5_max_abs_outside_sl=float(g.bp5_max_abs[~s].max()) if (~s).any() else 0.0,
                         adj_windows_differing_outside_sl=int((g.adj_entries_differing[~s] > 0).sum()),
                         f7_max_abs_in_sl=float(g.f7_max_abs[s].max()) if s.any() else None,
                         bp5_max_abs_in_sl=float(g.bp5_max_abs[s].max()) if s.any() else None,
                         adj_windows_differing_in_sl=int((g.adj_entries_differing[s] > 0).sum()),
                         f7_finite_flips=int(g.f7_finite_flips.sum())))
    pf = pd.DataFrame(rows)
    pf.to_csv(out / "per_file.csv", index=False, float_format="%.6g")
    R._jdump(out / "gfeat.json", rep)
    q = lambda x: {p: float(np.quantile(x, p / 100)) for p in (50, 99, 100)} if len(x) else {}   # noqa: E731
    outside = df[~df.is_signal_loss]
    dist = dict(f7_outside_sl_quantiles=q(outside.f7_max_abs), bp5_outside_sl_quantiles=q(outside.bp5_max_abs),
                zgamma_outside_sl_quantiles=q(outside.zgamma_raw_abs))
    return rep, df, pf, dist


def _filter_replica(data, n_windows):
    """continuous_eval.filter_file after its read, in its own four lines (checked bit-equal before it is used)."""
    from scipy.signal import filtfilt, sosfiltfilt
    import preprocessing as P
    bp = sosfiltfilt(P._BP_SOS, data, axis=1)
    notched = filtfilt(P._NOTCH_B, P._NOTCH_A, bp, axis=1)
    usable = n_windows * P.WIN_SAMPLES
    return np.ascontiguousarray(notched[:, :usable].reshape(data.shape[0], n_windows, P.WIN_SAMPLES)
                                .transpose(1, 0, 2)).astype(np.float32)


def _features(filt, mu, sd):
    import c1b_build_trainset as C1B
    import continuous_eval as CE
    f7, bp, adj = [], [], []
    for s in range(0, len(filt), CE.CHUNK_WINDOWS):                # c1b's own chunking (z-score per chunk)
        zw = CE.zscore(filt[s:s + CE.CHUNK_WINDOWS], mu, sd)
        a, b = C1B.graph_and_bp(zw)
        adj.append(a)
        bp.append(b)
        f7.append(C1B.f7(zw))
    return np.concatenate(f7), np.concatenate(bp), np.concatenate(adj)


def _cmp(a, b):
    """per window: max |diff| over cells finite in both, finite flips."""
    a = np.asarray(a, np.float64).reshape(len(a), -1)
    b = np.asarray(b, np.float64).reshape(len(b), -1)
    both = np.isfinite(a) & np.isfinite(b)
    d = np.where(both, np.abs(np.where(both, a, 0) - np.where(both, b, 0)), 0.0).max(axis=1)
    return d, (np.isfinite(a) != np.isfinite(b)).sum(axis=1)


def evidence_and_conditioning(case, files, earlier, df, new_npz, out):
    """raw evidence + conditioning test on the given files of the case (see module docstring)."""
    import continuous_eval as CE
    import preprocessing as P
    st = R.committed_stats(case)
    mu = np.asarray(st["ch_mean_uV"], np.float64) * 1e-6
    sd = np.asarray(st["ch_std_uV"], np.float64) * 1e-6
    CE.DATASET_DIR = Path(earlier) / "chbmit"
    N = np.load(new_npz, allow_pickle=True)
    ev, cond = [], []
    for f in files:
        g = df[df.file == f]
        gw = g.window.to_numpy()
        path = CE.edf_path(case, f)
        raw = P.open_edf(path)
        data = raw.get_data()
        del raw
        n = len(g)
        seg = data[:, :n * P.WIN_SAMPLES].reshape(data.shape[0], n, P.WIN_SAMPLES)
        rstd = seg.std(axis=2)                                   # [18, n] raw SD per window (V)
        flt_rec, n_rec = CE.filter_file(path)                    # the record filter
        assert n_rec == n, (f, n_rec, n)
        flt_rep = _filter_replica(data, n)
        replica_equal = bool(np.array_equal(flt_rec, flt_rep))
        flt_up = _filter_replica(data * SCALE, n)
        absmax = np.abs(flt_rec.astype(np.float64)).max(axis=(1, 2))
        flag_recomputed = np.all(rstd < CE.SIGNAL_LOSS_STD_V, axis=0)
        for i in range(n):
            ev.append(dict(file=f, window_in_file=i, window=int(gw[i]), is_signal_loss=bool(g.is_signal_loss.iloc[i]),
                           signal_loss_recomputed=bool(flag_recomputed[i]), raw_sd_max_V=float(rstd[:, i].max()),
                           raw_sd_min_V=float(rstd[:, i].min()), filtered_absmax_V=float(absmax[i]),
                           beyond_tolerance=bool(g.beyond_tolerance.iloc[i])))
        f7a, bpa, adja = _features(flt_rec, mu, sd)
        f7b, bpb, adjb = _features(flt_up, mu, sd)
        d_build_f7, fl_build_f7 = _cmp(f7a, N["f7"][gw])
        d_build_bp, _ = _cmp(bpa, N["bp5"][gw])
        A0, B0 = adja.astype(np.float32), N["adj"][gw].astype(np.float32)
        d_build_adj = ((A0 != B0) & ~(np.isnan(A0) & np.isnan(B0))).reshape(n, -1).sum(axis=1)
        d7, fl7 = _cmp(f7a, f7b)
        d5, _ = _cmp(bpa, bpb)
        A, B = adja.astype(np.float32), adjb.astype(np.float32)
        dadj = ((np.abs(A - B) > R.TOL["adj_entry"]) | (np.isnan(A) != np.isnan(B))).reshape(n, -1).sum(axis=1)
        for i in range(n):
            cond.append(dict(file=f, window_in_file=i, window=int(gw[i]), is_signal_loss=bool(g.is_signal_loss.iloc[i]),
                             beyond_tolerance=bool(g.beyond_tolerance.iloc[i]), replica_filter_bit_equal=replica_equal,
                             recomputed_vs_build_f7=float(d_build_f7[i]), recomputed_vs_build_f7_flips=int(fl_build_f7[i]),
                             recomputed_vs_build_bp5=float(d_build_bp[i]), recomputed_vs_build_adj_entries=int(d_build_adj[i]),
                             scaled_f7_max_abs=float(d7[i]), scaled_f7_finite_flips=int(fl7[i]),
                             scaled_bp5_max_abs=float(d5[i]), scaled_adj_entries_differing=int(dadj[i])))
        R.log(f"diag {case}/{f}: {n} windows, signal-loss {int(g.is_signal_loss.sum())}, replica filter bit-equal "
              f"{replica_equal}")
        del data, seg, flt_rec, flt_rep, flt_up
    ev = pd.DataFrame(ev)
    cond = pd.DataFrame(cond)
    ev.to_csv(out / "evidence_windows.csv", index=False, float_format="%.6g")
    cond.to_csv(out / "conditioning.csv", index=False, float_format="%.6g")
    rows = []
    for (f, s), g in cond.groupby(["file", "is_signal_loss"]):
        e = ev[(ev.file == f) & (ev.is_signal_loss == s)]
        rows.append(dict(file=f, group="signal_loss" if s else "other", windows=len(g),
                         raw_sd_max_V_median=float(e.raw_sd_max_V.median()), filtered_absmax_V_median=float(e.filtered_absmax_V.median()),
                         replica_filter_bit_equal=bool(g.replica_filter_bit_equal.all()),
                         recomputed_vs_build_f7_max=float(g.recomputed_vs_build_f7.max()),
                         recomputed_vs_build_adj_entries=int(g.recomputed_vs_build_adj_entries.sum()),
                         scaled_f7_median=float(g.scaled_f7_max_abs.median()), scaled_f7_max=float(g.scaled_f7_max_abs.max()),
                         scaled_f7_windows_with_flip=int((g.scaled_f7_finite_flips > 0).sum()),
                         scaled_bp5_median=float(g.scaled_bp5_max_abs.median()), scaled_bp5_max=float(g.scaled_bp5_max_abs.max()),
                         scaled_adj_windows_differing=int((g.scaled_adj_entries_differing > 0).sum()),
                         signal_loss_rule_recomputed_equal=bool((e.signal_loss_recomputed == e.is_signal_loss).all())))
    cs = pd.DataFrame(rows)
    cs.to_csv(out / "conditioning_summary.csv", index=False, float_format="%.6g")
    return ev, cond, cs


def scan_references(cases, out):
    rows = []
    for c in cases:
        try:
            p = R.locate_earlier(c)
        except SystemExit as e:
            rows.append(dict(case=c, error=str(e)))
            continue
        with np.load(p, allow_pickle=True) as z:
            sl = z["is_signal_loss"].astype(bool)
            fidx = z["file_idx"].astype(int)
            files = [str(x) for x in z["files"]]
            r = dict(case=c, windows=len(sl), signal_loss=int(sl.sum()),
                     files_with_signal_loss=";".join(sorted({files[i] for i in np.unique(fidx[sl])})))
            for k in ("f7", "bp5", "adj", "zgamma_raw"):
                if k not in z.files:
                    continue
                bad = ~np.isfinite(np.asarray(z[k], np.float32))
                bad = bad.reshape(len(bad), -1).sum(axis=1) if bad.ndim > 1 else bad.astype(int)
                r[f"{k}_nonfinite_cells_in_sl"] = int(bad[sl].sum())
                r[f"{k}_nonfinite_cells_outside_sl"] = int(bad[~sl].sum())
        rows.append(r)
    df = pd.DataFrame(rows)
    df.to_csv(out / "reference_scan.csv", index=False)
    return df


def diagnose(case, earlier, scan_cases=None):
    t0 = time.time()
    out = R.out_dir()
    logs = out / "logs"
    ref = R.locate_earlier(case)
    npz, build_s = rebuild(case, earlier, logs)
    R.phase("rebuild", t0)
    t = time.time()
    rep, df, pf, dist = localize(case, npz, ref, out)
    R.phase("localize", t)
    t = time.time()
    files = list(pf[(pf.signal_loss > 0) | (pf.beyond_tol > 0)].file)
    ev, cond, cs = evidence_and_conditioning(case, files, earlier, df, npz, out) if files else (None, None, pd.DataFrame())
    R.phase("evidence_conditioning", t)
    t = time.time()
    scan = scan_references(scan_cases or R.CHB_CASES, out)
    R.phase("reference_scan", t)
    sl = df.is_signal_loss
    o = df.beyond_tolerance
    summ = dict(case=case, reference=str(ref), reference_sha256=R.sha256_file(ref), build_s=build_s,
                windows=len(df), signal_loss_windows=int(sl.sum()), beyond_tolerance_windows=int(o.sum()),
                beyond_tolerance_in_signal_loss=int((o & sl).sum()), beyond_tolerance_outside_signal_loss=int((o & ~sl).sum()),
                signal_loss_windows_within_tolerance=int((sl & ~o).sum()),
                files_with_beyond_tolerance=sorted(set(df.file[o])), files_with_signal_loss=sorted(set(df.file[sl])),
                min_windows_from_beyond_tolerance_outside_sl_to_signal_loss=(float(df.windows_to_signal_loss[o & ~sl].min())
                                                                             if (o & ~sl).any() else None),
                nonfinite_flip_cells=int(df.f7_finite_flips.sum() + df.bp5_finite_flips.sum()),
                gfeat_all_windows=rep.get("status_all_windows"), gfeat_chain_windows=rep.get("status_chain_windows"),
                gfeat_status_with_scope=rep["status"], gfeat_scope=rep.get("gate_scope"),
                outside_signal_loss_distribution=dist,
                reference_cases_with_signal_loss={r.case: int(r.signal_loss) for r in scan.itertuples()
                                                  if getattr(r, "signal_loss", 0) and r.signal_loss > 0})
    R._jdump(out / "summary.json", summ)
    md = [f"# R0 diagnosis of {case} (descriptive; plan §12 07/11 12:49)", "",
          f"Rebuilt with the record code on the earlier view and the committed stats.json; compared with `{ref.name}` "
          f"(sha256 {summ['reference_sha256'][:12]}). Build {build_s:.0f} s.", "",
          f"- windows {summ['windows']}; signal-loss {summ['signal_loss_windows']}; beyond tolerance {summ['beyond_tolerance_windows']} "
          f"(in signal-loss {summ['beyond_tolerance_in_signal_loss']}, outside {summ['beyond_tolerance_outside_signal_loss']})",
          f"- G-feat: all windows {summ['gfeat_all_windows']}; chain windows {summ['gfeat_chain_windows']}; "
          f"gate (scope {summ['gfeat_scope']}) {summ['gfeat_status_with_scope']}",
          f"- non-finite flip cells: {summ['nonfinite_flip_cells']} (`cells_nonfinite.csv`)",
          f"- outside signal-loss, max |diff| quantiles (50/99/100 %): f7 {dist['f7_outside_sl_quantiles']}; "
          f"bp5 {dist['bp5_outside_sl_quantiles']}", "", "## Per file (files with signal-loss or beyond-tolerance windows)", "",
          md_table(pf[(pf.signal_loss > 0) | (pf.beyond_tol > 0)]), "",
          "## Conditioning (raw x (1 + 2**-40); record filter replicated bit-equal first)", "",
          md_table(cs), "", "## G-feat blocks", "", "```",
          json.dumps(rep.get("windows"), indent=1, default=str), "```", "", "## Earlier .npz scan (24 cases)", "",
          md_table(scan), ""]
    (out / "SUMMARY.md").write_text("\n".join(md))
    R.log(f"diag {case}: beyond tolerance {summ['beyond_tolerance_windows']} windows "
          f"(outside signal-loss {summ['beyond_tolerance_outside_signal_loss']}); G-feat all {summ['gfeat_all_windows']}, "
          f"chain {summ['gfeat_chain_windows']}")
    return summ
