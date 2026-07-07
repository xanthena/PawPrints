import PawIcon from './PawIcon.jsx'
import CatCaptureAnimation from './CatCaptureAnimation.jsx'
import PawStamp from './PawStamp.jsx'
import './SplashScreen.css'

// A real spiral: each paw is turned by the golden angle (~137.5°) from
// the previous one -- the same angle sunflower seed heads and pinecones
// use, because no ring of points ever lines up into straight spokes, so
// it reads as one continuous spiral rather than a fixed number of arms.
//
// Radius grows with the *square root* of the index (the actual formula
// behind that seed-head packing, not a linear step) so density stays
// even from the center out to the edges -- a linear radius step spaces
// rings further apart than the ring's own growing circumference, which
// thins out toward the outside. START_RADIUS is a flat floor added on
// top, which is what actually guarantees every paw clears the title
// (the cat-capture icon + "paw prints" text, stacked in the center) --
// sqrt(i) alone doesn't skip small values near i=0.
//
// COUNT/START_RADIUS/SPREAD_FACTOR were picked together, not
// independently: the max radius they produce (START_RADIUS +
// SPREAD_FACTOR * sqrt(COUNT - 1)) is kept a bit short of reaching the
// screen edges on its own, on purpose -- clamping stray points to the
// edge is what caused the last version's overlap (many different
// spiral points landing beyond the visible area all got pinned to the
// same clamped coordinate, stacking on top of each other). No clamping
// happens here at all; every point's real, computed position already
// lands on-screen. If either constant changes, re-verify with the
// min-pairwise-pixel-distance check described in this file's PR/commit
// before assuming it still looks non-overlapping.
const PAW_COUNT = 36
const CENTER_X = 50
const CENTER_Y = 50
const START_RADIUS = 17
const SPREAD_FACTOR = 5.3
const GOLDEN_ANGLE = 137.508 * (Math.PI / 180)

const PAW_STEPS = Array.from({ length: PAW_COUNT }, (_, i) => {
  const angle = i * GOLDEN_ANGLE
  const radius = START_RADIUS + SPREAD_FACTOR * Math.sqrt(i)
  return {
    left: `${CENTER_X + radius * Math.cos(angle)}%`,
    top: `${CENTER_Y + radius * Math.sin(angle)}%`,
    rotate: Math.round((angle * 180) / Math.PI) % 360,
  }
})

export default function SplashScreen({ fadingOut = false }) {
  return (
    <div className={`splash ${fadingOut ? 'splash--fade-out' : ''}`}>
      <div className="splash__trail">
        {PAW_STEPS.map((step, i) => (
          <PawIcon
            key={i}
            size={40}
            color="var(--paw-orange)"
            className="splash__paw"
            style={{
              left: step.left,
              top: step.top,
              transform: `rotate(${step.rotate}deg)`,
              animationDelay: `${i * 0.045}s`,
            }}
          />
        ))}
      </div>
      <div className="splash__title">
        <CatCaptureAnimation size={88} />
        <h1 className="brand-title">
          <span>paw</span>
          <PawStamp />
          <span>prints</span>
        </h1>
      </div>
    </div>
  )
}
