import { useEffect, useState } from 'react'
import Header from '../components/Header.jsx'
import Footer from '../components/Footer.jsx'
import { SearchIcon } from '../components/icons.jsx'
import { listSubjects } from '../api.js'

const COLUMNS = ['ID', 'No. files', 'Start date', 'Duration', 'Alert', 'Status', 'Memo']

// Database screen, empty state, per UI/A0a. Search, Create new, and the Delete/Open row
// actions render visually here but are NOT wired — that's Step 3 (§5.4-§5.7), see the
// TODO comments below.
export default function DatabaseScreen({ username, onLoggedOut }) {
  const [subjects, setSubjects] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    listSubjects()
      .then(setSubjects)
      .catch(() => setSubjects([]))
      .finally(() => setLoading(false))
  }, [])

  return (
    <div className="min-h-screen bg-bg text-text font-ui pb-14">
      <Header username={username} onLogout={onLoggedOut} />

      <main className="p-6">
        <div className="flex items-center gap-2 mb-4 max-w-sm">
          {/* TODO(step3): wire to SZSCAN_SPEC_v5.md §5.4 — filter by file/subject name,
              filters only on button click, not per keystroke. */}
          <input
            type="text"
            placeholder="Search"
            className="flex-1 border border-border rounded-control px-3 py-2 text-sm"
            disabled
          />
          <button
            type="button"
            disabled
            className="border border-border rounded-control p-2 disabled:opacity-60"
            aria-label="Search"
          >
            <SearchIcon className="w-5 h-5 text-text" />
          </button>
        </div>

        <div className="border border-border rounded-panel overflow-hidden">
          <div className="grid grid-cols-7 bg-[#F1F5F9] text-sm font-medium px-4 py-2">
            {COLUMNS.map((col) => (
              <span key={col}>{col}</span>
            ))}
          </div>
          {loading ? null : subjects.length === 0 ? (
            <div className="flex items-center justify-center py-24 text-text-muted text-3xl font-mono">
              No data
            </div>
          ) : (
            // TODO(step3): render subject/file rows (SZSCAN_SPEC_v5.md §5.1) once
            // Create new/upload/process exists — the database is empty by construction
            // until then, so this branch is unreachable today.
            <div className="divide-y divide-border">
              {subjects.map((s) => (
                <div key={s.id} className="grid grid-cols-7 px-4 py-2 text-sm">
                  <span className="font-semibold">{s.id}</span>
                  <span>{s.no_files}</span>
                  <span>{s.start_date}</span>
                  <span>{s.duration_seconds}</span>
                  <span />
                  <span />
                  <span>{s.memo}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="flex items-center justify-between mt-4">
          <button
            type="button"
            // TODO(step3): open the Create new panel (SZSCAN_SPEC_v5.md §5.5).
            className="bg-brand text-white rounded-control px-4 py-2 text-sm font-medium"
          >
            Create new
          </button>
          <div className="flex gap-2">
            {/* TODO(step3): Delete (§5.6) / Open (§5.7) act on the selected row; there is
                never a selection with an empty table, so both stay disabled here. */}
            <button type="button" disabled className="border border-border rounded-control px-4 py-2 text-sm disabled:opacity-60">
              Delete
            </button>
            <button type="button" disabled className="border border-border rounded-control px-4 py-2 text-sm disabled:opacity-60">
              Open
            </button>
            <button type="button" disabled className="border border-border rounded-control px-4 py-2 text-sm disabled:opacity-60">
              Cancel
            </button>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  )
}
