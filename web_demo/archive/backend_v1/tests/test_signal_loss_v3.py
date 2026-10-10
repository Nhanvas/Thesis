"""App v3 (CC_PROMPT_APP_V3_CODE.md): signal-loss rule, merge constant, headless entry point.

Covers:
  - a synthetic recording with a flat segment: flagged windows get score 0 and are excluded
    from every subject-wide fit (verified directly by spying on the fit calls, not inferred
    from downstream numerics);
  - a recording with no flat window gives bit-identical scores before and after this change,
    compared against the frozen pre-change code at git tag szscan-frozen-v2;
  - `detect_events` receives all three fixed constants (FIXED_MAG_PCT/FIXED_PEN_MULT/
    FIXED_MERGE_S);
  - `process_subject_headless` gives the same scores as the live Phase A + Phase B path on a
    synthetic two-file subject.

All synthetic EDFs are tiny (tens of windows), written with pyedflib directly (no mne EDF
writer available in this environment) — never a real recording, never processed by the live
backend/HTTP app (CC_PROMPT_APP_V3_CODE.md: "do not upload, process or score any recording").
"""
import importlib.util
import subprocess
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
import preprocessing  # noqa: E402  (src/dataprep, put on sys.path by importing pipeline_demo)

FS = preprocessing.FS
WIN_SAMPLES = preprocessing.WIN_SAMPLES
CHANNELS = preprocessing.COMMON_CHANNELS
N_CH = len(CHANNELS)

FROZEN_TAG = "szscan-frozen-v2"
FROZEN_PATH = "web_demo/backend/pipeline_demo.py"


def _write_synthetic_edf(path: Path, n_windows: int, flat_windows=(), seed: int = 0,
                          amp_uv: float = 20.0) -> None:
    """A tiny, fully synthetic 18-channel EDF at 256 Hz: Gaussian ~20 uV noise on every
    channel/sample, except `flat_windows` (0-indexed 4 s windows) forced to a constant 0 uV
    on every channel. A constant segment's std is exactly 0 regardless of the EDF's digital
    quantization (every sample in it decodes to the same physical value), so it reliably
    trips the < 1e-10 V signal-loss threshold without needing a real flat-lined recording."""
    rng = np.random.RandomState(seed)
    n = n_windows * WIN_SAMPLES
    data_uv = rng.normal(0.0, amp_uv, size=(N_CH, n))
    for w in flat_windows:
        data_uv[:, w * WIN_SAMPLES:(w + 1) * WIN_SAMPLES] = 0.0

    writer = pyedflib.EdfWriter(str(path), N_CH, file_type=pyedflib.FILETYPE_EDFPLUS)
    try:
        headers = [
            dict(label=ch, dimension="uV", sample_frequency=FS,
                 physical_max=2000, physical_min=-2000,
                 digital_max=32767, digital_min=-32768,
                 transducer="", prefilter="")
            for ch in CHANNELS
        ]
        writer.setSignalHeaders(headers)
        writer.writeSamples([data_uv[i] for i in range(N_CH)])
    finally:
        writer.close()


def _load_frozen_pipeline_demo():
    """Loads web_demo/backend/pipeline_demo.py as it was committed at git tag
    szscan-frozen-v2 (CC_PROMPT_APP_V3_CODE.md clarification (c)) — before App v3's
    signal-loss rule — as a separate module object, so its functions can be called directly
    and compared against the current module's. `git show` is read-only; nothing is checked
    out or written. `__file__` is set to this backend directory so the frozen code's own
    `REPO_ROOT = Path(__file__).resolve().parents[2]` resolves to the real repo root, same
    as the live module."""
    src = subprocess.run(
        ["git", "show", f"{FROZEN_TAG}:{FROZEN_PATH}"],
        cwd=str(REPO_ROOT), capture_output=True, text=True, check=True,
    ).stdout
    spec = importlib.util.spec_from_loader("pipeline_demo_frozen_v2", loader=None)
    mod = importlib.util.module_from_spec(spec)
    mod.__dict__["__file__"] = str(BACKEND_DIR / "pipeline_demo.py")
    sys.modules["pipeline_demo_frozen_v2"] = mod
    exec(compile(src, f"<frozen {FROZEN_TAG}:{FROZEN_PATH}>", "exec"), mod.__dict__)
    return mod


@pytest.fixture(scope="module")
def frozen_pd():
    mod = _load_frozen_pipeline_demo()
    yield mod
    sys.modules.pop("pipeline_demo_frozen_v2", None)


# ---------------------------------------------------------------------------------------
# 1. Flat segment -> flagged windows score 0 and are excluded from every subject-wide fit.
# ---------------------------------------------------------------------------------------

def test_flagged_windows_zero_and_excluded_from_every_fit(tmp_path, monkeypatch):
    n_windows = 24
    flat = {10, 11, 12}
    edf_path = tmp_path / "chbTEST_01.edf"
    _write_synthetic_edf(edf_path, n_windows, flat_windows=flat)

    phase_a = pd.process_file_phase_a(str(edf_path), cache_dir=tmp_path)
    assert phase_a.flag.shape == (n_windows,)
    assert set(np.flatnonzero(phase_a.flag).tolist()) == flat
    # Clarification (a): persisted as {stem}.flag.npy.
    flag_path = tmp_path / f"{edf_path.stem}.flag.npy"
    assert flag_path.exists()
    assert np.array_equal(np.load(flag_path), phase_a.flag)

    n_flagged = len(flat)
    expected_fit_len = n_windows - n_flagged

    median_mad_lengths = []
    orig_median_mad = pd._median_mad

    def spy_median_mad(x):
        median_mad_lengths.append(len(x))
        return orig_median_mad(x)

    ledoitwolf_lengths = []
    orig_fit = pd.LedoitWolf.fit

    def spy_fit(self, X, y=None):
        ledoitwolf_lengths.append(len(X))
        return orig_fit(self, X, y)

    monkeypatch.setattr(pd, "_median_mad", spy_median_mad)
    monkeypatch.setattr(pd.LedoitWolf, "fit", spy_fit)

    scores = pd.process_subject_phase_b(
        {phase_a.filename: phase_a.filtered},
        flag_by_filename={phase_a.filename: phase_a.flag},
    )

    # LedoitWolf.fit (zlatent) and all three _median_mad calls (zrecon/zlatent/zgamma) see
    # exactly n_windows - n_flagged rows -- the flagged windows never reach any fit.
    assert ledoitwolf_lengths == [expected_fit_len]
    assert median_mad_lengths == [expected_fit_len] * 3

    score = scores[phase_a.filename]
    assert score.shape == (n_windows,)
    assert np.all(score[sorted(flat)] == 0.0)
    # The non-flagged scores must still be finite -- confirms the flagged windows' raw GAE/
    # connectivity output (potentially numerically undefined, per Amendment A2's root cause)
    # never leaked into a fit that would have propagated into these.
    kept = np.ones(n_windows, dtype=bool)
    kept[sorted(flat)] = False
    assert np.all(np.isfinite(score[kept]))


# ---------------------------------------------------------------------------------------
# 2. No flat window -> bit-identical to the frozen pre-change code (max abs diff 0).
# ---------------------------------------------------------------------------------------

def test_bit_identical_when_no_flagged_window(tmp_path, frozen_pd):
    n_windows = 8
    edf_path = tmp_path / "chbTEST_02.edf"
    _write_synthetic_edf(edf_path, n_windows, flat_windows=())

    phase_a_new = pd.process_file_phase_a(str(edf_path))
    assert not phase_a_new.flag.any()  # no flat window -> nothing flagged

    scores_new = pd.process_subject_phase_b(
        {phase_a_new.filename: phase_a_new.filtered},
        flag_by_filename={phase_a_new.filename: phase_a_new.flag},
    )

    phase_a_frozen = frozen_pd.process_file_phase_a(str(edf_path))
    scores_frozen = frozen_pd.process_subject_phase_b(
        {phase_a_frozen.filename: phase_a_frozen.filtered}
    )

    new = scores_new[phase_a_new.filename]
    old = scores_frozen[phase_a_frozen.filename]
    assert new.shape == old.shape
    max_abs_diff = float(np.max(np.abs(new - old)))
    assert max_abs_diff == 0.0


# ---------------------------------------------------------------------------------------
# 3. detect_events receives the three fixed constants.
# ---------------------------------------------------------------------------------------

def test_detect_events_receives_the_three_constants(monkeypatch):
    seen = {}
    orig_detect_events = pd.cpd_pipeline_v14.detect_events

    def spy_detect_events(score_timeline, pen_mult, **kwargs):
        seen["pen_mult"] = pen_mult
        seen["min_mag_pct"] = kwargs.get("min_mag_pct")
        seen["merge_s"] = kwargs.get("merge_s")
        return orig_detect_events(score_timeline, pen_mult, **kwargs)

    monkeypatch.setattr(pd.cpd_pipeline_v14, "detect_events", spy_detect_events)

    rng = np.random.RandomState(0)
    scores = {"f1.edf": rng.normal(0, 1, size=60).astype(np.float64)}
    pd.process_subject_events(scores)

    assert seen["pen_mult"] == pd.FIXED_PEN_MULT
    assert seen["min_mag_pct"] == pd.FIXED_MAG_PCT
    assert seen["merge_s"] == pd.FIXED_MERGE_S


# ---------------------------------------------------------------------------------------
# 4. process_subject_headless matches the live Phase A + Phase B path, two-file subject.
# ---------------------------------------------------------------------------------------

def test_process_subject_headless_matches_live_phase_a_plus_b(tmp_path):
    n1, n2 = 10, 14
    flat1, flat2 = {3, 4}, {7}
    edf1 = tmp_path / "chbTEST_03a.edf"
    edf2 = tmp_path / "chbTEST_03b.edf"
    _write_synthetic_edf(edf1, n1, flat_windows=flat1, seed=1)
    _write_synthetic_edf(edf2, n2, flat_windows=flat2, seed=2)

    headless_cache = tmp_path / "headless_cache"
    scores_headless, flags_headless = pd.process_subject_headless(
        [str(edf1), str(edf2)], cache_dir=headless_cache, max_workers=2
    )

    # Clarification (b): per-file flag mask returned AND persisted.
    assert set(flags_headless) == {edf1.name, edf2.name}
    assert set(np.flatnonzero(flags_headless[edf1.name]).tolist()) == flat1
    assert set(np.flatnonzero(flags_headless[edf2.name]).tolist()) == flat2
    for edf in (edf1, edf2):
        assert (headless_cache / f"{edf.stem}.flag.npy").exists()

    phase_a_1 = pd.process_file_phase_a(str(edf1))
    phase_a_2 = pd.process_file_phase_a(str(edf2))
    scores_live = pd.process_subject_phase_b(
        {phase_a_1.filename: phase_a_1.filtered, phase_a_2.filename: phase_a_2.filtered},
        flag_by_filename={phase_a_1.filename: phase_a_1.flag, phase_a_2.filename: phase_a_2.flag},
    )

    for fn in (edf1.name, edf2.name):
        assert np.array_equal(scores_headless[fn], scores_live[fn])


# ---------------------------------------------------------------------------------------
# 5. Existing label guards still pass unchanged (test_guards.py is untouched; this just
#    re-asserts the module imports/collects cleanly alongside this new file).
# ---------------------------------------------------------------------------------------

def test_guards_module_still_importable():
    import test_guards  # noqa: F401
