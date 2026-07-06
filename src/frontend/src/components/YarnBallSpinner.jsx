import './YarnBallSpinner.css'

export default function YarnBallSpinner({ size = 64 }) {
  return (
    <span className="yarn-spinner" style={{ width: size, height: size }}>
      <svg
        className="yarn-spinner__ball"
        width={size}
        height={size}
        viewBox="0 0 64 64"
        xmlns="http://www.w3.org/2000/svg"
      >
        <defs>
          <clipPath id="yarn-spinner-clip">
            <circle cx="30" cy="28" r="24" />
          </clipPath>
        </defs>
        <circle cx="30" cy="28" r="24" fill="var(--paw-orange)" />
        {/* nested, parallel-ish arcs all curving the same general way --
            like a single strand wound around the ball repeatedly from
            one consistent angle, the classic flat "yarn ball" icon look
            (crossing bands in every direction read as a beach ball) */}
        <g
          clipPath="url(#yarn-spinner-clip)"
          stroke="var(--paw-orange-dark)"
          strokeWidth="4.5"
          strokeLinecap="round"
          fill="none"
        >
          <path d="M8 16 Q34 4 54 22" />
          <path d="M6 26 Q32 10 56 30" />
          <path d="M6 36 Q32 18 56 40" />
          <path d="M9 46 Q34 28 54 50" />
          <path d="M16 54 Q38 38 50 56" />
        </g>
        {/* a second family of nested strands crossing the first at a
            different angle, drawn on top so they read as wrapping *over*
            them -- one family alone looks like tidy stripes, two crossing
            families is what actually reads as a wound ball of yarn */}
        <g
          clipPath="url(#yarn-spinner-clip)"
          stroke="var(--paw-orange-dark)"
          strokeWidth="4.5"
          strokeLinecap="round"
          fill="none"
        >
          <path d="M34 2 Q6 26 30 56" />
          <path d="M42 3 Q12 28 40 55" />
          <path d="M50 8 Q22 30 48 54" />
        </g>
        <path
          className="yarn-spinner__tail"
          d="M50 46 Q62 50 55 58 Q50 64 58 63"
          stroke="var(--paw-orange-dark)"
          strokeWidth="3"
          strokeLinecap="round"
          fill="none"
        />
      </svg>
      <svg
        className="yarn-spinner__paw"
        width={size * 0.5}
        height={size * 0.5}
        viewBox="0 0 64 64"
        fill="var(--brown-soft)"
        xmlns="http://www.w3.org/2000/svg"
      >
        <ellipse cx="32" cy="42" rx="16" ry="13" />
        <ellipse cx="13" cy="26" rx="7" ry="9" transform="rotate(-20 13 26)" />
        <ellipse cx="29" cy="15" rx="7.5" ry="9.5" transform="rotate(-5 29 15)" />
        <ellipse cx="46" cy="16" rx="7.5" ry="9.5" transform="rotate(10 46 16)" />
        <ellipse cx="55" cy="30" rx="7" ry="9" transform="rotate(25 55 30)" />
      </svg>
    </span>
  )
}
