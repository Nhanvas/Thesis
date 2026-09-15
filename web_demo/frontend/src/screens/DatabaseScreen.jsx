import { useEffect, useRef, useState } from 'react'
import Header from '../components/Header.jsx'
import Footer from '../components/Footer.jsx'
import ConfirmDialog from '../components/ConfirmDialog.jsx'
import CreateNewPanel from './CreateNewPanel.jsx'
import { SearchIcon } from '../components/icons.jsx'
import {
  ChevronDownIcon,
  ChevronRightIcon,
  CheckCircleFilledIcon,
  CircleOutlineIcon,
  HalfCircleIcon,
} from '../components/icons.jsx'
import { acknowledgeUpload, deleteSubject, getUpload, listSubjects } from '../api.js'

const COLUMNS = ['ID', '| No. files', 'Start date', 'Duration', 'Alert', '| Status', 'Memo']
const POLL_MS = 1500

function StatusBadge({ status }) {
  if (status === 'Viewed') {
    return (
      <span className="inline-flex items-center gap-1.5 text-[#15803D]">
        <CheckCircleFilledIcon className="w-4 h-4" /> Viewed
      </span>
    )
  }
  if (status.startsWith('Viewing')) {
    const frac = status.replace('Viewing ', '')
    return (
      <span className="inline-flex items-center gap-1.5 text-[#B45309]">
        <HalfCircleIcon className="w-4 h-4" /> Viewing <span className="font-mono text-xs">{frac}</span>
      </span>
    )
  }
  return (
    <span className="inline-flex items-center gap-1.5 text-text-secondary">
      <CircleOutlineIcon className="w-4 h-4" /> View
    </span>
  )
}

// Applies SZSCAN_SPEC_v5.md §5.4's search rule to the already-fetched subject list (each
// subject arrives with its child files embedded — see db.py's list_subjects()). Returns
// {rows, noResults} where `rows` is [{subject, files, forceExpand}].
function applySearch(subjects, query) {
  const q = query.trim().toLowerCase()
  if (!q) {
    return { rows: subjects.map((s) => ({ subject: s, files: s.files, forceExpand: null })), noResults: false }
  }
  const rows = []
  for (const s of subjects) {
    if (s.id.toLowerCase().includes(q)) {
      rows.push({ subject: s, files: s.files, forceExpand: true })
      continue
    }
    const matchedFiles = s.files.filter((f) => f.filename.toLowerCase().includes(q))
    if (matchedFiles.length > 0) {
      rows.push({ subject: s, files: matchedFiles, forceExpand: true })
    }
  }
  return { rows, noResults: rows.length === 0 }
}

export default function DatabaseScreen({ username, onLoggedOut }) {
  const [subjects, setSubjects] = useState([])
  const [loading, setLoading] = useState(true)

  const [searchInput, setSearchInput] = useState('')
  const [activeSearch, setActiveSearch] = useState('')
  const [expanded, setExpanded] = useState(() => new Set())
  const [selected, setSelected] = useState(null) // {type: 'subject'|'file', subjectId, fileId}
  const [confirmDeleteId, setConfirmDeleteId] = useState(null)
  const [banner, setBanner] = useState('')

  const [panelMode, setPanelMode] = useState('closed') // closed | open | minimized
  const [session, setSession] = useState(null)
  const bannerTimer = useRef(null)

  function refreshSubjects() {
    return listSubjects()
      .then(setSubjects)
      .catch(() => setSubjects([]))
  }

  useEffect(() => {
    refreshSubjects().finally(() => setLoading(false))
    // Restore an in-flight session after a page reload (SPEC §5.5: work keeps running
    // regardless of the panel's UI state) — shown minimized since we don't know whether it
    // was open or minimized before the reload.
    getUpload()
      .then((s) => {
        setSession(s)
        setPanelMode('minimized')
      })
      .catch(() => {})
  }, [])

  // Poll the Create New session while one exists, regardless of panel open/minimized —
  // background work keeps running either way (SPEC §5.5).
  //
  // Gated on `hasSession`, not `panelMode`: a backend session is only created lazily on the
  // *first file upload* (see CreateNewPanel's ensureSession). Opening the panel and just typing
  // into Project ID/Memo — no file added yet — means there is genuinely no session yet, and
  // GET /api/uploads/current 404s. Gating on panelMode alone polled immediately in that state
  // and treated every one of those expected 404s as "the session disappeared," closing the
  // panel out from under the user a few seconds after they started typing (root cause of the
  // "panel closes itself" bug — nothing to do with scrolling, which was coincidental timing).
  const hasSession = Boolean(session)
  useEffect(() => {
    if (!hasSession) return undefined
    const id = setInterval(() => {
      getUpload()
        .then(setSession)
        .catch((err) => {
          if (err.status === 404) {
            setSession(null)
            setPanelMode('closed')
          }
        })
    }, POLL_MS)
    return () => clearInterval(id)
  }, [hasSession])

  function showBanner(text, ms = 4000) {
    setBanner(text)
    clearTimeout(bannerTimer.current)
    bannerTimer.current = setTimeout(() => setBanner(''), ms)
  }

  function handleCreateNewClick() {
    if (session && !session.done) {
      showBanner('Processing another subject. Please wait before creating a new one')
      return
    }
    setPanelMode('open')
  }

  function handlePanelClose() {
    setSession(null)
    setPanelMode('closed')
  }

  async function handlePanelDone() {
    await acknowledgeUpload().catch(() => {})
    await refreshSubjects()
    setSession(null)
    setPanelMode('closed')
  }

  function toggleExpand(subjectId) {
    setExpanded((prev) => {
      const next = new Set(prev)
      if (next.has(subjectId)) next.delete(subjectId)
      else next.add(subjectId)
      return next
    })
  }

  function selectSubjectRow(subjectId) {
    setSelected({ type: 'subject', subjectId })
    toggleExpand(subjectId)
  }

  function selectFileRow(subjectId, fileId) {
    setSelected({ type: 'file', subjectId, fileId })
  }

  function handleSearchSubmit(e) {
    e?.preventDefault()
    setActiveSearch(searchInput)
  }

  async function handleConfirmDelete() {
    const id = confirmDeleteId
    setConfirmDeleteId(null)
    await deleteSubject(id).catch(() => {})
    if (selected?.subjectId === id) setSelected(null)
    await refreshSubjects()
  }

  function handleDeleteClick() {
    if (!selected) return
    if (selected.type === 'file') return // SPEC §5.6: subject-level only, no response for a file row
    setConfirmDeleteId(selected.subjectId)
  }

  function handleOpenClick() {
    if (!selected) return
    // SPEC §5.7: Open should select+highlight correctly; the Analysis screen itself is
    // Step 4+ scope (DEMO_BUILD_HANDOFF.md §6 row 4) — not built yet.
    showBanner('Opening the Analysis screen isn’t implemented yet (Step 4).')
  }

  function handleCancelClick() {
    setSelected(null)
  }

  const { rows, noResults } = applySearch(subjects, activeSearch)

  return (
    <div className="min-h-screen bg-bg text-text font-ui pb-14">
      <Header username={username} onLogout={onLoggedOut} />

      <main className="p-6 relative">
        <div className="relative border border-border bg-surface overflow-hidden">
          <div className="p-5 pb-4">
            <form onSubmit={handleSearchSubmit} className="flex items-center gap-2 max-w-sm">
              <input
                type="text"
                placeholder="Search"
                value={searchInput}
                onChange={(e) => setSearchInput(e.target.value)}
                className="flex-1 border border-border rounded-control px-3 py-2 text-sm"
              />
              <button
                type="submit"
                className="border border-border rounded-control p-2"
                aria-label="Search"
              >
                <SearchIcon className="w-5 h-5 text-text" />
              </button>
            </form>
          </div>

          <div className="border-t border-border">
            <div className="grid grid-cols-7 bg-[#F1F5F9] text-sm font-medium px-4 py-2">
              {COLUMNS.map((col) => (
                <span key={col}>{col}</span>
              ))}
            </div>
            {loading ? null : noResults ? (
              <div className="flex items-center justify-center py-24 text-text-muted text-xl font-mono">
                No results for '{activeSearch}'
              </div>
            ) : rows.length === 0 ? (
              <div className="flex items-center justify-center py-24 text-text-muted text-3xl font-mono">
                No data
              </div>
            ) : (
              <div className="divide-y divide-border">
                {rows.map(({ subject: s, files, forceExpand }) => {
                  const isExpanded = forceExpand ?? expanded.has(s.id)
                  const isSelected = selected?.type === 'subject' && selected.subjectId === s.id
                  return (
                    <div key={s.id}>
                      <div
                        onClick={() => selectSubjectRow(s.id)}
                        className={`grid grid-cols-7 px-4 py-2 text-sm cursor-pointer ${
                          isSelected ? 'bg-[#EFF6FF] border-l-4 border-human' : 'hover:bg-bg'
                        }`}
                      >
                        <span className="font-semibold flex items-center gap-1.5">
                          {isExpanded ? (
                            <ChevronDownIcon className="w-3.5 h-3.5" />
                          ) : (
                            <ChevronRightIcon className="w-3.5 h-3.5" />
                          )}
                          {s.id}
                        </span>
                        <span>{s.no_files} files</span>
                        <span className="font-mono text-xs">{s.start_date ?? ''}</span>
                        <span className="font-mono text-xs">{s.duration}</span>
                        <span>{s.alert}</span>
                        <span>
                          <StatusBadge status={s.status} />
                        </span>
                        <span className="truncate">{s.memo}</span>
                      </div>
                      {isExpanded &&
                        files.map((f) => {
                          const fSelected =
                            selected?.type === 'file' && selected.subjectId === s.id && selected.fileId === f.id
                          return (
                            <div
                              key={f.id}
                              onClick={() => selectFileRow(s.id, f.id)}
                              className={`grid grid-cols-7 px-4 py-2 text-sm cursor-pointer ${
                                fSelected ? 'bg-[#EFF6FF] border-l-4 border-human' : 'hover:bg-bg'
                              }`}
                            >
                              <span className="pl-5 text-text-secondary font-mono text-xs">— {f.filename}</span>
                              <span />
                              <span className="font-mono text-xs">{f.start_date ?? ''}</span>
                              <span className="font-mono text-xs">{f.duration}</span>
                              <span>{f.alert}</span>
                              <span>
                                <StatusBadge status={f.status} />
                              </span>
                              <span />
                            </div>
                          )
                        })}
                    </div>
                  )
                })}
              </div>
            )}
          </div>

          <div className="flex items-center justify-between gap-2 border-t border-border bg-[#D9D9D9] px-5 py-4">
            <div className="flex items-center gap-3">
              <button
                type="button"
                onClick={handleCreateNewClick}
                className="bg-brand text-white rounded-control px-4 py-2 text-sm font-medium"
              >
                Create new
              </button>
              {banner && (
                <span className="text-sm text-text flex items-center gap-1.5">{banner}</span>
              )}
            </div>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={handleDeleteClick}
                disabled={!selected}
                className="border border-border rounded-control px-4 py-2 text-sm bg-surface disabled:opacity-60"
              >
                Delete
              </button>
              <button
                type="button"
                onClick={handleOpenClick}
                disabled={!selected}
                className="border border-border rounded-control px-4 py-2 text-sm bg-surface disabled:opacity-60"
              >
                Open
              </button>
              <button
                type="button"
                onClick={handleCancelClick}
                disabled={!selected}
                className="border border-border rounded-control px-4 py-2 text-sm bg-surface disabled:opacity-60"
              >
                Cancel
              </button>
            </div>
          </div>

          {confirmDeleteId && (
            <ConfirmDialog
              message="Are you sure you want to delete this process?"
              onConfirm={handleConfirmDelete}
              onCancel={() => setConfirmDeleteId(null)}
            />
          )}
        </div>

        {(panelMode === 'open' || panelMode === 'minimized') && (
          // Overlay, not a flex sibling of the table (SZSCAN_SPEC_v5.md §5.5, UI/A1a):
          // floats from the right edge on top of the Database view; the table above keeps
          // its own full-width layout underneath, unaffected by the panel opening/closing.
          //
          // Stays mounted while minimized (CC_STEP3_FIX4_PROMPT.md) — only `hidden` toggles
          // visibility — so CreateNewPanel's own projectId/memo React state survives a
          // minimize/restore cycle instead of being torn down and re-seeded from the last
          // polled session snapshot (which was clobbering in-progress edits).
          <CreateNewPanel
            hidden={panelMode === 'minimized'}
            session={session}
            onSessionChange={setSession}
            onMinimize={() => setPanelMode('minimized')}
            onClose={handlePanelClose}
            onDone={handlePanelDone}
          />
        )}
      </main>

      {panelMode === 'minimized' && (
        <button
          type="button"
          onClick={() => setPanelMode('open')}
          className="fixed bottom-16 right-6 bg-brand text-white rounded-control px-4 py-2 text-sm font-medium shadow-panel z-10"
        >
          {session?.processing ? 'Processing...' : 'Create New (draft)'}
        </button>
      )}

      <Footer />
    </div>
  )
}
