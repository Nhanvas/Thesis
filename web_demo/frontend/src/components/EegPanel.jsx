import { useEffect, useLayoutEffect, useRef, useState } from 'react'
import tokens from '../design-tokens.js'
import { formatFileTime } from '../time.js'
import { blockStyle, dimOpacity, blockLabelColor } from '../eventStyle.js'

// Panel EEG (SZSCAN_SPEC_v5.md §6.4) — the 18-channel waveform canvas, its channel-label
// gutter, the time axis underneath, and the (still-empty, Step 5+ scope) "Event Time" strip.
//
// Two stacked <canvas> elements: a base layer for the waveform (only redrawn when the
// fetched window / amplitude / filter state changes) and a transparent overlay for the
// playhead (redrawn every animation frame during playback without re-drawing 18 channels'
// worth of min/max envelope each time).
const ROW_HEIGHT = 38
const LABEL_WIDTH = 64
const TIME_AXIS_HEIGHT = 18
const EVENT_ROW_HEIGHT = 28
const N_GRID_DIVISIONS = 8

function clamp(v, lo, hi) {
  return Math.max(lo, Math.min(hi, v))
}

export default function EegPanel({
  channels,
  waveform, // {start_sec, end_sec, n_buckets, raw_uv, filtered_uv} | null
  amplitudeUv,
  anyFilterOn,
  playheadSec, // absolute seconds within the file, or null
  fileMeta, // {start_time, usable_duration_seconds} — for the §6.2 time axis
  onGridClick, // (absoluteSec) => void — a plain seek, or the next Select Range click,
  // depending on selectRangeActive; AnalysisScreen decides which.
  onWidthChange, // (widthPx) => void
  selectRangeActive = false,
  markingOnsetSec = null, // Step 6 (SPEC §6.6): the onset already locked in by the first
  // Select Range click this marking pass, or null before that click / after it completes.
  events = [], // Step 5 (SPEC §6.4's "Event Time" row) — all events in the file, not just
  // the visible window; filtered to the visible window below.
  selectedEventId = null,
}) {
  const containerRef = useRef(null)
  const baseCanvasRef = useRef(null)
  const overlayCanvasRef = useRef(null)
  // Step 6: live cursor position (absolute sec) while dragging out the offset half of a
  // Select Range mark — drives the stretching preview rectangle in the Event Time row
  // (SPEC §6.6 step 3). Local-only: nothing outside this component needs to know about it.
  const [hoverSec, setHoverSec] = useState(null)

  useEffect(() => {
    if (markingOnsetSec == null) setHoverSec(null)
  }, [markingOnsetSec])

  // Measure the canvas area's real pixel width so the backend can decimate to ~1
  // bucket/pixel (DEMO_BUILD_HANDOFF.md §5) — never a guessed constant.
  useLayoutEffect(() => {
    const el = containerRef.current
    if (!el) return undefined
    const report = () => onWidthChange(Math.max(1, Math.round(el.clientWidth)))
    report()
    const ro = new ResizeObserver(report)
    ro.observe(el)
    return () => ro.disconnect()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // Base waveform layer.
  useEffect(() => {
    const canvas = baseCanvasRef.current
    if (!canvas) return
    const dpr = window.devicePixelRatio || 1
    const cssWidth = canvas.clientWidth
    const cssHeight = canvas.clientHeight
    if (cssWidth === 0 || cssHeight === 0) return
    canvas.width = cssWidth * dpr
    canvas.height = cssHeight * dpr
    const ctx = canvas.getContext('2d')
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0)

    ctx.fillStyle = tokens.colorEegCanvas
    ctx.fillRect(0, 0, cssWidth, cssHeight)

    const rowHeight = cssHeight / channels.length

    // Vertical (time) gridlines first, so channel separators paint on top at the edges.
    ctx.strokeStyle = tokens.colorGrid
    ctx.lineWidth = 1
    for (let i = 1; i < N_GRID_DIVISIONS; i++) {
      const x = Math.round((i / N_GRID_DIVISIONS) * cssWidth) + 0.5
      ctx.beginPath()
      ctx.moveTo(x, 0)
      ctx.lineTo(x, cssHeight)
      ctx.stroke()
    }

    // Horizontal channel-band separators.
    ctx.strokeStyle = tokens.colorGridStrong
    for (let i = 1; i < channels.length; i++) {
      const y = Math.round(i * rowHeight) + 0.5
      ctx.beginPath()
      ctx.moveTo(0, y)
      ctx.lineTo(cssWidth, y)
      ctx.stroke()
    }

    if (waveform && waveform.n_buckets > 0) {
      const nBuckets = waveform.n_buckets
      const pxPerBucket = cssWidth / nBuckets

      const drawSeries = (seriesUv, chIdx, bandTop, bandMid, pxPerUv, color, alpha) => {
        ctx.strokeStyle = color
        ctx.globalAlpha = alpha
        ctx.lineWidth = 1
        ctx.beginPath()
        const series = seriesUv[chIdx]
        for (let b = 0; b < nBuckets; b++) {
          const mn = series[b][0]
          const mx = series[b][1]
          const x = b * pxPerBucket + pxPerBucket / 2
          // Deliberately NOT clamped to this channel's own band: real scalp EEG amplitude
          // (tens to hundreds of µV) routinely exceeds a sensitive µV/division setting like
          // the default 7 µV, and clinical EEG viewers let the trace overflow into
          // neighboring channel rows rather than hard-clip it flat — clipping here produced
          // a misleading solid-filled block instead of a readable (if busy) waveform.
          const yLo = bandMid - mn * pxPerUv
          const yHi = bandMid - mx * pxPerUv
          ctx.moveTo(x, yLo)
          ctx.lineTo(x, yHi)
        }
        ctx.stroke()
        ctx.globalAlpha = 1
      }

      channels.forEach((_, chIdx) => {
        const bandTop = chIdx * rowHeight
        const bandMid = bandTop + rowHeight / 2
        const pxPerUv = (rowHeight / 2 - 3) / Math.max(amplitudeUv, 1e-6)
        // Clip to this channel's own row (SPEC §6.4): real scalp EEG routinely exceeds a
        // sensitive µV/division setting, and drawing the overflow unclamped let one
        // saturated channel's line bleed into every other channel's row, painting the whole
        // canvas near-solid. Clipping (not clamping the coordinates — that flattened a
        // saturated bucket into a misleading solid block) keeps the overflow contained to its
        // own band: a channel may legitimately look clipped/busy at an aggressive amplitude
        // setting, matching how clinical EEG viewers behave, but it no longer corrupts the
        // rest of the display.
        ctx.save()
        ctx.beginPath()
        ctx.rect(0, bandTop, cssWidth, rowHeight)
        ctx.clip()
        // Raw is NEVER fully hidden (SPEC §6.4): full opacity alone, faint background when
        // a filtered trace is also shown on top.
        drawSeries(waveform.raw_uv, chIdx, bandTop, bandMid, pxPerUv, tokens.colorEegRaw, anyFilterOn ? 0.5 : 1)
        if (anyFilterOn) {
          drawSeries(waveform.filtered_uv, chIdx, bandTop, bandMid, pxPerUv, tokens.colorEegFiltered, 1)
        }
        ctx.restore()
      })
    }
  }, [channels, waveform, amplitudeUv, anyFilterOn])

  // Playhead + (Step 6) Select Range onset marker overlay — cheap enough to redraw every
  // animation frame during playback. The onset marker reuses the exact playhead visual
  // (violet line + triangle) rather than inventing a second style: DESIGN §2's interaction
  // axis (violet = "currently interacting") already covers an in-progress mark, and
  // `UI/B3a`'s onset line is visually identical to a playhead — see the report.
  useEffect(() => {
    const canvas = overlayCanvasRef.current
    if (!canvas) return
    const dpr = window.devicePixelRatio || 1
    const cssWidth = canvas.clientWidth
    const cssHeight = canvas.clientHeight
    if (cssWidth === 0 || cssHeight === 0) return
    canvas.width = cssWidth * dpr
    canvas.height = cssHeight * dpr
    const ctx = canvas.getContext('2d')
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
    ctx.clearRect(0, 0, cssWidth, cssHeight)
    if (!waveform) return
    const { start_sec: startSec, end_sec: endSec } = waveform
    if (endSec <= startSec) return

    function drawMarker(sec) {
      if (sec == null) return
      const frac = (sec - startSec) / (endSec - startSec)
      if (frac < 0 || frac > 1) return
      const x = frac * cssWidth
      ctx.strokeStyle = tokens.colorInteraction
      ctx.lineWidth = 2
      ctx.beginPath()
      ctx.moveTo(x, 0)
      ctx.lineTo(x, cssHeight)
      ctx.stroke()
      ctx.fillStyle = tokens.colorInteraction
      ctx.beginPath()
      ctx.moveTo(x - 5, 0)
      ctx.lineTo(x + 5, 0)
      ctx.lineTo(x, 8)
      ctx.closePath()
      ctx.fill()
    }

    drawMarker(playheadSec)
    drawMarker(markingOnsetSec)
  }, [playheadSec, markingOnsetSec, waveform])

  function secAtClientX(clientX) {
    const rect = containerRef.current.getBoundingClientRect()
    const frac = clamp((clientX - rect.left) / rect.width, 0, 1)
    return waveform.start_sec + frac * (waveform.end_sec - waveform.start_sec)
  }

  function handleCanvasClick(e) {
    if (!waveform || !onGridClick) return
    onGridClick(secAtClientX(e.clientX))
  }

  // Step 6: live drag preview (SPEC §6.6 step 3) — only tracked while a mark is actually in
  // progress (onset locked, offset not yet clicked), so ordinary hovering never re-renders.
  function handleCanvasMouseMove(e) {
    if (!waveform || !selectRangeActive || markingOnsetSec == null) return
    setHoverSec(secAtClientX(e.clientX))
  }

  function handleCanvasMouseLeave() {
    setHoverSec(null)
  }

  const gridTimeLabels = []
  if (waveform && fileMeta) {
    const span = waveform.end_sec - waveform.start_sec
    for (let i = 0; i <= N_GRID_DIVISIONS; i++) {
      const sec = waveform.start_sec + (i / N_GRID_DIVISIONS) * span
      gridTimeLabels.push({
        left: (i / N_GRID_DIVISIONS) * 100,
        label: formatFileTime(fileMeta.start_time, sec, fileMeta.usable_duration_seconds),
      })
    }
  }

  return (
    <div>
      <div className="flex">
        <div className="shrink-0" style={{ width: LABEL_WIDTH }}>
          {channels.map((ch) => (
            <div
              key={ch}
              style={{ height: ROW_HEIGHT }}
              className="flex items-center text-xs font-mono text-text-secondary pl-1"
            >
              {ch}
            </div>
          ))}
        </div>
        <div
          ref={containerRef}
          className={`relative flex-1 ${selectRangeActive ? 'cursor-crosshair' : 'cursor-pointer'}`}
          style={{ height: ROW_HEIGHT * channels.length }}
          onClick={handleCanvasClick}
          onMouseMove={handleCanvasMouseMove}
          onMouseLeave={handleCanvasMouseLeave}
        >
          <canvas ref={baseCanvasRef} className="absolute inset-0 w-full h-full" />
          <canvas ref={overlayCanvasRef} className="absolute inset-0 w-full h-full pointer-events-none" />
        </div>
      </div>

      <div className="flex" style={{ height: TIME_AXIS_HEIGHT }}>
        <div className="shrink-0" style={{ width: LABEL_WIDTH }} />
        <div className="relative flex-1">
          {gridTimeLabels.map(({ left, label }, i) => (
            <span
              key={i}
              className="absolute top-0 text-[10px] font-mono text-text-muted whitespace-nowrap"
              style={{ left: `${left}%`, transform: i === 0 ? 'none' : 'translateX(-50%)' }}
            >
              {label}
            </span>
          ))}
        </div>
      </div>

      {/* "Event Time" strip (SPEC §6.4) — blocks for events overlapping the visible window,
          same color rules as the mini-timeline's Detections row (eventStyle.js) so the two
          views never disagree on an event's color. */}
      <div className="flex border-t border-border" style={{ height: EVENT_ROW_HEIGHT }}>
        <div
          className="shrink-0 flex items-center text-[10px] text-text-muted leading-tight pl-1"
          style={{ width: LABEL_WIDTH }}
        >
          Event
          <br />
          Time
        </div>
        <div className="relative flex-1 bg-eeg-canvas overflow-hidden">
          {waveform && events
            .filter((ev) => ev.offset_sec >= waveform.start_sec && ev.onset_sec <= waveform.end_sec)
            .map((ev) => {
              const span = waveform.end_sec - waveform.start_sec
              if (span <= 0) return null
              const left = ((Math.max(ev.onset_sec, waveform.start_sec) - waveform.start_sec) / span) * 100
              const right = ((Math.min(ev.offset_sec, waveform.end_sec) - waveform.start_sec) / span) * 100
              const style = blockStyle(ev)
              const opacity = dimOpacity(ev, selectedEventId, style.opacity)
              return (
                <div
                  key={ev.id}
                  className="absolute top-0.5 bottom-0.5 rounded-sm flex items-center justify-center overflow-hidden"
                  style={{
                    left: `${left}%`,
                    width: `${Math.max(right - left, 0.3)}%`,
                    background: style.hatch
                      ? `repeating-linear-gradient(45deg, ${style.color}, ${style.color} 3px, rgba(255,255,255,0.5) 3px, rgba(255,255,255,0.5) 6px)`
                      : style.color,
                    opacity,
                    outline: ev.id === selectedEventId ? `2px solid ${tokens.colorInteraction}` : 'none',
                  }}
                  title={ev.name}
                >
                  <span
                    className="text-[9px] font-mono truncate px-1"
                    style={{ color: blockLabelColor(ev) }}
                  >
                    {ev.name}
                  </span>
                </div>
              )
            })}
          {/* Step 6 (SPEC §6.6 step 3): live stretching preview while the offset half of a
              Select Range mark hasn't been clicked yet. Human blue at reduced opacity + a
              dashed outline marks it as provisional — visually distinct from any committed
              block (all of which are solid per eventStyle.js). Min/max makes the preview
              direction-agnostic too (item 13), matching the final sorted result. */}
          {waveform && markingOnsetSec != null && hoverSec != null && (() => {
            const span = waveform.end_sec - waveform.start_sec
            if (span <= 0) return null
            const lo = Math.min(markingOnsetSec, hoverSec)
            const hi = Math.max(markingOnsetSec, hoverSec)
            if (hi < waveform.start_sec || lo > waveform.end_sec) return null
            const left = ((Math.max(lo, waveform.start_sec) - waveform.start_sec) / span) * 100
            const right = ((Math.min(hi, waveform.end_sec) - waveform.start_sec) / span) * 100
            return (
              <div
                className="absolute top-0.5 bottom-0.5 rounded-sm border border-dashed pointer-events-none"
                style={{
                  left: `${left}%`,
                  width: `${Math.max(right - left, 0.3)}%`,
                  background: tokens.colorHuman,
                  opacity: 0.35,
                  borderColor: tokens.colorHuman,
                }}
              />
            )
          })()}
        </div>
      </div>
    </div>
  )
}
