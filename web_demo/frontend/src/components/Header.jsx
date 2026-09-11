import { useEffect, useRef, useState } from 'react'
import { LogoIcon, LogoutIcon, PersonIcon } from './icons.jsx'

// Header chrome + avatar/logout dropdown, per UI/A0b. Used on every screen after Log in.
export default function Header({ username, onLogout }) {
  const [open, setOpen] = useState(false)
  const rootRef = useRef(null)

  useEffect(() => {
    function onClickOutside(e) {
      if (rootRef.current && !rootRef.current.contains(e.target)) setOpen(false)
    }
    document.addEventListener('mousedown', onClickOutside)
    return () => document.removeEventListener('mousedown', onClickOutside)
  }, [])

  return (
    <header className="bg-header-gradient text-white px-6 py-3 flex items-center justify-between">
      <div className="flex items-center gap-2">
        <LogoIcon className="w-8 h-8" />
        <span className="text-xl font-semibold">SzScan</span>
      </div>

      <div className="relative" ref={rootRef}>
        <button
          type="button"
          onClick={() => setOpen((v) => !v)}
          className="w-10 h-10 rounded-full bg-brand flex items-center justify-center"
          aria-label="Account menu"
        >
          <PersonIcon className="w-6 h-6 text-white" />
        </button>

        {open && (
          <div className="absolute right-0 mt-2 w-56 bg-surface rounded-panel shadow-panel overflow-hidden border border-border">
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
