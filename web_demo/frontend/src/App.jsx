import { useEffect, useState } from 'react'
import LoginScreen from './screens/LoginScreen.jsx'
import DatabaseScreen from './screens/DatabaseScreen.jsx'
import { getSession, logout } from './api.js'

function App() {
  const [username, setUsername] = useState(null)
  const [checkingSession, setCheckingSession] = useState(true)

  useEffect(() => {
    getSession()
      .then(({ username }) => setUsername(username))
      .catch(() => setUsername(null))
      .finally(() => setCheckingSession(false))
  }, [])

  async function handleLoggedOut() {
    await logout().catch(() => {})
    setUsername(null)
  }

  if (checkingSession) return null

  if (!username) {
    return <LoginScreen onLoggedIn={setUsername} />
  }

  return <DatabaseScreen username={username} onLoggedOut={handleLoggedOut} />
}

export default App
