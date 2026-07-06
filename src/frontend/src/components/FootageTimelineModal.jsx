import { useRef } from 'react'
import YarnBallSpinner from './YarnBallSpinner.jsx'
import { formatDuration } from '../utils/time.js'
import './FootageTimelineModal.css'

export default function FootageTimelineModal({ footage, onClose }) {
  const videoRef = useRef(null)
  const { filename, videoUrl, timeline, status, processedSeconds, durationSeconds, reelUrl, reelNote } = footage
  const isAnalyzing = status === 'starting' || status === 'analyzing'

  function seekTo(seconds) {
    const video = videoRef.current
    if (!video) return
    video.currentTime = seconds
    video.play()
  }

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal timeline-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal__header">
          <h2>{filename}</h2>
          <button className="modal__close" onClick={onClose} aria-label="Close">
            &times;
          </button>
        </div>

        <div className="timeline-modal__body">
          <video ref={videoRef} src={videoUrl} controls className="timeline-modal__video" />

          <div className="timeline-modal__panel">
            <h3 className="timeline-modal__panel-title">Detected activity</h3>
            <ul className="timeline-modal__list">
              {timeline.length === 0 && (
                <li className="timeline-modal__empty">Nothing detected yet.</li>
              )}
              {timeline.map((event) => (
                <li key={event.event_id} className="timeline-modal__item">
                  <button
                    className="timeline-modal__timestamp"
                    onClick={() => seekTo(event.start_time)}
                  >
                    {formatDuration(event.start_time)}
                  </button>
                  <span className="timeline-modal__activity">
                    {(event.activities || []).join(', ')}
                  </span>
                </li>
              ))}
            </ul>

            {isAnalyzing && (
              <div className="timeline-modal__analyzing">
                <YarnBallSpinner size={20} />
                <span>
                  Still analyzing… {formatDuration(processedSeconds)} / {formatDuration(durationSeconds)}
                </span>
              </div>
            )}

            {status === 'done' && reelUrl && (
              <a className="timeline-modal__reel-link" href={reelUrl} target="_blank" rel="noreferrer">
                Watch highlight reel
              </a>
            )}
            {status === 'done' && !reelUrl && (
              <span className="timeline-modal__reel-note">
                {reelNote || 'No highlight-worthy moments found.'}
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
