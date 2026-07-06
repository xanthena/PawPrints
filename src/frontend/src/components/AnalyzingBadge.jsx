import YarnBallSpinner from './YarnBallSpinner.jsx'
import { formatDuration } from '../utils/time.js'
import './AnalyzingBadge.css'

export default function AnalyzingBadge({ processedSeconds = 0, durationSeconds = 0 }) {
  return (
    <span className="analyzing-badge">
      <YarnBallSpinner size={18} />
      <span className="analyzing-badge__text">
        Still analyzing… {formatDuration(processedSeconds)}
        {durationSeconds > 0 ? ` / ${formatDuration(durationSeconds)}` : ''}
      </span>
    </span>
  )
}
