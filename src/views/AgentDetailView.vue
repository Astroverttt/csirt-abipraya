<template>
  <div class="page">
    <div class="page-header">
      <div>
        <button class="btn btn-ghost" style="margin-bottom: 10px;" @click="$router.back()">← Back</button>
        <h2>{{ agent?.name || `Agent ${agentId}` }}</h2>
        <div class="meta" v-if="agent">
          <span class="mono">{{ agent.ip }}</span>
          <span class="sep">·</span>
          <span>{{ agent.os?.name }}</span>
          <span class="sep">·</span>
          <span class="badge" :class="statusBadge(agent.status)">{{ agent.status }}</span>
          <span class="sep">·</span>
          <span class="age-badge">Age: {{ calculateAge(agent.dateAdd) }}</span>
        </div>
      </div>
      <button class="btn btn-primary" @click="loadData" :disabled="loading">
        {{ loading ? 'Loading...' : 'Load Data' }}
      </button>
    </div>

    <div class="tabs">
      <button v-for="t in tabs" :key="t.key" class="tab" :class="{ active: activeTab === t.key }" @click="activeTab = t.key">
        {{ t.label }}
        <span v-if="t.count" class="tab-count">{{ t.count }}</span>
        <span v-if="t.alert" class="tab-alert-dot"></span>
      </button>
    </div>

    <!-- Vulnerabilities -->
    <div v-if="activeTab === 'vulns'">
      <div class="toolbar">
        <input v-model="vulnSearch" placeholder="Cari CVE, package..." style="width: 260px;" />
        <select v-model="vulnSeverity">
          <option value="">Semua Severity</option>
          <option v-for="s in ['Critical','High','Medium','Low']" :key="s" :value="s">{{ s }}</option>
        </select>
        <span class="count-text">{{ filteredVulns.length }} hasil</span>
      </div>
      <div class="card" style="padding: 0; margin-top: 12px; overflow: hidden;">
        <table>
          <thead>
            <tr><th>CVE ID</th><th>Package</th><th>Version</th><th>Severity</th><th>CVSS</th><th>Fix</th></tr>
          </thead>
          <tbody>
            <tr v-if="!vulns.length"><td colspan="6" style="text-align:center; color:var(--text3); padding: 32px;">Klik "Load Data" untuk mengambil data vulnerabilities.</td></tr>
            <tr v-for="v in filteredVulns" :key="v.cve">
              <td><a :href="`https://nvd.nist.gov/vuln/detail/${v.cve}`" target="_blank" class="cve-link">{{ v.cve }}</a></td>
              <td>{{ v.name }}</td>
              <td><span class="mono" style="font-size: 11px;">{{ v.version }}</span></td>
              <td><span class="badge" :class="`badge-${v.severity?.toLowerCase()}`">{{ v.severity }}</span></td>
              <td><span class="mono">{{ v.cvss || '-' }}</span></td>
              <td><span class="mono" style="color: var(--low); font-size: 11px;">{{ v.condition || '-' }}</span></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Packages -->
    <div v-if="activeTab === 'packages'">
      <div class="toolbar">
        <input v-model="pkgSearch" placeholder="Cari package..." style="width: 260px;" />
        <select v-model="pkgArch">
          <option value="">Semua Arch</option>
          <option v-for="a in archList" :key="a" :value="a">{{ a }}</option>
        </select>
        <span class="count-text">{{ filteredPkgs.length }} packages</span>
      </div>
      <div class="card" style="padding: 0; margin-top: 12px; overflow: hidden;">
        <table>
          <thead>
            <tr><th>Package</th><th>Version</th><th>Architecture</th><th>Vendor</th><th>Description</th></tr>
          </thead>
          <tbody>
            <tr v-if="!packages.length"><td colspan="5" style="text-align:center; color:var(--text3); padding: 32px;">Klik "Load Data" untuk mengambil data packages.</td></tr>
            <tr v-for="p in filteredPkgs" :key="p.name + p.version">
              <td>{{ p.name }}</td>
              <td><span class="mono" style="font-size: 11px; color: var(--info);">{{ p.version }}</span></td>
              <td><span class="mono" style="font-size: 11px;">{{ p.architecture || '-' }}</span></td>
              <td style="color: var(--text3);">{{ p.vendor || '-' }}</td>
              <td style="color: var(--text3); font-size: 12px; max-width: 240px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">{{ p.description || '-' }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- OS Info -->
    <div v-if="activeTab === 'os'">
      <div class="card os-info" style="margin-top: 8px;">
        <div v-if="!agent" class="empty-state">No agent info</div>
        <div v-else class="info-grid">
          <div v-for="(val, key) in osFields" :key="key" class="info-row">
            <span class="info-key">{{ key }}</span>
            <span class="info-val mono">{{ val }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Activity History (FIM + SCA) -->
    <div v-if="activeTab === 'history'">
      <div class="history-container" style="margin-top: 12px; display: grid; grid-template-columns: 1fr 1fr; gap: 16px;">
        <div class="card">
          <h3 class="card-title">SCA Scan History</h3>
          <div v-if="!history?.sca?.length" class="empty-state" style="padding: 20px;">No SCA history found. Klik "Load Data".</div>
          <table v-else>
            <thead><tr><th>Policy</th><th>Result</th><th>Date</th></tr></thead>
            <tbody>
              <tr v-for="(h, i) in history.sca" :key="i">
                <td>{{ h.name || '-' }}</td>
                <td><span class="badge" :class="h.result === 'passed' ? 'badge-active' : 'badge-disconnected'">{{ h.result || '-' }}</span></td>
                <td class="mono" style="font-size: 11px;">{{ formatDate(h.end_scan) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <div class="card">
          <h3 class="card-title">FIM Recent Changes</h3>
          <div v-if="!history?.fim?.length" class="empty-state" style="padding: 20px;">No FIM history found. Klik "Load Data".</div>
          <table v-else>
            <thead><tr><th>File</th><th>Event</th><th>Date</th></tr></thead>
            <tbody>
              <tr v-for="(f, i) in history.fim" :key="i">
                <td style="max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" :title="f.file">{{ f.file || '-' }}</td>
                <td><span class="badge fim-event-badge">{{ f.event || '-' }}</span></td>
                <td class="mono" style="font-size: 11px;">{{ formatDate(f.mtime) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- Lifetime Alert History -->
    <div v-if="activeTab === 'alerts'">
      <div class="toolbar" style="margin-top: 8px;">
        <select v-model="alertSevFilter">
          <option value="">All (Critical & High)</option>
          <option value="Critical">Critical Only</option>
          <option value="High">High Only</option>
        </select>
        <input v-model="alertSearch" placeholder="Cari CVE ID / Deskripsi..." style="width: 200px;" />
        <span class="count-text">{{ filteredAlerts.length }} alerts</span>
      </div>
      <div class="card" style="margin-top: 12px; padding: 0; overflow: hidden;">
        <div style="padding: 16px 20px; border-bottom: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center;">
          <div>
            <h3 class="card-title" style="margin: 0;">Lifetime Security Alerts (High & Critical)</h3>
            <p style="font-size: 12px; color: var(--text3); margin-top: 4px;">Termasuk Vulnerability Alerts dan General Alerts (Level 12+).</p>
          </div>
          <div class="alert-summary-badges" v-if="historicalAlerts.length">
            <span class="alert-sum-badge crit">{{ alertCritCount }} Critical</span>
            <span class="alert-sum-badge hi">{{ alertHighCount }} High</span>
          </div>
        </div>
        <table>
          <thead>
            <tr><th>Timestamp</th><th>Category/CVE</th><th>Component</th><th>Severity</th><th>Rule/CVSS</th><th>Description</th></tr>
          </thead>
          <tbody>
            <tr v-if="!historicalAlerts.length"><td colspan="6" style="text-align:center; padding: 32px; color:var(--text3);">Belum ada alert history. Tekan "Load Data".</td></tr>
            <tr v-for="a in paginatedAlerts" :key="a._id">
              <td class="mono" style="font-size:11px; white-space: nowrap;">{{ formatDate(a._source?.timestamp) }}</td>
              <td>
                <a v-if="a._source?.data?.vulnerability?.cve" :href="`https://nvd.nist.gov/vuln/detail/${a._source?.data?.vulnerability?.cve}`" target="_blank" class="cve-link">{{ a._source.data.vulnerability.cve }}</a>
                <span v-else class="badge" style="background:var(--bg3); color:var(--text3);">Rule {{ a._source?.rule?.id }}</span>
              </td>
              <td>
                <template v-if="a._source?.data?.vulnerability?.package?.name">
                  {{ a._source.data.vulnerability.package.name }}
                  <span class="mono" style="color:var(--text3); font-size:10px">{{ a._source.data.vulnerability.package.version }}</span>
                </template>
                <template v-else>
                  <span class="mono" style="color:var(--text2); font-size:11px">{{ (a._source?.rule?.groups || []).join(', ') || '-' }}</span>
                </template>
              </td>
              <td><span class="badge" :class="`badge-${getAlertSeverity(a).toLowerCase()}`">{{ getAlertSeverity(a) }}</span></td>
              <td class="mono">{{ a._source?.data?.vulnerability?.cvss?.cvss3?.base_score || `Lvl ${a._source?.rule?.level || '-'}` }}</td>
              <td style="max-width: 250px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: 11px; color: var(--text3);" :title="a._source?.data?.vulnerability?.title || a._source?.rule?.description">{{ a._source?.data?.vulnerability?.title || a._source?.rule?.description || '-' }}</td>
            </tr>
          </tbody>
        </table>
        <div class="pagination" v-if="alertTotalPages > 1">
          <button class="btn btn-ghost" :disabled="alertPage === 1" @click="alertPage--">←</button>
          <span class="page-info">{{ alertPage }} / {{ alertTotalPages }}</span>
          <button class="btn btn-ghost" :disabled="alertPage === alertTotalPages" @click="alertPage++">→</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useAppStore } from '../stores/app'
import { getAlertHistoryDetails } from '../utils/indexerApi'

const route = useRoute()
const store = useAppStore()
const agentId = route.params.id
const loading = ref(false)
const activeTab = ref('vulns')
const vulns = ref([])
const packages = ref([])
const history = ref({ sca: [], fim: [] })
const historicalAlerts = ref([])
const vulnSearch = ref('')
const vulnSeverity = ref('')
const pkgSearch = ref('')
const pkgArch = ref('')
const alertSevFilter = ref('')
const alertSearch = ref('')
const alertPage = ref(1)
const ALERTS_PER_PAGE = 50

const agent = computed(() => store.agents.find(a => a.id === agentId))

// Helper for alert severity
function getAlertSeverity(a) {
  if (a._source?.data?.vulnerability?.severity) {
    return a._source.data.vulnerability.severity
  }
  const lvl = a._source?.rule?.level || 0
  if (lvl >= 15) return 'Critical'
  if (lvl >= 12) return 'High'
  return 'Medium'
}

// Check if there are recent critical alerts (< 7 days)
const hasRecentCritical = computed(() => {
  const sevenDaysAgo = Date.now() - 7 * 24 * 60 * 60 * 1000
  return historicalAlerts.value.some(a => {
    const ts = new Date(a._source?.timestamp).getTime()
    return ts > sevenDaysAgo && getAlertSeverity(a) === 'Critical'
  })
})

const tabs = computed(() => [
  { key: 'vulns', label: 'Vulnerabilities', count: vulns.value.length },
  { key: 'packages', label: 'Packages', count: packages.value.length },
  { key: 'history', label: 'Activity History' },
  { key: 'alerts', label: 'Alert History', count: historicalAlerts.value.length, alert: hasRecentCritical.value },
  { key: 'os', label: 'OS Info' }
])

onMounted(async () => {
  if (!store.agents.length) await store.initialize()
  if (store.vulnsByAgent[agentId]) vulns.value = store.vulnsByAgent[agentId]
  if (store.packagesByAgent[agentId]) packages.value = store.packagesByAgent[agentId]
  if (store.historyByAgent[agentId]) history.value = store.historyByAgent[agentId]
})

async function loadData() {
  loading.value = true
  const [v, p, h, alerts] = await Promise.all([
    store.fetchVulnerabilities(agentId),
    store.fetchPackages(agentId),
    store.fetchHistory(agentId),
    getAlertHistoryDetails(agentId).catch(() => [])
  ])
  vulns.value = v
  packages.value = p
  history.value = h
  historicalAlerts.value = alerts
  loading.value = false
}

// Alert history computed
const alertCritCount = computed(() => historicalAlerts.value.filter(a => getAlertSeverity(a) === 'Critical').length)
const alertHighCount = computed(() => historicalAlerts.value.filter(a => getAlertSeverity(a) === 'High').length)

const filteredAlerts = computed(() => {
  let list = historicalAlerts.value
  if (alertSevFilter.value) {
    list = list.filter(a => getAlertSeverity(a) === alertSevFilter.value)
  }
  if (alertSearch.value) {
    const q = alertSearch.value.toLowerCase()
    list = list.filter(a => 
      a._source?.data?.vulnerability?.cve?.toLowerCase().includes(q) ||
      a._source?.rule?.description?.toLowerCase().includes(q)
    )
  }
  return list
})

watch([alertSevFilter, alertSearch], () => { alertPage.value = 1 })

const alertTotalPages = computed(() => Math.ceil(filteredAlerts.value.length / ALERTS_PER_PAGE))
const paginatedAlerts = computed(() => filteredAlerts.value.slice((alertPage.value - 1) * ALERTS_PER_PAGE, alertPage.value * ALERTS_PER_PAGE))

const filteredVulns = computed(() => {
  return vulns.value.filter(v => {
    const q = vulnSearch.value.toLowerCase()
    const matchQ = !q || v.cve?.toLowerCase().includes(q) || v.name?.toLowerCase().includes(q)
    const matchS = !vulnSeverity.value || v.severity?.toLowerCase() === vulnSeverity.value.toLowerCase()
    return matchQ && matchS
  })
})

const archList = computed(() => [...new Set(packages.value.map(p => p.architecture).filter(Boolean))].sort())

const filteredPkgs = computed(() => {
  return packages.value.filter(p => {
    const q = pkgSearch.value.toLowerCase()
    const matchQ = !q || p.name?.toLowerCase().includes(q)
    const matchA = !pkgArch.value || p.architecture === pkgArch.value
    return matchQ && matchA
  })
})

const osFields = computed(() => {
  if (!agent.value) return {}
  const a = agent.value
  return {
    'Agent ID': a.id,
    'Name': a.name,
    'IP Address': a.ip,
    'OS Name': a.os?.name,
    'OS Version': a.os?.version,
    'OS Platform': a.os?.platform,
    'OS Arch': a.os?.arch,
    'Kernel': a.os?.uname,
    'Agent Version': a.version,
    'Registered': a.dateAdd,
    'Last Keep Alive': a.lastKeepAlive,
  }
})

function statusBadge(s) {
  if (s === 'active') return 'badge-active'
  if (s === 'disconnected') return 'badge-disconnected'
  return 'badge-never'
}

function calculateAge(dateStr) {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  const now = new Date()
  const diffDays = Math.floor((now - date) / (1000 * 60 * 60 * 24))
  if (diffDays === 0) return 'Today'
  if (diffDays < 30) return `${diffDays} days`
  if (diffDays < 365) return `${Math.floor(diffDays / 30)} months`
  return `${Math.floor(diffDays / 365)} years`
}

function formatDate(dateStr) {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('id-ID', { 
    day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' 
  })
}
</script>

<style scoped>
.page { padding: 28px; max-width: 1200px; }
.page-header { display: flex; align-items: flex-end; justify-content: space-between; margin-bottom: 20px; }
.page-header h2 { font-family: var(--font-display); font-size: 20px; font-weight: 700; }
.meta { display: flex; align-items: center; gap: 8px; margin-top: 4px; font-size: 12px; color: var(--text3); }
.sep { color: var(--border2); }
.mono { font-family: var(--font-mono); font-size: 12px; }

.tabs { display: flex; gap: 2px; border-bottom: 1px solid var(--border); margin-bottom: 16px; }
.tab { padding: 9px 16px; font-size: 13px; color: var(--text3); cursor: pointer; background: none; border: none; border-bottom: 2px solid transparent; display: flex; align-items: center; gap: 7px; transition: all 0.15s; }
.tab:hover { color: var(--text); }
.tab.active { color: var(--accent); border-bottom-color: var(--accent); }
.tab-count { background: var(--bg3); color: var(--text3); font-family: var(--font-mono); font-size: 10px; padding: 1px 6px; border-radius: 10px; }
.tab.active .tab-count { background: rgba(59,130,246,0.15); color: #60a5fa; }
.tab-alert-dot { width: 7px; height: 7px; border-radius: 50%; background: var(--critical); animation: pulse-dot 2s infinite; }
@keyframes pulse-dot { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }

.toolbar { display: flex; align-items: center; gap: 10px; }
.count-text { font-size: 11px; color: var(--text3); margin-left: auto; font-family: var(--font-mono); }
.cve-link { color: var(--accent); font-family: var(--font-mono); font-size: 12px; }
.cve-link:hover { text-decoration: underline; }

.info-grid { display: flex; flex-direction: column; gap: 0; }
.info-row { display: flex; padding: 10px 0; border-bottom: 1px solid var(--border); gap: 16px; align-items: baseline; }
.info-row:last-child { border-bottom: none; }
.info-key { font-size: 12px; color: var(--text3); width: 160px; flex-shrink: 0; }
.info-val { font-size: 13px; color: var(--text); }

.age-badge { background: rgba(59,130,246,0.1); color: #60a5fa; padding: 2px 8px; border-radius: 4px; font-weight: 600; }
.card-title { font-size: 12px; font-weight: 600; color: var(--text3); margin-bottom: 12px; text-transform: uppercase; letter-spacing: 0.05em; }
.fim-event-badge { background: var(--bg3); color: var(--text); font-size: 11px; }

.alert-summary-badges { display: flex; gap: 8px; }
.alert-sum-badge { font-family: var(--font-mono); font-size: 11px; padding: 4px 10px; border-radius: 6px; font-weight: 600; }
.alert-sum-badge.crit { background: rgba(239,68,68,0.12); color: #f87171; }
.alert-sum-badge.hi { background: rgba(249,115,22,0.1); color: #fb923c; }

.pagination { display: flex; align-items: center; justify-content: center; gap: 12px; padding: 12px; border-top: 1px solid var(--border); }
.page-info { font-family: var(--font-mono); font-size: 12px; color: var(--text3); }
</style>
