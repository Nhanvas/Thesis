#!/usr/bin/env python
"""
p2_bootstrap.py -- stage P2 pre-freeze check (record 6.5, item 1). 15 non-test subjects, 4 seeds.
Subject-level bootstrap of the difference between the final system and E (the P1-frozen system:
v2 clean, V2_LW = mean of robust-z recon, latent LW and gamma, D1 smoothing 15, top 0.02), each at its
own frozen cell. Descriptive (no gate): it tells how much of the non-test gain could be a few subjects.
Per subject: 4-seed-mean TP, n_ref, FP, non-ictal hours. Pooled sensitivity = sum TP / sum n_ref;
FA/day = sum FP / sum hours * 24; subject-mean sensitivity = mean of per-subject TP / n_ref.
B = 10,000 resamples of the 15 subjects with replacement (seed 0); 95 % percentile intervals of
final - E, for all 15 and without chb12; share of resamples with a positive difference.
Reproduction: E on seeds 42 and 1 must give E8's pooled 0.489 @ 19.78 FA/day within 0.002 / 0.05.
Added 2026-10-07 (record rev L, open item 3): a second reference "E_fine" = E with its D1 cell
re-selected on the E21 fine grid at <= 25 FA/day (4-seed pooled rule), so the comparison is at a
matched FA budget; and --cpd none|plain|overlap scores the final system after the E18 / E18d
localizer, i.e. as it would be frozen.
Run:  python src/p2_bootstrap.py --c-arm e --parts C --cell 5,0.0075   (estimated 5-15 min, not measured)
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

OUT = ROOT / "results" / "p2_bootstrap"
B = 10_000


def final_scalar(ctx, tag, a):
    if a.parts == "family":                    # E17b latent family, if adopted
        import e17b_latent_family as F17
        raw = [PS._full(ctx, F17.member(ctx["D"][tag], ctx["wf"], kk)) for kk in F17.MEMBERS.values()]
        return np.mean([PS.pct(v, ctx["ok"]) for v in raw], axis=0)
    parts = tuple(a.parts.split(","))
    if parts == ("C",):
        return E16.rz(PS.readout(ctx, tag, "C", c_arm=a.c_arm), ctx["ok"])
    return PS.ensemble_scalar(ctx, tag, parts, c_arm=a.c_arm)


def e_scalar(ctx, tag):
    ok = ctx["ok"]
    return np.mean([E16.rz(PS.readout(ctx, tag, k), ok) for k in ("recon", "L", "gamma")], axis=0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--c-arm", default="e", choices=["S9base", "e", "b"])
    ap.add_argument("--parts", default="C")
    ap.add_argument("--cell", default="5,0.0075")
    ap.add_argument("--cpd", default="none", choices=["none", "plain", "overlap"])
    a = ap.parse_args()
    cell = (int(a.cell.split(",")[0]), float(a.cell.split(",")[1]))
    OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    import e1_normal_definition as E1
    import e18_cpd_localizer as E18
    E1.TOPS = [0.05, 0.03, 0.02, 0.015, 0.01, 0.0075, 0.005, 0.002, 0.001]
    E18.OVERLAP = a.cpd == "overlap"
    ctxs, EV, grid = {}, {}, []
    for s in E8.SUBJS:                                   # E on the fine grid -> matched-budget cell
        ctx = PS.subject_context(s); ctxs[s] = ctx
        d = E8.d_for_grid(ctx["z"])
        for tag in PS.TAGS:
            EV[(s, tag)] = e_scalar(ctx, tag)
            for r_ in E1.event_grid(d, EV[(s, tag)]):
                r_.update(subject=s, score=f"{tag}|E", nonict_h=ctx["nh"]); grid.append(r_)
    g = pd.DataFrame(grid); g["kind"] = "E"; g["seed"] = g.score.str.split("|").str[0]
    ef = E16.summarise(g, "E")["cell"]
    efine = (ef[0], ef[1])

    def localize(ctx, x, ev):
        out = {}
        for f, evs in ev.items():
            m = np.flatnonzero(ctx["fidx"] == f)
            new = [E18.cpd_event(x[m], ctx["ok"][m], e0 // PS.WIN, e1 // PS.WIN, 15)[:2] for e0, e1 in evs]
            out[f] = PS.merge([(u * PS.WIN, v * PS.WIN) for u, v in new])
        return out

    rows = []
    for s in E8.SUBJS:
        ctx = ctxs[s]
        for tag in PS.TAGS:
            xf = final_scalar(ctx, tag, a)
            evf = PS.d1_events(ctx, xf, cell[0], cell[1])
            if a.cpd != "none":
                evf = localize(ctx, xf, evf)
            for sysname, ev in (("final", evf), ("E", PS.d1_events(ctx, EV[(s, tag)], 15, 0.02)),
                                ("E_fine", PS.d1_events(ctx, EV[(s, tag)], efine[0], efine[1]))):
                tp, fp, nr, h = PS.score(ctx, ev)
                rows.append(dict(subject=s, seed=tag, system=sysname, tp=tp, fp=fp, n_ref=nr, nonict_h=h))
        print(f"{s}: done ({time.time()-t0:.0f}s)", flush=True)
    D = pd.DataFrame(rows); D.to_csv(OUT / f"per_subject_seed_cpd{a.cpd}.csv", index=False)

    q = D[(D.system == "E") & D.seed.isin(["clean_seed42", "clean_seed1"])].groupby("seed")[["tp", "fp", "n_ref", "nonict_h"]].sum()
    e2 = float((q.tp / q.n_ref).mean()); fa2 = float((q.fp / q.nonict_h * 24).mean())
    if abs(e2 - 0.489) > 0.002 or abs(fa2 - 19.78) > 0.05:
        raise SystemExit(f"STOP: E on seeds 42+1 gives {e2:.3f} @ {fa2:.2f}, E8 0.489 @ 19.78")

    S = D.groupby(["system", "subject"])[["tp", "fp", "n_ref", "nonict_h"]].mean().reset_index()
    F = S[S.system == "final"].set_index("subject")
    subs = np.array(F.index)
    rng = np.random.default_rng(0)
    lines = [f"# Subject-level bootstrap: final ({a.parts}, C = {a.c_arm}, cell {cell}, CPD {a.cpd}) minus references\n",
             f"Reproduction of E8 (seeds 42+1): {e2:.3f} @ {fa2:.2f} OK. 4-seed means; B = {B}. "
             f"E_fine cell (fine grid, <= 25): {ef}.\n"]
    for refname, refcell in (("E", "(15, 0.02)"), ("E_fine", str(efine))):
        E = S[S.system == refname].set_index("subject")
        lines += [f"## final - {refname} {refcell}\n", "```",
                  "set           quantity                 point    95 % interval       share > 0"]
        lines += block(F, E, subs, rng)
        lines += ["```", f"Levels: final pooled {F.tp.sum() / F.n_ref.sum():.3f} @ {F.fp.sum() / F.nonict_h.sum() * 24:.2f} "
                  f"FA/day; {refname} pooled {E.tp.sum() / E.n_ref.sum():.3f} @ {E.fp.sum() / E.nonict_h.sum() * 24:.2f} FA/day\n"]
    lines.append(f"\nElapsed {time.time()-t0:.0f} s.")
    (OUT / f"SUMMARY_{a.parts.replace(',', '+')}_C{a.c_arm}_cpd{a.cpd}.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


def block(F, E, subs, rng):
    def stats(idx):
        f, e = F.loc[idx], E.loc[idx]
        return np.array([f.tp.sum() / f.n_ref.sum() - e.tp.sum() / e.n_ref.sum(),
                         (f.tp / f.n_ref).mean() - (e.tp / e.n_ref).mean(),
                         f.fp.sum() / f.nonict_h.sum() * 24 - e.fp.sum() / e.nonict_h.sum() * 24])

    out = []
    for lab, pool in (("all 15", subs), ("without chb12", subs[subs != "chb12"])):
        pt = stats(pool)
        bs = np.array([stats(rng.choice(pool, len(pool), replace=True)) for _ in range(B)])
        for j, name in enumerate(("pooled sensitivity", "subject-mean sens.", "FA/day")):
            lo, hi = np.percentile(bs[:, j], [2.5, 97.5])
            out.append(f"{lab:13s} {name:22s} {pt[j]:+7.3f}  [{lo:+7.3f}, {hi:+7.3f}]   {(bs[:, j] > 0).mean():.3f}")
    return out


if __name__ == "__main__":
    main()
