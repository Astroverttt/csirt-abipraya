import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as api from '../utils/wazuhApi'
import { getAllAlertHistorySum, getActiveVulnerabilities, getAllActiveVulnerabilities, getFIMHistory, getSCAHistory } from '../utils/indexerApi'
import { getStats as getTicketStats } from '../utils/ticketStore'

export const useAppStore = defineStore('app', () => {
  const authenticated = ref(false)
  const loading = ref(false)
  const agents = ref([])
  const vulnsByAgent = ref({})
  const packagesByAgent = ref({})
  const hardwareByAgent = ref({})
  const historyByAgent = ref({})
  const indexerAlertsSummary = ref({})
  const selectedAgent = ref(null)
  const lastFetch = ref(null)

  const totalAgents = computed(() => agents.value.length)
  const activeAgents = computed(() => agents.value.filter(a => a.status === 'active').length)

  const allVulns = computed(() => {
    return Object.values(vulnsByAgent.value).flat()
  })

  const criticalCount = computed(() =>
    allVulns.value.filter(v => v.severity?.toLowerCase() === 'critical').length
  )
  const highCount = computed(() =>
    allVulns.value.filter(v => v.severity?.toLowerCase() === 'high').length
  )
  const mediumCount = computed(() =>
    allVulns.value.filter(v => v.severity?.toLowerCase() === 'medium').length
  )
  const lowCount = computed(() =>
    allVulns.value.filter(v => v.severity?.toLowerCase() === 'low').length
  )

  const patchedPackages = computed(() => {
    return Object.values(packagesByAgent.value).flat().filter(p => p.version)
  })

  const openTicketsCount = computed(() => {
    try {
      const stats = getTicketStats()
      return stats.open || null
    } catch { return null }
  })

  async function initialize() {
    loading.value = true
    try {
      const agentData = await api.getAgents()
      agents.value = agentData.affected_items || []
      lastFetch.value = new Date()
    } finally {
      loading.value = false
    }
  }

  async function fetchVulnerabilities(agentId) {
    try {
      const data = await getActiveVulnerabilities(agentId)
      vulnsByAgent.value[agentId] = data || []
      return vulnsByAgent.value[agentId]
    } catch (err) {
      console.error(`Indexer error for agent ${agentId}:`, err)
      vulnsByAgent.value[agentId] = []
      return []
    }
  }

  async function fetchPackages(agentId) {
    try {
      const data = await api.getPackages(agentId)
      packagesByAgent.value[agentId] = data.affected_items || []
      return packagesByAgent.value[agentId]
    } catch {
      packagesByAgent.value[agentId] = []
      return []
    }
  }

  async function fetchHardware(agentId) {
    try {
      const data = await api.getHardware(agentId)
      hardwareByAgent.value[agentId] = data.affected_items?.[0] || {}
      return hardwareByAgent.value[agentId]
    } catch {
      hardwareByAgent.value[agentId] = {}
      return {}
    }
  }

  async function fetchHistory(agentId) {
    try {
      const [sca, fim] = await Promise.all([
        getSCAHistory(agentId).catch(() => []),
        getFIMHistory(agentId).catch(() => [])
      ])
      historyByAgent.value[agentId] = {
        sca: sca || [],
        fim: fim || []
      }
      return historyByAgent.value[agentId]
    } catch {
      historyByAgent.value[agentId] = { sca: [], fim: [] }
      return historyByAgent.value[agentId]
    }
  }

  async function fetchAllData() {
    loading.value = true
    try {
      if (!agents.value.length) await initialize()
      
      // Fetch indexer data in parallel with other fetches
      const indexerPromise = getAllAlertHistorySum().then(data => {
        indexerAlertsSummary.value = data || {}
      })

      // Fetch vulnerabilities for all agents in one call
      const vulnPromise = fetchAllVulnerabilities()

      await Promise.all([
        indexerPromise,
        vulnPromise
      ])
      
      await indexerPromise
    } finally {
      loading.value = false
    }
  }

  async function fetchAllVulnerabilities() {
    loading.value = true
    try {
      const data = await getAllActiveVulnerabilities()
      // data is a dict keyed by agentId
      vulnsByAgent.value = { ...vulnsByAgent.value, ...data }
    } finally {
      loading.value = false
    }
  }

  function setAuthenticated(val) {
    authenticated.value = val
  }

  return {
    authenticated, loading, agents, vulnsByAgent, packagesByAgent, hardwareByAgent, historyByAgent, indexerAlertsSummary,
    selectedAgent, lastFetch,
    totalAgents, activeAgents, allVulns,
    criticalCount, highCount, mediumCount, lowCount, patchedPackages, openTicketsCount,
    initialize, fetchVulnerabilities, fetchPackages, fetchHardware, fetchHistory, fetchAllData, fetchAllVulnerabilities,
    setAuthenticated
  }
})
