import { useEffect, useState } from 'react'
import './PawWatermark.css'

// One toe per claw, described in the same local coordinates as
// PawIcon's toe ellipses so the claw sits exactly at each toe's tip and
// shares its rotation -- keeps this visually the same paw, just with
// claws that can extend and retract.
const CLAWS = [
  { rotate: -20, cx: 13, cy: 26, ry: 9 },
  { rotate: -5, cx: 29, cy: 15, ry: 9.5 },
  { rotate: 10, cx: 46, cy: 16, ry: 9.5 },
  { rotate: 25, cx: 55, cy: 30, ry: 9 },
]

function clawPath({ cx, cy, ry }) {
  const base = cy - ry
  const tip = base - 7
  return `M ${cx - 2.2} ${base} L ${cx + 2.2} ${base} L ${cx} ${tip} Z`
}

// A faint, oversized paw print that sits behind the dashboard content as
// ambient decoration. Every so often it flexes -- claws slide out for a
// moment, then retract -- instead of just sitting there static.
export default function PawWatermark({ size = 320, className = '' }) {
  const [clawsOut, setClawsOut] = useState(false)

  useEffect(() => {
    let showTimer
    let hideTimer

    function scheduleFlex() {
      const delay = 14000 + Math.random() * 16000 // roughly every 14-30s
      showTimer = setTimeout(() => {
        setClawsOut(true)
        hideTimer = setTimeout(() => {
          setClawsOut(false)
          scheduleFlex()
        }, 900)
      }, delay)
    }

    scheduleFlex()
    return () => {
      clearTimeout(showTimer)
      clearTimeout(hideTimer)
    }
  }, [])

  return (
    <svg
      width={size}
      height={size}
      viewBox="-12 -12 88 88"
      className={`paw-watermark ${className}`}
      aria-hidden="true"
      xmlns="http://www.w3.org/2000/svg"
    >
      <g fill="var(--paw-orange)" className="paw-watermark__pad">
        <ellipse cx="32" cy="42" rx="16" ry="13" />
        <ellipse cx="13" cy="26" rx="7" ry="9" transform="rotate(-20 13 26)" />
        <ellipse cx="29" cy="15" rx="7.5" ry="9.5" transform="rotate(-5 29 15)" />
        <ellipse cx="46" cy="16" rx="7.5" ry="9.5" transform="rotate(10 46 16)" />
        <ellipse cx="55" cy="30" rx="7" ry="9" transform="rotate(25 55 30)" />
      </g>
      {CLAWS.map((claw, i) => (
        <g key={i} transform={`rotate(${claw.rotate} ${claw.cx} ${claw.cy})`}>
          <path
            className={`paw-watermark__claw${clawsOut ? ' paw-watermark__claw--out' : ''}`}
            d={clawPath(claw)}
            fill="var(--paw-orange)"
          />
        </g>
      ))}
    </svg>
  )
}
