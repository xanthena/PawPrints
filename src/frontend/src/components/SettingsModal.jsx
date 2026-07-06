import { useEffect, useState } from 'react'
import { fetchModels, fetchPets, addPet, deletePet } from '../api/settingsApi.js'
import { mediaUrl } from '../api/footageStream.js'
import './SettingsModal.css'

const MODEL_PREFS_KEY = 'pawprints:model-prefs'

export function loadModelPrefs() {
  try {
    return JSON.parse(localStorage.getItem(MODEL_PREFS_KEY)) || {}
  } catch {
    return {}
  }
}

function saveModelPrefs(prefs) {
  localStorage.setItem(MODEL_PREFS_KEY, JSON.stringify(prefs))
}

export default function SettingsModal({ onClose, onModelPrefsChange }) {
  const [pets, setPets] = useState([])
  const [maxPets, setMaxPets] = useState(2)
  const [models, setModels] = useState([])
  const [primaryModel, setPrimaryModel] = useState('')
  const [fallbackModel, setFallbackModel] = useState('')
  const [newName, setNewName] = useState('')
  const [newImage, setNewImage] = useState(null)
  const [error, setError] = useState(null)
  const [isSaving, setIsSaving] = useState(false)

  useEffect(() => {
    fetchPets()
      .then(({ pets, max_pets }) => {
        setPets(pets)
        setMaxPets(max_pets)
      })
      .catch((err) => setError(err.message))

    fetchModels()
      .then((loadedModels) => {
        setModels(loadedModels)
        const prefs = loadModelPrefs()
        setPrimaryModel(prefs.primary || loadedModels[0] || '')
        setFallbackModel(prefs.fallback || loadedModels[0] || '')
      })
      .catch((err) => setError(err.message))
  }, [])

  function updatePrimary(value) {
    setPrimaryModel(value)
    const prefs = { primary: value, fallback: fallbackModel }
    saveModelPrefs(prefs)
    onModelPrefsChange?.(prefs)
  }

  function updateFallback(value) {
    setFallbackModel(value)
    const prefs = { primary: primaryModel, fallback: value }
    saveModelPrefs(prefs)
    onModelPrefsChange?.(prefs)
  }

  async function handleAddPet(e) {
    e.preventDefault()
    if (!newName.trim() || !newImage) return
    setIsSaving(true)
    setError(null)
    try {
      const pet = await addPet(newName.trim(), newImage)
      setPets((current) => [...current, pet])
      setNewName('')
      setNewImage(null)
    } catch (err) {
      setError(err.message)
    } finally {
      setIsSaving(false)
    }
  }

  async function handleRemovePet(id) {
    setError(null)
    try {
      await deletePet(id)
      setPets((current) => current.filter((pet) => pet.id !== id))
    } catch (err) {
      setError(err.message)
    }
  }

  const canAddMore = pets.length < maxPets

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal settings-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal__header">
          <h2>Settings</h2>
          <button className="modal__close" onClick={onClose} aria-label="Close">
            &times;
          </button>
        </div>

        {error && <p className="settings-modal__error">{error}</p>}

        <section className="settings-modal__section">
          <h3 className="settings-modal__section-title">Pet profiles</h3>
          <p className="settings-modal__hint">
            Register up to {maxPets} pets with a reference photo so the model can name who it sees, instead of just "a cat".
          </p>

          {pets.length > 0 && (
            <ul className="settings-modal__pets">
              {pets.map((pet) => (
                <li key={pet.id} className="settings-modal__pet">
                  <img src={mediaUrl(pet.image_url)} alt={pet.name} />
                  <span className="settings-modal__pet-name">{pet.name}</span>
                  <button
                    className="settings-modal__pet-remove"
                    onClick={() => handleRemovePet(pet.id)}
                    aria-label={`Remove ${pet.name}`}
                  >
                    &times;
                  </button>
                </li>
              ))}
            </ul>
          )}

          {canAddMore ? (
            <form className="settings-modal__add-pet" onSubmit={handleAddPet}>
              <input
                type="text"
                placeholder="Pet name"
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
              />
              <input
                type="file"
                accept="image/jpeg,image/png"
                onChange={(e) => setNewImage(e.target.files?.[0] || null)}
              />
              <button
                className="btn btn--secondary"
                type="submit"
                disabled={isSaving || !newName.trim() || !newImage}
              >
                {isSaving ? 'Adding…' : 'Add pet'}
              </button>
            </form>
          ) : (
            <p className="settings-modal__hint">Remove a pet to register a different one.</p>
          )}
        </section>

        <section className="settings-modal__section">
          <h3 className="settings-modal__section-title">Model configuration</h3>
          <div className="settings-modal__model-row">
            <label className="settings-modal__model-field">
              Primary model
              <select value={primaryModel} onChange={(e) => updatePrimary(e.target.value)}>
                {models.map((model) => (
                  <option key={model} value={model}>
                    {model}
                  </option>
                ))}
              </select>
            </label>
            <label className="settings-modal__model-field">
              Failover model
              <select value={fallbackModel} onChange={(e) => updateFallback(e.target.value)}>
                {models.map((model) => (
                  <option key={model} value={model}>
                    {model}
                  </option>
                ))}
              </select>
            </label>
          </div>
        </section>
      </div>
    </div>
  )
}
