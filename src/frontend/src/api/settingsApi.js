const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export async function fetchModels() {
  const response = await fetch(`${API_BASE}/api/models`)
  if (!response.ok) throw new Error(`Could not load models: ${response.status}`)
  const data = await response.json()
  return data.models
}

// The locally-pulled Ollama models -- "qwen" as a provider covers any
// vision-capable model Ollama is serving, not just qwen2.5vl:3b, so
// picking *which* one needs this machine's actual list, not a fixed one.
export async function fetchOllamaModels() {
  const response = await fetch(`${API_BASE}/api/ollama-models`)
  if (!response.ok) throw new Error(`Could not load Ollama models: ${response.status}`)
  const data = await response.json()
  if (data.error) throw new Error(data.error)
  return data.models
}

export async function fetchPets() {
  const response = await fetch(`${API_BASE}/api/pets`)
  if (!response.ok) throw new Error(`Could not load pets: ${response.status}`)
  return response.json()
}

export async function addPet(name, imageFiles) {
  const formData = new FormData()
  formData.append('name', name)
  for (const file of imageFiles) {
    formData.append('images', file)
  }

  const response = await fetch(`${API_BASE}/api/pets`, {
    method: 'POST',
    body: formData,
  })
  const data = await response.json().catch(() => ({}))
  if (!response.ok) throw new Error(data.detail || `Could not add pet: ${response.status}`)
  return data
}

export async function addPetImage(identifier, imageFile) {
  const formData = new FormData()
  formData.append('image', imageFile)

  const response = await fetch(`${API_BASE}/api/pets/${encodeURIComponent(identifier)}/images`, {
    method: 'POST',
    body: formData,
  })
  const data = await response.json().catch(() => ({}))
  if (!response.ok) throw new Error(data.detail || `Could not add photo: ${response.status}`)
  return data
}

export async function renamePet(identifier, newName) {
  const response = await fetch(`${API_BASE}/api/pets/${encodeURIComponent(identifier)}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name: newName }),
  })
  const data = await response.json().catch(() => ({}))
  if (!response.ok) throw new Error(data.detail || `Could not rename pet: ${response.status}`)
  return data
}

export async function deletePet(identifier) {
  const response = await fetch(`${API_BASE}/api/pets/${encodeURIComponent(identifier)}`, {
    method: 'DELETE',
  })
  const data = await response.json().catch(() => ({}))
  if (!response.ok) throw new Error(data.detail || `Could not remove pet: ${response.status}`)
  return data
}
