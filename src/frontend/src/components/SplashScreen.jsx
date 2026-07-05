import PawIcon from './PawIcon.jsx'
import './SplashScreen.css'

const PAW_STEPS = [
  { left: '18%', top: '62%', rotate: -18 },
  { left: '30%', top: '46%', rotate: -8 },
  { left: '43%', top: '58%', rotate: -18 },
  { left: '56%', top: '42%', rotate: -8 },
  { left: '69%', top: '54%', rotate: -18 },
  { left: '82%', top: '38%', rotate: -8 },
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
        <PawIcon size={44} color="var(--paw-orange)" />
        <h1>PawPrints</h1>
      </div>
    </div>
  )
}
