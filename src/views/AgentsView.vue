<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h2>Agents</h2>
        <p class="sub">{{ store.totalAgents }} agents terdaftar · {{ store.activeAgents }} aktif</p>
      </div>
      <button class="btn btn-ghost" @click="store.initialize()">Refresh</button>
    </div>

    <div class="filters card" style="margin-bottom: 16px; display: flex; gap: 10px; align-items: center; padding: 14px 16px;">
      <input v-model="search" placeholder="Cari agent, IP, OS..." style="flex: 1;" />
      <select v-model="filterStatus">
        <option value="">Semua Status</option>
        <option value="active">Active</option>
        <option value="disconnected">Disconnected</option>
        <option value="never_connected">Never Connected</option>
      </select>
      <select v-model="filterOS">
        <option value="">Semua OS</option>
        <option v-for="os in osList" :key="os" :value="os">{{ os }}</option>
      </select>
      <select v-model="perPage">
        <option :value="5">5</option>
        <option :value="10">10</option>
        <option :value="20">20</option>
        <option :value="50">50</option>
        <option value="all">Semua Agent</option>
      </select>
    </div>

    <div class="card" style="padding: 0; overflow: hidden;">
      <table>
        <thead>
          <tr>
            <th>ID</th><th>Name</th><th>IP</th><th>OS</th><th>Version</th><th>Status</th><th>Last Seen</th><th>Action</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="store.loading"><td colspan="8" style="text-align:center; color:var(--text3); padding: 32px;">Loading...</td></tr>
          <tr v-else-if="filtered.length === 0"><td colspan="8" style="text-align:center; color:var(--text3); padding: 32px;">Tidak ada agent ditemukan</td></tr>
          <tr v-for="a in paginated" :key="a.id">
            <td><span class="mono">{{ a.id }}</span></td>
            <td>{{ a.name }}</td>
            <td><span class="mono" style="color: var(--info);">{{ a.ip || '-' }}</span></td>
            <td>{{ a.os?.name || a.os?.platform || '-' }}</td>
            <td><span class="mono" style="font-size: 11px;">{{ a.version || '-' }}</span></td>
            <td><span class="badge" :class="statusBadge(a.status)">{{ a.status }}</span></td>
            <td><span class="mono" style="font-size: 11px; color: var(--text3);">{{ formatDate(a.lastKeepAlive) }}</span></td>
            <td>
              <button class="btn btn-ghost" style="padding: 5px 12px; font-size: 12px;" @click="$router.push(`/agents/${a.id}`)">Detail →</button>
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
const filterStatus = ref('')
const filterOS = ref('')
const perPage = ref(5)
const page = ref(1)

watch([search, filterStatus, filterOS, perPage], () => { page.value = 1 })

onMounted(async () => { if (!store.agents.length) await store.initialize() })

const osList = computed(() => {
  const s = new Set(store.agents.map(a => a.os?.name || a.os?.platform).filter(Boolean))
  return [...s].sort()
})

const filtered = computed(() => {
  return store.agents.filter(a => {
    const q = search.value.toLowerCase()
    const matchQ = !q || a.name?.toLowerCase().includes(q) || a.ip?.includes(q) || a.os?.name?.toLowerCase().includes(q)
    const matchStatus = !filterStatus.value || a.status === filterStatus.value
    const matchOS = !filterOS.value || a.os?.name === filterOS.value || a.os?.platform === filterOS.value
    return matchQ && matchStatus && matchOS
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

function statusBadge(s) {
  if (s === 'active') return 'badge-active'
  if (s === 'disconnected') return 'badge-disconnected'
  return 'badge-never'
}

function formatDate(d) {
  if (!d) return '-'
  return new Date(d).toLocaleString('id-ID', { dateStyle: 'short', timeStyle: 'short' })
}
</script>

<style scoped>
.page { padding: 28px; max-width: 1200px; }
.page-header { display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 20px; }
.page-header h2 { font-family: var(--font-display); font-size: 20px; font-weight: 700; }
.sub { color: var(--text3); font-size: 12px; margin-top: 2px; }
.mono { font-family: var(--font-mono); font-size: 12px; }
.pagination { display: flex; align-items: center; justify-content: center; gap: 12px; margin-top: 16px; }
.page-info { font-family: var(--font-mono); font-size: 12px; color: var(--text3); }
</style>
