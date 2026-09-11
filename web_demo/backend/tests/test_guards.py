"""Guard tests enforcing CLAUDE.md's three hard guards + the write guard.

See CLAUDE.md ("Three hard guards") and SZSCAN_SPEC_v5.md §1.2 for what each guard
protects against and why: the demo is presented as label-free and must never see
ground-truth seizure annotations, and demo code must never write into locked thesis
artifacts. This file scans the web_demo/ source tree for violations of all four.

If a guard fires here, fix the offending code -- never weaken this test.
"""
import ast
import re
from pathlib import Path

WEB_DEMO_ROOT = Path(__file__).resolve().parents[2]

# Directories never treated as demo source. `tests/` is excluded on purpose: this
# file itself must contain the guarded literal strings (e.g. "build_timeline_masked",
# "Seizure Start Time") in order to scan for them, so including it would make every
# guard flag itself. Fixtures for the positive-case tests below live under pytest's
# `tmp_path`, entirely outside this tree, so excluding `tests/` never hides a real
# violation in demo source.
EXCLUDED_DIR_NAMES = {
    "node_modules", "venv", ".venv", ".git", "cache", "__pycache__", "dist", "tests",
}


def _iter_files(root: Path, suffixes):
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix not in suffixes:
            continue
        if any(part in EXCLUDED_DIR_NAMES for part in path.parts):
            continue
        yield path


def _iter_py_files(root: Path):
    return _iter_files(root, {".py"})


def _iter_source_files(root: Path):
    return _iter_files(root, {".py", ".js", ".jsx", ".ts", ".tsx"})


def _read_text(path: Path):
    try:
        return path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return None


# ---------------------------------------------------------------------------
# Guard 1 -- never import/call szcore_eval.build_timeline_masked (CLAUDE.md #1)
# ---------------------------------------------------------------------------

def find_build_timeline_masked_violations(root: Path):
    violations = []
    for path in _iter_py_files(root):
        text = _read_text(path)
        if text and "build_timeline_masked" in text:
            violations.append(path)
    return violations


# ---------------------------------------------------------------------------
# Guard 2 -- never read Seizure Start/End Time or Number of Seizures at runtime
# (CLAUDE.md #2, SZSCAN_SPEC_v5.md §1.2)
# ---------------------------------------------------------------------------

# "Seizure Start Time" / "Seizure End Time" have no legitimate demo use at all --
# any appearance as a string literal is a violation, full stop.
ALWAYS_FORBIDDEN_FIELDS = ["Seizure Start Time", "Seizure End Time"]

# "Number of Seizures" (as "Number of Seizures in File:") is allowed to appear ONLY
# as a text anchor for locating record boundaries in chb*-summary.md -- exactly what
# edf_order.py does, immediately discarding the captured value (bound to `_` in a
# `.groups()` unpack). If the value is ever bound to a real name instead, it becomes
# usable elsewhere, i.e. genuinely "read" -- that is a violation.
DISCARDABLE_FIELD = "Number of Seizures"


def _capturing_groups_before(pattern_text: str, index: int) -> int:
    """Count regex capturing groups (not `(?...)`) before `index` in pattern_text."""
    return len(re.findall(r"\((?!\?)", pattern_text[:index]))


def _groups_unpack_discards_index(tree: ast.AST, group_index: int) -> bool:
    """True if some `a, b, ..., _ = <expr>.groups()` in `tree` binds `group_index` to `_`."""
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        value = node.value
        if not (isinstance(value, ast.Call) and isinstance(value.func, ast.Attribute)
                and value.func.attr == "groups"):
            continue
        target = node.targets[0]
        if not isinstance(target, (ast.Tuple, ast.List)):
            continue
        elts = target.elts
        if group_index >= len(elts):
            continue
        elt = elts[group_index]
        if isinstance(elt, ast.Name) and elt.id == "_":
            return True
    return False


def find_seizure_field_violations(root: Path):
    violations = []
    for path in _iter_py_files(root):
        text = _read_text(path)
        if not text:
            continue

        for field in ALWAYS_FORBIDDEN_FIELDS:
            if field in text:
                violations.append((path, field))

        if DISCARDABLE_FIELD not in text:
            continue
        try:
            tree = ast.parse(text, filename=str(path))
        except SyntaxError:
            violations.append((path, DISCARDABLE_FIELD))
            continue

        for node in ast.walk(tree):
            if not (isinstance(node, ast.Constant) and isinstance(node.value, str)
                    and DISCARDABLE_FIELD in node.value):
                continue
            idx = node.value.find(DISCARDABLE_FIELD)
            group_index = _capturing_groups_before(node.value, idx)
            if not _groups_unpack_discards_index(tree, group_index):
                violations.append((path, DISCARDABLE_FIELD))
    return violations


# ---------------------------------------------------------------------------
# Guard 3 -- never load {subj}_interictal.npy / {subj}_ictal.npy (CLAUDE.md #3)
# ---------------------------------------------------------------------------

NPY_PATTERNS = ["_interictal.npy", "_ictal.npy"]
NPY_CALL_MARKERS = ["open(", "np.load(", "Path("]


def find_labeled_npy_violations(root: Path):
    violations = []
    for path in _iter_py_files(root):
        text = _read_text(path)
        if not text:
            continue
        for lineno, line in enumerate(text.splitlines(), start=1):
            if any(p in line for p in NPY_PATTERNS) and any(m in line for m in NPY_CALL_MARKERS):
                violations.append((path, lineno))
    return violations


# ---------------------------------------------------------------------------
# Guard 4 -- never write to results/, data/models_retrain/, data/processed/, docs/
# (the write guard, CLAUDE.md)
# ---------------------------------------------------------------------------

FORBIDDEN_WRITE_PATHS = ["results/", "data/models_retrain/", "data/processed/", "docs/"]
WRITE_CALL_MARKERS = ["np.save(", "np.savez(", "torch.save(", ".write_text("]
_OPEN_WRITE_MODE_RE = re.compile(r"""open\([^)]*['"]([wxa][bt+]{0,2})['"]""")


def find_disallowed_write_violations(root: Path):
    violations = []
    for path in _iter_source_files(root):
        text = _read_text(path)
        if not text:
            continue
        for lineno, line in enumerate(text.splitlines(), start=1):
            if not any(p in line for p in FORBIDDEN_WRITE_PATHS):
                continue
            if any(m in line for m in WRITE_CALL_MARKERS) or _OPEN_WRITE_MODE_RE.search(line):
                violations.append((path, lineno))
    return violations


# ---------------------------------------------------------------------------
# Tests -- one positive (injected fixture caught) + one negative (clean tree passes)
# per guard, combined per guard so a failure names exactly which guard broke.
# ---------------------------------------------------------------------------

def test_guard_no_build_timeline_masked(tmp_path):
    bad = tmp_path / "bad_pipeline.py"
    bad.write_text(
        "from szcore_eval import build_timeline_masked\n"
        "def run(edf, annotations):\n"
        "    return build_timeline_masked(edf, annotations)\n"
    )
    assert find_build_timeline_masked_violations(tmp_path) == [bad]

    assert find_build_timeline_masked_violations(WEB_DEMO_ROOT) == []


def test_guard_no_seizure_fields_at_runtime(tmp_path):
    leak_dir = tmp_path / "case_leak"
    leak_dir.mkdir()
    bad = leak_dir / "bad_reader.py"
    bad.write_text(
        "import re\n"
        "def leak(text):\n"
        "    m = re.search(r'Seizure Start Time:\\s*(\\S+)', text)\n"
        "    seizure_start = m.group(1)\n"
        "    return seizure_start\n"
    )
    violations = find_seizure_field_violations(leak_dir)
    assert any(v[0] == bad and v[1] == "Seizure Start Time" for v in violations)

    # Discarding the captured "Number of Seizures" value (edf_order.py's pattern)
    # must NOT be flagged -- only using it would be.
    ok_dir = tmp_path / "case_ok"
    ok_dir.mkdir()
    ok = ok_dir / "ok_boundary_anchor.py"
    ok.write_text(
        "import re\n"
        "pat = re.compile(r'File Name:\\s*(\\S+)\\s+Number of Seizures in File:\\s*(\\d+)')\n"
        "def parse(text):\n"
        "    for m in pat.finditer(text):\n"
        "        fname, _ = m.groups()\n"
        "        yield fname\n"
    )
    assert find_seizure_field_violations(ok_dir) == []

    used_dir = tmp_path / "case_used"
    used_dir.mkdir()
    used = used_dir / "bad_uses_count.py"
    used.write_text(
        "import re\n"
        "pat = re.compile(r'File Name:\\s*(\\S+)\\s+Number of Seizures in File:\\s*(\\d+)')\n"
        "def parse(text):\n"
        "    for m in pat.finditer(text):\n"
        "        fname, n_seizures = m.groups()\n"
        "        yield fname, n_seizures\n"
    )
    assert any(v[0] == used for v in find_seizure_field_violations(used_dir))

    assert find_seizure_field_violations(WEB_DEMO_ROOT) == []


def test_guard_no_labeled_npy(tmp_path):
    bad = tmp_path / "bad_loader.py"
    bad.write_text(
        "import numpy as np\n"
        "def load(subj):\n"
        "    return np.load(f'data/processed/{subj}_interictal.npy')\n"
    )
    assert find_labeled_npy_violations(tmp_path) == [(bad, 3)]

    assert find_labeled_npy_violations(WEB_DEMO_ROOT) == []


def test_guard_no_writes_outside_web_demo(tmp_path):
    bad = tmp_path / "bad_writer.py"
    bad.write_text(
        "def leak():\n"
        "    with open('results/leak.txt', 'w') as f:\n"
        "        f.write('leaked')\n"
    )
    assert find_disallowed_write_violations(tmp_path) == [(bad, 2)]

    assert find_disallowed_write_violations(WEB_DEMO_ROOT) == []
