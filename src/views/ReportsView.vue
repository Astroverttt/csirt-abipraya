<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h2>Reports & Export</h2>
        <p class="sub">Generate laporan patch management</p>
      </div>
      <button class="btn btn-primary" @click="syncAll" :disabled="store.loading">
        <svg v-if="!store.loading" style="margin-right:6px" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M23 4v6h-6M1 20v-6h6M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15"/></svg>
        {{ store.loading ? 'Syncing...' : 'Sync All Data' }}
      </button>
    </div>

    <div class="report-grid">
      <!-- CVE Summary Report -->
      <div class="card report-card">
        <div class="report-icon cve-icon">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M12 2L3 7v5c0 5.25 3.75 10.15 9 11.35C17.25 22.15 21 17.25 21 12V7L12 2z"/></svg>
        </div>
        <h3>CVE Summary Report</h3>
        <p>Rangkuman semua CVE dari seluruh agent, dikelompokkan berdasarkan severity.</p>
        <div class="report-options">
          <label><input type="checkbox" v-model="opts.cve.critical" /> Critical</label>
          <label><input type="checkbox" v-model="opts.cve.high" /> High</label>
          <label><input type="checkbox" v-model="opts.cve.medium" /> Medium</label>
          <label><input type="checkbox" v-model="opts.cve.low" /> Low</label>
        </div>
        <div class="report-actions">
          <button class="btn btn-ghost" @click="exportCVECSV">Export CSV</button>
          <button class="btn btn-primary" @click="exportCVEJSON">Export JSON</button>
        </div>
      </div>

      <!-- Patch Status Report -->
      <div class="card report-card">
        <div class="report-icon patch-icon">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="2" y="3" width="20" height="14" rx="2"/><path d="M8 21h8M12 17v4"/></svg>
        </div>
        <h3>Patch Status per Agent</h3>
        <p>Status vulnerability tiap agent dengan jumlah CVE per severity level.</p>
        <div class="report-options">
          <label><input type="radio" v-model="opts.patch.format" value="csv" /> CSV</label>
          <label><input type="radio" v-model="opts.patch.format" value="json" /> JSON</label>
        </div>
        <div class="report-actions">
          <button class="btn btn-primary" @click="exportPatchStatus">Export {{ opts.patch.format.toUpperCase() }}</button>
        </div>
      </div>

      <!-- Package Inventory -->
      <div class="card report-card">
        <div class="report-icon pkg-icon">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M21 16V8a2 2 0 00-1-1.73l-7-4a2 2 0 00-2 0l-7 4A2 2 0 003 8v8a2 2 0 001 1.73l7 4a2 2 0 002 0l7-4A2 2 0 0021 16z"/><polyline points="3.27 6.96 12 12.01 20.73 6.96"/><line x1="12" y1="22.08" x2="12" y2="12"/></svg>
        </div>
        <h3>Package Inventory</h3>
        <p>Daftar lengkap semua software yang terinstall per agent.</p>
        <div class="report-options">
          <select v-model="opts.pkg.agentId" style="width: 100%;">
            <option value="">Semua agent (merge)</option>
            <option v-for="a in store.agents" :key="a.id" :value="a.id">{{ a.name }}</option>
          </select>
        </div>
        <div class="report-actions">
          <button class="btn btn-primary" @click="exportPackages">Export CSV</button>
        </div>
      </div>
      <!-- Master Audit Report -->
      <div class="card report-card" style="grid-column: span 3; border: 1px solid rgba(59,130,246,0.3); background: rgba(59,130,246,0.02);">
        <div style="display: flex; align-items: center; gap: 16px; width: 100%;">
          <div class="report-icon" style="background: rgba(59,130,246,0.15); color: #60a5fa; flex-shrink: 0;">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M12 2L3 7v5c0 5.25 3.75 10.15 9 11.35C17.25 22.15 21 17.25 21 12V7L12 2z"/><path d="M8 12l3 3 5-5"/></svg>
          </div>
          <div style="flex: 1;">
            <h3 style="margin:0; font-size: 15px;">Master Audit Report (Custom Format)</h3>
            <p style="margin:4px 0 0; font-size: 12px; color: var(--text3);">Format lengkap mencakup Hostname, IP, OS, HW (CPU/RAM), dan Vulnerability Details.</p>
          </div>
          <button class="btn btn-primary" @click="exportMasterAudit" :disabled="store.loading">
            Export Master CSV
          </button>
        </div>
      </div>
    </div>

    <!-- Live preview table -->
    <div class="card" style="margin-top: 20px;">
      <div class="preview-header">
        <h3 class="card-title">Preview Data</h3>
        <div style="display: flex; gap: 8px;">
          <button class="btn btn-ghost" @click="previewType = 'vulns'" :class="{ 'btn-primary': previewType === 'vulns' }">Vulnerabilities</button>
          <button class="btn btn-ghost" @click="previewType = 'agents'" :class="{ 'btn-primary': previewType === 'agents' }">Agents</button>
        </div>
      </div>

      <div v-if="previewType === 'agents'">
        <div v-if="!hasAnyMetrics" class="call-to-sync">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
          Data metric masih 0. Klik tombol <strong>Sync All Data</strong> di pojok kanan atas untuk menarik semua laporan vulnerability dan riwayat Indexer.
        </div>
        <table>
          <thead><tr><th>Agent ID</th><th>Name</th><th>Status</th><th>Curr. Crit</th><th>Curr. High</th><th>Lifetime Crit</th><th>Lifetime High</th><th>Total Lifetime</th></tr></thead>
          <tbody>
            <tr v-if="!store.agents.length"><td colspan="8" style="text-align:center; padding: 30px; color: var(--text3);">Belum ada data agent.</td></tr>
            <tr v-for="row in paginatedAgents" :key="row.id" @click="$router.push(`/agents/${row.id}`)" style="cursor: pointer;" class="clickable-row">
              <td class="mono">{{ row.id }}</td><td>{{ row.name }}</td>
              <td><span class="badge" :class="row.status === 'active' ? 'badge-active' : 'badge-disconnected'">{{ row.status }}</span></td>
              <td style="color:var(--critical); font-weight:600;">{{ row.critical }}</td>
              <td style="color:var(--high);">{{ row.high }}</td>
              <td style="color:var(--critical); font-weight:600; background: rgba(239,68,68,0.05);">{{ row.lifetimeCritical }}</td>
              <td style="color:var(--high); background: rgba(249,115,22,0.05);">{{ row.lifetimeHigh }}</td>
              <td class="mono" style="color:var(--text2);">{{ row.lifetimeTotal }}</td>
            </tr>
          </tbody>
        </table>
        
        <div class="pagination" v-if="totalPagesAgents > 1">
          <button class="btn btn-ghost" :disabled="pageAgents === 1" @click="pageAgents--">←</button>
          <span class="page-info">Halaman {{ pageAgents }} dari {{ totalPagesAgents }} ({{ agentSummaryRows.length }} total)</span>
          <button class="btn btn-ghost" :disabled="pageAgents === totalPagesAgents" @click="pageAgents++">→</button>
        </div>
      </div>

      <div v-if="previewType === 'vulns'">
        <table>
          <thead><tr><th>Agent</th><th>CVE ID</th><th>Package</th><th>Version</th><th>Severity</th><th>CVSS</th></tr></thead>
          <tbody>
            <tr v-if="!allVulnsPreview.length"><td colspan="6" style="text-align:center; padding: 30px; color: var(--text3);">Belum ada data CVE. Load dari halaman Vulnerabilities terlebih dahulu.</td></tr>
            <tr v-for="v in paginatedVulns" :key="`${v._agentId}_${v.cve}`" @click="$router.push(`/agents/${v._agentId}`)" style="cursor: pointer;" class="clickable-row">
              <td class="mono" style="font-size: 11px; color: var(--info);">{{ agentName(v._agentId) }}</td>
              <td><span class="mono" style="color: var(--accent);">{{ v.cve }}</span></td>
              <td>{{ v.name }}</td>
              <td class="mono">{{ v.version }}</td>
              <td><span class="badge" :class="`badge-${v.severity?.toLowerCase()}`">{{ v.severity }}</span></td>
              <td class="mono">{{ v.cvss || '-' }}</td>
            </tr>
          </tbody>
        </table>
        
        <div class="pagination" v-if="totalPagesVulns > 1">
          <button class="btn btn-ghost" :disabled="pageVulns === 1" @click="pageVulns--">←</button>
          <span class="page-info">Halaman {{ pageVulns }} dari {{ totalPagesVulns }} ({{ allVulnsPreview.length }} total)</span>
          <button class="btn btn-ghost" :disabled="pageVulns === totalPagesVulns" @click="pageVulns++">→</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useAppStore } from '../stores/app'

const store = useAppStore()
const previewType = ref('agents')
const pageAgents = ref(1)
const pageVulns = ref(1)
const PER_PAGE = 10

const opts = ref({
  cve: { critical: true, high: true, medium: true, low: false },
  patch: { format: 'csv' },
  pkg: { agentId: '' }
})

watch(previewType, () => {
  pageAgents.value = 1
  pageVulns.value = 1
})

onMounted(async () => { if (!store.agents.length) await store.initialize() })

function agentName(id) { return store.agents.find(a => a.id === id)?.name || id }

const allVulnsPreview = computed(() =>
  Object.entries(store.vulnsByAgent).flatMap(([agentId, vulns]) =>
    vulns.map(v => ({ ...v, _agentId: agentId }))
  )
)

const hasAnyMetrics = computed(() => {
  return Object.keys(store.vulnsByAgent).length > 0 || Object.keys(store.indexerAlertsSummary).length > 0
})

const agentSummaryRows = computed(() =>
  store.agents.map(a => {
    const vulns = store.vulnsByAgent[a.id] || []
    const idx = store.indexerAlertsSummary[a.id] || { critical: 0, high: 0, total: 0 }
    return {
      id: a.id, name: a.name, ip: a.ip || '-', status: a.status,
      os: a.os?.name || a.os?.platform || '-',
      critical: vulns.filter(v => v.severity?.toLowerCase() === 'critical').length,
      high: vulns.filter(v => v.severity?.toLowerCase() === 'high').length,
      medium: vulns.filter(v => v.severity?.toLowerCase() === 'medium').length,
      low: vulns.filter(v => v.severity?.toLowerCase() === 'low').length,
      total: vulns.length,
      lifetimeCritical: idx.critical,
      lifetimeHigh: idx.high,
      lifetimeTotal: idx.total
    }
  })
)

const totalPagesAgents = computed(() => Math.ceil(agentSummaryRows.value.length / PER_PAGE))
const paginatedAgents = computed(() => agentSummaryRows.value.slice((pageAgents.value - 1) * PER_PAGE, pageAgents.value * PER_PAGE))

const totalPagesVulns = computed(() => Math.ceil(allVulnsPreview.value.length / PER_PAGE))
const paginatedVulns = computed(() => allVulnsPreview.value.slice((pageVulns.value - 1) * PER_PAGE, pageVulns.value * PER_PAGE))

function downloadFile(content, filename, type = 'text/csv') {
  const blob = new Blob([content], { type })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url; a.download = filename; a.click()
  URL.revokeObjectURL(url)
}

function toCSV(headers, rows) {
  return [headers.join(','), ...rows.map(r => r.map(v => {
    const s = String(v ?? '')
    return `"${s.replace(/"/g, '""')}"`
  }).join(','))].join('\n')
}

async function syncAll() {
  await store.fetchAllData()
}

function exportCVECSV() {
  const sevFilter = ['critical', 'high', 'medium', 'low'].filter(s => opts.value.cve[s])
  const data = allVulnsPreview.value.filter(v => sevFilter.includes(v.severity?.toLowerCase()))
  const csv = toCSV(['Agent', 'CVE_ID', 'Package', 'Version', 'Severity', 'CVSS', 'Condition'],
    data.map(v => [agentName(v._agentId), v.cve, v.name, v.version, v.severity, v.cvss, v.condition]))
  downloadFile(csv, `cve_report_${new Date().toISOString().slice(0,10)}.csv`)
}

function exportCVEJSON() {
  const sevFilter = ['critical', 'high', 'medium', 'low'].filter(s => opts.value.cve[s])
  const data = allVulnsPreview.value.filter(v => sevFilter.includes(v.severity?.toLowerCase()))
    .map(v => ({ agent: agentName(v._agentId), agentId: v._agentId, cve: v.cve, package: v.name, version: v.version, severity: v.severity, cvss: v.cvss }))
  downloadFile(JSON.stringify(data, null, 2), `cve_report_${new Date().toISOString().slice(0,10)}.json`, 'application/json')
}

function exportPatchStatus() {
  const rows = agentSummaryRows.value
  if (opts.value.patch.format === 'csv') {
    const csv = toCSV(['Agent ID', 'Name', 'IP', 'Status', 'OS', 'Critical', 'High', 'Medium', 'Low', 'Total'],
      rows.map(r => [r.id, r.name, r.ip, r.status, r.os, r.critical, r.high, r.medium, r.low, r.total]))
    downloadFile(csv, `patch_status_${new Date().toISOString().slice(0,10)}.csv`)
  } else {
    downloadFile(JSON.stringify(rows, null, 2), `patch_status_${new Date().toISOString().slice(0,10)}.json`, 'application/json')
  }
}

async function exportPackages() {
  const agentId = opts.value.pkg.agentId
  
  if (agentId) {
    if (!store.packagesByAgent[agentId]) await store.fetchPackages(agentId)
    const pkgs = (store.packagesByAgent[agentId] || []).map(p => ({ ...p, _agent: agentName(agentId) }))
    const csv = toCSV(['Agent', 'Name', 'Version', 'Architecture', 'Vendor', 'Description'],
      pkgs.map(p => [p._agent, p.name, p.version, p.architecture, p.vendor, p.description]))
    downloadFile(csv, `packages_${agentName(agentId)}_${new Date().toISOString().slice(0,10)}.csv`)
  } else {
    // For all agents, we must fetch if needed
    store.loading = true
    try {
      for (const a of store.agents) {
        if (!store.packagesByAgent[a.id]) await store.fetchPackages(a.id)
      }
      const pkgs = Object.entries(store.packagesByAgent).flatMap(([id, pkgs]) => pkgs.map(p => ({ ...p, _agent: agentName(id) })))
      const csv = toCSV(['Agent', 'Name', 'Version', 'Architecture', 'Vendor', 'Description'],
        pkgs.map(p => [p._agent, p.name, p.version, p.architecture, p.vendor, p.description]))
      downloadFile(csv, `packages_all_agents_${new Date().toISOString().slice(0,10)}.csv`)
    } finally {
      store.loading = false
    }
  }
}

async function exportMasterAudit() {
  store.loading = true
  try {
    // 1. Ensure we have vulnerability data for all agents
    if (Object.keys(store.vulnsByAgent).length === 0) {
      await store.fetchAllVulnerabilities()
    }

    // 2. Fetch hardware for all agents sequentially to avoid 429
    for (const a of store.agents) {
      if (!store.hardwareByAgent[a.id]) {
        await store.fetchHardware(a.id)
      }
    }

    const headers = [
      'No', 'Nama Server', 'IP Address', 'Tipe IP', 'Lokasi / Cloud',
      'OS Saat Ini', 'Versi Terbaru', 'Status OS', 'Vulnerability',
      'Vulnerability Details', 'CPU Cores', 'Memory (GB)', 'Disk Total (GB)', 'PIC', 'Status'
    ]

    const rows = store.agents.map((a, index) => {
      const vulns = (store.vulnsByAgent && store.vulnsByAgent[a.id]) || []
      const hw = (store.hardwareByAgent && store.hardwareByAgent[a.id]) || {}
      const cveDetails = vulns.slice(0, 5).map(v => v.cve).join(', ') + (vulns.length > 5 ? '...' : '')

      // Extract RAM (Wazuh returns in KB)
      const memGB = hw.ram_total ? (parseInt(hw.ram_total) / (1024 * 1024)).toFixed(1) : '-'

      return [
        index + 1,
        a.name,
        a.ip || '-',
        a.ip?.startsWith('10.') || a.ip?.startsWith('192.') ? 'Internal' : 'Public',
        'On-Premise', 
        `${a.os?.name} ${a.os?.version}`,
        '-', 
        a.status === 'active' ? 'Running' : 'Offline',
        vulns.length,
        cveDetails || 'None',
        hw.cpu?.cores || '-',
        memGB,
        '-', 
        'IT Security', 
        'Audited'
      ]
    })

    const csv = toCSV(headers, rows)
    downloadFile(csv, `WAZUH_MASTER_AUDIT_${new Date().toISOString().slice(0,10)}.csv`)
  } catch (err) {
    console.error('Audit export failed:', err)
    alert('Gagal membuat laporan audit. Silakan cek koneksi ke Wazuh API.')
  } finally {
    store.loading = false
  }
}
</script>

<style scoped>
.page { padding: 28px; max-width: 1200px; }
.page-header { margin-bottom: 20px; }
.page-header h2 { font-family: var(--font-display); font-size: 20px; font-weight: 700; }
.sub { color: var(--text3); font-size: 12px; margin-top: 2px; }
.mono { font-family: var(--font-mono); font-size: 12px; }
.card-title { font-size: 13px; font-weight: 600; color: var(--text2); text-transform: uppercase; letter-spacing: 0.05em; font-family: var(--font-mono); }

.report-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; }
.report-card { display: flex; flex-direction: column; gap: 10px; }
.report-card h3 { font-family: var(--font-display); font-size: 14px; font-weight: 600; }
.report-card p { font-size: 12px; color: var(--text3); line-height: 1.6; flex: 1; }
.report-icon { width: 36px; height: 36px; border-radius: var(--radius); display: flex; align-items: center; justify-content: center; }
.cve-icon { background: rgba(239,68,68,0.12); color: #f87171; }
.patch-icon { background: rgba(59,130,246,0.12); color: #60a5fa; }
.pkg-icon { background: rgba(34,197,94,0.1); color: #4ade80; }
.report-options { display: flex; gap: 12px; flex-wrap: wrap; font-size: 12px; color: var(--text2); }
.report-options label { display: flex; align-items: center; gap: 5px; cursor: pointer; }
.report-actions { display: flex; gap: 8px; margin-top: 4px; }

.preview-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; }
.clickable-row:hover { background: var(--bg3); }
.call-to-sync { display: flex; align-items: center; gap: 8px; padding: 12px 16px; background: rgba(234,179,8,0.1); border: 1px solid rgba(234,179,8,0.2); border-radius: var(--radius); color: #eab308; font-size: 12px; margin-bottom: 14px; }

.pagination { display: flex; align-items: center; justify-content: center; gap: 12px; margin-top: 16px; margin-bottom: 8px; }
.page-info { font-family: var(--font-mono); font-size: 12px; color: var(--text3); }
</style>
