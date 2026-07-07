import { useState } from 'react'
import PawIcon from './PawIcon.jsx'
import CatFaceIcon from './CatFaceIcon.jsx'
import FootageCard from './FootageCard.jsx'
import LiveFootageCard from './LiveFootageCard.jsx'
import AddFootageModal from './AddFootageModal.jsx'
import ProcessingModal from './ProcessingModal.jsx'
import FootageTimelineModal from './FootageTimelineModal.jsx'
import SettingsModal, { loadModelPrefs } from './SettingsModal.jsx'
import QueryWidget from './QueryWidget.jsx'
import { MOCK_FOOTAGES } from '../mock/footages.js'
import { streamFootageAnalysis, mediaUrl } from '../api/footageStream.js'
import { formatDayHeading, todayDateString } from '../utils/date.js'
import './Dashboard.css'

function newLiveJob(id, file) {
  return {
    id,
    kind: 'live',
    date: todayDateString(),
    filename: file.name,
    status: 'starting',
    processedSeconds: 0,
    durationSeconds: 0,
    thumbnailUrl: null,
    videoUrl: null,
    timeline: [],
    reelUrl: null,
    reelNote: null,
    errorMessage: null,
  }
}

// Groups every footage (live or mock) by calendar day and orders the
// days newest first, so the dashboard reads as a day-by-day log rather
// than one flat, undated grid.
function groupByDay(footages) {
  const byDate = new Map()
  for (const footage of footages) {
    if (!byDate.has(footage.date)) byDate.set(footage.date, [])
    byDate.get(footage.date).push(footage)
  }
  return [...byDate.entries()].sort(([a], [b]) => (a < b ? 1 : -1))
}

export default function Dashboard() {
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [isSettingsOpen, setIsSettingsOpen] = useState(false)
  const [modelPrefs, setModelPrefs] = useState(loadModelPrefs)
  const [processingJobId, setProcessingJobId] = useState(null)
  const [openJobId, setOpenJobId] = useState(null)
  const [liveJobs, setLiveJobs] = useState([])
  const mockFootages = [...MOCK_FOOTAGES].sort((a, b) => (a.date < b.date ? 1 : -1))

  function updateJob(jobId, patch) {
    setLiveJobs((jobs) =>
      jobs.map((job) => {
        if (job.id !== jobId) return job
        const changes = typeof patch === 'function' ? patch(job) : patch
        return { ...job, ...changes }
      })
    )
  }

  async function handleUpload(file) {
    setIsModalOpen(false)

    const jobId = `job-${Date.now()}`
    setLiveJobs((jobs) => [newLiveJob(jobId, file), ...jobs])
    setProcessingJobId(jobId)

    // The processing modal is a nice moment on its own, but once
    // something is actually visible (a real detected frame) there's no
    // reason to keep the user staring at a full-screen spinner instead
    // of the dashboard -- reveal it and let the card itself keep
    // showing progress from there via AnalyzingBadge.
    let revealed = false
    const revealDashboard = () => {
      if (!revealed) {
        revealed = true
        setProcessingJobId((current) => (current === jobId ? null : current))
      }
    }

    try {
      await streamFootageAnalysis(file, {
        primaryModel: modelPrefs.primary,
        fallbackModel: modelPrefs.fallback,
        ollamaModel: modelPrefs.ollamaModel,
        onEvent: (event) => {
          switch (event.type) {
            case 'started':
              updateJob(jobId, {
                status: 'analyzing',
                durationSeconds: event.duration_seconds,
                videoUrl: mediaUrl(event.video_url),
              })
              break

            case 'progress':
              updateJob(jobId, { processedSeconds: event.processed_seconds })
              break

            case 'candidate':
              updateJob(jobId, { thumbnailUrl: mediaUrl(event.frame_url) })
              revealDashboard()
              break

            case 'timeline':
              updateJob(jobId, { timeline: event.events })
              break

            case 'reel_ready':
              updateJob(jobId, { reelUrl: mediaUrl(event.reel_url) })
              break

            case 'reel_skipped':
              updateJob(jobId, { reelNote: event.reason })
              break

            case 'done':
              updateJob(jobId, { status: 'done' })
              revealDashboard()
              break

            case 'error':
              updateJob(jobId, { status: 'error', errorMessage: event.message })
              revealDashboard()
              break

            default:
              break
          }
        },
      })
    } catch (err) {
      updateJob(jobId, { status: 'error', errorMessage: err.message })
      revealDashboard()
    }
  }

  const processingJob = liveJobs.find((job) => job.id === processingJobId)
  const openJob = liveJobs.find((job) => job.id === openJobId)
  const days = groupByDay([...liveJobs, ...mockFootages])

  return (
    <div className="dashboard">
      <header className="dashboard__header">
        <div className="dashboard__brand">
          <PawIcon size={30} color="var(--paw-orange)" />
          <h1 className="brand-title">paw prints</h1>
        </div>
        <div className="dashboard__header-actions">
          <button className="btn btn--primary" onClick={() => setIsModalOpen(true)}>
            + Add Footage
          </button>
          <button
            className="dashboard__settings-btn"
            onClick={() => setIsSettingsOpen(true)}
            aria-label="Settings"
          >
            <CatFaceIcon size={22} color="var(--brown-deep)" />
          </button>
        </div>
      </header>

      <div className="dashboard__days">
        {days.map(([date, footages]) => (
          <section key={date} className="dashboard__day">
            <h2 className="dashboard__day-heading">{formatDayHeading(date)}</h2>
            <div className="dashboard__grid">
              {footages.map((footage) =>
                footage.kind === 'live' ? (
                  <LiveFootageCard
                    key={footage.id}
                    footage={footage}
                    onClick={() => setOpenJobId(footage.id)}
                  />
                ) : (
                  <FootageCard key={footage.id} footage={footage} />
                )
              )}
            </div>
          </section>
        ))}
      </div>

      {isModalOpen && (
        <AddFootageModal onClose={() => setIsModalOpen(false)} onUpload={handleUpload} />
      )}

      {processingJob && <ProcessingModal filename={processingJob.filename} />}

      {openJob && openJob.videoUrl && (
        <FootageTimelineModal footage={openJob} onClose={() => setOpenJobId(null)} />
      )}

      {isSettingsOpen && (
        <SettingsModal
          onClose={() => setIsSettingsOpen(false)}
          onModelPrefsChange={setModelPrefs}
        />
      )}

      <QueryWidget />
    </div>
  )
}
