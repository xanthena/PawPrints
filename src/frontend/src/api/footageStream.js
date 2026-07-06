const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

// Turns a relative path the backend returns (e.g. "/media/frames/x.jpg")
// into an absolute URL the browser can actually load, since the API
// runs on a different origin/port than the Vite dev server.
export function mediaUrl(path) {
  if (!path) return null
  return `${API_BASE}${path}`
}

/**
 * Uploads a video and streams back pipeline progress as it happens.
 *
 * The backend's response body is NDJSON (one JSON object per line) sent
 * as the pipeline works through the video -- not a single response
 * that arrives once everything is done. `onEvent` is called once per
 * line, in order, as each one arrives.
 */
export async function streamFootageAnalysis(file, { onEvent, signal } = {}) {
  const formData = new FormData()
  formData.append('file', file)

  const response = await fetch(`${API_BASE}/api/footage/analyze`, {
    method: 'POST',
    body: formData,
    signal,
  })

  if (!response.ok || !response.body) {
    throw new Error(`Upload failed: ${response.status} ${response.statusText}`)
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { value, done } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })

    let newlineIndex
    while ((newlineIndex = buffer.indexOf('\n')) >= 0) {
      const line = buffer.slice(0, newlineIndex).trim()
      buffer = buffer.slice(newlineIndex + 1)
      if (line) onEvent?.(JSON.parse(line))
    }
  }

  const trailing = buffer.trim()
  if (trailing) onEvent?.(JSON.parse(trailing))
}
