<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h2>Dashboard</h2>
        <p class="sub">Overview patch & vulnerability status</p>
      </div>
      <div class="header-actions">
        <span class="last-update" v-if="store.lastFetch">
          Updated {{ timeAgo(store.lastFetch) }}
        </span>
        <button class="btn btn-ghost" @click="refresh" :disabled="store.loading">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" :class="{ spin: store.loading }"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg>
          Refresh
        </button>
      </div>
    </div>

    <div class="stat-grid">
      <div class="stat-card">
        <div class="stat-label">Total Agents</div>
        <div class="stat-value">{{ store.totalAgents }}</div>
        <div class="stat-sub"><span class="badge badge-active">{{ store.activeAgents }} active</span></div>
      </div>
      <div class="stat-card critical">
        <div class="stat-label">Critical CVEs</div>
        <div class="stat-value">{{ store.criticalCount }}</div>
        <div class="stat-sub">Needs immediate action</div>
      </div>
      <div class="stat-card high">
        <div class="stat-label">High CVEs</div>
        <div class="stat-value">{{ store.highCount }}</div>
        <div class="stat-sub">Patch ASAP</div>
      </div>
      <div class="stat-card medium">
        <div class="stat-label">Medium / Low</div>
        <div class="stat-value">{{ store.mediumCount + store.lowCount }}</div>
        <div class="stat-sub">Monitor & schedule</div>
      </div>
    </div>

    <div class="charts-grid">
      <div class="card">
        <h3 class="card-title">Severity Distribution</h3>
        <div class="chart-wrap">
          <Doughnut v-if="donutData" :data="donutData" :options="donutOptions" />
          <div v-else class="empty-state">Belum ada data vulnerability.<br><small>Klik Refresh atau buka halaman Vulnerabilities.</small></div>
        </div>
      </div>

      <div class="card">
        <h3 class="card-title">Agents Status</h3>
        <div class="chart-wrap">
          <Bar v-if="barData" :data="barData" :options="barOptions" />
          <div v-else class="empty-state">Loading agents...</div>
        </div>
      </div>
    </div>

    <!-- Recent Critical & High Alerts Section -->
    <div class="card" style="margin-top: 16px;">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px;">
        <h3 class="card-title" style="margin: 0;">Recent Critical & High Alerts</h3>
        <button v-if="!hasAlertData" class="btn btn-primary btn-sm" @click="loadAlertHistory" :disabled="loadingAlerts">
          {{ loadingAlerts ? 'Loading...' : 'Load Alert History' }}
        </button>
        <span v-else class="count-text">From Wazuh Indexer</span>
      </div>
      <div v-if="!hasAlertData && !loadingAlerts" class="empty-state" style="padding: 24px;">
        Klik <strong>Load Alert History</strong> untuk menarik ringkasan alert dari Indexer.
      </div>
      <table v-else-if="alertSummaryRows.length">
        <thead>
          <tr><th>Agent</th><th>Status</th><th>Critical Alerts</th><th>High Alerts</th><th>Total</th></tr>
        </thead>
        <tbody>
          <tr v-for="row in alertSummaryRows" :key="row.id" @click="$router.push(`/agents/${row.id}`)" style="cursor:pointer" class="clickable-row">
            <td><span class="mono">{{ row.name }}</span></td>
            <td><span class="badge" :class="`badge-${row.status}`">{{ row.status }}</span></td>
            <td><span style="color: var(--critical); font-weight: 600;">{{ row.critical }}</span></td>
            <td><span style="color: var(--high);">{{ row.high }}</span></td>
            <td class="mono">{{ row.total }}</td>
          </tr>
        </tbody>
      </table>
      <div v-else-if="hasAlertData" class="empty-state" style="padding: 24px;">
        Tidak ada alert Critical/High yang ditemukan di Indexer.
      </div>
    </div>

    <div class="card" style="margin-top: 16px;">
      <h3 class="card-title" style="margin-bottom: 14px;">Top Vulnerable Agents</h3>
      <div v-if="topAgents.length === 0" class="empty-state">
        Klik <strong>Load Vulnerabilities</strong> untuk melihat data.
        <button class="btn btn-primary" style="margin-top: 12px;" @click="loadVulns">Load Vulnerabilities</button>
      </div>
      <table v-else>
        <thead>
          <tr><th>Agent</th><th>OS</th><th>Status</th><th>Critical</th><th>High</th><th>Total</th></tr>
        </thead>
        <tbody>
          <tr v-for="a in topAgents" :key="a.id" @click="$router.push(`/agents/${a.id}`)" style="cursor:pointer" class="clickable-row">
            <td><span class="mono">{{ a.name }}</span></td>
            <td>{{ a.os?.name || '-' }}</td>
            <td><span class="badge" :class="`badge-${a.status}`">{{ a.status }}</span></td>
            <td><span style="color: var(--critical); font-weight: 600;">{{ a.criticalCount }}</span></td>
            <td><span style="color: var(--high);">{{ a.highCount }}</span></td>
            <td>{{ a.totalVulns }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { Doughnut, Bar } from 'vue-chartjs'
import { Chart as ChartJS, ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement } from 'chart.js'
import { useAppStore } from '../stores/app'
import { getAllAlertHistorySum } from '../utils/indexerApi'

ChartJS.register(ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement)

const store = useAppStore()
const loadingAlerts = ref(false)

function timeAgo(date) {
  const diff = Math.floor((Date.now() - date.getTime()) / 1000)
  if (diff < 60) return `${diff}s ago`
  if (diff < 3600) return `${Math.floor(diff/60)}m ago`
  return `${Math.floor(diff/3600)}h ago`
}

async function refresh() {
  await store.initialize()
}

async function loadVulns() {
  await store.fetchAllVulnerabilities()
}

async function loadAlertHistory() {
  loadingAlerts.value = true
  try {
    const data = await getAllAlertHistorySum()
    store.indexerAlertsSummary = data || {}
  } finally {
    loadingAlerts.value = false
  }
}

onMounted(async () => {
  if (!store.agents.length) await store.initialize()
})

const hasAlertData = computed(() => Object.keys(store.indexerAlertsSummary).length > 0)

const alertSummaryRows = computed(() => {
  const summaryMap = store.indexerAlertsSummary
  if (!summaryMap || !Object.keys(summaryMap).length) return []
  
  return store.agents
    .filter(a => summaryMap[a.id])
    .map(a => {
      const s = summaryMap[a.id]
      return {
        id: a.id,
        name: a.name,
        status: a.status,
        critical: s.critical || 0,
        high: s.high || 0,
        total: s.total || 0
      }
    })
    .sort((a, b) => b.critical - a.critical)
    .slice(0, 5)
})

const donutData = computed(() => {
  const total = store.criticalCount + store.highCount + store.mediumCount + store.lowCount
  if (!total) return null
  return {
    labels: ['Critical', 'High', 'Medium', 'Low'],
    datasets: [{
      data: [store.criticalCount, store.highCount, store.mediumCount, store.lowCount],
      backgroundColor: ['#ef4444', '#f97316', '#eab308', '#22c55e'],
      borderWidth: 0,
      hoverOffset: 4
    }]
  }
})

const donutOptions = {
  responsive: true, maintainAspectRatio: false,
  plugins: {
    legend: { position: 'right', labels: { color: '#8892a4', font: { family: 'IBM Plex Mono', size: 11 }, padding: 14, boxWidth: 12 } }
  },
  cutout: '68%'
}

const barData = computed(() => {
  const active = store.activeAgents
  const inactive = store.totalAgents - active
  return {
    labels: ['Active', 'Inactive / Never Connected'],
    datasets: [{
      data: [active, inactive],
      backgroundColor: ['rgba(34,197,94,0.6)', 'rgba(239,68,68,0.5)'],
      borderColor: ['#22c55e', '#ef4444'],
      borderWidth: 1,
      borderRadius: 4
    }]
  }
})

const barOptions = {
  responsive: true, maintainAspectRatio: false,
  plugins: { legend: { display: false } },
  scales: {
    x: { ticks: { color: '#8892a4', font: { family: 'IBM Plex Mono', size: 11 } }, grid: { color: '#1e2636' } },
    y: { ticks: { color: '#8892a4', font: { size: 11 } }, grid: { color: '#1e2636' } }
  }
}

const topAgents = computed(() => {
  return store.agents.map(a => {
    const vulns = store.vulnsByAgent[a.id] || []
    return {
      ...a,
      totalVulns: vulns.length,
      criticalCount: vulns.filter(v => v.severity?.toLowerCase() === 'critical').length,
      highCount: vulns.filter(v => v.severity?.toLowerCase() === 'high').length
    }
  }).filter(a => a.totalVulns > 0).sort((a, b) => b.criticalCount - a.criticalCount).slice(0, 5)
})
</script>

<style scoped>
.page { padding: 28px; max-width: 1200px; }
.page-header { display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 24px; }
.page-header h2 { font-family: var(--font-display); font-size: 20px; font-weight: 700; }
.sub { color: var(--text3); font-size: 12px; margin-top: 2px; }
.header-actions { display: flex; align-items: center; gap: 10px; }
.last-update { font-size: 11px; color: var(--text3); font-family: var(--font-mono); }

.stat-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 16px; }
.stat-card { background: var(--bg2); border: 1px solid var(--border); border-radius: var(--radius-lg); padding: 18px 20px; }
.stat-card.critical { border-color: rgba(239,68,68,0.3); }
.stat-card.high { border-color: rgba(249,115,22,0.25); }
.stat-card.medium { border-color: rgba(234,179,8,0.2); }
.stat-label { font-size: 11px; font-weight: 500; color: var(--text3); letter-spacing: 0.05em; text-transform: uppercase; font-family: var(--font-mono); margin-bottom: 6px; }
.stat-value { font-family: var(--font-display); font-size: 32px; font-weight: 700; line-height: 1; }
.stat-card.critical .stat-value { color: var(--critical); }
.stat-card.high .stat-value { color: var(--high); }
.stat-card.medium .stat-value { color: var(--medium); }
.stat-sub { margin-top: 6px; font-size: 12px; color: var(--text3); }

.charts-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.card-title { font-size: 13px; font-weight: 600; color: var(--text2); margin-bottom: 16px; text-transform: uppercase; letter-spacing: 0.05em; font-family: var(--font-mono); }
.chart-wrap { height: 220px; display: flex; align-items: center; justify-content: center; }
.empty-state { text-align: center; color: var(--text3); font-size: 13px; line-height: 1.8; display: flex; flex-direction: column; align-items: center; }
.mono { font-family: var(--font-mono); font-size: 12px; }
.count-text { font-size: 11px; color: var(--text3); font-family: var(--font-mono); }
.spin { animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

.clickable-row { cursor: pointer; transition: background 0.15s; }
.clickable-row:hover { background: var(--bg3); }

.btn-sm { padding: 6px 14px; font-size: 12px; }
</style>
