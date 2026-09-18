import { useEffect, useRef, useState } from 'react'
import Header from '../components/Header.jsx'
import Footer from '../components/Footer.jsx'
import EegPanel from '../components/EegPanel.jsx'
import { ChevronDownIcon, PlayIcon, PauseIcon } from '../components/icons.jsx'
import {
  getFile,
  getSubjectDetail,
  getWaveform,
  markFileViewed,
  markFileViewing,
} from '../api.js'

// Analysis screen — Panel EEG + toolbar + scrub (Step 4, CC_STEP4_PROMPT.md). Mini-timeline,
// Panel Event, and Channel Attribution are Step 5+ scope and deliberately not rendered here
// (see the report's scope-boundary section) — this screen is Panel EEG's full-width column
// only, not the two-column B1a layout that panel eventually shares the page with.

// SPEC §6.4's popover value lists (`UI/B1b`, `UI/B1d`) — fixed UI copy, not derived from a
// pipeline source file (these are display *increments* for a frontend-only zoom/scale
// control, not pipeline thresholds/parameters — CLAUDE.md's "never hardcode a threshold"
// targets pipeline operating parameters, which these aren't).
const WINDOW_OPTIONS = [
  { seconds: 24 * 3600, label: '24 hr' },
  { seconds: 16 * 3600, label: '16 hr' },
  { seconds: 12 * 3600, label: '12 hr' },
  { seconds: 8 * 3600, label: '08 hr' },
  { seconds: 6 * 3600, label: '06 hr' },
  { seconds: 4 * 3600, label: '04 hr' },
  { seconds: 2 * 3600, label: '02 hr' },
  { seconds: 1 * 3600, label: '01 hr' },
  { seconds: 30 * 60, label: '30 min' },
  { seconds: 15 * 60, label: '15 min' },
  { seconds: 10 * 60, label: '10 min' },
  { seconds: 5 * 60, label: '5 min' },
  { seconds: 3 * 60, label: '3 min' },
  { seconds: 1 * 60, label: '1 min' },
]
// Window length and amplitude both independently make real EEG illegible if left too extreme
// (CC_STEP4_FIX_REPORT.md addendum: a full-file window compressed to ~1205px is a dense
// min/max envelope at ANY amplitude, and amplitude presets up to 30 µV can't contain a file's
// real excursions at ANY window length) — both were changed together per Boti's direction.
// `1 min` is the shortest entry in DURATION_OPTIONS (no `30 s` preset exists to pick instead).
const DEFAULT_WINDOW_SEC = 1 * 60

const AMPLITUDE_OPTIONS = [30, 20, 15, 10, 7, 5]
// SPEC §6.4 lists 5/7/10/15/20/30 µV as the available preset levels, not a mandated default
// (confirmed — no default is specified there or anywhere else in SPEC). 7 µV was previously
// just the list's mid-entry; at real scalp EEG amplitude it saturates the row height almost
// everywhere (see CC_STEP4_FIX_REPORT.md items 1/2). 20 µV chosen per Boti's direction.
const DEFAULT_AMPLITUDE_UV = 20

const SPEED_OPTIONS = [8, 4, 2, 1]

function clamp(v, lo, hi) {
  return Math.max(lo, Math.min(hi, v))
}

function windowLabel(seconds) {
  const found = WINDOW_OPTIONS.find((o) => o.seconds === seconds)
  return found ? found.label : `${Math.round(seconds / 60)} min`
}

// Filter toggle pill (SPEC §6.4's lff/hff/60 trio). The three buttons visually toggle
// independently (matches UI/B1a) but all gate the SAME real filtered series — see the
// report's "filter toggle semantics" note: pipeline_demo's bandpass+notch is one combined,
// non-separable filter (preprocessing.py Step 1+2), so there is no real "highpass-only" or
// "lowpass-only" signal to show. Filtered is prominent whenever at least one is on.
// UI/B1a shows this as a small violet badge holding the abbreviated label ("lff"/"hff"/
// "60"), with a corner dot marking on/off (green/gray) and the value ("0.5 Hz") as plain
// body text beside it — not a pill outline wrapping the whole control (see
// CC_STEP4_FIX_PROMPT.md item 3).
function FilterToggle({ active, onClick, badge, label }) {
  return (
    <button type="button" onClick={onClick} className="flex items-center gap-1.5 font-mono text-xs">
      <span className="relative inline-flex items-center justify-center w-7 h-7 rounded-full bg-brand text-white text-[10px] leading-none">
        {badge}
        <span
          className={`absolute -bottom-px -right-px w-2 h-2 rounded-full ring-1 ring-surface ${
            active ? 'bg-accept' : 'bg-unseen'
          }`}
        />
      </span>
      {label && <span className="text-text-secondary">{label}</span>}
    </button>
  )
}

export default function AnalysisScreen({ username, onLoggedOut, subjectId, initialFileId, onBack }) {
  const [subject, setSubject] = useState(null)
  const [currentFileId, setCurrentFileId] = useState(initialFileId)
  const [fileMeta, setFileMeta] = useState(null)
  const [error, setError] = useState('')
  const [banner, setBanner] = useState('')
  const bannerTimer = useRef(null)

  const [windowSec, setWindowSec] = useState(DEFAULT_WINDOW_SEC)
  const [windowStartSec, setWindowStartSec] = useState(0)
  const [amplitudeUv, setAmplitudeUv] = useState(DEFAULT_AMPLITUDE_UV)
  const [filters, setFilters] = useState({ lff: true, hff: true, notch: true })
  const [speed, setSpeed] = useState(1)
  const [playing, setPlaying] = useState(false)
  const [playheadSec, setPlayheadSec] = useState(null)
  const [waveform, setWaveform] = useState(null)
  const [widthPx, setWidthPx] = useState(0)
  const [openPopover, setOpenPopover] = useState(null) // 'duration'|'amplitude'|'speed'|'files'|null

  const anyFilterOn = filters.lff || filters.hff || filters.notch
  const waveformReqId = useRef(0)

  function showBanner(text, ms = 4000) {
    setBanner(text)
    clearTimeout(bannerTimer.current)
    bannerTimer.current = setTimeout(() => setBanner(''), ms)
  }

  // Close any open popover on an outside click — every popover trigger+panel pair shares
  // the `data-popover` wrapper attribute (see render below), so one listener covers all of
  // them regardless of which is open.
  useEffect(() => {
    function onDocMouseDown(e) {
      if (!e.target.closest('[data-popover]')) setOpenPopover(null)
    }
    document.addEventListener('mousedown', onDocMouseDown)
    return () => document.removeEventListener('mousedown', onDocMouseDown)
  }, [])

  useEffect(() => {
    getSubjectDetail(subjectId)
      .then(setSubject)
      .catch((err) => setError(err.message))
  }, [subjectId])

  // Opening a file: fetch its metadata, mark it Viewing (SPEC §5.2 — only actually
  // transitions a file that's currently 'View'), reset the view window, and refresh the
  // subject so the header/dropdown/progress reflect the new status immediately.
  useEffect(() => {
    let cancelled = false
    setFileMeta(null)
    setWaveform(null)
    setPlaying(false)
    setWindowStartSec(0)
    setPlayheadSec(null)

    getFile(currentFileId)
      .then((f) => {
        if (cancelled) return
        setFileMeta(f)
        setPlayheadSec(0)
      })
      .catch((err) => !cancelled && setError(err.message))

    markFileViewing(currentFileId)
      .then(() => !cancelled && getSubjectDetail(subjectId).then((s) => !cancelled && setSubject(s)))
      .catch(() => {})

    return () => {
      cancelled = true
    }
  }, [currentFileId, subjectId])

  // Waveform fetch — the only backend call Panel EEG makes (SPEC §6.4 / HANDOFF §5).
  // Amplitude and filter-toggle changes are deliberately NOT in this dependency list: both
  // are pure frontend re-renders of data already on hand (see EegPanel).
  useEffect(() => {
    if (!fileMeta || !widthPx) return
    const maxStart = Math.max(0, fileMeta.usable_duration_seconds - windowSec)
    const clampedStart = clamp(windowStartSec, 0, maxStart)
    if (clampedStart !== windowStartSec) {
      setWindowStartSec(clampedStart)
      return
    }
    const endSec = Math.min(clampedStart + windowSec, fileMeta.usable_duration_seconds)
    const reqId = ++waveformReqId.current
    getWaveform(currentFileId, clampedStart, endSec, widthPx)
      .then((wf) => {
        if (reqId === waveformReqId.current) setWaveform(wf)
      })
      .catch((err) => {
        if (reqId === waveformReqId.current) setError(err.message)
      })
  }, [fileMeta, currentFileId, windowSec, windowStartSec, widthPx])

  // Playback — advances the playhead in real time (scaled by `speed`) purely client-side;
  // no backend call, since the whole current window's data is already loaded. Stops at the
  // loaded window's own end rather than paging into the next window (Step 4 scope: panning
  // is manual via the scrub controls below).
  const playRef = useRef({ raf: null, lastTs: null })
  useEffect(() => {
    if (!playing || !waveform) return undefined
    function tick(ts) {
      if (playRef.current.lastTs != null) {
        const dt = (ts - playRef.current.lastTs) / 1000
        setPlayheadSec((prev) => {
          if (prev == null) return prev
          const next = prev + dt * speed
          if (next >= waveform.end_sec) {
            setPlaying(false)
            return waveform.end_sec
          }
          return next
        })
      }
      playRef.current.lastTs = ts
      playRef.current.raf = requestAnimationFrame(tick)
    }
    playRef.current.lastTs = null
    playRef.current.raf = requestAnimationFrame(tick)
    return () => {
      if (playRef.current.raf) cancelAnimationFrame(playRef.current.raf)
      playRef.current.lastTs = null
    }
  }, [playing, speed, waveform])

  function toggleFilter(key) {
    setFilters((f) => ({ ...f, [key]: !f[key] }))
  }

  function handleSelectWindow(seconds) {
    setWindowSec(seconds)
    setOpenPopover(null)
    setPlaying(false)
  }

  function handleSelectAmplitude(uv) {
    setAmplitudeUv(uv)
    setOpenPopover(null)
  }

  function handleSeek(sec) {
    setPlaying(false)
    setPlayheadSec(clamp(sec, windowStartSec, windowStartSec + windowSec))
  }

  const maxStart = fileMeta ? Math.max(0, fileMeta.usable_duration_seconds - windowSec) : 0

  function gotoStart() {
    setPlaying(false)
    setWindowStartSec(0)
    setPlayheadSec(0)
  }
  function pageBack() {
    setPlaying(false)
    setWindowStartSec((s) => {
      const next = Math.max(0, s - windowSec)
      setPlayheadSec(next)
      return next
    })
  }
  function pageForward() {
    setPlaying(false)
    setWindowStartSec((s) => {
      const next = Math.min(maxStart, s + windowSec)
      setPlayheadSec(next)
      return next
    })
  }
  function gotoEnd() {
    setPlaying(false)
    setWindowStartSec(maxStart)
    setPlayheadSec(maxStart)
  }
  function handleSlider(e) {
    const v = Number(e.target.value)
    setPlaying(false)
    setWindowStartSec(v)
    setPlayheadSec(v)
  }

  const fileIndex = subject ? subject.files.findIndex((f) => f.id === currentFileId) : -1

  function handlePrev() {
    if (subject && fileIndex > 0) setCurrentFileId(subject.files[fileIndex - 1].id)
  }
  function handleNext() {
    if (subject && fileIndex >= 0 && fileIndex < subject.files.length - 1) {
      setCurrentFileId(subject.files[fileIndex + 1].id)
    }
  }

  async function handleViewed() {
    const updated = await markFileViewed(currentFileId).catch((err) => {
      setError(err.message)
      return null
    })
    if (!updated) return
    setFileMeta(updated)
    getSubjectDetail(subjectId).then(setSubject).catch(() => {})
  }

  const exportEnabled = Boolean(subject && subject.files.length > 0 && subject.files.every((f) => f.status === 'Viewed'))
  function handleExportClick() {
    if (!exportEnabled) return
    showBanner("Export isn't implemented yet (Step 8).")
  }

  if (!fileMeta || !subject) {
    return (
      <div className="min-h-screen bg-bg text-text font-ui pb-14">
        <Header username={username} onLogout={onLoggedOut} onLogoClick={onBack} />
        <main className="p-6 text-text-muted text-sm">{error || 'Loading…'}</main>
        <Footer />
      </div>
    )
  }

  const viewedCount = subject.files.filter((f) => f.status === 'Viewed').length
  const totalCount = subject.files.length
  const headerTitle = `${fileMeta.filename.replace(/\.edf$/i, '').toUpperCase()} (${String(fileMeta.alert).padStart(2, '0')} alerts to check)`

  const headerCenter = (
    <>
      <span className="font-mono text-sm truncate">{headerTitle}</span>
      <button
        type="button"
        onClick={handlePrev}
        disabled={fileIndex <= 0}
        className="bg-white text-text rounded-control px-3 py-1.5 text-xs font-medium disabled:opacity-40 shrink-0"
      >
        &laquo; Previous
      </button>
      <button
        type="button"
        onClick={handleNext}
        disabled={fileIndex < 0 || fileIndex >= totalCount - 1}
        className="bg-white text-text rounded-control px-3 py-1.5 text-xs font-medium disabled:opacity-40 shrink-0"
      >
        Next &raquo;
      </button>
      <span className="w-px h-6 bg-white/30 shrink-0" />
      <button
        type="button"
        onClick={handleViewed}
        className="bg-white text-text rounded-control px-3 py-1.5 text-xs font-medium shrink-0"
      >
        Viewed
      </button>
      <button
        type="button"
        onClick={handleExportClick}
        disabled={!exportEnabled}
        className="bg-white/70 text-text-muted rounded-control px-3 py-1.5 text-xs font-medium disabled:opacity-50 shrink-0"
      >
        &#8681; Export
      </button>
      <div className="relative ml-auto shrink-0" data-popover>
        <button
          type="button"
          onClick={() => setOpenPopover((p) => (p === 'files' ? null : 'files'))}
          className="bg-white text-text rounded-control px-3 py-1.5 text-xs font-mono flex items-center gap-1"
        >
          {fileMeta.filename}
          <ChevronDownIcon className="w-3 h-3" />
        </button>
        {openPopover === 'files' && (
          <div className="absolute right-0 mt-1 w-56 bg-surface border border-border rounded-control shadow-panel z-50 max-h-72 overflow-y-auto text-text">
            {subject.files.map((f) => (
              <button
                key={f.id}
                type="button"
                onClick={() => {
                  setCurrentFileId(f.id)
                  setOpenPopover(null)
                }}
                className={`w-full text-left px-3 py-2 text-xs font-mono ${
                  f.id === currentFileId ? 'bg-[#EFF6FF] font-semibold' : 'hover:bg-bg text-text-secondary'
                }`}
              >
                {f.filename} ({f.alert})
              </button>
            ))}
          </div>
        )}
      </div>
    </>
  )

  return (
    <div className="min-h-screen bg-bg text-text font-ui pb-14">
      <Header username={username} onLogout={onLoggedOut} onLogoClick={onBack} center={headerCenter} />

      <div className="bg-[#D9D9D9] px-6 py-2.5 flex items-center gap-3">
        <span className="text-xs text-text shrink-0">Progress:</span>
        <div className="flex-1 h-2 bg-white rounded-full overflow-hidden max-w-3xl">
          <div
            className="h-full bg-[#22C55E]"
            style={{ width: totalCount ? `${(viewedCount / totalCount) * 100}%` : '0%' }}
          />
        </div>
        <span className="text-xs font-mono shrink-0">
          {String(viewedCount).padStart(2, '0')}/{totalCount}
        </span>
      </div>

      <main className="p-6">
        {banner && <div className="mb-3 text-sm text-text bg-[#FFFBEB] border border-[#FDE68A] rounded-control px-3 py-2">{banner}</div>}
        {error && <div className="mb-3 text-sm text-reject bg-reject-bg border border-reject rounded-control px-3 py-2">{error}</div>}

        <div className="border border-border bg-surface">
          <div className="flex items-center gap-3 px-4 py-3 border-b border-border flex-wrap">
            <h2 className="text-lg font-semibold mr-2 shrink-0">Seizure detection</h2>

            <div className="relative" data-popover>
              <button
                type="button"
                onClick={() => setOpenPopover((p) => (p === 'duration' ? null : 'duration'))}
                className="border border-border rounded-control px-3 py-1.5 text-sm font-mono"
              >
                &#8882;&#8883; {windowLabel(windowSec)}
              </button>
              {openPopover === 'duration' && (
                <div className="absolute left-0 mt-1 w-28 bg-surface border border-border rounded-control shadow-panel z-50 py-1 max-h-72 overflow-y-auto">
                  <div className="px-3 py-1 text-[11px] font-semibold text-text-muted">Duration</div>
                  {WINDOW_OPTIONS.map((opt) => (
                    <button
                      key={opt.seconds}
                      type="button"
                      onClick={() => handleSelectWindow(opt.seconds)}
                      className={`w-full text-left px-3 py-1.5 text-sm ${
                        opt.seconds === windowSec ? 'bg-[#EFF6FF] font-semibold text-interaction' : 'hover:bg-bg'
                      }`}
                    >
                      {opt.label}
                    </button>
                  ))}
                </div>
              )}
            </div>

            <div className="relative" data-popover>
              <button
                type="button"
                onClick={() => setOpenPopover((p) => (p === 'amplitude' ? null : 'amplitude'))}
                className="border border-border rounded-control px-3 py-1.5 text-sm font-mono"
              >
                &#8661; {amplitudeUv} uV
              </button>
              {openPopover === 'amplitude' && (
                <div className="absolute left-0 mt-1 w-24 bg-surface border border-border rounded-control shadow-panel z-50 py-1">
                  <div className="px-3 py-1 text-[11px] font-semibold text-text-muted">Amplitude</div>
                  {AMPLITUDE_OPTIONS.map((uv) => (
                    <button
                      key={uv}
                      type="button"
                      onClick={() => handleSelectAmplitude(uv)}
                      className={`w-full text-left px-3 py-1.5 text-sm ${
                        uv === amplitudeUv ? 'bg-[#EFF6FF] font-semibold text-interaction' : 'hover:bg-bg'
                      }`}
                    >
                      {uv} uV
                    </button>
                  ))}
                </div>
              )}
            </div>

            <button
              type="button"
              disabled
              title="Select Range — event creation lands in Step 6"
              className="border border-border rounded-control px-3 py-1.5 text-sm font-mono opacity-40 cursor-not-allowed"
            >
              &#8926;&#8927; Select Range
            </button>

            <div className="flex items-center gap-2 ml-auto">
              <FilterToggle active={filters.lff} onClick={() => toggleFilter('lff')} badge="lff" label="0.5 Hz" />
              <FilterToggle active={filters.hff} onClick={() => toggleFilter('hff')} badge="hff" label="60 Hz" />
              <FilterToggle active={filters.notch} onClick={() => toggleFilter('notch')} badge="60" />
            </div>
          </div>

          <div className="px-4 py-4 overflow-x-auto">
            <EegPanel
              channels={fileMeta.channels}
              waveform={waveform}
              amplitudeUv={amplitudeUv}
              anyFilterOn={anyFilterOn}
              playheadSec={playheadSec}
              fileMeta={fileMeta}
              onSeek={handleSeek}
              onWidthChange={setWidthPx}
            />
          </div>

          <div className="flex items-center gap-3 bg-[#D9D9D9] px-4 py-2.5 border-t border-border">
            <button type="button" onClick={gotoStart} className="text-lg leading-none px-1" aria-label="Jump to start">
              &laquo;
            </button>
            <button type="button" onClick={pageBack} className="text-lg leading-none px-1" aria-label="Page back">
              &lsaquo;
            </button>
            <input
              type="range"
              min={0}
              max={Math.max(maxStart, 0.001)}
              step={0.1}
              value={windowStartSec}
              onChange={handleSlider}
              className="flex-1 accent-interaction"
            />
            <button type="button" onClick={pageForward} className="text-lg leading-none px-1" aria-label="Page forward">
              &rsaquo;
            </button>
            <button type="button" onClick={gotoEnd} className="text-lg leading-none px-1" aria-label="Jump to end">
              &raquo;
            </button>
            <button
              type="button"
              onClick={() => setPlaying((p) => !p)}
              className="w-8 h-8 rounded-full bg-brand text-white flex items-center justify-center shrink-0"
              aria-label={playing ? 'Pause' : 'Play'}
            >
              {playing ? <PauseIcon className="w-4 h-4" /> : <PlayIcon className="w-4 h-4 ml-0.5" />}
            </button>
            <div className="relative" data-popover>
              <button
                type="button"
                onClick={() => setOpenPopover((p) => (p === 'speed' ? null : 'speed'))}
                className="border border-border rounded-control px-2 py-1 text-xs font-mono flex items-center gap-1 bg-surface"
              >
                {speed}x
                <ChevronDownIcon className="w-3 h-3" />
              </button>
              {openPopover === 'speed' && (
                <div className="absolute bottom-full right-0 mb-1 bg-surface border border-border rounded-control shadow-panel z-50 py-1 w-16">
                  {SPEED_OPTIONS.map((s) => (
                    <button
                      key={s}
                      type="button"
                      onClick={() => {
                        setSpeed(s)
                        setOpenPopover(null)
                      }}
                      className={`w-full text-left px-3 py-1 text-xs ${
                        s === speed ? 'bg-[#EFF6FF] font-semibold text-interaction' : 'hover:bg-bg'
                      }`}
                    >
                      {s}x
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  )
}
