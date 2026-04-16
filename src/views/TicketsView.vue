<template>
  <div class="page">
    <!-- Header -->
    <div class="page-header">
      <div>
        <h2>Incident Tickets</h2>
        <p class="sub">{{ stats.open }} open · {{ stats.in_progress }} in progress · {{ stats.total }} total</p>
      </div>
      <div class="header-actions">
        <button class="btn btn-ghost" @click="syncAlerts" :disabled="syncing">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" :class="{ spin: syncing }"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg>
          {{ syncing ? `Syncing (${syncProgress})...` : 'Sync Alerts' }}
        </button>
        <button class="btn btn-ghost" @click="showCreate = true">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
          New Ticket
        </button>
        <button class="btn btn-ghost" @click="exportAllJSON">Export JSON</button>
      </div>
    </div>

    <!-- Stats pills -->
    <div class="stats-row">
      <div class="stat-pill" :class="{ active: filterStatus === '' }" @click="setFilter('')">
        All <strong>{{ stats.total }}</strong>
      </div>
      <div class="stat-pill open" :class="{ active: filterStatus === 'open' }" @click="setFilter('open')">
        <span class="pill-dot" style="background:#fbbf24;"></span> Open <strong>{{ stats.open }}</strong>
      </div>
      <div class="stat-pill in-progress" :class="{ active: filterStatus === 'in_progress' }" @click="setFilter('in_progress')">
        <span class="pill-dot" style="background:#60a5fa;"></span> In Progress <strong>{{ stats.in_progress }}</strong>
      </div>
      <div class="stat-pill solved" :class="{ active: filterStatus === 'solved' }" @click="setFilter('solved')">
        <span class="pill-dot" style="background:#4ade80;"></span> Solved <strong>{{ stats.solved }}</strong>
      </div>
      <div class="stat-pill closed" :class="{ active: filterStatus === 'closed' }" @click="setFilter('closed')">
        <span class="pill-dot" style="background:#94a3b8;"></span> Closed <strong>{{ stats.closed }}</strong>
      </div>
      <div class="stat-pill false-pos" :class="{ active: filterStatus === 'false_positive' }" @click="setFilter('false_positive')">
        <span class="pill-dot" style="background:#fb923c;"></span> False Pos <strong>{{ stats.false_positive }}</strong>
      </div>
    </div>

    <!-- Filters toolbar -->
    <div class="toolbar-card">
      <input v-model="search" placeholder="Cari ticket ID, CVE, agent, package..." class="toolbar-search" />
      <select v-model="filterSeverity">
        <option value="">Semua Severity</option>
        <option value="critical">Critical</option>
        <option value="high">High</option>
        <option value="medium">Medium</option>
        <option value="low">Low</option>
      </select>
      <select v-model="filterAgent">
        <option value="">Semua Agent</option>
        <option v-for="a in store.agents" :key="a.id" :value="a.id">{{ a.name }}</option>
      </select>
      <select v-model="perPage">
        <option :value="5">5</option>
        <option :value="10">10</option>
        <option :value="20">20</option>
        <option :value="50">50</option>
        <option value="all">Semua</option>
      </select>
      <span class="count-text">{{ filteredTickets.length }} tiket</span>
    </div>

    <!-- Sync result banner -->
    <div v-if="syncResult" class="sync-banner" :class="syncResult.type">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
      {{ syncResult.message }}
      <button class="sync-dismiss" @click="syncResult = null">✕</button>
    </div>

    <!-- Storage warning -->
    <div v-if="storageWarn" class="sync-banner warning">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
      localStorage usage: {{ storageWarn }}%. Pertimbangkan untuk Export JSON sebagai backup, lalu hapus tiket lama.
    </div>

    <!-- Ticket list -->
    <div v-if="!filteredTickets.length" class="empty-state" style="margin-top: 40px; padding: 40px;">
      <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="var(--text3)" stroke-width="1" style="margin-bottom: 12px;"><path d="M15 5v2M15 11v2M15 17v2M5 5h14a2 2 0 012 2v3a2 2 0 000 4v3a2 2 0 01-2 2H5a2 2 0 01-2-2v-3a2 2 0 000-4V7a2 2 0 012-2z"/></svg>
      <p v-if="stats.total === 0">Belum ada tiket insiden. Klik <strong>Sync Alerts</strong> untuk menarik alert dari Indexer, atau <strong>New Ticket</strong> untuk membuat manual.</p>
      <p v-else>Tidak ada tiket yang cocok dengan filter saat ini.</p>
    </div>

    <div class="ticket-list">
      <TicketCard
        v-for="ticket in paginatedTickets"
        :key="ticket.id"
        :ticket="ticket"
        @click="openDetail(ticket)"
        @status-change="onStatusChange"
        @export-pdf="exportSinglePDF"
      />
    </div>

    <!-- Pagination -->
    <div class="pagination" v-if="totalPages > 1">
      <button class="btn btn-ghost" :disabled="page === 1" @click="page--">← Prev</button>
      <span class="page-info mono">{{ page }} / {{ totalPages }}</span>
      <button class="btn btn-ghost" :disabled="page === totalPages" @click="page++">Next →</button>
    </div>

    <!-- Modals -->
    <TicketModal
      v-if="selectedTicket"
      :ticket="selectedTicket"
      @close="selectedTicket = null"
      @save="onSaveTicket"
      @export-pdf="exportSinglePDF"
      @delete="onDeleteTicket"
    />
    <TicketCreateModal
      v-if="showCreate"
      :agents="store.agents"
      @close="showCreate = false"
      @create="onCreateManual"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useAppStore } from '../stores/app'
import { loadTickets, getTickets, getStats, createTicket, updateTicket, deleteTicket, exportJSON, getStorageUsage, syncTickets } from '../utils/ticketStore'
import { exportTicketPDF } from '../utils/pdfExport'
import { loadPlaybooks, seedDefaultPlaybooks } from '../utils/playbookStore'

import { DEFAULT_PLAYBOOKS } from '../utils/defaultPlaybooks'
import TicketCard from '../components/TicketCard.vue'
import TicketModal from '../components/TicketModal.vue'
import TicketCreateModal from '../components/TicketCreateModal.vue'

const store = useAppStore()
const search = ref('')
const filterStatus = ref('')
const filterSeverity = ref('')
const filterAgent = ref('')
const syncing = ref(false)
const syncProgress = ref('')
const syncResult = ref(null)
const selectedTicket = ref(null)
const showCreate = ref(false)
const page = ref(1)
const perPage = ref(10)
const stats = ref({})
const storageWarn = ref(null)

onMounted(async () => {
  seedDefaultPlaybooks(DEFAULT_PLAYBOOKS)
  await Promise.all([loadTickets(), loadPlaybooks()])
  refreshStats()
  if (!store.agents.length) store.initialize()
  checkStorage()
  
  // Auto-sync behind the scenes
  syncAlerts()
})

function refreshStats() {
  stats.value = getStats()
}

function checkStorage() {
  const usage = getStorageUsage()
  storageWarn.value = parseFloat(usage.percentage) > 70 ? usage.percentage : null
}

function setFilter(s) {
  filterStatus.value = s
  page.value = 1
}

// Reset page on filter changes
watch([search, filterSeverity, filterAgent, perPage], () => { page.value = 1 })

const filteredTickets = computed(() =>
  getTickets({
    status: filterStatus.value,
    severity: filterSeverity.value,
    agentId: filterAgent.value,
    search: search.value
  })
)

const totalPages = computed(() => {
  if (perPage.value === 'all') return 1
  return Math.max(1, Math.ceil(filteredTickets.value.length / perPage.value))
})
const paginatedTickets = computed(() => {
  if (perPage.value === 'all') return filteredTickets.value
  return filteredTickets.value.slice((page.value - 1) * perPage.value, page.value * perPage.value)
})

// ─── Full-Auto Sync ─────────────────────────────────────────────
async function syncAlerts() {
  syncing.value = true
  syncResult.value = null

  try {
    const result = await syncTickets()

    syncResult.value = {
      type: 'success',
      message: `Sync selesai: ${result.new_count} tiket baru dibuat, ${result.skipped} duplikat di-skip.`
    }
  } catch (err) {
    syncResult.value = {
      type: 'error',
      message: `Sync error: ${err.response?.data?.detail || err.message}`
    }
  } finally {
    syncing.value = false
    page.value = 1
    refreshStats()
    checkStorage()
  }
}

function openDetail(ticket) {
  selectedTicket.value = { ...ticket, tags: [...(ticket.tags || [])], history: [...(ticket.history || [])] }
}

async function onSaveTicket(updated) {
  await updateTicket(updated.id, updated)
  refreshStats()
  selectedTicket.value = null
}

async function onDeleteTicket(id) {
  if (confirm('Yakin hapus tiket ini?')) {
    await deleteTicket(id)
    refreshStats()
    selectedTicket.value = null
    checkStorage()
  }
}

async function onStatusChange({ id, status }) {
  await updateTicket(id, { status })
  refreshStats()
}

async function onCreateManual(data) {
  await createTicket(data)
  refreshStats()
  showCreate.value = false
  checkStorage()
}

function exportSinglePDF(ticket) {
  exportTicketPDF(ticket)
}

function exportAllJSON() {
  exportJSON()
}
</script>

<style scoped>
.page { padding: 28px; max-width: 1200px; }
.page-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px; flex-wrap: wrap; gap: 12px; }
.page-header h2 { font-family: var(--font-display); font-size: 20px; font-weight: 700; }
.sub { color: var(--text3); font-size: 12px; margin-top: 2px; font-family: var(--font-mono); }
.header-actions { display: flex; gap: 8px; flex-wrap: wrap; }

/* Stats row */
.stats-row {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}
.stat-pill {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 7px 14px;
  border-radius: 8px;
  font-size: 12px;
  color: var(--text3);
  background: var(--bg2);
  border: 1px solid var(--border);
  cursor: pointer;
  transition: all 0.15s;
}
.stat-pill:hover { border-color: var(--accent); color: var(--text); }
.stat-pill.active { background: var(--bg3); border-color: var(--accent); color: var(--text); }
.stat-pill strong { font-family: var(--font-mono); color: var(--text); }
.pill-dot { width: 6px; height: 6px; border-radius: 50%; flex-shrink: 0; }

/* Toolbar */
.toolbar-card {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 16px;
  background: var(--bg2);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  margin-bottom: 16px;
}
.toolbar-search { flex: 1; min-width: 200px; }
.count-text { font-size: 11px; color: var(--text3); font-family: var(--font-mono); margin-left: auto; white-space: nowrap; }

/* Sync banner */
.sync-banner {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  border-radius: var(--radius);
  font-size: 12px;
  margin-bottom: 14px;
  animation: slideIn 0.3s ease;
}
.sync-banner.success { background: rgba(34,197,94,0.1); border: 1px solid rgba(34,197,94,0.2); color: #4ade80; }
.sync-banner.error { background: rgba(239,68,68,0.1); border: 1px solid rgba(239,68,68,0.2); color: #f87171; }
.sync-banner.warning { background: rgba(234,179,8,0.1); border: 1px solid rgba(234,179,8,0.2); color: #eab308; }
.sync-dismiss {
  margin-left: auto;
  background: none;
  border: none;
  color: inherit;
  cursor: pointer;
  font-size: 14px;
  opacity: 0.7;
}
.sync-dismiss:hover { opacity: 1; }

@keyframes slideIn {
  from { opacity: 0; transform: translateY(-8px); }
  to { opacity: 1; transform: translateY(0); }
}

/* Ticket list */
.ticket-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.empty-state {
  text-align: center;
  color: var(--text3);
  font-size: 13px;
  line-height: 1.8;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 16px;
}
.page-info { font-size: 12px; color: var(--text3); }

.spin { animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.mono { font-family: var(--font-mono); }
</style>
