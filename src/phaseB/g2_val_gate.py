"""
g2_val_gate.py — CURSOR CPU (Phase B / Tier-2). VAL guardrail G2 + VAL operating-point cells.

Reads the per-candidate VAL event grids produced by score_ens.py:
    <tier2_dir>/<tag>/final_eval_seed{S}.csv   for tag in baseline_rtg, rltg, ltg, rlg
and (optional) the locked §0 VAL grid for the event-level FIDELITY diff.

Does, with the SzCORE-correct refTrue pooling (VAL chb11 = 3 summary seizures -> 5 ref-events;
pooled sensitivity = Σtp / Σ refTrue, NOT Σ n_seizures):
  (b) FIDELITY: baseline_rtg grid must equal the §0 VAL grid (tp/fp/fp_per_day) -> PASS/FAIL.
  (G2) GATE: each candidate's VAL event F1 at the pooled-nearest-B=40 cell >= baseline_rtg's.
       (each ensemble derives its OWN nearest-budget cell — same rule, different score dist.)
  (OP) prints the VAL-derived shared cell @B=40 and @B=75 per candidate (frozen for one-shot TEST).

NO torch. Reads sens/prec/F1 together (Pareto framing), not just AUROC.

USAGE (Cursor)
  python g2_val_gate.py --tier2_dir results/phaseB/tier2 --seed 42 \
      --baseline_ref results/retrain_v3p1/val/final_eval_seed42.csv \
      --out results/phaseB/tier2/G2_val_verdict.csv
"""
import argparse
from pathlib import Path
import numpy as np
import pandas as pd

# tags auto-discovered from tier2_dir subfolders that contain a grid
B_BAL, B_HI = 40.0, 75.0


def reftrue(df):
    """{subj -> refTrue}. refTrue = round(tp/sensitivity), constant per subject (ensemble-invariant)."""
    out = {}
    for s, g in df.groupby("subject"):
        gg = g[g.sensitivity > 0]
        out[s] = int(round((gg.tp / gg.sensitivity).median())) if len(gg) else int(g.n_seizures.iloc[0])
    return out


def pooled_cell(g, rt):
    TP, FP = int(g.tp.sum()), int(g.fp.sum())
    RT = sum(rt[s] for s in g.subject)
    H = float(g.n_inter_h.sum())
    sens = TP / RT if RT else 0.0
    prec = TP / (TP + FP) if (TP + FP) else 0.0
    f1 = 2 * prec * sens / (prec + sens) if (prec + sens) else 0.0
    return dict(TP=TP, FP=FP, RT=RT, sens=sens, prec=prec, f1=f1, fpday=FP / (H / 24.0) if H else 0.0)


def shared_at_budget(df, rt, B):
    best = None
    for (m, p), g in df.groupby(["mag_pct", "pen_mult"]):
        c = pooled_cell(g, rt); c["mag"], c["pen"] = m, p
        if best is None or abs(c["fpday"] - B) < abs(best["fpday"] - B):
            best = c
    return best


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tier2_dir", default="results/phaseB/tier2")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--baseline_ref", default=None, help="§0 VAL grid for fidelity diff (optional)")
    ap.add_argument("--baseline_tag", default="baseline_rtg", help="tag used as the G2 bar")
    ap.add_argument("--tags", default=None, help="comma list; default = auto-discover")
    ap.add_argument("--out", default="results/phaseB/tier2/G2_val_verdict.csv")
    a = ap.parse_args()
    td = Path(a.tier2_dir)

    if a.tags:
        tags = [t.strip() for t in a.tags.split(",")]
    else:
        tags = sorted(p.parent.name for p in td.glob(f"*/final_eval_seed{a.seed}.csv"))
    grids = {t: pd.read_csv(td / t / f"final_eval_seed{a.seed}.csv") for t in tags}
    base_tag = a.baseline_tag
    if base_tag not in grids:
        raise SystemExit(f"baseline_tag {base_tag} not found among {tags}")

    # (b) FIDELITY: baseline_rtg == §0 VAL grid
    if a.baseline_ref and Path(a.baseline_ref).exists() and "baseline_rtg" in grids:
        ref = pd.read_csv(a.baseline_ref)
        key = ["subject", "mag_pct", "pen_mult"]
        m = grids["baseline_rtg"].merge(ref, on=key, suffixes=("", "_ref"))
        d = max(float((m[c] - m[f"{c}_ref"]).abs().max()) for c in ["tp", "fp", "fp_per_day"])
        print(f"[FIDELITY b] baseline_rtg vs §0 VAL grid: max|Δ(tp,fp,fp/day)| = {d:.4g}  "
              f"-> {'PASS' if d < 1e-6 else 'CHECK (nonzero — investigate)'}")

    rt = reftrue(grids[base_tag])
    print(f"[refTrue] {rt}  (Σ={sum(rt.values())})")

    base = shared_at_budget(grids[base_tag], rt, B_BAL)
    print(f"\n{'candidate':13}{'@B=40 cell':>13}{'sens':>7}{'prec':>7}{'F1':>7}{'FP/d':>7}"
          f"{'|':>3}{'@B=75 F1':>9}{'FP/d':>7}{'  G2(F1@40≥base)':>18}")
    rows = []
    for tag, df in grids.items():
        c40 = shared_at_budget(df, rt, B_BAL)
        c75 = shared_at_budget(df, rt, B_HI)
        g2 = "" if tag == base_tag else ("PASS" if c40["f1"] >= base["f1"] else "FAIL")
        cell = f"m{int(c40['mag'])}/p{c40['pen']}"
        print(f"{tag:13}{cell:>13}{c40['sens']:7.3f}{c40['prec']:7.3f}{c40['f1']:7.3f}"
              f"{c40['fpday']:7.1f}{'|':>3}{c75['f1']:9.3f}{c75['fpday']:7.1f}{g2:>18}")
        rows.append(dict(candidate=tag, cell_B40=cell,
                         sens_B40=round(c40["sens"], 3), prec_B40=round(c40["prec"], 3),
                         f1_B40=round(c40["f1"], 3), fpday_B40=round(c40["fpday"], 1),
                         f1_B75=round(c75["f1"], 3), fpday_B75=round(c75["fpday"], 1), G2=g2))
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(a.out, index=False)
    print(f"\n[written] {a.out}")
    print("G2 gate = event F1@B=40 (VAL). PASS candidates are eligible for one-shot TEST; "
          f"(bar = {base_tag}). PRIMARY headline = rlg per Amendment A1.")


if __name__ == "__main__":
    main()
