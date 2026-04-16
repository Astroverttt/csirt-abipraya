<template>
  <div class="modal-overlay" @click.self="$emit('close')" @keydown.esc="$emit('close')">
    <div class="modal-container">
      <!-- Modal Header -->
      <div class="modal-header">
        <div class="modal-title-row">
          <span class="modal-id mono">{{ form.id }}</span>
          <span class="badge" :class="`badge-${form.severity?.toLowerCase()}`">{{ form.severity || 'N/A' }}</span>
          <span class="badge status-badge" :class="`status-${form.status}`">{{ formatStatus(form.status) }}</span>
        </div>
        <button class="btn-close" @click="$emit('close')" title="Close (Esc)">✕</button>
      </div>

      <!-- Tabs -->
      <div class="modal-tabs">
        <button class="mtab" :class="{ active: tab === 'overview' }" @click="tab = 'overview'">Overview</button>
        <button class="mtab" :class="{ active: tab === 'analysis' }" @click="tab = 'analysis'">Analysis</button>
        <button class="mtab" :class="{ active: tab === 'playbook' }" @click="tab = 'playbook'">
          Playbook
          <span v-if="playbookBadge" class="mtab-count">{{ playbookBadge }}</span>
        </button>
        <button class="mtab" :class="{ active: tab === 'evidence' }" @click="tab = 'evidence'">
          Evidence
          <span v-if="form.evidence?.length" class="mtab-count">{{ form.evidence.length }}</span>
        </button>
        <button class="mtab" :class="{ active: tab === 'activity' }" @click="tab = 'activity'">
          Activity
          <span v-if="form.history?.length" class="mtab-count">{{ form.history.length }}</span>
        </button>
      </div>

      <!-- Tab Content -->
      <div class="modal-body">
        <!-- Overview Tab -->
        <div v-if="tab === 'overview'" class="tab-content">
          <div class="info-section">
            <h4>Alert Information</h4>
            <div class="info-grid">
              <div class="info-row"><span class="info-key">Agent</span><span class="info-val">{{ form.agentName }} ({{ form.agentIp }})</span></div>
              <div class="info-row"><span class="info-key">Agent ID</span><span class="info-val mono">{{ form.agentId }}</span></div>
              <div class="info-row"><span class="info-key">Alert Time</span><span class="info-val mono">{{ formatDate(form.alertTimestamp || form.createdAt) }}</span></div>
              <div class="info-row"><span class="info-key">Rule ID</span><span class="info-val mono">{{ form.ruleId || '-' }}</span></div>
              <div class="info-row"><span class="info-key">Rule Level</span><span class="info-val mono">{{ form.ruleLevel || '-' }}</span></div>
              <div class="info-row"><span class="info-key">Rule Description</span><span class="info-val">{{ form.ruleDescription || '-' }}</span></div>
              <div class="info-row"><span class="info-key">CVE ID</span>
                <span class="info-val">
                  <a v-if="form.cveId" :href="`https://nvd.nist.gov/vuln/detail/${form.cveId}`" target="_blank" class="cve-link">{{ form.cveId }}</a>
                  <span v-else>-</span>
                </span>
              </div>
              <div class="info-row"><span class="info-key">Package</span><span class="info-val mono">{{ form.packageName || '-' }} {{ form.packageVersion || '' }}</span></div>
              <div class="info-row"><span class="info-key">Priority</span><span class="info-val"><span class="badge" :class="`badge-${form.priority}`">{{ form.priority }}</span></span></div>
              <div class="info-row"><span class="info-key">Auto Created</span><span class="info-val">{{ form.isAutoCreated ? 'Yes (from sync)' : 'No (manual)' }}</span></div>
              <div class="info-row"><span class="info-key">Created</span><span class="info-val mono">{{ formatDate(form.createdAt) }}</span></div>
              <div class="info-row"><span class="info-key">Updated</span><span class="info-val mono">{{ formatDate(form.updatedAt) }}</span></div>
            </div>
          </div>

          <!-- Status Changer -->
          <div class="info-section">
            <h4>Status</h4>
            <div class="status-changer">
              <span v-for="s in statuses" :key="s.value"
                class="status-btn" :class="[`sc-${s.value}`, { active: form.status === s.value }]"
                @click="form.status = s.value"
              >{{ s.label }}</span>
            </div>
          </div>
        </div>

        <!-- Analysis Tab -->
        <div v-if="tab === 'analysis'" class="tab-content">
          <div class="form-group">
            <label>Assignee</label>
            <input v-model="form.assignee" placeholder="Nama analyst yang bertanggung jawab" />
          </div>

          <div class="form-group">
            <label>Deskripsi Alert</label>
            <textarea v-model="form.description" rows="3" placeholder="Jelaskan apa yang terjadi pada alert ini..."></textarea>
          </div>

          <div class="form-group">
            <label>Root Cause</label>
            <textarea v-model="form.rootCause" rows="3" placeholder="Kenapa alert ini muncul? Apa penyebab dasarnya?"></textarea>
          </div>

          <div class="form-group">
            <label>Solusi / Tindakan</label>
            <textarea v-model="form.solution" rows="3" placeholder="Apa yang sudah/akan dilakukan untuk mengatasi ini?"></textarea>
          </div>

          <div class="form-group">
            <label>Catatan Analyst</label>
            <textarea v-model="form.notes" rows="2" placeholder="Catatan tambahan..."></textarea>
          </div>

          <div class="form-group">
            <label>Tags</label>
            <div class="tag-input">
              <span v-for="tag in form.tags" :key="tag" class="tag-pill">
                {{ tag }}
                <span class="tag-remove" @click="removeTag(tag)">×</span>
              </span>
              <input v-model="tagInput" @keydown.enter.prevent="addTag" placeholder="Tambah tag + Enter" class="tag-field" />
            </div>
          </div>
        </div>

        <!-- Playbook Tab -->
        <div v-if="tab === 'playbook'" class="tab-content">
          <PlaybookPanel
            :ticket="form"
            @ticket-updated="onPlaybookUpdated"
            @upload-evidence="onUploadEvidence"
          />
        </div>

        <!-- Evidence Tab -->
        <div v-if="tab === 'evidence'" class="tab-content">
          <EvidenceUploader
            :ticket="form"
            :available-steps="currentPlaybookSteps"
            @ticket-updated="onEvidenceUpdated"
          />
        </div>

        <!-- Activity Tab -->
        <div v-if="tab === 'activity'" class="tab-content">
          <div v-if="!form.history?.length" class="empty-state" style="padding: 30px;">
            Belum ada aktivitas tercatat.
          </div>
          <div v-else class="timeline">
            <div v-for="(h, i) in [...(form.history || [])].reverse()" :key="i" class="timeline-item">
              <div class="tl-dot" :class="h.action === 'created' ? 'tl-created' : h.action === 'status_change' ? 'tl-status' : 'tl-other'"></div>
              <div class="tl-content">
                <span class="tl-action">{{ h.action?.replace('_', ' ') }}</span>
                <span class="tl-detail">{{ h.detail }}</span>
                <span class="tl-time mono">{{ formatDate(h.timestamp) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Modal Footer -->
      <div class="modal-footer">
        <button class="btn btn-danger" @click="$emit('delete', form.id)">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="m19 6-.86 14.14A2 2 0 0 1 16.17 22H7.83a2 2 0 0 1-1.97-1.86L5 6m5 0V4c0-.55.45-1 1-1h2c.55 0 1 .45 1 1v2"/></svg>
          Hapus
        </button>
        <div style="flex: 1"></div>
        <button class="btn btn-ghost" @click="$emit('export-pdf', form)">Export PDF</button>
        <button class="btn btn-ghost" @click="$emit('close')">Batal</button>
        <button class="btn btn-primary" @click="save">Simpan</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { getAllPlaybooks } from '../utils/playbookStore'
import PlaybookPanel from './PlaybookPanel.vue'
import EvidenceUploader from './EvidenceUploader.vue'

const props = defineProps({
  ticket: { type: Object, required: true }
})

const emit = defineEmits(['close', 'save', 'export-pdf', 'delete'])

const tab = ref('overview')
const tagInput = ref('')
const form = reactive({
  ...props.ticket,
  tags: [...(props.ticket.tags || [])],
  history: [...(props.ticket.history || [])],
  playbook: props.ticket.playbook ? { ...props.ticket.playbook, steps: { ...props.ticket.playbook.steps } } : null,
  evidence: props.ticket.evidence ? [...props.ticket.evidence] : [],
})

const statuses = [
  { value: 'open', label: 'Open' },
  { value: 'in_progress', label: 'In Progress' },
  { value: 'solved', label: 'Solved' },
  { value: 'closed', label: 'Closed' },
  { value: 'false_positive', label: 'False Positive' }
]

const playbookBadge = computed(() => {
  if (!form.playbook) return null
  return `${form.playbook.completedSteps}/${form.playbook.totalSteps}`
})

const currentPlaybookSteps = computed(() => {
  if (!form.playbook?.playbookId) return []
  const pb = getAllPlaybooks().find(p => p.id === form.playbook.playbookId)
  return pb?.steps?.slice().sort((a, b) => a.order - b.order) || []
})

function formatStatus(s) {
  return statuses.find(x => x.value === s)?.label || s
}

function formatDate(dateStr) {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('id-ID', {
    day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit'
  })
}

function addTag() {
  const val = tagInput.value.trim().toLowerCase()
  if (val && !form.tags.includes(val)) {
    form.tags.push(val)
  }
  tagInput.value = ''
}

function removeTag(tag) {
  form.tags = form.tags.filter(t => t !== tag)
}

function onPlaybookUpdated(updatedTicket) {
  if (updatedTicket) {
    form.playbook = updatedTicket.playbook ? { ...updatedTicket.playbook, steps: { ...updatedTicket.playbook.steps } } : null
  }
}

function onEvidenceUpdated(updatedTicket) {
  if (updatedTicket) {
    form.evidence = updatedTicket.evidence ? [...updatedTicket.evidence] : []
  }
}

function onUploadEvidence(stepId) {
  tab.value = 'evidence'
}

function save() {
  emit('save', { ...form })
}

// Keyboard shortcut: Esc to close
function handleKeydown(e) {
  if (e.key === 'Escape') emit('close')
}
onMounted(() => window.addEventListener('keydown', handleKeydown))
onUnmounted(() => window.removeEventListener('keydown', handleKeydown))
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.6);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
}
.modal-container {
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  width: 100%;
  max-width: 760px;
  max-height: 88vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: 0 20px 60px rgba(0,0,0,0.4);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border);
}
.modal-title-row { display: flex; align-items: center; gap: 8px; }
.modal-id { font-size: 15px; font-weight: 700; color: var(--accent); }
.btn-close {
  background: var(--bg3);
  border: 1px solid var(--border);
  color: var(--text3);
  width: 28px; height: 28px;
  border-radius: 6px;
  cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  font-size: 14px;
  transition: all 0.15s;
}
.btn-close:hover { background: rgba(239,68,68,0.15); color: #f87171; border-color: rgba(239,68,68,0.3); }

.modal-tabs {
  display: flex;
  gap: 0;
  border-bottom: 1px solid var(--border);
  padding: 0 20px;
  overflow-x: auto;
}
.mtab {
  padding: 10px 14px;
  font-size: 12px;
  color: var(--text3);
  cursor: pointer;
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  display: flex; align-items: center; gap: 6px;
  transition: all 0.15s;
  white-space: nowrap;
}
.mtab:hover { color: var(--text); }
.mtab.active { color: var(--accent); border-bottom-color: var(--accent); }
.mtab-count { background: rgba(59,130,246,0.15); color: #60a5fa; font-size: 10px; padding: 1px 6px; border-radius: 10px; font-family: var(--font-mono); }

.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.info-section { margin-bottom: 24px; }
.info-section h4 {
  font-size: 11px;
  font-weight: 600;
  color: var(--text3);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 12px;
  font-family: var(--font-mono);
}
.info-grid { display: flex; flex-direction: column; gap: 0; }
.info-row {
  display: flex;
  padding: 8px 0;
  border-bottom: 1px solid var(--border);
  gap: 16px;
  align-items: baseline;
}
.info-row:last-child { border-bottom: none; }
.info-key { font-size: 12px; color: var(--text3); width: 140px; flex-shrink: 0; }
.info-val { font-size: 13px; color: var(--text); word-break: break-word; }

.cve-link { color: var(--accent); font-family: var(--font-mono); font-size: 12px; }
.cve-link:hover { text-decoration: underline; }

.status-changer { display: flex; gap: 6px; flex-wrap: wrap; }
.status-btn {
  padding: 6px 14px;
  border-radius: 6px;
  font-size: 12px;
  cursor: pointer;
  border: 1px solid var(--border);
  background: var(--bg3);
  color: var(--text3);
  transition: all 0.15s;
}
.status-btn:hover { border-color: var(--accent); color: var(--text); }
.status-btn.active { font-weight: 600; }
.status-btn.active.sc-open { background: rgba(234,179,8,0.15); color: #fbbf24; border-color: rgba(234,179,8,0.4); }
.status-btn.active.sc-in_progress { background: rgba(59,130,246,0.15); color: #60a5fa; border-color: rgba(59,130,246,0.4); }
.status-btn.active.sc-solved { background: rgba(34,197,94,0.15); color: #4ade80; border-color: rgba(34,197,94,0.4); }
.status-btn.active.sc-closed { background: rgba(100,116,139,0.15); color: #94a3b8; border-color: rgba(100,116,139,0.4); }
.status-btn.active.sc-false_positive { background: rgba(249,115,22,0.15); color: #fb923c; border-color: rgba(249,115,22,0.4); }

/* Form fields */
.form-group { margin-bottom: 16px; }
.form-group label {
  display: block;
  font-size: 11px;
  font-weight: 600;
  color: var(--text3);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 6px;
  font-family: var(--font-mono);
}
.form-group textarea,
.form-group input {
  width: 100%;
  background: var(--bg3);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  color: var(--text);
  padding: 10px 12px;
  font-size: 13px;
  font-family: var(--font-body);
  resize: vertical;
  transition: border-color 0.15s;
}
.form-group textarea:focus,
.form-group input:focus {
  outline: none;
  border-color: var(--accent);
}

/* Tag input */
.tag-input {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  padding: 8px 10px;
  background: var(--bg3);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  min-height: 40px;
  align-items: center;
}
.tag-pill {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 3px 10px;
  background: rgba(59,130,246,0.15);
  color: #60a5fa;
  border-radius: 4px;
  font-size: 11px;
  font-family: var(--font-mono);
}
.tag-remove {
  cursor: pointer;
  font-size: 14px;
  line-height: 1;
  margin-left: 2px;
  opacity: 0.7;
}
.tag-remove:hover { opacity: 1; color: #f87171; }
.tag-field {
  background: transparent !important;
  border: none !important;
  padding: 2px 4px !important;
  color: var(--text);
  font-size: 12px;
  flex: 1;
  min-width: 100px;
}
.tag-field:focus { outline: none; }

/* Timeline */
.timeline { display: flex; flex-direction: column; gap: 0; }
.timeline-item {
  display: flex;
  gap: 12px;
  padding: 12px 0;
  border-left: 2px solid var(--border);
  margin-left: 6px;
  padding-left: 16px;
  position: relative;
}
.tl-dot {
  position: absolute;
  left: -5px;
  top: 16px;
  width: 8px; height: 8px;
  border-radius: 50%;
  background: var(--border);
}
.tl-dot.tl-created { background: #4ade80; }
.tl-dot.tl-status { background: #60a5fa; }
.tl-dot.tl-other { background: #fbbf24; }
.tl-content { display: flex; flex-direction: column; gap: 2px; }
.tl-action { font-size: 11px; color: var(--text3); text-transform: uppercase; font-family: var(--font-mono); }
.tl-detail { font-size: 13px; color: var(--text); }
.tl-time { font-size: 10px; color: var(--text3); }

/* Footer */
.modal-footer {
  display: flex;
  gap: 8px;
  padding: 14px 20px;
  border-top: 1px solid var(--border);
  align-items: center;
}
.btn-danger {
  display: flex; align-items: center; gap: 5px;
  padding: 7px 14px;
  font-size: 12px;
  background: rgba(239,68,68,0.12);
  color: #f87171;
  border: 1px solid rgba(239,68,68,0.3);
  border-radius: var(--radius);
  cursor: pointer;
  transition: all 0.15s;
}
.btn-danger:hover { background: rgba(239,68,68,0.2); }

/* Status badges (scoped copy) */
.status-badge { font-size: 10px; padding: 2px 8px; border-radius: 4px; font-weight: 500; }
.status-open { background: rgba(234,179,8,0.15); color: #fbbf24; }
.status-in_progress { background: rgba(59,130,246,0.15); color: #60a5fa; }
.status-solved { background: rgba(34,197,94,0.15); color: #4ade80; }
.status-closed { background: rgba(100,116,139,0.15); color: #94a3b8; }
.status-false_positive { background: rgba(249,115,22,0.15); color: #fb923c; }

.mono { font-family: var(--font-mono); }
.empty-state { text-align: center; color: var(--text3); font-size: 13px; }
</style>
