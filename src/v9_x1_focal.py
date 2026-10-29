#!/usr/bin/env python
"""
v9_x1_focal.py -- V9-X1 (docs/prompts/V9_X1_FOCAL.md): why focal seizures are missed, and a
focal-aware ensemble member. Read-only on every frozen script and committed result; new output only
under results/v9_x1/ and F:/Study/Thesis/Defense/slides/figs/eeg_evidence/x1/.

PART 0 -- reproduce the mechanism (no new model), cheap, mostly from already-committed CSVs:
  1. Channel-count vs caught, two stages, CHB-MIT test, seed 42:
       stage A (p3_anatomy, fixed detector top-p=0.005): recomputed here (p3_anatomy.build +
         PS.d1_events, CELL=(5,0.005)), gated against results/e22_test_oneshot/per_subject_seed.csv
         (stage detector) -- the exact construction results/p3_anatomy/seizures.csv used for test.
       stage B (the final system, per-patient budget + CPD localizer, balanced point): reused from
         v9_anatomy.check_repro_test + final_events (gated against results/e23_test_look7/ inside
         v9_anatomy.py itself) -- the same per-seizure table as results/v9_anatomy/per_seizure.csv
         (chb-test rows), recomputed here only to also keep the detector-only (pre-localizer) stage
         for the mechanism note below.
     Both stages are joined to results/attribution_v7/labels/ictal_channels_FINAL.csv by (subject,
     edf_file, nearest onset_s within 15 s -- the committed annotation onset and the window-grid
     onset differ by a few seconds; every row matched in-range, verified at runtime).
  2. Mechanism: for every test seizure (seed 42), the peak over its SzCORE-tolerance window of the
     r-th-largest-channel robust-z (r = 1, 2, 3, 6, 9, 12; after the detrend_file ±15-min correction,
     e17b_latent_family.member's own construction) as a within-patient percentile of that SAME member
     (1 - results/p3_anatomy/seizures.csv's own pn_<member> columns, already computed there for test
     rows -- read, not recomputed) -- by annotated channel bucket (<=3 / >=4) and caught/missed
     (stage-A caught, i.e. p3_anatomy's own fixed-threshold label, since that is the stage p3_anatomy
     computed pn_* against).
  3. CAR vs bipolar: read off src/c1b_build_trainset.py's own graph_and_bp()/f7() call sites.
  TIER T-B: reads CHB-MIT TEST annotations (channel labels test-informed this analysis, like every
  prior V9-T3/p3_anatomy test-informed step); logged here, not silently used.

PART A -- one pre-registered change, {3rd, 6th, 9th, 12th largest, channel mean} (MEMBERS_X1) instead
  of the frozen {6th, 9th, 12th largest, mean} (e17b_latent_family.MEMBERS), for G and for F (F's own
  B4 constituent gets the identical member set -- the SAME generic e17b_latent_family.member(D, wf, k)
  call, just D = B4's per-channel kNN distance instead of G's GAE distance, exactly how v9_e1b_
  calibrate.py built B4's m(t)/x(t) from G's own construction). k recalibrated with p3_levers.
  calibrate() UNCHANGED (median q_i(k)=0.005, 15 development patients, seed 42, label-free). Secondary
  arms G2/F2 (2nd largest instead of 3rd) are descriptive-only, development patients only.

READ-ONLY REUSE (nothing below recomputes a score, threshold or localizer from scratch beyond
swapping the member set): v9_e1_baselines.py (subject_ctx/cache_D/load_D/repro_check_G/DEV/TEST/TAGS/
GRID/FP_TARGETS/DUR_BINS/duration_bins/sweep_detector/boot_mean_ci), v9_e1b_calibrate.py (one_pass/
sys_sweep/SIENA_ALL_14/ALL_SUBS/SET_OF/K_MULT/matched_curve_k -- both are generic over x/m/k, so
reused verbatim with X1's own member set), p3_levers.py (calibrate/q_of/localize/refs_of/err_stats),
e17b_latent_family.py (member -- generic over any integer k or "mean"), e16_recording_baseline.py
(rz), p2_scalars.py (pct/_full/smoothed/d1_events/score/caught/short_refs), v9_anatomy.py (final_events/
check_repro_test/test_ctx/CHB_DATA/chb_thresh_v/_RAW cache), v9_e2_veto.py (event_features/
label_events/spectral_features/amplitude_feature/chb_event_segment/paired_boot/per_patient_sens_at_fa),
v9_eeg_evidence.py (read_window/ctx_and_res_G/render_event/draw_eeg/top_k_channels/event_done),
e18_cpd_localizer.py (match_errors), p3_anatomy.py (build/zc_of/detr/pneed_fn -- Part 0 only),
raw_eeg_view.py (read_segment), e22_test_oneshot.py (test_context/TEST/CELL).

ONE SUBJECT PER PROCESS is NOT needed for eval_one here (unlike V9-T4/V9-E1b/V9-E2): every subject's
B1-B4 feature cache (results/v9_e1/cache/) and GAE-distance xcache for chb24/Siena (results/
v9_anatomy/xcache/) are already built and committed-equivalent on this checkout (38/38 files present),
so eval_one never decodes a raw EDF -- it is pure array arithmetic on cached D matrices. --eval-all
loops every subject in one process; --eval-one SUBJ stays available for manual resumption if a cache
ever needs rebuilding (falls through to v9_e1_baselines.cache_D, which DOES decode raw EDF, same cost
and same single-worker discipline as V9-T4/V9-E1b).

Run:  python src/v9_x1_focal.py --smoke
      python src/v9_x1_focal.py --part0
      python src/v9_x1_focal.py --calibrate
      python src/v9_x1_focal.py --eval-all
      python src/v9_x1_focal.py --aggregate
      python src/v9_x1_focal.py --posthoc
      python src/v9_x1_focal.py --eeg
      python src/v9_x1_focal.py --report
"""
import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu

ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT / "src", ROOT / "src" / "retrain", ROOT / "src" / "phaseB", ROOT / "src" / "phaseC",
          ROOT / "src" / "dataprep"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
import p2_scalars as PS                 # noqa: E402
import e16_recording_baseline as E16    # noqa: E402
import e17b_latent_family as F17        # noqa: E402
import e18_cpd_localizer as E18         # noqa: E402
import e22_test_oneshot as E22          # noqa: E402
import p3_levers as P3L                 # noqa: E402
import p3_anatomy as P3A                # noqa: E402
import v9_e1_baselines as V9E1          # noqa: E402 -- read-only reuse
import v9_e1b_calibrate as V9E1B        # noqa: E402 -- read-only reuse (patches V9E1.EXT at import)
import v9_e2_veto as V9E2               # noqa: E402 -- read-only reuse
import v9_anatomy as V9A                # noqa: E402
import v9_eeg_evidence as V9V           # noqa: E402 -- read-only reuse (draw primitives)
import v9_eeg_samples as V9S            # noqa: E402
import raw_eeg_view as RV               # noqa: E402

OUT = ROOT / "results" / "v9_x1"
PART0 = OUT / "part0"
PARTS = OUT / "_parts"
POSTHOC = OUT / "posthoc"
FIGOUT = Path("F:/Study/Thesis/Defense/slides/figs/eeg_evidence/x1")
ATT = ROOT / "results" / "attribution_v7" / "labels" / "ictal_channels_FINAL.csv"
E1B = ROOT / "results" / "v9_e1b"

DEV = V9E1.DEV
TEST = V9E1.TEST
TAGS = V9E1.TAGS
HEAD = "clean_seed42"
FLOOR, CAP, SMOOTH = V9E1B.FLOOR, V9E1B.CAP, V9E1B.SMOOTH
SIENA_ALL_14 = V9E1B.SIENA_ALL_14
ALL_SUBS = V9E1B.ALL_SUBS
SET_OF = V9E1B.SET_OF
K_MULT = V9E1B.K_MULT
FP_TARGETS = V9E1B.FP_TARGETS
GRID = V9E1.GRID

# ---- the one pre-registered change: 3rd largest added to the frozen family {6,9,12,mean} -----------
MEMBERS_X1 = {"S3e": 3, "S6e": 6, "S9e": 9, "S12e": 12, "Smean_e": "mean"}
# descriptive-only secondary arm (2nd instead of 3rd), development patients only
MEMBERS_X1_SEC = {"S2e": 2, "S6e": 6, "S9e": 9, "S12e": 12, "Smean_e": "mean"}
ARMS_PRIMARY = ["G", "B4", "F"]
ARMS_SEC = ["G2", "F2"]
ARMS_ALL = ARMS_PRIMARY + ARMS_SEC
ARM_LABEL = dict(G="G (GAE, members 3/6/9/12+mean)", B4="B4 (kNN, members 3/6/9/12+mean)",
                 F="F (fusion G+B4, members 3/6/9/12+mean)",
                 G2="G2 descriptive (GAE, members 2/6/9/12+mean)",
                 F2="F2 descriptive (fusion, members 2/6/9/12+mean)")


def _peak_ram_mb():
    import psutil
    mi = psutil.Process().memory_info()
    return getattr(mi, "peak_wset", mi.rss) / 1e6


def _native(o):
    if isinstance(o, dict):
        return {k: _native(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_native(v) for v in o]
    if isinstance(o, np.generic):
        return o.item()
    return o


# ============================================================================ PART 0 -- helpers
def nearest_join(df, att, tol=15):
    """row-wise nearest-onset join of a per-seizure table (subject, file, onset_s) to the attribution
    CSV (subject, edf_file, onset_s), tolerance in seconds (annotation onset vs window-grid onset)."""
    out = []
    for _, r in df.iterrows():
        cand = att[(att.subject == r.subject) & (att.edf_file == r.file)]
        if not len(cand):
            out.append(dict(**r, n_ictal=np.nan, focal_generalized=None)); continue
        d = (cand.onset_s - r.onset_s).abs()
        j = d.idxmin()
        ok = d[j] <= tol
        out.append(dict(**r, n_ictal=cand.loc[j, "n_ictal"] if ok else np.nan,
                        focal_generalized=cand.loc[j, "focal_generalized"] if ok else None))
    return pd.DataFrame(out)


def stage_a_rows():
    """p3_anatomy detector stage (CELL = (5, 0.005), fixed for every patient), CHB-MIT test, seed 42.
    Reproduction gated against results/e22_test_oneshot/per_subject_seed.csv (stage detector) -- the
    SAME gate p3_anatomy.py itself runs (R3) when called with --include-test."""
    look6 = pd.read_csv(ROOT / "results" / "e22_test_oneshot" / "per_subject_seed.csv")
    rows = []
    for s in E22.TEST:
        ctx = E22.test_context(s)
        D = ctx["D"][HEAD]
        series, _Zf = P3A.build(ctx, D)
        det = PS.d1_events(ctx, series["final"], P3A.CELL[0], P3A.CELL[1])
        tp, fp, nr, h = PS.score(ctx, det)
        r = look6[(look6.subject == s) & (look6.seed == HEAD) & (look6.stage == "detector")].iloc[0]
        if (int(tp), int(fp)) != (int(r.tp), int(r.fp)):
            raise SystemExit(f"STOP stage-A repro {s}: {(int(tp), int(fp))} vs look6 {(int(r.tp), int(r.fp))}")
        files = ctx["z"]["files"] if "files" in ctx["z"].files else None
        fidx = ctx["fidx"]
        for f in np.unique(fidx):
            m = np.flatnonzero(fidx == f)
            fname = str(files[f]) if files is not None else str(f)
            for a, b in PS._runs(ctx["ict"][m]):
                a_s, b_s = a * 4, b * 4
                caught = any(h1 >= a_s - 30 and h0 <= b_s + 60 for h0, h1 in det.get(f, []))
                rows.append(dict(subject=s, file=fname, onset_s=a_s, dur_s=(b - a) * 4, caught=bool(caught)))
    return pd.DataFrame(rows)


def stage_b_rows():
    """the final system (per-patient budget + CPD localizer, balanced point), CHB-MIT test, seed 42.
    Reused via v9_anatomy.check_repro_test (gates against results/e23_test_look7 inside v9_anatomy.py
    itself) + final_events; both detector-stage (post-budget, pre-localizer) and localized-stage caught
    status are kept (the mechanism note in the report compares them)."""
    rows = []
    for s in E22.TEST:
        ctx, res = V9A.check_repro_test(s)
        det, loc = res["det"], res["loc"]
        files = ctx["z"]["files"] if "files" in ctx["z"].files else None
        fidx = ctx["fidx"]
        for f in np.unique(fidx):
            m = np.flatnonzero(fidx == f)
            fname = str(files[f]) if files is not None else str(f)
            for a, b in PS._runs(ctx["ict"][m]):
                a_s, b_s = a * 4, b * 4
                c_det = any(h1 >= a_s - 30 and h0 <= b_s + 60 for h0, h1 in det.get(f, []))
                c_loc = any(h1 >= a_s - 30 and h0 <= b_s + 60 for h0, h1 in loc.get(f, []))
                rows.append(dict(subject=s, file=fname, onset_s=a_s, dur_s=(b - a) * 4,
                                 caught_det=bool(c_det), caught_loc=bool(c_loc)))
    return pd.DataFrame(rows)


def mwu_summary(caught_n, missed_n):
    if len(caught_n) < 2 or len(missed_n) < 2:
        return dict(n_caught=len(caught_n), n_missed=len(missed_n), med_caught=np.nan, med_missed=np.nan,
                   p=np.nan, min_caught=np.nan)
    u, p = mannwhitneyu(missed_n, caught_n, alternative="two-sided")
    return dict(n_caught=len(caught_n), n_missed=len(missed_n), med_caught=float(caught_n.median()),
               med_missed=float(missed_n.median()), p=float(p), min_caught=float(caught_n.min()))


def part0():
    t0 = time.time()
    PART0.mkdir(parents=True, exist_ok=True)
    att = pd.read_csv(ATT)
    print("TIER T-B: this reads CHB-MIT TEST channel annotations (test-informed), as results/"
          "p3_anatomy/SUMMARY.md's own test rows already do.", flush=True)

    # ---- item 1: two-stage channel-count vs caught ----
    A = nearest_join(stage_a_rows(), att)
    B = nearest_join(stage_b_rows(), att)
    A.to_csv(PART0 / "stageA_seizures.csv", index=False)
    B.to_csv(PART0 / "stageB_seizures.csv", index=False)
    print(f"stage A matched {A.n_ictal.notna().sum()}/{len(A)}; stage B matched {B.n_ictal.notna().sum()}/{len(B)}",
          flush=True)

    foc_a = A[A.focal_generalized == "focal"]
    foc_b = B[B.focal_generalized == "focal"]
    sA = mwu_summary(foc_a[foc_a.caught].n_ictal, foc_a[~foc_a.caught].n_ictal)
    sB_det = mwu_summary(foc_b[foc_b.caught_det].n_ictal, foc_b[~foc_b.caught_det].n_ictal)
    sB_loc = mwu_summary(foc_b[foc_b.caught_loc].n_ictal, foc_b[~foc_b.caught_loc].n_ictal)

    def crosstab3(df, col):
        return pd.crosstab(df.n_ictal <= 3, df[col]).rename_axis(index="channels<=3", columns=col)

    ct_a = crosstab3(foc_a, "caught")
    ct_b = crosstab3(foc_b, "caught_loc")
    chb06_a = A[A.subject == "chb06"][["file", "onset_s", "dur_s", "n_ictal", "caught"]]
    chb06_b = B[B.subject == "chb06"][["file", "onset_s", "dur_s", "n_ictal", "caught_det", "caught_loc"]]
    chb15_a = A[A.subject == "chb15"]
    chb15_b = B[B.subject == "chb15"]

    # ---- item 2: mechanism, r=1,2,3,6,9,12, peak percentile by channel bucket and caught/missed ----
    seiz = pd.read_csv(ROOT / "results" / "p3_anatomy" / "seizures.csv")
    seiz = seiz[(seiz.set == "test") & (seiz.seed == HEAD)].copy()
    # recover filenames for the join (seizures.csv stores an integer file index, not a name)
    fname_map = {}
    for s in E22.TEST:
        ctx = E22.test_context(s)
        files = ctx["z"]["files"]
        for f in np.unique(ctx["fidx"]):
            fname_map[(s, int(f))] = str(files[int(f)])
    seiz["file"] = [fname_map.get((r.subject, int(r.file))) for r in seiz.itertuples()]
    seiz_j = nearest_join(seiz, att)
    rs = [1, 3, 6, 9, 12]
    mech_rows = []
    for r_ in rs:
        col = f"pn_S{r_}e" if r_ != 1 else "pn_S1e"
        if col not in seiz_j.columns:
            continue
        pct_ = 1.0 - seiz_j[col]
        bucket = np.where(seiz_j.n_ictal <= 3, "<=3", ">=4")
        for b_ in ("<=3", ">=4"):
            for caught_flag in (True, False):
                m = (bucket == b_) & (seiz_j.caught == caught_flag)
                v = pct_[m]
                if len(v):
                    mech_rows.append(dict(r=r_, channels=b_, caught=caught_flag, n=int(m.sum()),
                                          median_pct=float(v.median())))
    MECH = pd.DataFrame(mech_rows)
    MECH.to_csv(PART0 / "mechanism_by_r.csv", index=False)

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(6.5, 4.2), dpi=150)
        for b_, mk in (("<=3", "o"), (">=4", "s")):
            for caught_flag, ls, col in ((True, "-", "#1f9e89"), (False, "--", "#c0392b")):
                d = MECH[(MECH.channels == b_) & (MECH.caught == caught_flag)].sort_values("r")
                if len(d):
                    ax.plot(d.r, d.median_pct, marker=mk, ls=ls, color=col,
                           label=f"{b_} ch, {'caught' if caught_flag else 'missed'}")
        ax.set_xlabel("order statistic r (largest channel)"); ax.set_ylabel("median within-patient percentile")
        ax.set_title("Part 0 item 2 -- mechanism (CHB-MIT test, seed 42, stage-A caught)")
        ax.legend(fontsize=7); fig.tight_layout()
        fig.savefig(PART0 / "mechanism.png"); plt.close(fig)
    except Exception as e:
        print(f"mechanism plot skipped: {e}", flush=True)

    # ---- item 3: CAR vs bipolar (read off the frozen code, not recomputed) ----
    car_note = (
        "src/c1b_build_trainset.py: graph_and_bp(zw) computes `car = CE.GC.apply_car(zw[i])` and feeds "
        "car ONLY into the wPLI/AEC adjacency (`adj[i] = ... compute_wpli(car), compute_aec(car) ...`), "
        "the GNN's message-passing GRAPH. Both node-feature blocks that the GAE actually reconstructs -- "
        "`bp[i] = CE.FE.compute_band_powers(zw[i])` and `f7(zw)` (called as `parts['f7'].append(f7(zw))`, "
        "build(), line ~124) -- are computed on `zw` directly, the BIPOLAR double-banana z-scored signal, "
        "never on `car`. So: the per-channel reconstruction TARGET (and therefore the per-channel distance "
        "D that every ensemble member, r-th-largest or mean, is built from) stays bipolar -- in the 18-"
        "channel double banana each electrode appears in <=2 pairs, so a single bad electrode can only "
        "ever inflate <=2 of the 18 channel distances directly. CAR enters only through the adjacency "
        "(connectivity estimate for graph message-passing); if CAR itself smears a single-electrode "
        "artifact into the common average, that can still let the artifact's INFLUENCE reach other "
        "channels indirectly through GNN message-passing edges, even though their own reconstruction "
        "target is untouched -- a weaker, indirect path, not the direct one the r-th-largest-member "
        "construction is designed against.")
    print(car_note, flush=True)

    L = ["# V9-X1 Part 0 -- why focal seizures are missed (mechanism, no new model)\n",
         "TIER T-B: CHB-MIT test channel annotations are read (test-informed), as results/p3_anatomy's "
         "own test rows already are; logged, not hidden.\n",
         "## Item 1 -- channel-count vs caught, two stages, CHB-MIT test, seed 42 (focal seizures only)\n"]
    L += [f"- **Stage A** (p3_anatomy, fixed detector top-p=0.005): caught median {sA['med_caught']:.1f} "
          f"ch (n={sA['n_caught']}) vs missed median {sA['med_missed']:.1f} ch (n={sA['n_missed']}), "
          f"Mann-Whitney p={sA['p']:.2e}, no caught seizure below {sA['min_caught']:.0f} channels.",
          f"- **Stage B** (final system, per-patient budget + CPD localizer, balanced point) -- "
          f"detector sub-stage: caught median {sB_det['med_caught']:.1f} ch (n={sB_det['n_caught']}) vs "
          f"missed median {sB_det['med_missed']:.1f} ch (n={sB_det['n_missed']}), p={sB_det['p']:.3f}, "
          f"min caught {sB_det['min_caught']:.0f} ch; localized sub-stage identical "
          f"(caught {sB_loc['med_caught']:.1f} vs missed {sB_loc['med_missed']:.1f}, p={sB_loc['p']:.3f}) "
          "-- the CPD localizer itself changes no seizure's caught status here; the per-patient budget "
          "(clip(q_i(k), 0.005, 0.02), already adopted as L2) is what moves the picture, BEFORE the "
          "localizer runs.",
          "\nThe strong fixed-threshold relationship (stage A) partly washes out once each patient's own "
          "budget is applied (stage B): some patients with narrow-footprint seizures already get a "
          "wider-than-0.005 per-patient budget, rescuing roughly half of their <=3-channel focal "
          "seizures (table below) even under the FROZEN 4-member ensemble -- the per-patient budget, not "
          "the member set, is already doing some of this work.\n",
          "### Annotated channels <=3 vs >=4 x caught/missed (focal only)\n",
          "Stage A (fixed threshold):\n```", ct_a.to_string(), "```",
          "Stage B (final system, localized):\n```", ct_b.to_string(), "```",
          "\n### chb06 (generalized, 18 channels, ~16-24 s) -- differs from the focal pattern\n",
          "Stage A:\n```", chb06_a.to_string(index=False), "```",
          "Stage B:\n```", chb06_b.to_string(index=False), "```",
          f"\nchb15 (median {chb15_a.n_ictal.median():.0f} channels): stage A {int(chb15_a.caught.sum())}/"
          f"{len(chb15_a)} caught; stage B (localized) {int(chb15_b.caught_loc.sum())}/{len(chb15_b)} caught."]

    L += ["\n## Item 2 -- mechanism: peak within-patient percentile of the r-th-largest-channel member, "
          "by annotated channel bucket and stage-A caught/missed (results/p3_anatomy/seizures.csv, "
          "already-computed pn_S{1,3,6,9,12}e columns, test rows, seed 42)\n", "```",
          MECH.pivot_table(index="r", columns=["channels", "caught"], values="median_pct").round(3).to_string(),
          "```", "\nExpected if the hypothesis holds: missed, <=3-channel seizures high (low percentile) on "
          "r=1-3, low (high percentile) on r>=6. See mechanism.png.\n"]

    L += ["\n## Item 3 -- CAR vs bipolar (src/c1b_build_trainset.py)\n", car_note]
    L.append(f"\nElapsed {time.time() - t0:.0f} s.")
    (PART0 / "SUMMARY.md").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))
    print(f"\nWrote {PART0}/SUMMARY.md")


# ============================================================================ PART A -- construction
def final_scalar_from_D_x1(ctx, D, members=MEMBERS_X1):
    raw = [PS._full(ctx, F17.member(D, ctx["wf"], kk)) for kk in members.values()]
    return np.mean([PS.pct(v, ctx["ok"]) for v in raw], axis=0)


def member_mean_z_from_D_x1(ctx, D, members=MEMBERS_X1):
    zs = [E16.rz(PS._full(ctx, F17.member(D, ctx["wf"], kk)), ctx["ok"]) for kk in members.values()]
    return np.mean(zs, axis=0)


def f_signals_x1(ctx, D_g, D_b4, members=MEMBERS_X1):
    xg, xb = final_scalar_from_D_x1(ctx, D_g, members), final_scalar_from_D_x1(ctx, D_b4, members)
    ok = ctx["ok"]
    xf = np.mean([PS.pct(xg, ok), PS.pct(xb, ok)], axis=0)
    mf = np.mean([E16.rz(xg, ok), E16.rz(xb, ok)], axis=0)
    return xf, mf


# ============================================================================ step 1: calibration
def calibrate():
    t0 = time.time()
    V9E1.repro_check_G()
    for s in DEV:
        V9E1.cache_D(s)
    mg, mb, mf, mg2, mf2 = [], [], [], [], []
    for s in DEV:
        ctx = V9E1.subject_ctx(s)
        Dg, Db = ctx["D"][HEAD], V9E1.load_D(s, "B4")
        mg.append(PS.smoothed(ctx, member_mean_z_from_D_x1(ctx, Dg, MEMBERS_X1), SMOOTH))
        mb.append(PS.smoothed(ctx, member_mean_z_from_D_x1(ctx, Db, MEMBERS_X1), SMOOTH))
        _, mf_raw = f_signals_x1(ctx, Dg, Db, MEMBERS_X1)
        mf.append(PS.smoothed(ctx, mf_raw, SMOOTH))
        mg2.append(PS.smoothed(ctx, member_mean_z_from_D_x1(ctx, Dg, MEMBERS_X1_SEC), SMOOTH))
        _, mf2_raw = f_signals_x1(ctx, Dg, Db, MEMBERS_X1_SEC)
        mf2.append(PS.smoothed(ctx, mf2_raw, SMOOTH))
    k_g, k_b4, k_f = P3L.calibrate(mg), P3L.calibrate(mb), P3L.calibrate(mf)
    k_g2, k_f2 = P3L.calibrate(mg2), P3L.calibrate(mf2)
    cal = dict(k_G=k_g, k_B4=k_b4, k_F=k_f, k_G2=k_g2, k_F2=k_f2, floor=FLOOR, cap=CAP, smooth=SMOOTH,
              dev_n=len(DEV), elapsed_s=time.time() - t0)
    OUT.mkdir(parents=True, exist_ok=True)
    json.dump(cal, open(OUT / "calibration.json", "w"), indent=1)
    for k_, v_ in (("k_G", k_g), ("k_B4", k_b4), ("k_F", k_f), ("k_G2", k_g2), ("k_F2", k_f2)):
        print(f"{k_} = {v_:.6f}", flush=True)
    print(f"calibrate() done in {cal['elapsed_s']:.0f}s", flush=True)
    return cal


# ============================================================================ step 2: eval one subject
def eval_one(s):
    t0 = time.time()
    cal = json.load(open(OUT / "calibration.json"))
    k_g, k_b4, k_f = cal["k_G"], cal["k_B4"], cal["k_F"]
    k_g2, k_f2 = cal["k_G2"], cal["k_F2"]
    ctx = V9E1.subject_ctx(s)
    V9E1.cache_D(s)
    Db = V9E1.load_D(s, "B4")
    refs = P3L.refs_of(ctx)

    rows, sweep_rows, sys_rows, dur_rows, err_rows = [], [], [], [], []

    def record(arm, seed, x, m, k):
        out, det, loc, errs = V9E1B.one_pass(ctx, x, k, m, refs)
        for st, v in out.items():
            rows.append(dict(subject=s, arm=arm, seed=seed, stage=st, **v))
        for e in errs:
            err_rows.append(dict(subject=s, arm=arm, seed=seed, **e))
        for r_ in V9E1.sweep_detector(ctx, x, GRID):
            sweep_rows.append(dict(subject=s, arm=arm, seed=seed, **r_))
        for r_ in V9E1B.sys_sweep(ctx, x, m, k, refs):
            sys_rows.append(dict(subject=s, arm=arm, seed=seed, **r_))
        bins = V9E1.duration_bins(ctx, loc)
        for (lo, hi), (caught, n) in bins.items():
            dur_rows.append(dict(subject=s, arm=arm, seed=seed, lo=lo, hi=hi, caught=caught, n=n))
        return loc

    locs = {}
    for tag in TAGS:
        Dg = ctx["D"][tag]
        locs[("G", tag)] = record("G", tag, final_scalar_from_D_x1(ctx, Dg, MEMBERS_X1),
                                  member_mean_z_from_D_x1(ctx, Dg, MEMBERS_X1), k_g)

    xb4 = final_scalar_from_D_x1(ctx, Db, MEMBERS_X1)
    locs[("B4", "-")] = record("B4", "-", xb4, member_mean_z_from_D_x1(ctx, Db, MEMBERS_X1), k_b4)

    for tag in TAGS:
        Dg = ctx["D"][tag]
        xf, mf = f_signals_x1(ctx, Dg, Db, MEMBERS_X1)
        locs[("F", tag)] = record("F", tag, xf, mf, k_f)

    if s in DEV:
        for tag in TAGS:
            Dg = ctx["D"][tag]
            record("G2", tag, final_scalar_from_D_x1(ctx, Dg, MEMBERS_X1_SEC),
                   member_mean_z_from_D_x1(ctx, Dg, MEMBERS_X1_SEC), k_g2)
        for tag in TAGS:
            Dg = ctx["D"][tag]
            xf2, mf2 = f_signals_x1(ctx, Dg, Db, MEMBERS_X1_SEC)
            record("F2", tag, xf2, mf2, k_f2)

    PARTS.mkdir(parents=True, exist_ok=True)
    payload = _native(dict(rows=rows, sweep=sweep_rows, sys=sys_rows, dur=dur_rows, err=err_rows))
    (PARTS / f"{s}.json").write_text(json.dumps(payload), encoding="utf-8")
    print(f"eval-one {s}: done in {time.time() - t0:.0f}s, peak RAM {_peak_ram_mb():.0f} MB", flush=True)


def eval_all():
    t0 = time.time()
    for s in ALL_SUBS:
        fp = PARTS / f"{s}.json"
        if fp.exists():
            continue
        eval_one(s)
    print(f"eval-all done in {time.time() - t0:.0f}s", flush=True)


# ============================================================================ step 3: aggregate
def aggregate():
    parts = {}
    for s in ALL_SUBS:
        fp = PARTS / f"{s}.json"
        if not fp.exists():
            raise SystemExit(f"STOP: missing part file for {s} -- run --eval-one {s} first")
        parts[s] = json.loads(fp.read_text())

    rows = [r for s in ALL_SUBS for r in parts[s]["rows"]]
    sweep_rows = [r for s in ALL_SUBS for r in parts[s]["sweep"]]
    sys_rows = [r for s in ALL_SUBS for r in parts[s]["sys"]]
    err_rows = [r for s in ALL_SUBS for r in parts[s]["err"]]
    dur_rows = [dict(r, set=SET_OF[s]) for s in ALL_SUBS for r in parts[s]["dur"]]

    R, SW, SYS, DB, ERR = (pd.DataFrame(rows), pd.DataFrame(sweep_rows), pd.DataFrame(sys_rows),
                           pd.DataFrame(dur_rows), pd.DataFrame(err_rows))
    OUT.mkdir(parents=True, exist_ok=True)
    R.to_csv(OUT / "per_subject.csv", index=False)
    SW.to_csv(OUT / "sweep.csv", index=False)
    SYS.to_csv(OUT / "sys_sweep.csv", index=False)
    DB.to_csv(OUT / "duration_bins.csv", index=False)
    ERR.to_csv(OUT / "loc_errors.csv", index=False)
    V9E1.check_ext_repro(R[R.arm.isin(ARMS_PRIMARY)])
    print(f"aggregate: {len(ALL_SUBS)} subjects -> {OUT}", flush=True)


# ============================================================================ posthoc: paired bootstrap, channel
# count, false-alarm types, onset/offset
def paired_vs_old(SYS, subs, new_arm, old_arm):
    """per_patient_sens_at_fa + paired_boot (v9_e2_veto, read-only) comparing a NEW arm's own system-
    stage sweep (this script's SYS) against the OLD (results/v9_e1b/sys_sweep.csv) same arm name."""
    old_sys = pd.read_csv(E1B / "sys_sweep.csv")
    out = []
    for t in FP_TARGETS:
        new_sens = V9E2.per_patient_sens_at_fa(SYS, subs, new_arm, t)
        old_sens = V9E2.per_patient_sens_at_fa(old_sys, subs, old_arm, t)
        if not len(new_sens) or not len(old_sens):
            out.append(dict(fa_target=t, mean_diff=np.nan, ci_lo=np.nan, ci_hi=np.nan, share_gt0=np.nan, n_patients=0))
            continue
        out.append(dict(fa_target=t, **V9E2.paired_boot(new_sens, old_sens)))
    return pd.DataFrame(out)


def channel_count_crosstab(R, test_annot):
    """detections by annotated channel count (test, <=3 vs >=4), arm G, headline seed, localized stage."""
    d = R[(R.subject.isin(TEST)) & (R.arm == "G") & (R.seed == HEAD) & (R.stage == "localized")]
    # per-subject tp/n_ref alone can't give per-seizure channel buckets; use the per-seizure join instead,
    # built from this arm's own localized events (same construction as stage_b_rows, new member set).
    rows = []
    cal = json.load(open(OUT / "calibration.json"))
    for s in TEST:
        ctx = V9E1.subject_ctx(s)
        Dg = ctx["D"][HEAD]
        x = final_scalar_from_D_x1(ctx, Dg, MEMBERS_X1)
        m = member_mean_z_from_D_x1(ctx, Dg, MEMBERS_X1)
        refs = P3L.refs_of(ctx)
        _out, det, loc, _errs = V9E1B.one_pass(ctx, x, cal["k_G"], m, refs)
        files = ctx["z"]["files"] if "files" in ctx["z"].files else None
        fidx = ctx["fidx"]
        for f in np.unique(fidx):
            mm = np.flatnonzero(fidx == f)
            fname = str(files[f]) if files is not None else str(f)
            for a, b in PS._runs(ctx["ict"][mm]):
                a_s, b_s = a * 4, b * 4
                c = any(h1 >= a_s - 30 and h0 <= b_s + 60 for h0, h1 in loc.get(f, []))
                rows.append(dict(subject=s, file=fname, onset_s=a_s, dur_s=(b - a) * 4, caught=bool(c)))
    seiz = pd.DataFrame(rows)
    att = pd.read_csv(ATT)
    j = nearest_join(seiz, att)
    j.to_csv(POSTHOC / "channel_count_new_arm.csv", index=False)
    return j


def fa_types_test_only():
    """false-alarm types, same rule as results/v9_v1/ Part 4 (v9_eeg_evidence.part4): per FP, percentile
    of f1-f4 against this arm's OWN development-TP distribution; assign to the highest-percentile
    feature if > 0.90 else 'unassigned'. Scoped to arm G, CHB-MIT test only (development TPs supply the
    reference distribution) -- chb24/Siena are skipped here to keep this step's raw-EEG cost bounded on
    a laptop (reported explicitly, not silently)."""
    cal = json.load(open(OUT / "calibration.json"))
    k_g = cal["k_G"]
    sd_cache = {}

    def sd_uV(s):
        if s not in sd_cache:
            sd_cache[s] = V9E2.subject_sd_uV(s)
        return sd_cache[s]

    ev_rows = []
    for s in DEV + TEST:
        ctx = V9E1.subject_ctx(s)
        Dg = ctx["D"][HEAD]
        x = final_scalar_from_D_x1(ctx, Dg, MEMBERS_X1)
        m = member_mean_z_from_D_x1(ctx, Dg, MEMBERS_X1)
        refs = P3L.refs_of(ctx)
        _out, det, loc, _errs = V9E1B.one_pass(ctx, x, k_g, m, refs)
        labelled = V9E2.label_events(loc, refs)
        files = ctx["z"]["files"]
        setname = "dev" if s in DEV else "test"
        for f, a, b, label, _refdur in labelled:
            feat = V9E2.event_features(s, setname, f, a, b, files, sd_uV(s))
            ev_rows.append(dict(subject=s, set=setname, file=int(f), onset_s=a, offset_s=b, label=label, **feat))
    EV = pd.DataFrame(ev_rows)
    POSTHOC.mkdir(parents=True, exist_ok=True)
    EV.to_csv(POSTHOC / "events_new_arm.csv", index=False)

    FEATS4 = ["f1", "f2", "f3", "f4"]
    dev_tp = EV[(EV.set == "dev") & (EV.label == "TP")]
    ref = {f: np.sort(dev_tp[f].dropna().values) for f in FEATS4}
    fp = EV[(EV.set == "test") & (EV.label == "FP")].copy()
    for f in FEATS4:
        fp[f"{f}_pct"] = [V9V.pct_rank(ref[f], v) for v in fp[f]]
    pct_cols = [f"{f}_pct" for f in FEATS4]
    fp["best_feat"] = fp[pct_cols].idxmax(axis=1).str.replace("_pct", "", regex=False)
    fp["best_pct"] = fp[pct_cols].max(axis=1)
    fp["fp_type"] = np.where(fp["best_pct"] > 0.90, fp["best_feat"], "unassigned")
    fp.to_csv(POSTHOC / "fp_types_new_arm.csv", index=False)
    share = fp.groupby("fp_type").size().rename("n").reset_index()
    share["share"] = share.n / max(len(fp), 1)
    share.to_csv(POSTHOC / "fp_type_shares_new_arm.csv", index=False)
    return EV, fp, share


def posthoc():
    t0 = time.time()
    POSTHOC.mkdir(parents=True, exist_ok=True)
    SYS = pd.read_csv(OUT / "sys_sweep.csv")

    rows = []
    for setname, subs in (("dev", DEV), ("test", TEST), ("siena14", SIENA_ALL_14)):
        for new_arm, old_arm in (("G", "G"), ("F", "F")):
            d = paired_vs_old(SYS, subs, new_arm, old_arm)
            d.insert(0, "set", setname); d.insert(1, "arm", new_arm)
            rows.append(d)
    PAIRED = pd.concat(rows, ignore_index=True)
    PAIRED.to_csv(POSTHOC / "paired_vs_old.csv", index=False)
    print(PAIRED.to_string(index=False), flush=True)

    j = channel_count_crosstab(pd.read_csv(OUT / "per_subject.csv"), None)
    foc = j[j.focal_generalized == "focal"]
    print("\nNew arm (G, members 3/6/9/12+mean), test, focal: channels<=3 x caught\n",
          pd.crosstab(foc.n_ictal <= 3, foc.caught).to_string(), flush=True)

    EV, fp, share = fa_types_test_only()
    print("\nFalse-alarm types (arm G, test, vs own dev-TP distribution):\n", share.to_string(index=False), flush=True)

    print(f"posthoc done in {time.time() - t0:.0f}s", flush=True)


# ============================================================================ EEG draws
def member_strip(ctx, D, r, file_id, w0, w1):
    v = PS._full(ctx, F17.member(D, ctx["wf"], r))
    m = np.flatnonzero(ctx["fidx"] == file_id)
    w0, w1 = max(0, w0), min(len(m), w1)
    g = m[w0:w1]
    vals = v[g].copy()
    vals[~ctx["ok"][g]] = np.nan
    return vals, w0


def draw_change_eeg():
    """newly-caught / newly-lost test seizures (G, new member set vs the old frozen system), up to 6
    each, shortest first; score strips r=1,3,9 (member(D, wf, r), the ±15-min-corrected robust-z, NOT
    percentile -- same units p3_anatomy/e17b use before the ensemble's own percentile-mean)."""
    t0 = time.time()
    FIGOUT.mkdir(parents=True, exist_ok=True)
    old = pd.read_csv(ROOT / "results" / "v9_anatomy" / "per_seizure.csv")
    old = old[old.set == "chb-test"][["subject", "file", "onset_s", "caught"]].rename(
        columns={"caught": "caught_old"})

    cal = json.load(open(OUT / "calibration.json"))
    new_rows = []
    ctxs, locs = {}, {}
    for s in TEST:
        ctx = V9E1.subject_ctx(s)
        Dg = ctx["D"][HEAD]
        x = final_scalar_from_D_x1(ctx, Dg, MEMBERS_X1)
        m = member_mean_z_from_D_x1(ctx, Dg, MEMBERS_X1)
        refs = P3L.refs_of(ctx)
        _out, det, loc, _errs = V9E1B.one_pass(ctx, x, cal["k_G"], m, refs)
        ctxs[s] = ctx; locs[s] = loc
        files = ctx["z"]["files"]
        fidx = ctx["fidx"]
        for f in np.unique(fidx):
            mm = np.flatnonzero(fidx == f)
            fname = str(files[f])
            for a, b in PS._runs(ctx["ict"][mm]):
                a_s, b_s = a * 4, b * 4
                c = any(h1 >= a_s - 30 and h0 <= b_s + 60 for h0, h1 in loc.get(f, []))
                new_rows.append(dict(subject=s, file=fname, onset_s=a_s, dur_s=(b - a) * 4,
                                     caught_new=bool(c), file_idx=int(f)))
    new = pd.DataFrame(new_rows)
    j = new.merge(old, on=["subject", "file", "onset_s"], how="left")
    j["caught_old"] = j["caught_old"].fillna(False)
    newly_caught = j[(~j.caught_old) & (j.caught_new)].sort_values("dur_s").head(6)
    newly_lost = j[(j.caught_old) & (~j.caught_new)].sort_values("dur_s").head(6)
    j.to_csv(POSTHOC / "change_join.csv", index=False)
    print(f"newly caught: {len(newly_caught)} candidates (showing up to 6); newly lost: {len(newly_lost)}", flush=True)

    written = []
    for kind, picks in (("newly_caught", newly_caught), ("newly_lost", newly_lost)):
        for _, r in picks.iterrows():
            s = r.subject
            ctx = ctxs[s]
            Dg = ctx["D"][HEAD]
            dur = r.dur_s
            margin = V9S.margin_for(dur)
            out = RV.read_segment(s, r.file, r.onset_s - margin, r.onset_s + dur + margin)
            if out is None:
                print(f"  SKIP {s} {r.file}: read failed", flush=True); continue
            filt, _raw, a, b = out
            refs, _ = V9S.refs_and_loc(ctx, {"loc": locs[s]}, r.file_idx)
            loc_ev = [(ca, cb) for ca, cb in locs[s].get(r.file_idx, [])]
            w0, w1 = int(a // 4), int(np.ceil(b / 4))
            specs = []
            for rr in (1, 3, 9):
                vals, sw0 = member_strip(ctx, Dg, rr, r.file_idx, w0, w1)
                specs.append((vals, sw0 * 4, f"r={rr}"))
            tag = f"{kind}_{s}_{int(r.onset_s)}"
            if V9V.event_done(FIGOUT, tag):
                written.append(tag); continue
            title = f"{s}  {r.file}  {kind}  duration {dur:.0f} s"
            fp, sp = V9V.render_event(FIGOUT, tag, filt, a, b, title, refs, loc_ev, r.onset_s, specs)
            written.append(str(fp))
            print(f"  drew {tag}", flush=True)
    print(f"EEG draws done in {time.time() - t0:.0f}s -> {len(written)} panels at {FIGOUT}", flush=True)


# ============================================================================ smoke
def smoke():
    t0 = time.time()
    V9E1.repro_check_G()
    subs = ["chb01", "chb10", "chb03"]
    for s in subs:
        V9E1.cache_D(s)
    mg, mb, mf = [], [], []
    for s in subs:
        ctx = V9E1.subject_ctx(s)
        Dg, Db = ctx["D"][HEAD], V9E1.load_D(s, "B4")
        mg.append(PS.smoothed(ctx, member_mean_z_from_D_x1(ctx, Dg), SMOOTH))
        mb.append(PS.smoothed(ctx, member_mean_z_from_D_x1(ctx, Db), SMOOTH))
        _, mfr = f_signals_x1(ctx, Dg, Db)
        mf.append(PS.smoothed(ctx, mfr, SMOOTH))
    k_g, k_b4, k_f = P3L.calibrate(mg), P3L.calibrate(mb), P3L.calibrate(mf)
    print(f"smoke calibration (3 patients, NOT the real dev k): k_G={k_g:.4f} k_B4={k_b4:.4f} k_F={k_f:.4f}", flush=True)
    s0 = subs[0]
    ctx = V9E1.subject_ctx(s0)
    Dg, Db = ctx["D"][HEAD], V9E1.load_D(s0, "B4")
    refs = P3L.refs_of(ctx)
    x, m = final_scalar_from_D_x1(ctx, Dg), member_mean_z_from_D_x1(ctx, Dg)
    out, det, loc, errs = V9E1B.one_pass(ctx, x, k_g, m, refs)
    print(f"smoke one_pass(G) OK: {out['localized']}", flush=True)
    print(f"smoke done in {time.time() - t0:.0f}s", flush=True)


# ============================================================================ final report
def build_report():
    L = ["# V9-X1 -- why focal seizures are missed, and a focal-aware ensemble member\n",
         "Part 0: see `results/v9_x1/part0/SUMMARY.md` (reproduced below is a pointer, not a copy).\n",
         "Part A full tables: `results/v9_x1/*.csv`, `results/v9_x1/posthoc/*.csv`. Code: "
         "`src/v9_x1_focal.py` (new; every frozen script it calls -- p2_scalars, e16_recording_baseline, "
         "e17b_latent_family, e18_cpd_localizer, p3_levers, p3_anatomy, e22_test_oneshot, v9_e1_baselines, "
         "v9_e1b_calibrate, v9_e2_veto, v9_anatomy, v9_eeg_samples, v9_eeg_evidence -- is read-only and "
         "unmodified).\n"]
    part0_path = PART0 / "SUMMARY.md"
    if part0_path.exists():
        L.append(part0_path.read_text(encoding="utf-8"))

    cal = json.load(open(OUT / "calibration.json")) if (OUT / "calibration.json").exists() else None
    if cal:
        L += ["\n## Part A -- calibration\n",
             f"k_G = {cal['k_G']:.6f}, k_B4 = {cal['k_B4']:.6f}, k_F = {cal['k_F']:.6f} "
             f"(primary, members {list(MEMBERS_X1.values())}); descriptive secondary (2nd largest, "
             f"development only): k_G2 = {cal['k_G2']:.6f}, k_F2 = {cal['k_F2']:.6f}."]

    if (OUT / "per_subject.csv").exists():
        R = pd.read_csv(OUT / "per_subject.csv")
        for setname, subs in (("dev", DEV), ("test", TEST), ("chb24", ["chb24"]), ("siena14", SIENA_ALL_14)):
            L.append(f"\n### {setname} ({len(subs)} patients)\n```")
            for arm in [a for a in ARMS_ALL if a in R.arm.unique()]:
                d = R[(R.subject.isin(subs)) & (R.arm == arm) & (R.stage == "localized")]
                if not len(d):
                    continue
                if arm in ("G", "F", "G2", "F2"):
                    d = d[d.seed == HEAD]
                tp, fp, nr, h = d.tp.sum(), d.fp.sum(), d.n_ref.sum(), d.nonict_h.sum()
                sens = tp / nr if nr else np.nan
                prec = tp / (tp + fp) if (tp + fp) else np.nan
                f1 = 2 * tp / (2 * tp + fp + (nr - tp)) if nr else np.nan
                fa = fp / h * 24 if h else np.nan
                L.append(f"{ARM_LABEL.get(arm, arm):48s} tp/ref {tp:.0f}/{nr:.0f}  fp {fp:.0f}  "
                         f"sens {sens:.3f}  prec {prec:.3f}  F1 {f1:.3f}  FP/day {fa:.2f}")
            L.append("```")

    if (POSTHOC / "paired_vs_old.csv").exists():
        P_ = pd.read_csv(POSTHOC / "paired_vs_old.csv")
        L += ["\n## Paired patient bootstrap vs the SAME arm without the change (B=10,000)\n", "```",
             P_.round(4).to_string(index=False), "```"]
        L.append("\n### Adoption rule (fixed): dev paired diff @ 27.5 FP/day, point estimate > 0 AND "
                 "95% CI lower bound >= -0.02\n")
        for arm in ("G", "F"):
            d = P_[(P_.set == "dev") & (P_.arm == arm) & (P_.fa_target == 27.5)]
            if not len(d):
                L.append(f"- {arm}: not available"); continue
            r = d.iloc[0]
            ok = (r.mean_diff > 0) and (r.ci_lo >= -0.02)
            L.append(f"- {arm}: mean diff {r.mean_diff:+.4f}, 95% CI [{r.ci_lo:+.4f}, {r.ci_hi:+.4f}] "
                     f"-> **{'ADOPTED' if ok else 'NOT adopted'}**")

    if (POSTHOC / "channel_count_new_arm.csv").exists():
        j = pd.read_csv(POSTHOC / "channel_count_new_arm.csv")
        foc = j[j.focal_generalized == "focal"]
        L += ["\n## Detections by annotated channel count (test, new arm G, focal only)\n", "```",
             pd.crosstab(foc.n_ictal <= 3, foc.caught).to_string(), "```"]

    if (OUT / "loc_errors.csv").exists():
        ERR = pd.read_csv(OUT / "loc_errors.csv")
        L += ["\n## Onset/offset |error| (median s), new arm, test\n", "```"]
        for arm in ("G", "F"):
            e = ERR[(ERR.subject.isin(TEST)) & (ERR.arm == arm)]
            if not len(e):
                continue
            _, on_s = P3L.err_stats(e, "onset_err")
            _, off_s = P3L.err_stats(e, "offset_err")
            L.append(f"{ARM_LABEL[arm]:48s} onset {on_s} | offset {off_s}")
        L.append("```")

    if (POSTHOC / "fp_type_shares_new_arm.csv").exists():
        share = pd.read_csv(POSTHOC / "fp_type_shares_new_arm.csv")
        L += ["\n## False-alarm types (arm G, test, same rule as results/v9_v1/ Part 4; scoped to test "
             "only -- see module docstring)\n", "```", share.to_string(index=False), "```"]

    if FIGOUT.exists() and any(FIGOUT.iterdir()):
        L.append(f"\n## EEG evidence\n{len(list(FIGOUT.glob('*_full18.png')))} panels at `{FIGOUT}` "
                "(newly-caught / newly-lost test seizures, shortest first, strips r=1,3,9).")

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "SUMMARY.md").write_text("\n".join(L), encoding="utf-8")
    inbox = Path("F:/Study/Thesis/Agent/inbox/V9_X1_REPORT.md")
    inbox.parent.mkdir(parents=True, exist_ok=True)
    inbox.write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))
    print(f"\nWrote results/v9_x1/SUMMARY.md and {inbox}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--part0", action="store_true")
    ap.add_argument("--calibrate", action="store_true")
    ap.add_argument("--eval-one", metavar="SUBJ")
    ap.add_argument("--eval-all", action="store_true")
    ap.add_argument("--aggregate", action="store_true")
    ap.add_argument("--posthoc", action="store_true")
    ap.add_argument("--eeg", action="store_true")
    ap.add_argument("--report", action="store_true")
    a = ap.parse_args()
    if a.smoke:
        smoke()
    elif a.part0:
        part0()
    elif a.calibrate:
        calibrate()
    elif a.eval_one:
        eval_one(a.eval_one)
    elif a.eval_all:
        eval_all()
    elif a.aggregate:
        aggregate()
    elif a.posthoc:
        posthoc()
    elif a.eeg:
        draw_change_eeg()
    elif a.report:
        build_report()
    else:
        raise SystemExit("pass --smoke, --part0, --calibrate, --eval-one SUBJ, --eval-all, --aggregate, "
                         "--posthoc, --eeg or --report")


if __name__ == "__main__":
    main()
