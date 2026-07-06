function ordinal(day) {
  const remainder = day % 100
  if (remainder >= 11 && remainder <= 13) return `${day}th`
  switch (day % 10) {
    case 1:
      return `${day}st`
    case 2:
      return `${day}nd`
    case 3:
      return `${day}rd`
    default:
      return `${day}th`
  }
}

// "2026-07-06" -> "6th July, 2026 - Monday"
export function formatDayHeading(dateStr) {
  const date = new Date(`${dateStr}T00:00:00`)
  const month = date.toLocaleDateString('en-US', { month: 'long' })
  const weekday = date.toLocaleDateString('en-US', { weekday: 'long' })
  return `${ordinal(date.getDate())} ${month}, ${date.getFullYear()} - ${weekday}`
}

// Local calendar date (not UTC, so it doesn't drift a day near midnight).
export function todayDateString() {
  const now = new Date()
  const month = String(now.getMonth() + 1).padStart(2, '0')
  const day = String(now.getDate()).padStart(2, '0')
  return `${now.getFullYear()}-${month}-${day}`
}
