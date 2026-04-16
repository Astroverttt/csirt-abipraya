<template>
  <div class="evidence-section">
    <h4 class="section-title">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21.44 11.05l-9.19 9.19a6 6 0 01-8.49-8.49l9.19-9.19a4 4 0 015.66 5.66l-9.2 9.19a2 2 0 01-2.83-2.83l8.49-8.48"/></svg>
      Evidence & Artifacts
    </h4>

    <!-- Upload area -->
    <div
      class="upload-zone"
      :class="{ dragging: isDragging }"
      @dragover.prevent="isDragging = true"
      @dragleave="isDragging = false"
      @drop.prevent="onDrop"
      @click="fileInput?.click()"
    >
      <input ref="fileInput" type="file" multiple hidden @change="onFileSelect" />
      <div class="upload-content">
        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" style="opacity:0.5;">
          <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/>
        </svg>
        <p>Drag & drop file di sini, atau <span class="upload-link">klik untuk browse</span></p>
        <span class="hint">Semua tipe file · Maks. 4MB per file</span>
      </div>
    </div>

    <!-- Upload progress -->
    <div v-if="uploading" class="upload-progress">
      <div class="upload-spinner"></div>
      <span>Uploading {{ uploadingFile }}...</span>
    </div>

    <!-- Error -->
    <div v-if="uploadError" class="upload-error">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
      {{ uploadError }}
      <button class="upload-error-dismiss" @click="uploadError = ''">✕</button>
    </div>

    <!-- Linked step selector -->
    <div v-if="availableSteps?.length" class="link-controls">
      <div class="link-step">
        <label>Link ke step:</label>
        <select v-model="linkedStepId">
          <option value="">Tidak terkait step</option>
          <option v-for="step in availableSteps" :key="step.id" :value="step.id">
            {{ step.order }}. {{ step.title }}
          </option>
        </select>
      </div>
    </div>

    <!-- Description input -->
    <div class="ev-desc-input">
      <input
        v-model="evDescription"
        placeholder="Deskripsi evidence (opsional)"
      />
    </div>

    <!-- Gallery -->
    <EvidenceGallery
      :evidence="ticket.evidence || []"
      :steps="availableSteps || []"
      @remove="removeEv"
      @download="downloadEv"
    />

    <!-- Storage warning -->
    <div v-if="storageWarning" class="storage-warn">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
      localStorage usage: {{ storageWarning }}% — Pertimbangkan untuk menghapus evidence lama.
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { addEvidence, removeEvidence, downloadEvidence, getPlaybookStorageUsage } from '../utils/playbookStore'
import { updateTicket } from '../utils/ticketStore'
import EvidenceGallery from './EvidenceGallery.vue'

const props = defineProps({
  ticket: { type: Object, required: true },
  availableSteps: { type: Array, default: () => [] },
})

const emit = defineEmits(['ticket-updated'])

const fileInput = ref(null)
const isDragging = ref(false)
const uploading = ref(false)
const uploadingFile = ref('')
const uploadError = ref('')
const linkedStepId = ref('')
const evDescription = ref('')

const storageWarning = computed(() => {
  const usage = getPlaybookStorageUsage()
  return usage.isWarning ? usage.percentage : null
})

async function handleFiles(files) {
  uploadError.value = ''
  for (const file of files) {
    uploading.value = true
    uploadingFile.value = file.name
    try {
      const updatedEvidence = await addEvidence(props.ticket, file, {
        linkedStepId: linkedStepId.value || null,
        description: evDescription.value,
        uploadedBy: 'analyst',
      })
      const updatedTicket = await updateTicket(props.ticket.id, { evidence: updatedEvidence })
      emit('ticket-updated', updatedTicket)
      evDescription.value = ''
    } catch (e) {
      uploadError.value = e.message
    } finally {
      uploading.value = false
      uploadingFile.value = ''
    }
  }
}

function onDrop(e) {
  isDragging.value = false
  handleFiles([...e.dataTransfer.files])
}

function onFileSelect(e) {
  handleFiles([...e.target.files])
  e.target.value = '' // reset input
}

async function removeEv(evId) {
  if (!confirm('Hapus evidence ini?')) return
  const updated = removeEvidence(props.ticket, evId)
  const updatedTicket = await updateTicket(props.ticket.id, { evidence: updated })
  emit('ticket-updated', updatedTicket)
}

function downloadEv(ev) {
  downloadEvidence(ev)
}
</script>

<style scoped>
.evidence-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 600;
  color: var(--text);
  margin: 0;
}

.upload-zone {
  border: 1.5px dashed var(--border2);
  border-radius: var(--radius-lg);
  padding: 28px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
  color: var(--text3);
  background: transparent;
}
.upload-zone:hover,
.upload-zone.dragging {
  border-color: var(--accent);
  background: rgba(59, 130, 246, 0.04);
  color: var(--text2);
}
.upload-zone.dragging {
  background: rgba(59, 130, 246, 0.08);
  transform: scale(1.01);
}
.upload-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}
.upload-content p {
  font-size: 13px;
  margin: 0;
}
.upload-link {
  color: var(--accent);
  font-weight: 500;
}
.hint {
  font-size: 11px;
  color: var(--text3);
  font-family: var(--font-mono);
}

.upload-progress {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  border-radius: var(--radius);
  background: rgba(59, 130, 246, 0.08);
  border: 1px solid rgba(59, 130, 246, 0.2);
  font-size: 12px;
  color: #60a5fa;
  animation: pulse 1.5s ease infinite;
}
.upload-spinner {
  width: 14px; height: 14px;
  border: 2px solid rgba(59, 130, 246, 0.3);
  border-top-color: #60a5fa;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.upload-error {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  border-radius: var(--radius);
  background: rgba(239, 68, 68, 0.08);
  border: 1px solid rgba(239, 68, 68, 0.2);
  font-size: 12px;
  color: #f87171;
}
.upload-error-dismiss {
  margin-left: auto;
  background: none;
  border: none;
  color: inherit;
  cursor: pointer;
  opacity: 0.7;
  font-size: 14px;
}
.upload-error-dismiss:hover { opacity: 1; }

.link-controls {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}
.link-step {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
}
.link-step label {
  font-size: 11px;
  color: var(--text3);
  white-space: nowrap;
  font-family: var(--font-mono);
}
.link-step select {
  flex: 1;
  min-width: 180px;
}

.ev-desc-input input {
  width: 100%;
  background: var(--bg3);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 8px 12px;
  font-size: 12px;
  color: var(--text);
  font-family: var(--font-body);
}
.ev-desc-input input:focus {
  outline: none;
  border-color: var(--accent);
}

.storage-warn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: var(--radius);
  background: rgba(234, 179, 8, 0.08);
  border: 1px solid rgba(234, 179, 8, 0.2);
  font-size: 11px;
  color: #fbbf24;
}

@keyframes spin { to { transform: rotate(360deg); } }
@keyframes pulse { 50% { opacity: 0.7; } }
</style>
