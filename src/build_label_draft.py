#!/usr/bin/env python
"""
build_label_draft.py — deterministic conversion of results/attribution_v5/labels/labels_ALL_FINAL.csv
into ATTRIBUTION_SPEC §3.2 schema. NO new labelling: channel sets and DIFFUSE verdicts are carried
over verbatim from the existing reader pass.

  dominant_ch non-empty  -> focal,       ictal_channels = that set
  dominant_ch empty      -> generalized, ictal_channels = <empty>  (excluded from AUROC by §4.5)

Hard gate: every (edf_file, onset_s) must match results/attribution_v6/seizure_blocks.csv, proving
the seizure_idx convention is identical across the two files.

Output carries an AI-DRAFT / PROVISIONAL banner. NOT supervisor-frozen.
"""
import csv, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC  = ROOT / "results" / "attribution_v5" / "labels" / "labels_ALL_FINAL.csv"
BLK  = ROOT / "results" / "attribution_v6" / "seizure_blocks.csv"
OUTD = ROOT / "results" / "attribution_v6" / "labels"
CH = ["FP1-F7","F7-T7","T7-P7","P7-O1","FP1-F3","F3-C3","C3-P3","P3-O1",
      "FP2-F4","F4-C4","C4-P4","P4-O2","FP2-F8","F8-T8","T8-P8","P8-O2","FZ-CZ","CZ-PZ"]
TEST = ["chb03","chb06","chb13","chb14","chb15","chb16","chb17","chb18"]


def die(m):
    print(f"\n[FATAL] {m}\n", file=sys.stderr); sys.exit(1)


def main():
    for f in (SRC, BLK):
        if not f.is_file():
            die(f"missing {f}")
    OUTD.mkdir(parents=True, exist_ok=True)

    blk = {(r["subject"], int(r["seizure_idx"])): r
           for r in csv.DictReader(open(BLK)) if r["subject"] in TEST}
    src = list(csv.DictReader(open(SRC)))
    if len(src) != 76:
        die(f"expected 76 rows in {SRC}, got {len(src)}")

    out, bad, nfocal, ngen = [], [], 0, 0
    for r in src:
        key = (r["subject"], int(r["seizure_idx"]))
        if key not in blk:
            bad.append(f"{key} absent from seizure_blocks.csv"); continue
        b = blk[key]
        if b["edf_file"] != r["fname"] or int(b["onset_s"]) != int(r["onset_s"]):
            bad.append(f"{key} MISALIGNED: blocks=({b['edf_file']},{b['onset_s']}) "
                       f"labels=({r['fname']},{r['onset_s']})"); continue

        chans = [c.strip() for c in r["dominant_ch"].split(",") if c.strip()]
        unknown = [c for c in chans if c not in CH]
        if unknown:
            bad.append(f"{key} unknown channel name(s): {unknown}"); continue

        focal = bool(chans)
        nfocal += focal; ngen += (not focal)
        out.append({"subject": r["subject"], "seizure_idx": r["seizure_idx"],
                    "edf_file": b["edf_file"], "onset_s": b["onset_s"], "offset_s": b["offset_s"],
                    "dur_s": b["dur_s"], "n_windows": b["n_windows"],
                    "ictal_channels": "|".join(chans),
                    "n_ictal_channels": len(chans),
                    "uncertain_channels": "", "flags": "",
                    "focal_generalized": "focal" if focal else "generalized",
                    "label_source": "AI-DRAFT (attribution_v5 reader pass, verbatim)",
                    "note": (r.get("note") or "").strip()})

    if bad:
        die("conversion gate FAILED:\n  " + "\n  ".join(bad[:10]))

    f = OUTD / "ictal_channels_DRAFT.csv"
    with open(f, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(out)

    (OUTD / "README_DRAFT_STATUS.md").write_text(
        "# ictal_channels_DRAFT.csv — AI-DRAFT, PROVISIONAL\n\n"
        "Converted verbatim from `results/attribution_v5/labels/labels_ALL_FINAL.csv` by\n"
        "`src/build_label_draft.py`. **Not reviewed or frozen by the supervisor.** Every result\n"
        "scored against this file must be reported as PROVISIONAL (ATTRIBUTION_SPEC §9, A2/D2).\n\n"
        "Rows with an empty `ictal_channels` are **generalized** seizures whose reader note reads\n"
        "DIFFUSE (no localisable lead channel) — they are labels, not missing data. Per §4.5 they are\n"
        "excluded from AUROC/AUPRC (y would be undefined) and enter only the spread analysis.\n\n"
        "Alignment with `seizure_blocks.csv` verified on all 76 seizures (edf_file + onset_s).\n",
        encoding="utf-8")

    print(f"wrote {f}  ({len(out)} seizures: {nfocal} focal / {ngen} generalized)")
    print("\nfocal seizures per subject (this is the AUROC-eligible set):")
    per = {}
    for r in out:
        if r["focal_generalized"] == "focal":
            per[r["subject"]] = per.get(r["subject"], 0) + 1
    for s in TEST:
        print(f"  {s:<8}{per.get(s,0):>3}")
    print(f"  {'TOTAL':<8}{sum(per.values()):>3}")


if __name__ == "__main__":
    main()