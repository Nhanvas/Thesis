#!/usr/bin/env python
"""
make_v8_exhibits.py -- figures and tables of the v8 report that are drawn from COMMITTED result files only
(integrity rule 13: nothing is recomputed from EEG or from score caches). Exhibit numbers follow
docs/writing/REPORT_OUTLINE_v8.md section 5.

Every exhibit has a GATE: the values it is built from must reproduce the numbers of record
(e23 / e22 / x1 summaries, attribution tests, application run). A mismatch stops the script.

Figures (PNG, 300 dpi):
  fig11_sparsification.png   density per rule and seizure-background separation, 8 test patients
                             (results/diagnostics/density_frobenius_v2/)
  fig13_boundaries.png       signed onset / offset error, detector vs localizer, final system, 4 seeds
                             (results/e23_test_look7/errors.csv)
  fig16_sens_fa.png          sensitivity vs false alarms per day, (a) CHB-MIT (b) Siena
                             (src/figures_v8/comparison_rows.csv = Table 18 rows with their sources)
  fig17_budget_needed.png    alarm budget needed per test seizure (results/p3_anatomy/seizures.csv, seed 42)
  fig12_duration.png         detection by seizure duration -- ONLY if results/figures_v8_data/
                             perseizure_final.csv exists (written by Claude Code, CC_FIGURES_V8.md)

Tables (Markdown + CSV): table04_split, table11_test, table12_per_patient, table13_boundaries,
  table14_external, table15_siena, table16_channel, table17_application, appD1_test_seeds,
  appD2_siena_seeds, appD3_chb24_seeds, appA1_chbmit_accounting.

Run:  python src/figures_v8/make_v8_exhibits.py [--out ../Reports/v8]      (~15 s, measured in the cloud copy)
Writes <out>/figures/*.png and <out>/tables/*.md|csv.
"""
import argparse
import json
import re
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
TEST = ["chb03", "chb06", "chb13", "chb14", "chb15", "chb16", "chb17", "chb18"]
TRAIN = ["chb01", "chb02", "chb04", "chb05", "chb07", "chb08", "chb09", "chb12", "chb19", "chb20", "chb21", "chb23"]
VAL = ["chb10", "chb11", "chb22"]
SIENA = ["PN00", "PN01", "PN03", "PN05", "PN06", "PN07", "PN09", "PN10", "PN11", "PN12", "PN13", "PN14", "PN16", "PN17"]
SEEDS = ["clean_seed42", "clean_seed1", "clean_seed2", "clean_seed3"]
C = dict(det="#E69F00", loc="#009E73", sz="#D55E00", miss="#D9D9D9", main="#0072B2", grey="#777777",
         sup="#999999", uns="#CC79A7")
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.spines.top": False,
                     "axes.spines.right": False, "savefig.dpi": 300})


def stop(msg):
    raise SystemExit(f"STOP (gate): {msg}")


def gate(cond, msg):
    if not cond:
        stop(msg)


def write_table(df, out, name, title, note=None):
    (out / "tables").mkdir(parents=True, exist_ok=True)
    df.to_csv(out / "tables" / f"{name}.csv", index=False)
    cols = list(df.columns)
    lines = [f"Table: {title}", "", "| " + " | ".join(map(str, cols)) + " |", "|" + "---|" * len(cols)]
    for _, r in df.iterrows():
        lines.append("| " + " | ".join("" if (isinstance(v, float) and np.isnan(v)) else str(v) for v in r) + " |")
    if note:
        lines += ["", note]
    (out / "tables" / f"{name}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def f3(x):
    return f"{x:.3f}"


def f1(x):
    return f"{x:.1f}"


# ───────────────────────────── shared readers ─────────────────────────────

def e23_seed(stage="localized"):
    d = pd.read_csv(ROOT / "results/e23_test_look7/summary_per_seed.csv")
    return d[(d.point == "balanced") & (d.system == stage)].set_index("seed").loc[SEEDS]


def e22_per_subject():
    d = pd.read_csv(ROOT / "results/e22_test_oneshot/per_subject_seed.csv")
    return d[d.stage == "localized"]


def e23_per_subject():
    d = pd.read_csv(ROOT / "results/e23_test_look7/per_subject_seed.csv")
    return d[(d.point == "balanced") & (d.stage == "localized")]


def x1_rows():
    parts = [pd.read_csv(p) for p in sorted((ROOT / "results/x1_external").glob("rows_*.csv"))]
    d = pd.concat(parts)
    return d[(d.point == "balanced") & (d.stage == "localized")]


def pooled(df):
    tp, fp, n, h = df.tp.sum(), df.fp.sum(), df.n_ref.sum(), df.nonict_h.sum()
    return dict(tp=tp, fp=fp, n=n, sens=tp / n, prec=tp / (tp + fp), f1=2 * tp / (2 * tp + fp + (n - tp)),
                fa=fp / h * 24)


def subject_mean(df):
    s = df.tp / df.n_ref
    p = df.tp / (df.tp + df.fp)
    f = 2 * df.tp / (2 * df.tp + df.fp + (df.n_ref - df.tp))
    fa = df.fp / df.nonict_h * 24
    return dict(sens=s.mean(), prec=p.mean(), f1=f.mean(), fa=fa.mean())


# ───────────────────────────── tables ─────────────────────────────

def table04_split(out):
    """Recorded hours: summary-file start/end times (distributed corpus) and hours scored (anatomy)."""
    def secs(t):
        h, m, s = map(int, t.split(":"))
        return h * 3600 + m * 60 + s
    rows = []
    hours_scored = pd.read_csv(ROOT / "results/p3_anatomy/labelfree.csv").groupby("subject")[["hours", "files"]].first()
    for subj in TRAIN + VAL + TEST:
        txt = (ROOT / f"data/summaries/{subj}-summary.txt").read_text()
        blocks = re.findall(r"File Name: (\S+)\s*\nFile Start Time: (\S+)\s*\nFile End Time: (\S+)\s*\n"
                            r"Number of Seizures in File: (\d+)", txt)
        listed_h = sum(((secs(b) - secs(a)) % 86400) / 3600 for _, a, b, _ in blocks)
        n_sz = sum(int(k) for *_, k in blocks)
        rows.append(dict(set="training" if subj in TRAIN else "validation" if subj in VAL else "test",
                         case=subj, files_listed=len(blocks), hours_listed=listed_h,
                         files_scored=int(hours_scored.loc[subj, "files"]),
                         hours_scored=hours_scored.loc[subj, "hours"], seizures_listed=n_sz))
    a = pd.DataFrame(rows)
    tot = a.groupby("set", sort=False)[["files_listed", "hours_listed", "files_scored", "hours_scored", "seizures_listed"]].sum().round(2)
    a[["hours_listed", "hours_scored"]] = a[["hours_listed", "hours_scored"]].round(2)
    gate(abs(tot.loc["test", "hours_listed"] - 279.39) < 0.01 and tot.loc["test", "seizures_listed"] == 76,
         f"test hours/seizures {tot.loc['test'].to_dict()}")
    gate(abs(tot.loc["training", "hours_listed"] - 566.43) < 0.01 and abs(tot.loc["validation", "hours_listed"] - 115.82) < 0.01,
         "development hours differ from v5 Table 4")
    write_table(a, out, "appA1_chbmit_accounting", "CHB-MIT recording accounting per case",
                "hours_listed: start/end times of the CHB-MIT summary files; hours_scored: windows scored in the "
                "evaluation (results/p3_anatomy/labelfree.csv). Differences: chb12 three files without the 18 "
                "common derivations; chb11 four files and chb21 one file listed in the summaries but absent from "
                "the local dataset copy (no seizures in them).")
    write_table(tot.reset_index(), out, "table04_split_totals", "Patient split (totals per set)")
    return tot


def table11_test(out):
    loc, held = e23_seed("localized"), None
    e22 = pd.read_csv(ROOT / "results/e22_test_oneshot/summary_per_seed.csv")
    # held-out values are the 'look #6' rows written by e23 (same as e22): read them from e23
    d = pd.read_csv(ROOT / "results/e23_test_look7/summary_per_seed.csv")
    held = d[(d.point == "balanced") & (d.system.str.contains("6"))].set_index("seed").loc[SEEDS]
    s42f, s42h = loc.loc["clean_seed42"], held.loc["clean_seed42"]
    gate((s42f.tp, s42f.fp, round(s42f.sens, 3), round(s42f.s_sens, 3)) == (37, 318, 0.487, 0.577), "final seed 42")
    gate((s42h.tp, s42h.fp, round(s42h.sens, 3), round(s42h.s_sens, 3)) == (26, 257, 0.342, 0.508), "held-out seed 42")
    boot6 = (ROOT / "results/e22_test_oneshot/BOOTSTRAP.md").read_text()
    b_pool = re.search(r"all 8\s+final pooled sens\s+\+?([\d.]+)\s+\[\s*\+?([\d.]+),\s*\+?([\d.]+)\]", boot6).groups()
    b_mean = re.search(r"all 8\s+final subject-mean sens\s+\+?([\d.]+)\s+\[\s*\+?([\d.]+),\s*\+?([\d.]+)\]", boot6).groups()
    s7 = (ROOT / "results/e23_test_look7/SUMMARY.md").read_text().split("## sensitivity")[0]
    dp = re.search(r"pooled sens diff \+([\d.]+) \[\+([\d.]+), \+([\d.]+)\]", s7).groups()
    dm = re.search(r"subject-mean diff \+([\d.]+) \[\+([\d.]+), \+([\d.]+)\]", s7).groups()
    df = re.search(r"FP/day diff \+([\d.]+) \[\+([\d.]+), \+([\d.]+)\]", s7).groups()

    def col(s42, all4):
        return [f"{int(s42.tp)} / {int(s42.n_ref - s42.tp)} / {int(s42.fp)}",
                f"{f3(s42.sens)} / {f3(s42.s_sens)}", f"{f3(s42.prec)} / {f3(s42.s_prec)}",
                f"{f3(s42.f1)} / {f3(s42.s_f1)}", f"{f1(s42.fa_day)} / {f1(s42.s_fa)}",
                f"{f3(all4.sens.mean())} ± {f3(all4.sens.std())} / {f3(all4.s_sens.mean())} ± {f3(all4.s_sens.std())}",
                f"{f1(all4.fa_day.mean())} ± {f1(all4.fa_day.std())}"]
    rows = ["Seizures detected / missed / false alarms (seed 42)", "Sensitivity, pooled / per-patient mean",
            "Precision, pooled / per-patient mean", "F1, pooled / per-patient mean",
            "False alarms per day, pooled / per-patient mean", "Sensitivity, four seeds (mean ± SD), pooled / per-patient mean",
            "False alarms per day, four seeds (mean ± SD)"]
    t = pd.DataFrame({"Metric": rows, "Held-out evaluation": col(s42h, held), "Final system (test-informed)": col(s42f, loc)})
    t.loc[len(t)] = ["95 % patient bootstrap interval (four-seed mean)",
                     f"pooled {b_pool[0]} [{b_pool[1]}, {b_pool[2]}]; per-patient mean {b_mean[0]} [{b_mean[1]}, {b_mean[2]}]",
                     f"difference from held-out: pooled +{dp[0]} [{dp[1]}, {dp[2]}]; per-patient mean +{dm[0]} [{dm[1]}, {dm[2]}]; "
                     f"false alarms per day +{df[0]} [+{df[1]}, +{df[2]}]"]
    write_table(t, out, "table11_test", "Detection on the test patients",
                "SD over four seeds is spread due to initialisation, not uncertainty; the bootstrap resamples patients.")
    return t


def table12_per_patient(out):
    h = e22_per_subject(); f = e23_per_subject()
    h42 = h[h.seed == "clean_seed42"].set_index("subject").loc[TEST]
    f42 = f[f.seed == "clean_seed42"].set_index("subject").loc[TEST]
    gate((h42.tp.sum(), h42.fp.sum(), f42.tp.sum(), f42.fp.sum()) == (26, 257, 37, 318), "per-patient totals")
    t = pd.DataFrame({"Patient": TEST, "Seizures": f42.n_ref.values,
                      "Held-out: detected": h42.tp.values, "Held-out: false alarms": h42.fp.values,
                      "Held-out: FP/day": (h42.fp / h42.nonict_h * 24).round(1).values,
                      "Final: alarm budget": f42.top.round(4).values, "Final: detected": f42.tp.values,
                      "Final: false alarms": f42.fp.values, "Final: FP/day": (f42.fp / f42.nonict_h * 24).round(1).values})
    t.loc[len(t)] = ["Total", 76, 26, 257, round(pooled(h42.reset_index())["fa"], 1), "", 37, 318,
                     round(pooled(f42.reset_index())["fa"], 1)]
    write_table(t, out, "table12_per_patient", "Detection per test patient", "Seed 42, after the localizer.")
    return t


def table13_boundaries(out):
    dev = pd.read_csv(ROOT / "results/p3c_freeze/errors.csv"); dev = dev[dev.budget == "L2f"]
    held = pd.read_csv(ROOT / "results/e22_test_oneshot/errors.csv")
    fin = pd.read_csv(ROOT / "results/e23_test_look7/errors.csv"); fin = fin[fin.point == "balanced"]
    x = pd.concat([pd.read_csv(p) for p in sorted((ROOT / "results/x1_external").glob("errors_*.csv")) if p.stat().st_size > 5])
    x = x[x.point == "balanced"]
    rows = []
    for name, d, on, off in (("Development patients", dev, "cpd_on", "cpd_off"), ("Test, held-out evaluation", held, "loc_on", "loc_off"),
                             ("Test, final system", fin, "cpd_on", "cpd_off"), ("chb24", x[x.subject == "chb24"], "cpd_on", "cpd_off"),
                             ("Siena", x[x.set == "siena"], "cpd_on", "cpd_off")):
        m = d[["det_on", "det_off", on, off]].abs().median()
        rows.append([name, len(d), f"{m.det_on:.0f} / {m.det_off:.0f}", f"{m[on]:.0f} / {m[off]:.0f}",
                     f"{d[on].median():+.0f} / {d[off].median():+.0f}"])
    t = pd.DataFrame(rows, columns=["Patients", "Matched seizure-seed pairs", "Detector onset / offset (s)",
                                    "Localizer onset / offset (s)", "Localizer bias onset / offset (s)"])
    gate(list(t["Matched seizure-seed pairs"]) == [247, 103, 146, 53, 116], f"pair counts {list(t.iloc[:, 1])}")
    gate(list(t.iloc[:, 3]) == ["4 / 16", "8 / 20", "12 / 24", "4 / 4", "20 / 28"], f"localizer medians {list(t.iloc[:, 3])}")
    write_table(t, out, "table13_boundaries", "Onset and offset error",
                "Median absolute error over matched pairs of the four seeds; bias = median signed error (positive = late).")
    return t


def table14_external(out, bench):
    x = x1_rows()
    rows = []
    for name, sel in (("chb24", x.subject == "chb24"), ("Siena", x.set == "siena")):
        d = x[sel]
        d42 = d[d.seed == "clean_seed42"]
        p42, m42 = pooled(d42), subject_mean(d42)
        ps = [pooled(d[d.seed == s]) for s in SEEDS]; ms = [subject_mean(d[d.seed == s]) for s in SEEDS]
        rows.append([name, f"{p42['tp']}/{p42['n']}", p42["fp"], f"{f3(p42['sens'])} / {f3(m42['sens'])}",
                     f"{f3(p42['prec'])} / {f3(m42['prec'])}", f"{f3(p42['f1'])} / {f3(m42['f1'])}",
                     f"{f1(p42['fa'])} / {f1(m42['fa'])}",
                     f"{f3(np.mean([p['sens'] for p in ps]))} ± {f3(np.std([p['sens'] for p in ps], ddof=1))} / "
                     f"{f3(np.mean([m['sens'] for m in ms]))} ± {f3(np.std([m['sens'] for m in ms], ddof=1))}",
                     f"{f3(np.mean([m['prec'] for m in ms]))} / {f3(np.mean([m['f1'] for m in ms]))}",
                     f"{f1(np.mean([p['fa'] for p in ps]))} / {f1(np.mean([m['fa'] for m in ms]))}"])
    t = pd.DataFrame(rows, columns=["Set", "Detected (seed 42)", "False alarms (seed 42)", "Sensitivity pooled / per-patient mean (seed 42)",
                                    "Precision pooled / mean (seed 42)", "F1 pooled / mean (seed 42)", "FP/day pooled / mean (seed 42)",
                                    "Sensitivity, four seeds, pooled / mean", "Precision / F1, four seeds, mean", "FP/day, four seeds, pooled / mean"])
    gate(t.iloc[0, 1] == "14/16" and t.iloc[1, 1] == "33/47", "external counts")
    gate(t.iloc[1, 7].endswith("0.633 ± 0.079") and t.iloc[1, 8] == "0.160 / 0.226" and t.iloc[1, 9].endswith("/ 41.0"),
         f"Siena four-seed values {t.iloc[1, 7:].tolist()}")
    dyn = bench["DynaSD"]
    t.loc[len(t)] = ["Siena, DynaSD (benchmark)", "", "", f"— / {dyn[0]}", f"— / {dyn[1]}", f"— / {dyn[2]}", f"— / {dyn[3]}", "", "", ""]
    write_table(t, out, "table14_external", "External validation",
                "Per-patient mean = the SzCORE aggregate. Siena patient bootstrap of the four-seed per-patient mean "
                "sensitivity [0.477, 0.777], FP/day [32.3, 53.9] (record 9.9, computed). Benchmark row: SzCORE "
                "benchmark results, commit c57da2f.")
    return t


def table15_siena(out):
    x = x1_rows(); s = x[(x.set == "siena") & (x.seed == "clean_seed42")].set_index("subject").loc[SIENA]
    gate((s.tp.sum(), s.n_ref.sum(), s.fp.sum(), round(s.hours.sum(), 1)) == (33, 47, 257, 141.0), "Siena per patient")
    t = pd.DataFrame({"Patient": SIENA, "Recorded hours": s.hours.round(2).values, "Seizures": s.n_ref.values,
                      "Detected": s.tp.values, "False alarms": s.fp.values,
                      "FP/day": (s.fp / s.nonict_h * 24).round(1).values, "Alarm budget": s.top.round(4).values})
    t.loc[len(t)] = ["Total", round(s.hours.sum(), 1), 47, 33, 257, round(pooled(s.reset_index())["fa"], 1), ""]
    write_table(t, out, "table15_siena", "Detection per Siena patient", "Seed 42, after the localizer.")
    return t


def table16_channel(out):
    rows = []
    for name, d in (("Channel-level latent anomaly (final system)", "attribution_v8"), ("Reconstruction error (earlier autoencoder)", "attribution_v7")):
        t = pd.read_csv(ROOT / f"results/{d}/attribution_tests.csv").set_index("test")
        sm = pd.read_csv(ROOT / f"results/{d}/attribution_summary.csv")
        ex = sm[sm.panel.str.startswith("focal excl. chb15")].macro_AUROC.iloc[0]
        l1, l2, l3 = t.loc["L1 chance"], t.loc["L2 anatomical prior"], t.loc["L3 matched vs swapped"]
        rows.append([name, f"{l1.value:.3f} [{l1.CI_lo:.3f}, {l1.CI_hi:.3f}], p = {l1.p:.3f}",
                     f"{l2.value:+.3f} [{l2.CI_lo:+.3f}, {l2.CI_hi:+.3f}]",
                     f"p = {l3.p:.2f} (Holm {l3.p_holm:.2f})", f"{ex:.3f}"])
    t = pd.DataFrame(rows, columns=["Readout", "Mean AUROC [95 % CI], p vs chance", "Difference from anatomical prior (0.739) [95 % CI]",
                                    "Seizure specificity", "Without chb15"])
    gate(t.iloc[0, 1].startswith("0.547 [0.499, 0.597]") and t.iloc[1, 1].startswith("0.569 [0.510, 0.632]"), "channel L1")
    write_table(t, out, "table16_channel", "Channel ranking against expert annotation", "62 focal test seizures; seed 42.")
    return t


def table17_application(out):
    a = pd.read_csv(ROOT / "results/application_eval_v4/per_subject.csv").set_index("subject").loc[TEST]
    f42 = e23_per_subject(); f42 = f42[f42.seed == "clean_seed42"].set_index("subject").loc[TEST]
    pj = json.loads((ROOT / "results/application_eval_v4/pooled.json").read_text())
    gate((a.detected.sum(), a.false_alarms.sum(), pj["pooled"]["tp"]) == (33, 323, 33), "application totals")
    t = pd.DataFrame({"Patient": TEST, "Seizures": a.seizures.values,
                      "Application: detected": a.detected.values, "Application: false alarms": a.false_alarms.values,
                      "Final system: detected": f42.tp.values, "Final system: false alarms": f42.fp.values})
    t.loc[len(t)] = ["Total", 76, 33, 323, 37, 318]
    am = a.sensitivity.mean()
    note = (f"Application (label-free normalisation statistics), all events before review: pooled sensitivity "
            f"{pj['pooled']['sensitivity']:.3f}, precision {pj['pooled']['precision']:.3f}, F1 {pj['pooled']['f1']:.3f}, "
            f"{pj['pooled']['false_alarms_per_day']:.2f} FP/day; per-patient mean sensitivity {am:.3f}. Final system: seed 42.")
    gate(round(am, 3) == 0.528, "application per-patient mean")
    write_table(t, out, "table17_application", "Review application on the test patients", note)
    return t


def appendix_d(out):
    h = e22_per_subject(); f = e23_per_subject()
    rows = []
    for subj in TEST:
        r = [subj, int(f[f.subject == subj].n_ref.iloc[0])]
        for d in (h, f):
            r.append(" / ".join(str(int(d[(d.subject == subj) & (d.seed == s)].tp.iloc[0])) for s in SEEDS))
            r.append(" / ".join(str(int(d[(d.subject == subj) & (d.seed == s)].fp.iloc[0])) for s in SEEDS))
        rows.append(r)
    t = pd.DataFrame(rows, columns=["Patient", "Seizures", "Held-out detected (42/1/2/3)", "Held-out false alarms",
                                    "Final detected (42/1/2/3)", "Final false alarms"])
    write_table(t, out, "appD1_test_seeds", "Detection per test patient and seed")
    x = x1_rows()
    for name, sel, code in (("Siena", x.set == "siena", "appD2_siena_seeds"), ("chb24", x.subject == "chb24", "appD3_chb24_seeds")):
        d = x[sel]; rows = []
        for subj in sorted(d.subject.unique()):
            g = d[d.subject == subj]
            rows.append([subj, int(g.n_ref.iloc[0]), " / ".join(str(int(g[g.seed == s].tp.iloc[0])) for s in SEEDS),
                         " / ".join(str(int(g[g.seed == s].fp.iloc[0])) for s in SEEDS)])
        write_table(pd.DataFrame(rows, columns=["Patient", "Seizures", "Detected (42/1/2/3)", "False alarms (42/1/2/3)"]),
                    out, code, f"Detection per {name} patient and seed")


# ───────────────────────────── figures ─────────────────────────────

def fig11_sparsification(out):
    den = pd.read_csv(ROOT / "results/diagnostics/density_frobenius_v2/density_per_subject.csv")
    sep = pd.read_csv(ROOT / "results/diagnostics/density_frobenius_v2/separation_per_subject.csv").set_index("subject").loc[TEST]
    gate(round(sep.pct_change_rel_topk_vs_fixed.min()) == 48 and round(sep.pct_change_rel_topk_vs_fixed.max()) == 196, "Frobenius change")
    fig, ax = plt.subplots(1, 2, figsize=(6.3, 3.1))
    x = np.arange(len(TEST)); w = 0.2
    for i, (rule, split, col, lab) in enumerate((("fixed_t0.05", "interictal", C["grey"], "fixed threshold, background"),
                                                 ("fixed_t0.05", "ictal", C["sz"], "fixed threshold, seizure"),
                                                 ("topk20", "interictal", C["main"], "strongest 20 %, background"),
                                                 ("topk20", "ictal", C["loc"], "strongest 20 %, seizure"))):
        v = den[(den.rule == rule) & (den.split == split)].set_index("subject").loc[TEST].mean_density
        ax[0].bar(x + (i - 1.5) * w, v, w, color=col, label=lab)
    ax[0].set_xticks(x, [s[3:] for s in TEST]); ax[0].set_xlabel("Test patient (chb)"); ax[0].set_ylabel("Graph density")
    ax[0].set_ylim(0, 1.0)
    ax[0].set_title("(a)", loc="left")
    fig.legend(*ax[0].get_legend_handles_labels(), frameon=False, fontsize=7, ncol=2, loc="lower center", bbox_to_anchor=(0.5, 0.0))
    ax[1].bar(x - 0.2, sep.rel_frobenius_fixed_t0_05, 0.4, color=C["grey"], label="fixed threshold")
    ax[1].bar(x + 0.2, sep.rel_frobenius_topk20, 0.4, color=C["main"], label="strongest 20 %")
    ax[1].set_xticks(x, [s[3:] for s in TEST]); ax[1].set_xlabel("Test patient (chb)")
    ax[1].set_ylabel("Seizure–background distance\n(relative Frobenius)"); ax[1].set_ylim(0, 0.9)
    ax[1].legend(frameon=False, fontsize=7, loc="upper left", ncol=2)
    ax[1].set_title("(b)", loc="left")
    fig.tight_layout(rect=(0, 0.13, 1, 1)); fig.savefig(out / "figures" / "fig11_sparsification.png"); plt.close(fig)


def fig13_boundaries(out):
    e = pd.read_csv(ROOT / "results/e23_test_look7/errors.csv"); e = e[e.point == "balanced"]
    med = e[["det_on", "det_off", "cpd_on", "cpd_off"]].abs().median()
    gate(len(e) == 146 and tuple(med) == (32.0, 20.0, 12.0, 24.0), "boundary medians")
    fig, ax = plt.subplots(1, 2, figsize=(6.3, 2.6), sharey=True)
    for a, side, lab in ((ax[0], "on", "Onset"), (ax[1], "off", "Offset")):
        data = [e[f"det_{side}"].values, e[f"cpd_{side}"].values]
        bp = a.boxplot(data, vert=False, widths=0.55, showfliers=False, patch_artist=True)
        for patch, col in zip(bp["boxes"], (C["det"], C["loc"])):
            patch.set_facecolor(col); patch.set_alpha(0.55)
        for m in bp["medians"]:
            m.set_color("k")
        rng = np.random.default_rng(0)
        for i, v in enumerate(data, start=1):
            a.scatter(np.clip(v, -150, 150), i + rng.uniform(-0.18, 0.18, len(v)), s=5, color="k", alpha=0.35, lw=0)
        a.axvline(0, color=C["sz"], lw=1)
        a.set_xlim(-150, 150); a.set_xticks([-120, -60, 0, 60, 120]); a.set_xlabel(f"{lab} error (s)")
        a.set_title("(a)" if side == "on" else "(b)", loc="left")
    ax[0].set_yticks([1, 2], ["Detector\nboundaries", "Change point\nlocalizer"])
    fig.tight_layout(); fig.savefig(out / "figures" / "fig13_boundaries.png"); plt.close(fig)


def fig16_sens_fa(out):
    r = pd.read_csv(Path(__file__).with_name("comparison_rows.csv"))
    fig, ax = plt.subplots(1, 2, figsize=(6.3, 3.0), sharey=True)
    for a, ds, title in ((ax[0], "CHB-MIT", "(a) CHB-MIT"), (ax[1], "Siena", "(b) Siena")):
        d = r[(r.dataset == ds) & (r["show"] == 1)]
        for _, q in d.iterrows():
            if q.group == "this":
                a.scatter(q.fp_day, q.sens, s=46, marker="*", color=C["main"], zorder=3)
            elif q.group == "unsupervised":
                a.scatter(q.fp_day, q.sens, s=30, marker="D", facecolor="white", edgecolor=C["uns"], lw=1.4, zorder=3)
            else:
                a.scatter(q.fp_day, q.sens, s=22, marker="o", color=C["sup"], zorder=2)
            a.annotate(q.label, (q.fp_day, q.sens), textcoords="offset points", xytext=(q.dx, q.dy),
                       ha="right" if q.dx < 0 else "left", fontsize=6.5)
        a.set_xscale("log"); a.set_xlim(0.8, 300); a.set_ylim(0, 1.05); a.set_xlabel("False alarms per day (log)")
        a.set_title(title, loc="left")
    ax[0].set_ylabel("Sensitivity")
    ax[1].scatter([], [], marker="*", s=46, color=C["main"], label="this work")
    ax[1].scatter([], [], marker="D", s=30, facecolor="white", edgecolor=C["uns"], label="unsupervised (other)")
    ax[1].scatter([], [], marker="o", s=22, color=C["sup"], label="supervised")
    ax[1].legend(frameon=False, fontsize=7, loc="lower right")
    fig.tight_layout(); fig.savefig(out / "figures" / "fig16_sens_fa.png"); plt.close(fig)


def fig17_budget_needed(out):
    s = pd.read_csv(ROOT / "results/p3_anatomy/seizures.csv"); s = s[(s.set == "test") & (s.seed == "clean_seed42")]
    gate(len(s) == 76, "76 test seizures")
    b = e23_per_subject(); b = b[b.seed == "clean_seed42"].set_index("subject")
    fig, a = plt.subplots(figsize=(6.3, 2.8))
    rng = np.random.default_rng(1)
    for i, subj in enumerate(TEST):
        v = s[s.subject == subj].pn_final.values
        a.scatter(i + rng.uniform(-0.15, 0.15, len(v)), v, s=12, color=C["main"], alpha=0.75, lw=0)
        a.hlines(b.loc[subj, "top"], i - 0.32, i + 0.32, color=C["loc"], lw=2)
    a.axhline(0.005, color=C["grey"], ls=":", lw=1); a.axhline(0.02, color=C["grey"], ls="--", lw=1)
    a.text(7.45, 0.005, "0.5 %", va="center", fontsize=8); a.text(7.45, 0.02, "2 %", va="center", fontsize=8)
    a.set_yscale("log"); a.set_xticks(range(len(TEST)), TEST); a.set_xlim(-0.5, 7.9)
    a.set_ylabel("Alarm budget needed\n(share of patient time)")
    a.plot([], [], color=C["loc"], lw=2, label="patient's alarm budget (final system)")
    a.scatter([], [], s=12, color=C["main"], label="one seizure")
    fig.legend(*a.get_legend_handles_labels(), frameon=False, fontsize=8, ncol=2, loc="upper center")
    fig.tight_layout(rect=(0, 0, 1, 0.9)); fig.savefig(out / "figures" / "fig17_budget_needed.png"); plt.close(fig)
    return s.groupby("subject").pn_final.median()


def fig12_duration(out):
    p = ROOT / "results/figures_v8_data/perseizure_final.csv"
    if not p.exists():
        print("fig12: results/figures_v8_data/perseizure_final.csv not found (Claude Code step) -- skipped")
        return None
    d = pd.read_csv(p)
    d42 = d[d.seed == "clean_seed42"]
    gate(len(d42) == 76 and int(d42.detected_final.sum()) == 37 and int(d42.detected_heldout.sum()) == 26,
         "per-seizure file must reproduce 37/76 (final) and 26/76 (held-out), seed 42")
    bins = [0, 20, 40, 60, 120, 400]; labels = ["< 20", "20–39", "40–59", "60–119", "≥ 120"]
    d42 = d42.assign(bin=pd.cut(d42.dur_s, bins, right=False, labels=labels))
    g = d42.groupby("bin", observed=False).agg(n=("dur_s", "size"), fin=("detected_final", "sum"), held=("detected_heldout", "sum"))
    fig, a = plt.subplots(figsize=(6.3, 2.5))
    x = np.arange(len(labels))
    a.bar(x, g.n, 0.6, color=C["miss"], label="annotated")
    a.bar(x - 0.13, g.held, 0.26, color=C["grey"], label="detected, held-out evaluation")
    a.bar(x + 0.13, g.fin, 0.26, color=C["main"], label="detected, final system")
    for xi, (n, fi) in enumerate(zip(g.n, g.fin)):
        a.text(xi, n + 0.4, f"{int(fi)}/{int(n)}", ha="center", fontsize=8)
    a.set_xticks(x, labels); a.set_xlabel("Annotated seizure duration (s)"); a.set_ylabel("Seizures")
    a.legend(frameon=False, fontsize=7, loc="upper right")
    fig.tight_layout(); fig.savefig(out / "figures" / "fig12_duration.png"); plt.close(fig)
    return g


def bench_rows():
    txt = (ROOT / "docs/BENCHMARK_CHECK_szcore_c57da2f.md").read_text().split("### Siena")[1].split("###")[0]
    m = re.search(r"\| DynaSD \|[^|]*\| ([\d.]+) \| ([\d.]+) \| ([\d.]+) \| ([\d.]+) \|", txt)
    return {"DynaSD": m.groups()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT.parent / "Reports" / "v8"))
    a = ap.parse_args()
    warnings.filterwarnings("ignore")
    out = Path(a.out); (out / "figures").mkdir(parents=True, exist_ok=True); (out / "tables").mkdir(parents=True, exist_ok=True)
    bench = bench_rows()
    gate(bench["DynaSD"] == ("0.664", "0.126", "0.170", "77.74"), f"benchmark DynaSD row {bench}")
    tot = table04_split(out)
    table11_test(out); table12_per_patient(out); table13_boundaries(out)
    table14_external(out, bench); table15_siena(out); table16_channel(out); table17_application(out); appendix_d(out)
    fig11_sparsification(out); fig13_boundaries(out); fig16_sens_fa(out)
    pk = fig17_budget_needed(out); g12 = fig12_duration(out)
    print("split totals:\n", tot.to_string())
    print("median budget needed per test patient (seed 42):", pk.round(4).to_dict())
    if g12 is not None:
        print("detection by duration:\n", g12.to_string())
    print("ALL GATES PASSED ->", out)


if __name__ == "__main__":
    sys.exit(main())
