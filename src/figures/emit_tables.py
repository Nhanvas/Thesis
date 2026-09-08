"""
emit_tables.py -- Task D, Figure Brief Round 2. Output location moved to
tables/csv/ by docs/FIGURE_ROUND6.md §2 (was results/report_tables/).

Emits the four report tables to tables/csv/. Every value is read
from a committed file; nothing is typed in. Each table keeps a numeric
self-check against docs/VERIFIED_NUMBERS.md and stops rather than writing a
value it cannot confirm (brief rule 1).

Table 3.4  event-level performance per patient, m50/p2.0
           <- results/phaseB/tier2/rlg_test/final_eval_seed42.csv
Table A.1  corpus metadata for all 23 subjects
           <- data/summaries/*.txt (parsed with evaluation_protocol.parse_summary_edf_list)
Table A.2  channel annotation for all 76 held-out seizures
           <- results/attribution_v6/labels/ictal_channels_DRAFT.csv
Table A.3  the full 384-row parameter grid, pass-through
           <- results/phaseB/tier2/rlg_test/final_eval_seed42.csv

docs/FIGURE_ROUND6.md §3: each table above (A.3 excepted -- 384 rows, a CSV
attachment/appendix listing only) is also rendered to a markdown table via
render_markdown(), written alongside its CSV in tables/csv/ and meant to be
pasted verbatim into the matching chapter file under tables/ (see §4).

USAGE
    python src/figures/emit_tables.py
"""
import os as _os, sys as _sys
_here = _os.path.dirname(_os.path.abspath(__file__))
_src = _os.path.dirname(_here)
for _p in (_here, _src):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

from pathlib import Path

import numpy as np
import pandas as pd

import evaluation_protocol as E

ROOT = Path(_src).parent
GRID_CSV = ROOT / "results" / "phaseB" / "tier2" / "rlg_test" / "final_eval_seed42.csv"
SUMMARY_DIR = ROOT / "data" / "summaries"
LABELS_CSV = ROOT / "results" / "attribution_v6" / "labels" / "ictal_channels_DRAFT.csv"
SPLIT_JSON = ROOT / "data" / "splits" / "split_main.json"
OUT_DIR = ROOT / "tables" / "csv"

MAG_PCT, PEN_MULT = 50.0, 2.0

HELD_OUT = ["chb03", "chb06", "chb13", "chb14", "chb15", "chb16", "chb17", "chb18"]

# Self-check values from the Figure Brief §5, printed by plot_event_level.py.
EXPECTED_TABLE_34 = {
    "chb03": (1.000, 0.152, 0.264, 24.7),
    "chb06": (0.000, 0.000, None, 19.4),
    "chb13": (0.750, 0.220, 0.340, 23.4),
    "chb14": (0.375, 0.049, 0.087, 53.6),
    "chb15": (0.900, 0.286, 0.434, 27.4),
    "chb16": (0.200, 0.105, 0.138, 21.5),
    "chb17": (1.000, 0.115, 0.207, 26.4),
    "chb18": (0.833, 0.091, 0.164, 33.8),
}

# docs/VERIFIED_NUMBERS.md Part 3 -- per-set totals.
EXPECTED_TABLE_A1_TOTALS = {
    "train": (12, 342, 566.43, 93),
    "validation": (3, 91, 115.82, 13),
    "held-out": (8, 231, 279.39, 76),
}


# ============================================================================
# docs/FIGURE_ROUND6.md §3 -- render a table to a markdown block ready to paste
# into a chapter file. Column headers are given explicitly (sentence case, no
# code-variable names) rather than derived from the DataFrame's own column
# names, which are lower_snake_case internal identifiers.
# ============================================================================
def render_markdown(df: pd.DataFrame, headers: dict, csv_path: Path) -> str:
    cols = list(headers.keys())
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise ValueError(f"render_markdown: columns {missing} not in dataframe "
                          f"(have {list(df.columns)}) -- stop")
    def esc(v):
        # A literal "|" (e.g. multiple annotated channels joined "A|B") would
        # otherwise be read as a markdown cell delimiter and break the table.
        return str(v).replace("|", "\\|")

    lines = ["| " + " | ".join(headers[c] for c in cols) + " |",
              "|" + "|".join(["---"] * len(cols)) + "|"]
    for _, row in df.iterrows():
        lines.append("| " + " | ".join(esc(row[c]) for c in cols) + " |")
    md = "\n".join(lines) + "\n"
    md_path = csv_path.with_suffix(".md")
    md_path.write_text(md, encoding="utf-8")
    print(f"  [render_markdown] wrote {md_path} ({len(df)} rows)")
    return md


# ============================================================================
# Table 3.4 -- event-level performance per patient, m50/p2.0
# ============================================================================
def emit_table_34():
    # Recomputed from tp/fp/n_seizures/n_inter_h at the row level, the same
    # convention plot_event_level.py uses (never a stored, pre-rounded
    # sensitivity/precision/fp_per_day column) -- this is what the brief's
    # self-check values were themselves printed from.
    df = pd.read_csv(GRID_CSV)
    d = df[(np.isclose(df.mag_pct, MAG_PCT)) & (np.isclose(df.pen_mult, PEN_MULT))]
    d = d.set_index("subject").reindex(HELD_OUT)
    if d[["tp", "fp", "n_seizures", "n_inter_h"]].isna().any().any():
        raise ValueError(f"Table 3.4: missing rows at m{MAG_PCT:.0f}/p{PEN_MULT:.1f}")

    rows = []
    for subj in HELD_OUT:
        r = d.loc[subj]
        tp, fp, nsz, ih = float(r.tp), float(r.fp), float(r.n_seizures), float(r.n_inter_h)
        sens = tp / nsz if nsz else float("nan")
        prec = tp / (tp + fp) if (tp + fp) else float("nan")
        fpd = fp / ih * 24 if ih else float("nan")
        if (sens + prec) == 0:
            f1_str = "undefined"
        else:
            f1_str = f"{2 * prec * sens / (prec + sens):.3f}"
        # docs/FIGURE_ROUND4.md §4: the report's convention is three decimals for
        # sensitivity/precision/F1/discrimination and one decimal for FP/day. round()
        # alone drops trailing zeros when written to CSV (1.0 instead of 1.000, 0.22
        # instead of 0.220) -- format as fixed-decimal strings instead. `undefined`
        # stays as it is.
        rows.append(dict(patient=subj, seizures=int(r.n_seizures),
                          sensitivity=f"{sens:.3f}", precision=f"{prec:.3f}",
                          f1=f1_str, fp_per_day=f"{fpd:.1f}"))

        exp_sens, exp_prec, exp_f1, exp_fpd = EXPECTED_TABLE_34[subj]
        got_f1 = None if f1_str == "undefined" else float(f1_str)
        ok = (round(sens, 3) == exp_sens and round(prec, 3) == exp_prec
              and got_f1 == exp_f1 and round(fpd, 1) == exp_fpd)
        if not ok:
            raise ValueError(f"Table 3.4 self-check failed for {subj}: got "
                              f"{(round(sens,3), round(prec,3), got_f1, round(fpd,1))}, "
                              f"expected {(exp_sens, exp_prec, exp_f1, exp_fpd)} -- stop")

    out = pd.DataFrame(rows)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = OUT_DIR / "table_3_4_event_level_per_patient.csv"
    out.to_csv(csv_path, index=False)
    print(f"[Table 3.4] wrote {len(out)} rows, self-check OK against brief §5")
    print(out.to_string(index=False))
    render_markdown(out, {"patient": "Patient", "seizures": "Seizures",
                          "sensitivity": "Sensitivity", "precision": "Precision",
                          "f1": "F1", "fp_per_day": "False alarms / day"}, csv_path)
    return out


# ============================================================================
# Table A.1 -- corpus metadata for all 23 subjects
# ============================================================================
def load_split():
    import json
    d = json.loads(SPLIT_JSON.read_text())
    subj_set = {}
    for s in d["inner_train"]:
        subj_set[s] = "train"
    for s in d["val"]:
        subj_set[s] = "validation"
    for s in d["test"]:
        subj_set[s] = "held-out"
    return subj_set


def emit_table_a1():
    subj_set = load_split()
    all_subjects = sorted(subj_set.keys())
    rows = []
    raw_hours = {}
    for subj in all_subjects:
        summary_path = SUMMARY_DIR / f"{subj}-summary.txt"
        edfs = E.parse_summary_edf_list(summary_path)
        n_files = len(edfs)
        hours = sum(e["duration_s"] for e in edfs) / 3600.0
        raw_hours[subj] = hours
        n_sz = sum(len(e["seizures"]) for e in edfs)
        sz_dur_s = sum((off - on) for e in edfs for (on, off) in e["seizures"])
        rows.append(dict(subject=subj, set=subj_set[subj], recordings=n_files,
                          recorded_hours=round(hours, 2), seizures=n_sz,
                          total_seizure_duration_s=sz_dur_s))

    out = pd.DataFrame(rows)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = OUT_DIR / "table_A1_corpus_metadata.csv"
    out.to_csv(csv_path, index=False)

    print(f"[Table A.1] wrote {len(out)} rows (expect 23)")
    if len(out) != 23:
        raise ValueError(f"Table A.1: {len(out)} subjects, expected 23 -- stop")

    # Per-subject rounded hours already match docs/VERIFIED_NUMBERS.md Part 3's
    # per-subject table exactly. The per-set TOTAL there was summed from the
    # raw (unrounded) hours, then rounded once -- summing the already-rounded
    # per-subject column instead can differ by ~0.01 h from accumulated
    # rounding, so the self-check below sums raw hours, matching how the
    # committed total was produced.
    for set_name, (n_subj, n_files, hrs, n_sz) in EXPECTED_TABLE_A1_TOTALS.items():
        sub = out[out.set == set_name]
        got_n_subj, got_n_files = len(sub), int(sub.recordings.sum())
        got_hrs_raw = round(sum(raw_hours[s] for s in sub.subject), 2)
        got_sz = int(sub.seizures.sum())
        ok = (got_n_subj, got_n_files, got_hrs_raw, got_sz) == (n_subj, n_files, hrs, n_sz)
        print(f"  {set_name}: subjects={got_n_subj} files={got_n_files} "
              f"hours={got_hrs_raw} seizures={got_sz}  "
              f"(expected {n_subj}/{n_files}/{hrs}/{n_sz})  {'OK' if ok else 'MISMATCH'}")
        if not ok:
            raise ValueError(f"Table A.1 self-check failed for set={set_name} -- stop")

    total_sz_dur_h = out[out.set == "held-out"].total_seizure_duration_s.sum() / 3600.0
    print(f"  held-out total seizure duration = {total_sz_dur_h:.3f} h "
          f"(brief: ~1.10 h, 76 x 51.9 s)")
    render_markdown(out, {"subject": "Patient", "set": "Set", "recordings": "Recordings",
                          "recorded_hours": "Recorded hours (h)", "seizures": "Seizures",
                          "total_seizure_duration_s": "Total seizure duration (s)"}, csv_path)
    return out


# ============================================================================
# Table A.2 -- channel annotation for every held-out seizure
# ============================================================================
def emit_table_a2():
    df = pd.read_csv(LABELS_CSV)
    required = {"subject", "seizure_idx", "ictal_channels", "label_source"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Table A.2: {LABELS_CSV} missing columns {missing} -- stop")

    out = df[["subject", "seizure_idx", "ictal_channels", "label_source"]].copy()
    out.rename(columns={"ictal_channels": "annotated_channels"}, inplace=True)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = OUT_DIR / "table_A2_channel_annotation.csv"
    out.to_csv(csv_path, index=False)
    print(f"[Table A.2] wrote {len(out)} rows (expect 76)")
    if len(out) != 76:
        raise ValueError(f"Table A.2: {len(out)} rows, expected 76 -- stop")

    sources = out["label_source"].unique()
    print(f"  label_source values present: {list(sources)}")
    if len(sources) != 1 or "AI-DRAFT" not in sources[0]:
        raise ValueError("Table A.2: label_source is not uniformly the machine-generated "
                          "draft banner -- stop, this changes what the report's banner "
                          "can claim (docs/VERIFIED_NUMBERS.md §7.1)")
    # docs/FIGURE_ROUND6.md §3: render to markdown, carrying label_source through
    # verbatim (column renamed for sentence case; the AI-draft banner TEXT is
    # not altered).
    render_markdown(out, {"subject": "Patient", "seizure_idx": "Seizure index",
                          "annotated_channels": "Annotated channels",
                          "label_source": "Label source"}, csv_path)
    return out


# ============================================================================
# Table A.3 -- full parameter grid, pass-through. docs/FIGURE_ROUND6.md §3: 384
# rows -- deliberately NOT rendered to markdown. Goes into the report as a CSV
# attachment or a long appendix listing; the chapter file gets a one-line
# pointer to this CSV instead.
# ============================================================================
def emit_table_a3():
    df = pd.read_csv(GRID_CSV)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_DIR / "table_A3_full_grid.csv", index=False)
    print(f"[Table A.3] wrote {len(df)} rows, {df.subject.nunique()} subjects")
    if len(df) != 384:
        raise ValueError(f"Table A.3: {len(df)} rows, expected 384 -- stop")
    if df.subject.nunique() != 8:
        raise ValueError(f"Table A.3: {df.subject.nunique()} subjects, expected 8 -- stop")
    cells_per_subj = df.groupby("subject").size()
    if not (cells_per_subj == 48).all():
        raise ValueError(f"Table A.3: cells per subject not all 48:\n{cells_per_subj} -- stop")
    print("  384 rows, 8 subjects, 48 cells each -- OK")
    return df


def main():
    print("=" * 78)
    emit_table_34()
    print("=" * 78)
    emit_table_a1()
    print("=" * 78)
    emit_table_a2()
    print("=" * 78)
    emit_table_a3()
    print("=" * 78)
    print(f"\nAll four tables written to {OUT_DIR.resolve()}")


if __name__ == "__main__":
    main()
