import { useEffect, useRef, useState } from 'react'
import { LogoutIcon, PersonIcon } from './icons.jsx'
import logo from '../assets/logo.png'

// Header chrome + avatar/logout dropdown, per UI/A0b. Used on every screen after Log in.
// `center` (Step 4, UI/B1a): the Analysis screen's header controls (subject/file title,
// Previous/Next, Viewed/Export, file dropdown) render in the same navy bar as the
// logo/avatar rather than a second header row — DatabaseScreen passes nothing here.
export default function Header({ username, onLogout, center, onLogoClick }) {
  const [open, setOpen] = useState(false)
  const rootRef = useRef(null)

  useEffect(() => {
    function onClickOutside(e) {
      if (rootRef.current && !rootRef.current.contains(e.target)) setOpen(false)
    }
    document.addEventListener('mousedown', onClickOutside)
    return () => document.removeEventListener('mousedown', onClickOutside)
  }, [])

  const logoContent = (
    <>
      <img src={logo} alt="SzScan" className="h-16 w-auto" />
      <span className="text-5xl font-semibold">SzScan</span>
    </>
  )

  return (
    <header className="bg-header-gradient text-white px-6 py-5 flex items-center justify-between gap-4">
      {/* Not in any mockup — a pragmatic "back to Database" affordance for the Analysis
          screen (SPEC/UI have no explicit back control there). Flagged in CC_STEP4_REPORT.md
          for Boti to confirm or replace. */}
      {onLogoClick ? (
        <button type="button" onClick={onLogoClick} className="flex items-center gap-4 shrink-0" aria-label="Back to Database">
          {logoContent}
        </button>
      ) : (
        <div className="flex items-center gap-4 shrink-0">{logoContent}</div>
      )}

      {center && <div className="flex items-center gap-3 flex-1 min-w-0">{center}</div>}

      <div className="relative shrink-0" ref={rootRef}>
        <button
          type="button"
          onClick={() => setOpen((v) => !v)}
          className="w-16 h-16 rounded-full bg-brand flex items-center justify-center"
          aria-label="Account menu"
        >
          <PersonIcon className="w-10 h-10 text-white" />
        </button>

        {open && (
          <div className="absolute right-0 mt-2 w-56 z-50 bg-surface rounded-panel shadow-panel overflow-hidden border border-border">
            <div className="bg-brand text-white text-center font-semibold py-3">
              {username}
            </div>
            <button
              type="button"
              onClick={onLogout}
              className="w-full flex items-center gap-2 px-4 py-3 text-text hover:bg-bg text-sm"
            >
              <LogoutIcon className="w-5 h-5" />
              Log out
            </button>
          </div>
        )}
      </div>
    </header>
  )
}
