#!/usr/bin/env python
"""r2_rps_synthetic_test.py -- end-to-end test of RP_SERIES (src/r2_rps.py, the notebook builder) and
src/r2_rps_aggregate.py on SYNTHETIC data (build container only; never on Kaggle, never on real data).

World: the stage-RP synthetic world of src/r2_rp_synthetic_test.py (--base; built by that test: synthetic feature
datasets, the real R1_RUN notebook (3 epochs) as the committed R1 output, the real RP_RUN notebook as the committed RP
output), plus
  attribution  a synthetic channel annotation of the synthetic test seizures (attribution_v6 blocks, attribution_v7
               labels with the order token) and a synthetic "attribution_v8 record" (random scores; tables made by
               cmd_eval7) -> gate RS-attr tests the mechanics, the real-data equivalence is RS-attr on Kaggle;
  raw EEG      synthetic EDF files for the 12 training patients (seizures, high-amplitude bursts; chb12_27 without one
               derivation, refused by the record loader; chb21_11 present), their summaries, a fake PhysioNet (file://
               URLs with SHA256SUMS.txt) and a Kaggle copy missing one file; the R0 references of these files built by R0's
               own builders (r2_core.stats_record + features_record = c1b_build_trainset.build) -> gate G-flags compares
               this module's flag pass with them window by window (non-circular: another code path); the RB1c table of
               the 11 patients from an independent loop.
Checks:
  N1  r2_rps.model_outputs_z gives D = x1_external.model_outputs(z) bit for bit (and latents of the right shape)
  N2  the aggregate's macro / micro selection = a hand computation on a toy table
  RP_SERIES PASS in mode exact: every gate; RS.0 all rows exact and every test score equal; every output present;
  aggregate: A0 on the REAL record grids of this clone, A1 on the synthetic output, every table and the figure
  negative paths (each a fresh run that must STOP): one rp2 row tp + 1 -> RS.0; one stored test score changed -> RS.0;
  one training count in the seed-4 json -> G-alat; one committed attribution_v8 value -> RS-attr; one is_flag5sd of an R0
  reference flipped -> G-flags; one RB1c count -> G-flags; aggregate on an output whose RS.0 failed -> STOP A1
  python src/r2_rps_synthetic_test.py [--base /tmp/rpsynth] [--root /tmp/rps_synth] [--skip-negative]
"""
import argparse
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
_s = importlib.util.spec_from_file_location("r1t", ROOT / "src" / "r2_r1_synthetic_test.py")
T1 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(T1)
_s = importlib.util.spec_from_file_location("r0t", ROOT / "src" / "r2_synthetic_test.py")
T0 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(T0)
RAWNAME = "combined-siena-scalp-and-chb-mit-eeg-datasets"
TRAIN = ["chb01", "chb02", "chb04", "chb05", "chb07", "chb08", "chb09", "chb12", "chb19", "chb20", "chb21", "chb23"]
TEST = ["chb03", "chb06", "chb13", "chb14", "chb15", "chb16", "chb17", "chb18"]
CH = T0.CHB18
GATES = ["G-grid", "G-data", "RS.0", "G-alat", "RS-attr", "G-flags"]

HELPER_ATTR = r'''
# attribution world: blocks, labels, synthetic attribution_v8 record (made with cmd_eval7 itself)
import csv, json, os, sys
from pathlib import Path
import numpy as np, pandas as pd
if __name__ == "__main__":
    sys.path[:0] = [os.environ["R1_SRC"]]
    import r2_rps as RS
    AP, AV8, REPO = RS.AP, RS.AV8, RS.REPO
    ds = Path(os.environ["DS"])
    rng = np.random.default_rng(5)
    blocks, labels = [], []
    for s in AP.TEST_SUBJ:
        z = np.load(ds / f"{s}.npz", allow_pickle=True)
        fidx, ict = z["file_idx"].astype(int), z["is_ictal"].astype(bool)
        k = 0
        for f in np.unique(fidx):
            m = np.flatnonzero(fidx == f)
            i = 0
            while i < len(m):
                if ict[m[i]]:
                    j = i
                    while j < len(m) and ict[m[j]]:
                        j += 1
                    blocks.append(dict(subject=s, seizure_idx=k, edf_file=str(z["files"][f]), onset_s=i * 4, offset_s=j * 4,
                                       n_windows=j - i))
                    gen = (s == "chb06" and k == 1)
                    ch = list(AP.CH) if gen else list(rng.choice(AP.CH, size=int(rng.integers(2, 7)), replace=False))
                    labels.append(dict(subject=s, seizure_idx=k, focal_generalized="generalized" if gen else "focal",
                                       n_ictal=len(ch), ictal_channels="|".join(ch)))
                    k += 1
                    i = j
                else:
                    i += 1
    (REPO / "results/attribution_v6").mkdir(parents=True, exist_ok=True)
    (REPO / "results/attribution_v7/labels").mkdir(parents=True, exist_ok=True)
    (REPO / "results/attribution_v8").mkdir(parents=True, exist_ok=True)
    pd.DataFrame(blocks).to_csv(REPO / "results/attribution_v6/seizure_blocks.csv", index=False)
    pd.DataFrame(labels).to_csv(REPO / "results/attribution_v7/labels/ictal_channels_FINAL.csv", index=False)
    (REPO / "results/attribution_v7/labels/parse_log.txt").write_text(f"synthetic\n{AP.CONFIRM_TOKEN} synthetic\n")
    print(len(blocks), "synthetic test seizures")
    assert len(blocks) == int(os.environ["R2_TEST_N_TEST_SEIZURES"]), len(blocks)
    AV8.TESTSET = ds
    rows, spans = AV8.align()
    nw = {}
    for (s, k), ww in spans.items():
        sl = np.load(ds / f"{s}.npz", allow_pickle=True)["is_signal_loss"].astype(bool)
        nw[(s, k)] = int((~sl[ww]).sum())
    for r in rows:
        r["n_windows_scored"] = nw[(r["subject"], r["seizure_idx"])]
    AP.write_csv(REPO / "results/attribution_v8/alignment.csv", rows)
    out = []
    for seed in (42, 1, 2, 3):
        for agg in ("mean", "p95"):
            for (s, k) in sorted(spans):
                v = np.abs(rng.normal(1, 1, 18))
                out += [dict(seed=seed, agg=agg, subject=s, seizure_idx=k, ch_idx=i, ch_name=AP.CH[i], score=round(float(v[i]), 6))
                        for i in range(18)]
    pd.DataFrame(out).to_csv(REPO / "results/attribution_v8/attribution_scores.csv", index=False)
    S = {}
    for r in csv.DictReader(open(REPO / "results/attribution_v8/attribution_scores.csv")):
        S.setdefault((int(r["seed"]), r["agg"], r["subject"], int(r["seizure_idx"])), np.zeros(18))[int(r["ch_idx"])] = float(r["score"])
    RS.run_eval7(S, nw, REPO / "results/attribution_v8")
    print("synthetic attribution_v8 record written")
'''

HELPER_FLAGS = r'''
# raw-EEG world: R0 references by R0's own builders (stats_record + features_record = c1b.build) and an RB1c-like table
import json, os, sys
from pathlib import Path
import numpy as np, pandas as pd
if __name__ == "__main__":
    sys.path[:0] = [os.environ["R1_SRC"]]
    import r2_core as R0
    import preprocessing as P
    import continuous_eval as CE
    view, ref = Path(os.environ["RAWVIEW"]), Path(os.environ["FLAGS_REF"])
    ref.mkdir(parents=True, exist_ok=True)
    rb = []
    for c in sorted(p.name for p in (view / "chbmit").iterdir()):
        st = R0.stats_record(c, view, ref / f"_log_{c}.txt")
        st.pop("r2", None)
        p = R0.features_record(c, view, st, ref, ref / f"_flog_{c}.txt")
        Path(p).replace(ref / f"{c}.npz")
        (ref / f"{c}_stats.json").write_text(json.dumps(st, indent=1))
        thr = np.asarray(st["artifact_thresh_uV"]) * 1e-6
        smap = P.parse_summary(view / "chbmit" / c / f"{c}-summary.txt")
        ni = nf = 0
        for f in sorted((view / "chbmit" / c).glob("*.edf")):
            if P.open_edf(f) is None:
                continue
            filt, n = CE.filter_file(f)
            peak = np.abs(filt.astype(np.float64)).max(axis=2)
            lab = P.build_labels(n * 4, smap.get(f.name, [])).reshape(n, 4).max(axis=1) == 1
            ni += int(lab.sum()); nf += int(((peak > thr[None, :]).any(axis=1) & lab).sum())
        rb.append(dict(case=c, ictal_windows=ni, ictal_over_record_threshold=(nf / ni) if ni else float("nan")))
        print(c, "reference built", ni, nf, flush=True)
    out = Path(os.environ["THESIS_REPO"]) / "results/r2/r0_data/rb1c"
    out.mkdir(parents=True, exist_ok=True)
    pd.DataFrame([r for r in rb if r["case"] != "chb12"]).to_csv(out / "cases.csv", index=False)
'''

CHECK_N1 = r'''
import os, sys
from pathlib import Path
import numpy as np
if __name__ == "__main__":
    sys.path[:0] = [os.environ["R1_SRC"]]
    import r2_rps as RS
    RP, R1 = RS.RP, RS.R1
    R1.STATE["tag"] = "n1"
    RP.build_views()
    RP.set_tags(RS.TAGS)
    RS.PD.CKPT = RP.ckpt_dir_all(RS.RP_DIR / "models")
    z, _ = R1.load_case("chb05", "new")
    idx, D, Z = RS.model_outputs_z(z)
    idx2, D2 = RS.X1.model_outputs(z)
    assert np.array_equal(idx, idx2) and all(np.array_equal(D[t], D2[t]) for t in RS.TAGS), "D differs"
    assert all(Z[t].shape == (len(idx), 18, 16) and Z[t].dtype == np.float32 for t in RS.TAGS)
    print("N1: model_outputs_z D = x1_external.model_outputs D bit for bit; latents (n, 18, 16) float32")
'''


def write_raw_world(root):
    """12 training patients: 1-3 short EDF files each, summaries; chb12_27 lacks one derivation; chb21_11 present."""
    raw = root / "raw" / "chbmit"
    files = {}
    rng = np.random.default_rng(11)
    for i, c in enumerate(TRAIN):
        fl = [(f"{c}_01.edf", 4, [(int(rng.integers(60, 120)), 0)], None), (f"{c}_02.edf", 3, [], None)]
        fl[0] = (fl[0][0], 4, [(fl[0][2][0][0], fl[0][2][0][0] + int(rng.integers(16, 40)))], None)
        if c == "chb12":
            fl.append(("chb12_27.edf", 3, [(40, 70)], None))
        if c == "chb21":
            fl.append(("chb21_11.edf", 3, [], None))
        files[c] = fl
        (raw / c).mkdir(parents=True, exist_ok=True)
        for j, (f, m, sz, flat) in enumerate(fl):
            T0.write_chb_edf(raw / c / f, m, sz, flat, 1000 + 10 * i + j, missing="FP1-F7" if f == "chb12_27.edf" else None)
        (raw / c / f"{c}-summary.txt").write_text(T0.chb_summary(c, fl))
    return raw, files


def fake_physionet_and_kaggle(root, raw):
    phys = root / "physionet" / "chbmit"
    shutil.copytree(raw, phys)
    lines = [f"{T0.sha(p)}  {p.relative_to(phys).as_posix()}" for p in sorted(phys.rglob("*")) if p.is_file()]
    (phys / "SHA256SUMS.txt").write_text("\n".join(lines) + "\n")
    kag = root / "input" / RAWNAME / "chbmit"
    shutil.copytree(raw, kag)
    (kag / "chb05" / "chb05_02.edf").unlink()                       # absent on "Kaggle": taken from "PhysioNet"
    return phys


def toy_selection():
    sys.path[:0] = [str(ROOT / "src")]
    import r2_rps_aggregate as A
    rows = []
    for seed in ("s1", "s2"):
        for cell, (tp_a, fp_a, tp_b, fp_b) in {1: (1, 1, 2, 0), 2: (2, 30, 2, 30)}.items():
            rows += [dict(seed=seed, subject="a", c=cell, tp=tp_a, fp=fp_a, n_ref=2, nonict_h=24.0),
                     dict(seed=seed, subject="b", c=cell, tp=tp_b, fp=fp_b, n_ref=4, nonict_h=24.0)]
    df = pd.DataFrame(rows)
    ma = A.select(df, ["c"], "macro")       # cell 1: sens (0.5 + 0.5)/2 = 0.5, fa (1 + 0)/2 = 0.5; cell 2 fa 30 > 25
    mi = A.select(df, ["c"], "micro")       # cell 1: pooled 3/6 = 0.5, fa 1/48*24 = 0.5
    assert ma["cell_c"] == 1 and abs(ma["sens"] - 0.5) < 1e-12 and abs(ma["fa"] - 0.5) < 1e-12, ma
    assert mi["cell_c"] == 1 and abs(mi["micro_sens"] - 0.5) < 1e-12 and abs(mi["micro_fa"] - 0.5) < 1e-12, mi
    df2 = df.copy()
    df2.loc[(df2.c == 2), "fp"] = 0                                # cell 2 feasible: macro (1 + 0.5)/2 = 0.75 wins
    ma2 = A.select(df2, ["c"], "macro")
    assert ma2["cell_c"] == 2 and abs(ma2["sens"] - 0.75) < 1e-12 and abs(ma2["micro_sens"] - 4 / 6) < 1e-12, ma2
    print("N2: macro / micro selection = hand computation")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="/tmp/rpsynth")
    ap.add_argument("--root", default="/tmp/rps_synth")
    ap.add_argument("--skip-negative", action="store_true")
    a = ap.parse_args()
    t0 = time.time()
    base, root = Path(a.base), Path(a.root)
    if not (base / "work_rp" / "r2" / "r1_system" / "rp" / "demo_model.json").exists():
        subprocess.check_call([sys.executable, str(ROOT / "src" / "r2_rp_synthetic_test.py"), "--root", str(base)])
    shutil.rmtree(root, ignore_errors=True)
    shutil.copytree(base / "repo", root / "repo", symlinks=True)
    shutil.copytree(base / "input", root / "input", symlinks=True)
    repo, inp = root / "repo", root / "input"
    for p in (ROOT / "src").glob("*.py"):                              # this clone's code (record modules unchanged)
        shutil.copyfile(p, repo / "src" / p.name)
    for rel in ("results/e16_recording_baseline", "results/e10_kernel_cpd", "results/e7_ensemble_cpd",
                "results/p3b_diag"):
        if not (repo / rel).exists():
            (repo / rel).mkdir(parents=True)
    shutil.copytree(base / "work_rp" / "r2" / "r1_system" / "rp", repo / "results/r2/r1_system/rp")
    (root / "runner.py").write_text(T1.RUNNER)
    ds = inp / "datasets/u/thesis-r2-chbmit-features/thesis-r2-chbmit-features"
    n_sz = 0
    for c in TEST:
        z = np.load(ds / f"{c}.npz", allow_pickle=True)
        ict = z["is_ictal"].astype(bool)
        n_sz += int((np.diff(np.r_[0, ict.astype(int)]) == 1).sum())
    base_env = dict(R2_TEST="1", THESIS_REPO=str(repo), R1_SRC=str(repo / "src"), OMP_NUM_THREADS="1",
                    OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1", PYTHONHASHSEED="0", R2_TEST_N_TEST_SEIZURES=str(n_sz))
    # attribution world
    (root / "helper_attr.py").write_text(HELPER_ATTR)
    print(T1.run(root / "helper_attr.py", dict(base_env, DS=str(ds), R2_INPUT=str(inp), R2_WORK=str(root / "h_work"),
                                               R2_SCRATCH=str(root / "h_scratch")))[-300:])
    # raw-EEG world
    raw, _ = write_raw_world(root)
    (repo / "data" / "summaries").mkdir(parents=True, exist_ok=True)
    for c in TRAIN:
        shutil.copyfile(raw / c / f"{c}-summary.txt", repo / "data" / "summaries" / f"{c}-summary.txt")
    phys = fake_physionet_and_kaggle(root, raw)
    (root / "helper_flags.py").write_text(HELPER_FLAGS)
    fref = root / "flags_ref"
    print(T1.run(root / "helper_flags.py", dict(base_env, RAWVIEW=str(root / "raw"), FLAGS_REF=str(fref),
                                                R2_INPUT=str(inp), R2_WORK=str(root / "h_work"),
                                                R2_SCRATCH=str(root / "h_scratch")))[-600:])
    # N1, N2
    (root / "check_n1.py").write_text(CHECK_N1)
    print(T1.run(root / "check_n1.py", dict(base_env, R2_INPUT=str(inp), R2_WORK=str(root / "n1_work"),
                                            R2_SCRATCH=str(root / "n1_scratch"))))
    toy_selection()
    # notebook
    nbdir = root / "notebooks"
    subprocess.check_call([sys.executable, str(ROOT / "src" / "r2_rps_make_notebook.py"), "--run", "0" * 40],
                          env=dict(os.environ, R2_NB_OUTDIR=str(nbdir)))
    nb = nbdir / "RP_SERIES.ipynb"

    def nb_env(tag, extra=None):
        e = dict(base_env, R2_TEST_REPO=str(repo), R2_TEST_INPUT=str(inp), R2_TEST_WORK=str(root / f"work_{tag}"),
                 R2_TEST_SCRATCH=str(root / f"scratch_{tag}"), R2_TEST_FLAGS_REF=str(fref),
                 R2_PHYSIONET_CHBMIT=phys.as_uri() + "/", R2_PHYSIONET_SIENA=(root / "physionet" / "siena").as_uri() + "/")
        for k in ("THESIS_REPO", "R1_SRC"):
            e.pop(k, None)
        e.update(extra or {})
        return e
    t1 = time.time()
    print(T1.run(root / "runner.py", nb_env("ok"), [nb])[-2500:])
    print(f"positive run {time.time() - t1:.0f} s")
    out = root / "work_ok/r2/r1_system/rp_series"
    g = {x["gate"]: x for x in json.loads((out / "gates.json").read_text())}
    assert all(g[w]["status"] == "PASS" for w in GATES), {w: g.get(w, {}).get("status") for w in GATES}
    r0 = g["RS.0"]
    assert r0["mode"] == "exact" and r0["exact_rows"] == r0["rows"] == r0["rows_expected"] == 23 * 4 * 4 * 3, r0
    assert r0["score_rows"] == 32 and r0["score_rows_differ"] == 0 and r0["q_differ"] == 0, r0
    assert g["G-flags"]["files"] == 12 * 2 + 1 and g["G-flags"]["refused"] == {"chb12": ["chb12_27.edf"]}, g["G-flags"]
    for f in ("rs0/per_subject.csv", "rs0/scores_cmp.csv", "grid_e16.csv", "mechanism.csv", "diagnostics.csv",
              "grid_d1b.csv", "table7.csv", "flags.csv", "flags_files.csv", "e1_chb03_seed3.csv", "timing.csv",
              "rp5/alignment.csv", "rp5/attribution_scores.csv", "rp5/seed_map.json", "SUMMARY.md", "data_sha256.csv",
              "inventory/inventory.csv"):
        assert (out / f).exists(), f
    for s in (1, 2, 3, 4):
        assert (out / f"rp5/seed{s}/attribution_tests.csv").exists()
    e1 = pd.read_csv(out / "e1_chb03_seed3.csv")
    assert set(e1.file_idx) == {0, 1, 2} and np.allclose(e1.s9 - e1.running_median, e1.s9_corrected), "e1"
    fl = pd.read_csv(out / "flags.csv")
    assert (fl[fl.case != "chb12"].rb1c_equal == True).all() and fl.ictal.sum() > 0 and fl.ictal_flagged.sum() > 0, fl  # noqa: E712
    print("RP_SERIES PASS (mode exact; RS.0 every row and score exact; G-alat, RS-attr, G-flags PASS; outputs present)")
    # aggregate: A0 on the real record grids of this clone, A1 on the synthetic output
    env_agg = {k: v for k, v in os.environ.items() if not k.startswith("R2_TEST")}
    env_agg["THESIS_REPO"] = str(ROOT)
    p = subprocess.run([sys.executable, str(ROOT / "src" / "r2_rps_aggregate.py"), "--series", str(out)], env=env_agg,
                       capture_output=True, text=True)
    assert p.returncode == 0 and "A0 PASS" in p.stdout and "A1 PASS" in p.stdout, p.stdout[-3000:] + p.stderr[-3000:]
    for f in ("table6.csv", "table7.csv", "budget.csv", "drift.csv", "seizure_z.csv", "flags.csv", "rp5.csv",
              "rp5_per_seed.csv", "e1_figure.png", "SUMMARY.md", "gates.json"):
        assert (out / "aggregate" / f).exists(), f
    t6 = pd.read_csv(out / "aggregate/table6.csv")
    assert len(t6) == 7 * 3 * 2, len(t6)
    print("aggregate PASS (A0 real record, A1 synthetic output, every table, figure)")
    gj = out / "gates.json"
    keep = gj.read_bytes()
    gg = json.loads(keep)
    for x in gg:
        if x["gate"] == "RS.0":
            x["status"] = "FAIL"
    gj.write_text(json.dumps(gg))
    p = subprocess.run([sys.executable, str(ROOT / "src" / "r2_rps_aggregate.py"), "--series", str(out), "--out",
                        str(root / "agg_neg")], env=env_agg, capture_output=True, text=True)
    assert p.returncode != 0 and "STOP A1" in (p.stdout + p.stderr), p.stdout[-2000:] + p.stderr[-2000:]
    gj.write_bytes(keep)
    print("aggregate negative: RS.0 not PASS -> STOP A1")
    if a.skip_negative:
        print(f"ALL PASS (negative notebook paths skipped) ({time.time() - t0:.0f} s)")
        return

    def perturb(path, fn):
        keep = path.read_bytes()
        fn(path)
        return keep

    def csv_edit(fn, compression=None):
        def f(path):
            d = pd.read_csv(path)
            fn(d)
            d.to_csv(path, index=False, compression=compression, float_format="%.7g" if compression else None)
        return f
    rp = repo / "results/r2/r1_system/rp"
    cases = [
        ("rs0_row", rp / "rp2/per_subject.csv",
         csv_edit(lambda d: d.__setitem__("tp", d.tp + ((d.subject == "chb05") & (d.seed == "clean_seed2")
                                                        & (d.budget == "L2f") & (d.stage == "cpd")).astype(int))), "RS.0 FAIL"),
        ("rs0_score", rp / "rp2/scores/chb03.csv.gz",
         csv_edit(lambda d: d.__setitem__("x_s3", d.x_s3.where(d.index != 10, d.x_s3 + 0.01)), "gzip"), "RS.0 FAIL"),
        ("galat", rp / "models/gae_v2_clean_seed4.json",
         lambda p: p.write_text(json.dumps({**json.loads(p.read_text()), "n_train": {
             k: v + (k == "chb05") for k, v in json.loads(p.read_text())["n_train"].items()}}, indent=1)), "G-alat FAIL"),
        ("attr", repo / "results/attribution_v8/attribution_summary.csv",
         csv_edit(lambda d: d.__setitem__("macro_AUROC", d.macro_AUROC.where(d.index != 0, d.macro_AUROC + 0.0001))), "RS-attr FAIL"),
        ("rb1c", repo / "results/r2/r0_data/rb1c/cases.csv",
         csv_edit(lambda d: d.__setitem__("ictal_windows", d.ictal_windows + (d.case == "chb01").astype(int))), "G-flags FAIL"),
    ]

    def flip_flag(p):
        z = dict(np.load(p, allow_pickle=True))
        i = int(np.flatnonzero(~z["is_ictal"].astype(bool) & ~z["is_buffer"].astype(bool))[3])
        z["is_flag5sd"] = z["is_flag5sd"].copy()
        z["is_flag5sd"][i] = ~z["is_flag5sd"][i]
        with open(p, "wb") as fh:
            np.savez(fh, **z)
    cases.append(("flag", fref / "chb05.npz", flip_flag, "G-flags FAIL"))
    for tag, path, fn, msg in cases:
        keep = perturb(path, fn)
        try:
            T1.run(root / "runner.py", nb_env(f"neg_{tag}"), [nb], expect_fail=msg)
        finally:
            path.write_bytes(keep)
        print(f"negative {tag}: STOP ({msg})")
    print(f"ALL PASS ({time.time() - t0:.0f} s)")


if __name__ == "__main__":
    main()
