"""Tests for batch_ingest.subject_edfs's file-name pattern.

CHB-MIT names chb17's recording in three lettered segments (chb17a/b/c_NN.edf) instead of the
plain {subject}_NN.edf every other test subject uses. The pattern must match both shapes for the
right subject and never match another subject's files.
"""
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import batch_ingest as bi  # noqa: E402


def _touch(dir_: Path, *names: str) -> None:
    for n in names:
        (dir_ / n).write_bytes(b"")


def test_chb17_lettered_names_match(tmp_path):
    _touch(tmp_path, "chb17a_03.edf", "chb17b_57.edf", "chb17c_02.edf")
    got = [p.name for p in bi.subject_edfs("chb17", tmp_path)]
    assert got == ["chb17a_03.edf", "chb17b_57.edf", "chb17c_02.edf"]


def test_plain_subject_name_still_matches(tmp_path):
    _touch(tmp_path, "chb03_01.edf", "chb03_02.edf")
    got = [p.name for p in bi.subject_edfs("chb03", tmp_path)]
    assert got == ["chb03_01.edf", "chb03_02.edf"]


def test_other_subjects_never_match_chb17(tmp_path):
    _touch(tmp_path, "chb1_01.edf", "chb170_01.edf", "chb03_01.edf", "chb17a_03.edf")
    got = [p.name for p in bi.subject_edfs("chb17", tmp_path)]
    assert got == ["chb17a_03.edf"]


def test_non_edf_and_summary_files_ignored(tmp_path):
    _touch(
        tmp_path,
        "chb17a_03.edf",
        "chb17a_03.edf.seizures",
        "chb17-summary.md",
        "chb17a_03.EDF",
    )
    got = [p.name for p in bi.subject_edfs("chb17", tmp_path)]
    assert got == ["chb17a_03.edf"]
