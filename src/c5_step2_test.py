#!/usr/bin/env python
"""
c5_step2_test.py -- synthetic test of SzScan Step 2 (chat C5; results/c5_szscan/DESIGN_STEP2.md). No real EEG.

Each rule is shown to act on the case it is for and to leave the others alone; each gate has a failing case.
  E1  referential input (Siena-like labels, T3-T6 aliases, 512 Hz) = x1_external.load_18 (exact)            [G3]
  E2  hospital-like input (103 signals, '-REF' suffixes, non-EEG channels) is read; one electrode x12 is flagged
      bad (z > 5), interpolated only when asked; a flat electrode is flagged; > 3 bad -> refused              [C7]
  E3  mains rule: 50-Hz line -> 50, 60-Hz line -> 60, no line -> no suggestion (auto refuses)                 [C5, G4]
  E4  truncated header -> notice with durations only                                                         [C6]
  E5  bipolar CHB-like input -> Phase A arrays identical to the pre-Step-2 operations (open_edf, 60 Hz)      [G1 premise]
  E6  file engine (engine_file.run_file on the app's caches) = the m2l_core chain on the raw signal: same
      distances, same events; a 20-min file -> no event (minimum 30 min)                                     [G2 premise]
  E7  the whole app on a temporary database (FastAPI TestClient): project-id rules, session and file modes,
      mains mismatch inside a study, private study (person name in the file name and the header) -> the name,
      the header fields and the date appear nowhere (database bytes, cache names, EDF copy, API, action log,
      export, backend log); action log one row per action, append-only, CSV = table                          [G7, G8]
  E10 memory-light reading (Step 2a fix, second version without memory maps): a 25-min 512-Hz referential file
      read derivation by derivation into a plain disk file = x1_external.load_18 (exact); Phase A on it = the
      whole-file operations (filtered, band-pass, raw, flags, moments; exact); no temporary file is left after
      Phase A or after a refused file; the interpolation matrix = MNE's whole-recording interpolate_bads (rounding
      only); process-memory growth of Phase A (file pages included) below half of load_18's                    [C8]
Run: PYTHONUTF8=1 python src/c5_step2_test.py   -> ALL PASS or the failing items (exit code 1).
"""
import csv
import io
import json
import logging
import os
import shutil
import sqlite3
import sys
import tempfile
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "web_demo" / "backend"
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(ROOT / "src"))
os.environ.setdefault("ADMIN_USER", "c5_test_user")
os.environ.setdefault("ADMIN_PASS", "c5_test_pass")

import pipeline_demo as pdm          # noqa: E402
import edf_input as EI               # noqa: E402
import engine_file as EF             # noqa: E402
import db                            # noqa: E402
import upload_manager as um          # noqa: E402

X1, P = pdm.X1, pdm.preprocessing
RESULTS = []
PERSON = "Nguyen Van Testperson"


def check(name, cond, detail=""):
    RESULTS.append((name, bool(cond)))
    print(f"{'PASS' if cond else 'FAIL'}  {name}  {detail}", flush=True)


def write_edf(path, labels, fs, data_uv, patient="X X X X", startdate="01.01.01", starttime="12.00.00",
              header_records=None, phys=(-6400.0, 6400.0)):
    data_uv = np.asarray(data_uv, float)
    ns, n = data_uv.shape
    n_rec = n // fs
    def f(x, w):
        t = str(x)[:w]
        return t + " " * (w - len(t))
    h = f("0", 8) + f(patient, 80) + f("Startdate " + startdate + " X X X", 80) + f(startdate, 8) + f(starttime, 8)
    h += f(256 + 256 * ns, 8) + f("", 44) + f(n_rec if header_records is None else header_records, 8) + f(1, 8)
    h += f(ns, 4)
    cols = [("label", 16), ("tr", 80), ("dim", 8), ("pmin", 8), ("pmax", 8), ("dmin", 8), ("dmax", 8), ("pre", 80),
            ("ns", 8), ("res", 32)]
    for key, w in cols:
        for i in range(ns):
            h += f(dict(label=labels[i], tr="", dim="uV", pmin=phys[0], pmax=phys[1], dmin=-32768, dmax=32767, pre="",
                        ns=fs, res="")[key], w)
    gain = (phys[1] - phys[0]) / 65535
    dig = np.clip(np.round((data_uv[:, :n_rec * fs] - phys[0]) / gain - 32768), -32768, 32767).astype("<i2")
    Path(path).write_bytes(h.encode("latin-1") + dig.reshape(ns, n_rec, fs).transpose(1, 0, 2).tobytes())


REF19 = ["FP1", "FP2", "F3", "F4", "C3", "C4", "P3", "P4", "O1", "O2", "F7", "F8", "T3", "T4", "T5", "T6", "FZ", "CZ",
         "PZ"]


def eeg(n_sig, seconds, fs, seed, line_hz=None, line_uv=15.0):
    rng = np.random.default_rng(seed)
    t = np.arange(int(seconds * fs)) / fs
    x = rng.normal(0, 30, (n_sig, len(t)))
    for k in range(n_sig):                       # some slow activity so the band-pass sees signal
        x[k] += 20 * np.sin(2 * np.pi * (6 + k % 5) * t + k)
    if line_hz:
        x += line_uv * np.sin(2 * np.pi * line_hz * t)[None]
    return x


CHB23 = ["FP1-F7", "F7-T7", "T7-P7", "P7-O1", "FP1-F3", "F3-C3", "C3-P3", "P3-O1", "FP2-F4", "F4-C4", "C4-P4", "P4-O2",
         "FP2-F8", "F8-T8", "T8-P8", "P8-O2", "FZ-CZ", "CZ-PZ", "P7-T7", "T7-FT9", "FT9-FT10", "FT10-T8", "T8-P8"]


def main():
    root = Path(tempfile.mkdtemp(prefix="c5s2_"))
    try:
        # ── E1 referential Siena-like at 512 Hz = x1_external.load_18
        p1 = root / "sienalike.edf"
        write_edf(p1, [f"EEG {e.capitalize()}" for e in REF19] + ["EKG EKG"], 512, eeg(20, 300, 512, 1, 50))
        d_app, meta = EI.load_any(p1, mains=50.0)
        d_x1 = X1.load_18(p1, "siena")
        check("E1 referential 512 Hz = x1_external.load_18 (exact)",
              d_app.shape == d_x1.shape and np.array_equal(d_app, d_x1), f"{meta['montage']}, fs_in {meta['fs_in']}")
        # ── E2 hospital-like: 103 signals, '-REF' suffixes, bad electrodes
        labs = [f"EEG {e}-REF" for e in REF19] + [f"POL X{i}" for i in range(84)]
        x = eeg(103, 600, 256, 2, 50)
        x[REF19.index("C3")] *= 12
        p2 = root / "hosplike.edf"
        write_edf(p2, labs, 256, x, phys=(-32000.0, 32000.0))
        _, m_no = EI.load_any(p2, mains=50.0, interpolate=False)
        d_yes, m_yes = EI.load_any(p2, mains=50.0, interpolate=True)
        check("E2 hospital-like read, C3 x12 flagged bad", m_no["bad"] == ["C3"] and m_no["interpolated"] == [],
              str(m_no["bad"]))
        check("E2 interpolated only when asked, notice given",
              m_yes["interpolated"] == ["C3"] and "interpolated" in " ".join(m_yes["notices"]))
        z = {t["electrode"]: t["z"] for t in m_no["electrodes"]}
        others = max(abs(v) for k, v in z.items() if k != "C3")
        check("E2 no other electrode flagged (largest other |z| < 5)", others < 5, f"{others:.2f}")
        x3 = eeg(103, 600, 256, 3, 50)
        x3[REF19.index("O2")] = 0.0
        p3 = root / "flat.edf"
        write_edf(p3, labs, 256, x3, phys=(-32000.0, 32000.0))
        _, m3 = EI.load_any(p3, mains=50.0)
        check("E2 flat electrode flagged", m3["bad"] == ["O2"], str(m3["bad"]))
        x4 = eeg(103, 600, 256, 4, 50)
        for e in ("C3", "C4", "P3", "P4"):
            x4[REF19.index(e)] *= 15
        p4 = root / "fourbad.edf"
        write_edf(p4, labs, 256, x4, phys=(-32000.0, 32000.0))
        try:
            EI.load_any(p4, mains=50.0); check("E2 more than 3 bad electrodes refused", False)
        except EI.InputError as e:
            check("E2 more than 3 bad electrodes refused", "4 electrodes" in str(e), str(e)[:60])
        # ── E3 mains rule
        for hz in (50, 60):
            pm = root / f"line{hz}.edf"
            write_edf(pm, CHB23, 256, eeg(23, 300, 256, 10 + hz, hz))
            _, mm = EI.load_any(pm, mains="auto")
            check(f"E3 {hz}-Hz line -> {hz} Hz", mm["notch_hz"] == float(hz), f"ratios {mm['mains_ratios']}")
        pn = root / "noline.edf"
        write_edf(pn, CHB23, 256, eeg(23, 300, 256, 77, None))
        try:
            EI.load_any(pn, mains="auto"); check("E3 no line -> no suggestion, auto refuses", False)
        except EI.InputError as e:
            check("E3 no line -> no suggestion, auto refuses", "could not be determined" in str(e))
        # ── E4 truncated header
        pt = root / "trunc.edf"
        write_edf(pt, CHB23, 256, eeg(23, 600, 256, 5, 60), header_records=1200)
        _, mt = EI.load_any(pt, mains=60.0)
        nt = " ".join(mt["notices"])
        check("E4 truncated header -> notice with durations", "declares 0.33 h" in nt and "holds 0.17 h" in nt, nt)
        # ── E5 bipolar Phase A = the pre-Step-2 operations
        pb = root / "chbx_01.edf"
        write_edf(pb, CHB23, 256, eeg(23, 1200, 256, 6, 60), starttime="11.42.54")
        pa = pdm.process_file_phase_a(str(pb), None, root / "pa", mains=60.0)
        raw = P.open_edf(str(pb))
        data = raw.get_data().astype(np.float64)
        n = data.shape[1] // 1024
        bp = __import__("scipy.signal", fromlist=["sosfiltfilt"]).sosfiltfilt(P._BP_SOS, data, axis=1)
        nf = __import__("scipy.signal", fromlist=["filtfilt"]).filtfilt(P._NOTCH_B, P._NOTCH_A, bp, axis=1)
        old = np.ascontiguousarray(nf[:, :n * 1024].reshape(18, n, 1024).transpose(1, 0, 2)).astype(np.float32)
        oldm = np.empty((n, 18, 2))
        for i in range(n):
            w = X1.window_padded(data, i, 60.0); oldm[i, :, 0] = w.sum(1); oldm[i, :, 1] = (w * w).sum(1)
        check("E5 bipolar Phase A filtered + moments = pre-Step-2 operations (exact)",
              np.array_equal(np.load(pa.filtered_path), old) and np.array_equal(np.load(pa.moments_path), oldm)
              and pa.start_time == raw.info["meas_date"])
        # ── E6 file engine = m2l chain
        import m2l_core as M
        pe = root / "chbf_01.edf"
        xe = eeg(23, 40 * 60, 256, 8, 60)
        xe[:, 900 * 256:960 * 256] *= 6                       # a strong rhythmic stretch
        write_edf(pe, CHB23, 256, xe)
        pa = pdm.process_file_phase_a(str(pe), None, root / "pe", mains=60.0)
        r = EF.run_file(np.load(pa.filtered_path, mmap_mode="r"), np.load(pa.flag_path), np.load(pa.fsamp_path))
        s = EF.settings()
        dat = X1.load_18(pe, "chb")
        n = dat.shape[1] // 1024
        mu, sd = M.stats_of(M.sampled(dat, 60.0, n), "B", M.c_table())
        rec = M.features(dat, 60.0, [], (mu, sd))
        _, Z = M.latents(rec, ["clean_seed42"])
        D = M.distances(Z["clean_seed42"], "MCD")
        ok = ~rec["is_signal_loss"]
        ctx = M.onefile_ctx(n, ok, {"clean_seed42": D})
        xx, smm = M.series(ctx, "clean_seed42")
        q = M.P3L.q_of(smm, s["k"])
        top, st, _ = M.detect(M.onefile_ctx(n, ok), xx, q, *M.FLOORS["F"])
        ref_ev = [(float(a), float(b)) for a, b in st["cpd"].get(0, [])]
        check("E6 file engine distances = m2l_core chain (exact)", np.array_equal(r["dist"][ok], D))
        check("E6 file engine events = m2l_core chain", r["events"] == ref_ev and len(ref_ev) > 0,
              f"{len(ref_ev)} events, top {top:.4f}")
        ps = root / "chbs_01.edf"
        write_edf(ps, CHB23, 256, eeg(23, 20 * 60, 256, 9, 60))
        pa = pdm.process_file_phase_a(str(ps), None, root / "ps", mains=60.0)
        rs = EF.run_file(np.load(pa.filtered_path, mmap_mode="r"), np.load(pa.flag_path), np.load(pa.fsamp_path))
        check("E6 20-min file: no event (minimum 30 min)", rs["short"] and rs["events"] == [])
        # ── E10 memory-light reading
        e10(root)
        # ── E7 the whole app, temporary state
        e7(root, pb)
    finally:
        shutil.rmtree(root, ignore_errors=True)
    bad = [r for r in RESULTS if not r[1]]
    print(f"\n{'ALL PASS' if not bad else f'{len(bad)} FAIL'} ({len(RESULTS)} checks)")
    return 0 if not bad else 1


def e10(root):
    import tracemalloc
    import mne
    from scipy.signal import filtfilt, sosfiltfilt, resample_poly
    labels = [f"EEG {e.capitalize()}" for e in REF19] + ["EKG EKG"]
    pl = root / "longref.edf"
    write_edf(pl, labels, 512, eeg(20, 1500, 512, 21, 50))
    wd = root / "wd"
    wd.mkdir()
    d_app, meta = EI.load_any(pl, mains=50.0, workdir=wd)
    d_x1 = X1.load_18(pl, "siena")
    check("E10 referential read per derivation into a plain disk file = x1_external.load_18 (exact)",
          d_app.shape == d_x1.shape and np.array_equal(np.asarray(d_app), d_x1) and meta["data_path"] is not None
          and isinstance(d_app, EI.DiskRows),
          f"{d_app.shape[1] / 256 / 60:.0f} min, disk file without memory map: {isinstance(d_app, EI.DiskRows)}")
    EI.drop_temp(meta["data_path"], d_app)
    del d_app
    cache = root / "pl"
    pa = pdm.process_file_phase_a(str(pl), None, cache, mains=50.0)
    sos, b, a = X1.filters(50.0)
    n = d_x1.shape[1] // 1024
    bp = sosfiltfilt(sos, d_x1, axis=1)
    nf = filtfilt(b, a, bp, axis=1)
    win = lambda x: np.ascontiguousarray(x[:, :n * 1024].reshape(18, n, 1024).transpose(1, 0, 2))
    raw64 = win(d_x1)
    ok = (np.array_equal(np.load(pa.filtered_path), win(nf).astype(np.float32))
          and np.array_equal(np.load(pa.bandpass_path), win(bp).astype(np.float32))
          and np.array_equal(np.load(pa.raw_path), raw64.astype(np.float32))
          and np.array_equal(np.load(pa.flag_path), pdm.compute_signal_loss_flags(raw64))
          and np.array_equal(np.load(pa.moments_path), pdm.padded_window_moments(d_x1, n, 50.0)))
    check("E10 Phase A per derivation = whole-file operations (filtered, band-pass, raw, flags, moments; exact)", ok)
    left = sorted(q.name for q in cache.glob("_c5_*")) + sorted(q.name for q in wd.glob("_c5_*"))
    check("E10 no temporary file left after Phase A", not left, str(left))
    pq = root / "longref_noline.edf"
    write_edf(pq, labels, 512, eeg(20, 700, 512, 22, None))
    try:
        EI.load_any(pq, mains="auto", workdir=wd); refused = False
    except EI.InputError:
        refused = True
    left = sorted(q.name for q in wd.glob("_c5_*"))
    check("E10 refused file (no mains line): no temporary file left", refused and not left, str(left))
    # interpolation: block-wise matrix vs MNE on the whole recording
    xi = eeg(20, 700, 512, 23, 50)
    xi[REF19.index("C3")] *= 12
    pi = root / "interp.edf"
    write_edf(pi, labels, 512, xi, phys=(-32000.0, 32000.0))
    d_i, m_i = EI.load_any(pi, mains=50.0, interpolate=True, workdir=wd)
    _, names = EI.classify(labels)
    r = mne.io.read_raw_edf(str(pi), preload=True, verbose="ERROR")
    r.pick([names[e] for e in EI.ELECTRODES])
    r.rename_channels({names[e]: e for e in EI.ELECTRODES})
    r.set_montage(mne.channels.make_standard_montage("standard_1020"), on_missing="ignore", match_case=False)
    r.info["bads"] = list(m_i["bad"])          # whatever the rule flagged (C3 x12 must be among them)
    r.interpolate_bads(reset_bads=True, mode="accurate", verbose="ERROR")
    X = r.get_data(picks=list(EI.ELECTRODES))
    pos = {e: i for i, e in enumerate(EI.ELECTRODES)}
    ref = resample_poly(np.stack([X[pos[a]] - X[pos[b]] for a, b in EI.BIPOLAR]), 1, 2, axis=1)
    err = float(np.max(np.abs(np.asarray(d_i) - ref)) / np.max(np.abs(ref)))
    check("E10 interpolation matrix = MNE whole-recording interpolate_bads (relative error < 1e-9)",
          "C3" in m_i["interpolated"] and m_i["interpolated"] == m_i["bad"] and err < 1e-9,
          f"relative max error {err:.1e}; interpolated {m_i['interpolated']}")
    EI.drop_temp(m_i["data_path"], d_i)
    del d_i
    # process memory (resident / working set, memory-mapped file pages included -- the first fix was judged on the
    # traced heap only, which does not see them)
    import threading
    import c5_step2_gates as G

    def grow(fn, *a, **k):
        import gc
        gc.collect()
        base, peak, stop = G.process_mb(), [0.0], [False]

        def mon():
            while not stop[0]:
                peak[0] = max(peak[0], G.process_mb())
                time.sleep(0.02)
        th = threading.Thread(target=mon, daemon=True)
        th.start()
        try:
            out = fn(*a, **k)
        finally:
            stop[0] = True
            th.join()
        return out, max(peak[0], G.process_mb()) - base
    r2, g_pa = grow(pdm.process_file_phase_a, str(pl), None, root / "pl2", mains=50.0)   # first: nothing freed before
    del r2
    x1, g_x1 = grow(X1.load_18, pl, "siena")
    del x1
    check("E10 process-memory growth of the whole Phase A < half that of load_18 alone (file pages included)",
          g_pa < 0.5 * g_x1, f"Phase A +{g_pa:.0f} MB vs load_18 +{g_x1:.0f} MB (25 min, 512 Hz)")


def e7(root, chb_path):
    from fastapi.testclient import TestClient
    real_db, real_up = db.DB_PATH, um.UPLOAD_DIR
    db.DB_PATH = root / "app.db"
    um.UPLOAD_DIR = root / "uploads"
    um.UPLOAD_DIR.mkdir()
    log_stream = io.StringIO()
    h = logging.StreamHandler(log_stream); h.setLevel(logging.DEBUG)
    logging.getLogger().addHandler(h)
    try:
        import main
        with TestClient(main.app) as cl:
            assert cl.post("/api/login", json=dict(username=main.ADMIN_USER, password="wrong")).status_code == 401
            assert cl.post("/api/login", json=dict(username=main.ADMIN_USER, password=main.ADMIN_PASS)).status_code == 200

            def wait_done(timeout=1200):
                t0 = time.time()
                while time.time() - t0 < timeout:
                    s = cl.get("/api/uploads/current").json()
                    if s["done"] or s["error"] or any(f["status"] == "error" for f in s["files"]):
                        return s
                    if s["ready_to_process"] and not s["processing"]:
                        cl.post("/api/uploads/current/process", json=dict(project_id=s["project_id"], memo=""))
                    time.sleep(0.5)
                return cl.get("/api/uploads/current").json()

            # project-id rules
            r = cl.post("/api/uploads/current", json=dict(project_id="Nguyen Van A", memo=""))
            check("E7 project id with spaces refused", r.status_code == 422, r.json().get("detail", "")[:50])
            # session mode, two CHB-like files, mains auto
            assert cl.post("/api/uploads/current", json=dict(project_id="chb01", memo="")).status_code == 200
            p2 = root / "chbx_02.edf"
            write_edf(p2, CHB23, 256, eeg(23, 1200, 256, 21, 60), starttime="12.42.54")
            for p in (chb_path, p2):
                cl.post("/api/uploads/current/files", files={"file": (p.name, p.read_bytes(), "application/octet-stream")})
            s = wait_done()
            check("E7 chb01 accepted (the defense case), session mode, mains auto -> 60 Hz",
                  s["done"] and s["mains_resolved"] == 60.0, str({k: s[k] for k in ("done", "error", "mains_resolved")}))
            cl.post("/api/uploads/current/acknowledge")
            subj = cl.get("/api/subjects/chb01").json()
            check("E7 study stored with mode / mains / engine", subj["mode"] == "session" and subj["mains_hz"] == 60.0
                  and "whole session" in subj["engine"], subj["engine"][:50])
            r = cl.post("/api/uploads/current", json=dict(project_id="chb01", memo=""))
            check("E7 existing project id refused", r.status_code == 422)
            # file mode, one 35-min file
            assert cl.post("/api/uploads/current", json=dict(project_id="fmode", mode="file", mains=60)).status_code == 200
            pf = root / "fm_01.edf"
            xf = eeg(23, 35 * 60, 256, 31, 60); xf[:, 600 * 256:660 * 256] *= 6
            write_edf(pf, CHB23, 256, xf)
            cl.post("/api/uploads/current/files", files={"file": (pf.name, pf.read_bytes(), "application/octet-stream")})
            s = wait_done()
            cl.post("/api/uploads/current/acknowledge")
            subj = cl.get("/api/subjects/fmode").json()
            fid = subj["files"][0]["id"]
            evs = cl.get(f"/api/files/{fid}/events").json()
            r_ref = EF.run_file(np.load(um.UPLOAD_DIR / "fmode" / "fm_01.filtered.npy", mmap_mode="r"),
                                np.load(um.UPLOAD_DIR / "fmode" / "fm_01.flag.npy"),
                                np.load(um.UPLOAD_DIR / "fmode" / "fm_01.fsamp.npy"))
            check("E7 file mode: stored events = engine_file on the same caches",
                  [(e["onset_sec"], e["offset_sec"]) for e in evs] == r_ref["events"] and subj["mode"] == "file",
                  f"{len(evs)} events")
            # mains mismatch inside one study (auto)
            assert cl.post("/api/uploads/current", json=dict(project_id="mix", mains="auto")).status_code == 200
            pa50 = root / "mix_01.edf"; pa60 = root / "mix_02.edf"
            write_edf(pa50, CHB23, 256, eeg(23, 300, 256, 41, 50))
            write_edf(pa60, CHB23, 256, eeg(23, 300, 256, 42, 60))
            cl.post("/api/uploads/current/files", files={"file": (pa50.name, pa50.read_bytes(), "application/octet-stream")})
            time.sleep(0.2)
            for _ in range(200):
                if all(f["status"] != "uploading" for f in cl.get("/api/uploads/current").json()["files"]):
                    break
                time.sleep(0.2)
            cl.post("/api/uploads/current/files", files={"file": (pa60.name, pa60.read_bytes(), "application/octet-stream")})
            for _ in range(400):
                s = cl.get("/api/uploads/current").json()
                if all(f["status"] != "uploading" for f in s["files"]):
                    break
                time.sleep(0.2)
            st = {f["filename"]: f["status"] + (": " + f["error"] if f["error"] else "") for f in s["files"]}
            check("E7 mains mismatch inside a study refused", st.get("mix_02.edf", "").startswith("error")
                  and "differs" in st["mix_02.edf"], st.get("mix_02.edf", "")[:80])
            # wait for any Phase B started by the first file, then discard
            for _ in range(600):
                s = cl.get("/api/uploads/current").json()
                if s["phase_b_done"] or s["error"]:
                    break
                time.sleep(0.5)
            cl.delete("/api/uploads/current")
            # private study: person name in the file name and in the header
            assert cl.post("/api/uploads/current", json=dict(project_id="clin01", mains=50, private=True,
                                                             interpolate=True)).status_code == 200
            labs = [f"EEG {e}-REF" for e in REF19] + [f"POL X{i}" for i in range(84)]
            xh = eeg(103, 40 * 60, 256, 51, 50); xh[REF19.index("C3")] *= 12
            ph = root / f"{PERSON}.edf"
            write_edf(ph, labs, 256, xh, patient=PERSON, startdate="17.03.26", starttime="21.13.45",
                      phys=(-32000.0, 32000.0))
            cl.post("/api/uploads/current/files",
                    files={"file": ("recording.edf", ph.read_bytes(), "application/octet-stream")})
            s = wait_done()
            cl.post("/api/uploads/current/acknowledge")
            subj = cl.get("/api/subjects/clin01").json()
            f0 = subj["files"][0]
            fd = cl.get(f"/api/files/{f0['id']}").json()
            check("E7 private: neutral file name, elapsed time, notice of the interpolated electrode",
                  f0["filename"] == "rec01.edf" and f0["start_date"] == "Recording 1, 00:00:00"
                  and "C3" in fd["notice"] and subj["private"], f"{f0['filename']} / {f0['start_date']}")
            # G8 grep for the person name, the header date / time
            needles = [PERSON, PERSON.split()[-1], "17.03.26", "21.13.45", "2026-03-17", "21:13:45"]
            texts = {
                "database": (root / "app.db").read_bytes().decode("latin-1"),
                "cache names": " ".join(str(p) for p in um.UPLOAD_DIR.rglob("*")),
                "EDF copy": (um.UPLOAD_DIR / "clin01" / "rec01.edf").read_bytes()[:256 * 104].decode("latin-1"),
                "API": json.dumps(subj) + json.dumps(fd) + json.dumps(cl.get("/api/subjects").json()),
                "action log": cl.get("/api/audit.csv").text,
                "backend log": log_stream.getvalue(),
            }
            for fid_ in [f["id"] for f in subj["files"]]:
                cl.post(f"/api/files/{fid_}/viewed")
            texts["export"] = cl.get("/api/subjects/clin01/export").text
            leaks = [(k, nd) for k, t in texts.items() for nd in needles if nd in t]
            check("E8 private: no name, header field or date anywhere", not leaks, str(leaks[:4]))
            # action log
            con = sqlite3.connect(root / "app.db")
            acts = [r[0] for r in con.execute("SELECT action FROM audit_log ORDER BY id")]
            con.close()
            want = {"login_failed", "login", "study_started", "file_uploaded", "process_started", "file_opened",
                    "file_marked_viewed", "export", "audit_exported", "study_discarded"}
            check("E9 action log holds every action of the session", want <= set(acts), str(sorted(want - set(acts))))
            ev_list = cl.get(f"/api/files/{fid}/events").json()
            if ev_list:
                n0 = len(acts)
                cl.patch(f"/api/events/{ev_list[0]['id']}", json=dict(review_status="Accept"))
                con = sqlite3.connect(root / "app.db")
                last = con.execute("SELECT action, detail FROM audit_log ORDER BY id DESC LIMIT 1").fetchone()
                n1 = con.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0]
                con.close()
                check("E9 a review decision writes one row 'Unseen -> Accept'",
                      n1 == n0 + 1 and last == ("review_decision", "Unseen -> Accept"), str(last))
            con = sqlite3.connect(root / "app.db")
            for q in ("UPDATE audit_log SET actor='x'", "DELETE FROM audit_log"):
                try:
                    con.execute(q); con.commit(); check(f"E9 append-only: {q.split()[0]} refused", False)
                except sqlite3.DatabaseError:
                    check(f"E9 append-only: {q.split()[0]} refused", True)
            rows = con.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0]
            con.close()
            csv_rows = list(csv.reader(io.StringIO(cl.get("/api/audit.csv").text)))
            check("E9 CSV = table (+ the export row itself)", len(csv_rows) - 1 == rows + 1, f"{len(csv_rows) - 1} / {rows}")
    finally:
        logging.getLogger().removeHandler(h)
        db.DB_PATH, um.UPLOAD_DIR = real_db, real_up


if __name__ == "__main__":
    sys.exit(main())
