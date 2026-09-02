"""
================================================================================
 edf_index.py  —  global-window-index -> (edf filename, offset_s) lookup
================================================================================
WHY THIS FILE
-------------
The demo needs to answer: "for subject chb15, show me the raw EEG for the
time range [start_s, end_s]" where start_s/end_s are seconds measured from
the start of that subject's FIRST .edf file in chronological order (the same
convention build_timeline_masked in szcore_eval.py already uses for its
reconstructed pseudo-timeline).

CHB-MIT subjects are recorded across MULTIPLE .edf files (e.g. chb15_01.edf,
chb15_02.edf, ... each up to 1h), sorted() == chronological (verified in the
original preprocessing pipeline, see PLAN_AND_STATUS.md / experiment logs).
A global "seconds since recording start" position can fall in any one of
these files. This module builds that mapping ONCE at server startup (not per
request) using the EXACT same summary-file parser already used everywhere
else in the codebase (evaluation_protocol.parse_summary_edf_list), so the
demo's notion of "time" is identical to the notion of "time" used to produce
every locked result -- no new parsing logic, no risk of a second, subtly
different implementation drifting from the original.

WHAT THIS PROVIDES
-------------------
  EdfIndex(subj, summary_dir).locate(global_offset_s) -> (fname, local_offset_s)
  EdfIndex(subj, summary_dir).total_duration_s
  EdfIndex(subj, summary_dir).files   # ordered list of (fname, start_s, end_s)

NOTE ON SCOPE: this module only concerns itself with TIME mapping (which file,
which offset). It does NOT read EEG signal data -- that is edf_reader.py's job
(uses pyedflib to actually decode samples). Keeping these separate means the
time-mapping logic (shared with every other locked result) never touches
signal-decoding logic (demo-only, added for Phase C).
================================================================================
"""
import bisect
from pathlib import Path
from dataclasses import dataclass
from typing import List, Tuple

import evaluation_protocol as EP


@dataclass
class EdfFileSpan:
    fname: str
    start_s: float   # inclusive, seconds since this subject's recording start
    end_s: float     # exclusive
    duration_s: float


class EdfIndex:
    """Chronological (file, offset) index for one subject, built once from
    that subject's -summary.txt (same parser as every locked result)."""

    def __init__(self, subj: str, summary_dir: str):
        self.subj = subj
        edfs = EP.parse_summary_edf_list(str(Path(summary_dir) / f"{subj}-summary.txt"))
        if not edfs:
            raise ValueError(f"no EDF entries found for {subj} in {summary_dir} "
                            f"-- check the summary file exists and parses correctly")
        self.files: List[EdfFileSpan] = []
        cursor = 0.0
        for edf in edfs:
            dur = float(edf["duration_s"])
            self.files.append(EdfFileSpan(
                fname=edf["fname"], start_s=cursor, end_s=cursor + dur, duration_s=dur))
            cursor += dur
        self.total_duration_s = cursor
        # sorted starts, for bisect -- files is already chronological (the
        # parser sorts by fname, which is chronological for CHB-MIT naming)
        self._starts = [f.start_s for f in self.files]

    def locate(self, global_offset_s: float) -> Tuple[str, float]:
        """Returns (edf_filename, offset_within_that_file_s) for a global
        offset measured from this subject's recording start. Raises
        ValueError if out of range -- callers should catch this and return
        an HTTP 416/400, not silently clamp (a silent clamp could show the
        wrong segment of EEG to a clinician)."""
        if global_offset_s < 0 or global_offset_s > self.total_duration_s:
            raise ValueError(
                f"{self.subj}: offset {global_offset_s}s outside recording "
                f"range [0, {self.total_duration_s}s]")
        idx = bisect.bisect_right(self._starts, global_offset_s) - 1
        idx = max(0, min(idx, len(self.files) - 1))
        span = self.files[idx]
        local = global_offset_s - span.start_s
        # guard against float-boundary edge case landing just past this
        # file's end due to the bisect choosing the wrong neighbor
        if local > span.duration_s and idx + 1 < len(self.files):
            idx += 1
            span = self.files[idx]
            local = global_offset_s - span.start_s
        return span.fname, local

    def locate_range(self, start_s: float, end_s: float) -> List[Tuple[str, float, float]]:
        """Returns a list of (fname, local_start_s, local_end_s) segments
        covering [start_s, end_s], SPLIT at file boundaries if the requested
        range spans more than one .edf file. Almost always a single-element
        list in practice (segments of interest are seconds to a couple
        minutes long, files are up to 1h), but must be handled correctly for
        the rare case a flagged segment sits right at a file boundary."""
        if end_s <= start_s:
            raise ValueError(f"end_s ({end_s}) must be > start_s ({start_s})")
        # validate against the recording bounds -- consistent with locate()'s
        # "raise, don't silently clamp" policy. Without this, end_s > total_duration_s
        # sends the loop below past the last file and it spins forever emitting
        # zero-length segments. Callers should clamp the display window to
        # [0, total_duration_s] BEFORE calling, or catch this and return HTTP 400/416.
        if start_s < 0 or end_s > self.total_duration_s:
            raise ValueError(
                f"{self.subj}: requested range [{start_s}, {end_s}]s outside "
                f"recording [0, {self.total_duration_s}s]")
        out = []
        cursor = start_s
        while cursor < end_s:
            fname, local_start = self.locate(cursor)
            span = next(f for f in self.files if f.fname == fname)
            local_end = min(end_s, span.end_s) - span.start_s
            out.append((fname, local_start, local_end))
            if span.end_s <= cursor:      # defensive: never loop without advancing
                break
            cursor = span.end_s
        return out
