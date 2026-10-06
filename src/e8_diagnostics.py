#!/usr/bin/env python
"""
e8_diagnostics.py -- read-only diagnostics of E8 (15 non-test subjects). Reads committed E8
outputs, the v2 checkpoints' json/loss files and the v2 data set; recomputes nothing new.
Writes only results/e8_gae_v2/diag/ (never figures/, which holds the 21 report PNGs).

  1 loss_curves.png         train / validation loss per v2 checkpoint (+ meta table)
  2 score_distributions.png locked V1 vs v2 clean seed 42 (frozen score V2_LW): ensemble score
                            of seizure / flagged non-seizure / clean background windows, pooled
                            over the 15 subjects (per-patient robust-z, as the detector sees it)
  3 per_subject_frozen.csv  TP / seizures / FP / FA per day per subject at the frozen cell
                            (smooth 15, top 2 %) for V1 and for each v2 clean seed
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT / "src", ROOT / "src" / "retrain"):
    sys.path.insert(0, str(p))
import e8_gae_v2_eval as E8      # noqa: E402
import ensemble_recipe as ER     # noqa: E402
from sklearn.covariance import LedoitWolf  # noqa: E402

OUT = ROOT / "results" / "e8_gae_v2" / "diag"
OUT.mkdir(parents=True, exist_ok=True)
CK = ROOT / "data" / "models_v2"


def rz(x, ok):
    m = np.median(x[ok]); s = np.median(np.abs(x[ok] - m)) + 1e-9
    return (x - m) / s


def main():
    # 1 loss curves + meta
    metas = []
    fig, ax = plt.subplots(1, 2, figsize=(11, 4))
    for js in sorted(CK.glob("gae_v2_*_seed*.json")):
        if "SMOKE" in js.name:
            continue
        m = json.loads(js.read_text())
        L = np.load(js.with_name(js.stem + "_loss.npz"))
        lab = f"{m['variant']} s{m['seed']}"
        ax[0].plot(L["train"], label=lab); ax[1].plot(L["val"], label=lab)
        metas.append(dict(ckpt=js.stem, n_train=sum(m["n_train"].values()), n_val=sum(m["n_val"].values()),
                          final_train=round(m["final_train"], 6), final_val=round(m["final_val"], 6),
                          val_sanity_auroc=m["val_sanity_auroc"], elapsed_h=round(m["elapsed_s"] / 3600, 2)))
    for a, t in zip(ax, ("train loss", "validation loss")):
        a.set_title(t); a.set_xlabel("epoch"); a.set_yscale("log"); a.legend(fontsize=8)
    fig.tight_layout(); fig.savefig(OUT / "loss_curves.png", dpi=130); plt.close(fig)
    pd.DataFrame(metas).to_csv(OUT / "checkpoint_meta.csv", index=False)

    # 2 score distributions (V1 vs clean seed 42 V2_LW)
    groups = {"V1": {"seizure": [], "flagged": [], "clean bg": []},
              "v2 clean s42": {"seizure": [], "flagged": [], "clean bg": []}}
    for s in E8.SUBJS:
        z = np.load(E8.DATA / f"{s}.npz", allow_pickle=True)
        sc = np.load(E8.OUT / "scores" / f"{s}.npz")
        d = E8.d_for_grid(z); n = len(d["is_ictal"]); ok = ~d["is_signal_loss"]; idx = sc["idx"]

        def full(v):
            o = np.full(n, np.nan); o[idx] = v; o[~ok] = np.nanmedian(v); return o
        zg = rz(full(z["zgamma_raw"][idx].astype(float)), ok)
        out = {}
        for name, rk, lk in (("V1", "v1_recon", "v1_lat"), ("v2 clean s42", "clean_seed42_recon", "clean_seed42_lat")):
            lat = sc[lk]
            l = rz(full(LedoitWolf().fit(lat).mahalanobis(lat)), ok)
            out[name] = np.asarray(ER.build_ensemble_subset(
                {"zrecon": rz(full(sc[rk]), ok), "zlatent": l, "zgamma": zg}, ER.CANDIDATES["rlg"]), float)
        ict = d["is_ictal"] & ok
        base = ~d["is_ictal"] & ~d["is_buffer"] & ok
        for name, v in out.items():
            groups[name]["seizure"].append(v[ict])
            groups[name]["flagged"].append(v[base & d["is_artifact"]])
            groups[name]["clean bg"].append(v[base & ~d["is_artifact"]])
    fig, ax = plt.subplots(1, 2, figsize=(11, 4), sharey=True)
    rows = []
    for a, (name, g) in zip(ax, groups.items()):
        for k, col in (("clean bg", "tab:gray"), ("flagged", "tab:orange"), ("seizure", "tab:red")):
            v = np.concatenate(g[k]); v = v[np.isfinite(v)]
            a.hist(np.clip(v, -5, 30), bins=120, density=True, histtype="step", color=col, label=f"{k} (n={len(v)})")
            rows.append(dict(score=name, group=k, n=len(v), median=np.median(v), p90=np.percentile(v, 90),
                             p98=np.percentile(v, 98)))
        a.set_title(name); a.set_xlabel("ensemble score (per-patient robust z, clipped)"); a.legend(fontsize=8)
    ax[0].set_ylabel("density"); fig.tight_layout(); fig.savefig(OUT / "score_distributions.png", dpi=130); plt.close(fig)
    pd.DataFrame(rows).round(3).to_csv(OUT / "score_distribution_stats.csv", index=False)

    # 3 per subject at the frozen cell
    gr = pd.read_csv(E8.OUT / "grid_per_subject.csv")
    f = gr[(gr.smooth == 15) & (gr.top == 0.02) & (gr.score.isin(["V1"]) | gr.score.str.startswith("clean_seed"))
           & (gr.score.str.endswith("V2_LW") | (gr.score == "V1"))]
    f = f.assign(fa_day=(f.fp / f.nonict_h * 24).round(1))[["subject", "score", "tp", "n_ref", "fp", "fa_day"]]
    f.to_csv(OUT / "per_subject_frozen.csv", index=False)
    piv = f.pivot_table(index="subject", columns="score", values=["tp", "fa_day"])
    print(pd.DataFrame(metas).to_string(index=False))
    print(pd.DataFrame(rows).round(3).to_string(index=False))
    print(piv.to_string())


if __name__ == "__main__":
    main()
