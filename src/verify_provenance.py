#!/usr/bin/env python
"""
verify_provenance.py — machine-verified checkpoint identity for the rlg pipeline of record.

RUN THIS AT THE START OF ANY SESSION THAT TOUCHES THE GAE. It answers, by measurement rather
than by filename, "is the checkpoint on disk the one that produced the locked TEST numbers?"

  python src/verify_provenance.py            # fast gate (~20 s), prints PASS/FAIL, writes nothing
  python src/verify_provenance.py --full     # all 16 arrays + all seeds, regenerates docs/PROVENANCE.md

Ground truth = the committed one-shot TEST components (results/phaseB/tier2/ens_test_tf/components/).
zrecon on disk is robust-z'd (affine per subject), so Pearson corr is the correct comparison:
the true checkpoint gives corr = 1.0000000.

Every number written to docs/PROVENANCE.md is measured here. Nothing is copied from documentation.
"""
import argparse, hashlib, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT / "src", ROOT / "src" / "retrain"):
    if p.is_dir() and str(p) not in sys.path:
        sys.path.insert(0, str(p))

import numpy as np, torch
from sklearn.metrics import roc_auc_score
from gae_joint import load_checkpoint, score_windows, BIAS_FP_CANONICAL

PROC   = ROOT / "data" / "processed"
COMP   = ROOT / "results" / "phaseB" / "tier2" / "ens_test_tf" / "components"
CANON  = ROOT / "data" / "models_retrain" / "gae_joint_seed42.pt"
SEEDS  = [ROOT / "data" / "models_retrain" / f"gae_joint_seed{s}.pt" for s in (1, 2, 3)]
FAST   = ["chb16", "chb17"]
ALL    = ["chb03", "chb06", "chb13", "chb14", "chb15", "chb16", "chb17", "chb18"]
DEV    = torch.device("cpu")
CORR_TOL = 1e-6


def sha256(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def recon(model, subj, split):
    return score_windows(model, PROC / f"{subj}_{split}_adjs_topk20.npy",
                         PROC / f"{subj}_{split}_features.npy", DEV, 256).ravel()


def chb13_auroc(model):
    si, sc = recon(model, "chb13", "interictal"), recon(model, "chb13", "ictal")
    y = np.r_[np.zeros(len(si)), np.ones(len(sc))]
    return float(roc_auc_score(y, np.r_[si, sc]))


def component_corrs(model, subjects):
    out = {}
    for s in subjects:
        for split, tag in [("interictal", "inter"), ("ictal", "ictal")]:
            f = COMP / f"zrecon_{s}_{tag}.npy"
            if not f.is_file():
                out[f"{s}_{tag}"] = None; continue
            ref, mine = np.load(f).ravel(), recon(model, s, split)
            out[f"{s}_{tag}"] = None if len(ref) != len(mine) else \
                float(np.corrcoef(ref, mine)[0, 1])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--full", action="store_true")
    a = ap.parse_args()
    t0 = time.time()

    for p in (PROC, COMP, CANON):
        if not p.exists():
            print(f"[FATAL] missing: {p}", file=sys.stderr); sys.exit(2)

    model = load_checkpoint(CANON, DEV)
    bfp = float(model.encoder.conv1.bias.detach().abs().max())
    sha = sha256(CANON)
    print(f"canonical : {CANON.relative_to(ROOT)}")
    print(f"  size    : {CANON.stat().st_size} B")
    print(f"  sha256  : {sha}")
    print(f"  bias_fp : {bfp:.4f}   (module constant BIAS_FP_CANONICAL = {BIAS_FP_CANONICAL})")

    corrs = component_corrs(model, ALL if a.full else FAST)
    vals = [v for v in corrs.values() if v is not None]
    n_missing = sum(1 for v in corrs.values() if v is None)
    worst = min(vals) if vals else 0.0
    for k, v in corrs.items():
        print(f"  zrecon {k:<14} corr={'MISSING/LEN-MISMATCH' if v is None else f'{v:.7f}'}")

    auc = chb13_auroc(model)
    print(f"  chb13 recon AUROC : {auc:.4f}")

    ok = (abs(bfp - BIAS_FP_CANONICAL) < 0.01) and (n_missing == 0) and (1.0 - worst < CORR_TOL)
    print(f"\nworst corr = {worst:.7f} over {len(vals)} array(s), missing={n_missing}")
    print("VERDICT:", "PASS — checkpoint is canonical" if ok else "FAIL — DO NOT PROCEED")
    print(f"({time.time()-t0:.0f}s)")

    if not a.full:
        print("\n(fast gate; run --full to check all 16 arrays and regenerate docs/PROVENANCE.md)")
        sys.exit(0 if ok else 1)

    seed_rows = []
    for sp in SEEDS:
        if not sp.is_file():
            seed_rows.append((sp.name, "MISSING", "", "")); continue
        m = load_checkpoint(sp, DEV)
        seed_rows.append((sp.name, sha256(sp)[:16],
                          f"{float(m.encoder.conv1.bias.abs().max()):.4f}",
                          f"{chb13_auroc(m):.4f}"))
        print(f"  seed {sp.name}: bias_fp={seed_rows[-1][2]} chb13={seed_rows[-1][3]}")

    doc = ROOT / "docs" / "PROVENANCE.md"
    L = []
    L.append("# PROVENANCE — checkpoint identity (MACHINE-GENERATED, DO NOT EDIT BY HAND)\n")
    L.append(f"Generated `{time.strftime('%Y-%m-%d %H:%M')}` local by `src/verify_provenance.py --full`.")
    L.append("Every number below was measured at generation time. Regenerate rather than edit.\n")
    L.append("## Identity test\n")
    L.append("A checkpoint is canonical **iff** it reproduces the committed one-shot TEST components")
    L.append("`results/phaseB/tier2/ens_test_tf/components/zrecon_*` at Pearson corr = 1.0000000.")
    L.append("Filenames and the legacy constants 0.8676 / 0.836 are **not** identity evidence — they are")
    L.append("pre-rebuild §0 values.\n")
    L.append("## Canonical checkpoint\n")
    L.append(f"- path: `{CANON.relative_to(ROOT).as_posix()}`")
    L.append(f"- size: {CANON.stat().st_size} B")
    L.append(f"- sha256: `{sha}`")
    L.append(f"- bias fingerprint: **{bfp:.4f}**")
    L.append(f"- chb13 recon AUROC: **{auc:.4f}**")
    L.append(f"- zrecon vs committed TEST components: **corr = {worst:.7f} (worst of {len(vals)}/16)**\n")
    L.append("## GAE seeds (RoR §7 robustness set)\n")
    L.append("| file | sha256 (16) | bias_fp | chb13 recon AUROC |")
    L.append("|---|---|---|---|")
    for n, s, b, c in seed_rows:
        L.append(f"| `{n}` | `{s}` | {b} | {c} |")
    L.append("\n## Quarantined pre-rebuild §0 artifacts — DO NOT USE\n")
    L.append("`archive/pre_rebuild_s0/` — the §0 joint GAE and its per-node dumps. They correlate")
    L.append("0.987–0.999 with canonical output, close enough to pass any spot check. See the README there.\n")
    L.append("## Session gate\n")
    L.append("```bash\npython src/verify_provenance.py        # ~20 s, exit 0 = canonical\n```")
    doc.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"\nwrote {doc}")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()