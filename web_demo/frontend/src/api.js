// Thin fetch wrapper for the backend's session-cookie auth (see backend/main.py).
// `credentials: 'include'` is required so the browser sends/stores the HttpOnly session
// cookie even though Vite's dev proxy makes requests look same-origin.

async function request(path, options = {}) {
  const res = await fetch(path, {
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail || `Request failed (${res.status})`)
  }
  return res.status === 204 ? null : res.json()
}

export const login = (username, password) =>
  request('/api/login', { method: 'POST', body: JSON.stringify({ username, password }) })

export const logout = () => request('/api/logout', { method: 'POST' })

export const getSession = () => request('/api/session')

export const listSubjects = () => request('/api/subjects')
