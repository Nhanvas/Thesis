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

export const deleteSubject = (subjectId) =>
  request(`/api/subjects/${encodeURIComponent(subjectId)}`, { method: 'DELETE' })

// Create New panel — SZSCAN_SPEC_v5.md §5.5. There is only ever one session system-wide
// (the single-subject-in-flight constraint), so none of these take a session id.

async function uploadRequest(path, options = {}) {
  // Like request(), but for endpoints that return the toast text in `detail` on a non-2xx
  // response we want the CALLER to see verbatim (SPEC's exact rejection wording) rather than
  // a generic "Request failed (409)" fallback.
  const res = await fetch(path, { credentials: 'include', ...options })
  const body = res.status === 204 ? null : await res.json().catch(() => ({}))
  if (!res.ok) {
    const err = new Error(body?.detail || `Request failed (${res.status})`)
    err.status = res.status
    throw err
  }
  return body
}

export const startUpload = (projectId, memo) =>
  uploadRequest('/api/uploads/current', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ project_id: projectId, memo }),
  })

export const getUpload = () => uploadRequest('/api/uploads/current')

export const discardUpload = () => uploadRequest('/api/uploads/current', { method: 'DELETE' })

export const acknowledgeUpload = () =>
  uploadRequest('/api/uploads/current/acknowledge', { method: 'POST' })

export const addUploadFile = (file) => {
  const form = new FormData()
  form.append('file', file, file.name)
  return uploadRequest('/api/uploads/current/files', { method: 'POST', body: form })
}

export const removeUploadFile = (filename) =>
  uploadRequest(`/api/uploads/current/files/${encodeURIComponent(filename)}`, { method: 'DELETE' })

export const processUpload = (projectId, memo) =>
  uploadRequest('/api/uploads/current/process', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ project_id: projectId, memo }),
  })

// Analysis screen (Step 4, CC_STEP4_PROMPT.md) — Panel EEG + toolbar + scrub.

export const getSubjectDetail = (subjectId) =>
  request(`/api/subjects/${encodeURIComponent(subjectId)}`)

export const getFile = (fileId) => request(`/api/files/${fileId}`)

export const markFileViewing = (fileId) => request(`/api/files/${fileId}/viewing`, { method: 'POST' })

export const markFileViewed = (fileId) => request(`/api/files/${fileId}/viewed`, { method: 'POST' })

export const getWaveform = (fileId, startSec, endSec, widthPx) =>
  request(
    `/api/files/${fileId}/waveform?start_sec=${startSec}&end_sec=${endSec}&width_px=${Math.round(widthPx)}`
  )

// Mini-timeline + Panel Event (Step 5, CC_STEP5_PROMPT.md).

export const getTimeline = (fileId) => request(`/api/files/${fileId}/timeline`)

export const getFileEvents = (fileId) => request(`/api/files/${fileId}/events`)

export const updateEvent = (eventId, payload) =>
  request(`/api/events/${eventId}`, { method: 'PATCH', body: JSON.stringify(payload) })

export const deleteEvent = (eventId) => request(`/api/events/${eventId}`, { method: 'DELETE' })

// Select Range (Step 6, CC_STEP6_PROMPT.md §6.6).

export const createEvent = (fileId, onsetSec, offsetSec) =>
  request(`/api/files/${fileId}/events`, {
    method: 'POST',
    body: JSON.stringify({ onset_sec: onsetSec, offset_sec: offsetSec }),
  })

// Channel Attribution Panel (Step 7, CC_STEP7_PROMPT.md §2.2).

export const getAttribution = (eventId) => request(`/api/events/${eventId}/attribution`)

export const saveAttributionStatus = (eventId, statuses) =>
  request(`/api/events/${eventId}/attribution-status`, {
    method: 'PUT',
    body: JSON.stringify({ statuses }),
  })

// Export (Step 8, CC_STEP8_PROMPT.md) — triggers a real browser download rather than
// returning JSON, so this bypasses request()'s res.json() parsing.
export async function exportSubjectTxt(subjectId) {
  const res = await fetch(`/api/subjects/${encodeURIComponent(subjectId)}/export`, {
    credentials: 'include',
  })
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail || `Request failed (${res.status})`)
  }
  const blob = await res.blob()
  const disposition = res.headers.get('Content-Disposition') || ''
  const match = disposition.match(/filename="?([^"]+)"?/)
  const filename = match ? match[1] : `${subjectId}-summary.txt`
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(url)
}
