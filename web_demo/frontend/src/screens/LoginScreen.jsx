import { useState } from 'react'
import { LogoIcon } from '../components/icons.jsx'
import { login } from '../api.js'

// Log in screen, per UI/A0c. Pre-app screen: no header chrome, no footer disclaimer
// (SZSCAN_SPEC_v5.md §4, §0). No registration, no forgot/change password.
export default function LoginScreen({ onLoggedIn }) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setSubmitting(true)
    try {
      const { username: loggedInUser } = await login(username, password)
      onLoggedIn(loggedInUser)
    } catch (err) {
      setError(err.message || 'Invalid username or password.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div
      className="min-h-screen flex flex-col items-center justify-center px-4"
      style={{ background: 'linear-gradient(115deg, #624C8A 0%, #10182B 100%)' }}
    >
      <div className="flex items-center gap-3 text-white mb-8">
        <LogoIcon className="w-10 h-10" />
        <span className="text-3xl font-semibold">SzScan</span>
      </div>

      <form
        onSubmit={handleSubmit}
        className="w-full max-w-sm bg-surface rounded-panel shadow-panel p-8"
      >
        <h1 className="text-2xl font-semibold text-brand mb-6">Log in</h1>

        <label className="block text-sm text-text mb-1" htmlFor="username">
          User name
        </label>
        <input
          id="username"
          type="text"
          autoComplete="username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          className="w-full border border-border rounded-control px-3 py-2 mb-4 text-sm"
          required
        />

        <label className="block text-sm text-text mb-1" htmlFor="password">
          Password:
        </label>
        <input
          id="password"
          type="password"
          autoComplete="current-password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="w-full border border-border rounded-control px-3 py-2 mb-2 text-sm"
          required
        />

        {error && <p className="text-reject text-sm mb-2">{error}</p>}

        <button
          type="submit"
          disabled={submitting}
          className="w-full bg-brand text-white rounded-control py-2.5 mt-4 font-medium disabled:opacity-60"
        >
          {submitting ? 'Logging in…' : 'Log in'}
        </button>
      </form>
    </div>
  )
}
