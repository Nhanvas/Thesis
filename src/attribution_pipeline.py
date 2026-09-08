#!/usr/bin/env python
"""
attribution_pipeline.py — SINGLE SOURCE for the channel-attribution study.

Consolidates nine scripts written on 2026-09-01 (dump_pernode_recon, build_seizure_blocks,
build_label_draft, attribution_score_seizures, attribution_diagnostics,
attribution_synthetic_check, attribution_synthetic_spread, attribution_score_labels,
attribution_label_diversity) into one module with sub-commands. Logic is unchanged: outputs are
byte-identical to the separate scripts.

Governed by docs/ATTRIBUTION_SPEC.md (v2 + Amendment A2, decisions D1-D8).
Framing: XAI for the GAE reconstruction branch. NOT seizure localization, NOT SOZ.

Canonical checkpoint: data/models_retrain/gae_joint_seed42.pt
  sha256 dea06cb533df1c7d0520ae21c4cbb1b8a938297f937366bc9915b040726ea108
  bias fingerprint 1.1597 | chb13 recon AUROC 0.8319
  verified corr = 1.0000000 vs results/phaseB/tier2/ens_test_tf/components/zrecon_* (16/16)
Do NOT use archive/pre_rebuild_s0/ artifacts: they are the pre-rebuild S0 model and correlate
0.987-0.999 with canonical output, which is close enough to pass a spot check and be wrong.

--------------------------------------------------------------------------------------------
SUB-COMMANDS (run from repo ROOT)

  dump      --seed 42            regenerate per-node recon error -> data/pernode_v2/seed{N}/
  blocks    --edf_root --summary_dir
                                 map ictal rows -> seizures      -> seizure_blocks.csv,
                                                                    ictal_row_to_seizure.csv
  labels                         convert v5 reader labels        -> labels/ictal_channels_DRAFT.csv
  score                          per-seizure 18-ch score+rank    -> attribution_scores.csv
  diag                           seed/bias/C1 diagnostics        -> attribution_diagnostics.csv
  synth                          synthetic sanity, gates G-S1..3 -> synthetic_sanity.csv
  spread                         gate G-S4' (D6.1)               -> synthetic_spread.csv
  eval                           score vs labels                 -> attribution_summary.csv,
                                                                    attribution_perseizure.csv
  labeldiv                       can labels test per-seizure?    -> label_diversity.csv

  all                            score -> diag -> synth -> spread -> eval -> labeldiv
                                 (assumes dump/blocks/labels already ran)

Prerequisite for every sub-command that touches the GAE: python src/verify_provenance.py
--------------------------------------------------------------------------------------------
"""
import argparse
import csv
import hashlib
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for _p in (ROOT / "src", ROOT / "src" / "retrain", ROOT / "src" / "phaseB",
           ROOT / "src" / "dataprep"):
    if _p.is_dir() and str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import numpy as np

# ============================================================================
# CONSTANTS
# ============================================================================
TEST_SUBJ = ["chb03", "chb06", "chb13", "chb14", "chb15", "chb16", "chb17", "chb18"]
VAL_SUBJ = ["chb10", "chb11", "chb22"]
SPLITS = ["interictal", "ictal"]
SEEDS = [42, 1, 2, 3]
EXPECTED_TEST_SEIZURES = 76

CH = ["FP1-F7", "F7-T7", "T7-P7", "P7-O1", "FP1-F3", "F3-C3", "C3-P3", "P3-O1",
      "FP2-F4", "F4-C4", "C4-P4", "P4-O2", "FP2-F8", "F8-T8", "T8-P8", "P8-O2",
      "FZ-CZ", "CZ-PZ"]
IDX = {c: i for i, c in enumerate(CH)}
NCH = 18

PROC = ROOT / "data" / "processed"
PNR = ROOT / "data" / "pernode_v2"
OUT = ROOT / "results" / "attribution_v6"
LABDIR = OUT / "labels"
V5LAB = ROOT / "results" / "attribution_v5" / "labels" / "labels_ALL_FINAL.csv"

# synthetic grid (D6 / D6.1) -- pre-registered, do not tune
ALPHAS = [1.0, 1.25, 1.5, 2.0, 3.0]
SIZES = [1, 2, 4, 8, 12]
SPREAD_ALPHA, SPREAD_KS = 2.0, [1, 2, 4, 12, 18]
R, NPERM, SEED = 200, 1000, 42
NBOOT = 1000


def die(msg):
    print(f"\n[FATAL] {msg}\n", file=sys.stderr)
    sys.exit(1)


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


# ============================================================================
# SHARED METRIC HELPERS
# ============================================================================
def auroc18(y, s):
    """AUROC over the 18 channels of one seizure. Undefined if y is all-0 or all-1."""
    r = np.empty(NCH)
    r[np.argsort(s)] = np.arange(1, NCH + 1)
    p, n = y.sum(), NCH - y.sum()
    return np.nan if p == 0 or n == 0 else (r[y == 1].sum() - p * (p + 1) / 2) / (p * n)


def ap18(y, s):
    o = np.argsort(-s, kind="mergesort")
    yy = y[o]
    return float((np.cumsum(yy) / np.arange(1, NCH + 1) * yy).sum() / max(yy.sum(), 1))


def rec_at_S(y, s):
    k = int(y.sum())
    return float(y[np.argsort(-s)[:k]].sum() / k)


def spread_one(s):
    """Normalised entropy of a non-negative score vector; 1 = perfectly uniform."""
    p = np.clip(s, 1e-12, None)
    p = p / p.sum()
    return float(-(p * np.log(p)).sum() / np.log(NCH))


def spreads(S):
    P = np.clip(S, 1e-12, None)
    P = P / P.sum(1, keepdims=True)
    return -(P * np.log(P)).sum(1) / np.log(S.shape[1])


def macro_auroc_rows(S, Y):
    """Vectorised macro AUROC over rows. No ties expected in S (float recon error)."""
    Rn, C = S.shape
    order = np.argsort(S, axis=1)
    ranks = np.empty_like(order)
    ranks[np.arange(Rn)[:, None], order] = np.arange(1, C + 1)[None, :]
    npos = Y.sum(1)
    nneg = C - npos
    sr = (ranks * Y).sum(1)
    return float(np.mean((sr - npos * (npos + 1) / 2) / (npos * nneg)))


def macro_ap_rows(S, Y):
    aps = []
    for s, y in zip(S, Y):
        o = np.argsort(-s, kind="mergesort")
        yy = y[o]
        prec = np.cumsum(yy) / np.arange(1, len(yy) + 1)
        aps.append((prec * yy).sum() / max(yy.sum(), 1))
    return float(np.mean(aps))


def macro_recall_rows(S, Y):
    rec = []
    for s, y in zip(S, Y):
        k = int(y.sum())
        rec.append(y[np.argsort(-s)[:k]].sum() / k)
    return float(np.mean(rec))


def bootstrap_mean(vals, rng):
    v = np.asarray(vals, float)
    m = [np.mean(rng.choice(v, len(v), replace=True)) for _ in range(NBOOT)]
    return float(v.mean()), float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))


def write_csv(path, rows):
    if not rows:
        die(f"no rows to write for {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {path}  ({len(rows)} rows)")


# ============================================================================
# LOADERS
# ============================================================================
def load_scores(seed=None, agg=None):
    """attribution_scores.csv -> {(seed, agg, subject, seizure_idx): ndarray[18]}"""
    f = OUT / "attribution_scores.csv"
    if not f.is_file():
        die(f"missing {f} — run: python src/attribution_pipeline.py score")
    S = {}
    for r in csv.DictReader(open(f)):
        if seed is not None and int(r["seed"]) != seed:
            continue
        if agg is not None and r["agg"] != agg:
            continue
        S.setdefault((int(r["seed"]), r["agg"], r["subject"], int(r["seizure_idx"])),
                     np.zeros(NCH))[int(r["ch_idx"])] = float(r["score"])
    return S


def load_labels():
    """ictal_channels_DRAFT.csv -> {(subject, seizure_idx): {y, kind, nw, nS, chans}}"""
    f = LABDIR / "ictal_channels_DRAFT.csv"
    if not f.is_file():
        die(f"missing {f} — run: python src/attribution_pipeline.py labels")
    lab = {}
    for r in csv.DictReader(open(f)):
        chans = [c for c in r["ictal_channels"].split("|") if c]
        y = np.zeros(NCH, dtype=int)
        for c in chans:
            if c not in IDX:
                die(f"unknown channel {c}")
            y[IDX[c]] = 1
        lab[(r["subject"], int(r["seizure_idx"]))] = {
            "y": y, "kind": r["focal_generalized"], "nw": int(r["n_windows"]),
            "nS": int(r["n_ictal_channels"]), "chans": set(chans)}
    if len(lab) != EXPECTED_TEST_SEIZURES:
        die(f"expected {EXPECTED_TEST_SEIZURES} labels, got {len(lab)}")
    return lab


def load_len_distribution():
    f = OUT / "seizure_blocks.csv"
    if not f.is_file():
        die(f"missing {f} — run: python src/attribution_pipeline.py blocks ...")
    lens = [int(r["n_windows"]) for r in csv.DictReader(open(f)) if r["subject"] in TEST_SUBJ]
    if len(lens) != EXPECTED_TEST_SEIZURES:
        die(f"expected {EXPECTED_TEST_SEIZURES} TEST seizures in {f}, got {len(lens)}")
    return np.array(lens)


# ============================================================================
# 1. dump — per-node reconstruction error from the canonical checkpoint (D1/D4)
# ============================================================================
def cmd_dump(a):
    import torch
    from gae_joint import load_checkpoint, score_windows

    proc = Path(a.proc_dir)
    ckpt = ROOT / "data" / "models_retrain" / f"gae_joint_seed{a.seed}.pt"
    out_dir = Path(a.out_root) / f"seed{a.seed}"
    out_dir.mkdir(parents=True, exist_ok=True)
    subjects = ["chb13"] if a.smoke else TEST_SUBJ + VAL_SUBJ

    if not proc.is_dir():
        die(f"proc_dir not found: {proc}")
    if not ckpt.is_file():
        die(f"checkpoint not found: {ckpt}")
    missing = [str(f) for s in subjects for sp in SPLITS
               for f in (proc / f"{s}_{sp}_adjs_topk20.npy", proc / f"{s}_{sp}_features.npy")
               if not f.is_file()]
    if missing:
        die("missing inputs:\n  " + "\n  ".join(missing))

    dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = load_checkpoint(ckpt, dev)
    bmax = model.encoder.conv1.bias.detach().abs().max().item()
    ck_sha = sha256(ckpt)
    print(f"device={dev}  ckpt={ckpt.name}  sha256={ck_sha[:16]}...  bias_fp={bmax:.4f}")
    if bmax <= 0.5:
        die(f"bias fingerprint {bmax:.4f} <= 0.5 — random-init / wrong checkpoint")

    sl_adj = proc / "chb13_interictal_adjs_topk20.npy"
    sl_feat = proc / "chb13_interictal_features.npy"
    pn0 = score_windows(model, sl_adj, sl_feat, dev, a.batch_size, per_node=True)[:a.batch_size]
    sc0 = score_windows(model, sl_adj, sl_feat, dev, a.batch_size, per_node=False)[:a.batch_size]
    err = float(np.max(np.abs(pn0.mean(axis=1) - sc0)))
    print(f"self-check max|mean_node - scalar| = {err:.2e}  (must be < 1e-5)")
    if err >= 1e-5:
        die("per-node decomposition inconsistent with scalar score")

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
            if pn.ndim != 2 or pn.shape[1] != NCH:
                die(f"bad shape {pn.shape} for {s}_{sp}")
            if not np.isfinite(pn).all():
                die(f"non-finite values in {s}_{sp}")
            fp = out_dir / f"{s}_{sp}_pernode.npy"
            np.save(fp, pn.astype(np.float32))
            manifest["arrays"][f"{s}_{sp}"] = {
                "file": fp.name, "shape": list(pn.shape), "mean": float(pn.mean()),
                "median": float(np.median(pn)), "p99": float(np.percentile(pn, 99)),
                "sec": round(time.time() - t0, 1)}
            print(f"  {s}_{sp:<10} {str(pn.shape):>14}  {time.time()-t0:6.1f}s  -> {fp.name}")

    (out_dir / "MANIFEST.json").write_text(json.dumps(manifest, indent=2))
    print(f"\nDONE -> {out_dir}\nmanifest: {out_dir/'MANIFEST.json'}")


# ============================================================================
# 2. blocks — exact ictal row -> seizure mapping
# ============================================================================
def _resolve_summary(summary_dir, subj):
    for ext in (".txt", ".md"):
        f = summary_dir / f"{subj}-summary{ext}"
        if f.is_file():
            return f
    die(f"summary not found for {subj} (tried .txt/.md) in {summary_dir}")


def _blocks_for_subject(subj, edf_root, summary_dir):
    import preprocessing as pp
    seizure_map = pp.parse_summary(_resolve_summary(summary_dir, subj))
    n_sz_in_summary = sum(len(v) for v in seizure_map.values())

    subj_dir = edf_root / subj
    if not subj_dir.is_dir():
        die(f"EDF dir not found: {subj_dir}")

    registry, rows, skipped = [], [], []
    idx = 0
    for edf_path in sorted(subj_dir.glob("*.edf")):
        raw = pp.open_edf(edf_path)
        if raw is None:
            skipped.append(edf_path.name)
            continue
        seizure_list = seizure_map.get(edf_path.name, [])
        n_samples = int(raw.n_times)
        n_seconds = n_samples // pp.FS
        n_windows = n_samples // pp.WIN_SAMPLES
        labels = pp.build_labels(n_seconds, seizure_list)

        local = []
        for (on, off) in sorted(seizure_list):
            registry.append({"edf": edf_path.name, "onset_s": on, "offset_s": off})
            local.append((len(registry) - 1, on, off))

        for i in range(n_windows):
            s0, s1 = i * pp.WIN_S, i * pp.WIN_S + pp.WIN_S
            if int(labels[s0:s1].max()) == 1:
                best, bov = None, -1
                for gid, on, off in local:
                    ov = max(0, min(s1, off) - max(s0, on))
                    if ov > bov:
                        bov, best = ov, gid
                rows.append({"row": idx, "edf": edf_path.name, "win_i": i,
                             "start_s": s0, "sz": best, "overlap_s": bov})
                idx += 1
        del raw
    return rows, registry, n_sz_in_summary, skipped


def cmd_blocks(a):
    edf_root, summary_dir = Path(a.edf_root), Path(a.summary_dir)
    proc = Path(a.proc_dir)
    OUT.mkdir(parents=True, exist_ok=True)
    for d, nm in [(edf_root, "edf_root"), (summary_dir, "summary_dir"), (proc, "proc_dir")]:
        if not d.is_dir():
            die(f"{nm} not found: {d}")

    blocks, rowmap, fails, n_test_sz = [], [], [], 0
    for subj in TEST_SUBJ + VAL_SUBJ:
        rows, registry, n_summary, skipped = _blocks_for_subject(subj, edf_root, summary_dir)
        arr = proc / f"{subj}_ictal.npy"
        if not arr.is_file():
            die(f"missing {arr}")
        n_arr = int(np.load(arr, mmap_mode="r").shape[0])

        status = "OK" if len(rows) == n_arr else "MISMATCH"
        if status == "MISMATCH":
            fails.append(f"{subj}: mapped {len(rows)} rows vs array {n_arr}")
        if len(registry) != n_summary:
            fails.append(f"{subj}: {n_summary - len(registry)} seizure(s) lost in "
                         f"skipped EDFs {skipped}")

        by_sz = {}
        for r in rows:
            by_sz.setdefault(r["sz"], []).append(r["row"])
        empty = [g for g in range(len(registry)) if g not in by_sz]

        for g, meta in enumerate(registry):
            rr = sorted(by_sz.get(g, []))
            blocks.append({"subject": subj, "seizure_idx": g, "edf_file": meta["edf"],
                           "onset_s": meta["onset_s"], "offset_s": meta["offset_s"],
                           "dur_s": meta["offset_s"] - meta["onset_s"], "n_windows": len(rr),
                           "row_start": rr[0] if rr else -1, "row_end": rr[-1] if rr else -1,
                           "contiguous": bool(rr) and (rr[-1] - rr[0] + 1 == len(rr))})
        for r in rows:
            rowmap.append({"subject": subj, "row": r["row"], "seizure_idx": r["sz"],
                           "edf_file": r["edf"], "start_s": r["start_s"],
                           "overlap_s": r["overlap_s"]})

        if subj in TEST_SUBJ:
            n_test_sz += len(registry)
        print(f"  {subj:<7} seizures={len(registry):>2} (summary {n_summary:>2})  "
              f"rows mapped={len(rows):>5} / array={n_arr:<5} [{status}]"
              + (f"  EMPTY_SZ={empty}" if empty else "")
              + (f"  SKIPPED_EDF={len(skipped)}" if skipped else ""))

    write_csv(OUT / "seizure_blocks.csv", blocks)
    write_csv(OUT / "ictal_row_to_seizure.csv", rowmap)

    nw = [b["n_windows"] for b in blocks if b["subject"] in TEST_SUBJ]
    print(f"\nTEST seizures registered = {n_test_sz} (expects {EXPECTED_TEST_SEIZURES})")
    print(f"TEST windows/seizure: min={min(nw)} p25={int(np.percentile(nw,25))} "
          f"median={int(np.median(nw))} max={max(nw)}  |  n_sz with <3 windows = "
          f"{sum(1 for v in nw if v < 3)}")
    if n_test_sz != EXPECTED_TEST_SEIZURES:
        fails.append(f"TEST seizure count {n_test_sz} != {EXPECTED_TEST_SEIZURES}")
    if fails:
        die("GATE FAILED:\n  " + "\n  ".join(fails))
    print("GATE PASSED — row->seizure map is exact.")


# ============================================================================
# 3. labels — deterministic conversion of the v5 reader pass (D2)
# ============================================================================
def cmd_labels(a):
    if not V5LAB.is_file():
        die(f"missing {V5LAB}")
    blkf = OUT / "seizure_blocks.csv"
    if not blkf.is_file():
        die(f"missing {blkf}")
    LABDIR.mkdir(parents=True, exist_ok=True)

    blk = {(r["subject"], int(r["seizure_idx"])): r
           for r in csv.DictReader(open(blkf)) if r["subject"] in TEST_SUBJ}
    src = list(csv.DictReader(open(V5LAB)))
    if len(src) != EXPECTED_TEST_SEIZURES:
        die(f"expected {EXPECTED_TEST_SEIZURES} rows in {V5LAB}, got {len(src)}")

    out, bad, nfocal, ngen = [], [], 0, 0
    for r in src:
        key = (r["subject"], int(r["seizure_idx"]))
        if key not in blk:
            bad.append(f"{key} absent from seizure_blocks.csv")
            continue
        b = blk[key]
        if b["edf_file"] != r["fname"] or int(b["onset_s"]) != int(r["onset_s"]):
            bad.append(f"{key} MISALIGNED: blocks=({b['edf_file']},{b['onset_s']}) "
                       f"labels=({r['fname']},{r['onset_s']})")
            continue
        chans = [c.strip() for c in r["dominant_ch"].split(",") if c.strip()]
        unknown = [c for c in chans if c not in CH]
        if unknown:
            bad.append(f"{key} unknown channel name(s): {unknown}")
            continue
        focal = bool(chans)
        nfocal += focal
        ngen += (not focal)
        out.append({"subject": r["subject"], "seizure_idx": r["seizure_idx"],
                    "edf_file": b["edf_file"], "onset_s": b["onset_s"],
                    "offset_s": b["offset_s"], "dur_s": b["dur_s"],
                    "n_windows": b["n_windows"], "ictal_channels": "|".join(chans),
                    "n_ictal_channels": len(chans), "uncertain_channels": "", "flags": "",
                    "focal_generalized": "focal" if focal else "generalized",
                    "label_source": "AI-DRAFT (attribution_v5 reader pass, verbatim)",
                    "note": (r.get("note") or "").strip()})

    if bad:
        die("conversion gate FAILED:\n  " + "\n  ".join(bad[:10]))

    write_csv(LABDIR / "ictal_channels_DRAFT.csv", out)
    (LABDIR / "README_DRAFT_STATUS.md").write_text(
        "# ictal_channels_DRAFT.csv — AI-DRAFT, PROVISIONAL\n\n"
        "Converted verbatim from `results/attribution_v5/labels/labels_ALL_FINAL.csv` by\n"
        "`src/attribution_pipeline.py labels`. **Not reviewed or frozen by the supervisor.**\n"
        "Every result scored against this file is PROVISIONAL (ATTRIBUTION_SPEC §9, A2/D2).\n\n"
        "Rows with an empty `ictal_channels` are **generalized** seizures whose reader note reads\n"
        "DIFFUSE (no localisable lead channel) — they are labels, not missing data. Per §4.5 they\n"
        "are excluded from AUROC/AUPRC and enter only the spread analysis.\n\n"
        "Alignment with `seizure_blocks.csv` verified on all 76 seizures (edf_file + onset_s).\n\n"
        "KNOWN LIMITATION (see label_diversity.csv): within-subject Jaccard is 0.8879, i.e. the\n"
        "label set is near-constant within a subject. These labels CANNOT distinguish per-seizure\n"
        "attribution from a subject-level channel prior.\n", encoding="utf-8")

    print(f"\n{len(out)} seizures: {nfocal} focal / {ngen} generalized")
    per = {}
    for r in out:
        if r["focal_generalized"] == "focal":
            per[r["subject"]] = per.get(r["subject"], 0) + 1
    print("focal seizures per subject (the AUROC-eligible set):")
    for s in TEST_SUBJ:
        print(f"  {s:<8}{per.get(s,0):>3}")
    print(f"  {'TOTAL':<8}{sum(per.values()):>3}")


# ============================================================================
# 4. score — per-seizure 18-channel score vector and ranking (D3/D4/D5)
# ============================================================================
def cmd_score(a):
    mapf = OUT / "ictal_row_to_seizure.csv"
    if not mapf.is_file():
        die(f"missing {mapf}")
    rowmap = {}
    for r in csv.DictReader(open(mapf)):
        if r["subject"] in TEST_SUBJ:
            rowmap.setdefault((r["subject"], int(r["seizure_idx"])), []).append(int(r["row"]))
    if len(rowmap) != EXPECTED_TEST_SEIZURES:
        die(f"expected {EXPECTED_TEST_SEIZURES} TEST seizures in map, got {len(rowmap)}")

    out = []
    for seed in SEEDS:
        d = PNR / f"seed{seed}"
        if not d.is_dir():
            die(f"missing {d} — run: python src/attribution_pipeline.py dump --seed {seed}")
        for subj in TEST_SUBJ:
            ict = np.load(d / f"{subj}_ictal_pernode.npy")
            base = np.load(d / f"{subj}_interictal_pernode.npy")
            med = np.median(base, axis=0)
            mad = np.median(np.abs(base - med), axis=0) + 1e-9
            for (s, k), rows in sorted(rowmap.items()):
                if s != subj:
                    continue
                z = np.abs((ict[np.array(rows)] - med) / mad)
                for agg, vec in [("p95", np.percentile(z, 95, axis=0)), ("mean", z.mean(axis=0))]:
                    order = np.argsort(-vec)
                    rank = np.empty(NCH, dtype=int)
                    rank[order] = np.arange(1, NCH + 1)
                    for i in range(NCH):
                        out.append({"seed": seed, "subject": subj, "seizure_idx": k,
                                    "n_windows": len(rows), "agg": agg, "ch_idx": i,
                                    "ch_name": CH[i], "score": round(float(vec[i]), 6),
                                    "rank": int(rank[i])})
            print(f"  seed{seed} {subj}: scored "
                  f"{sum(1 for x, _ in rowmap if x == subj)} seizures")

    write_csv(OUT / "attribution_scores.csv", out)
    exp = len(SEEDS) * EXPECTED_TEST_SEIZURES * 2 * NCH
    if len(out) != exp:
        die(f"row count {len(out)} != expected {exp}")

    top = {}
    for r in out:
        if r["seed"] == 42 and r["agg"] == "p95" and r["rank"] == 1:
            top[r["ch_name"]] = top.get(r["ch_name"], 0) + 1
    print(f"\nseed42/p95 — top-1 channel frequency across {EXPECTED_TEST_SEIZURES} seizures:")
    for k, v in sorted(top.items(), key=lambda x: -x[1]):
        print(f"  {k:<8} {v}")


# ============================================================================
# 5. diag — label-free internal validity (§4.7) + seed robustness (D4)
# ============================================================================
def cmd_diag(a):
    from scipy.stats import spearmanr
    S = load_scores(agg="p95")
    keys = sorted({(s, k) for (sd, ag, s, k) in S if sd == 42})
    print(f"loaded {len(keys)} seizures x {len(SEEDS)} seeds (p95)\n")

    top_agree, rho_seed = [], []
    for (s, k) in keys:
        v = [S[(sd, "p95", s, k)] for sd in SEEDS]
        t = [int(np.argmax(x)) for x in v]
        top_agree.append(sum(1 for x in t[1:] if x == t[0]) / (len(SEEDS) - 1))
        rho_seed += [spearmanr(v[0], v[i]).statistic for i in range(1, len(v))]
    print("(i) SEED ROBUSTNESS (seed42 vs 1/2/3)")
    print(f"    top-1 agreement : {np.mean(top_agree):.3f}  "
          f"(all 3 agree on {np.mean([x == 1.0 for x in top_agree])*100:.0f}% of seizures)")
    print(f"    Spearman rho    : {np.mean(rho_seed):.3f} +- {np.std(rho_seed):.3f}\n")

    rng = np.random.default_rng(SEED)
    print("(ii) WITHIN-SUBJECT TOP-1 CONCENTRATION (seed42)")
    print(f"     {'subject':<9}{'n_sz':>5}{'distinct':>9}{'max_share':>11}{'null_p95':>10}  verdict")
    rows = []
    for subj in sorted({s for s, _ in keys}):
        ks = [k for s, k in keys if s == subj]
        t = [int(np.argmax(S[(42, "p95", subj, k)])) for k in ks]
        n = len(ks)
        share = max(np.bincount(t, minlength=NCH)) / n
        null = np.array([max(np.bincount(rng.integers(0, NCH, n), minlength=NCH)) / n
                         for _ in range(2000)])
        p95 = float(np.percentile(null, 95))
        flag = "CONCENTRATED" if share > p95 else "ok"
        rows.append({"subject": subj, "n_seizures": n, "distinct_top1": len(set(t)),
                     "max_share": round(float(share), 3), "null_p95": round(p95, 3),
                     "verdict": flag})
        print(f"     {subj:<9}{n:>5}{len(set(t)):>9}{share:>11.3f}{p95:>10.3f}  {flag}")

    def mean_pair_rho(pairs):
        return float(np.mean([spearmanr(S[(42, "p95", a, b)], S[(42, "p95", c, d)]).statistic
                              for (a, b), (c, d) in pairs])) if pairs else np.nan
    within = [(x, y) for i, x in enumerate(keys) for y in keys[i + 1:] if x[0] == y[0]]
    across = [(x, y) for i, x in enumerate(keys) for y in keys[i + 1:] if x[0] != y[0]]
    sel = rng.choice(len(across), size=min(3000, len(across)), replace=False)
    w, ac = mean_pair_rho(within), mean_pair_rho([across[i] for i in sel])
    print("\n(iii) C1 CONSISTENCY (mean pairwise Spearman of s)")
    print(f"      within-subject  : {w:.3f}  (n={len(within)} pairs)")
    print(f"      across-subject  : {ac:.3f}  (n={len(sel)} sampled pairs)")
    print(f"      delta           : {w - ac:+.3f}")

    write_csv(OUT / "attribution_diagnostics.csv", rows)


# ============================================================================
# 6. synth — synthetic anomaly injection, gates G-S1..G-S3 (§4.6 / D6)
# ============================================================================
def _perm_null(S, Y, rng):
    out = np.empty(NPERM)
    for t in range(NPERM):
        idx = np.argsort(rng.random(S.shape), axis=1)
        out[t] = macro_auroc_rows(np.take_along_axis(S, idx, axis=1), Y)
    return out


def _synth_run(subjects, lens, tag):
    rng = np.random.default_rng(SEED)
    inter = {}
    for s in subjects:
        f = PNR / "seed42" / f"{s}_interictal_pernode.npy"
        if not f.is_file():
            die(f"missing {f}")
        inter[s] = np.load(f)

    rows, store = [], {}
    for alpha in ALPHAS:
        for k in SIZES:
            S = np.zeros((R, NCH))
            Y = np.zeros((R, NCH), dtype=int)
            for r in range(R):
                A = inter[subjects[rng.integers(len(subjects))]]
                L = min(int(lens[rng.integers(len(lens))]), A.shape[0] // 4)
                st = int(rng.integers(0, A.shape[0] - L))
                blk = A[st:st + L].copy()
                base = np.delete(A, np.arange(st, st + L), axis=0)
                inj = rng.choice(NCH, size=k, replace=False)
                blk[:, inj] *= alpha
                med = np.median(base, axis=0)
                mad = np.median(np.abs(base - med), axis=0) + 1e-9
                z = np.abs((blk - med) / mad)
                S[r] = np.percentile(z, 95, axis=0)
                Y[r, inj] = 1

            auroc, ap = macro_auroc_rows(S, Y), macro_ap_rows(S, Y)
            rec, spr = macro_recall_rows(S, Y), spreads(S)
            null = _perm_null(S, Y, rng)
            pval = (np.sum(null >= auroc) + 1) / (NPERM + 1)
            rows.append({"panel": tag, "alpha": alpha, "n_injected": k,
                         "macro_AUROC": round(auroc, 4), "macro_AUPRC": round(ap, 4),
                         "recall_at_S": round(rec, 4), "null_mean": round(float(null.mean()), 4),
                         "null_p95": round(float(np.percentile(null, 95)), 4),
                         "p_perm": round(float(pval), 4),
                         "spread_mean": round(float(spr.mean()), 4)})
            store[(alpha, k)] = spr
            print(f"  {tag:<4} a={alpha:<5} |S|={k:<3} AUROC={auroc:.4f} AUPRC={ap:.4f} "
                  f"R@S={rec:.4f} null={null.mean():.4f} p={pval:.4f} spread={spr.mean():.4f}")
    return rows, store


def cmd_synth(a):
    from scipy.stats import mannwhitneyu
    lens = load_len_distribution()
    print(f"seizure-length distribution from {EXPECTED_TEST_SEIZURES} TEST seizures: "
          f"min={lens.min()} median={int(np.median(lens))} max={lens.max()}\n")

    all_rows, store_val = {}, None
    for tag, subs in [("VAL", VAL_SUBJ), ("TEST", TEST_SUBJ)]:
        print(f"--- {tag} ---")
        rows, store = _synth_run(subs, lens, tag)
        all_rows[tag] = rows
        if tag == "VAL":
            store_val = store
        print()

    write_csv(OUT / "synthetic_sanity.csv", all_rows["VAL"] + all_rows["TEST"])

    g = {r["alpha"]: r for r in all_rows["VAL"] if r["n_injected"] == 1}
    gs1 = 0.45 <= g[1.0]["macro_AUROC"] <= 0.55
    gs2 = g[3.0]["macro_AUROC"] >= 0.95
    gs3 = all(
        all(next(r for r in all_rows["VAL"] if r["alpha"] == x and r["n_injected"] == k)["macro_AUROC"]
            <= next(r for r in all_rows["VAL"] if r["alpha"] == y and r["n_injected"] == k)["macro_AUROC"]
            + 1e-9 for x, y in zip(ALPHAS, ALPHAS[1:])) for k in SIZES)
    _, p4 = mannwhitneyu(store_val[(2.0, 12)], store_val[(2.0, 1)], alternative="greater")

    print("\n=== PRE-REGISTERED GATES (VAL) ===")
    print(f"  G-S1 negative control  a=1.0,|S|=1 AUROC={g[1.0]['macro_AUROC']:.4f} in [0.45,0.55]"
          f"  -> {'PASS' if gs1 else 'FAIL'}")
    print(f"  G-S2 upper bound       a=3.0,|S|=1 AUROC={g[3.0]['macro_AUROC']:.4f} >= 0.95"
          f"  -> {'PASS' if gs2 else 'FAIL'}")
    print(f"  G-S3 monotone in alpha -> {'PASS' if gs3 else 'FAIL'}")
    print(f"  G-S4 (SUPERSEDED by D6.1; |S|=12 is not a generalized seizure) p={p4:.2e}")
    print("\nVERDICT:", "PASS on G-S1/2/3" if all([gs1, gs2, gs3]) else "FAIL — diagnose first")
    print("G-S4' is evaluated by:  python src/attribution_pipeline.py spread")


# ============================================================================
# 7. spread — gate G-S4' after the D6.1 construction fix
# ============================================================================
def _spread_run(subjects, lens, tag):
    rng = np.random.default_rng(SEED)
    inter = {s: np.load(PNR / "seed42" / f"{s}_interictal_pernode.npy") for s in subjects}
    res = {}
    for k in SPREAD_KS:
        S = np.zeros((R, NCH))
        for r in range(R):
            A = inter[subjects[rng.integers(len(subjects))]]
            L = min(int(lens[rng.integers(len(lens))]), A.shape[0] // 4)
            st = int(rng.integers(0, A.shape[0] - L))
            blk = A[st:st + L].copy()
            base = np.delete(A, np.arange(st, st + L), axis=0)
            blk[:, rng.choice(NCH, size=k, replace=False)] *= SPREAD_ALPHA
            med = np.median(base, axis=0)
            mad = np.median(np.abs(base - med), axis=0) + 1e-9
            S[r] = np.percentile(np.abs((blk - med) / mad), 95, axis=0)
        res[k] = spreads(S)
        print(f"  {tag:<4} a={SPREAD_ALPHA} |S|={k:<3} spread={res[k].mean():.4f} "
              f"(sd {res[k].std():.4f})" + ("   [AUROC undefined]" if k == NCH else ""))
    return res


def cmd_spread(a):
    from scipy.stats import mannwhitneyu
    lens = load_len_distribution()
    out = {}
    for tag, subs in [("VAL", VAL_SUBJ), ("TEST", TEST_SUBJ)]:
        print(f"--- {tag} ---")
        out[tag] = _spread_run(subs, lens, tag)
        print()

    write_csv(OUT / "synthetic_spread.csv",
              [{"panel": t, "alpha": SPREAD_ALPHA, "n_injected": k,
                "spread_mean": round(float(v.mean()), 4), "spread_sd": round(float(v.std()), 4)}
               for t, d in out.items() for k, v in d.items()])

    v = out["VAL"]
    _, p_g = mannwhitneyu(v[18], v[1], alternative="greater")
    _, p_2 = mannwhitneyu(v[18], v[1], alternative="two-sided")
    print("\n=== G-S4' (VAL, D6.1) ===")
    print(f"  spread(|S|=18) = {v[18].mean():.4f}   spread(|S|=1) = {v[1].mean():.4f}")
    print(f"  one-sided p = {p_g:.3e} | two-sided p = {p_2:.3e}")
    print("  VERDICT:", "PASS — proceed to real labels" if p_g < 0.05 else
          "FAIL — normalised entropy is not a usable diffuseness metric here")


# ============================================================================
# 8. eval — score against labels (§4.1/4.3/4.4/4.5 + D5/D7/D8). PROVISIONAL.
# ============================================================================
def cmd_eval(a):
    from scipy.stats import mannwhitneyu
    S = load_scores()
    lab = load_labels()
    rng = np.random.default_rng(SEED)

    all_keys = sorted(lab)
    focal = [k for k in all_keys if lab[k]["kind"] == "focal"]
    gen = [k for k in all_keys if lab[k]["kind"] == "generalized"]
    print(f"focal={len(focal)}  generalized={len(gen)}  "
          f"prevalence(|S|/18)={np.mean([lab[k]['nS'] for k in focal])/NCH:.3f}\n")

    def loo(seed, agg, k):
        """D7 subject-constant control: mean s over the OTHER seizures of the same subject."""
        others = [S[(seed, agg, *o)] for o in all_keys if o[0] == k[0] and o != k]
        return np.mean(others, axis=0) if others else None

    per = []
    for k in focal:
        d = lab[k]
        s = S[(42, "p95", *k)]
        c = loo(42, "p95", k)
        per.append({"subject": k[0], "seizure_idx": k[1], "n_windows": d["nw"],
                    "n_ictal_ch": d["nS"], "AUROC": round(float(auroc18(d["y"], s)), 4),
                    "AUPRC": round(ap18(d["y"], s), 4),
                    "recall_at_S": round(rec_at_S(d["y"], s), 4),
                    "spread": round(spread_one(s), 4),
                    "AUROC_ctrl": None if c is None else round(float(auroc18(d["y"], c)), 4)})
    write_csv(OUT / "attribution_perseizure.csv", per)

    rows = []

    def panel(name, keys, seed=42, agg="p95"):
        A = [auroc18(lab[k]["y"], S[(seed, agg, *k)]) for k in keys]
        P = [ap18(lab[k]["y"], S[(seed, agg, *k)]) for k in keys]
        Rc = [rec_at_S(lab[k]["y"], S[(seed, agg, *k)]) for k in keys]
        C = [auroc18(lab[k]["y"], loo(seed, agg, k)) for k in keys if loo(seed, agg, k) is not None]
        ma, lo, hi = bootstrap_mean(A, rng)
        mp, plo, phi = bootstrap_mean(P, rng)
        mc = float(np.mean(C)) if C else float("nan")
        null = np.empty(NPERM)
        for t in range(NPERM):
            null[t] = np.mean([auroc18(lab[k]["y"], rng.permutation(S[(seed, agg, *k)]))
                               for k in keys])
        pv = (np.sum(null >= ma) + 1) / (NPERM + 1)
        rows.append({"panel": name, "n_seizures": len(keys), "seed": seed, "agg": agg,
                     "macro_AUROC": round(ma, 4), "AUROC_CI_lo": round(lo, 4),
                     "AUROC_CI_hi": round(hi, 4), "macro_AUPRC": round(mp, 4),
                     "AUPRC_CI_lo": round(plo, 4), "AUPRC_CI_hi": round(phi, 4),
                     "recall_at_S": round(float(np.mean(Rc)), 4),
                     "AUROC_subject_ctrl": round(mc, 4), "delta_vs_ctrl": round(ma - mc, 4),
                     "null_mean": round(float(null.mean()), 4), "p_perm": round(float(pv), 4)})
        print(f"  {name:<28} n={len(keys):<3} AUROC={ma:.4f} [{lo:.4f},{hi:.4f}] "
              f"AUPRC={mp:.4f} R@S={np.mean(Rc):.4f} ctrl={mc:.4f} D={ma-mc:+.4f} p={pv:.4f}")

    print("=== PRIMARY (seed42, p95) ===")
    panel("ALL focal (D5 primary)", focal)
    print("\n=== D8 chb15 dominance ===")
    panel("focal excl. chb15", [k for k in focal if k[0] != "chb15"])
    panel("chb15 only", [k for k in focal if k[0] == "chb15"])
    print("\n=== D5 secondary (n_windows >= 3) ===")
    panel("focal, n_win>=3", [k for k in focal if lab[k]["nw"] >= 3])
    print("\n=== per-subject ===")
    for s in sorted({k[0] for k in focal}):
        ks = [k for k in focal if k[0] == s]
        if len(ks) >= 2:
            panel(f"subject {s}", ks)
        else:
            print(f"  subject {s:<20} n=1   "
                  f"AUROC={auroc18(lab[ks[0]]['y'], S[(42,'p95',*ks[0])]):.4f}  (no CI)")
    print("\n=== D4 seed robustness ===")
    for sd in (1, 2, 3):
        panel(f"ALL focal seed{sd}", focal, seed=sd)
    print("\n=== sensitivity: mean aggregation ===")
    panel("ALL focal (mean agg)", focal, agg="mean")

    sf = np.array([spread_one(S[(42, "p95", *k)]) for k in focal])
    sg = np.array([spread_one(S[(42, "p95", *k)]) for k in gen])
    _, pg = mannwhitneyu(sg, sf, alternative="greater")

    # Per-seizure generalized (diffuse) spread, for Fig 3.15 (docs/FIGURE_FIXES_R3.md §1):
    # the group mean (sg.mean(), written into attribution_summary.csv below) was already
    # committed, but the 40 individual points behind it were computed and discarded. This
    # persists them (same spread_one call, same S/lab already loaded -- no new computation)
    # so the figure script can read committed per-seizure values instead of typing in the mean.
    per_gen = [{"subject": k[0], "seizure_idx": k[1], "n_windows": lab[k]["nw"],
                "spread": round(spread_one(S[(42, "p95", *k)]), 4)} for k in gen]
    write_csv(OUT / "attribution_perseizure_generalized.csv", per_gen)

    print("\n=== §4.5 spread, real labels ===")
    print(f"  focal (n={len(sf)}) {sf.mean():.4f}   generalized (n={len(sg)}) {sg.mean():.4f}"
          f"   one-sided p={pg:.3e}")
    rows.append({"panel": "spread focal vs generalized", "n_seizures": len(sf) + len(sg),
                 "seed": 42, "agg": "p95", "macro_AUROC": round(float(sf.mean()), 4),
                 "AUROC_subject_ctrl": round(float(sg.mean()), 4), "p_perm": round(float(pg), 6)})

    write_csv(OUT / "attribution_summary.csv", rows)
    print("\nALL NUMBERS PROVISIONAL — labels are an AI draft, not supervisor-frozen.")
    print("Read attribution_summary.csv together with label_diversity.csv: the D7 control is")
    print("UNINFORMATIVE because within-subject label Jaccard is 0.8879 (see labeldiv).")


# ============================================================================
# 9. labeldiv — can these labels test per-seizure attribution at all?
# ============================================================================
def _jac(a, b):
    u = len(a | b)
    return 1.0 if u == 0 else len(a & b) / u


def cmd_labeldiv(a):
    lab = load_labels()
    S = load_scores(seed=42, agg="p95")
    foc = {k: v["chans"] for k, v in lab.items() if v["kind"] == "focal"}

    print(f"{'subject':<9}{'n':>4}{'distinct_y':>12}{'mean_Jaccard':>14}{'union_size':>12}")
    rows = []
    for s in sorted({k[0] for k in foc}):
        ks = [k for k in foc if k[0] == s]
        if len(ks) < 2:
            print(f"{s:<9}{len(ks):>4}{'-':>12}{'-':>14}{len(foc[ks[0]]):>12}")
            continue
        sets = [foc[k] for k in ks]
        j = np.mean([_jac(sets[i], sets[m]) for i in range(len(sets))
                     for m in range(i + 1, len(sets))])
        rows.append({"subject": s, "n_focal": len(ks),
                     "distinct_label_sets": len({frozenset(x) for x in sets}),
                     "mean_jaccard": round(float(j), 4), "union_size": len(set().union(*sets))})
        print(f"{s:<9}{len(ks):>4}{rows[-1]['distinct_label_sets']:>12}"
              f"{j:>14.4f}{rows[-1]['union_size']:>12}")

    allk = sorted(foc)
    sets = [foc[k] for k in allk]
    j_all = np.mean([_jac(sets[i], sets[m]) for i in range(len(sets))
                     for m in range(i + 1, len(sets)) if allk[i][0] == allk[m][0]])
    print(f"\npooled within-subject mean Jaccard = {j_all:.4f}")
    print("  ~1.0 => labels are subject-constant; the D7 control is uninformative")
    print("  ~0.0 => labels vary per seizure; a losing D7 control is a real negative")

    print("\nper-seizure deviation test (chb15, the dominant subject):")
    ks = [k for k in allk if k[0] == "chb15"]
    if len(ks) >= 3:
        Y = np.array([[1.0 if c in foc[k] else 0.0 for c in CH] for k in ks])
        Sm = np.array([S[(42, "p95", *k)] for k in ks])
        dy, ds = Y - Y.mean(0), Sm - Sm.mean(0)
        num = (dy * ds).sum()
        den = np.sqrt((dy ** 2).sum() * (ds ** 2).sum())
        print(f"  corr(y - y_subjmean, s - s_subjmean) = {num/den:+.4f}  (n={len(ks)} seizures)")
        print("  positive => s tracks per-seizure deviations; ~0 => it does not")

    write_csv(OUT / "label_diversity.csv", rows)


# ============================================================================
# CLI
# ============================================================================
def cmd_all(a):
    for name, fn in [("score", cmd_score), ("diag", cmd_diag), ("synth", cmd_synth),
                     ("spread", cmd_spread), ("eval", cmd_eval), ("labeldiv", cmd_labeldiv)]:
        print(f"\n{'#'*90}\n# {name}\n{'#'*90}")
        fn(a)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("dump", help="regenerate per-node recon error (D1/D4)")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--proc_dir", default=str(PROC))
    p.add_argument("--out_root", default=str(PNR))
    p.add_argument("--batch_size", type=int, default=256)
    p.add_argument("--smoke", action="store_true")
    p.set_defaults(func=cmd_dump)

    p = sub.add_parser("blocks", help="map ictal rows to seizures")
    p.add_argument("--edf_root", required=True)
    p.add_argument("--summary_dir", required=True)
    p.add_argument("--proc_dir", default=str(PROC))
    p.set_defaults(func=cmd_blocks)

    for name, fn, helptxt in [
            ("labels", cmd_labels, "convert v5 reader labels to §3.2 schema (D2)"),
            ("score", cmd_score, "per-seizure 18-channel score + rank"),
            ("diag", cmd_diag, "label-free diagnostics (§4.7 + D4)"),
            ("synth", cmd_synth, "synthetic sanity check, gates G-S1..G-S3 (§4.6)"),
            ("spread", cmd_spread, "gate G-S4' after the D6.1 fix"),
            ("eval", cmd_eval, "score against labels — PROVISIONAL"),
            ("labeldiv", cmd_labeldiv, "label diversity: can labels test per-seizure?"),
            ("all", cmd_all, "score -> diag -> synth -> spread -> eval -> labeldiv")]:
        q = sub.add_parser(name, help=helptxt)
        q.set_defaults(func=fn)

    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    a.func(a)


if __name__ == "__main__":
    main()
