import { useEffect, useLayoutEffect, useRef } from 'react'
import tokens from '../design-tokens.js'
import { formatFileTime } from '../time.js'

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
  onSeek, // (absoluteSec) => void
  onWidthChange, // (widthPx) => void
  selectRangeActive = false,
}) {
  const containerRef = useRef(null)
  const baseCanvasRef = useRef(null)
  const overlayCanvasRef = useRef(null)

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
        // Raw is NEVER fully hidden (SPEC §6.4): full opacity alone, faint background when
        // a filtered trace is also shown on top.
        drawSeries(waveform.raw_uv, chIdx, bandTop, bandMid, pxPerUv, tokens.colorEegRaw, anyFilterOn ? 0.5 : 1)
        if (anyFilterOn) {
          drawSeries(waveform.filtered_uv, chIdx, bandTop, bandMid, pxPerUv, tokens.colorEegFiltered, 1)
        }
      })
    }
  }, [channels, waveform, amplitudeUv, anyFilterOn])

  // Playhead overlay — cheap enough to redraw every animation frame during playback.
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

    if (playheadSec == null || !waveform) return
    const { start_sec: startSec, end_sec: endSec } = waveform
    if (endSec <= startSec) return
    const frac = (playheadSec - startSec) / (endSec - startSec)
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
  }, [playheadSec, waveform])

  function handleCanvasClick(e) {
    if (!waveform || !onSeek) return
    const rect = containerRef.current.getBoundingClientRect()
    const frac = clamp((e.clientX - rect.left) / rect.width, 0, 1)
    const sec = waveform.start_sec + frac * (waveform.end_sec - waveform.start_sec)
    onSeek(sec)
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

      {/* "Event Time" strip (SPEC §6.4) — reserved, empty this step (Step 5/6 add event
          blocks here — see CC_STEP4_PROMPT.md's scope boundary). */}
      <div className="flex border-t border-border" style={{ height: EVENT_ROW_HEIGHT }}>
        <div
          className="shrink-0 flex items-center text-[10px] text-text-muted leading-tight pl-1"
          style={{ width: LABEL_WIDTH }}
        >
          Event
          <br />
          Time
        </div>
        <div className="flex-1 bg-eeg-canvas" />
      </div>
    </div>
  )
}
