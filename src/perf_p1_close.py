"""perf_p1_close.py -- close stage P1 of the performance phase in the repo docs (2026-10-06).

Run from the repo root (F:/Study/Thesis/Code). Idempotent: a second run changes nothing.
Reads no seizure label, scores nothing, touches no TEST result.

1. docs/PROVENANCE_V2.md   : sha256 + size of every data/models_v2/*.pt and of the v2 input sets
2. docs/PROJECT_STATUS.md  : dated pointer banner under the title (nothing else edited)
3. docs/RESULTS_OF_RECORD_phaseB.md : dated pointer banner (no number edited)
4. docs/VERIFIED_CORRECTIONS.md     : appends the P1 corrections section
5. archives docs/HANDOVER_PERF_2026-10-06.md -> docs/archive/perf_handover/
6. stages F:/Study/Thesis/Agent/project_upload_2026-10-06/ (docs, summaries, v2 code, inventories)
"""
import hashlib, os, re, shutil, subprocess, sys
from pathlib import Path

ROOT = Path.cwd()
if not (ROOT / "src").is_dir() or not (ROOT / "docs").is_dir():
    sys.exit("run from the repo root F:/Study/Thesis/Code")
AGENT = ROOT.parent / "Agent"
STAGE = AGENT / "project_upload_2026-10-06"
DATE = "2026-10-06"
MARK = "<!-- perf-p1-close 2026-10-06 -->"


def sha256(p, buf=1 << 20):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(buf), b""):
            h.update(b)
    return h.hexdigest()


def read(p):
    return Path(p).read_text(encoding="utf-8")


def write(p, s):
    Path(p).write_text(s, encoding="utf-8", newline="\n")


# ---------------------------------------------------------------- 1. provenance v2
def provenance_v2():
    out = ROOT / "docs" / "PROVENANCE_V2.md"
    lines = [
        "# PROVENANCE_V2 — identity of the v2 GAE checkpoints and input sets (MACHINE-GENERATED)",
        "",
        f"Generated {DATE} by `src/perf_p1_close.py`. Regenerate rather than edit. A v2 checkpoint is",
        "identified by the sha256 below, never by its filename.",
        "",
        "## Checkpoints (`data/models_v2/`)",
        "",
        "| file | bytes | sha256 | note |",
        "|---|---|---|---|",
    ]
    md = ROOT / "data" / "models_v2"
    pts = sorted(md.glob("*.pt")) if md.is_dir() else []
    if not pts:
        sys.exit("no data/models_v2/*.pt found")
    for p in pts:
        note = "SMOKE, not a model of record" if "SMOKE" in p.name.upper() else ""
        lines.append(f"| {p.name} | {p.stat().st_size} | `{sha256(p)}` | {note} |")
    for sub in ("trainset_v2", "testset_v2"):
        d = ROOT / "data" / sub
        files = sorted(d.glob("*.npz")) if d.is_dir() else []
        lines += ["", f"## Input set `data/{sub}/` ({len(files)} npz)", "",
                  "| file | bytes | sha256 |", "|---|---|---|"]
        for p in files:
            lines.append(f"| {p.name} | {p.stat().st_size} | `{sha256(p)}` |")
    write(out, "\n".join(lines) + "\n")
    print(f"[1] wrote {out.relative_to(ROOT)} ({len(pts)} checkpoints)")


# ---------------------------------------------------------------- 2-3. banners
BANNERS = {
    "docs/PROJECT_STATUS.md": (
        "> **⚠️ 2026-10-06 — current state is NOT in this file.** Performance work was re-opened on\n"
        "> 2026-10-05. The current state, the continuous-timeline numbers, the log of every TEST look and the\n"
        "> next plan are in `docs/PERF_PHASE_RECORD.md`, which wins over this file. The report and demo\n"
        "> entries below are as of rev F (2026-09-28)."
    ),
    "docs/RESULTS_OF_RECORD_phaseB.md": (
        "> **Note 2026-10-06 (pointer only; no number below is changed).** Every detection number in this\n"
        "> file is from the **offline protocol**: the timeline is rebuilt from the seizure annotations and its\n"
        "> gaps are filled with bootstrapped scores of artifact-rejected interictal windows. Continuous-timeline\n"
        "> numbers and the performance phase are in `docs/PERF_PHASE_RECORD.md`."
    ),
}


def banners():
    for rel, text in BANNERS.items():
        p = ROOT / rel
        s = read(p)
        if MARK in s:
            print(f"[2] banner already present: {rel}")
            continue
        first, _, rest = s.partition("\n")
        write(p, f"{first}\n{MARK}\n{text}\n\n{rest}")
        print(f"[2] banner added: {rel}")


# ---------------------------------------------------------------- 4. corrections
CORR = """
## {n} · Performance phase, stage P1 (2026-10-06)

Settled by code reading and runs during the performance phase; full log in `PERF_PHASE_RECORD.md`.

- **The offline timeline is not a continuous-recording estimate.** `szcore_eval.build_timeline_masked`
  rebuilds it from the annotations and fills gaps with bootstrapped scores of artifact-rejected interictal
  windows (`src/szcore_eval.py:98–109`). On the real continuous timeline V1 + PELT scores 23/76 at
  73.3 FA/day (`results/continuous_eval/`). Replaces: "F1 0.213 @ 27.4 is the honest headline".
- **The ±5 SD flag means high amplitude, not artifact.** One sample on one channel above 5 SD flags the
  window; it flags 46 % of training interictal windows and ~90 % of seizure windows
  (`results/raw_eeg_view/`). Using it as an artifact label (E4) calls 81.5 % of seizure windows artifact.
- **V1's node features erase amplitude and window spectral shape**: band powers are z-scored within each
  window (`feature_extraction.compute_band_powers`) and min-maxed per band across channels within each
  window (`train_gae_joint.make_window_data`).
- **PELT on the anomaly score alarms on falling change points as well as rising ones**
  (`results/diag_detector_ceiling/`).
- **Precision and F1 come from the scorer's counts.** timescoring: precision = tp/(tp+fp),
  F1 = 2tp/(2tp+fp+(ref−tp)) (read from `timescoring/scoring.py`). The E9 hand formula gave negative
  precision; its precision/F1 columns are invalid.
- **SzCORE's official aggregate is the mean of per-subject metrics** (`szcore-evaluation`,
  `evaluate_dataset(avg_per_subject=True)` by default, `nanmean` over subjects; counts summed within a
  subject; each recording scored separately). The P1 scripts pool counts; both are reported from P2 on.
- **The selection set over-predicts test.** v2: 0.489 @ 19.8 on the 15 non-test subjects (E8), 3/76 @ 24.1
  on test (E9); test seizure peaks are out-ranked by 20–50 % of same-length non-ictal spans vs 4 % on
  validation (`results/oracle_gate_bound/`).
- **The test collapse is not mainly a detection-stage problem** (corrects HANDOVER_PERF §3): a
  local-contrast kernel-CPD detector (E10) and removing long events (D1c) do not raise sensitivity, while
  removing flagged windows (oracle) does.
- **Benchmark rows are read from `esl-epfl/szcore/results/*/chbmit.json`.** A Perplexity row
  "ESL_RF 34.1 % / 1.08 FP/day" is not in that repository and is not cited.
"""


def corrections():
    p = ROOT / "docs" / "VERIFIED_CORRECTIONS.md"
    s = read(p)
    if MARK in s:
        print("[4] corrections already appended")
        return
    nums = [int(x) for x in re.findall(r"^## (\d+) ·", s, flags=re.M)]
    n = max(nums) + 1 if nums else 13
    write(p, s.rstrip("\n") + "\n\n" + MARK + CORR.format(n=n))
    print(f"[4] corrections appended as section {n}")


# ---------------------------------------------------------------- 5. archive handover
def archive_handover():
    src = ROOT / "docs" / "HANDOVER_PERF_2026-10-06.md"
    dst_dir = ROOT / "docs" / "archive" / "perf_handover"
    dst = dst_dir / src.name
    if not src.exists():
        print(f"[5] {src.name} not in docs/ (already archived or never saved)")
        return
    dst_dir.mkdir(parents=True, exist_ok=True)
    tracked = subprocess.run(["git", "ls-files", "--error-unmatch", str(src)],
                             capture_output=True).returncode == 0
    if tracked:
        subprocess.run(["git", "mv", str(src), str(dst)], check=True)
    else:
        shutil.move(str(src), str(dst))
    print(f"[5] archived -> {dst.relative_to(ROOT)} (tracked={tracked})")


# ---------------------------------------------------------------- 6. staging
def inventory(d, out, max_files=6):
    lines = [f"# inventory of {d}"]
    if not d.exists():
        lines.append("MISSING")
    else:
        files = sorted(p for p in d.rglob("*") if p.is_file())
        exts = {}
        for p in files:
            exts[p.suffix] = exts.get(p.suffix, 0) + 1
        lines.append(f"{len(files)} files, by extension: {exts}")
        lines += [f"  {p.relative_to(d)}  {p.stat().st_size} B" for p in files[:40]]
        try:
            import numpy as np
            shown = 0
            for p in files:
                if p.suffix in (".npz", ".npy") and shown < max_files:
                    shown += 1
                    lines.append(f"\n== {p.relative_to(d)}")
                    z = np.load(p, allow_pickle=True)
                    items = z.items() if p.suffix == ".npz" else [("<array>", z)]
                    for k, a in items:
                        a = np.asarray(a)
                        head = a.ravel()[:4].tolist() if a.size and a.dtype != object else ""
                        lines.append(f"  {k}: shape {a.shape} dtype {a.dtype} head {head}")
            for p in files:
                if p.suffix == ".csv":
                    lines.append(f"\n== {p.relative_to(d)} (first 3 lines)")
                    with open(p, encoding="utf-8", errors="replace") as f:
                        lines += ["  " + next(f, "").rstrip() for _ in range(3)]
                    break
        except Exception as e:  # inventory must never stop the close-out
            lines.append(f"inventory error: {e!r}")
    write(out, "\n".join(lines) + "\n")


def stage():
    if STAGE.exists():
        shutil.rmtree(STAGE)
    STAGE.mkdir(parents=True)
    copies = {
        "docs/PERF_PHASE_RECORD.md": "PERF_PHASE_RECORD.md",
        "docs/PROVENANCE_V2.md": "PROVENANCE_V2.md",
        "docs/VERIFIED_CORRECTIONS.md": "VERIFIED_CORRECTIONS.md",
        "docs/PROJECT_STATUS.md": "PROJECT_STATUS.md",
        "docs/RESULTS_OF_RECORD_phaseB.md": "RESULTS_OF_RECORD_phaseB.md",
        "results/e8_gae_v2/SUMMARY.md": "e8_SUMMARY.md",
        "results/e8_gae_v2/diag/per_subject_frozen.csv": "e8_diag_per_subject_frozen.csv",
        "results/e9_test_oneshot/SUMMARY.md": "e9_SUMMARY.md",
        "results/e10_kernel_cpd/SUMMARY.md": "e10_SUMMARY.md",
        "src/retrain/train_gae_v2.py": "train_gae_v2.py",
        "src/c1b_build_trainset.py": "c1b_build_trainset.py",
        "src/c1t_build_testset.py": "c1t_build_testset.py",
        "src/e8_gae_v2_eval.py": "e8_gae_v2_eval.py",
        "src/e9_test_oneshot.py": "e9_test_oneshot.py",
        "src/e10_kernel_cpd.py": "e10_kernel_cpd.py",
    }
    missing = []
    for rel, name in copies.items():
        p = ROOT / rel
        if p.exists():
            shutil.copy2(p, STAGE / name)
        else:
            missing.append(rel)
    gj = [p for p in (ROOT / "src").rglob("gae_joint.py") if "archive" not in p.parts]
    if gj:
        shutil.copy2(gj[0], STAGE / "gae_joint.py")
    else:
        missing.append("src/**/gae_joint.py")
    inventory(ROOT / "results" / "e8_gae_v2" / "scores", STAGE / "_e8_cache_inventory.txt")
    inventory(ROOT / "data" / "trainset_v2", STAGE / "_trainset_v2_inventory.txt", max_files=1)
    rep = ROOT.parent / "Reports"
    rl = [f"# {rep}"] + ([f"{p.name}  {p.stat().st_size} B  mtime {int(p.stat().st_mtime)}"
                          for p in sorted(rep.iterdir()) if p.is_file()] if rep.exists() else ["MISSING"])
    write(STAGE / "_reports_listing.txt", "\n".join(rl) + "\n")
    tr = subprocess.run(["git", "status", "--short", "rank_readout.py", "results/attribution_v7"],
                        capture_output=True, text=True).stdout
    write(STAGE / "_untracked_check.txt", tr or "clean\n")
    write(STAGE / "_missing.txt", "\n".join(missing) + "\n" if missing else "none\n")
    print(f"[6] staged {len(list(STAGE.iterdir()))} files in {STAGE}; missing: {missing or 'none'}")


if __name__ == "__main__":
    for f in ("docs/PERF_PHASE_RECORD.md", "docs/PROJECT_INSTRUCTIONS.md"):
        if not (ROOT / f).exists():
            sys.exit(f"save {f} first")
    provenance_v2()
    banners()
    corrections()
    archive_handover()
    stage()
    print("DONE")
