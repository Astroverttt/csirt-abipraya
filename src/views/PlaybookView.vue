<template>
  <div class="page">
    <!-- Header -->
    <div class="page-header">
      <div>
        <h2>Incident Playbooks</h2>
        <p class="sub">{{ activeCount }} active · {{ playbooks.length }} total playbooks</p>
      </div>
      <div class="header-actions">
        <button class="btn btn-ghost" :class="{ 'btn-active': isAdminMode }" @click="isAdminMode = !isAdminMode">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-2 2 2 2 0 01-2-2v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83 0 2 2 0 010-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 01-2-2 2 2 0 012-2h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 010-2.83 2 2 0 012.83 0l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 012-2 2 2 0 012 2v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 0 2 2 0 010 2.83l-.06.06A1.65 1.65 0 0019.4 9a1.65 1.65 0 001.51 1H21a2 2 0 012 2 2 2 0 01-2 2h-.09a1.65 1.65 0 00-1.51 1z"/></svg>
          {{ isAdminMode ? 'Exit Admin' : 'Admin Mode' }}
        </button>
        <button v-if="isAdminMode" class="btn btn-primary" @click="openCreate">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
          New Playbook
        </button>
      </div>
    </div>

    <!-- Filters -->
    <div class="toolbar-card">
      <input v-model="search" placeholder="Cari playbook..." class="toolbar-search" />
      <div class="filter-pills">
        <span class="fpill" :class="{ active: filterActive === 'all' }" @click="filterActive = 'all'">All</span>
        <span class="fpill" :class="{ active: filterActive === 'active' }" @click="filterActive = 'active'">Active</span>
        <span class="fpill" :class="{ active: filterActive === 'inactive' }" @click="filterActive = 'inactive'">Inactive</span>
      </div>
      <span class="count-text">{{ filtered.length }} playbook{{ filtered.length !== 1 ? 's' : '' }}</span>
    </div>

    <!-- Playbook Grid -->
    <div v-if="filtered.length" class="playbook-grid">
      <div v-for="pb in filtered" :key="pb.id" class="pb-card" :class="{ inactive: !pb.isActive }">
        <div class="pb-card-header">
          <span class="pb-card-icon">{{ getIcon(pb.icon) }}</span>
          <div class="pb-card-info">
            <span class="pb-card-name">{{ pb.name }}</span>
            <span class="pb-card-id mono">{{ pb.id }}</span>
          </div>
          <span v-if="pb.isDefault" class="pb-default-badge">DEFAULT</span>
          <span class="pb-status-dot" :class="pb.isActive ? 'active' : 'inactive'" :title="pb.isActive ? 'Active' : 'Inactive'"></span>
        </div>

        <p v-if="pb.description" class="pb-card-desc">{{ pb.description }}</p>

        <div class="pb-card-meta">
          <span class="pb-meta-item">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11"/></svg>
            {{ pb.steps?.length || 0 }} steps
          </span>
          <span class="pb-meta-item">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
            {{ pb.triggers?.length || 0 }} triggers
          </span>
          <span class="pb-meta-item est-total">
            ~{{ totalEstimate(pb) }}m
          </span>
        </div>

        <!-- Trigger tags -->
        <div class="pb-triggers">
          <span v-for="(trigger, i) in pb.triggers?.slice(0, 4)" :key="i" class="trigger-tag" :class="`tt-${trigger.type}`">
            {{ trigger.type === 'severity' ? '⚠' : '#' }} {{ trigger.value }}
          </span>
          <span v-if="(pb.triggers?.length || 0) > 4" class="trigger-tag tt-more">+{{ pb.triggers.length - 4 }}</span>
        </div>

        <!-- Actions -->
        <div class="pb-card-actions">
          <button class="btn btn-ghost btn-sm" @click="previewPlaybook = pb">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
            View
          </button>
          <template v-if="isAdminMode">
            <button class="btn btn-ghost btn-sm" @click="openEdit(pb)">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
              Edit
            </button>
            <button class="btn btn-ghost btn-sm" @click="toggleActive(pb)">
              {{ pb.isActive ? 'Deactivate' : 'Activate' }}
            </button>
            <button v-if="!pb.isDefault" class="btn btn-danger btn-sm" @click="handleDelete(pb.id)">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="m19 6-.86 14.14A2 2 0 0116.17 22H7.83a2 2 0 01-1.97-1.86L5 6m5 0V4c0-.55.45-1 1-1h2c.55 0 1 .45 1 1v2"/></svg>
            </button>
          </template>
        </div>
      </div>
    </div>

    <div v-else class="empty-state" style="margin-top: 40px; padding: 40px;">
      <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="var(--text3)" stroke-width="1" style="margin-bottom: 12px;"><path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11"/></svg>
      <p>Tidak ada playbook yang cocok dengan filter.</p>
    </div>

    <!-- Preview Modal -->
    <Teleport to="body">
      <div v-if="previewPlaybook" class="preview-overlay" @click.self="previewPlaybook = null">
        <div class="preview-modal">
          <div class="preview-header">
            <div class="preview-title-row">
              <span class="pb-card-icon" style="font-size:24px;">{{ getIcon(previewPlaybook.icon) }}</span>
              <div>
                <h3>{{ previewPlaybook.name }}</h3>
                <span class="mono" style="font-size:11px; color: var(--text3);">{{ previewPlaybook.id }}</span>
              </div>
            </div>
            <button class="btn-close" @click="previewPlaybook = null">✕</button>
          </div>
          <div class="preview-body">
            <div class="markdown-preview" v-if="previewPlaybook.description" v-html="parseMarkdown(previewPlaybook.description)" style="margin-bottom: 16px;"></div>

            <h4 class="preview-section-title">Triggers</h4>
            <div class="pb-triggers" style="margin-bottom: 16px;">
              <span v-for="(trigger, i) in previewPlaybook.triggers" :key="i" class="trigger-tag" :class="`tt-${trigger.type}`">
                {{ trigger.type === 'severity' ? '⚠' : '#' }} {{ trigger.value }}
              </span>
            </div>

            <h4 class="preview-section-title">Steps ({{ previewPlaybook.steps?.length || 0 }})</h4>
            <div class="preview-steps">
              <div v-for="step in sortedSteps(previewPlaybook)" :key="step.id" class="preview-step">
                <span class="step-num-preview">{{ step.order }}</span>
                <div class="preview-step-content">
                  <div class="preview-step-title">{{ step.title }}</div>
                  <p class="preview-step-desc">{{ step.description }}</p>
                  <div class="preview-step-meta">
                    <span class="category-badge" :class="`cat-${step.category}`">{{ step.category }}</span>
                    <span v-if="step.requiresEvidence" class="ev-required">📎 evidence</span>
                    <span class="est-time">~{{ step.estimatedMinutes }}m</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Editor Modal -->
    <PlaybookEditor
      v-if="showEditor"
      :playbook="editingPlaybook"
      @save="onSave"
      @close="showEditor = false"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { loadPlaybooks as fetchPlaybooks, getAllPlaybooks, createPlaybook, updatePlaybook, deletePlaybook, seedDefaultPlaybooks, getPlaybookIcon } from '../utils/playbookStore'
import { DEFAULT_PLAYBOOKS } from '../utils/defaultPlaybooks'
import PlaybookEditor from '../components/PlaybookEditor.vue'
import { parseMarkdown } from '../utils/markdown'

const playbooks = ref([])
const isAdminMode = ref(false)
const search = ref('')
const filterActive = ref('all')
const showEditor = ref(false)
const editingPlaybook = ref(null)
const previewPlaybook = ref(null)

onMounted(async () => {
  seedDefaultPlaybooks(DEFAULT_PLAYBOOKS)
  await fetchPlaybooks()
  reloadPlaybooks()
})

function reloadPlaybooks() {
  playbooks.value = getAllPlaybooks()
}

const activeCount = computed(() => playbooks.value.filter(p => p.isActive).length)

const filtered = computed(() => playbooks.value.filter(pb => {
  const matchSearch = !search.value || pb.name.toLowerCase().includes(search.value.toLowerCase()) || pb.description?.toLowerCase().includes(search.value.toLowerCase())
  const matchActive = filterActive.value === 'all' ||
                      (filterActive.value === 'active' && pb.isActive) ||
                      (filterActive.value === 'inactive' && !pb.isActive)
  return matchSearch && matchActive
}))

function getIcon(icon) {
  return getPlaybookIcon(icon)
}

function totalEstimate(pb) {
  return (pb.steps || []).reduce((sum, s) => sum + (s.estimatedMinutes || 0), 0)
}

function sortedSteps(pb) {
  return (pb.steps || []).slice().sort((a, b) => a.order - b.order)
}

function openCreate() {
  editingPlaybook.value = null
  showEditor.value = true
}

function openEdit(pb) {
  editingPlaybook.value = { ...pb, steps: pb.steps.map(s => ({ ...s })), triggers: pb.triggers.map(t => ({ ...t })) }
  showEditor.value = true
}

async function onSave(data) {
  if (editingPlaybook.value?.id) {
    await updatePlaybook(editingPlaybook.value.id, data)
  } else {
    await createPlaybook(data)
  }
  showEditor.value = false
  reloadPlaybooks()
}

async function handleDelete(id) {
  if (!confirm('Yakin hapus playbook ini? Aksi ini tidak bisa dibatalkan.')) return
  try {
    await deletePlaybook(id)
    reloadPlaybooks()
  } catch (e) {
    alert(e.message)
  }
}

async function toggleActive(pb) {
  await updatePlaybook(pb.id, { isActive: !pb.isActive })
  reloadPlaybooks()
}
</script>

<style scoped>
.page { padding: 28px; max-width: 1200px; }
.page-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px; flex-wrap: wrap; gap: 12px; }
.page-header h2 { font-family: var(--font-display); font-size: 20px; font-weight: 700; }
.sub { color: var(--text3); font-size: 12px; margin-top: 2px; font-family: var(--font-mono); }
.header-actions { display: flex; gap: 8px; }

.btn-active {
  background: rgba(59, 130, 246, 0.12) !important;
  color: #60a5fa !important;
  border-color: rgba(59, 130, 246, 0.3) !important;
}

/* Toolbar */
.toolbar-card {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 16px;
  background: var(--bg2);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  margin-bottom: 20px;
}
.toolbar-search { flex: 1; min-width: 200px; }

.filter-pills { display: flex; gap: 4px; }
.fpill {
  padding: 5px 12px;
  border-radius: 6px;
  font-size: 11px;
  cursor: pointer;
  border: 1px solid var(--border);
  background: var(--bg3);
  color: var(--text3);
  transition: all 0.15s;
}
.fpill:hover { color: var(--text); border-color: var(--accent); }
.fpill.active { background: rgba(59,130,246,0.12); color: #60a5fa; border-color: rgba(59,130,246,0.3); }
.count-text { font-size: 11px; color: var(--text3); font-family: var(--font-mono); margin-left: auto; white-space: nowrap; }

/* Playbook Grid */
.playbook-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 14px;
}

.pb-card {
  background: var(--bg2);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 18px;
  transition: all 0.2s;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.pb-card:hover {
  border-color: var(--border2);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
}
.pb-card.inactive {
  opacity: 0.5;
}

.pb-card-header {
  display: flex;
  align-items: center;
  gap: 10px;
}
.pb-card-icon { font-size: 26px; }
.pb-card-info { flex: 1; display: flex; flex-direction: column; }
.pb-card-name { font-size: 14px; font-weight: 600; color: var(--text); }
.pb-card-id { font-size: 10px; color: var(--text3); }

.pb-default-badge {
  font-size: 9px;
  padding: 2px 6px;
  border-radius: 4px;
  background: rgba(168, 85, 247, 0.12);
  color: #c084fc;
  border: 1px solid rgba(168, 85, 247, 0.25);
  font-family: var(--font-mono);
  font-weight: 600;
  letter-spacing: 0.04em;
}

.pb-status-dot {
  width: 8px; height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}
.pb-status-dot.active { background: var(--low); box-shadow: 0 0 6px var(--low); }
.pb-status-dot.inactive { background: var(--text3); }

.pb-card-desc {
  font-size: 12px;
  color: var(--text2);
  line-height: 1.5;
  margin: 0;
}

.pb-card-meta {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}
.pb-meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  color: var(--text3);
  font-family: var(--font-mono);
}
.est-total { color: var(--text3); }

.pb-triggers {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}
.trigger-tag {
  font-size: 10px;
  padding: 2px 8px;
  border-radius: 4px;
  font-family: var(--font-mono);
}
.tt-rule_group {
  background: rgba(59,130,246,0.1);
  color: #60a5fa;
  border: 1px solid rgba(59,130,246,0.2);
}
.tt-severity {
  background: rgba(249,115,22,0.1);
  color: #fb923c;
  border: 1px solid rgba(249,115,22,0.2);
}
.tt-more {
  background: var(--bg3);
  color: var(--text3);
  border: 1px solid var(--border);
}

.pb-card-actions {
  display: flex;
  gap: 6px;
  margin-top: 4px;
  flex-wrap: wrap;
}

.btn-sm {
  padding: 5px 10px;
  font-size: 11px;
}

.btn-danger {
  display: flex; align-items: center; gap: 5px;
  padding: 5px 10px;
  font-size: 11px;
  background: rgba(239,68,68,0.12);
  color: #f87171;
  border: 1px solid rgba(239,68,68,0.3);
  border-radius: var(--radius);
  cursor: pointer;
  transition: all 0.15s;
}
.btn-danger:hover { background: rgba(239,68,68,0.2); }

/* Preview modal */
.preview-overlay {
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
.preview-modal {
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  width: 100%;
  max-width: 640px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: 0 20px 60px rgba(0,0,0,0.4);
}
.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border);
}
.preview-title-row { display: flex; align-items: center; gap: 10px; }
.preview-header h3 { font-family: var(--font-display); font-size: 16px; font-weight: 700; }

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

.preview-body {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}
.preview-section-title {
  font-size: 11px;
  font-weight: 600;
  color: var(--text3);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 10px;
  font-family: var(--font-mono);
}

.preview-steps { display: flex; flex-direction: column; gap: 6px; }
.preview-step {
  display: flex;
  gap: 10px;
  padding: 10px 12px;
  background: var(--bg2);
  border: 1px solid var(--border);
  border-radius: var(--radius);
}
.step-num-preview {
  width: 24px; height: 24px;
  border-radius: 50%;
  background: var(--bg3);
  border: 1px solid var(--border2);
  display: flex; align-items: center; justify-content: center;
  font-size: 11px; font-weight: 700;
  color: var(--accent);
  font-family: var(--font-mono);
  flex-shrink: 0;
}
.preview-step-content { flex: 1; }
.preview-step-title { font-size: 13px; font-weight: 600; color: var(--text); margin-bottom: 2px; }
.preview-step-desc { font-size: 11px; color: var(--text2); line-height: 1.4; margin: 0 0 6px; }
.preview-step-meta { display: flex; gap: 6px; flex-wrap: wrap; align-items: center; }

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
  background: rgba(234,179,8,0.1); color: #fbbf24;
  border: 1px solid rgba(234,179,8,0.25); font-size: 10px;
  padding: 1px 6px; border-radius: 4px; font-family: var(--font-mono);
}
.est-time {
  font-size: 10px; color: var(--text3); font-family: var(--font-mono);
}

.mono { font-family: var(--font-mono); }

.empty-state {
  text-align: center;
  color: var(--text3);
  font-size: 13px;
  line-height: 1.8;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.markdown-preview {
  color: var(--text2);
  font-size: 13px;
  font-family: var(--font-body);
  line-height: 1.6;
}
.markdown-preview :deep(h1), .markdown-preview :deep(h2), .markdown-preview :deep(h3) { margin-top: 0; margin-bottom: 10px; color: var(--text); }
.markdown-preview :deep(img) { max-width: 100%; border-radius: 8px; margin: 8px 0; }
.markdown-preview :deep(code) { background: rgba(0,0,0,0.2); padding: 2px 4px; border-radius: 4px; font-family: monospace; }
</style>
