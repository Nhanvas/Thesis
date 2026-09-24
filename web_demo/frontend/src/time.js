// SZSCAN_SPEC_v5.md §6.2 — one time-format rule for every file-level time axis (Panel EEG's
// axis now; mini-timeline's in Step 5): HH:MM:SS if the FILE's total duration is < 24h,
// dN:HH:MM:SS if >= 24h (N = elapsed days since the file's own start, 1-based). `startIso`
// is the file's EDF-header start time (meas_date) — a de-identified wall-clock stamp, not a
// real calendar date (see db.py's _recording_label / SPEC §5.1's C17 footnote), so this
// reads it with the UTC getters to reproduce the same wall-clock hour/minute/second Python's
// datetime.fromisoformat(...).strftime(...) already uses on the backend, never converting
// through the browser's local timezone.
export function formatFileTime(startIso, offsetSec, fileDurationSec) {
  const start = new Date(startIso)
  const t = new Date(start.getTime() + offsetSec * 1000)
  const hh = String(t.getUTCHours()).padStart(2, '0')
  const mm = String(t.getUTCMinutes()).padStart(2, '0')
  const ss = String(t.getUTCSeconds()).padStart(2, '0')
  if (fileDurationSec >= 86400) {
    const elapsedDays = Math.floor(offsetSec / 86400) + 1
    return `d${elapsedDays} ${hh}:${mm}:${ss}`
  }
  return `${hh}:${mm}:${ss}`
}

// Same §6.2 rule as formatFileTime, with the trailing ":SS" dropped — for the mini-
// timeline's column-boundary ticks (MiniTimeline.jsx), which always land on exact 10-min
// marks (seconds are always :00, so showing them is redundant clutter, not information).
export function formatFileTimeMinutes(startIso, offsetSec, fileDurationSec) {
  return formatFileTime(startIso, offsetSec, fileDurationSec).replace(/:\d{2}$/, '')
}

// mm:ss (or hh:mm:ss past an hour) for compact scrub-bar / duration labels that are
// durations, not wall-clock times (never uses the dN prefix — that's only for §6.2's
// file-level clock axis).
export function formatDurationShort(totalSec) {
  const s = Math.max(0, Math.round(totalSec))
  const h = Math.floor(s / 3600)
  const m = Math.floor((s % 3600) / 60)
  const sec = s % 60
  if (h > 0) return `${h}:${String(m).padStart(2, '0')}:${String(sec).padStart(2, '0')}`
  return `${m}:${String(sec).padStart(2, '0')}`
}
