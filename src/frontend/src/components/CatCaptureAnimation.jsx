import './CatCaptureAnimation.css'

export default function CatCaptureAnimation({ size = 96 }) {
  return (
    <svg
      className="cat-capture"
      width={size}
      height={size}
      viewBox="0 0 120 96"
      xmlns="http://www.w3.org/2000/svg"
    >
      {/* viewfinder corners */}
      <g stroke="var(--paw-orange)" strokeWidth="3" strokeLinecap="round" fill="none">
        <path d="M6 22 V8 H20" />
        <path d="M100 8 H114 V22" />
        <path d="M114 74 V88 H100" />
        <path d="M20 88 H6 V74" />
      </g>

      {/* cat silhouette being captured -- nudged to sit centered in the
          viewfinder frame (box center is 60,48; the tail's extra mass on
          the right pulls the visual center further right than the raw
          shape bounds do, hence the larger horizontal correction) */}
      <g className="cat-capture__cat" fill="var(--brown-deep)" transform="translate(-4, 6)">
        <ellipse cx="60" cy="58" rx="22" ry="16" />
        <circle cx="60" cy="34" r="14" />
        <polygon points="47,26 41,10 55,22" />
        <polygon points="73,26 79,10 65,22" />
        <circle cx="55" cy="33" r="1.6" fill="var(--cream)" />
        <circle cx="65" cy="33" r="1.6" fill="var(--cream)" />
        <path
          d="M42 40 Q34 38 28 41 M42 43 Q33 43 27 46 M78 40 Q86 38 92 41 M78 43 Q87 43 93 46"
          stroke="var(--brown-deep)"
          strokeWidth="1.2"
          fill="none"
        />
        <path
          className="cat-capture__tail"
          d="M80 66 Q100 66 98 46"
          stroke="var(--brown-deep)"
          strokeWidth="6"
          strokeLinecap="round"
          fill="none"
        />
      </g>

      {/* scanning capture line */}
      <rect className="cat-capture__scanline" x="10" y="8" width="100" height="2" fill="var(--paw-orange)" />

      {/* rec indicator */}
      <circle className="cat-capture__rec-dot" cx="16" cy="16" r="4" fill="#e0503a" />
      <text x="24" y="19" className="cat-capture__rec-text">REC</text>
    </svg>
  )
}
