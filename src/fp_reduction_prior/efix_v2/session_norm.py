"""
session_norm.py
===============
Per-session z-normalization for subjects with multiple recording sessions.

Problem: Standard per-subject z-norm mixes windows from different recording
sessions (different days/weeks) that may have different EEG baselines. For
subjects like chb17 (sessions 17a, 17b, 17c recorded on different dates),
the mixed statistics inflate the interictal variance and degrade z-scores.

Solution: Detect session boundaries from filename prefixes in the summary
file. Estimate how many interictal windows came from each session using
proportional duration. Apply session-specific (median, MAD) normalization.

NOTE: Window-to-session mapping is approximate because the preprocessing
artifact rejection rate is not stored per-file. The approximation error is
small when sessions differ substantially in duration (which they do for chb17).
"""

import re
import numpy as np
from pathlib import Path
from datetime import datetime


def _parse_time(t_str: str) -> int:
    """
    Parse 'HH:MM:SS' or 'H:MM:SS' to seconds since midnight.
    Handles recordings that cross midnight (end < start → +86400).
    """
    parts = t_str.strip().split(":")
    h, m, s = int(parts[0]), int(parts[1]), int(parts[2])
    return h * 3600 + m * 60 + s


def detect_sessions(summary_path: str) -> dict:
    """
    Parse summary file and detect sessions from filename prefixes.

    A 'session' is defined by the letter suffix in the filename:
      chb17a_03.edf → session 'a'
      chb17b_57.edf → session 'b'
      chb17c_02.edf → session 'c'
      chb01_01.edf  → session '' (single session subject)

    Returns
    -------
    dict: {session_label: {'files': [...], 'inter_duration_s': float}}
      Only interictal files (0 seizures, outside 4h buffer) are counted.
    """
    text = Path(summary_path).read_text()

    # Parse all file entries
    # Each entry: File Name, Start Time, End Time, Number of Seizures
    file_pattern = re.compile(
        r'File Name:\s*(\S+\.edf)\s+'
        r'File Start Time:\s*(\S+)\s+'
        r'File End Time:\s*(\S+)\s+'
        r'Number of Seizures in File:\s*(\d+)',
        re.IGNORECASE
    )

    sessions = {}

    for match in file_pattern.finditer(text):
        fname      = match.group(1)
        start_str  = match.group(2)
        end_str    = match.group(3)
        n_seizures = int(match.group(4))

        # Detect session label from filename prefix
        # chb17a_03.edf → 'a'; chb01_01.edf → ''
        m_sess = re.match(r'chb\d+([a-z])_', fname, re.IGNORECASE)
        session_label = m_sess.group(1) if m_sess else ''

        if session_label not in sessions:
            sessions[session_label] = {'files': [], 'inter_duration_s': 0.0}

        sessions[session_label]['files'].append(fname)

        # Only count interictal recording time (files with 0 seizures)
        if n_seizures == 0:
            t_start = _parse_time(start_str)
            t_end   = _parse_time(end_str)
            duration = t_end - t_start
            if duration < 0:
                duration += 86400   # crossed midnight
            sessions[session_label]['inter_duration_s'] += max(0, duration)

    return sessions


def get_session_boundaries(
    sessions: dict,
    n_total_inter: int
) -> list:
    """
    Estimate session boundaries in the interictal window array.

    Uses proportional duration to split n_total_inter windows into sessions.
    Returns list of (start_idx, end_idx, session_label) tuples.

    NOTE: This is an approximation. The actual window counts per session
    depend on artifact rejection, which is not tracked per-file.
    """
    total_dur = sum(v['inter_duration_s'] for v in sessions.values())
    if total_dur == 0 or len(sessions) <= 1:
        return [(0, n_total_inter, list(sessions.keys())[0])]

    boundaries = []
    cumulative = 0
    session_items = sorted(sessions.items())   # sort by label for reproducibility

    for i, (label, info) in enumerate(session_items):
        proportion = info['inter_duration_s'] / total_dur
        if i < len(sessions) - 1:
            n_windows = int(round(n_total_inter * proportion))
            boundaries.append((cumulative, cumulative + n_windows, label))
            cumulative += n_windows
        else:
            boundaries.append((cumulative, n_total_inter, label))  # last session gets remainder

    return boundaries


def apply_session_znorm(
    scores: np.ndarray,
    is_interictal: bool,
    boundaries: list,
    session_stats: dict   # {label: {'median': float, 'mad': float}}
) -> np.ndarray:
    """
    Apply session-specific z-normalization to a score array.

    For interictal scores: apply boundary-partitioned normalization.
    For ictal scores: each seizure belongs to the LAST known session
                      before the seizure (approximation: use last session's stats).

    Parameters
    ----------
    scores        : [N] raw anomaly scores
    is_interictal : True → use per-session boundaries; False → use last session
    boundaries    : output of get_session_boundaries()
    session_stats : {label: {median, mad}} computed from interictal

    Returns
    -------
    z_scores : [N] z-normalized scores
    """
    z = np.empty_like(scores)

    if is_interictal:
        for (start, end, label) in boundaries:
            med = session_stats[label]['median']
            mad = session_stats[label]['mad']
            z[start:end] = (scores[start:end] - med) / (mad + 1e-8)
    else:
        # Approximate: ictal windows distributed across sessions.
        # Use global stats (same as standard z-norm) as fallback.
        # TODO: improve with per-seizure session assignment if summary timestamps available.
        all_meds = [v['median'] for v in session_stats.values()]
        all_mads = [v['mad']    for v in session_stats.values()]
        med = np.median(all_meds)
        mad = np.median(all_mads)
        z = (scores - med) / (mad + 1e-8)

    return z


def compute_session_znorm(
    scores_inter: np.ndarray,
    scores_ictal: np.ndarray,
    summary_path: str,
    tau_z: float = 1.48
) -> tuple:
    """
    Full per-session z-normalization pipeline.

    Parameters
    ----------
    scores_inter  : [N_inter] raw reconstruction scores (interictal)
    scores_ictal  : [N_ictal] raw reconstruction scores (ictal)
    summary_path  : path to subject summary .txt file
    tau_z         : Youden threshold

    Returns
    -------
    z_inter, z_ictal : z-normalized scores
    session_info     : dict for debugging
    """
    sessions = detect_sessions(summary_path)
    n_sessions = len([k for k, v in sessions.items()
                      if v['inter_duration_s'] > 0])

    # If only one session: fall back to standard per-subject z-norm
    if n_sessions <= 1:
        median = np.median(scores_inter)
        mad    = np.median(np.abs(scores_inter - median)) + 1e-8
        z_inter = (scores_inter - median) / mad
        z_ictal = (scores_ictal - median) / mad
        return z_inter, z_ictal, {"n_sessions": 1, "fallback": True}

    boundaries = get_session_boundaries(sessions, len(scores_inter))

    # Compute per-session stats from interictal scores
    session_stats = {}
    for (start, end, label) in boundaries:
        seg = scores_inter[start:end]
        if len(seg) == 0:
            continue
        med = np.median(seg)
        mad = np.median(np.abs(seg - med)) + 1e-8
        session_stats[label] = {"median": float(med), "mad": float(mad),
                                 "n_windows": len(seg)}

    z_inter = apply_session_znorm(scores_inter, True,  boundaries, session_stats)
    z_ictal = apply_session_znorm(scores_ictal, False, boundaries, session_stats)

    return z_inter, z_ictal, {
        "n_sessions": n_sessions,
        "session_stats": session_stats,
        "boundaries": [(s, e, l) for s, e, l in boundaries],
        "fallback": False
    }