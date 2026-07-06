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
        <circle cx="32" cy="32" r="26" fill="var(--paw-orange)" />
        <g stroke="var(--paw-orange-dark)" strokeWidth="2" fill="none" opacity="0.65">
          <path d="M8 24 Q32 10 56 24" />
          <path d="M7 34 Q32 50 57 34" />
          <path d="M11 14 Q32 32 11 50" />
          <path d="M53 14 Q32 32 53 50" />
          <path d="M6 32 Q32 22 58 32" />
        </g>
        <path
          className="yarn-spinner__tail"
          d="M50 20 Q62 26 58 38"
          stroke="var(--paw-orange-dark)"
          strokeWidth="2.5"
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
