import PawIcon from './PawIcon.jsx'
import './PawStamp.css'

export default function PawStamp() {
  return (
    <span className="paw-stamp">
      <PawIcon size={22} color="var(--paw-orange)" className="paw-stamp__print" />
      <PawIcon size={30} color="var(--brown-soft)" className="paw-stamp__hand" />
    </span>
  )
}
