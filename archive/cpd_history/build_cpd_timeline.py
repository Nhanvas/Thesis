# src/build_cpd_timeline.py
"""
Reconstruct chronological score timeline from separate inter/ictal arrays.

Algorithm:
  1. Parse summary file → get all EDF files in chronological order
     with their seizure annotations
  2. For each EDF file, determine how many windows it contributes
     to interictal_adjs and ictal_adjs
  3. Build interleaved timeline: [inter, inter, ictal, ictal, inter, ...]
     with correct chronological ordering
  4. Map back to actual stored array indices

Output:
  timeline_scores[subj]  — [N_total] float32, chronological order
  timeline_labels[subj]  — [N_total] int {0: inter, 1: ictal}
  timeline_window_s[subj] — [N_total] float, start time in seconds
"""
import re
import numpy as np
from pathlib import Path

FS      = 256
WIN_S   = 4
WIN_SAMP = FS * WIN_S   # 1024
BUFFER_H = 4            # 4-hour post-seizure buffer (same as preprocessing)


def parse_time_s(t_str):
    """'HH:MM:SS' → seconds since midnight. Handles cross-midnight."""
    h, m, s = [int(x) for x in t_str.strip().split(':')]
    return h * 3600 + m * 60 + s


def parse_summary(summary_path):
    """
    Returns list of dicts per EDF file:
      {'fname': str, 'start_s': int, 'end_s': int,
       'seizures': [(onset_s, offset_s), ...]}
    All times in seconds since midnight of the recording day.
    """
    text = Path(summary_path).read_text()
    files = []
    pattern = re.compile(
        r'File Name:\s*(\S+\.edf)\s+'
        r'File Start Time:\s*(\S+)\s+'
        r'File End Time:\s*(\S+)\s+'
        r'Number of Seizures in File:\s*(\d+)(.*?)(?=File Name:|$)',
        re.DOTALL | re.IGNORECASE
    )
    for m in pattern.finditer(text):
        fname, t_start, t_end, n_sz, rest = m.groups()
        t_s = parse_time_s(t_start)
        t_e = parse_time_s(t_end)
        if t_e <= t_s:
            t_e += 86400   # crossed midnight

        seizures = []
        sz_starts = re.findall(r'Seizure.*?Start Time.*?:\s*(\d+)\s*second', rest, re.I)
        sz_ends   = re.findall(r'Seizure.*?End Time.*?:\s*(\d+)\s*second',   rest, re.I)
        for s, e in zip(sz_starts, sz_ends):
            seizures.append((int(s), int(e)))

        files.append({
            'fname': fname,
            'start_s': t_s,
            'end_s': t_e,
            'seizures': seizures
        })
    return sorted(files, key=lambda x: x['start_s'])


def build_timeline(subj, summary_path, scores_inter, scores_ictal):
    """
    Reconstruct chronological score timeline.
    
    Parameters
    ----------
    subj         : subject ID (e.g. 'chb03')
    summary_path : path to summary .txt file
    scores_inter : [N_inter] float32 — chronological inter scores
    scores_ictal  : [N_ictal] float32 — chronological ictal scores

    Returns
    -------
    timeline  : [N_total] float32 — scores in chronological order
    labels    : [N_total] int8   — 0=inter, 1=ictal
    times_s   : [N_total] float  — window start time in seconds
    """
    edf_files = parse_summary(summary_path)

    # Collect ALL seizure annotations across recording
    # to build buffer masks
    all_seizure_times = []
    for ef in edf_files:
        file_start = ef['start_s']
        for onset_rel, offset_rel in ef['seizures']:
            abs_onset  = file_start + onset_rel
            abs_offset = file_start + offset_rel
            all_seizure_times.append((abs_onset, abs_offset))

    # Build buffer set: seconds within 4h after any seizure end
    buffer_s = set()
    for onset, offset in all_seizure_times:
        for t in range(offset, offset + BUFFER_H * 3600):
            buffer_s.add(t)

    # Walk through EDF files chronologically and assign windows
    timeline   = []
    labels     = []
    times_s    = []
    ptr_inter  = 0
    ptr_ictal   = 0

    for ef in edf_files:
        file_start = ef['start_s']
        n_samp_file = int((ef['end_s'] - ef['start_s']) * FS)
        n_win_file  = n_samp_file // WIN_SAMP

        # Build per-second ictal mask for this file
        ictal_s = set()
        for onset_rel, offset_rel in ef['seizures']:
            for t in range(onset_rel, offset_rel):
                ictal_s.add(t)

        for i in range(n_win_file):
            win_start_s = file_start + i * WIN_S
            win_end_s   = win_start_s + WIN_S

            # Determine label: ictal if any second in window is ictal
            is_ictal   = any(t in ictal_s
                             for t in range(i * WIN_S, (i + 1) * WIN_S))
            is_buffered = any(s in buffer_s
                              for s in range(int(win_start_s), int(win_end_s)))

            if is_ictal:
                if ptr_ictal < len(scores_ictal):
                    timeline.append(scores_ictal[ptr_ictal])
                    labels.append(1)
                    times_s.append(float(win_start_s))
                    ptr_ictal += 1
            elif not is_buffered:
                if ptr_inter < len(scores_inter):
                    timeline.append(scores_inter[ptr_inter])
                    labels.append(0)
                    times_s.append(float(win_start_s))
                    ptr_inter += 1
            # buffered windows: skip (excluded during preprocessing)

    print(f"  {subj}: {len(timeline)} windows mapped "
          f"({ptr_inter} inter, {ptr_ictal} ictal), "
          f"unmatched: inter={len(scores_inter)-ptr_inter}, "
          f"ictal={len(scores_ictal)-ptr_ictal}")

    return (np.array(timeline, dtype=np.float32),
            np.array(labels,   dtype=np.int8),
            np.array(times_s,  dtype=np.float64))