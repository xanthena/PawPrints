import YarnBallSpinner from './YarnBallSpinner.jsx'
import { formatDuration } from '../utils/time.js'
import './ProcessingModal.css'

export default function ProcessingModal({ filename, processedSeconds = 0, durationSeconds = 0 }) {
  const pct = durationSeconds > 0 ? Math.min(100, (processedSeconds / durationSeconds) * 100) : 0

  return (
    <div className="modal-backdrop">
      <div className="modal processing-modal">
        <YarnBallSpinner size={96} />
        <h2 className="processing-modal__title">Analyzing {filename}</h2>
        <p className="processing-modal__subtext">
          Motion detection is scanning the footage frame by frame -- every
          moment it catches gets sent straight to the vision model as it
          happens.
        </p>
        <div className="processing-modal__bar">
          <div className="processing-modal__bar-fill" style={{ width: `${pct}%` }} />
        </div>
        <span className="processing-modal__time">
          {formatDuration(processedSeconds)} / {formatDuration(durationSeconds)}
        </span>
      </div>
    </div>
  )
}
