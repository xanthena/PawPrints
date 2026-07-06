export default function PawIcon({ size = 24, color = 'currentColor', className = '', style = {} }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 64 64"
      fill={color}
      className={className}
      style={style}
      xmlns="http://www.w3.org/2000/svg"
    >
      <ellipse cx="32" cy="42" rx="16" ry="13" />
      <ellipse cx="13" cy="26" rx="7" ry="9" transform="rotate(-20 13 26)" />
      <ellipse cx="29" cy="15" rx="7.5" ry="9.5" transform="rotate(-5 29 15)" />
      <ellipse cx="46" cy="16" rx="7.5" ry="9.5" transform="rotate(10 46 16)" />
      <ellipse cx="55" cy="30" rx="7" ry="9" transform="rotate(25 55 30)" />
    </svg>
  )
}
