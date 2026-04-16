<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h2>Vulnerabilities</h2>
        <p class="sub">Semua CVE dari seluruh agent</p>
      </div>
      <button class="btn btn-primary" @click="loadAll" :disabled="store.loading">
        {{ store.loading ? 'Loading...' : 'Load All Agents' }}
      </button>
    </div>

    <div class="summary-bar">
      <div class="sev-pill" v-for="s in severityList" :key="s.label" @click="toggleSev(s.label)" :class="{ active: activeSev.includes(s.label), [s.cls]: true }">
        <span class="sev-dot"></span>
        {{ s.label }} <strong>{{ s.count }}</strong>
      </div>
    </div>

    <div class="toolbar card" style="margin-bottom: 14px; display: flex; gap: 10px; padding: 12px 14px;">
      <input v-model="search" placeholder="Cari CVE ID, package name..." style="flex: 1;" />
      <select v-model="filterAgent">
        <option value="">Semua Agent</option>
        <option v-for="a in store.agents" :key="a.id" :value="a.id">{{ a.name }}</option>
      </select>
      <select v-model="sortBy">
        <option value="severity">Sort: Severity</option>
        <option value="cvss">Sort: CVSS Score</option>
        <option value="cve">Sort: CVE ID</option>
      </select>
      <span class="count-text">{{ filtered.length }} items</span>
    </div>

    <div class="card" style="padding: 0; overflow: hidden;">
      <table>
        <thead>
          <tr><th>CVE ID</th><th>Package</th><th>Version</th><th>Fix</th><th>Severity</th><th>CVSS</th><th>Agent</th></tr>
        </thead>
        <tbody>
          <tr v-if="store.loading"><td colspan="7" style="text-align:center; color:var(--text3); padding: 40px;">Mengambil data...</td></tr>
          <tr v-else-if="!hasData"><td colspan="7" style="text-align:center; color:var(--text3); padding: 40px;">Klik "Load All Agents" untuk memuat semua vulnerabilities.</td></tr>
          <tr v-else-if="!filtered.length"><td colspan="7" style="text-align:center; color:var(--text3); padding: 40px;">Tidak ada hasil.</td></tr>
          <tr v-for="v in paginated" :key="`${v._agentId}_${v.cve}_${v.name}`">
            <td><a :href="`https://nvd.nist.gov/vuln/detail/${v.cve}`" target="_blank" class="cve-link">{{ v.cve }}</a></td>
            <td>{{ v.name }}</td>
            <td><span class="mono">{{ v.version }}</span></td>
            <td><span class="mono" style="color: var(--low); font-size: 11px;">{{ v.condition || '-' }}</span></td>
            <td><span class="badge" :class="`badge-${v.severity?.toLowerCase()}`">{{ v.severity }}</span></td>
            <td><span class="mono">{{ v.cvss || '-' }}</span></td>
            <td>
              <span class="agent-chip" @click="$router.push(`/agents/${v._agentId}`)">
                {{ agentName(v._agentId) }}
              </span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="pagination" v-if="totalPages > 1">
      <button class="btn btn-ghost" :disabled="page === 1" @click="page--">←</button>
      <span class="page-info">{{ page }} / {{ totalPages }}</span>
      <button class="btn btn-ghost" :disabled="page === totalPages" @click="page++">→</button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useAppStore } from '../stores/app'

const store = useAppStore()
const search = ref('')
const filterAgent = ref('')
const sortBy = ref('severity')
const activeSev = ref([])
const page = ref(1)
const PER_PAGE = 10

const SEVERITY_ORDER = { critical: 0, high: 1, medium: 2, low: 3 }

watch([search, filterAgent, sortBy], () => { page.value = 1 })


onMounted(async () => { if (!store.agents.length) await store.initialize() })

const hasData = computed(() => Object.keys(store.vulnsByAgent).length > 0)

const allWithAgent = computed(() => {
  return Object.entries(store.vulnsByAgent).flatMap(([agentId, vulns]) =>
    vulns.map(v => ({ ...v, _agentId: agentId }))
  )
})

const severityList = computed(() => {
  return [
    { label: 'Critical', cls: 'crit', count: allWithAgent.value.filter(v => v.severity?.toLowerCase() === 'critical').length },
    { label: 'High', cls: 'hi', count: allWithAgent.value.filter(v => v.severity?.toLowerCase() === 'high').length },
    { label: 'Medium', cls: 'med', count: allWithAgent.value.filter(v => v.severity?.toLowerCase() === 'medium').length },
    { label: 'Low', cls: 'lo', count: allWithAgent.value.filter(v => v.severity?.toLowerCase() === 'low').length },
  ]
})

function toggleSev(s) {
  const i = activeSev.value.indexOf(s)
  if (i >= 0) activeSev.value.splice(i, 1)
  else activeSev.value.push(s)
  page.value = 1
}

const filtered = computed(() => {
  let list = allWithAgent.value
  if (search.value) {
    const q = search.value.toLowerCase()
    list = list.filter(v => v.cve?.toLowerCase().includes(q) || v.name?.toLowerCase().includes(q))
  }
  if (filterAgent.value) list = list.filter(v => v._agentId === filterAgent.value)
  if (activeSev.value.length) list = list.filter(v => activeSev.value.includes(v.severity))
  list = [...list].sort((a, b) => {
    if (sortBy.value === 'severity') return (SEVERITY_ORDER[a.severity?.toLowerCase()] ?? 99) - (SEVERITY_ORDER[b.severity?.toLowerCase()] ?? 99)
    if (sortBy.value === 'cvss') return (b.cvss || 0) - (a.cvss || 0)
    return (a.cve || '').localeCompare(b.cve || '')
  })
  return list
})

const totalPages = computed(() => Math.ceil(filtered.value.length / PER_PAGE))
const paginated = computed(() => filtered.value.slice((page.value - 1) * PER_PAGE, page.value * PER_PAGE))

function agentName(id) { return store.agents.find(a => a.id === id)?.name || id }

async function loadAll() { await store.fetchAllVulnerabilities() }
</script>

<style scoped>
.page { padding: 28px; max-width: 1200px; }
.page-header { display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 18px; }
.page-header h2 { font-family: var(--font-display); font-size: 20px; font-weight: 700; }
.sub { color: var(--text3); font-size: 12px; margin-top: 2px; }
.mono { font-family: var(--font-mono); font-size: 12px; }
.count-text { font-size: 11px; color: var(--text3); font-family: var(--font-mono); white-space: nowrap; }
.cve-link { color: var(--accent); font-family: var(--font-mono); font-size: 12px; }
.cve-link:hover { text-decoration: underline; }

.summary-bar { display: flex; gap: 8px; margin-bottom: 16px; }
.sev-pill {
  display: flex; align-items: center; gap: 7px; padding: 7px 14px;
  border-radius: 100px; font-size: 12px; cursor: pointer;
  border: 1px solid var(--border2); background: var(--bg2); color: var(--text2);
  transition: all 0.15s;
}
.sev-pill strong { font-family: var(--font-mono); font-weight: 600; }
.sev-dot { width: 8px; height: 8px; border-radius: 50%; }
.sev-pill.crit .sev-dot { background: var(--critical); }
.sev-pill.hi .sev-dot { background: var(--high); }
.sev-pill.med .sev-dot { background: var(--medium); }
.sev-pill.lo .sev-dot { background: var(--low); }
.sev-pill.active.crit { background: rgba(239,68,68,0.1); border-color: rgba(239,68,68,0.4); color: #f87171; }
.sev-pill.active.hi { background: rgba(249,115,22,0.1); border-color: rgba(249,115,22,0.4); color: #fb923c; }
.sev-pill.active.med { background: rgba(234,179,8,0.1); border-color: rgba(234,179,8,0.4); color: #fbbf24; }
.sev-pill.active.lo { background: rgba(34,197,94,0.1); border-color: rgba(34,197,94,0.4); color: #4ade80; }

.agent-chip { font-family: var(--font-mono); font-size: 11px; background: var(--bg3); padding: 2px 8px; border-radius: 4px; cursor: pointer; color: var(--info); }
.agent-chip:hover { background: rgba(6,182,212,0.1); }

.pagination { display: flex; align-items: center; justify-content: center; gap: 12px; margin-top: 16px; }
.page-info { font-family: var(--font-mono); font-size: 12px; color: var(--text3); }
</style>
