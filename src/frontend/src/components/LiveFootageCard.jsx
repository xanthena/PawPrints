import PawIcon from './PawIcon.jsx'
import AnalyzingBadge from './AnalyzingBadge.jsx'
import './LiveFootageCard.css'

export default function LiveFootageCard({ footage, onClick }) {
  const {
    filename,
    status,
    thumbnailUrl,
    processedSeconds,
    durationSeconds,
    reelUrl,
    reelNote,
    errorMessage,
  } = footage

  return (
    <button className="live-footage-card" onClick={onClick}>
      <div className="live-footage-card__thumb">
        {thumbnailUrl ? (
          <img src={thumbnailUrl} alt="" />
        ) : (
          <div className="live-footage-card__thumb-placeholder">
            <PawIcon size={32} color="rgba(255, 255, 255, 0.85)" />
          </div>
        )}
        {status === 'starting' || status === 'analyzing' ? (
          <div className="live-footage-card__badge">
            <AnalyzingBadge processedSeconds={processedSeconds} durationSeconds={durationSeconds} />
          </div>
        ) : null}
      </div>

      <div className="live-footage-card__label">
        <span className="live-footage-card__name">{filename}</span>

        {status === 'done' && reelUrl && (
          <span className="live-footage-card__link">Watch highlight reel</span>
        )}
        {status === 'done' && !reelUrl && (
          <span className="live-footage-card__note">{reelNote || 'No highlight-worthy moments found.'}</span>
        )}
        {status === 'error' && (
          <span className="live-footage-card__error">{errorMessage || 'Something went wrong.'}</span>
        )}
      </div>
    </button>
  )
}
