#!/usr/bin/env python
"""
r2_rp4.py -- research track, stage RP, step RP4 (docs/FUTURE_RESEARCH_PLAN.md §7b; rules in §12 row 12/11 09:40, D21-F,
written before any RP4 output). Missed seizures and false alarms of the report's main model (seeds 1-4, k per seed),
read from the committed RP2 per-window scores; no model is run.

  gate     R4.0: a context built from each rp2/scores file + p3c_freeze.run_budget (saved x, q_raw of rp2/q.csv)
           reproduce rp2/per_subject.csv (tp, fp, n_ref exact; top, nonict_h relative 1e-9) and rp2/errors.csv (pairs in
           order) for test 8 + chb24 + Siena 14, seeds 1-4, arms frozen and L2f, stages detector / cpd / hybrid;
           thresholds vs rp2/thresholds.csv relative 1e-6; file map (windows per file = R0 inventory, files sorted by name);
           every reference seizure joined to results/v9_v1/part1_descriptors.csv by (file, onset_s, duration_s). STOP on
           any difference.
  seizures per-seizure table (caught by the E1 rule on the CPD events, p_need, amplitude ratio, duration) and the
           statistics of rule (d).
  alarms   false-alarm table of the 8 test patients (rule (e)); the flagged-share part needs rp4/flags/ (laptop export).
  figs     figure candidates E2-E6 (rule (f)).

Verbatim reuse without importing modules that need torch / mne: the functions named below are read from their source
files with ast and executed unchanged (v9_final_hard.logreg_cluster_boot, mwu; v9_anatomy.pneed_fn).

Run: python src/r2_rp4.py            (gate + every table; the flag part runs only if rp/rp4/flags/ exists)
"""
import ast
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT / "src", ROOT / "src" / "retrain", ROOT / "src" / "phaseB", ROOT / "src" / "phaseC",
          ROOT / "src" / "dataprep"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
import p2_scalars as PS                 # noqa: E402
import p3_levers as P3L                 # noqa: E402
import p3c_freeze as P3C                # noqa: E402
import e18_cpd_localizer as E18         # noqa: E402

RP = ROOT / "results" / "r2" / "r1_system" / "rp"
RP2 = RP / "rp2"
OUT = RP / "rp4"
FLAGS = OUT / "flags"
DESC = ROOT / "results" / "v9_v1" / "part1_descriptors.csv"
INV_CHB = ROOT / "results" / "r2" / "r0_data" / "chb" / "inventory.csv"
INV_EXT = ROOT / "results" / "r2" / "r0_data" / "ext" / "inventory.csv"
TEST = ["chb03", "chb06", "chb13", "chb14", "chb15", "chb16", "chb17", "chb18"]
SIENA = ["PN00", "PN01", "PN03", "PN05", "PN06", "PN07", "PN09", "PN10", "PN11", "PN12", "PN13", "PN14", "PN16", "PN17"]
EXT = ["chb24"] + SIENA
SEEDS = [1, 2, 3, 4]
TAG = {s: f"clean_seed{s}" for s in SEEDS}
ARMS = {"frozen": (0.005, 0.005), "L2f": (0.005, P3C.CAP)}
DEMO_SEED = 3
WIN = PS.WIN
PRE, POST = 30, 60
EDGE_S = 900
FAR_S = 600
B_PAT = 10_000
ERR_ALL = ["det_on", "det_off", "cpd_on", "cpd_off", "hyb_on", "hyb_off"]
ERR_GATED = ["det_on", "det_off", "cpd_on", "cpd_off"]


def _verbatim(path, names):
    """exec the named top-level function definitions of a source file, unchanged, in a namespace with np / pd."""
    tree = ast.parse(Path(path).read_text(encoding="utf-8"))
    ns = dict(np=np, pd=pd)
    from scipy.stats import mannwhitneyu
    from sklearn.linear_model import LogisticRegression
    ns.update(mannwhitneyu=mannwhitneyu, LogisticRegression=LogisticRegression)
    found = []
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name in names:
            exec(compile(ast.Module([node], []), str(path), "exec"), ns)
            found.append(node.name)
        if isinstance(node, ast.Assign) and any(getattr(t, "id", "") in ("RNG_SEED", "N_BOOT") for t in node.targets):
            exec(compile(ast.Module([node], []), str(path), "exec"), ns)
    if sorted(found) != sorted(names):
        raise SystemExit(f"STOP: {set(names) - set(found)} not found in {path}")
    return ns


HARD = _verbatim(ROOT / "src" / "v9_final_hard.py", ["mwu", "logreg_cluster_boot"])
ANAT = _verbatim(ROOT / "src" / "v9_anatomy.py", ["pneed_fn"])
assert HARD["N_BOOT"] == 2000 and HARD["RNG_SEED"] == 42


def log(m):
    print(m, flush=True)


# ============================================================================ context from the scores file
def set_of(case):
    return "test" if case in TEST else "external"


def load_case(case):
    df = pd.read_csv(RP2 / "scores" / f"{case}.csv.gz")
    ok = df.ok.values.astype(bool)
    ict = df.ictal.values.astype(bool)
    fidx = df.file_idx.values.astype(int)
    z = dict(is_signal_loss=~ok, is_ictal=ict, file_idx=fidx)
    ctx = dict(s=case, z=z, n=len(df), ok=ok, ict=ict, fidx=fidx)
    return ctx, df


def file_names(case, ctx):
    inv = pd.read_csv(INV_CHB if case.startswith("chb") and case != "chb24" else INV_EXT)
    if case == "chb24" and "chb24" not in set(inv.case):
        inv = pd.read_csv(INV_CHB)
    r = inv[(inv.case == case) & inv.file.str.endswith(".edf")].copy()
    if "skipped_by_design" in r:
        r = r[r.skipped_by_design.fillna(False).astype(str).str.lower() != "true"]
    r = r.sort_values("file")
    nwin = pd.Series(ctx["fidx"]).value_counts().sort_index()
    names = list(r.file)
    inv_w = [int(w) for w in r.windows_4s]
    got_w = [int(nwin.get(i, 0)) for i in range(len(nwin))]
    if len(names) != len(got_w) or inv_w != got_w:
        # a file with zero windows would not appear in the scores; keep only names with windows, in order
        keep = [(n, w) for n, w in zip(names, inv_w) if w > 0]
        if [w for _, w in keep] != got_w:
            raise SystemExit(f"STOP file map {case}: inventory windows {inv_w} vs scores {got_w}")
        names = [n for n, _ in keep]
    return names


# ============================================================================ R4.0 gate
def gate_and_events():
    t0 = time.time()
    ref = pd.read_csv(RP2 / "per_subject.csv")
    eref = pd.read_csv(RP2 / "errors.csv")
    thr_ref = pd.read_csv(RP2 / "thresholds.csv")
    q = pd.read_csv(RP2 / "q.csv")
    bad, hyb_diff, n_rows, n_pairs, thr_max = [], [], 0, 0, 0.0
    EV, CTX = {}, {}
    for case in TEST + EXT:
        ctx, df = load_case(case)
        ctx["files"] = file_names(case, ctx)
        CTX[case] = (ctx, df)
        sname = set_of(case)
        for s in SEEDS:
            tag = TAG[s]
            x = df[f"x_s{s}"].values.astype(np.float64)
            xs_saved = df[f"xs_s{s}"].values.astype(np.float64)
            qr = float(q[(q.subject == case) & (q.seed == tag)].q_raw.iloc[0])
            sm = PS.smoothed(ctx, x, P3C.SMOOTH)
            fin = np.isfinite(sm)
            if not np.array_equal(fin, np.isfinite(xs_saved)):
                bad.append((case, tag, "xs finiteness"))
            rows, errs = [], []
            for arm, (fl, cp) in ARMS.items():
                P3C.run_budget(ctx, case, tag, x, qr, fl, cp, arm, rows, errs)
                top = P3C.budget(qr, fl, cp)
                thr = float(np.nanquantile(sm, 1 - top))
                tr = float(thr_ref[(thr_ref.subject == case) & (thr_ref.seed == tag) & (thr_ref.budget == arm)].thr.iloc[0])
                thr_max = max(thr_max, abs(thr - tr) / abs(tr))
                if abs(thr - tr) > 1e-6 * abs(tr):
                    bad.append((case, tag, arm, "thr", thr, tr))
                det = PS.d1_events(ctx, x, P3C.SMOOTH, top)
                cpd, _ = P3L.localize(ctx, x, det, thr, "cpd")
                pairs = E18.match_errors(P3L.refs_of(ctx), det)
                _, pr = P3L.localize(ctx, x, det, thr, "cpd")
                EV[(case, s, arm)] = dict(x=x, sm=sm, top=top, thr=thr, det=det, cpd=cpd,
                                          pairs=[(f, ra, rb, h0, h1, *pr[(f, h0, h1)]) for f, ra, rb, h0, h1 in pairs])
            R = pd.DataFrame(rows)
            for _, r in R.iterrows():
                g = ref[(ref.subject == case) & (ref.seed == tag) & (ref.budget == r.budget) & (ref.stage == r.stage)]
                if len(g) != 1:
                    bad.append((case, tag, r.budget, r.stage, "missing ref")); continue
                g = g.iloc[0]
                n_rows += 1
                for c in ("tp", "fp", "n_ref"):
                    if int(r[c]) != int(g[c]):
                        bad.append((case, tag, r.budget, r.stage, c, int(r[c]), int(g[c])))
                for c in ("top", "nonict_h"):
                    if abs(float(r[c]) - float(g[c])) > 1e-9 * max(abs(float(g[c])), 1e-12):
                        bad.append((case, tag, r.budget, r.stage, c, float(r[c]), float(g[c])))
            E = pd.DataFrame(errs)
            for arm in ARMS:
                mine = E[E.budget == arm][ERR_ALL].values if len(E) else np.zeros((0, 6))
                theirs = eref[(eref.subject == case) & (eref.seed == tag) & (eref.budget == arm)][ERR_ALL].values
                n_pairs += len(theirs)
                if mine.shape != theirs.shape:
                    bad.append((case, tag, arm, "error pairs count", mine.shape, theirs.shape)); continue
                for j, c in enumerate(ERR_ALL):
                    d = np.flatnonzero(mine[:, j].astype(np.int64) != theirs[:, j].astype(np.int64))
                    for i in d:
                        item = (case, tag, arm, c, int(i), int(mine[i, j]), int(theirs[i, j]))
                        (bad if c in ERR_GATED else hyb_diff).append(item)
        log(f"  gate {case}: done ({time.time() - t0:.0f} s)")
    gate = dict(rows_compared=n_rows, error_pairs_compared=n_pairs, thr_max_rel=thr_max, differences=len(bad),
                hybrid_boundary_differences=[list(map(str, b)) for b in hyb_diff],
                hybrid_note="hybrid boundaries are reported, not gated (plan §12 12/11 10:05): the hybrid offset takes the "
                            "argmax of the unsmoothed score; two windows equal within float32 storage can swap the peak. "
                            "RP4 reads detector and cpd only; every tp / fp / n_ref (hybrid included) is gated exactly.",
                first_differences=[list(map(str, b)) for b in bad[:30]], elapsed_s=round(time.time() - t0, 1))
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "gate_R4_0.json").write_text(json.dumps(gate, indent=1))
    if bad:
        log(json.dumps(gate, indent=1))
        raise SystemExit("STOP R4.0: rebuilt events differ from rp2 (see rp4/gate_R4_0.json)")
    log(f"R4.0 PASS: {n_rows} rows, {n_pairs} error pairs, thresholds max relative {thr_max:.2e}")
    return EV, CTX


# ============================================================================ per-seizure table
def seizure_table(EV, CTX):
    desc = pd.read_csv(DESC)
    out, unmatched = [], []
    for case in TEST + EXT:
        ctx, df = CTX[case]
        refs = P3L.refs_of(ctx)
        for arm in ARMS:
            for s in SEEDS:
                ev = EV[(case, s, arm)]
                pn = ANAT["pneed_fn"](ev["sm"])
                errmap = {(f, ra, rb): (h0, h1, c0, c1) for f, ra, rb, h0, h1, c0, c1 in ev["pairs"]}
                for f, rr in refs.items():
                    m = np.flatnonzero(ctx["fidx"] == f)
                    for a, b in rr:
                        caught = any(h1 >= a - PRE and h0 <= b + POST for h0, h1 in ev["cpd"].get(f, []))
                        aw, bw = a // WIN, b // WIN
                        seg = ev["sm"][m[max(0, aw - 8):min(len(m), bw + 15)]]
                        p_need = pn(np.nanmax(seg)) if np.isfinite(seg).any() else np.nan
                        e = errmap.get((f, a, b))
                        out.append(dict(set=set_of(case), subject=case, file=ctx["files"][f], file_idx=int(f),
                                        onset_s=int(a), duration_s=int(b - a), arm=arm, seed=s, caught=bool(caught),
                                        p_need=float(p_need), top=ev["top"],
                                        cpd_on_err=(e[2] - a) if e else np.nan, cpd_off_err=(e[3] - b) if e else np.nan))
    S = pd.DataFrame(out)
    key = S[["subject", "file", "onset_s", "duration_s"]].drop_duplicates()
    j = key.merge(desc[["subject", "file", "onset_s", "duration_s", "amp_ratio"]], how="left",
                  on=["subject", "file", "onset_s", "duration_s"])
    if j.amp_ratio.isna().any():
        bad = j[j.amp_ratio.isna()]
        raise SystemExit(f"STOP descriptor join: {len(bad)} seizures unmatched\n{bad.head(20)}")
    S = S.merge(j, on=["subject", "file", "onset_s", "duration_s"], how="left")
    S["set2"] = np.where(S.subject.isin(TEST), "test", np.where(S.subject == "chb24", "chb24", "siena"))
    # consistency: E1-rule caught vs scorer tp (cpd) per subject / seed / arm
    ref = pd.read_csv(RP2 / "per_subject.csv")
    chk = []
    for (case, arm, s), g in S.groupby(["subject", "arm", "seed"]):
        r = ref[(ref.subject == case) & (ref.seed == TAG[s]) & (ref.budget == arm) & (ref.stage == "cpd")].iloc[0]
        chk.append(dict(subject=case, arm=arm, seed=s, runs=len(g), n_ref=int(r.n_ref), caught_e1=int(g.caught.sum()),
                        tp=int(r.tp)))
    C = pd.DataFrame(chk)
    C["same_count"] = C.runs == C.n_ref
    C["equal"] = C.caught_e1 == C.tp
    return S, C


# ============================================================================ statistics
def stats(S):
    rows, lr = [], []
    groups = {"test": ["test"], "chb24+siena": ["chb24", "siena"], "all23": ["test", "chb24", "siena"]}
    for arm in ARMS:
        for gname, sets in groups.items():
            for s in SEEDS:
                d = S[(S.arm == arm) & (S.seed == s) & S.set2.isin(sets)]
                for var in ("amp_ratio", "duration_s"):
                    m = HARD["mwu"](d[d.caught][var], d[~d.caught][var])
                    rows.append(dict(arm=arm, group=gname, seed=s, var=var, **m))
                L = HARD["logreg_cluster_boot"](d)
                lr.append(dict(arm=arm, group=gname, seed=s, n=L["n"], n_caught=int(d.caught.sum()),
                               coef_amp=L["coef_amp"], amp_lo=L["ci_amp"][0], amp_hi=L["ci_amp"][1],
                               coef_dur=L["coef_dur"], dur_lo=L["ci_dur"][0], dur_hi=L["ci_dur"][1],
                               n_boot_ok=L["n_boot_ok"]))
                log(f"  stats {arm} {gname} seed {s}: n {L['n']} caught {int(d.caught.sum())} "
                    f"amp {L['coef_amp']:+.2f} [{L['ci_amp'][0]:+.2f}, {L['ci_amp'][1]:+.2f}] "
                    f"dur {L['coef_dur']:+.2f} [{L['ci_dur'][0]:+.2f}, {L['ci_dur'][1]:+.2f}]")
    return pd.DataFrame(rows), pd.DataFrame(lr)


def seizure_4seed(S):
    g = S.groupby(["arm", "set2", "subject", "file", "onset_s", "duration_s", "amp_ratio"])
    T = g.agg(n_caught=("caught", "sum"), p_need_med=("p_need", "median"), top_med=("top", "median"),
              p_need_over_top=("p_need", lambda v: np.nan)).reset_index()
    over = S.assign(over=S.p_need > S.top).groupby(["arm", "subject", "file", "onset_s"]).over.sum().rename("seeds_p_need_over_top")
    T = T.drop(columns="p_need_over_top").merge(over.reset_index(), on=["arm", "subject", "file", "onset_s"])
    T["class"] = np.where(T.n_caught == 4, "caught_all4", np.where(T.n_caught == 0, "missed_all4", "mixed"))
    summ = T.groupby(["arm", "set2", "class"]).agg(n=("onset_s", "size"), amp_med=("amp_ratio", "median"),
                                                   dur_med=("duration_s", "median"),
                                                   p_need_med=("p_need_med", "median")).reset_index()
    return T, summ


def missed_vs_budget(S):
    """missed seizures (per seed): is the seizure peak ranked below the patient's own budget (p_need > top)?"""
    out = []
    for (arm, set2, s), g in S.groupby(["arm", "set2", "seed"]):
        mi, ca = g[~g.caught], g[g.caught]
        out.append(dict(arm=arm, set=set2, seed=s, n_missed=len(mi), missed_p_need_over_top=int((mi.p_need > mi.top).sum()),
                        n_caught=len(ca), caught_p_need_over_top=int((ca.p_need > ca.top).sum()),
                        missed_p_need_median=float(mi.p_need.median()) if len(mi) else np.nan,
                        missed_ratio_median=float((mi.p_need / mi.top).median()) if len(mi) else np.nan))
    return pd.DataFrame(out)


# ============================================================================ false alarms
def false_alarms(EV, CTX):
    rows = []
    for case in TEST:
        ctx, df = CTX[case]
        refs = P3L.refs_of(ctx)
        for arm in ARMS:
            for s in SEEDS:
                ev = EV[(case, s, arm)]
                x = ev["x"]
                for f, evs in ev["cpd"].items():
                    m = np.flatnonzero(ctx["fidx"] == f)
                    L = len(m)
                    rr = refs.get(f, [])
                    for a_s, b_s in evs:
                        if any(h1 >= a_s - PRE and h0 <= b_s + POST for h0, h1 in rr):
                            continue
                        aw, bw = a_s // WIN, min(b_s // WIN, L)
                        aw = max(0, min(aw, L - 1))
                        g = m[aw:max(bw, aw + 1)]
                        okg = g[ctx["ok"][g]]
                        pk = float(np.nanmax(x[okg])) if len(okg) else np.nan
                        mid = 0.5 * (a_s + b_s)
                        fdur = L * WIN
                        pos = "edge" if (mid < EDGE_S or mid > fdur - EDGE_S) else "middle"
                        dist = min(max(0.0, ra - b_s, a_s - rb) for ra, rb in rr) if rr else np.nan
                        rows.append(dict(subject=case, arm=arm, seed=s, file_idx=int(f), file=ctx["files"][f],
                                         onset_s=int(a_s), offset_s=int(b_s), duration_s=int(b_s - a_s), peak_x=pk,
                                         position=pos, dist_to_seizure_s=dist, file_has_seizure=bool(rr),
                                         w0=int(g[0]), w1=int(g[-1]) + 1))
    F = pd.DataFrame(rows)
    # persistence: number of seeds (incl. this one) with an overlapping false alarm in the same file
    pers = []
    for _, r in F.iterrows():
        o = F[(F.subject == r.subject) & (F.arm == r.arm) & (F.file_idx == r.file_idx) &
              (F.onset_s <= r.offset_s) & (F.offset_s >= r.onset_s)]
        pers.append(int(o.seed.nunique()))
    F["n_seeds"] = pers
    return F


def zone_hours(ctx):
    """valid hours near a file edge (window centre within EDGE_S of the start or end) and in the middle."""
    he = hm = 0.0
    for f in np.unique(ctx["fidx"]):
        m = np.flatnonzero(ctx["fidx"] == f)
        L = len(m)
        c = np.arange(L) * WIN + WIN / 2
        edge = (c < EDGE_S) | (c > L * WIN - EDGE_S)
        okf = ctx["ok"][m]
        he += float((edge & okf).sum()) * WIN / 3600
        hm += float((~edge & okf).sum()) * WIN / 3600
    return he, hm


def boot_mean(v, b=B_PAT, seed=0):
    v = np.asarray(v, float)
    v = v[np.isfinite(v)]
    rng = np.random.default_rng(seed)
    bs = rng.choice(v, size=(b, len(v)), replace=True).mean(axis=1)
    return float(v.mean()), float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5)), len(v)


def alarm_summary(F, CTX):
    Z = {c: zone_hours(CTX[c][0]) for c in TEST}
    per = []
    for (arm, s, case), g in F.groupby(["arm", "seed", "subject"]):
        he, hm = Z[case]
        per.append(dict(arm=arm, seed=s, subject=case, n_fa=len(g), n_edge=int((g.position == "edge").sum()),
                        h_edge=he, h_mid=hm, rate_edge=(g.position == "edge").sum() / he if he else np.nan,
                        rate_mid=(g.position == "middle").sum() / hm if hm else np.nan,
                        dur_med=float(g.duration_s.median()), share_far=float((g.dist_to_seizure_s.fillna(np.inf) > FAR_S).mean()),
                        share_persist3=float((g.n_seeds >= 3).mean())))
    P = pd.DataFrame(per)
    P["edge_minus_mid"] = P.rate_edge - P.rate_mid
    res = []
    for arm in ARMS:
        pp = P[P.arm == arm].groupby("subject")[["rate_edge", "rate_mid", "edge_minus_mid", "share_persist3"]].mean()
        m, lo, hi, n = boot_mean(pp.edge_minus_mid.values)
        res.append(dict(arm=arm, measure="FA/h edge - FA/h middle (per patient, 4-seed mean)", mean=m, lo=lo, hi=hi, n=n,
                        edge_mean=float(pp.rate_edge.mean()), mid_mean=float(pp.rate_mid.mean())))
        tot = P[P.arm == arm]
        res.append(dict(arm=arm, measure="pooled FA/h edge / FA/h middle (all patients, 4 seeds)",
                        mean=float((tot.n_edge.sum() / tot.h_edge.sum()) / ((tot.n_fa - tot.n_edge).sum() / tot.h_mid.sum())),
                        lo=np.nan, hi=np.nan, n=len(pp)))
        res.append(dict(arm=arm, measure="share of FA in edge zones (pooled)", mean=float(tot.n_edge.sum() / tot.n_fa.sum()),
                        lo=np.nan, hi=np.nan, n=len(pp), edge_mean=float(tot.h_edge.sum() / (tot.h_edge.sum() + tot.h_mid.sum()))))
    return P, pd.DataFrame(res)


def flag_part(F, CTX):
    """flagged share of false-alarm windows vs the patient's valid non-seizure windows (rule (e)); needs rp4/flags/."""
    if not FLAGS.exists():
        log("flags: rp/rp4/flags/ absent -> flagged-share part not computed")
        return None, None
    F5, base = {}, []
    for case in TEST:
        fl = pd.read_csv(FLAGS / f"{case}.csv.gz")
        ctx = CTX[case][0]
        if len(fl) != ctx["n"] or not np.array_equal(fl.is_ictal.values.astype(bool), ctx["ict"]) or \
                not np.array_equal(fl.file_idx.values.astype(int), ctx["fidx"]) or \
                not np.array_equal(fl.is_signal_loss.values.astype(bool), ~ctx["ok"]):
            raise SystemExit(f"STOP flags {case}: windows / ictal / file_idx / signal loss differ from the scores file")
        F5[case] = fl.is_flag5sd.values.astype(bool)
        bg = ctx["ok"] & ~ctx["ict"]
        base.append(dict(subject=case, bg_flag_share=float(F5[case][bg].mean()),
                         ictal_flag_share=float(F5[case][ctx["ict"] & ctx["ok"]].mean())))
    B = pd.DataFrame(base)
    Fl = F.copy()
    share = []
    for _, r in Fl.iterrows():
        ok = CTX[r.subject][0]["ok"]
        w = np.arange(r.w0, r.w1)
        w = w[ok[w]]
        share.append(float(F5[r.subject][w].mean()) if len(w) else np.nan)
    Fl["flag_share"] = share
    Fl["high_amp"] = Fl.flag_share >= 0.5
    rows = []
    for arm in ARMS:
        g = Fl[Fl.arm == arm]
        ws = []
        for (case, s), h in g.groupby(["subject", "seed"]):
            ok = CTX[case][0]["ok"]
            w = np.unique(np.concatenate([np.arange(a, b) for a, b in zip(h.w0, h.w1)]))
            w = w[ok[w]]
            ws.append(dict(subject=case, seed=s, fa_win_flag_share=float(F5[case][w].mean()),
                           fa_high_amp_share=float(h.high_amp.mean())))
        W = pd.DataFrame(ws).groupby("subject").mean(numeric_only=True).drop(columns="seed").reset_index().merge(B, on="subject")
        W["diff"] = W.fa_win_flag_share - W.bg_flag_share
        m, lo, hi, n = boot_mean(W["diff"].values)
        rows.append(dict(arm=arm, measure="flag share of FA windows - of valid non-seizure windows (per patient, 4-seed mean)",
                         mean=m, lo=lo, hi=hi, n=n, edge_mean=np.nan, mid_mean=np.nan,
                         fa_mean=float(W.fa_win_flag_share.mean()), bg_mean=float(W.bg_flag_share.mean())))
        rows.append(dict(arm=arm, measure="share of FA events with flag share >= 0.5 (pooled, earlier rule)",
                         mean=float(g.high_amp.mean()), lo=np.nan, hi=np.nan, n=len(g)))
        W.insert(0, "arm", arm)
        W.to_csv(OUT / f"fa_flags_per_patient_{arm}.csv", index=False)
    return Fl, pd.DataFrame(rows)


# ============================================================================ figure candidates
def figure_candidates(S, F, T):
    R = []
    a = S[(S.arm == "L2f") & (S.set2 == "test")]
    g = a.groupby(["subject", "file", "onset_s", "duration_s", "amp_ratio"])
    t = g.agg(n=("caught", "sum"), on_med=("cpd_on_err", lambda v: np.nanmedian(np.abs(v)) if np.isfinite(v).any() else np.nan),
              off_med=("cpd_off_err", lambda v: np.nanmedian(np.abs(v)) if np.isfinite(v).any() else np.nan)).reset_index()
    t = t.sort_values(["subject", "file", "onset_s"])
    c4 = t[t.n == 4].copy()
    if len(c4):
        med = float(c4.on_med.median())
        c4["d"] = (c4.on_med - med).abs()
        r = c4.sort_values(["d", "subject", "file", "onset_s"]).iloc[0]
        R.append(dict(figure="E2", rule="caught by all 4 seeds, 4-seed median |onset error| closest to the median "
                                         f"({med:.0f} s)", subject=r.subject, file=r.file, onset_s=int(r.onset_s),
                      duration_s=int(r.duration_s), value=float(r.on_med)))
    ps = pd.read_csv(RP / "aggregate" / "per_subject_mean.csv")
    ps = ps[(ps.set == "test") & (ps.arm == "L2f") & (ps.stage == "cpd")].sort_values("subject")
    hi = ps.sort_values(["sens", "subject"], ascending=[False, True]).iloc[0]
    lo = ps.sort_values(["sens", "subject"], ascending=[True, True]).iloc[0]
    R.append(dict(figure="E3", rule="highest 4-seed sensitivity (final, cpd)", subject=hi.subject, value=float(hi.sens)))
    R.append(dict(figure="E3", rule="lowest 4-seed sensitivity (final, cpd)", subject=lo.subject, value=float(lo.sens)))
    m0 = t[t.n == 0]
    if len(m0):
        r = m0.sort_values(["amp_ratio", "subject", "file", "onset_s"]).iloc[0]
        R.append(dict(figure="E4", rule="missed by all 4 seeds, lowest amplitude ratio", subject=r.subject, file=r.file,
                      onset_s=int(r.onset_s), duration_s=int(r.duration_s), value=float(r.amp_ratio)))
        r = m0.sort_values(["duration_s", "subject", "file", "onset_s"]).iloc[0]
        R.append(dict(figure="E4", rule="missed by all 4 seeds, shortest", subject=r.subject, file=r.file,
                      onset_s=int(r.onset_s), duration_s=int(r.duration_s), value=float(r.amp_ratio)))
    f = F[(F.arm == "L2f") & (F.seed == DEMO_SEED) & (F.n_seeds >= 3) &
          ((~F.file_has_seizure) | (F.dist_to_seizure_s > FAR_S))]
    if len(f):
        r = f.sort_values(["peak_x", "subject", "file", "onset_s"], ascending=[False, True, True, True]).iloc[0]
        R.append(dict(figure="E5", rule="false alarm > 600 s from any seizure of its file, in >= 3 of 4 seeds, highest peak "
                                         "score of the demo model (seed 3)", subject=r.subject, file=r.file,
                      onset_s=int(r.onset_s), duration_s=int(r.duration_s), value=float(r.peak_x)))
    c3 = t[t.n >= 3]
    if len(c3):
        r = c3.sort_values(["off_med", "subject", "file", "onset_s"], ascending=[False, True, True, True]).iloc[0]
        R.append(dict(figure="E6", rule="caught by >= 3 of 4 seeds, largest median |offset error| (cpd)", subject=r.subject,
                      file=r.file, onset_s=int(r.onset_s), duration_s=int(r.duration_s), value=float(r.off_med)))
    return pd.DataFrame(R)


# ============================================================================ main
def main():
    t0 = time.time()
    EV, CTX = gate_and_events()
    S, C = seizure_table(EV, CTX)
    S.to_csv(OUT / "seizures_per_seed.csv", index=False)
    C.to_csv(OUT / "caught_vs_scorer.csv", index=False)
    bad = C[C.same_count & ~C.equal]
    if len(bad):
        raise SystemExit(f"STOP: E1-rule caught differs from the scorer tp where run count = n_ref:\n{bad}")
    T, summ = seizure_4seed(S)
    T.to_csv(OUT / "seizures_4seed.csv", index=False)
    summ.to_csv(OUT / "seizures_4seed_summary.csv", index=False)
    missed_vs_budget(S).to_csv(OUT / "missed_vs_budget.csv", index=False)
    MW, LR = stats(S)
    MW.to_csv(OUT / "mannwhitney.csv", index=False)
    LR.to_csv(OUT / "logistic.csv", index=False)
    F = false_alarms(EV, CTX)
    P, Az = alarm_summary(F, CTX)
    P.to_csv(OUT / "fa_per_patient.csv", index=False)
    Fl, Fs = flag_part(F, CTX)
    (Fl if Fl is not None else F).drop(columns=["w0", "w1"]).to_csv(OUT / "false_alarms.csv", index=False)
    if Fs is not None:
        Az = pd.concat([Az, Fs], ignore_index=True)
    Az.to_csv(OUT / "fa_summary.csv", index=False)
    figure_candidates(S, F, T).to_csv(OUT / "figure_candidates.csv", index=False)
    meta = dict(script_sha16=__import__("hashlib").sha256(Path(__file__).read_bytes()).hexdigest()[:16],
                flags=FLAGS.exists(), elapsed_s=round(time.time() - t0, 1), numpy=np.__version__, pandas=pd.__version__)
    (OUT / "run_meta.json").write_text(json.dumps(meta, indent=1))
    log(f"done in {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
