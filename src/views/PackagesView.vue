<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h2>Packages & Dependencies</h2>
        <p class="sub">Inventaris software dari agent yang dipilih</p>
      </div>
    </div>

    <div class="agent-selector card" style="padding: 14px 16px; margin-bottom: 16px; display: flex; gap: 10px; align-items: center;">
      <label style="font-size: 12px; color: var(--text3); white-space: nowrap;">Pilih Agent</label>
      <select v-model="selectedAgent" style="flex: 1;" @change="onAgentChange">
        <option value="">-- Pilih agent --</option>
        <option v-for="a in store.agents" :key="a.id" :value="a.id">{{ a.name }} ({{ a.ip }})</option>
      </select>
      <button class="btn btn-primary" @click="loadPackages" :disabled="!selectedAgent || loading">
        {{ loading ? 'Loading...' : 'Load Packages' }}
      </button>
    </div>

    <div v-if="packages.length">
      <div class="stats-row">
        <div class="mini-stat"><span class="ms-val">{{ packages.length }}</span><span class="ms-label">Total Packages</span></div>
        <div class="mini-stat"><span class="ms-val">{{ archCount }}</span><span class="ms-label">Architectures</span></div>
        <div class="mini-stat"><span class="ms-val">{{ vendorCount }}</span><span class="ms-label">Vendors</span></div>
      </div>

      <div class="toolbar" style="margin-bottom: 12px;">
        <input v-model="search" placeholder="Cari nama package..." style="flex: 1;" />
        <select v-model="filterArch">
          <option value="">Semua Arch</option>
          <option v-for="a in archList" :key="a" :value="a">{{ a }}</option>
        </select>
        <select v-model="perPage">
          <option :value="5">5</option>
          <option :value="10">10</option>
          <option :value="20">20</option>
          <option :value="50">50</option>
          <option value="all">Semua</option>
        </select>
        <button class="btn btn-ghost" @click="exportCSV">Export CSV</button>
        <span class="count-text">{{ filtered.length }} packages</span>
      </div>

      <div class="card" style="padding: 0; overflow: hidden;">
        <table>
          <thead>
            <tr><th>#</th><th>Package Name</th><th>Version</th><th>Architecture</th><th>Vendor</th><th>Description</th></tr>
          </thead>
          <tbody>
            <tr v-for="(p, i) in paginated" :key="i">
              <td class="mono" style="color: var(--text3);">{{ perPage === 'all' ? i + 1 : (page-1)*perPage + i + 1 }}</td>
              <td><strong style="font-weight: 500;">{{ p.name }}</strong></td>
              <td><span class="mono" style="color: var(--info);">{{ p.version }}</span></td>
              <td><span class="mono">{{ p.architecture || '-' }}</span></td>
              <td style="color: var(--text3);">{{ p.vendor || '-' }}</td>
              <td style="color: var(--text3); font-size: 12px; max-width: 300px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" :title="p.description">{{ p.description || '-' }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="pagination" v-if="totalPages > 1">
        <button class="btn btn-ghost" :disabled="page === 1" @click="page--">←</button>
        <span class="page-info">Halaman {{ page }} dari {{ totalPages }} ({{ filtered.length }} total)</span>
        <button class="btn btn-ghost" :disabled="page === totalPages" @click="page++">→</button>
      </div>
    </div>

    <div v-else class="empty-state card" style="text-align: center; padding: 60px; color: var(--text3);">
      Pilih agent dan klik "Load Packages" untuk melihat daftar software yang terinstal.
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useAppStore } from '../stores/app'

const store = useAppStore()
const selectedAgent = ref('')
const packages = ref([])
const loading = ref(false)
const search = ref('')
const filterArch = ref('')
const page = ref(1)
const perPage = ref(10)

watch([search, filterArch, perPage], () => { page.value = 1 })

onMounted(async () => { if (!store.agents.length) await store.initialize() })

function onAgentChange() { packages.value = []; page.value = 1 }

async function loadPackages() {
  if (!selectedAgent.value) return
  loading.value = true
  const data = await store.fetchPackages(selectedAgent.value)
  packages.value = data
  page.value = 1
  loading.value = false
}

const archList = computed(() => [...new Set(packages.value.map(p => p.architecture).filter(Boolean))].sort())
const archCount = computed(() => archList.value.length)
const vendorCount = computed(() => new Set(packages.value.map(p => p.vendor).filter(Boolean)).size)

const filtered = computed(() => {
  return packages.value.filter(p => {
    const q = search.value.toLowerCase()
    const matchQ = !q || p.name?.toLowerCase().includes(q) || p.description?.toLowerCase().includes(q)
    const matchA = !filterArch.value || p.architecture === filterArch.value
    return matchQ && matchA
  })
})

const totalPages = computed(() => {
  if (perPage.value === 'all') return 1
  return Math.max(1, Math.ceil(filtered.value.length / perPage.value))
})

const paginated = computed(() => {
  if (perPage.value === 'all') return filtered.value
  return filtered.value.slice((page.value - 1) * perPage.value, page.value * perPage.value)
})

function exportCSV() {
  const headers = ['Name', 'Version', 'Architecture', 'Vendor', 'Description']
  const rows = filtered.value.map(p => [p.name, p.version, p.architecture, p.vendor, p.description].map(v => `"${(v || '').replace(/"/g, '""')}"`))
  const csv = [headers.join(','), ...rows.map(r => r.join(','))].join('\n')
  const blob = new Blob([csv], { type: 'text/csv' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `packages_agent_${selectedAgent.value}.csv`
  a.click()
  URL.revokeObjectURL(url)
}
</script>

<style scoped>
.page { padding: 28px; max-width: 1200px; }
.page-header { display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 18px; }
.page-header h2 { font-family: var(--font-display); font-size: 20px; font-weight: 700; }
.sub { color: var(--text3); font-size: 12px; margin-top: 2px; }
.mono { font-family: var(--font-mono); font-size: 12px; }
.count-text { font-size: 11px; color: var(--text3); font-family: var(--font-mono); white-space: nowrap; }

.stats-row { display: flex; gap: 12px; margin-bottom: 16px; }
.mini-stat { background: var(--bg2); border: 1px solid var(--border); border-radius: var(--radius); padding: 14px 18px; flex: 1; }
.ms-val { display: block; font-family: var(--font-display); font-size: 24px; font-weight: 700; }
.ms-label { font-size: 11px; color: var(--text3); text-transform: uppercase; letter-spacing: 0.05em; font-family: var(--font-mono); }

.toolbar { display: flex; align-items: center; gap: 10px; }
.pagination { display: flex; align-items: center; justify-content: center; gap: 12px; margin-top: 16px; }
.page-info { font-family: var(--font-mono); font-size: 12px; color: var(--text3); }
</style>
