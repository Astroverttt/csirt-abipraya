<template>
  <div class="playbook-panel">
    <!-- No playbook attached -->
    <div v-if="!ticket.playbook" class="no-playbook">
      <div class="no-pb-icon">📋</div>
      <p class="no-pb-text">Belum ada playbook yang di-attach ke tiket ini.</p>

      <!-- Suggested playbooks -->
      <div v-if="suggestedPlaybooks.length" class="suggestions">
        <p class="sugg-label">Playbook yang disarankan berdasarkan alert ini:</p>
        <div v-for="pb in suggestedPlaybooks" :key="pb.id" class="pb-suggestion">
          <span class="pb-icon">{{ getIcon(pb.icon) }}</span>
          <div class="pb-sugg-info">
            <strong>{{ pb.name }}</strong>
            <span class="pb-sugg-meta">{{ pb.steps.length }} steps · {{ pb.triggers.length }} triggers</span>
          </div>
          <button class="btn btn-primary btn-sm" @click="attachPlaybook(pb.id)">Attach</button>
        </div>
      </div>

      <!-- Manual attach -->
      <div class="manual-attach">
        <span class="manual-label">Atau pilih manual:</span>
        <div class="manual-row">
          <select v-model="selectedPbId">
            <option value="">-- Pilih Playbook --</option>
            <option v-for="pb in allActivePlaybooks" :key="pb.id" :value="pb.id">{{ getIcon(pb.icon) }} {{ pb.name }}</option>
          </select>
          <button class="btn btn-ghost btn-sm" :disabled="!selectedPbId" @click="attachManual">Attach</button>
        </div>
      </div>
    </div>

    <!-- Playbook attached -->
    <div v-else class="playbook-active">
      <!-- Header progress -->
      <div class="pb-header">
        <div class="pb-header-top">
          <div class="pb-info">
            <span class="pb-icon-lg">{{ getIcon(currentPlaybook?.icon) }}</span>
            <div>
              <span class="pb-name">{{ ticket.playbook.playbookName }}</span>
              <span class="pb-progress-text">
                {{ ticket.playbook.completedSteps }} / {{ ticket.playbook.totalSteps }} steps selesai
              </span>
              <span class="pb-author" v-if="currentPlaybook?.createdBy">
                · Dibuat oleh {{ currentPlaybook.createdBy }}
              </span>
            </div>
          </div>
          <span class="progress-pct" :class="progressPercent === 100 ? 'complete' : ''">{{ progressPercent }}%</span>
        </div>
        <div class="progress-bar">
          <div
            class="progress-fill"
            :style="{ width: progressPercent + '%' }"
            :class="progressPercent === 100 ? 'complete' : ''"
          ></div>
        </div>
        </div>
        <div v-if="ticket.playbook.completedAt" class="pb-completed-badge">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
          Semua step selesai!
        </div>
      </div>

      <!-- Playbook Markdown Description -->
      <div v-if="currentPlaybook?.description" class="pb-desc-markdown" v-html="parseMarkdown(currentPlaybook.description)"></div>

      <!-- Step list -->
      <div class="steps-list">
        <div
          v-for="step in currentPlaybookSteps"
          :key="step.id"
          class="step-item"
          :class="{ checked: stepProgress(step.id)?.checked }"
        >
          <!-- Checkbox -->
          <div class="step-check" @click="toggleStep(step)">
            <div class="check-box" :class="{ done: stepProgress(step.id)?.checked }">
              <svg v-if="stepProgress(step.id)?.checked" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
            </div>
          </div>

          <!-- Content -->
          <div class="step-content">
            <div class="step-title-row">
              <span class="step-num">{{ step.order }}</span>
              <span class="step-title" :class="{ crossed: stepProgress(step.id)?.checked }">
                {{ step.title }}
              </span>
            </div>
            <div class="step-badges">
              <span class="category-badge" :class="`cat-${step.category}`">{{ step.category }}</span>
              <span v-if="step.requiresEvidence" class="ev-required" :class="{ 'ev-missing': stepProgress(step.id)?.checked && !hasEvidenceForStep(step.id) }">
                📎 evidence {{ step.requiresEvidence && stepProgress(step.id)?.checked && !hasEvidenceForStep(step.id) ? 'missing!' : 'required' }}
              </span>
              <span class="est-time">~{{ step.estimatedMinutes }}m</span>
            </div>

            <p class="step-desc">{{ step.description }}</p>

            <!-- Check info -->
            <div v-if="stepProgress(step.id)?.checked && stepProgress(step.id)?.checkedAt" class="step-checked-info">
              ✓ Completed {{ formatDate(stepProgress(step.id).checkedAt) }}
              <span v-if="stepProgress(step.id).checkedBy"> by {{ stepProgress(step.id).checkedBy }}</span>
            </div>

            <!-- Step note -->
            <div v-if="expandedStep === step.id || stepProgress(step.id)?.note" class="step-note">
              <textarea
                :value="stepNotes[step.id] ?? stepProgress(step.id)?.note ?? ''"
                @input="stepNotes[step.id] = $event.target.value"
                @blur="saveStepNote(step.id)"
                placeholder="Catatan untuk step ini..."
                rows="2"
              ></textarea>
            </div>

            <!-- Evidence terkait step ini -->
            <div class="step-evidence" v-if="evidenceForStep(step.id).length">
              <span v-for="ev in evidenceForStep(step.id)" :key="ev.id" class="ev-chip">
                📎 {{ ev.fileName }}
              </span>
            </div>

            <!-- Step actions -->
            <div class="step-actions-row">
              <button class="btn-tiny" @click="expandedStep = expandedStep === step.id ? null : step.id">
                📝 Note
              </button>
              <button class="btn-tiny" @click="$emit('upload-evidence', step.id)">
                📎 Upload
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Detach playbook -->
      <div class="pb-footer">
        <button class="btn btn-ghost btn-sm" @click="detachPlaybook">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
          Detach Playbook
        </button>
      </div>
    </div>
  <!-- </div> -->
</template>

<script setup>
import { ref, computed } from 'vue'
import { getAllPlaybooks, matchPlaybooks, attachPlaybookToTicket, updateStepProgress, getPlaybookIcon } from '../utils/playbookStore'
import { updateTicket } from '../utils/ticketStore'
import { parseMarkdown } from '../utils/markdown'

const props = defineProps({
  ticket: { type: Object, required: true },
})

const emit = defineEmits(['ticket-updated', 'upload-evidence'])

const expandedStep = ref(null)
const stepNotes = ref({})
const selectedPbId = ref('')

const allActivePlaybooks = computed(() => getAllPlaybooks().filter(p => p.isActive))
const suggestedPlaybooks = computed(() => matchPlaybooks(props.ticket))

const progressPercent = computed(() => {
  if (!props.ticket.playbook) return 0
  const { completedSteps, totalSteps } = props.ticket.playbook
  return totalSteps ? Math.round((completedSteps / totalSteps) * 100) : 0
})

const currentPlaybook = computed(() =>
  allActivePlaybooks.value.find(pb => pb.id === props.ticket.playbook?.playbookId)
)

const currentPlaybookSteps = computed(() =>
  currentPlaybook.value?.steps?.slice().sort((a, b) => a.order - b.order) || []
)

function getIcon(icon) {
  return getPlaybookIcon(icon)
}

function stepProgress(stepId) {
  return props.ticket.playbook?.steps?.[stepId] || null
}

function evidenceForStep(stepId) {
  return (props.ticket.evidence || []).filter(e => e.linkedStepId === stepId)
}

function hasEvidenceForStep(stepId) {
  return evidenceForStep(stepId).length > 0
}

async function toggleStep(step) {
  const current = stepProgress(step.id)

  // Advisory warning for requiresEvidence
  if (!current?.checked && step.requiresEvidence && !hasEvidenceForStep(step.id)) {
    // Show warning but don't block
  }

  const updated = updateStepProgress(props.ticket.playbook, step.id, {
    checked: !current?.checked,
    checkedAt: !current?.checked ? new Date().toISOString() : null,
    checkedBy: !current?.checked ? 'analyst' : null,
    note: stepNotes.value[step.id] ?? current?.note ?? '',
  })
  const updatedTicket = await updateTicket(props.ticket.id, { playbook: updated })
  emit('ticket-updated', updatedTicket)
}

async function saveStepNote(stepId) {
  if (stepNotes.value[stepId] === undefined) return
  const updated = updateStepProgress(props.ticket.playbook, stepId, {
    note: stepNotes.value[stepId]
  })
  const updatedTicket = await updateTicket(props.ticket.id, { playbook: updated })
  emit('ticket-updated', updatedTicket)
}

async function attachPlaybook(pbId) {
  const progress = attachPlaybookToTicket(props.ticket, pbId)
  if (!progress) return
  const updatedTicket = await updateTicket(props.ticket.id, { playbook: progress })
  emit('ticket-updated', updatedTicket)
}

function attachManual() {
  if (selectedPbId.value) attachPlaybook(selectedPbId.value)
}

async function detachPlaybook() {
  if (!confirm('Detach playbook dari tiket ini?')) return
  const updatedTicket = await updateTicket(props.ticket.id, { playbook: null })
  emit('ticket-updated', updatedTicket)
}

function formatDate(dateStr) {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('id-ID', {
    day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit'
  })
}
</script>

<style scoped>
.playbook-panel { }

/* No playbook state */
.no-playbook {
  text-align: center;
  padding: 20px 0;
}
.no-pb-icon {
  font-size: 32px;
  margin-bottom: 8px;
}
.no-pb-text {
  color: var(--text3);
  font-size: 13px;
  margin-bottom: 20px;
}

.suggestions {
  text-align: left;
  margin-bottom: 20px;
}
.sugg-label {
  font-size: 11px;
  color: var(--text3);
  font-family: var(--font-mono);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  margin-bottom: 10px;
}
.pb-suggestion {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  background: var(--bg3);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  margin-bottom: 6px;
  transition: all 0.15s;
}
.pb-suggestion:hover {
  border-color: var(--accent);
}
.pb-icon {
  font-size: 20px;
}
.pb-sugg-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.pb-sugg-info strong {
  font-size: 13px;
  color: var(--text);
}
.pb-sugg-meta {
  font-size: 11px;
  color: var(--text3);
  font-family: var(--font-mono);
}

.manual-attach {
  text-align: left;
  padding-top: 12px;
  border-top: 1px solid var(--border);
}
.manual-label {
  font-size: 11px;
  color: var(--text3);
  font-family: var(--font-mono);
}
.manual-row {
  display: flex;
  gap: 8px;
  margin-top: 8px;
}
.manual-row select {
  flex: 1;
}

/* Active playbook */
.playbook-active { }

.pb-header {
  margin-bottom: 16px;
}
.pb-header-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}
.pb-info {
  display: flex;
  align-items: center;
  gap: 10px;
}
.pb-icon-lg {
  font-size: 24px;
}
.pb-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--text);
  display: block;
}
.pb-progress-text {
  font-size: 11px;
  color: var(--text3);
  font-family: var(--font-mono);
}
.pb-author {
  font-size: 11px;
  color: var(--text3);
  font-family: var(--font-mono);
}
.progress-pct {
  font-size: 18px;
  font-weight: 700;
  color: var(--accent);
  font-family: var(--font-mono);
}
.progress-pct.complete {
  color: var(--low);
}

.progress-bar {
  height: 6px;
  background: var(--border2);
  border-radius: 3px;
  overflow: hidden;
}
.progress-fill {
  height: 100%;
  background: var(--accent);
  border-radius: 3px;
  transition: width 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}
.progress-fill.complete {
  background: var(--low);
}

.pb-completed-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 8px;
  padding: 8px 12px;
  border-radius: var(--radius);
  background: rgba(34, 197, 94, 0.08);
  border: 1px solid rgba(34, 197, 94, 0.2);
  color: #4ade80;
  font-size: 12px;
  font-weight: 500;
}

/* Markdown Description */
.pb-desc-markdown {
  background: var(--bg2);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 12px;
  margin-bottom: 16px;
  color: var(--text2);
  font-size: 12px;
  line-height: 1.5;
  font-family: var(--font-body);
}
.pb-desc-markdown :deep(h1), .pb-desc-markdown :deep(h2), .pb-desc-markdown :deep(h3) { margin-top: 0; margin-bottom: 8px; color: var(--text); font-size: 14px; }
.pb-desc-markdown :deep(p) { margin: 0 0 8px; }
.pb-desc-markdown :deep(p:last-child) { margin-bottom: 0; }
.pb-desc-markdown :deep(img) { max-width: 100%; border-radius: 6px; margin: 8px 0; border: 1px solid var(--border); }
.pb-desc-markdown :deep(code) { background: rgba(0,0,0,0.2); padding: 2px 4px; border-radius: 4px; font-family: monospace; }
.pb-desc-markdown :deep(ul) { margin: 0 0 8px; padding-left: 20px; }

/* Steps */
.steps-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.step-item {
  display: flex;
  gap: 12px;
  padding: 12px;
  border-radius: var(--radius);
  background: var(--bg2);
  border: 1px solid var(--border);
  transition: all 0.15s;
}
.step-item:hover {
  border-color: var(--border2);
}
.step-item.checked {
  opacity: 0.65;
  background: rgba(17, 22, 32, 0.6);
}

.step-check {
  flex-shrink: 0;
  padding-top: 2px;
  cursor: pointer;
}
.check-box {
  width: 22px;
  height: 22px;
  border: 2px solid var(--border2);
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  background: transparent;
}
.check-box:hover {
  border-color: var(--accent);
}
.check-box.done {
  background: var(--low);
  border-color: var(--low);
  color: white;
}

.step-content {
  flex: 1;
  min-width: 0;
}
.step-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}
.step-num {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: var(--bg3);
  border: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  font-weight: 700;
  color: var(--text3);
  font-family: var(--font-mono);
  flex-shrink: 0;
}
.step-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text);
}
.step-title.crossed {
  text-decoration: line-through;
  color: var(--text3);
}

.step-badges {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 6px;
}
.category-badge {
  font-size: 10px;
  padding: 1px 8px;
  border-radius: 4px;
  font-family: var(--font-mono);
  text-transform: uppercase;
  letter-spacing: 0.03em;
  font-weight: 500;
}
.cat-identification { background: rgba(59,130,246,0.12); color: #60a5fa; border: 1px solid rgba(59,130,246,0.25); }
.cat-containment    { background: rgba(239,68,68,0.12);  color: #f87171; border: 1px solid rgba(239,68,68,0.25); }
.cat-eradication    { background: rgba(249,115,22,0.12); color: #fb923c; border: 1px solid rgba(249,115,22,0.25); }
.cat-recovery       { background: rgba(34,197,94,0.12);  color: #4ade80; border: 1px solid rgba(34,197,94,0.25); }
.cat-lessons        { background: rgba(168,85,247,0.12); color: #c084fc; border: 1px solid rgba(168,85,247,0.25); }

.ev-required {
  background: rgba(234,179,8,0.1);
  color: #fbbf24;
  border: 1px solid rgba(234,179,8,0.25);
  font-size: 10px;
  padding: 1px 6px;
  border-radius: 4px;
  font-family: var(--font-mono);
}
.ev-required.ev-missing {
  background: rgba(239,68,68,0.1);
  color: #f87171;
  border-color: rgba(239,68,68,0.25);
  animation: pulse 2s ease infinite;
}

.est-time {
  font-size: 10px;
  color: var(--text3);
  font-family: var(--font-mono);
}

.step-desc {
  font-size: 12px;
  color: var(--text2);
  line-height: 1.5;
  margin: 0 0 6px;
}

.step-checked-info {
  font-size: 10px;
  color: var(--low);
  font-family: var(--font-mono);
  margin-bottom: 6px;
}

.step-note textarea {
  width: 100%;
  background: var(--bg3);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  color: var(--text);
  padding: 8px 10px;
  font-size: 12px;
  font-family: var(--font-body);
  resize: vertical;
  margin-bottom: 6px;
}
.step-note textarea:focus {
  outline: none;
  border-color: var(--accent);
}

.step-evidence {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-bottom: 6px;
}
.ev-chip {
  font-size: 10px;
  padding: 2px 8px;
  border-radius: 4px;
  background: rgba(59,130,246,0.1);
  color: #60a5fa;
  border: 1px solid rgba(59,130,246,0.2);
  font-family: var(--font-mono);
}

.step-actions-row {
  display: flex;
  gap: 6px;
}
.btn-tiny {
  padding: 3px 8px;
  font-size: 10px;
  border-radius: 4px;
  background: var(--bg3);
  border: 1px solid var(--border);
  color: var(--text3);
  cursor: pointer;
  transition: all 0.15s;
}
.btn-tiny:hover {
  color: var(--text);
  border-color: var(--accent);
}

.btn-sm {
  padding: 5px 12px;
  font-size: 11px;
}

.pb-footer {
  margin-top: 16px;
  padding-top: 12px;
  border-top: 1px solid var(--border);
}

@keyframes pulse { 50% { opacity: 0.6; } }
</style>
