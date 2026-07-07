import YarnBallSpinner from './YarnBallSpinner.jsx'
import './ProcessingModal.css'

export default function ProcessingModal({ filename }) {
  return (
    <div className="modal-backdrop">
      <div className="modal processing-modal">
        <YarnBallSpinner size={96} />
        <h2 className="processing-modal__title">Analyzing {filename}</h2>
        <p className="processing-modal__status">Initializing…</p>
        <div className="processing-modal__bar">
          <div className="processing-modal__bar-fill" />
        </div>
        <p className="processing-modal__subtext">
          Motion detection is scanning the footage frame by frame; each moment
          it catches gets sent straight to the vision model as it happens.
        </p>
      </div>
    </div>
  )
}
