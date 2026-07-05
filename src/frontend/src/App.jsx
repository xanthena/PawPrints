import { useEffect, useState } from 'react'
import SplashScreen from './components/SplashScreen.jsx'
import Dashboard from './components/Dashboard.jsx'

const SPLASH_VISIBLE_MS = 2200
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
