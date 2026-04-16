/**
 * Playbook Store — API-backed with local cache.
 *
 * Same function signatures preserved from the original localStorage version.
 * Call loadPlaybooks() on mount to populate the cache.
 *
 * Client-side-only functions (evidence, icons, formatting) are kept as-is.
 */
import api from './api'

// ── In-memory cache ──────────────────────────────────────────────────────────
let _playbooks = []
let _loaded = false

/**
 * Load playbooks from the backend into the cahce.
 */
export async function loadPlaybooks() {
  try {
    const res = await api.get('/playbooks')
    _playbooks = res.data
    _loaded = true
  } catch (err) {
    console.warn('Failed to load playbooks from backend:', err)
    _playbooks = []
  }
}

// ── Seed (now handled by backend on startup) ─────────────────────────────────

export function seedDefaultPlaybooks(_defaults) {
  // No-op: seeding is handled by the backend on startup.
  // Kept for backward compatibility with imports.
}

// ── CRUD ─────────────────────────────────────────────────────────────────────

export function getAllPlaybooks() {
  return _playbooks
}

export function getPlaybookById(id) {
  return _playbooks.find(p => p.id === id) || null
}

export function saveAllPlaybooks(_pbs) {
  // No-op in API-backed mode. Individual CRUD ops handle persistence.
}

export async function createPlaybook(data) {
  const res = await api.post('/playbooks', data)
  const pb = res.data
  _playbooks.push(pb)
  return pb
}

export async function updatePlaybook(id, updates) {
  const res = await api.put(`/playbooks/${id}`, updates)
  const updated = res.data
  const idx = _playbooks.findIndex(p => p.id === id)
  if (idx !== -1) _playbooks[idx] = updated
  return updated
}

export async function deletePlaybook(id) {
  await api.delete(`/playbooks/${id}`)
  _playbooks = _playbooks.filter(p => p.id !== id)
}

// ── Matching Engine ──────────────────────────────────────────────────────────

export function matchPlaybooks(ticket) {
  const pbs = _playbooks.filter(p => p.isActive)
  const ticketGroups = (ticket.ruleGroups || []).map(g => g.toLowerCase())
  const ticketSev = (ticket.severity || '').toLowerCase()

  return pbs.filter(pb =>
    pb.triggers.some(trigger => {
      if (trigger.type === 'rule_group') {
        return ticketGroups.includes(trigger.value.toLowerCase())
      }
      if (trigger.type === 'severity') {
        return ticketSev === trigger.value.toLowerCase()
      }
      return false
    })
  )
}

// ── Ticket Playbook Progress (client-side logic, unchanged) ──────────────────

export function attachPlaybookToTicket(ticket, playbookId) {
  const pb = _playbooks.find(p => p.id === playbookId)
  if (!pb) return null

  const stepsProgress = {}
  pb.steps.forEach(step => {
    stepsProgress[step.id] = {
      checked: false, checkedAt: null, checkedBy: null, note: ''
    }
  })

  return {
    playbookId: pb.id,
    playbookName: pb.name,
    attachedAt: new Date().toISOString(),
    attachedBy: 'auto',
    steps: stepsProgress,
    completedSteps: 0,
    totalSteps: pb.steps.length,
    completedAt: null,
  }
}

export function updateStepProgress(ticketPlaybook, stepId, update) {
  const steps = { ...ticketPlaybook.steps }
  steps[stepId] = { ...steps[stepId], ...update }
  const completedSteps = Object.values(steps).filter(s => s.checked).length
  const totalSteps = Object.keys(steps).length
  return {
    ...ticketPlaybook,
    steps,
    completedSteps,
    totalSteps,
    completedAt: completedSteps === totalSteps ? new Date().toISOString() : null,
  }
}

// ── Evidence (client-side only — files stored in ticket data) ────────────────

const MAX_EVIDENCE_BYTES = 4 * 1024 * 1024

function generateEvId() {
  return `EV-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`
}

export async function addEvidence(ticket, file, options = {}) {
  const { linkedStepId = null, description = '', uploadedBy = 'analyst', tags = [] } = options

  if (file.size > MAX_EVIDENCE_BYTES) {
    throw new Error(`File terlalu besar. Maksimum 4MB. File ini ${(file.size / 1024 / 1024).toFixed(1)}MB`)
  }

  const base64 = await fileToBase64(file)

  const ev = {
    id: generateEvId(),
    ticketId: ticket.id,
    uploadedAt: new Date().toISOString(),
    uploadedBy,
    fileName: file.name,
    fileType: file.type || 'application/octet-stream',
    fileSize: file.size,
    base64,
    linkedStepId,
    description,
    tags,
  }

  return [...(ticket.evidence || []), ev]
}

export function removeEvidence(ticket, evidenceId) {
  return (ticket.evidence || []).filter(e => e.id !== evidenceId)
}

function fileToBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(reader.result)
    reader.onerror = reject
    reader.readAsDataURL(file)
  })
}

export function downloadEvidence(ev) {
  const a = document.createElement('a')
  a.href = ev.base64
  a.download = ev.fileName
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
}

export function formatFileSize(bytes) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

export function getPlaybookIcon(icon) {
  const icons = {
    malware: '🦠',
    auth: '🔐',
    vuln: '🛡',
    fim: '📁',
    rootkit: '🕵️',
    network: '🌐',
    dos: '🌊',
    generic: '⚡',
  }
  return icons[icon] || '📋'
}

// ── Storage Usage (legacy compat) ────────────────────────────────────────────

export function getPlaybookStorageUsage() {
  const dataStr = JSON.stringify(_playbooks)
  const bytes = new Blob([dataStr]).size
  return {
    usedBytes: bytes,
    usedMB: (bytes / (1024 * 1024)).toFixed(2),
    percentage: '0', // No localStorage limit anymore
    isWarning: false,
  }
}
