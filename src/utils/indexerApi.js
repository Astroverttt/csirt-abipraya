/**
 * Indexer API wrapper — now calls the backend instead of Elasticsearch directly.
 *
 * All function signatures and return types are preserved.
 */
import api from './api'

export async function getAllAlertHistorySum() {
  try {
    const res = await api.get('/indexer/alerts/summary')
    return res.data
  } catch (err) {
    console.warn('Could not fetch indexer alert summary:', err)
    return {}
  }
}

export async function getAlertHistoryDetails(agentId) {
  const res = await api.get(`/indexer/alerts/${agentId}`)
  return res.data
}

export async function getActiveVulnerabilities(agentId) {
  try {
    const res = await api.get(`/indexer/vulnerabilities/${agentId}`)
    return res.data
  } catch (err) {
    console.warn('Could not fetch active vulnerabilities:', err)
    return []
  }
}

export async function getAllActiveVulnerabilities() {
  try {
    const res = await api.get('/indexer/vulnerabilities')
    return res.data
  } catch (err) {
    console.warn('Could not fetch all active vulnerabilities:', err)
    return {}
  }
}

export async function getFIMHistory(agentId) {
  try {
    const res = await api.get(`/indexer/fim/${agentId}`)
    return res.data
  } catch {
    return []
  }
}

export async function getSCAHistory(agentId) {
  try {
    const res = await api.get(`/indexer/sca/${agentId}`)
    return res.data
  } catch {
    return []
  }
}
