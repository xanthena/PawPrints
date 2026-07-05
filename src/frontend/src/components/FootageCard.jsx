import PawIcon from './PawIcon.jsx'
import './FootageCard.css'

const HUES = [22, 30, 15, 38]

function formatDate(dateStr) {
  const date = new Date(`${dateStr}T00:00:00`)
  const day = date.toLocaleDateString('en-US', { weekday: 'long' })
  const rest = date.toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })
  return { day, rest }
}

export default function FootageCard({ footage }) {
  const { day, rest } = formatDate(footage.date)
  const hue = HUES[footage.id % HUES.length]

  return (
    <button className="footage-card">
      <div className="footage-card__thumb" style={{ '--hue': hue }}>
        <PawIcon size={32} color="rgba(255, 255, 255, 0.85)" />
      </div>
      <div className="footage-card__label">
        <span className="footage-card__day">{day}</span>
        <span className="footage-card__date">{rest}</span>
      </div>
    </button>
  )
}
