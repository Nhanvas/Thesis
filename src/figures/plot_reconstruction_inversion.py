"""
================================================================================
 plot_reconstruction_inversion.py -- Fig 2.8 reconstruction error, two patients
================================================================================
Interictal vs ictal distributions of the reconstruction-branch z-score, for one
validation subject where it behaves as expected (chb11, AUROC 0.8517) and one
where it is fully inverted (chb10, AUROC 0.2680). docs/VERIFIED_NUMBERS.md §6.2
and the brief require validation subjects here, not a held-out one, because this
figure illustrates a design decision made before the held-out set was touched.

Source: results/phaseB/tier2/ens_val_tf/components/zrecon_{chb10,chb11}_{inter,ictal}.npy
-- the reconstruction-branch component z-scores that feed the ensemble. Recomputing
AUROC from these arrays reproduces recon_auroc in results/phaseB/E2_latent_val.csv
to four decimals (checked below); that is the source-of-truth cross-check for using
this exact pair of arrays.
"""
import argparse
from pathlib import Path
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.metrics import roc_auc_score

sys.path.insert(0, str(Path(__file__).parent))
from palette import INTERICTAL, ICTAL, apply_rc

EXPECTED_AUROC = {"chb10": 0.2680, "chb11": 0.8517}


def load(component_dir, subj):
    inter = np.load(Path(component_dir) / f"zrecon_{subj}_inter.npy")
    ictal = np.load(Path(component_dir) / f"zrecon_{subj}_ictal.npy")
    return inter, ictal


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--component_dir", default="results/phaseB/tier2/ens_val_tf/components")
    ap.add_argument("--out_dir", default="figures")
    a = ap.parse_args()

    apply_rc()

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.6))
    tags = {"chb11": "normal direction — ictal shifts right of interictal",
            "chb10": "inverted — ictal shifts left of interictal"}

    print("[Fig 2.8] reconstruction-branch AUROC check against results/phaseB/E2_latent_val.csv:")
    for ax, subj in zip(axes, ["chb11", "chb10"]):
        inter, ictal = load(a.component_dir, subj)
        y = np.concatenate([np.zeros(len(inter)), np.ones(len(ictal))])
        s = np.concatenate([inter, ictal])
        auroc = roc_auc_score(y, s)
        exp = EXPECTED_AUROC[subj]
        print(f"  {subj}: computed={auroc:.4f}  E2_latent_val.csv={exp:.4f}")
        if round(auroc, 4) != round(exp, 4):
            raise ValueError(f"{subj}: reconstruction AUROC {auroc:.4f} does not match "
                             f"E2_latent_val.csv {exp:.4f} -- stop, wrong arrays")

        bins = np.linspace(min(inter.min(), ictal.min()), max(inter.max(), ictal.max()), 45)
        ax.hist(inter, bins=bins, density=True, alpha=0.6, color=INTERICTAL,
               label=f"interictal (n={len(inter)})")
        ax.hist(ictal, bins=bins, density=True, alpha=0.6, color=ICTAL,
               label=f"ictal (n={len(ictal)})")
        ax.axvline(np.median(inter), color=INTERICTAL, lw=1.2, ls="--")
        ax.axvline(np.median(ictal), color=ICTAL, lw=1.2, ls="--")
        ax.set_title(f"{subj} — {tags[subj]}\nreconstruction AUROC = {auroc:.4f}", fontsize=9.5)
        ax.set_xlabel("reconstruction-branch z-score")
        ax.legend(fontsize=8)
    axes[0].set_ylabel("density")

    fig.suptitle("Fig 2.8 — reconstruction error in two validation patients: "
                "expected direction (chb11) vs inversion (chb10)", fontsize=11, y=1.03)
    fig.tight_layout()

    out_dir = Path(a.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_dir / "fig2_8_reconstruction_inversion.png", bbox_inches="tight")
    plt.close(fig)
    print(f"  [saved] {(out_dir / 'fig2_8_reconstruction_inversion.png').resolve()}")


if __name__ == "__main__":
    main()
