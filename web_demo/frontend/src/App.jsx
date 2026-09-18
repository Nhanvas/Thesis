import { useEffect, useState } from 'react'
import LoginScreen from './screens/LoginScreen.jsx'
import DatabaseScreen from './screens/DatabaseScreen.jsx'
import AnalysisScreen from './screens/AnalysisScreen.jsx'
import { getSession, logout } from './api.js'

function App() {
  const [username, setUsername] = useState(null)
  const [checkingSession, setCheckingSession] = useState(true)
  // Analysis screen navigation (Step 4, SPEC §5.7 "Open"): no router in this app (see
  // DatabaseScreen's own precedent of plain useState screens) — { subjectId, fileId } or
  // null. Kept at this level (not inside DatabaseScreen) so leaving Analysis via its own
  // header/back action returns to a still-mounted Database screen.
  const [analysisTarget, setAnalysisTarget] = useState(null)

  useEffect(() => {
    getSession()
      .then(({ username }) => setUsername(username))
      .catch(() => setUsername(null))
      .finally(() => setCheckingSession(false))
  }, [])

  async function handleLoggedOut() {
    await logout().catch(() => {})
    setUsername(null)
    setAnalysisTarget(null)
  }

  if (checkingSession) return null

  if (!username) {
    return <LoginScreen onLoggedIn={setUsername} />
  }

  if (analysisTarget) {
    return (
      <AnalysisScreen
        username={username}
        onLoggedOut={handleLoggedOut}
        subjectId={analysisTarget.subjectId}
        initialFileId={analysisTarget.fileId}
        onBack={() => setAnalysisTarget(null)}
      />
    )
  }

  return (
    <DatabaseScreen
      username={username}
      onLoggedOut={handleLoggedOut}
      onOpen={(subjectId, fileId) => setAnalysisTarget({ subjectId, fileId })}
    />
  )
}

export default App
