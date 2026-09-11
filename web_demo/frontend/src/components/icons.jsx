// Small inline icons. Recreated by hand from the UI/ mockups' visual style — not extracted
// from the locked PNGs (CLAUDE.md: UI/ is read/view-only, never a source of copied assets).

export function LogoIcon({ className = '' }) {
  return (
    <svg viewBox="0 0 32 32" fill="none" className={className} aria-hidden="true">
      <path
        d="M11 27v-4.2c-2.4-1.6-4-4.4-4-7.6 0-5 4-9 9-9s9 4 9 9c0 1.9-.6 3.6-1.6 5.1-.8 1.2-1.4 1.8-1.4 3.1V27"
        stroke="currentColor"
        strokeWidth="1.4"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path d="M13 27h6" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" />
      <path d="M13 23.5h6" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" />
      <path
        d="M16.8 9.5 14 15h2.4l-1 4.5 4.6-6.2h-2.6z"
        fill="currentColor"
        stroke="currentColor"
        strokeWidth="0.6"
        strokeLinejoin="round"
      />
    </svg>
  )
}

export function PersonIcon({ className = '' }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" className={className} aria-hidden="true">
      <circle cx="12" cy="8.5" r="3.5" fill="currentColor" />
      <path d="M4.5 20c0-4.1 3.4-7 7.5-7s7.5 2.9 7.5 7" fill="currentColor" />
    </svg>
  )
}

export function SearchIcon({ className = '' }) {
  return (
    <svg viewBox="0 0 20 20" fill="none" className={className} aria-hidden="true">
      <circle cx="9" cy="9" r="6" stroke="currentColor" strokeWidth="1.6" />
      <path d="m17 17-3.5-3.5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
    </svg>
  )
}

export function LogoutIcon({ className = '' }) {
  return (
    <svg viewBox="0 0 20 20" fill="none" className={className} aria-hidden="true">
      <path
        d="M8 3H4.5a1 1 0 0 0-1 1v12a1 1 0 0 0 1 1H8"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path d="M12.5 13.5 16 10l-3.5-3.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M16 10H7.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  )
}
