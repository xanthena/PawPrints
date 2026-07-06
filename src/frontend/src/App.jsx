import { useEffect, useState } from 'react'
import SplashScreen from './components/SplashScreen.jsx'
import Dashboard from './components/Dashboard.jsx'

// Long enough for the title to fade in (finishes ~2.2s), the gap between
// "paw" and "prints" to open (finishes ~2.55s), and the paw-stamp
// animation that follows to fully play out (finishes ~3.15s) before the
// fade-out begins.
const SPLASH_VISIBLE_MS = 3400
const SPLASH_FADE_MS = 500

export default function App() {
  const [splashPhase, setSplashPhase] = useState('visible') // visible -> fading -> gone

  useEffect(() => {
    const fadeTimer = setTimeout(() => setSplashPhase('fading'), SPLASH_VISIBLE_MS)
    const goneTimer = setTimeout(() => setSplashPhase('gone'), SPLASH_VISIBLE_MS + SPLASH_FADE_MS)
    return () => {
      clearTimeout(fadeTimer)
      clearTimeout(goneTimer)
    }
  }, [])

  return (
    <>
      <Dashboard />
      {splashPhase !== 'gone' && <SplashScreen fadingOut={splashPhase === 'fading'} />}
    </>
  )
}
