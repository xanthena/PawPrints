import { app, BrowserWindow, dialog } from 'electron'
import { spawn, exec } from 'node:child_process'
import { existsSync } from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const isDev = !app.isPackaged

const BACKEND_DIR = path.join(__dirname, '../../backend')
const BACKEND_HEALTH_URL = 'http://localhost:8000/api/health'

// "py -3.12" resolves whatever Python 3.12 is registered system-wide --
// not necessarily the one the project's dependencies were installed
// into. The README has users create src/backend/.venv and pip install
// there, so that venv's own interpreter (guaranteed to have uvicorn,
// torch, etc.) is tried first; the bare launcher is only a fallback for
// a global, no-venv install.
function resolvePythonCommand() {
  const venvPython =
    process.platform === 'win32'
      ? path.join(BACKEND_DIR, '.venv', 'Scripts', 'python.exe')
      : path.join(BACKEND_DIR, '.venv', 'bin', 'python')
  if (existsSync(venvPython)) {
    return { command: venvPython, versionArgs: [] }
  }
  if (process.platform === 'win32') {
    return { command: 'py', versionArgs: ['-3.12'] }
  }
  return { command: 'python3', versionArgs: [] }
}

let backendProcess = null
// Keeps the tail of stderr so a failed startup can show *why* -- e.g.
// "No module named uvicorn" -- instead of just "it never came up".
let backendStderrTail = ''

function startBackend() {
  const { command, versionArgs } = resolvePythonCommand()
  backendProcess = spawn(
    command,
    [...versionArgs, '-m', 'uvicorn', 'app.api.server:app', '--port', '8000'],
    { cwd: BACKEND_DIR }
  )
  backendProcess.stdout.on('data', (data) => process.stdout.write(`[backend] ${data}`))
  backendProcess.stderr.on('data', (data) => {
    process.stderr.write(`[backend] ${data}`)
    backendStderrTail = (backendStderrTail + data.toString()).slice(-2000)
  })
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
      // Opening the window anyway just reproduces this same failure
      // one layer up, as a confusing "Failed to fetch" deep inside
      // Settings -- show what actually went wrong up front instead.
      console.error('Backend did not become healthy in time:', error)
      stopBackend()
      dialog.showErrorBox(
        'PawPrints backend failed to start',
        'The app could not reach the backend at ' +
          BACKEND_HEALTH_URL +
          '.\n\n' +
          'Make sure the backend dependencies are installed (see README.md: ' +
          '"Install and configure the backend") for whichever Python this ' +
          'launched -- either src/backend/.venv or a global Python 3.12.\n\n' +
          'Recent backend output:\n' +
          (backendStderrTail.trim() || '(no output captured)')
      )
      app.quit()
    })
})

app.on('before-quit', stopBackend)

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit()
})
