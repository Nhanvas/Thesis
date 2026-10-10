"""Tests of the rebuilt demo pipeline (final thesis system, tag p3-frozen).

Synthetic, tiny EDFs only (written with pyedflib into pytest's tmp_path) -- never a real
recording. What is checked:
  1. Phase A filtering and the label-free z-score statistics equal x1_external's own functions
     (the thesis's reference implementation for an unseen, label-free recording).
  2. The per-window graph and node features equal x1_external.file_features.
  3. The demo's events equal the events produced INSIDE the frozen e23_test_look7.evaluate on the
     same distances (captured at its scoring call), for the balanced operating point.
  4. Runtime label-freeness: the whole headless path runs with every label-reading thesis entry
     point replaced by a function that raises.
  5. The channel panel reads the per-channel |robust-z| p95 of attribution_v8 over the
     non-signal-loss windows of the event.
  6. The checkpoint constants match docs/PROVENANCE_V2.md and the file on disk.
A fake, deterministic latent replaces the GAE forward pass in 3-5 (torch is not needed); test 7
runs the real GAE v2 when torch is installed.
"""
import json
import re
import sys
from pathlib import Path

import numpy as np
import pyedflib
import pytest

BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_DIR.parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import pipeline_demo as pd  # noqa: E402

P = pd.preprocessing
FS, WIN = P.FS, P.WIN_SAMPLES


# ------------------------------------------------------------------------------- fixtures
def _write_edf(path: Path, n_windows: int, seed: int, burst=None, flat=()):
    """18-channel EDF at 256 Hz, ~20 uV noise; `burst` = (first_window, n_windows) of a 5 Hz,
    150 uV rhythm on 6 channels; `flat` = windows forced to 0 uV (signal loss)."""
    rng = np.random.RandomState(seed)
    n = n_windows * WIN + 300                       # a partial window at the end, as real files
    x = rng.normal(0.0, 20.0, size=(18, n))
    if burst is not None:
        a, k = burst
        t = np.arange(k * WIN) / FS
        x[:6, a * WIN:(a + k) * WIN] += 150.0 * np.sin(2 * np.pi * 5.0 * t)
    for w in flat:
        x[:, w * WIN:(w + 1) * WIN] = 0.0
    wr = pyedflib.EdfWriter(str(path), 18, file_type=pyedflib.FILETYPE_EDFPLUS)
    try:
        wr.setSignalHeaders([dict(label=ch, dimension="uV", sample_frequency=FS, physical_max=2000,
                                  physical_min=-2000, digital_max=32767, digital_min=-32768,
                                  transducer="", prefilter="") for ch in P.COMMON_CHANNELS])
        wr.writeSamples([x[i] for i in range(18)])
    finally:
        wr.close()


@pytest.fixture(scope="module")
def subject(tmp_path_factory):
    d = tmp_path_factory.mktemp("chbXX")
    specs = [("chbXX_01.edf", 70, 1, (40, 6), ()), ("chbXX_02.edf", 55, 2, None, (10, 11, 12)),
             ("chbXX_03.edf", 80, 3, (20, 8), ())]
    for name, n, seed, burst, flat in specs:
        _write_edf(d / name, n, seed, burst, flat)
    return d, [d / s[0] for s in specs]


def fake_latent(adj, bp5, f7):
    """Deterministic stand-in for the GAE: 16 features per node from the real inputs."""
    a = adj.astype(np.float64)
    deg = np.nan_to_num(a.sum(axis=2))[..., None]
    mx = np.nan_to_num(a.max(axis=2))[..., None]
    bp = np.nan_to_num(np.log(np.abs(bp5.astype(np.float64)) + 1e-12))
    f = np.nan_to_num(f7.astype(np.float64))
    z = np.concatenate([bp, f, deg, mx, (bp[..., :1] * f[..., :1]), np.tanh(f[..., 5:6])], axis=2)
    return z.astype(np.float32)


# ------------------------------------------------------------------------------- 1, 2
def test_phase_a_and_labelfree_stats_equal_x1(subject):
    d, paths = subject
    X1 = pd.X1
    res = {p.name: pd.process_file_phase_a(str(p)) for p in paths}
    for p in paths:
        filt, n = X1.filter_windows(X1.load_18(p, "chb"), 60.0)
        assert n == res[p.name].n_windows
        assert np.array_equal(filt, res[p.name].filtered)
    mu, sd = pd.labelfree_zscore_stats({k: r.moments for k, r in res.items()})
    mu_x, sd_x = X1.labelfree_stats([(p, []) for p in sorted(paths)], "chb", 60.0)
    assert np.allclose(mu, mu_x, rtol=1e-9, atol=1e-18)
    assert np.allclose(sd, sd_x, rtol=1e-9, atol=0)


def test_features_equal_x1(subject):
    d, paths = subject
    X1 = pd.X1
    res = {p.name: pd.process_file_phase_a(str(p)) for p in paths}
    mu, sd = pd.labelfree_zscore_stats({k: r.moments for k, r in res.items()})
    for i, p in enumerate(sorted(paths)):
        ref = X1.file_features((p, [], "chb", 60.0, mu, sd, i))
        r = res[p.name]
        assert np.array_equal(ref["is_signal_loss"], r.flag)
        adj, bp5, f7 = pd.file_features(r.filtered, r.flag, mu, sd)
        keep = ~r.flag
        assert np.array_equal(adj, ref["adj"][keep])
        assert np.array_equal(bp5, ref["bp5"][keep])
        assert np.array_equal(f7, ref["f7"][keep])


# ------------------------------------------------------------------------------- 3
def test_events_equal_frozen_e23_evaluate(subject, monkeypatch, tmp_path):
    d, paths = subject
    monkeypatch.setattr(pd, "run_gae", fake_latent)
    out = pd.process_subject_headless([str(p) for p in paths], cache_dir=tmp_path)
    names = sorted(out["scores"])
    assert sum(len(v) for v in out["events"].values()) > 0, "synthetic bursts should raise events"

    # the thesis side: x1_external.make_ctx on the same distances, then e23_test_look7.evaluate
    X1, PS = pd.X1, pd.PS
    import e23_test_look7 as E23
    flags = np.concatenate([out["flags"][f] for f in names])
    fidx = np.concatenate([np.full(len(out["flags"][f]), i) for i, f in enumerate(names)])
    D = np.concatenate([out["dists"][f][~out["flags"][f]] for f in names])
    z = dict(is_ictal=np.zeros(len(flags), bool), is_signal_loss=flags, file_idx=fidx)
    ctx = X1.make_ctx(z, np.flatnonzero(~flags), {t: D for t in X1.TAGS})
    captured = []
    monkeypatch.setattr(PS, "score", lambda c, ev: (captured.append(ev), (0, 0, 0, 0.0))[1])
    fl, cp = pd.FREEZE["points"]["balanced"]
    E23.evaluate(ctx, pd.MODEL_TAG, pd.FREEZE, fl, cp, pd.FREEZE["localizer"])
    localized = captured[1]
    want = {names[int(f)]: [tuple(map(float, e)) for e in v] for f, v in localized.items()}
    got = {f: [tuple(e) for e in v] for f, v in out["events"].items()}
    assert got == {f: want.get(f, []) for f in names}
    # and the timeline score is the frozen final scalar
    x = np.concatenate([out["scores"][f] for f in names])
    import e22_test_oneshot as E22
    assert np.array_equal(x, E22.final_scalar(ctx, pd.MODEL_TAG))


# ------------------------------------------------------------------------------- 4
def test_runtime_label_free(subject, monkeypatch, tmp_path):
    d, paths = subject
    monkeypatch.setattr(pd, "run_gae", fake_latent)

    def boom(*a, **k):
        raise AssertionError("label-reading function called by the demo")

    import szcore_eval as SE
    import e22_test_oneshot as E22
    for mod, names in ((P, ["parse_summary", "build_labels", "build_buffer_mask", "compute_subject_stats"]),
                       (SE, [n for n in dir(SE) if n.startswith("build_timeline")]),
                       (pd.X1, ["_loadSeizures", "chb_subject", "siena_subject", "subject_files", "build_subject"]),
                       (pd.PS, ["subject_context", "score", "short_refs", "caught"]),
                       (E22, ["test_context"]), (pd.P3L, ["refs_of"])):
        for n in names:
            monkeypatch.setattr(mod, n, boom)
    out = pd.process_subject_headless([str(p) for p in paths], cache_dir=tmp_path)
    assert set(out["events"]) == {p.name for p in paths}


# ------------------------------------------------------------------------------- 5
def test_channel_panel_is_attribution_v8_quantity(subject, monkeypatch, tmp_path):
    d, paths = subject
    monkeypatch.setattr(pd, "run_gae", fake_latent)
    out = pd.process_subject_headless([str(p) for p in paths], cache_dir=tmp_path)
    import attribution
    import db
    monkeypatch.setattr(db, "get_attribution_status", lambda eid: {})
    sdir = tmp_path / "chbXX"
    sdir.mkdir()
    names = sorted(out["dists"])
    for f in names:
        np.save(sdir / f"{Path(f).stem}.pernode.npy", out["dists"][f].astype(np.float32))
    np.save(sdir / pd.PERNODE_BASELINE_FILENAME, out["baseline"])
    f = "chbXX_02.edf"                                       # has signal-loss windows 10-12
    ev = dict(id=1, name="Event 1", onset_sec=36.0, offset_sec=60.0)
    got = attribution.get_event_attribution(ev, dict(subject_id="chbXX", filename=f), tmp_path)
    assert got["available"]
    D_all = np.concatenate([out["dists"][g][~out["flags"][g]] for g in names])
    Zc = np.column_stack([(D_all[:, j] - np.median(D_all[:, j])) / (np.median(np.abs(D_all[:, j] - np.median(D_all[:, j]))) + 1e-9)
                          for j in range(18)])
    rows_f = np.flatnonzero(~out["flags"][f])
    off = sum(int((~out["flags"][g]).sum()) for g in names[:names.index(f)])
    ww = [off + int(np.flatnonzero(rows_f == w)[0]) for w in range(9, 15) if w in rows_f]   # windows 9..14 minus loss
    want = np.percentile(np.abs(Zc[ww]), 95, axis=0)
    by_ch = {r["channel"]: r["score"] for r in got["rows"]}
    for j, ch in enumerate(P.COMMON_CHANNELS):
        assert abs(by_ch[ch] - want[j]) < 1e-4 * max(1.0, abs(want[j]))

    ev2 = dict(id=2, name="Event 2", onset_sec=40.0, offset_sec=52.0)    # windows 10-12: all loss
    got2 = attribution.get_event_attribution(ev2, dict(subject_id="chbXX", filename=f), tmp_path)
    assert got2["available"] is False


# ------------------------------------------------------------------------------- 6
def test_checkpoint_identity_matches_provenance():
    txt = (REPO_ROOT / "docs" / "PROVENANCE_V2.md").read_text(encoding="utf-8")
    m = re.search(r"\|\s*gae_v2_clean_seed42\.pt\s*\|\s*\d+\s*\|\s*`([0-9a-f]{64})`", txt)
    assert m and m.group(1) == pd.CHECKPOINT_SHA256
    pd.verify_checkpoint()
    meta = json.loads(pd.CHECKPOINT_META_PATH.read_text())
    assert meta["in_dim"] == 30 and meta["seed"] == 42 and meta["variant"] == "clean"


# ------------------------------------------------------------------------------- 7
def test_real_gae_runs_when_torch_is_installed(subject, tmp_path):
    torch = pytest.importorskip("torch")
    if getattr(torch, "STUB", False):
        pytest.skip("torch is a stub in this environment")
    d, paths = subject
    out = pd.process_subject_headless([str(p) for p in paths], cache_dir=tmp_path)
    D = np.concatenate([out["dists"][f][~out["flags"][f]] for f in sorted(out["dists"])])
    assert D.shape[1] == 18 and np.isfinite(D).all()
