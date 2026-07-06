import PawIcon from './PawIcon.jsx'
import CatCaptureAnimation from './CatCaptureAnimation.jsx'
import PawStamp from './PawStamp.jsx'
import './SplashScreen.css'

// Kept well outside the title's own footprint (roughly the center 40%
// of the screen, both axes) so the trail never collides with the
// cat-capture animation, the title text, or the paw-stamp between the
// two words.
const PAW_STEPS = [
  { left: '10%', top: '78%', rotate: -18 },
  { left: '20%', top: '88%', rotate: -8 },
  { left: '82%', top: '14%', rotate: -18 },
  { left: '90%', top: '24%', rotate: -8 },
  { left: '12%', top: '16%', rotate: -18 },
  { left: '86%', top: '82%', rotate: -8 },
]

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
              animationDelay: `${i * 0.28}s`,
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
