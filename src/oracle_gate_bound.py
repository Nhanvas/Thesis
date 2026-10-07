#!/usr/bin/env python
"""
oracle_gate_bound.py -- Part A (oracle upper bound of artifact gating, validation only, event level)
                        Part B (descriptive: seizure visibility vs smoothing length and seizure length)

Save as  F:\\Study\\Thesis\\Code\\src\\oracle_gate_bound.py ; run from the repo root:
    python src/oracle_gate_bound.py
Pre-registration: docs/PREREG_ORACLE_GATE_BOUND.md (commit it BEFORE running).
Reads only the continuous_eval cache (fused scope-T score + masks). No EDF, no model, nothing trained.
Writes only to results/oracle_gate_bound/. Existing files are never modified.

Part A, validation patients only (chb10, chb11, chb22):
  V0  the cached score, unchanged                                          (reference; reproduction gate)
  V1  score of flagged (+-5 SD peak rule) non-ictal windows -> subject background median   [ORACLE]
  V2  as V1, and post-seizure buffer windows -> background median                          [ORACLE]
  Ictal windows are never touched, which is exactly why V1 and V2 are upper bounds: a real gate
  cannot know which flagged windows are ictal. The event grid, the merge gaps, the FA/day denominator
  and the rule 'highest pooled sensitivity with pooled FA/day <= 25' are those of continuous_eval.
Part B, validation and test, DESCRIPTIVE ONLY (nothing is chosen from it):
  for each seizure (contiguous ictal run) and each moving-average length k, the peak of the smoothed
  series inside the seizure is compared with the maxima of equally long spans of non-ictal windows;
  e = share of those spans whose maximum is >= the seizure's peak. Smaller e = more visible.
  'all' uses the cached score; 'oracleV1' uses the V1 series.
"""
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import continuous_eval as CE   # noqa: E402

OUT = ROOT / "results" / "oracle_gate_bound"
VAL = list(CE.VAL_SUBJS)
TEST = ["chb03", "chb06", "chb13", "chb14", "chb15", "chb16", "chb17", "chb18"]
GATE = {(75.0, 5.0, 300): (5, 116), (50.0, 2.0, 90): (11, 448)}   # tp, fp of the cached score (stepA_selected.json)
MAS = [1, 3, 5, 9, 15]


def log(msg):
    print(time.strftime("%H:%M:%S"), msg, flush=True)


def series(variant, s):
    m = CE.load_mask(s)
    sc = np.asarray(CE.load_subject_data("T", s)["score"], dtype=np.float64).copy()
    if variant == "V0":
        return sc, m
    ict, buf, art, sl = m["is_ictal"], m["is_buffer"], m["is_artifact"], m["is_signal_loss"]
    bg = ~(ict | buf | art | sl)
    med = float(np.median(sc[bg]))
    rep = art & ~ict & ~buf
    if variant == "V2":
        rep = rep | (buf & ~ict)
    sc[rep] = med
    return sc, m


def run_grid(variant):
    path = OUT / f"grid_{variant}.csv"
    if path.exists():
        return pd.read_csv(path)
    data = {s: CE.load_subject_data("T", s) for s in VAL}
    grids = {}
    for s in VAL:
        t0 = time.time()
        sc, _ = series(variant, s)
        data[s]["score"] = sc
        grids[s] = CE.grid_for_subject(sc, data[s]["inter_mask"], None, CE.MAG_PCTS, CE.PEN_MULTS, CE.MERGE_GAPS)
        log(f"{variant} {s}: grid {time.time() - t0:.0f}s")
    rows = []
    for i in range(len(grids[VAL[0]])):
        ref = grids[VAL[0]][i]
        cells = [CE.score_one_cell(data[s], grids[s][i]["hyp_events"]) for s in VAL]
        rows.append(dict(variant=variant, mag_pct=ref["mag_pct"], pen_mult=ref["pen_mult"],
                         merge_s=ref["merge_s"], **CE.pool_cells(cells)))
    g = pd.DataFrame(rows)
    g.to_csv(path, index=False)
    return g


def a8(g):
    ok = g[g.fp_per_day <= 25.0]
    if not len(ok):
        return None
    best = ok.sensitivity.max()
    return ok[ok.sensitivity == best].sort_values(["fp_per_day", "pen_mult", "mag_pct", "merge_s"]).iloc[0]


def part_a():
    res = {v: run_grid(v) for v in ("V0", "V1", "V2")}
    # reproduction gate on V0
    for (mg, pn, ms), (tp, fp) in GATE.items():
        r = res["V0"][(res["V0"].mag_pct == mg) & (res["V0"].pen_mult == pn) & (res["V0"].merge_s == ms)].iloc[0]
        if int(r.tp) != tp or int(r.fp) != fp:
            raise SystemExit(f"GATE FAILED at m{mg}/p{pn}/mg{ms}: got TP {int(r.tp)} FP {int(r.fp)}, "
                             f"expected TP {tp} FP {fp}. Do not interpret any variant.")
    log("reproduction gate passed (V0 reproduces both cached cells exactly)")
    base = a8(res["V0"])
    L = ["# Part A -- oracle upper bound of gating, validation only (3 patients, 15 reference events)", "",
         "| variant | A8 matched/15 | A8 sens | A8 FA/day | A8 cell | at 50/2.0/90: TP | FP | FA/day | "
         "min FA/day with TP >= V0's A8 TP |", "|---|---|---|---|---|---|---|---|---|"]
    for v, g in res.items():
        p = a8(g)
        fx = g[(g.mag_pct == 50.0) & (g.pen_mult == 2.0) & (g.merge_s == 90)].iloc[0]
        same = g[g.tp >= int(base.tp)]
        mfa = float(same.fp_per_day.min()) if len(same) else float("nan")
        L.append(f"| {v} | {int(p.tp)} | {p.sensitivity:.3f} | {p.fp_per_day:.1f} | "
                 f"m{p.mag_pct:.0f}/p{p.pen_mult}/mg{int(p.merge_s)} | {int(fx.tp)} | {int(fx.fp)} | "
                 f"{fx.fp_per_day:.1f} | {mfa:.1f} |")
    L += ["", "V1 and V2 keep every ictal window untouched, so they are upper bounds that no gate without "
              "seizure labels can reach. Part of any gain comes from the lower background variance, hence a "
              "lower effective PELT penalty, once 40% of the windows are replaced by a constant."]
    return L


# ---------------- Part B ----------------
def runs(mask):
    d = np.diff(np.concatenate([[0], mask.astype(int), [0]]))
    return list(zip(np.where(d == 1)[0], np.where(d == -1)[0]))


def smooth(x, k):
    return x if k == 1 else pd.Series(x).rolling(k, center=True, min_periods=1).mean().values


def span_max_ref(sm, ok, n):
    mx = pd.Series(sm).rolling(n).max().values
    full = pd.Series(ok.astype(np.int32)).rolling(n).sum().values == n
    return np.sort(mx[full])


def group_of(n):
    return "short (<=4 windows)" if n <= 4 else ("mid (5-14)" if n <= 14 else "long (>=15)")


def part_b():
    rows = []
    for s in VAL + TEST:
        sc0, m = series("V0", s)
        sc1, _ = series("V1", s)
        ok = ~(m["is_ictal"] | m["is_buffer"] | m["is_signal_loss"])
        for k in MAS:
            for tag, sc in (("all", sc0), ("oracleV1", sc1)):
                sm = smooth(sc, k)
                refs = {}
                for a, b in runs(m["is_ictal"]):
                    n = int(b - a)
                    if n not in refs:
                        refs[n] = span_max_ref(sm, ok, n)
                    ref = refs[n]
                    peak = sm[a:b].max()
                    e = 1 - np.searchsorted(ref, peak, side="left") / len(ref) if len(ref) else np.nan
                    rows.append(dict(set="val" if s in VAL else "test", subject=s, k=k, ref=tag,
                                     group=group_of(n), n_win=n, e=e))
        log(f"part B {s} done")
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "partB_per_seizure.csv", index=False)
    L = ["# Part B -- seizure visibility vs smoothing length, by seizure length (DESCRIPTIVE ONLY)", "",
         "e = share of equally long non-ictal spans whose smoothed maximum >= the seizure's peak. Compare k "
         "only within a row group. Nothing is selected from this table.", "",
         "| set | seizure length | reference | k (windows) | seizures | median e | e <= 5% | e <= 2% |",
         "|---|---|---|---|---|---|---|---|"]
    for (st, gr, rf, k), g in df.groupby(["set", "group", "ref", "k"]):
        L.append(f"| {st} | {gr} | {rf} | {k} | {len(g)} | {g.e.median():.3f} | {(g.e <= .05).sum()} | {(g.e <= .02).sum()} |")
    return L


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    L = part_a() + [""] + part_b()
    (OUT / "summary.md").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
