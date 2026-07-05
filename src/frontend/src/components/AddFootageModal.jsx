import { useRef, useState } from 'react'
import PawIcon from './PawIcon.jsx'
import './AddFootageModal.css'

function formatSize(bytes) {
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

export default function AddFootageModal({ onClose, onUpload }) {
  const [isDragging, setIsDragging] = useState(false)
  const [selectedFile, setSelectedFile] = useState(null)
  const fileInputRef = useRef(null)

  function handleFiles(files) {
    const file = files?.[0]
    if (file && file.type.startsWith('video/')) {
      setSelectedFile(file)
    }
  }

  function handleDrop(e) {
    e.preventDefault()
    setIsDragging(false)
    handleFiles(e.dataTransfer.files)
  }

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal__header">
          <h2>Add Footage</h2>
          <button className="modal__close" onClick={onClose} aria-label="Close">
            &times;
          </button>
        </div>

        {!selectedFile ? (
          <div
            className={`dropzone ${isDragging ? 'dropzone--active' : ''}`}
            onDragOver={(e) => {
              e.preventDefault()
              setIsDragging(true)
            }}
            onDragLeave={() => setIsDragging(false)}
            onDrop={handleDrop}
          >
            <PawIcon size={40} color="var(--paw-orange)" />
            <p className="dropzone__text">Drag &amp; drop your video here</p>
            <p className="dropzone__or">or</p>
            <button className="btn btn--secondary" onClick={() => fileInputRef.current.click()}>
              Browse Files
            </button>
            <input
              ref={fileInputRef}
              type="file"
              accept="video/*"
              hidden
              onChange={(e) => handleFiles(e.target.files)}
            />
          </div>
        ) : (
          <div className="selected-file">
            <div className="selected-file__icon">
              <PawIcon size={28} color="var(--paw-orange)" />
            </div>
            <div className="selected-file__info">
              <span className="selected-file__name">{selectedFile.name}</span>
              <span className="selected-file__size">{formatSize(selectedFile.size)}</span>
            </div>
            <button className="selected-file__remove" onClick={() => setSelectedFile(null)} aria-label="Remove file">
              &times;
            </button>
          </div>
        )}

        <div className="modal__actions">
          <button className="btn btn--secondary" onClick={onClose}>
            Cancel
          </button>
          <button
            className="btn btn--primary"
            disabled={!selectedFile}
            onClick={() => onUpload?.(selectedFile)}
          >
            Analyze Footage
          </button>
        </div>
      </div>
    </div>
  )
}
