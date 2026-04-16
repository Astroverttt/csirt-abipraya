/**
 * Ticket Store — API-backed with local cache.
 *
 * Sync accessors read from in-memory cache.
 * Mutations call the backend API AND update the cache.
 * Call loadTickets() on mount to populate the cache.
 *
 * All function signatures are preserved from the original localStorage version.
 */
import api from './api'

// ── In-memory cache ──────────────────────────────────────────────────────────
let _tickets = []
let _loaded = false

/**
 * Load tickets from the backend into the cache.
 * Call this in onMounted of any view that uses tickets.
 */
export async function loadTickets() {
  try {
    const res = await api.get('/tickets')
    _tickets = res.data
    _loaded = true
  } catch (err) {
    console.warn('Failed to load tickets from backend:', err)
    _tickets = []
  }
}

export async function syncTickets() {
  try {
    const res = await api.post('/tickets/sync')
    await loadTickets() // reload cache immediately
    return res.data
  } catch (err) {
    console.error('Failed to sync tickets:', err)
    throw err
  }
}

function _ensureLoaded() {
  if (!_loaded) {
    console.warn('Tickets not loaded yet. Call loadTickets() first.')
  }
}

// ── Read operations (sync from cache) ────────────────────────────────────────

export function getTickets(filters = {}) {
  _ensureLoaded()
  let tickets = [..._tickets]

  if (filters.status) tickets = tickets.filter(t => t.status === filters.status)
  if (filters.severity) tickets = tickets.filter(t => t.severity?.toLowerCase() === filters.severity)
  if (filters.agentId) tickets = tickets.filter(t => t.agentId === filters.agentId)
  if (filters.search) {
    const q = filters.search.toLowerCase()
    tickets = tickets.filter(t =>
      t.id.toLowerCase().includes(q) ||
      t.cveId?.toLowerCase().includes(q) ||
      t.agentName?.toLowerCase().includes(q) ||
      t.ruleDescription?.toLowerCase().includes(q) ||
      t.packageName?.toLowerCase().includes(q) ||
      t.assignee?.toLowerCase().includes(q)
    )
  }
  return tickets.sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt))
}

export function getTicketById(id) {
  _ensureLoaded()
  return _tickets.find(t => t.id === id) || null
}

export function getStats() {
  _ensureLoaded()
  const tickets = _tickets
  return {
    total: tickets.length,
    open: tickets.filter(t => t.status === 'open').length,
    in_progress: tickets.filter(t => t.status === 'in_progress').length,
    solved: tickets.filter(t => t.status === 'solved').length,
    closed: tickets.filter(t => t.status === 'closed').length,
    false_positive: tickets.filter(t => t.status === 'false_positive').length,
    critical: tickets.filter(t => t.priority === 'critical').length,
    high: tickets.filter(t => t.priority === 'high').length,
  }
}

// ── Write operations (API call + cache update) ───────────────────────────────

export async function createTicket(data) {
  try {
    const res = await api.post('/tickets', data)
    const ticket = res.data
    _tickets.unshift(ticket)
    return ticket
  } catch (err) {
    if (err.response?.status === 409) return null // Duplicate
    throw err
  }
}

export async function updateTicket(id, updates) {
  const res = await api.put(`/tickets/${id}`, updates)
  const updated = res.data
  const idx = _tickets.findIndex(t => t.id === id)
  if (idx !== -1) _tickets[idx] = updated
  return updated
}

export async function deleteTicket(id) {
  await api.delete(`/tickets/${id}`)
  _tickets = _tickets.filter(t => t.id !== id)
}

// ── Export / Import ──────────────────────────────────────────────────────────

export async function exportJSON() {
  try {
    const res = await api.get('/tickets/export')
    const data = JSON.stringify(res.data, null, 2)
    const blob = new Blob([data], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `tickets_backup_${new Date().toISOString().slice(0, 10)}.json`
    a.click()
    URL.revokeObjectURL(url)
  } catch (err) {
    console.error('Export failed:', err)
  }
}

export async function importJSON(file) {
  const formData = new FormData()
  formData.append('file', file)
  const res = await api.post('/tickets/import', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
  // Reload cache after import
  await loadTickets()
  return res.data.imported
}

// ── Storage info (legacy compat) ─────────────────────────────────────────────

export function getStorageUsage() {
  const dataStr = JSON.stringify(_tickets)
  const bytes = new Blob([dataStr]).size
  const mb = (bytes / (1024 * 1024)).toFixed(2)
  return { bytes, mb, percentage: '0' } // No 5MB limit anymore
}
