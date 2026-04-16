<template>
  <div class="evidence-gallery" v-if="evidence.length">
    <div class="gallery-header">
      <span class="gallery-count">{{ evidence.length }} file{{ evidence.length > 1 ? 's' : '' }} tersimpan</span>
      <span class="total-size">Total: {{ totalSize }}</span>
    </div>

    <div class="gallery-grid">
      <div v-for="ev in evidence" :key="ev.id" class="ev-item">
        <!-- Preview thumbnail -->
        <div class="ev-thumb" @click="previewItem = isImage(ev.fileType) ? ev : null">
          <img v-if="isImage(ev.fileType)" :src="ev.base64" :alt="ev.fileName" loading="lazy" />
          <div v-else class="ev-icon-wrap">
            <span class="ev-ext">{{ getExt(ev.fileName) }}</span>
          </div>
        </div>

        <!-- Info -->
        <div class="ev-info">
          <span class="ev-name" :title="ev.fileName">{{ truncate(ev.fileName, 22) }}</span>
          <div class="ev-meta-row">
            <span class="ev-size">{{ formatFileSize(ev.fileSize) }}</span>
            <span v-if="ev.linkedStepId" class="ev-step-link">→ step {{ getStepOrder(ev.linkedStepId) }}</span>
          </div>
          <span class="ev-date">{{ timeAgo(ev.uploadedAt) }}</span>
          <p v-if="ev.description" class="ev-desc">{{ ev.description }}</p>
        </div>

        <!-- Actions -->
        <div class="ev-actions">
          <button class="ev-action-btn" @click="$emit('download', ev)" title="Download">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
          </button>
          <button class="ev-action-btn danger" @click="$emit('remove', ev.id)" title="Hapus">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="m19 6-.86 14.14A2 2 0 0116.17 22H7.83a2 2 0 01-1.97-1.86L5 6m5 0V4c0-.55.45-1 1-1h2c.55 0 1 .45 1 1v2"/></svg>
          </button>
        </div>
      </div>
    </div>
  </div>

  <!-- Image preview modal -->
  <Teleport to="body">
    <div v-if="previewItem" class="preview-overlay" @click.self="previewItem = null">
      <div class="preview-content">
        <button class="preview-close" @click="previewItem = null">✕</button>
        <img :src="previewItem.base64" :alt="previewItem.fileName" class="preview-img" />
        <p class="preview-name">{{ previewItem.fileName }}</p>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, computed } from 'vue'
import { formatFileSize } from '../utils/playbookStore'

const props = defineProps({
  evidence: { type: Array, default: () => [] },
  steps: { type: Array, default: () => [] },
})

defineEmits(['download', 'remove', 'preview'])

const previewItem = ref(null)

const totalSize = computed(() => {
  const total = props.evidence.reduce((sum, ev) => sum + (ev.fileSize || 0), 0)
  return formatFileSize(total)
})

function isImage(fileType) {
  return fileType?.startsWith('image/')
}

function getExt(fileName) {
  const parts = fileName?.split('.') || []
  return parts.length > 1 ? parts.pop().toUpperCase() : 'FILE'
}

function truncate(str, len) {
  if (!str) return ''
  return str.length > len ? str.slice(0, len - 3) + '...' : str
}

function getStepOrder(stepId) {
  const step = props.steps.find(s => s.id === stepId)
  return step?.order || '?'
}

function timeAgo(dateStr) {
  if (!dateStr) return ''
  const diff = Date.now() - new Date(dateStr).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return 'Just now'
  if (mins < 60) return `${mins}m ago`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  return `${days}d ago`
}
</script>

<style scoped>
.evidence-gallery {
  margin-top: 16px;
}

.gallery-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--border);
}
.gallery-count {
  font-size: 12px;
  font-weight: 600;
  color: var(--text2);
}
.total-size {
  font-size: 11px;
  color: var(--text3);
  font-family: var(--font-mono);
}

.gallery-grid {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.ev-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  background: var(--bg3);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  transition: all 0.15s;
}
.ev-item:hover {
  border-color: var(--border2);
  background: rgba(30, 38, 54, 0.8);
}

.ev-thumb {
  width: 48px;
  height: 48px;
  border-radius: 6px;
  overflow: hidden;
  flex-shrink: 0;
  cursor: pointer;
  background: var(--bg2);
  border: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: center;
}
.ev-thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.ev-icon-wrap {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
}
.ev-ext {
  font-size: 10px;
  font-weight: 700;
  font-family: var(--font-mono);
  color: var(--accent);
  text-transform: uppercase;
}

.ev-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.ev-name {
  font-size: 12px;
  font-weight: 600;
  color: var(--text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.ev-meta-row {
  display: flex;
  align-items: center;
  gap: 8px;
}
.ev-size {
  font-size: 11px;
  color: var(--text3);
  font-family: var(--font-mono);
}
.ev-step-link {
  font-size: 10px;
  color: var(--accent);
  font-family: var(--font-mono);
}
.ev-date {
  font-size: 10px;
  color: var(--text3);
}
.ev-desc {
  font-size: 11px;
  color: var(--text2);
  margin-top: 2px;
  line-height: 1.4;
}

.ev-actions {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex-shrink: 0;
}
.ev-action-btn {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: var(--bg2);
  color: var(--text3);
  cursor: pointer;
  transition: all 0.15s;
}
.ev-action-btn:hover {
  color: var(--text);
  border-color: var(--accent);
  background: rgba(59, 130, 246, 0.1);
}
.ev-action-btn.danger:hover {
  color: #f87171;
  border-color: rgba(239, 68, 68, 0.4);
  background: rgba(239, 68, 68, 0.1);
}

/* Preview modal */
.preview-overlay {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0, 0, 0, 0.85);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  padding: 20px;
  animation: fadeIn 0.2s ease;
}
.preview-content {
  position: relative;
  max-width: 90vw;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  align-items: center;
}
.preview-close {
  position: absolute;
  top: -40px;
  right: 0;
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  transition: all 0.15s;
}
.preview-close:hover {
  background: rgba(239, 68, 68, 0.3);
  border-color: rgba(239, 68, 68, 0.5);
}
.preview-img {
  max-width: 90vw;
  max-height: 80vh;
  border-radius: 8px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
}
.preview-name {
  color: rgba(255, 255, 255, 0.7);
  font-size: 12px;
  margin-top: 12px;
  font-family: var(--font-mono);
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}
</style>
