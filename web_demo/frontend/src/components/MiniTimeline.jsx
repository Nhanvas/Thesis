import { useMemo } from 'react'
import tokens from '../design-tokens.js'
import { formatFileTimeMinutes } from '../time.js'
import { blockStyle, dimOpacity } from '../eventStyle.js'

// Mini-timeline (SZSCAN_SPEC_v5.md §6.3) — scoped to the currently-open file only, default
// 1-hour view / 6 columns of 10 min each. Two rows (Seizure Detection Score line chart +
// Detections blocks) plus a playhead synced one-way from Panel EEG. View-only: no click
// handler anywhere in this component — SPEC is explicit that only Panel EEG is interactive.
//
// C26, 2026-09-28: files can run past 1 h (chb06 up to ~4 h), so the mini-timeline is paged
// in fixed 3600 s pages that follow the playhead — pageStart = floor(playheadSec / 3600) *
// 3600. Every page is drawn on the same fixed PAGE_WIDTH_SEC-wide grid (so a page's 6 columns
// are always 10 min each, even on a trailing partial page); only the data drawn on top
// (score line, detection blocks) is clipped to [pageStart, pageEnd). For a <= 1 h file
// pageStart is always 0 and this is pixel-identical to the old single-page behaviour.
const PAGE_WIDTH_SEC = 3600 // SPEC §6.3's stated default page size.
const N_COLUMNS = 6
const LABEL_W = 168
const SCORE_ROW_H = 64
const DET_ROW_H = 26
const TICK_ROW_H = 16

function percentile(sortedAsc, p) {
  if (sortedAsc.length === 0) return 0
  const idx = Math.min(sortedAsc.length - 1, Math.max(0, Math.round(p * (sortedAsc.length - 1))))
  return sortedAsc[idx]
}

function Playhead({ frac, height }) {
  if (frac == null || frac < 0 || frac > 1) return null
  return (
    <div
      className="absolute top-0 pointer-events-none"
      style={{ left: `${frac * 100}%`, height, transform: 'translateX(-1px)' }}
    >
      <div style={{ width: 2, height: '100%', background: tokens.colorInteraction }} />
    </div>
  )
}

export default function MiniTimeline({ fileMeta, score, scoreWindowSec, events, playheadSec, selectedEventId }) {
  const pageStart = playheadSec != null ? Math.floor(playheadSec / PAGE_WIDTH_SEC) * PAGE_WIDTH_SEC : 0
  const fileDurationSec = fileMeta?.usable_duration_seconds ?? (pageStart + PAGE_WIDTH_SEC)
  const pageEnd = Math.min(pageStart + PAGE_WIDTH_SEC, fileDurationSec)

  const { p1, p99 } = useMemo(() => {
    if (!score || score.length === 0) return { p1: -1, p99: 1 }
    const sorted = [...score].sort((a, b) => a - b)
    const lo = percentile(sorted, 0.01)
    const hi = percentile(sorted, 0.99)
    return { p1: lo, p99: hi > lo ? hi : lo + 1e-6 }
  }, [score])

  const center = (p1 + p99) / 2
  const halfRange = Math.max((p99 - p1) / 2, 1e-6)

  function clampVal(v, lo, hi) {
    return Math.max(lo, Math.min(hi, v))
  }

  const scorePath = useMemo(() => {
    if (!score || !scoreWindowSec) return ''
    const pts = []
    for (let i = 0; i < score.length; i++) {
      const t = i * scoreWindowSec
      if (t < pageStart) continue
      if (t > pageEnd) break
      const xFrac = (t - pageStart) / PAGE_WIDTH_SEC
      const v = clampVal(score[i], p1, p99)
      const yFrac = 0.5 - ((v - center) / halfRange) * 0.45
      pts.push(`${(xFrac * 1000).toFixed(2)},${(yFrac * 100).toFixed(2)}`)
    }
    return pts.join(' ')
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [score, scoreWindowSec, p1, p99, center, halfRange, pageStart, pageEnd])

  const zeroFrac = 0.5 - ((0 - center) / halfRange) * 0.45

  const playheadFrac = playheadSec != null ? (playheadSec - pageStart) / PAGE_WIDTH_SEC : null

  const ticks = []
  for (let i = 0; i <= N_COLUMNS; i++) {
    const sec = pageStart + (i / N_COLUMNS) * PAGE_WIDTH_SEC
    ticks.push({
      left: (i / N_COLUMNS) * 100,
      label: fileMeta ? formatFileTimeMinutes(fileMeta.start_time, sec, fileMeta.usable_duration_seconds) : '',
    })
  }

  const columnLines = []
  for (let i = 1; i < N_COLUMNS; i++) columnLines.push((i / N_COLUMNS) * 100)

  return (
    <div className="border border-border bg-surface mb-4">
      {/* Row 1 — Seizure Detection Score. SPEC §6.3: y-axis shows no numbers, just a zero
          line + relative height, auto-scaled to THIS file's own P1-P99 (never a fixed scale,
          never shared across files) — never call this "Probability", it's a robust z-score. */}
      <div className="flex" style={{ height: SCORE_ROW_H }}>
        <div className="shrink-0 flex items-center text-xs text-text-secondary pl-2" style={{ width: LABEL_W }}>
          Seizure Detection Score
        </div>
        <div className="relative flex-1 border-l border-border bg-eeg-canvas overflow-hidden">
          {columnLines.map((left) => (
            <div key={left} className="absolute top-0 bottom-0 border-l border-grid" style={{ left: `${left}%` }} />
          ))}
          <div
            className="absolute left-0 right-0 border-t border-grid-strong"
            style={{ top: `${zeroFrac * 100}%` }}
          />
          {scorePath && (
            <svg
              viewBox="0 0 1000 100"
              preserveAspectRatio="none"
              className="absolute inset-0 w-full h-full"
            >
              <polyline
                points={scorePath}
                fill="none"
                stroke={tokens.colorInteraction}
                strokeWidth="1.2"
                vectorEffect="non-scaling-stroke"
              />
            </svg>
          )}
          <Playhead frac={playheadFrac} height={SCORE_ROW_H} />
        </div>
      </div>

      {/* Row 2 — Detections. Label is deliberately "Detections", not "Seizure Detections" —
          SZSCAN_DESIGN_v2.md §8's anti-overclaiming wording rule (the mockups still show the
          old "Seizure Detections" text; that's the mockup lagging the wording table, not the
          table being wrong — see CC_STEP5_PROMPT.md's wording flag). */}
      <div className="flex border-t border-border" style={{ height: DET_ROW_H }}>
        <div className="shrink-0 flex items-center text-xs text-text-secondary pl-2" style={{ width: LABEL_W }}>
          Detections
        </div>
        <div className="relative flex-1 border-l border-border bg-eeg-canvas overflow-hidden">
          {columnLines.map((left) => (
            <div key={left} className="absolute top-0 bottom-0 border-l border-grid" style={{ left: `${left}%` }} />
          ))}
          {events.map((ev) => {
            if (ev.offset_sec <= pageStart || ev.onset_sec >= pageEnd) return null
            const left = ((Math.max(pageStart, ev.onset_sec) - pageStart) / PAGE_WIDTH_SEC) * 100
            const right = ((Math.min(pageEnd, ev.offset_sec) - pageStart) / PAGE_WIDTH_SEC) * 100
            const widthPct = Math.max(right - left, 0.3)
            const style = blockStyle(ev)
            const opacity = dimOpacity(ev, selectedEventId, style.opacity)
            return (
              <div
                key={ev.id}
                className="absolute top-0.5 bottom-0.5 rounded-sm"
                style={{
                  left: `${left}%`,
                  width: `${widthPct}%`,
                  background: style.hatch
                    ? `repeating-linear-gradient(45deg, ${style.color}, ${style.color} 3px, rgba(255,255,255,0.5) 3px, rgba(255,255,255,0.5) 6px)`
                    : style.color,
                  opacity,
                  outline: ev.id === selectedEventId ? `2px solid ${tokens.colorInteraction}` : 'none',
                  outlineOffset: 1,
                }}
                title={`${ev.name} — ${ev.source}${ev.source === 'AI' ? ` / ${ev.review_status}` : ''}`}
              />
            )
          })}
          <Playhead frac={playheadFrac} height={DET_ROW_H} />
        </div>
      </div>

      {/* Column-boundary ticks. */}
      <div className="flex" style={{ height: TICK_ROW_H }}>
        <div className="shrink-0" style={{ width: LABEL_W }} />
        <div className="relative flex-1">
          {ticks.map(({ left, label }, i) => (
            <span
              key={i}
              className="absolute top-0 text-[10px] font-mono text-text-muted whitespace-nowrap"
              style={{ left: `${left}%`, transform: i === 0 ? 'none' : i === ticks.length - 1 ? 'translateX(-100%)' : 'translateX(-50%)' }}
            >
              {label}
            </span>
          ))}
        </div>
      </div>
    </div>
  )
}
