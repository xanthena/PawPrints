import PawIcon from './PawIcon.jsx'
import './FootageCard.css'

const HUES = [22, 30, 15, 38]

export default function FootageCard({ footage }) {
  const hue = HUES[footage.id % HUES.length]

  return (
    <button className="footage-card">
      <div className="footage-card__thumb" style={{ '--hue': hue }}>
        <PawIcon size={32} color="rgba(255, 255, 255, 0.85)" />
      </div>
    </button>
  )
}
