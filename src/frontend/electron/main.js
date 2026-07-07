import { app, BrowserWindow } from 'electron'
import { spawn, exec } from 'node:child_process'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const isDev = !app.isPackaged

const BACKEND_DIR = path.join(__dirname, '../../backend')
// Same invocation the rest of this project's tooling already uses (see
// .claude/launch.json) -- the "py" launcher resolves whichever machine's
// Python 3.12 install without hardcoding a user-specific path. Whether
// "py" execs directly into python.exe or spawns it as a child, taskkill
// /t below kills the whole process tree either way, so backend cleanup
// on quit doesn't depend on which one happens.
const PYTHON_LAUNCHER = 'py'
const PYTHON_VERSION_FLAG = '-3.12'
const BACKEND_HEALTH_URL = 'http://localhost:8000/api/health'

let backendProcess = null

function startBackend() {
  backendProcess = spawn(
    PYTHON_LAUNCHER,
    [PYTHON_VERSION_FLAG, '-m', 'uvicorn', 'app.api.server:app', '--port', '8000'],
    { cwd: BACKEND_DIR }
  )
  backendProcess.stdout.on('data', (data) => process.stdout.write(`[backend] ${data}`))
  backendProcess.stderr.on('data', (data) => process.stderr.write(`[backend] ${data}`))
}

function stopBackend() {
  if (!backendProcess) return
  // child.kill() alone doesn't reliably tear down a process tree on
  // Windows -- taskkill /t walks and kills the whole tree.
  exec(`taskkill /pid ${backendProcess.pid} /t /f`)
  backendProcess = null
}

function waitForBackend(deadline = Date.now() + 30000) {
  return fetch(BACKEND_HEALTH_URL)
    .then((response) => {
      if (!response.ok) throw new Error(`Backend health check failed: ${response.status}`)
    })
    .catch((error) => {
      if (Date.now() >= deadline) throw error
      return new Promise((resolve) => setTimeout(resolve, 300)).then(() =>
        waitForBackend(deadline)
      )
    })
}

function createWindow() {
  const win = new BrowserWindow({
    width: 1280,
    height: 800,
    title: 'PawPrints',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
    },
  })

  if (isDev) {
    win.loadURL('http://localhost:5173')
  } else {
    win.loadFile(path.join(__dirname, '../dist/index.html'))
  }
}

app.whenReady().then(() => {
  startBackend()
  waitForBackend()
    .then(createWindow)
    .catch((error) => {
      console.error('Backend did not become healthy in time:', error)
      createWindow()
    })
})

app.on('before-quit', stopBackend)

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit()
})
