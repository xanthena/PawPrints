import { useEffect, useState } from 'react'
import {
  fetchModels,
  fetchOllamaModels,
  fetchPets,
  addPet,
  addPetImage,
  renamePet,
  deletePet,
} from '../api/settingsApi.js'
import { mediaUrl } from '../api/footageStream.js'
import './SettingsModal.css'

const MODEL_PREFS_KEY = 'pawprints:model-prefs'

// "qwen" is the provider-family key used throughout the backend (env
// vars, timeline file naming) -- Ollama can serve any vision-capable
// model the user has pulled, not just Qwen, so the dropdown shows a
// truthful label without renaming that key everywhere it's used.
function modelLabel(model) {
  return model === 'qwen' ? 'Ollama (local)' : model
}

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
  const savedPrefs = loadModelPrefs()
  const [primaryModel, setPrimaryModel] = useState(savedPrefs.primary || '')
  const [fallbackModel, setFallbackModel] = useState(savedPrefs.fallback || '')
  const [ollamaModels, setOllamaModels] = useState([])
  const [ollamaModel, setOllamaModel] = useState(savedPrefs.ollamaModel || '')
  const [ollamaError, setOllamaError] = useState(null)
  const [newName, setNewName] = useState('')
  const [newImages, setNewImages] = useState([])
  const [error, setError] = useState(null)
  const [isSaving, setIsSaving] = useState(false)
  const [editingPetId, setEditingPetId] = useState(null)
  const [editingName, setEditingName] = useState('')
  const [isRenaming, setIsRenaming] = useState(false)
  const [modelConfigSaved, setModelConfigSaved] = useState(false)

  useEffect(() => {
    fetchPets()
      .then(({ pets, max_pets }) => {
        setPets(pets)
        setMaxPets(max_pets)
      })
      .catch((err) => setError(err.message))

    fetchModels().then(setModels).catch((err) => setError(err.message))
    fetchOllamaModels()
      .then(setOllamaModels)
      .catch((err) => setOllamaError(err.message))
  }, [])

  function handleSaveModelConfig() {
    const prefs = { primary: primaryModel, fallback: fallbackModel, ollamaModel }
    saveModelPrefs(prefs)
    onModelPrefsChange?.(prefs)
    setModelConfigSaved(true)
    setTimeout(() => setModelConfigSaved(false), 2000)
  }

  async function handleAddPet(e) {
    e.preventDefault()
    if (!newName.trim() || newImages.length === 0) return
    setIsSaving(true)
    setError(null)
    try {
      const pet = await addPet(newName.trim(), newImages)
      setPets((current) => [...current, pet])
      setNewName('')
      setNewImages([])
    } catch (err) {
      setError(err.message)
    } finally {
      setIsSaving(false)
    }
  }

  async function handleAddPhoto(petId, file) {
    if (!file) return
    setError(null)
    try {
      const updated = await addPetImage(petId, file)
      setPets((current) => current.map((pet) => (pet.id === petId ? updated : pet)))
    } catch (err) {
      setError(err.message)
    }
  }

  function startRename(pet) {
    setError(null)
    setEditingPetId(pet.id)
    setEditingName(pet.name)
  }

  function cancelRename() {
    setEditingPetId(null)
    setEditingName('')
  }

  async function handleRenamePet(e, id) {
    e.preventDefault()
    const trimmed = editingName.trim()
    if (!trimmed || isRenaming) return
    setIsRenaming(true)
    setError(null)
    try {
      const updated = await renamePet(id, trimmed)
      setPets((current) => current.map((pet) => (pet.id === id ? updated : pet)))
      cancelRename()
    } catch (err) {
      setError(err.message)
    } finally {
      setIsRenaming(false)
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
            Register up to {maxPets} pets with one or more reference photos so the model can
            name who it sees, instead of just "a cat". More photos of a pet (different angles,
            lighting) can be added anytime with the + button below.
          </p>

          {pets.length > 0 && (
            <ul className="settings-modal__pets">
              {pets.map((pet) => (
                <li key={pet.id} className="settings-modal__pet">
                  <div className="settings-modal__pet-photos">
                    {pet.image_urls.map((url) => (
                      <img key={url} src={mediaUrl(url)} alt={pet.name} />
                    ))}
                    <label
                      className="settings-modal__add-photo"
                      title={`Add another photo of ${pet.name}`}
                    >
                      +
                      <input
                        type="file"
                        accept="image/jpeg,image/png"
                        hidden
                        onChange={(e) => {
                          handleAddPhoto(pet.id, e.target.files?.[0])
                          e.target.value = ''
                        }}
                      />
                    </label>
                  </div>
                  {editingPetId === pet.id ? (
                    <form
                      className="settings-modal__rename-form"
                      onSubmit={(e) => handleRenamePet(e, pet.id)}
                    >
                      <input
                        type="text"
                        value={editingName}
                        onChange={(e) => setEditingName(e.target.value)}
                        autoFocus
                        onKeyDown={(e) => {
                          if (e.key === 'Escape') cancelRename()
                        }}
                      />
                      <button
                        className="settings-modal__pet-rename-save"
                        type="submit"
                        disabled={isRenaming || !editingName.trim()}
                        aria-label={`Save name for ${pet.name}`}
                      >
                        ✓
                      </button>
                      <button
                        className="settings-modal__pet-rename-cancel"
                        type="button"
                        onClick={cancelRename}
                        aria-label="Cancel rename"
                      >
                        &times;
                      </button>
                    </form>
                  ) : (
                    <button
                      className="settings-modal__pet-name"
                      onClick={() => startRename(pet)}
                      title={`Rename ${pet.name}`}
                    >
                      {pet.name}
                    </button>
                  )}
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
                multiple
                onChange={(e) => setNewImages(Array.from(e.target.files || []))}
              />
              <button
                className="btn btn--secondary"
                type="submit"
                disabled={isSaving || !newName.trim() || newImages.length === 0}
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
              <select value={primaryModel} onChange={(e) => setPrimaryModel(e.target.value)}>
                <option value="">Select a model…</option>
                {models.map((model) => (
                  <option key={model} value={model}>
                    {modelLabel(model)}
                  </option>
                ))}
              </select>
            </label>
            <label className="settings-modal__model-field">
              Failover model
              <select value={fallbackModel} onChange={(e) => setFallbackModel(e.target.value)}>
                <option value="">Select a model…</option>
                {models.map((model) => (
                  <option key={model} value={model}>
                    {modelLabel(model)}
                  </option>
                ))}
              </select>
            </label>
          </div>

          {(primaryModel === 'qwen' || fallbackModel === 'qwen') && (
            <div className="settings-modal__ollama-model">
              <label className="settings-modal__model-field">
                Ollama model
                {ollamaModels.length > 0 ? (
                  <select value={ollamaModel} onChange={(e) => setOllamaModel(e.target.value)}>
                    <option value="">Select a model…</option>
                    {ollamaModels.map((model) => (
                      <option key={model} value={model}>
                        {model}
                      </option>
                    ))}
                  </select>
                ) : (
                  <span className="settings-modal__hint">
                    {ollamaError || 'No local Ollama models found -- pull one and reopen Settings.'}
                  </span>
                )}
              </label>
            </div>
          )}

          <div className="settings-modal__model-actions">
            <button
              className="btn btn--primary"
              type="button"
              onClick={handleSaveModelConfig}
              disabled={!primaryModel}
            >
              {modelConfigSaved ? 'Saved ✓' : 'Save'}
            </button>
          </div>
        </section>
      </div>
    </div>
  )
}
