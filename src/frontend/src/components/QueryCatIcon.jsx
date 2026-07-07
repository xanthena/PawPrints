export default function QueryCatIcon({ size = 40, className = '' }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 64 64"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
    >
      {/* headphone band */}
      <path
        d="M14 26 Q32 4 50 26"
        stroke="var(--brown-deep)"
        strokeWidth="4"
        fill="none"
        strokeLinecap="round"
      />
      {/* ear cups */}
      <rect x="6" y="24" width="11" height="17" rx="5.5" fill="var(--brown-deep)" />
      <rect x="47" y="24" width="11" height="17" rx="5.5" fill="var(--brown-deep)" />

      {/* cat ears, poking up between the headphone band and the cups */}
      <path d="M19 21 L14 8 L27 18 Z" fill="var(--paw-orange)" />
      <path d="M45 21 L50 8 L37 18 Z" fill="var(--paw-orange)" />

      {/* face */}
      <circle cx="32" cy="38" r="20" fill="var(--paw-orange)" />

      {/* eyes */}
      <circle cx="25" cy="36" r="2.6" fill="var(--brown-deep)" />
      <circle cx="39" cy="36" r="2.6" fill="var(--brown-deep)" />

      {/* nose + mouth */}
      <path d="M32 41 L29.5 44.5 L34.5 44.5 Z" fill="var(--brown-deep)" />
      <path
        d="M32 44.5 Q32 47 29 47.5 M32 44.5 Q32 47 35 47.5"
        stroke="var(--brown-deep)"
        strokeWidth="1.3"
        fill="none"
        strokeLinecap="round"
      />

      {/* whiskers */}
      <g stroke="var(--brown-deep)" strokeWidth="1.1" strokeLinecap="round" opacity="0.6">
        <path d="M14 38 L22 39 M14 43 L22 41" />
        <path d="M50 38 L42 39 M50 43 L42 41" />
      </g>
    </svg>
  )
}
