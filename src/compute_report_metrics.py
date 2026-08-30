"""
compute_report_metrics.py — bang ket qua DAY DU cho report. Cursor CPU, khong torch.

Doc BASELINE v3.1 (equal-weight, seed42):
  - results/retrain_v3p1/ens/ens_seed42_{subj}_{inter,ictal}.npy   -> window AUROC + AUPRC per-subject + macro
  - results/retrain_v3p1/fp_budget_locked.csv                       -> event pooled (Sens/Prec/F1/FP-day + CI) tai 2 OP
  - results/retrain_v3p1/final_eval_seed42.csv                      -> event per-subject tai 2 OP locked

Xuat:
  results/retrain_v3p1/report_metrics.md    (bang doc luon)
  results/retrain_v3p1/report_metrics.csv   (long format, de dung dung table/plot)

Chay tu repo ROOT:
  python src/compute_report_metrics.py
Smoke:
  python src/compute_report_metrics.py --smoke
"""
import argparse
import csv
import glob
import statistics
from pathlib import Path

import numpy as np
from sklearn.metrics import roc_auc_score, average_precision_score

TEST_SUBJS = ["chb03", "chb06", "chb13", "chb14", "chb15", "chb16", "chb17", "chb18"]
OPS = [("balanced", 70.0, 0.5), ("high-sensitivity", 55.0, 0.3)]   # §0 locked operating points


# ---------- window-level: AUROC + AUPRC tu raw ensemble scores ----------
def window_metrics(ens_dir, seed=42, subjs=TEST_SUBJS):
    rows = []
    for s in subjs:
        fi = Path(ens_dir) / f"ens_seed{seed}_{s}_inter.npy"
        fc = Path(ens_dir) / f"ens_seed{seed}_{s}_ictal.npy"
        ei = np.load(fi); ec = np.load(fc)
        ei = ei[~np.isnan(ei)]; ec = ec[~np.isnan(ec)]
        y = np.r_[np.zeros(len(ei)), np.ones(len(ec))]
        score = np.r_[ei, ec]
        auroc = roc_auc_score(y, score)
        auprc = average_precision_score(y, score)         # = area under PR curve
        prev = len(ec) / (len(ei) + len(ec))              # baseline AP = prevalence
        rows.append(dict(subject=s, n_inter=len(ei), n_ictal=len(ec),
                         prevalence=round(prev, 4),
                         window_auroc=round(auroc, 4), window_auprc=round(auprc, 4)))
    macro_auroc = statistics.mean(r["window_auroc"] for r in rows)
    macro_auprc = statistics.mean(r["window_auprc"] for r in rows)
    return rows, round(macro_auroc, 4), round(macro_auprc, 4)


# ---------- event-level pooled: doc thang fp_budget_locked.csv ----------
def event_pooled(fp_budget_csv):
    out = []
    for r in csv.DictReader(open(fp_budget_csv)):
        out.append(dict(operating_point=r["operating_point"], mag_pen=r["mag_pen"],
                        n_seizures=r["n_seizures"], TP=r["TP"], FN=r["FN"], FP=r["FP"],
                        sensitivity=r["sensitivity"], sensitivity_CI=r["sensitivity_CI"],
                        precision=r["precision"], precision_CI=r["precision_CI"],
                        f1=r["f1"], fp_per_day=r["fp_per_day"], fp_per_day_CI=r["fp_per_day_CI"]))
    return out


# ---------- event-level per-subject: final_eval tai 2 OP locked ----------
def event_persubject(final_eval_csv, subjs=TEST_SUBJS):
    rows = list(csv.DictReader(open(final_eval_csv)))
    for r in rows:
        for k in ("mag_pct", "pen_mult", "tp", "fp", "n_seizures", "n_inter_h"):
            r[k] = float(r[k]) if r[k] not in ("", "nan") else float("nan")
    out = []
    for name, mag, pen in OPS:
        for s in subjs:
            m = [r for r in rows if r["subject"] == s
                 and abs(r["mag_pct"] - mag) < 1e-9 and abs(r["pen_mult"] - pen) < 1e-9]
            if not m:
                continue
            r = m[0]; ns = r["n_seizures"]; tp = r["tp"]; fp = r["fp"]; ih = r["n_inter_h"]
            sens = tp / ns if ns else float("nan")
            prec = tp / (tp + fp) if (tp + fp) else float("nan")
            fpd = fp / ih * 24 if ih else float("nan")
            f1 = 2 * prec * sens / (prec + sens) if (prec and sens) else 0.0
            out.append(dict(operating_point=name, subject=s, tp=int(tp), fn=int(ns - tp),
                            fp=int(fp), sensitivity=round(sens, 4), precision=round(prec, 4),
                            f1=round(f1, 4), fp_per_day=round(fpd, 2)))
    return out


def write_md(path, wrows, wmac_auroc, wmac_auprc, epool, epersub):
    L = ["# Report metrics — BASELINE v3.1 (equal-weight, canonical seed 42)", ""]
    L.append("## Window-level (per-subject + macro)")
    L.append("| subject | n_inter | n_ictal | prevalence | AUROC | AUPRC |")
    L.append("|---|---|---|---|---|---|")
    for r in wrows:
        L.append(f"| {r['subject']} | {r['n_inter']} | {r['n_ictal']} | {r['prevalence']} "
                 f"| {r['window_auroc']} | {r['window_auprc']} |")
    L.append(f"| **MACRO** | | | | **{wmac_auroc}** | **{wmac_auprc}** |")
    L.append("\n_AUPRC baseline = prevalence (cot prevalence); AUPRC that vi su kien hiem, doc kem prevalence._")

    L.append("\n## Event-level (pooled, 8 sub / 76 con)")
    L.append("| operating point | mag/pen | Sensitivity (CI) | Precision (CI) | F1 | FP/day (CI) | TP/FN/FP |")
    L.append("|---|---|---|---|---|---|---|")
    for r in epool:
        L.append(f"| {r['operating_point']} | {r['mag_pen']} | {r['sensitivity']} {r['sensitivity_CI']} "
                 f"| {r['precision']} {r['precision_CI']} | {r['f1']} | {r['fp_per_day']} {r['fp_per_day_CI']} "
                 f"| {r['TP']}/{r['FN']}/{r['FP']} |")

    L.append("\n## Event-level (per-subject, tai 2 OP locked)")
    L.append("| operating point | subject | Sens | Prec | F1 | FP/day | TP/FN/FP |")
    L.append("|---|---|---|---|---|---|---|")
    for r in epersub:
        L.append(f"| {r['operating_point']} | {r['subject']} | {r['sensitivity']} | {r['precision']} "
                 f"| {r['f1']} | {r['fp_per_day']} | {r['tp']}/{r['fn']}/{r['fp']} |")
    Path(path).write_text("\n".join(L), encoding="utf-8")


def write_csv(path, wrows, epool, epersub):
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["table", "operating_point", "subject", "n_inter", "n_ictal", "prevalence",
                    "window_auroc", "window_auprc", "sensitivity", "precision", "f1",
                    "fp_per_day", "tp", "fn", "fp", "sensitivity_CI", "fp_per_day_CI"])
        for r in wrows:
            w.writerow(["window_persubject", "", r["subject"], r["n_inter"], r["n_ictal"],
                        r["prevalence"], r["window_auroc"], r["window_auprc"], "", "", "", "", "", "", "", "", ""])
        for r in epool:
            w.writerow(["event_pooled", r["operating_point"], "", "", "", "", "", "",
                        r["sensitivity"], r["precision"], r["f1"], r["fp_per_day"],
                        r["TP"], r["FN"], r["FP"], r["sensitivity_CI"], r["fp_per_day_CI"]])
        for r in epersub:
            w.writerow(["event_persubject", r["operating_point"], r["subject"], "", "", "", "", "",
                        r["sensitivity"], r["precision"], r["f1"], r["fp_per_day"],
                        r["tp"], r["fn"], r["fp"], "", ""])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="results/retrain_v3p1")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--smoke", action="store_true")
    a = ap.parse_args()

    if a.smoke:
        d = Path("/tmp/rep_smoke/ens"); d.mkdir(parents=True, exist_ok=True)
        rng = np.random.default_rng(0)
        for s in TEST_SUBJS:
            np.save(d / f"ens_seed42_{s}_inter.npy", rng.normal(0, 1, 400))
            np.save(d / f"ens_seed42_{s}_ictal.npy", rng.normal(1.3, 1, 30))
        wr, ma, mp = window_metrics(d)
        assert 0 <= ma <= 1 and 0 <= mp <= 1 and len(wr) == 8
        print(f"[SMOKE] macro AUROC={ma} AUPRC={mp} -> PASS")
        return

    base = Path(a.base)
    ens_dir = base / "ens"
    wr, ma, mp = window_metrics(ens_dir, a.seed)
    epool = event_pooled(base / "fp_budget_locked.csv")
    epersub = event_persubject(base / "final_eval_seed42.csv")
    write_md(base / "report_metrics.md", wr, ma, mp, epool, epersub)
    write_csv(base / "report_metrics.csv", wr, epool, epersub)
    print(f"window macro: AUROC={ma}  AUPRC={mp}")
    print(f"[saved] {base/'report_metrics.md'} , {base/'report_metrics.csv'}")


if __name__ == "__main__":
    main()
