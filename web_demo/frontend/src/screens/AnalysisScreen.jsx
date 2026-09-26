import { useEffect, useRef, useState } from 'react'
import Header from '../components/Header.jsx'
import Footer from '../components/Footer.jsx'
import EegPanel from '../components/EegPanel.jsx'
import MiniTimeline from '../components/MiniTimeline.jsx'
import PanelEvent from '../components/PanelEvent.jsx'
import AttributionPanel from '../components/AttributionPanel.jsx'
import { ChevronDownIcon, PlayIcon, PauseIcon } from '../components/icons.jsx'
import {
  getFile,
  getSubjectDetail,
  getWaveform,
  getTimeline,
  getFileEvents,
  updateEvent,
  deleteEvent,
  createEvent,
  markFileViewed,
  markFileViewing,
  exportSubjectTxt,
} from '../api.js'

// Analysis screen — Panel EEG + toolbar + scrub (Step 4) plus, as of Step 5
// (CC_STEP5_PROMPT.md), the mini-timeline and Panel Event columns. Channel Attribution is
// still Step 7+ scope and deliberately not rendered here — same "don't reserve blank space"
// precedent as Step 4's report: the right column holds only what actually exists yet.

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

// SPEC §6.4 / C18 (2026-09-21, floor decided in Step 5 fix round 6): 500/250/150/100/75 µV.
// Round 2 first extended the old 5/7/10/15/20/30 max-30 list once measured data
// (CC_STEP5_FIX2_REPORT.md §3) showed real per-channel amplitude running median ~106–111 µV,
// peaks ~1200–1800 µV, far past the old range. Round 4 (CC_STEP5_FIX4_REPORT.md §1) then
// measured the file's own calmest segment and found the 6 old small levels never earn their
// place even there (median spread ~102 µV, same regime as a busy window) — Boti decided the
// final floor at 75 µV; 50/30/20/15/10/7/5 µV are dropped entirely, not kept for a flat/
// interictal case that this data doesn't actually have.
const AMPLITUDE_OPTIONS = [500, 250, 150, 100, 75]
// Not a mandated default (confirmed — none is specified in SPEC). 20 µV (chosen per
// CC_STEP4_FIX_REPORT.md items 1/2) no longer exists once the floor moved to 75 µV in round 6
// (CC_STEP5_FIX6_PROMPT.md item 1) — the default must be one of AMPLITUDE_OPTIONS' own values.
// Set to the new floor, 75 µV, as the closest analog to the old default's role (smallest
// available option); this is a judgment call to keep the default valid, not something Boti was
// explicitly asked about — flagged in CC_STEP5_FIX6_REPORT.md for override if he wants otherwise.
const DEFAULT_AMPLITUDE_UV = 75

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
  // CC_STEP5_FIX4_PROMPT.md item 2: default must be genuinely raw. All three OFF on a fresh
  // load — SPEC §6.4 ("when on, the filtered wave is highlighted, raw recedes") and DESIGN
  // §3's raw/filtered tokens both describe an on/off toggle from a raw baseline, not three
  // filters defaulting to already-applied. A prior default of all-true meant the very first
  // thing shown was already-filtered data drawn prominent (EegPanel's `anyFilterOn` gate),
  // with raw merely the dimmed background — the opposite of CLAUDE.md's "everything shown
  // must be data that genuinely went into the computation" as the *default*, unannounced
  // view.
  const [filters, setFilters] = useState({ lff: false, hff: false, notch: false })
  const [speed, setSpeed] = useState(1)
  const [playing, setPlaying] = useState(false)
  const [playheadSec, setPlayheadSec] = useState(null)
  const [waveform, setWaveform] = useState(null)
  const [widthPx, setWidthPx] = useState(0)
  const [openPopover, setOpenPopover] = useState(null) // 'duration'|'amplitude'|'speed'|'files'|null

  // Step 5 (CC_STEP5_PROMPT.md): mini-timeline's score row + both panels' shared event list.
  const [timeline, setTimeline] = useState(null) // {score, window_sec} | null
  const [events, setEvents] = useState([])
  const [selectedEventId, setSelectedEventId] = useState(null)
  // Step 6 (CC_STEP6_PROMPT.md §6.6, Select Range): marking-mode state. `editingEventId`
  // non-null means this mark's two clicks will PATCH that Human event's range instead of
  // creating a new one (the Edit reading — see the report). `markingOnsetSec` is the first
  // click; the second click (in EegPanel's onGridClick handler below) completes the mark.
  const [selectRangeActive, setSelectRangeActive] = useState(false)
  const [markingOnsetSec, setMarkingOnsetSec] = useState(null)
  const [editingEventId, setEditingEventId] = useState(null)
  // Live-updated mirror of selectedEventId for handleSaveEvent's async catch below (item 4):
  // a slow save's error must not land after the user has already switched to another event.
  const selectedEventIdRef = useRef(selectedEventId)
  useEffect(() => {
    selectedEventIdRef.current = selectedEventId
  }, [selectedEventId])
  // Mirror of fileMeta for the playback tick below (CC_STEP5_FIX3_PROMPT.md item 1): read
  // without adding fileMeta to the playback effect's deps, which would reset the rAF loop's
  // lastTs (and briefly stutter playback) on every unrelated fileMeta refresh (e.g. alert
  // count changes from a save elsewhere).
  const fileMetaRef = useRef(fileMeta)
  useEffect(() => {
    fileMetaRef.current = fileMeta
  }, [fileMeta])

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
    setTimeline(null)
    setEvents([])
    setSelectedEventId(null)
    setSelectRangeActive(false)
    setMarkingOnsetSec(null)
    setEditingEventId(null)

    getFile(currentFileId)
      .then((f) => {
        if (cancelled) return
        setFileMeta(f)
        setPlayheadSec(0)
      })
      .catch((err) => !cancelled && setError(err.message))

    // Mini-timeline's score row — read-only cache, never re-runs the pipeline (SPEC §6.3 /
    // CC_STEP5_REPORT.md's backfill note). A 404 here means this file's score array was
    // never persisted; degrade to "no score line" rather than blocking the whole screen.
    getTimeline(currentFileId)
      .then((t) => !cancelled && setTimeline(t))
      .catch(() => !cancelled && setTimeline(null))

    getFileEvents(currentFileId)
      .then((evs) => !cancelled && setEvents(evs))
      .catch((err) => !cancelled && setError(err.message))

    markFileViewing(currentFileId)
      .then(() => !cancelled && getSubjectDetail(subjectId).then((s) => !cancelled && setSubject(s)))
      .catch(() => {})

    return () => {
      cancelled = true
    }
  }, [currentFileId, subjectId])

  // Panel Event is the primary control source (SPEC §6.5): clicking a row jumps Panel EEG
  // to that event's onset (with a little pre-roll so the onset isn't flush against the
  // window's left edge) and moves the playhead there — the mini-timeline's own playhead
  // updates for free since it's driven by this same `playheadSec` state, one-way from here.
  function handleToggleEvent(eventId) {
    // CC_STEP5_FIX2_PROMPT.md item 4: a stale validation error (e.g. "review_status must be
    // one of Accept/Reject/Uncertain.") from a previous save must not survive switching to a
    // different event.
    setError('')
    if (eventId === selectedEventId) {
      setSelectedEventId(null)
      return
    }
    setSelectedEventId(eventId)
    const ev = events.find((e) => e.id === eventId)
    if (!ev || !fileMeta) return
    setPlaying(false)
    const preRoll = windowSec * 0.1
    const start = clamp(ev.onset_sec - preRoll, 0, Math.max(0, fileMeta.usable_duration_seconds - windowSec))
    setWindowStartSec(start)
    setPlayheadSec(ev.onset_sec)
  }

  async function refreshEventsAndAlert() {
    const [evs] = await Promise.all([
      getFileEvents(currentFileId),
      getFile(currentFileId).then(setFileMeta),
      getSubjectDetail(subjectId).then(setSubject),
    ])
    setEvents(evs)
  }

  async function handleSaveEvent(eventId, payload) {
    // Clear any stale error up front — a successful save must not leave a previous attempt's
    // validation message on screen (CC_STEP5_FIX2_PROMPT.md item 4). If this attempt also
    // fails, the catch below immediately replaces it with the new message — unless the user
    // has since switched to a different event, in which case a slow, now-irrelevant error
    // must not reappear on top of whatever they've moved on to.
    setError('')
    await updateEvent(eventId, payload).catch((err) => {
      if (selectedEventIdRef.current === eventId) setError(err.message)
      throw err
    })
    await refreshEventsAndAlert().catch((err) => {
      if (selectedEventIdRef.current === eventId) setError(err.message)
    })
  }

  async function handleDeleteEvent(eventId) {
    await deleteEvent(eventId).catch((err) => {
      setError(err.message)
      throw err
    })
    if (selectedEventId === eventId) setSelectedEventId(null)
    await refreshEventsAndAlert().catch((err) => setError(err.message))
  }

  // Select Range (CC_STEP6_PROMPT.md §6.6). Clicking the toolbar button toggles marking
  // mode on; clicking it again mid-mark cancels cleanly (item 12 — no explicit cancel
  // affordance in the mockups, so this reuses the same toggle rather than adding a second
  // control) — no partial event is ever created from a cancelled mark, since creation only
  // happens after both clicks land, in handleGridClick below.
  function handleToggleSelectRange() {
    if (selectRangeActive) {
      setSelectRangeActive(false)
      setMarkingOnsetSec(null)
      setEditingEventId(null)
      return
    }
    setPlaying(false)
    setSelectRangeActive(true)
  }

  // Edit (item 11's reading): re-enter Select Range-style marking, scoped to overwrite this
  // Human event's range instead of creating a new one, once both clicks land.
  function handleEditEvent(ev) {
    setPlaying(false)
    setEditingEventId(ev.id)
    setMarkingOnsetSec(null)
    setSelectRangeActive(true)
  }

  // The single click target for Panel EEG's grid: a plain seek outside marking mode, or the
  // onset/offset click of a Select Range mark. Direction-agnostic (item 13) — sorts the two
  // points regardless of click order, so a right-to-left drag still yields onset < offset.
  async function handleGridClick(sec) {
    if (!selectRangeActive) {
      handleSeek(sec)
      return
    }
    if (markingOnsetSec == null) {
      setMarkingOnsetSec(sec)
      return
    }
    const onset = Math.min(markingOnsetSec, sec)
    const offset = Math.max(markingOnsetSec, sec)
    const targetEventId = editingEventId
    setSelectRangeActive(false)
    setMarkingOnsetSec(null)
    setEditingEventId(null)
    setError('')
    try {
      const saved = targetEventId != null
        ? await updateEvent(targetEventId, { onset_sec: onset, offset_sec: offset })
        : await createEvent(currentFileId, onset, offset)
      await refreshEventsAndAlert()
      // Matches UI/B3c: the just-created (or just-redrawn) event lands expanded, showing
      // its own Onset/Offset/Duration + Delete/Edit immediately, not collapsed in the list.
      setSelectedEventId(saved.id)
    } catch (err) {
      setError(err.message)
    }
  }

  // Waveform fetch — the only backend call Panel EEG makes (SPEC §6.4 / HANDOFF §5).
  // Amplitude and filter-toggle changes are deliberately NOT in this dependency list: both
  // are pure frontend re-renders of data already on hand (see EegPanel).
  // Debounced (CC_STEP5_FIX2_PROMPT.md item 1): dragging the bottom scrub bar fires an
  // onChange — and therefore a windowStartSec update — on every pixel of mouse movement.
  // Without this, each of those fired its own fetch immediately; live testing showed the
  // resulting flood of in-flight requests (confirmed via network log: dozens per drag)
  // made Panel EEG's displayed window lag several seconds behind the slider, which is what
  // reads as "dragging doesn't move it" during a normal drag-and-look test. Only the
  // position the drag actually settles on now triggers a fetch.
  useEffect(() => {
    if (!fileMeta || !widthPx) return
    const maxStart = Math.max(0, fileMeta.usable_duration_seconds - windowSec)
    const clampedStart = clamp(windowStartSec, 0, maxStart)
    if (clampedStart !== windowStartSec) {
      setWindowStartSec(clampedStart)
      return
    }
    const endSec = Math.min(clampedStart + windowSec, fileMeta.usable_duration_seconds)
    const timer = setTimeout(() => {
      const reqId = ++waveformReqId.current
      getWaveform(currentFileId, clampedStart, endSec, widthPx)
        .then((wf) => {
          if (reqId === waveformReqId.current) setWaveform(wf)
        })
        .catch((err) => {
          if (reqId === waveformReqId.current) setError(err.message)
        })
    }, 120)
    return () => clearTimeout(timer)
  }, [fileMeta, currentFileId, windowSec, windowStartSec, widthPx])

  // Playback — advances the playhead in real time (scaled by `speed`) purely client-side;
  // no backend call for the playhead itself. CC_STEP5_FIX3_PROMPT.md item 1: once the
  // playhead reaches the right edge of the currently loaded window, the window itself must
  // advance (shift forward + fetch the next segment, HANDOFF §5's decimated-window-fetch
  // architecture) rather than freezing playback at that boundary. Advancing windowStartSec
  // here re-triggers the waveform-fetch effect above; this effect's own `waveform` dependency
  // then restarts the rAF loop (lastTs reset to null) once the new segment lands, so dt isn't
  // computed across the fetch gap.
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
            const usableDuration = fileMetaRef.current?.usable_duration_seconds ?? waveform.end_sec
            const atRecordingEnd = waveform.end_sec >= usableDuration - 1e-6
            if (atRecordingEnd) {
              setPlaying(false)
              return waveform.end_sec
            }
            // More recording ahead: shift the displayed window to start exactly where this
            // one ended, so playback continues into it instead of stopping at the boundary.
            setWindowStartSec(waveform.end_sec)
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
  async function handleExportClick() {
    if (!exportEnabled) return
    try {
      await exportSubjectTxt(subjectId)
    } catch (err) {
      showBanner(err.message)
    }
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
      {/* CC_STEP6_FIX2_PROMPT.md item 1: UI/B1a and B2a put the title itself inside the
          right-hand cluster, immediately left of Previous — not flush against the logo.
          `ml-auto` now sits on this whole cluster (title included) so flexible space opens
          up between the logo group and here, with the title, Previous/Next, divider,
          Viewed/Export, and (below) the file dropdown all packed together on the right. */}
      <div className="flex items-center gap-3 ml-auto shrink-0">
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
          className={`rounded-control px-3 py-1.5 text-xs font-medium shrink-0 ${
            exportEnabled ? 'bg-white text-text' : 'bg-white/70 text-text-muted opacity-50'
          }`}
        >
          &#8681; Export
        </button>
      </div>
      <div className="relative shrink-0" data-popover>
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

        <MiniTimeline
          fileMeta={fileMeta}
          score={timeline?.score ?? null}
          scoreWindowSec={timeline?.window_sec ?? null}
          events={events}
          playheadSec={playheadSec}
          selectedEventId={selectedEventId}
        />

        <div className="flex gap-4 items-stretch mt-4">
        <div className="flex-1 min-w-0">
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
              onClick={handleToggleSelectRange}
              title={selectRangeActive ? 'Click to cancel' : undefined}
              className={`border rounded-control px-3 py-1.5 text-sm font-mono ${
                selectRangeActive ? 'bg-brand text-white border-brand' : 'border-border'
              }`}
            >
              &#8926;&#8927;{' '}
              {selectRangeActive
                ? markingOnsetSec == null
                  ? 'Click onset…'
                  : 'Click offset…'
                : 'Select Range'}
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
              onGridClick={handleGridClick}
              onWidthChange={setWidthPx}
              selectRangeActive={selectRangeActive}
              markingOnsetSec={markingOnsetSec}
              events={events}
              selectedEventId={selectedEventId}
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
              // CC_STEP7_FIX_PROMPT.md Part A: supersedes the round-7 formula above (`max =
              // usable_duration_seconds`, `value = windowStartSec`) — that formula can never
              // reach 100%, since windowStartSec's largest reachable value is `maxStart =
              // usable_duration - windowSec`, strictly less than usable_duration whenever
              // windowSec > 0 (a 1 min window on a 1 h file left the handle stuck ≈97-98%).
              // Standard scrollbar convention instead: position = windowStartSec / maxStart,
              // i.e. `max` IS `maxStart` (already computed above for pageForward/gotoEnd/the
              // waveform-fetch clamp) — 0% at windowStartSec=0, 100% at windowStartSec=maxStart,
              // linear between. When maxStart is 0 (window length >= file duration) the input
              // is disabled outright rather than rendering a degenerate min=max=0 track.
              max={maxStart}
              step={0.1}
              value={windowStartSec}
              onChange={handleSlider}
              disabled={maxStart <= 0}
              className="flex-1 accent-interaction disabled:opacity-50"
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
        </div>

        {/* CC_STEP7_FIX_PROMPT.md Part B: UI/B2a stacks Event Panel + Attribution Panel in
            this column with the column's TOTAL height equal to the EEG card's height (the
            EEG card alone defines the row's height; this column must not contribute to it).
            Technique: this outer div is `relative` with no intrinsic height of its own
            (nothing here sits in normal flow except position, so it takes only whatever
            height `items-stretch` on the row above gives it — the EEG card's natural
            height); the inner wrapper is `absolute inset-0`, taken out of flow entirely, so
            IT sees a fixed, definite height to split between the two panels. Each panel is
            `flex-1 basis-0 min-h-0` (measured from UI/B2a: ≈0.49/0.49 of the EEG card height
            with a small gap — near enough to equal halves that a plain 50/50 split matches
            it) with its own `overflow-y-auto` inside (built into PanelEvent already since
            Step 5; AttributionPanel restructured this round). No hardcoded pixel height or
            `maxHeight` anywhere here — that was the Step 5 round-1 mistake this deliberately
            avoids repeating. */}
        <div className="w-[340px] shrink-0 relative">
          <div className="absolute inset-0 flex flex-col gap-3">
            <div className="flex-1 basis-0 min-h-0">
              <PanelEvent
                events={events}
                fileMeta={fileMeta}
                selectedEventId={selectedEventId}
                editingEventId={editingEventId}
                onToggleEvent={handleToggleEvent}
                onSaveEvent={handleSaveEvent}
                onDeleteEvent={handleDeleteEvent}
                onEditEvent={handleEditEvent}
                onClearError={() => setError('')}
              />
            </div>
            <div className="flex-1 basis-0 min-h-0">
              <AttributionPanel event={events.find((e) => e.id === selectedEventId) || null} />
            </div>
          </div>
        </div>
        </div>
      </main>

      <Footer />
    </div>
  )
}
