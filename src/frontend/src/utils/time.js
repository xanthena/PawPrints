export function formatDuration(seconds) {
  const total = Math.max(0, Math.round(seconds || 0))
  const minutes = Math.floor(total / 60)
  const secs = total % 60
  return `${minutes}:${String(secs).padStart(2, '0')}`
}
