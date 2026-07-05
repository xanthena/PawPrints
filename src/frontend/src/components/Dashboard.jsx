import { useState } from 'react'
import PawIcon from './PawIcon.jsx'
import FootageCard from './FootageCard.jsx'
import AddFootageModal from './AddFootageModal.jsx'
import { MOCK_FOOTAGES } from '../mock/footages.js'
import './Dashboard.css'

export default function Dashboard() {
  const [isModalOpen, setIsModalOpen] = useState(false)
  const footages = [...MOCK_FOOTAGES].sort((a, b) => (a.date < b.date ? 1 : -1))

  function handleUpload(file) {
    // Wiring to the real processing pipeline comes later -- for now this
    // just confirms the file made it out of the modal.
    console.log('Selected footage for analysis:', file)
    setIsModalOpen(false)
  }

  return (
    <div className="dashboard">
      <header className="dashboard__header">
        <div className="dashboard__brand">
          <PawIcon size={30} color="var(--paw-orange)" />
          <h1>PawPrints</h1>
        </div>
        <button className="btn btn--primary" onClick={() => setIsModalOpen(true)}>
          + Add Footage
        </button>
      </header>

      <div className="dashboard__grid">
        {footages.map((footage) => (
          <FootageCard key={footage.id} footage={footage} />
        ))}
      </div>

      {isModalOpen && (
        <AddFootageModal onClose={() => setIsModalOpen(false)} onUpload={handleUpload} />
      )}
    </div>
  )
}
