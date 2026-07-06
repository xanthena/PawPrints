export default function CatFaceIcon({ size = 24, color = 'currentColor', className = '' }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 64 64"
      fill={color}
      className={className}
      xmlns="http://www.w3.org/2000/svg"
    >
      <path d="M14 8 L24 26 L14 26 Z" />
      <path d="M50 8 L40 26 L50 26 Z" />
      <circle cx="32" cy="36" r="22" />
      <circle cx="24" cy="33" r="3" fill="var(--cream)" />
      <circle cx="40" cy="33" r="3" fill="var(--cream)" />
      <path
        d="M32 39 L29 43 L35 43 Z M32 39 L26 39 M32 39 L38 39"
        fill="var(--cream)"
        stroke="var(--cream)"
        strokeWidth="1.5"
        strokeLinecap="round"
      />
      <g stroke={color} strokeWidth="1.6" strokeLinecap="round">
        <path d="M6 40 L20 42 M6 48 L20 44" />
        <path d="M58 40 L44 42 M58 48 L44 44" />
      </g>
    </svg>
  )
}
