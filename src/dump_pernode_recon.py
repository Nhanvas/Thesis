#!/usr/bin/env python
"""
dump_pernode_recon.py — regenerate per-node GAE reconstruction error from the CANONICAL
rlg checkpoint. ATTRIBUTION_SPEC §2 + Amendment A2 (D1/D4).

Deterministic dump only: no thresholds, no selection, no tuning. Writes [n_win, 18] float32
+ a provenance manifest (checkpoint SHA-256, shapes, timestamp).

Usage (from repo ROOT):
    python src/dump_pernode_recon.py --smoke                 # 1 subject, timing + self-checks
    python src/dump_pernode_recon.py --seed 42               # full 11 subjects
    python src/dump_pernode_recon.py --seed 42 --compare_legacy data/pernode
"""
import argparse, hashlib, json, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT / "src", ROOT / "src" / "phaseB", ROOT / "src" / "retrain", ROOT / "src" / "dataprep"):
    if p.is_dir() and str(p) not in sys.path:
        sys.path.insert(0, str(p))

import numpy as np
import torch
from gae_joint import load_checkpoint, score_windows, N_CH

TEST_SUBJ = ["chb03", "chb06", "chb13", "chb14", "chb15", "chb16", "chb17", "chb18"]
VAL_SUBJ  = ["chb10", "chb11", "chb22"]
SPLITS    = ["interictal", "ictal"]


def die(msg):
    print(f"\n[FATAL] {msg}\n", file=sys.stderr)
    sys.exit(1)


def sha256(path, nbytes=None):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read() if nbytes is None else f.read(nbytes))
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--proc_dir", default=str(ROOT / "data" / "processed"))
    ap.add_argument("--out_root", default=str(ROOT / "data" / "pernode_v2"))
    ap.add_argument("--batch_size", type=int, default=256)
    ap.add_argument("--smoke", action="store_true", help="chb13 only, for timing + self-check")
    ap.add_argument("--compare_legacy", default=None, help="dir with legacy *_pernode.npy")
    a = ap.parse_args()

    proc = Path(a.proc_dir)
    ckpt = ROOT / "data" / "models_retrain" / f"gae_joint_seed{a.seed}.pt"
    out_dir = Path(a.out_root) / f"seed{a.seed}"
    out_dir.mkdir(parents=True, exist_ok=True)

    subjects = ["chb13"] if a.smoke else TEST_SUBJ + VAL_SUBJ

    # ---------- PRE-FLIGHT (fail fast) ----------
    if not proc.is_dir():
        die(f"proc_dir not found: {proc}")
    if not ckpt.is_file():
        die(f"checkpoint not found: {ckpt}")
    missing = []
    for s in subjects:
        for sp in SPLITS:
            for f in (proc / f"{s}_{sp}_adjs_topk20.npy", proc / f"{s}_{sp}_features.npy"):
                if not f.is_file():
                    missing.append(str(f))
    if missing:
        die("missing inputs:\n  " + "\n  ".join(missing))

    dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = load_checkpoint(ckpt, dev)
    bmax = model.encoder.conv1.bias.abs().max().item()
    ck_sha = sha256(ckpt)
    print(f"device={dev}  ckpt={ckpt.name}  sha256={ck_sha[:16]}...  bias_fp={bmax:.4f}")
    if bmax <= 0.5:
        die(f"bias fingerprint {bmax:.4f} <= 0.5 — random-init / wrong checkpoint")

    # ---------- SELF-CHECK: per-node mean must equal the scalar score ----------
    sl_adj = proc / "chb13_interictal_adjs_topk20.npy"
    sl_feat = proc / "chb13_interictal_features.npy"
    pn0 = score_windows(model, sl_adj, sl_feat, dev, a.batch_size, per_node=True)[:a.batch_size]
    sc0 = score_windows(model, sl_adj, sl_feat, dev, a.batch_size, per_node=False)[:a.batch_size]
    err = float(np.max(np.abs(pn0.mean(axis=1) - sc0)))
    print(f"self-check max|mean_node - scalar| = {err:.2e}  (must be < 1e-5)")
    if err >= 1e-5:
        die("per-node decomposition inconsistent with scalar score")

    # ---------- DUMP ----------
    manifest = {"checkpoint": str(ckpt.relative_to(ROOT)), "checkpoint_sha256": ck_sha,
                "bias_fingerprint": round(bmax, 6), "seed": a.seed, "device": str(dev),
                "self_check_max_abs_err": err, "batch_size": a.batch_size,
                "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "test_subjects": TEST_SUBJ, "val_subjects_tau_only": VAL_SUBJ, "arrays": {}}

    for s in subjects:
        for sp in SPLITS:
            t0 = time.time()
            pn = score_windows(model, proc / f"{s}_{sp}_adjs_topk20.npy",
                               proc / f"{s}_{sp}_features.npy", dev, a.batch_size, per_node=True)
            assert pn.ndim == 2 and pn.shape[1] == N_CH, f"bad shape {pn.shape}"
            if not np.isfinite(pn).all():
                die(f"non-finite values in {s}_{sp}")
            fp = out_dir / f"{s}_{sp}_pernode.npy"
            np.save(fp, pn.astype(np.float32))
            manifest["arrays"][f"{s}_{sp}"] = {
                "file": fp.name, "shape": list(pn.shape),
                "mean": float(pn.mean()), "median": float(np.median(pn)),
                "p99": float(np.percentile(pn, 99)), "sec": round(time.time() - t0, 1)}
            print(f"  {s}_{sp:<10} {str(pn.shape):>14}  {time.time()-t0:6.1f}s  -> {fp.name}")

    # ---------- LEGACY COMPARISON (provenance evidence, not a gate) ----------
    if a.compare_legacy:
        leg = Path(a.compare_legacy)
        cmp_rows = {}
        for s in subjects:
            for sp in SPLITS:
                f = leg / f"{s}_{sp}_pernode.npy"
                if not f.is_file():
                    cmp_rows[f"{s}_{sp}"] = "ABSENT"; continue
                old = np.load(f)
                new = np.load(out_dir / f"{s}_{sp}_pernode.npy")
                if old.shape != new.shape:
                    cmp_rows[f"{s}_{sp}"] = f"SHAPE {old.shape} vs {new.shape}"; continue
                r = float(np.corrcoef(old.ravel(), new.ravel())[0, 1])
                cmp_rows[f"{s}_{sp}"] = {"corr": round(r, 6),
                                         "max_abs_diff": float(np.abs(old - new).max())}
                print(f"  LEGACY {s}_{sp:<10} corr={r:.6f}  maxdiff={np.abs(old-new).max():.3e}")
        manifest["legacy_comparison"] = cmp_rows

    (out_dir / "MANIFEST.json").write_text(json.dumps(manifest, indent=2))
    print(f"\nDONE -> {out_dir}\nmanifest: {out_dir/'MANIFEST.json'}")


if __name__ == "__main__":
    main()