/**
 * Wazuh API wrapper — now calls the backend instead of Wazuh directly.
 *
 * IMPORTANT: All function signatures and return types are preserved
 * so that existing views DO NOT need to change.
 */
import api, { setToken, clearToken, isAuthenticated as checkAuth } from './api'

// ── Auth ─────────────────────────────────────────────────────────────────────

export async function login(username, password) {
  const res = await api.post('/auth/login', { username, password })
  setToken(res.data.token)
  return res.data.token
}

export function logout() {
  api.post('/auth/logout').catch(() => {})
  clearToken()
}

export function isAuthenticated() {
  return checkAuth()
}

// Keep backward compat — some code imports getCredentials
export function getCredentials() {
  return isAuthenticated() ? { username: 'session' } : null
}

// ── Agents ───────────────────────────────────────────────────────────────────

export async function getAgents(params = {}) {
  const res = await api.get('/agents', { params: { limit: 500, ...params } })
  return res.data
}

export async function getAgentSummary() {
  const res = await api.get('/agents/summary/status')
  return res.data
}

// ── Vulnerabilities ──────────────────────────────────────────────────────────

export async function getVulnerabilities(agentId, params = {}) {
  const res = await api.get(`/vulnerability/${agentId}`, { params: { limit: 500, ...params } })
  return res.data
}

export async function getAllVulnerabilities(params = {}) {
  const res = await api.get('/vulnerability', { params: { limit: 500, ...params } })
  return res.data
}

export async function getVulnerabilitySummary(agentId) {
  const res = await api.get(`/vulnerability/${agentId}/summary/severity`)
  return res.data
}

// ── Packages / Syscollector ──────────────────────────────────────────────────

export async function getPackages(agentId, params = {}) {
  const res = await api.get(`/syscollector/${agentId}/packages`, { params: { limit: 500, ...params } })
  return res.data
}

export async function getHotfixes(agentId) {
  const res = await api.get(`/syscollector/${agentId}/hotfixes`)
  return res.data
}

export async function getOS(agentId) {
  const res = await api.get(`/syscollector/${agentId}/os`)
  return res.data
}

export async function getHardware(agentId) {
  const res = await api.get(`/syscollector/${agentId}/hardware`)
  return res.data
}

export async function getNetwork(agentId) {
  const res = await api.get(`/syscollector/${agentId}/netaddr`)
  return res.data
}

// ── SCA ──────────────────────────────────────────────────────────────────────

export async function getSCAPolicy(agentId) {
  const res = await api.get(`/sca/${agentId}`)
  return res.data
}

// ── Overview Stats ───────────────────────────────────────────────────────────

export async function getOverviewStats() {
  const [agents, vulns] = await Promise.all([
    getAgents(),
    getAllVulnerabilities().catch(() => ({ affected_items: [], total_affected_items: 0 }))
  ])
  return { agents, vulns }
}
