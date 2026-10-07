#!/usr/bin/env python
"""
e18_cpd_localizer.py -- stage P2, E18 (design approved 2026-10-07, PERF_PHASE_RECORD 6.3).
Objective 2 of the registration form: temporal localization (onset, offset) with NON-PARAMETRIC change
point detection on the ensemble anomaly score. 15 non-test subjects, 4 seeds, cache only.

Detection: D1 on the candidate scalar (cell re-selected by the 4-seed pooled rule), plus the E19
short branch if E19 adopted it (--short-p). Localization: for every detected event, the UNSMOOTHED
scalar on [event - 15 windows, event + 15 windows] inside the file (always >= 31 windows, short events
included); signal-loss windows replaced by the segment median; ruptures KernelCPD (rbf, min_size 2),
exactly 2 change points (no penalty to tune). New event = the segment between the two change points,
kept only if it spans >= 2 windows and its mean exceeds the means of both outer segments; otherwise
the detector's own boundaries are kept (fallback, rate reported). Events are re-merged (90 s).
E18 CANNOT raise sensitivity or lower FA/day: it only moves boundaries (SzCORE tolerates 30 s / 60 s).
Detection guard: pooled sensitivity >= detector - 0.02 and FA/day <= detector + 1 (4-seed mean).
No-CPD control (reviewer, 2026-10-07; reported, not gated): boundaries = first and last window of the
UNSMOOTHED scalar above the detector's threshold inside the same segment -- separates the gain of
looking at the unsmoothed score from the gain of change point detection itself.
Localization metric: for every reference seizure matched by a detector event (E1 overlap rule, matched
on the detector events so n is identical for both boundary sets), |onset error| and |offset error| in
seconds, detector boundaries vs CPD boundaries; median, IQR, n, signed median bias; also split by event
duration (<= 30 s vs longer).
E18d (2026-10-07, --overlap): a CPD segment is accepted only if it overlaps the detector event, else
the detector's boundaries; seizures lost after CPD are listed (lost_<arm>.csv). Choice between E18 and
E18d: among arms passing the localization rule, the higher post-CPD sensitivity; ties -> E18.
ADOPTED as the localizer if the detection guard holds and the median onset and offset errors are each
not worse than the detector's by more than 4 s, and at least one is strictly better.
If not: report error by seizure duration and bias sign; fallbacks fixed now: --input smoothed (E18b,
CPD on the D1-smoothed scalar) and --margin 30 (E18c), same rule.
E20a (approved 2026-10-07, --multi): the same localizer with KernelCPD on the 18-channel trajectory
(per-channel robust-z latent distances, each E16e-detrended), acceptance judged on the final scalar.
Adopted in place of E18 only if post-CPD sensitivity >= E18's on the same scalar and the median onset
and offset errors are each not worse than E18's, with at least one better by >= 4 s. Localizer only;
no detection role (E20b not run). Diagnostics added the same day: a stronger no-CPD control (the
contiguous supra-threshold run containing the event peak, 1-window gaps bridged, no 90 s merge) and
the split-reference table (references > 300 s cut into 300-s pieces, as SzCORE does).
Run:  python src/e18_cpd_localizer.py --scalar Eb [--short-p P]     (estimated 5-15 min, not measured)
"""
import argparse
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import p2_scalars as PS                # noqa: E402
import e16_recording_baseline as E16   # noqa: E402
import e8_gae_v2_eval as E8            # noqa: E402
FINE = [0.05, 0.03, 0.02, 0.015, 0.01, 0.0075, 0.005, 0.002, 0.001]

OUT = ROOT / "results" / "e18_cpd_localizer"
PARTS = ("C", "L", "gamma")
WIN = PS.WIN


def scalar(ctx, tag, a, c_k=9):
    """final scalar from --c-arm / --parts (or the legacy --scalar names)."""
    if a.parts == "family":                    # E17b latent family, if adopted
        import e17b_latent_family as F17
        raw = [PS._full(ctx, F17.member(ctx["D"][tag], ctx["wf"], kk)) for kk in F17.MEMBERS.values()]
        return np.mean([PS.pct(v, ctx["ok"]) for v in raw], axis=0)
    parts = tuple(a.parts.split(",")) if a.parts else PARTS
    c_arm = a.c_arm
    if a.scalar == "Eb_h":
        c_arm = "e"
    if parts == ("C",):
        v = E16.rz(PS.readout(ctx, tag, "C", c_arm=c_arm, c_k=c_k), ctx["ok"])
    else:
        v = PS.ensemble_scalar(ctx, tag, parts, c_arm=c_arm, c_k=c_k)
    return PS.detrend_file(ctx, v) if a.scalar == "Eb_dt" else v

OVERLAP = False   # E18d: accept the CPD segment only if it overlaps the detector event


def cpd_event(x, ok, a_w, b_w, margin):
    """x, ok: per-file arrays. a_w, b_w: event in windows [a_w, b_w). Returns (a, b, used_cpd)."""
    import ruptures as rpt
    s0, s1 = max(0, a_w - margin), min(len(x), b_w + margin)
    seg = x[s0:s1].astype(float).copy()
    good = ok[s0:s1] & np.isfinite(seg)
    if good.sum() < 6 or len(seg) < 6:
        return a_w, b_w, False
    seg[~good] = np.median(seg[good])
    try:
        bk = rpt.KernelCPD(kernel="rbf", min_size=2).fit(seg.reshape(-1, 1)).predict(n_bkps=2)
    except Exception:
        return a_w, b_w, False
    b1, b2 = bk[0], bk[1]
    inner, left, right = seg[b1:b2], seg[:b1], seg[b2:]
    if b2 - b1 < 2 or not len(left) or not len(right) or not (inner.mean() > left.mean() and inner.mean() > right.mean()):
        return a_w, b_w, False
    if OVERLAP and not (s0 + b2 > a_w and s0 + b1 < b_w):
        return a_w, b_w, False
    return s0 + b1, s0 + b2, True


def thr_event(x, ok, a_w, b_w, margin, thr):
    """non-CPD control: first and last window of the unsmoothed scalar above the detector threshold,
    inside the same segment; the detector's boundaries if none."""
    s0, s1 = max(0, a_w - margin), min(len(x), b_w + margin)
    above = np.flatnonzero(ok[s0:s1] & (np.nan_to_num(x[s0:s1], nan=-np.inf) > thr))
    if not len(above):
        return a_w, b_w
    return s0 + above[0], s0 + above[-1] + 1


def run_event(x, ok, a_w, b_w, margin, thr, gap=1):
    """stronger no-CPD control (reviewer 2026-10-07): the contiguous run of the UNSMOOTHED scalar above
    the detector threshold that contains the event's peak, gaps of <= `gap` windows bridged, no 90 s
    merge, limited to the event +- margin; the detector's boundaries if the peak is not above it."""
    s0, s1 = max(0, a_w - margin), min(len(x), b_w + margin)
    xs = np.where(ok[s0:s1], np.nan_to_num(x[s0:s1], nan=-np.inf), -np.inf)
    inner = xs[a_w - s0:b_w - s0]
    if not len(inner) or not np.isfinite(inner).any():
        return a_w, b_w
    pk = (a_w - s0) + int(np.argmax(inner))
    if xs[pk] <= thr:
        return a_w, b_w
    above = xs > thr
    lo = pk
    while lo - 1 >= 0 and (above[lo - 1] or (lo - 2 >= 0 and gap >= 1 and above[lo - 2])):
        lo -= 1
    hi = pk
    while hi + 1 < len(xs) and (above[hi + 1] or (hi + 2 < len(xs) and gap >= 1 and above[hi + 2])):
        hi += 1
    while lo < pk and not above[lo]:
        lo += 1
    while hi > pk and not above[hi]:
        hi -= 1
    return s0 + lo, s0 + hi + 1


def cpd_event_multi(XM, x, ok, a_w, b_w, margin):
    """E20a: kernel CPD (rbf, 2 change points) on the 18-channel trajectory XM (per-channel
    robust-z distances, E16e-detrended) over the event +- margin; acceptance (bump) judged on the
    final scalar x, exactly as cpd_event; detector boundaries otherwise."""
    import ruptures as rpt
    s0, s1 = max(0, a_w - margin), min(len(x), b_w + margin)
    seg = XM[s0:s1].astype(float).copy()
    xs = x[s0:s1].astype(float).copy()
    good = ok[s0:s1] & np.isfinite(xs) & np.isfinite(seg).all(axis=1)
    if good.sum() < 6 or len(seg) < 6:
        return a_w, b_w, False
    seg[~good] = np.median(seg[good], axis=0)
    xs[~good] = np.median(xs[good])
    try:
        bk = rpt.KernelCPD(kernel="rbf", min_size=2).fit(seg).predict(n_bkps=2)
    except Exception:
        return a_w, b_w, False
    b1, b2 = bk[0], bk[1]
    inner, left, right = xs[b1:b2], xs[:b1], xs[b2:]
    if b2 - b1 < 2 or not len(left) or not len(right) or not (inner.mean() > left.mean() and inner.mean() > right.mean()):
        return a_w, b_w, False
    if OVERLAP and not (s0 + b2 > a_w and s0 + b1 < b_w):
        return a_w, b_w, False
    return s0 + b1, s0 + b2, True


def channel_trajectory(ctx, tag):
    """per-channel robust-z of the per-channel latent distances, each minus its +-15 min running median
    inside each file (the E16e correction channel by channel); n x 18, NaN at signal-loss windows."""
    D = ctx["D"][tag].astype(np.float64); wf = ctx["wf"]
    okk = np.ones(len(D), bool)
    Zc = np.column_stack([E16.rz(D[:, j], okk) for j in range(D.shape[1])])
    for f in np.unique(wf):
        w = np.flatnonzero(wf == f)
        Zc[w] = Zc[w] - pd.DataFrame(Zc[w]).rolling(451, min_periods=1, center=True).median().values
    out = np.full((ctx["n"], D.shape[1]), np.nan); out[ctx["idx"]] = Zc
    return out


def split_pieces(a, b, max_s=300):
    """SzCORE/timescoring split of a reference event longer than max_s into consecutive pieces."""
    if b - a <= max_s:
        return [(a, b)]
    out, t = [], a
    while t < b:
        out.append((t, min(t + max_s, b))); t += max_s
    return out


def match_errors(refs, hyp):
    """for each reference, the first hypothesis overlapping it (E1 rule) -> (ref, hyp) pairs (seconds)."""
    pairs = []
    for f, rr in refs.items():
        for a, b in rr:
            for h0, h1 in hyp.get(f, []):
                if h1 >= a - 30 and h0 <= b + 60:
                    pairs.append((f, a, b, h0, h1)); break
    return pairs


def main():
    import e1_normal_definition as E1
    ap = argparse.ArgumentParser()
    ap.add_argument("--scalar", default="Eb", choices=["Eb", "Eb_dt", "Eb_h"])
    ap.add_argument("--c-arm", default="S9base", choices=["S9base", "e", "b"], help="C of the final scalar (E21)")
    ap.add_argument("--parts", default=None, help="comma list, e.g. C,L,gamma or C (E21 final scalar)")
    ap.add_argument("--fine", action="store_true", help="E21 fine top-p grid")
    ap.add_argument("--short-p", type=float, default=None, help="E19 short branch p_s, if E19 adopted it")
    ap.add_argument("--input", default="raw", choices=["raw", "smoothed"])
    ap.add_argument("--margin", type=int, default=15)
    ap.add_argument("--main-cell", default=None, help="smooth,top of the main detector when E19b adopted a union")
    ap.add_argument("--overlap", action="store_true", help="E18d: CPD segment must overlap the detector event")
    ap.add_argument("--multi", action="store_true", help="E20a: multivariate CPD on the 18-channel trajectory")
    ap.add_argument("--no-ledger", action="store_true", help="diagnostic re-run: do not append to the ledger")
    a = ap.parse_args()
    global OVERLAP
    OVERLAP = a.overlap
    if a.fine:
        E1.TOPS = FINE
    spec = f"{a.scalar}" if not a.parts else f"{a.parts.replace(',', '+')}_C{a.c_arm}"
    spec += "_fine" if a.fine else ""
    arm = (f"{spec}_{a.input}_m{a.margin}" + (f"_short{a.short_p}" if a.short_p else "") + ("_ovl" if a.overlap else "")
           + ("_multi" if a.multi else ""))
    base_arm = f"{spec}_{a.input}_m{a.margin}" + (f"_short{a.short_p}" if a.short_p else "")
    OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    ctxs, X, rows = {}, {}, []
    for s in E8.SUBJS:
        ctx = PS.subject_context(s); ctxs[s] = ctx
        d = E8.d_for_grid(ctx["z"])
        for tag in PS.TAGS:
            X[(s, tag)] = scalar(ctx, tag, a)
            for r_ in E1.event_grid(d, X[(s, tag)]):
                r_.update(subject=s, score=f"{tag}|main", nonict_h=ctx["nh"]); rows.append(r_)
    gr = pd.DataFrame(rows); gr["kind"] = "main"; gr["seed"] = gr.score.str.split("|").str[0]
    Mn = E16.summarise(gr, "main")
    if Mn["cell"] is None:
        raise SystemExit("STOP: the scalar never reaches FA/day <= 25")
    sm_, top_ = Mn["cell"][0], Mn["cell"][1]
    if a.main_cell:
        sm_, top_ = int(a.main_cell.split(",")[0]), float(a.main_cell.split(",")[1])

    det_rows, err_rows, fb, lost, lostp = [], [], [], [], []
    for s in E8.SUBJS:
        ctx = ctxs[s]
        g = gr[(gr.subject == s) & (gr.smooth == sm_) & (gr.top == top_)].set_index("seed")
        refs = {}
        for f in np.unique(ctx["fidx"]):
            m = np.flatnonzero(ctx["fidx"] == f)
            refs[f] = [(i * WIN, j * WIN) for i, j in PS._runs(ctx["ict"][m])]
        for tag in PS.TAGS:
            x = X[(s, tag)]
            main = PS.d1_events(ctx, x, sm_, top_)
            tp, fp, nr, h = PS.score(ctx, main)
            if tp != int(g.loc[tag, "tp"]) or fp != int(g.loc[tag, "fp"]):
                raise SystemExit(f"STOP {s} {tag}: D1 ({tp},{fp}) differs from event_grid "
                                 f"({int(g.loc[tag, 'tp'])},{int(g.loc[tag, 'fp'])})")
            det = {f: list(v) for f, v in main.items()}
            kind = {f: ["main"] * len(v) for f, v in main.items()}
            if a.short_p:
                short = PS.d1_events(ctx, x, 3, a.short_p, keep_max_s=30)
                for f in set(det) | set(short):
                    allev = sorted([(e, "main") for e in det.get(f, [])] + [(e, "short") for e in short.get(f, [])])
                    merged, mk = [], []
                    for (e0, e1), k in allev:
                        if merged and e0 - merged[-1][1] <= PS.MERGE_S:
                            merged[-1] = (merged[-1][0], max(e1, merged[-1][1])); mk[-1] = "main" if "main" in (k, mk[-1]) else k
                        else:
                            merged.append((e0, e1)); mk.append(k)
                    det[f], kind[f] = merged, mk
            xin = x if a.input == "raw" else PS.smoothed(ctx, x, sm_)
            thr = np.nanquantile(PS.smoothed(ctx, x, sm_), 1 - top_)
            XM = channel_trajectory(ctx, tag) if a.multi else None

            def localize(f, aw, bw):
                mm = np.flatnonzero(ctx["fidx"] == f)
                if a.multi:
                    return cpd_event_multi(XM[mm], xin[mm], ctx["ok"][mm], aw, bw, a.margin)
                return cpd_event(xin[mm], ctx["ok"][mm], aw, bw, a.margin)
            loc, lk, pair = {}, {}, {}
            for f in det:
                m = np.flatnonzero(ctx["fidx"] == f)
                xf, okf = xin[m], ctx["ok"][m]
                new = []
                for (e0, e1), k in zip(det[f], kind[f]):
                    a_w, b_w, used = localize(f, e0 // WIN, e1 // WIN)
                    new.append((a_w * WIN, b_w * WIN))
                    pair[(f, e0, e1)] = (a_w * WIN, b_w * WIN, used)
                    fb.append(dict(subject=s, seed=tag, kind=k, short=(e1 - e0) <= 30, used_cpd=used))
                loc[f] = PS.merge(new)
            tpd, fpd, nrd, hd = PS.score(ctx, det)
            tpc, fpc, nrc, hc = PS.score(ctx, loc)
            # diagnostic: seizures caught by the detector but not after CPD (E1 overlap rule)
            for f, rr in refs.items():
                for ra, rb in rr:
                    hit = [(h0, h1) for h0, h1 in det.get(f, []) if h1 >= ra - 30 and h0 <= rb + 60]
                    if hit and not any(c1 >= ra - 30 and c0 <= rb + 60 for c0, c1 in loc.get(f, [])):
                        h0, h1 = hit[0]; c0, c1, used = pair[(f, h0, h1)]
                        lost.append(dict(subject=s, seed=tag, file=int(f), ref_on=ra, ref_dur=rb - ra,
                                         det_on=h0, det_dur=h1 - h0, cpd_on=c0, cpd_dur=c1 - c0, used_cpd=used,
                                         cpd_overlaps_det=bool(c1 > h0 and c0 < h1),
                                         cpd_shift_s=(c0 + c1) / 2 - (h0 + h1) / 2))
            # split-reference diagnostic: pieces of references > 300 s (SzCORE split), overlap without tolerance
            for f, rr in refs.items():
                for ra, rb in rr:
                    for pa, pb in split_pieces(ra, rb):
                        dh = any(h1 > pa and h0 < pb for h0, h1 in det.get(f, []))
                        ch = any(c1 > pa and c0 < pb for c0, c1 in loc.get(f, []))
                        lostp.append(dict(subject=s, seed=tag, file=int(f), ref_on=ra, ref_dur=rb - ra,
                                          piece_on=pa, piece_dur=pb - pa, long=(rb - ra) > 300,
                                          det_cover=dh, cpd_cover=ch))
            det_rows += [dict(subject=s, seed=tag, arm="detector", tp=tpd, fp=fpd, n_ref=nrd, nonict_h=hd),
                         dict(subject=s, seed=tag, arm="cpd", tp=tpc, fp=fpc, n_ref=nrc, nonict_h=hc)]
            # localization errors, matched on the detector events (same n for both boundary sets)
            for f, ra, rb, h0, h1 in match_errors(refs, det):
                a_w, b_w, used = localize(f, h0 // WIN, h1 // WIN)
                c0, c1 = a_w * WIN, b_w * WIN
                mf = np.flatnonzero(ctx["fidx"] == f)
                t_a, t_b = thr_event(x[mf], ctx["ok"][mf], h0 // WIN, h1 // WIN, a.margin, thr)
                r_a, r_b = run_event(x[mf], ctx["ok"][mf], h0 // WIN, h1 // WIN, a.margin, thr)
                err_rows.append(dict(subject=s, seed=tag, ref_dur=rb - ra, ev_dur=h1 - h0, used_cpd=used,
                                     det_on=h0 - ra, det_off=h1 - rb, cpd_on=c0 - ra, cpd_off=c1 - rb,
                                     thr_on=t_a * WIN - ra, thr_off=t_b * WIN - rb,
                                     run_on=r_a * WIN - ra, run_off=r_b * WIN - rb))
        print(f"{s}: done ({time.time()-t0:.0f}s)", flush=True)

    Dd, Ee, Fb = pd.DataFrame(det_rows), pd.DataFrame(err_rows), pd.DataFrame(fb)
    Dd.to_csv(OUT / f"detection_{arm}.csv", index=False); Ee.to_csv(OUT / f"errors_{arm}.csv", index=False)
    Fb.to_csv(OUT / f"fallback_{arm}.csv", index=False)
    Lo = pd.DataFrame(lost); Lo.to_csv(OUT / f"lost_{arm}.csv", index=False)
    Lp = pd.DataFrame(lostp); Lp.to_csv(OUT / f"pieces_{arm}.csv", index=False)
    q = Dd.groupby(["arm", "seed"])[["tp", "fp", "n_ref", "nonict_h"]].sum().reset_index()
    q["sens"] = q.tp / q.n_ref; q["fa_day"] = q.fp / q.nonict_h * 24
    P = q.groupby("arm")[["sens", "fa_day"]].mean()

    def stats(col, df):
        v = df[col].abs()
        return f"median {v.median():5.1f} s  IQR [{v.quantile(.25):.1f}, {v.quantile(.75):.1f}]  bias {df[col].median():+5.1f} s"

    lines = [f"# {'E20a -- multivariate' if a.multi else 'E18 --'} kernel CPD onset/offset localizer, arm {arm}, 4 seeds, 15 non-test\n",
             f"Detector cell (re-selected): smooth {sm_}, top {top_}; D1 reproduction of event_grid exact.\n",
             "## Detection (guard only; CPD cannot raise sensitivity or lower FA)\n", "```",
             f"detector  sens {P.loc['detector', 'sens']:.3f}  FA/day {P.loc['detector', 'fa_day']:.2f}",
             f"cpd       sens {P.loc['cpd', 'sens']:.3f}  FA/day {P.loc['cpd', 'fa_day']:.2f}", "```",
             f"\n## Localization on matched seizures (n = {len(Ee)} reference-seed pairs; "
             f"CPD used on {Ee.used_cpd.mean():.0%} of them; fallback rate on all events "
             f"{1 - Fb.used_cpd.mean():.0%}, short events {1 - Fb[Fb.short].used_cpd.mean() if Fb.short.any() else float('nan'):.0%})\n", "```"]
    for lab, df in (("all", Ee), ("events <= 30 s", Ee[Ee.ev_dur <= 30]), ("events > 30 s", Ee[Ee.ev_dur > 30])):
        if not len(df):
            continue
        lines += [f"{lab} (n = {len(df)})",
                  f"  onset   detector {stats('det_on', df)} | cpd {stats('cpd_on', df)}",
                  f"          no-CPD control (unsmoothed > threshold) {stats('thr_on', df)}",
                  f"          no-CPD control 2 (contiguous run, no merge) {stats('run_on', df)}",
                  f"  offset  detector {stats('det_off', df)} | cpd {stats('cpd_off', df)}",
                  f"          no-CPD control (unsmoothed > threshold) {stats('thr_off', df)}",
                  f"          no-CPD control 2 (contiguous run, no merge) {stats('run_off', df)}"]
    lines.append("```")
    guard = P.loc["cpd", "sens"] >= P.loc["detector", "sens"] - 0.02 and P.loc["cpd", "fa_day"] <= P.loc["detector", "fa_day"] + 1
    don, doff = Ee.det_on.abs().median(), Ee.det_off.abs().median()
    con, coff = Ee.cpd_on.abs().median(), Ee.cpd_off.abs().median()
    loc_ok = con <= don + 4 and coff <= doff + 4 and (con < don or coff < doff)
    adopted = bool(guard and loc_ok)
    if not a.no_ledger:
        E16.ledger("E20a" if a.multi else "E18", arm,
                   dict(best=float(P.loc["cpd", "sens"]), cell=(sm_, top_, round(float(P.loc["cpd", "fa_day"]), 2))),
                   dict(detection_guard=guard, localization=loc_ok), "ADOPTED" if adopted else "NOT adopted")
    lines += [f"\n- detection guard -> {'pass' if guard else 'FAIL'}",
              f"- localization: onset {con:.1f} vs {don:.1f} s, offset {coff:.1f} vs {doff:.1f} s -> {'pass' if loc_ok else 'FAIL'}",
              f"\n**{'ADOPTED: kernel CPD is the onset/offset localizer' if adopted else 'NOT adopted'}**"]
    nl = len(Lo)
    lines += [f"\n## Seizure-seed pairs caught by the detector but lost after CPD: {nl} "
              f"({nl / 4:.1f} per seed)\n"]
    if nl:
        lines += ["```", f"CPD segment overlaps the detector event: {Lo.cpd_overlaps_det.mean():.0%}; "
                  f"median centre shift {Lo.cpd_shift_s.median():+.0f} s; median CPD segment {Lo.cpd_dur.median():.0f} s "
                  f"vs detector event {Lo.det_dur.median():.0f} s; median seizure {Lo.ref_dur.median():.0f} s",
                  Lo.drop(columns=["file"]).to_string(index=False), "```"]
    prev = OUT / f"detection_{base_arm}.csv"
    if a.overlap and prev.exists():
        Q = pd.read_csv(prev).groupby(["arm", "seed"])[["tp", "fp", "n_ref", "nonict_h"]].sum().reset_index()
        Q["sens"] = Q.tp / Q.n_ref
        s_base = float(Q[Q.arm == "cpd"].groupby("seed").sens.mean().mean())
        lines.append(f"\nChoice rule (fixed before the run): among arms passing the localization rule, the one with the "
                     f"higher post-CPD sensitivity. E18 {s_base:.3f} vs E18d {P.loc['cpd', 'sens']:.3f} -> "
                     f"**{'E18d' if adopted and P.loc['cpd', 'sens'] > s_base else 'E18'}** "
                     f"(E18d must also pass the localization rule; ties -> E18)")
    if len(Lp):
        n_pieces = len(Lp) / 4
        n_scorer = Dd[Dd.arm == "detector"].groupby("seed").n_ref.sum().mean()
        lp = Lp[Lp.det_cover & ~Lp.cpd_cover]
        lines += [f"\n## Split-reference diagnostic (references > 300 s cut into 300-s pieces)\n", "```",
                  f"pieces per seed {n_pieces:.1f} vs scorer n_ref per seed {n_scorer:.1f} (equal if the split rule is right)",
                  f"pieces covered by the detector but not after CPD: {len(lp)} ({len(lp) / 4:.1f} per seed), "
                  f"of which in seizures > 300 s: {int(lp.long.sum())}",
                  (lp.drop(columns=["file"]).to_string(index=False) if len(lp) else "none"), "```"]
    if a.multi:
        base = OUT / f"errors_{arm.replace('_multi', '')}.csv"
        bdet = OUT / f"detection_{arm.replace('_multi', '')}.csv"
        if base.exists() and bdet.exists():
            Eb_ = pd.read_csv(base)
            Q = pd.read_csv(bdet).groupby(["arm", "seed"])[["tp", "n_ref"]].sum().reset_index()
            s_base = float((Q[Q.arm == "cpd"].tp / Q[Q.arm == "cpd"].n_ref).mean())
            bon, boff = Eb_.cpd_on.abs().median(), Eb_.cpd_off.abs().median()
            g_s = P.loc["cpd", "sens"] >= s_base
            g_l = con <= bon and coff <= boff and (con <= bon - 4 or coff <= boff - 4)
            lines.append(f"\nE20a rule (fixed before the run): post-CPD sensitivity {P.loc['cpd', 'sens']:.3f} >= E18 "
                         f"{s_base:.3f} -> {'pass' if g_s else 'FAIL'}; onset {con:.1f} vs {bon:.1f} s, offset {coff:.1f} vs "
                         f"{boff:.1f} s, neither worse and one better by >= 4 s -> {'pass' if g_l else 'FAIL'} -> "
                         f"**{'E20a replaces E18 as the localizer' if g_s and g_l else 'E18 stays the localizer'}**")
        else:
            lines.append("\nE20a rule: the E18 run on the same scalar is missing; run it first.")
    lines += [f"\nElapsed {time.time()-t0:.0f} s."]
    (OUT / f"SUMMARY_{arm}.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
