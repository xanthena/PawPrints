const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export async function postQuery(question, { startDate, endDate, includeProof } = {}) {
  const response = await fetch(`${API_BASE}/api/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      question,
      start_date: startDate || null,
      end_date: endDate || null,
      include_proof: Boolean(includeProof),
    }),
  })
  const data = await response.json().catch(() => ({}))
  if (!response.ok) throw new Error(data.detail || `Query failed: ${response.status}`)
  return data
}

export function proofVideoUrl(path) {
  if (!path) return null
  return `${API_BASE}${path}`
}
