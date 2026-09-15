import { useEffect, useRef, useState } from 'react'
import {
  CheckCircleFilledIcon,
  FileIcon,
  SpinnerIcon,
  StopInCircleIcon,
  UploadCloudIcon,
  WarningTriangleIcon,
  XIcon,
} from '../components/icons.jsx'
import ConfirmDialog from '../components/ConfirmDialog.jsx'
import { addUploadFile, discardUpload, processUpload, removeUploadFile, startUpload } from '../api.js'

// Create New panel — SZSCAN_SPEC_v5.md §5.5, mockups UI/A1a-A2b.
//
// `session` is the backend's upload_manager.py snapshot (null until the first file is
// added — see handleFiles below) or null; the parent (DatabaseScreen) owns the polling
// loop and passes the latest snapshot down on every render. `hidden` is true while the
// panel is minimized — DatabaseScreen keeps this component mounted the whole time a
// draft/session is alive (CC_STEP3_FIX4_PROMPT.md) so projectId/memo survive
// minimize/restore; it only ever toggles this visibility flag.
export default function CreateNewPanel({ hidden, session, onSessionChange, onMinimize, onClose, onDone }) {
  const [projectId, setProjectId] = useState('')
  const [memo, setMemo] = useState('')
  const [error, setError] = useState('') // full-panel takeover message (UI/A1b-style)
  const [dragActive, setDragActive] = useState(false)
  const [finishing, setFinishing] = useState(false)
  const [confirmDiscard, setConfirmDiscard] = useState(false)
  const fileInputRef = useRef(null)
  const hydratedRef = useRef(false)

  // CC_STEP3_FIX3_PROMPT.md: Project ID/Memo are editable the whole time the panel is
  // open — the input's value is always this local state, never `session.project_id`, so
  // typing is never overwritten by the ~1.5s session poll. The one exception is restoring
  // a session after a page reload (DatabaseScreen's mount effect): seed local state from
  // the session's last-known values exactly once when it first appears, then never again.
  useEffect(() => {
    if (!hydratedRef.current && session) {
      setProjectId(session.project_id)
      setMemo(session.memo)
      hydratedRef.current = true
    }
  }, [session])

  const sessionFiles = session?.files ?? []
  const erroredFile = sessionFiles.find((f) => f.status === 'error')

  async function ensureSession() {
    if (session) return session
    const trimmed = projectId.trim()
    if (!trimmed) {
      setError('Enter a Project ID before adding files.')
      return null
    }
    try {
      const started = await startUpload(trimmed, memo)
      onSessionChange(started)
      return started
    } catch (err) {
      if (err.status === 409) {
        onClose()
        return null
      }
      setError(err.message)
      return null
    }
  }

  async function handleFiles(fileList) {
    const files = Array.from(fileList || [])
    if (files.length === 0) return
    const active = await ensureSession()
    if (!active) return

    for (const file of files) {
      try {
        const updated = await addUploadFile(file)
        onSessionChange(updated)
      } catch (err) {
        if (err.status === 409) continue // duplicate filename or process already running — skip
        setError(err.message)
        return
      }
    }
  }

  function handleBrowseClick() {
    fileInputRef.current?.click()
  }

  function handleDrop(e) {
    e.preventDefault()
    setDragActive(false)
    handleFiles(e.dataTransfer.files)
  }

  async function dismissFileError() {
    if (session?.error) {
      // A pipeline crash (Phase B / Process) rather than one rejected file — nothing left
      // to salvage in this draft, so close it the same way the × button would.
      await discardUpload().catch(() => {})
      onClose()
      return
    }
    if (erroredFile) {
      const updated = await removeUploadFile(erroredFile.filename).catch(() => null)
      if (updated) onSessionChange(updated)
    }
    setError('')
  }

  async function handleRemove(filename) {
    const updated = await removeUploadFile(filename).catch(() => null)
    if (updated) onSessionChange(updated)
  }

  async function handleProcess() {
    // The allowlist check's point of final authority (CC_STEP3_FIX3_PROMPT.md): whatever is
    // in the fields at this instant is what gets validated and, if valid, saved with the
    // subject — not whatever project_id the backend session happened to start with.
    try {
      const updated = await processUpload(projectId.trim(), memo)
      onSessionChange(updated)
    } catch (err) {
      setError(err.message)
    }
  }

  async function discardAndClose() {
    if (session && !session.processing && !session.done) {
      await discardUpload().catch(() => {})
    }
    onClose()
  }

  function hasDraftContent() {
    // Decision 1 (CC_STEP3_FIX4_PROMPT.md): only confirm if there's actually something to
    // lose — a completely untouched panel should still close immediately.
    return Boolean(projectId.trim()) || Boolean(memo.trim()) || sessionFiles.length > 0
  }

  function handleCloseClick() {
    if (hasDraftContent()) {
      setConfirmDiscard(true)
      return
    }
    discardAndClose()
  }

  async function handleConfirmDiscard() {
    setConfirmDiscard(false)
    await discardAndClose()
  }

  async function handleFinish() {
    setFinishing(true)
    await onDone()
  }

  const takeoverMessage = error || erroredFile?.error || session?.error

  return (
    <div
      className={`absolute top-0 right-0 bottom-0 w-[420px] z-30 bg-surface border border-border shadow-panel flex-col ${
        hidden ? 'hidden' : 'flex'
      }`}
    >
      <div className="bg-brand text-white flex items-center justify-between px-5 py-3">
        <span className="text-lg font-medium">Create new study</span>
        <div className="flex items-center gap-3">
          <button type="button" onClick={onMinimize} aria-label="Minimize" className="text-xl leading-none px-1">
            &minus;
          </button>
          <button type="button" onClick={handleCloseClick} aria-label="Close" className="text-xl leading-none px-1">
            &times;
          </button>
        </div>
      </div>

      {takeoverMessage ? (
        <div className="flex-1 flex flex-col items-center justify-center px-8 py-10 bg-brand text-white text-center gap-6">
          <WarningTriangleIcon className="w-16 h-16" />
          <p className="text-base">{takeoverMessage}</p>
          <button
            type="button"
            onClick={dismissFileError}
            className="bg-white text-text rounded-control px-5 py-2.5 text-sm font-medium"
          >
            {session?.error ? 'Close' : erroredFile ? 'Upload Another File' : 'Back'}
          </button>
        </div>
      ) : session?.processing ? (
        <div className="flex-1 flex flex-col items-center justify-center px-8 py-10 gap-4">
          <SpinnerIcon className="w-14 h-14 text-brand animate-spin" />
          <p className="text-center text-text">
            Processing subject — combining files and detecting change points...
          </p>
        </div>
      ) : session?.done ? (
        <div className="flex-1 flex flex-col items-center justify-center px-8 py-10 gap-4">
          <CheckCircleFilledIcon className="w-14 h-14 text-brand" />
          <p className="text-lg font-medium">Upload Complete!</p>
          <button
            type="button"
            onClick={handleFinish}
            disabled={finishing}
            className="mt-2 bg-brand text-white rounded-control px-5 py-2.5 text-sm font-medium disabled:opacity-60"
          >
            {finishing ? 'Closing…' : 'Done'}
          </button>
        </div>
      ) : (
        <div className="flex-1 overflow-y-auto px-5 py-5">
          <label className="block text-sm font-medium text-text mb-1">Project ID</label>
          <input
            type="text"
            value={projectId}
            onChange={(e) => setProjectId(e.target.value)}
            placeholder="e.g. chb06"
            className="w-full border border-border rounded-control px-3 py-2 mb-4 text-sm"
          />

          <label className="block text-sm font-medium text-text mb-1">Memo</label>
          <textarea
            value={memo}
            onChange={(e) => setMemo(e.target.value)}
            rows={3}
            className="w-full border border-border rounded-control px-3 py-2 mb-4 text-sm resize-none"
          />

          <label className="block text-sm font-medium text-text mb-2">FILES</label>
          {sessionFiles.length > 0 && (
            <ul className="mb-3 divide-y divide-border border border-border rounded-control overflow-hidden">
              {sessionFiles.map((f) => (
                <li key={f.filename} className="flex items-center gap-2 px-3 py-2 text-sm">
                  <FileIcon className="w-4 h-4 text-text-secondary shrink-0" />
                  <span className="flex-1 truncate font-mono text-xs">{f.filename}</span>
                  {f.status === 'uploading' ? (
                    <button
                      type="button"
                      onClick={() => handleRemove(f.filename)}
                      aria-label={`Stop uploading ${f.filename}`}
                      className="text-brand"
                    >
                      <StopInCircleIcon className="w-5 h-5 animate-spin" />
                    </button>
                  ) : (
                    <button
                      type="button"
                      onClick={() => handleRemove(f.filename)}
                      aria-label={`Remove ${f.filename}`}
                      className="text-text"
                    >
                      <XIcon className="w-4 h-4" />
                    </button>
                  )}
                </li>
              ))}
            </ul>
          )}

          <input
            ref={fileInputRef}
            type="file"
            accept=".edf"
            multiple
            className="hidden"
            onChange={(e) => {
              handleFiles(e.target.files)
              e.target.value = ''
            }}
          />
          <div
            onClick={handleBrowseClick}
            onDragOver={(e) => {
              e.preventDefault()
              setDragActive(true)
            }}
            onDragLeave={() => setDragActive(false)}
            onDrop={handleDrop}
            className={`border-2 border-dashed rounded-control flex flex-col items-center justify-center gap-2 py-8 cursor-pointer text-text-muted ${
              dragActive ? 'border-brand bg-bg' : 'border-border-strong'
            }`}
          >
            <UploadCloudIcon className="w-10 h-10" />
            <span className="font-medium text-text">Browse Files</span>
          </div>

          <button
            type="button"
            onClick={handleProcess}
            disabled={!session?.ready_to_process}
            className="w-full mt-5 bg-text text-white rounded-control py-3 text-sm font-semibold disabled:opacity-40"
          >
            PROCESS
          </button>
          <p className="text-xs text-text-muted text-center mt-2">
            Click "PROCESS" once all files for the study have been uploaded
          </p>
        </div>
      )}

      {confirmDiscard && (
        <ConfirmDialog
          message="Discard this draft? Any uploaded files and progress will be lost."
          onConfirm={handleConfirmDiscard}
          onCancel={() => setConfirmDiscard(false)}
        />
      )}
    </div>
  )
}
