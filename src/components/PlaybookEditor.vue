<template>
  <div class="editor-overlay" @click.self="$emit('close')">
    <div class="editor-container">
      <!-- Header -->
      <div class="editor-header">
        <h3>{{ isEdit ? 'Edit Playbook' : 'New Playbook' }}</h3>
        <button class="btn-close" @click="$emit('close')">✕</button>
      </div>

      <div class="editor-body">
        <!-- Section 1: Basic Info -->
        <div class="editor-section">
          <h4 class="section-label">Informasi Dasar</h4>

          <!-- Import Templates -->
          <div class="form-group template-import" v-if="!isEdit">
            <label>Import dari Template / Internet</label>
            <div class="import-row">
              <select v-model="selectedTemplate" @change="importTemplate">
                <option value="">-- Pilih Template --</option>
                <option value="owasp-injection">OWASP Top 1: Injection</option>
                <option value="owasp-xss">OWASP Top 3: XSS</option>
                <option value="generic-malware">Generic Malware Template</option>
              </select>
            </div>
            <div class="import-hint" v-if="selectedTemplate">Template playbook telah diisi secara otomatis.</div>
          </div>

          <div class="form-group row-group">
            <div class="col">
              <label>Nama Playbook</label>
              <input v-model="form.name" placeholder="e.g. Malware Detection Response" />
            </div>
            <div class="col">
              <label>Author / Pembuat</label>
              <input v-model="form.createdBy" placeholder="e.g. SecOps Team" />
            </div>
          </div>

          <div class="form-group">
            <div class="label-row">
              <label>Konten & Deskripsi (Markdown Support)</label>
              <div class="view-tabs">
                <span :class="{ active: contentTab === 'edit' }" @click="contentTab = 'edit'">Edit</span>
                <span :class="{ active: contentTab === 'preview' }" @click="contentTab = 'preview'">Preview</span>
              </div>
            </div>
            <textarea v-if="contentTab === 'edit'" v-model="form.description" rows="5" placeholder="Gunakan Markdown untuk format seperti Notion... (e.g. ## Header, **bold**, ![gambar](url))" />
            <div v-else class="markdown-preview" v-html="parsedContent"></div>
            <span class="step-hint">Bisa menyematkan gambar external contoh: ![evidence](https://url-gambar.com/img.png)</span>
          </div>

          <div class="form-group">
            <label>Icon</label>
            <div class="icon-picker">
              <span
                v-for="ic in iconOptions"
                :key="ic.value"
                class="icon-option"
                :class="{ selected: form.icon === ic.value }"
                @click="form.icon = ic.value"
              >
                {{ ic.emoji }} <span class="icon-label">{{ ic.label }}</span>
              </span>
            </div>
          </div>
        </div>

        <!-- Section 2: Triggers -->
        <div class="editor-section">
          <h4 class="section-label">
            Trigger Conditions
            <span class="section-hint">(cocok jika ANY satu trigger terpenuhi)</span>
          </h4>

          <div v-for="(trigger, idx) in form.triggers" :key="idx" class="trigger-row">
            <select v-model="trigger.type" class="trigger-type">
              <option value="rule_group">Rule Group</option>
              <option value="severity">Severity</option>
            </select>

            <input
              v-if="trigger.type === 'rule_group'"
              v-model="trigger.value"
              placeholder="e.g. malware, syscheck, authentication_failed..."
              class="trigger-value"
            />
            <select v-else v-model="trigger.value" class="trigger-value">
              <option value="Critical">Critical</option>
              <option value="High">High</option>
              <option value="Medium">Medium</option>
            </select>

            <button class="btn-icon danger" @click="removeTrigger(idx)" title="Hapus trigger">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
            </button>
          </div>

          <button class="btn btn-ghost btn-sm" @click="addTrigger">+ Add Trigger</button>
        </div>

        <!-- Section 3: Steps -->
        <div class="editor-section">
          <h4 class="section-label">Checklist Steps</h4>

          <div v-for="(step, idx) in form.steps" :key="step.id || idx" class="step-row">
            <span class="step-num">{{ idx + 1 }}</span>

            <div class="step-fields">
              <input v-model="step.title" placeholder="Judul step..." class="step-title-input" />
              <textarea v-model="step.description" rows="2" placeholder="Deskripsi detail langkah ini..." class="step-desc-input" />
              <div class="step-meta">
                <select v-model="step.category" class="step-cat">
                  <option value="identification">Identification</option>
                  <option value="containment">Containment</option>
                  <option value="eradication">Eradication</option>
                  <option value="recovery">Recovery</option>
                  <option value="lessons">Lessons Learned</option>
                </select>
                <label class="step-ev-check">
                  <input type="checkbox" v-model="step.requiresEvidence" />
                  <span>Evidence</span>
                </label>
                <div class="step-time">
                  <input type="number" v-model.number="step.estimatedMinutes" min="1" class="time-input" />
                  <span class="time-label">menit</span>
                </div>
              </div>
            </div>

            <div class="step-actions">
              <button class="btn-icon" @click="moveStep(idx, -1)" :disabled="idx === 0" title="Move up">↑</button>
              <button class="btn-icon" @click="moveStep(idx, 1)" :disabled="idx === form.steps.length - 1" title="Move down">↓</button>
              <button class="btn-icon danger" @click="removeStep(idx)" title="Hapus step">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
              </button>
            </div>
          </div>

          <button class="btn btn-ghost btn-sm" @click="addStep">+ Add Step</button>
        </div>
      </div>

      <!-- Footer -->
      <div class="editor-footer">
        <button class="btn btn-ghost" @click="$emit('close')">Batal</button>
        <button class="btn btn-primary" @click="save" :disabled="!form.name?.trim()">
          {{ isEdit ? 'Update Playbook' : 'Create Playbook' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, computed, ref } from 'vue'
import { parseMarkdown } from '../utils/markdown'

const props = defineProps({
  playbook: { type: Object, default: null }, // null = create mode
})

const emit = defineEmits(['save', 'close'])

const isEdit = computed(() => !!props.playbook?.id)

const iconOptions = [
  { value: 'malware', emoji: '🦠', label: 'Malware' },
  { value: 'auth', emoji: '🔐', label: 'Auth' },
  { value: 'vuln', emoji: '🛡', label: 'Vuln' },
  { value: 'fim', emoji: '📁', label: 'FIM' },
  { value: 'rootkit', emoji: '🕵️', label: 'Rootkit' },
  { value: 'network', emoji: '🌐', label: 'Network' },
  { value: 'dos', emoji: '🌊', label: 'DoS' },
  { value: 'generic', emoji: '⚡', label: 'Generic' },
]

const contentTab = ref('edit')
const selectedTemplate = ref('')

const parsedContent = computed(() => parseMarkdown(form.description))

const form = reactive({
  name: props.playbook?.name || '',
  description: props.playbook?.description || '',
  createdBy: props.playbook?.createdBy || 'admin',
  icon: props.playbook?.icon || 'generic',
  triggers: props.playbook?.triggers?.map(t => ({ ...t })) || [],
  steps: props.playbook?.steps?.map(s => ({ ...s })) || [],
})

function importTemplate() {
  if (!selectedTemplate.value) return
  
  if (selectedTemplate.value === 'owasp-injection') {
    form.name = 'OWASP Injection Mitigation'
    form.createdBy = 'OWASP Community API'
    form.icon = 'vuln'
    form.description = `## Injection Overview\nInjection flaws, such as SQL, NoSQL, OS, and LDAP injection, occur when untrusted data is sent to an interpreter as part of a command or query.\n\n### Evidence Examples\n![SQLi example](https://owasp.org/www-project-top-ten/assets/images/header-logo.png)\n\n### Recommendations\n- Use safe APIs\n- Escape special characters\n- Implement positive server-side input validation`
    form.triggers = [{ type: 'rule_group', value: 'sqli' }]
    form.steps = [
      { id: 't1', order: 1, title: 'Identify Affected Parameter', description: 'Review logs to find vulnerable parameter', category: 'identification', requiresEvidence: true, estimatedMinutes: 15 },
      { id: 't2', order: 2, title: 'Contain Incident', description: 'Block source IP temporarily', category: 'containment', requiresEvidence: false, estimatedMinutes: 10 }
    ]
  } else if (selectedTemplate.value === 'owasp-xss') {
    form.name = 'OWASP XSS Mitigation'
    form.createdBy = 'OWASP Community API'
    form.icon = 'network'
    form.description = `## Cross-Site Scripting (XSS)\nXSS flaws occur whenever an application includes untrusted data in a webpage without proper validation or escaping.\n\n### Types of XSS\n- **Reflected XSS**\n- **Stored XSS**\n- **DOM XSS**`
    form.triggers = [{ type: 'rule_group', value: 'xss' }]
    form.steps = [
      { id: 'x1', order: 1, title: 'Sanitize Input', description: 'Implement context-aware HTML encoding', category: 'eradication', requiresEvidence: false, estimatedMinutes: 30 }
    ]
  } else if (selectedTemplate.value === 'generic-malware') {
    form.name = 'Generic Malware Response'
    form.createdBy = 'Internal Security Dept'
    form.icon = 'malware'
    form.description = `## Malware Response Protocol\nStandard operating procedure for containing malicious applications found on host endpoints.\n\n> "Speed is critical. Isolate first, analyze second."`
    form.triggers = [{ type: 'rule_group', value: 'malware' }]
    form.steps = [
      { id: 'm1', order: 1, title: 'Isolate Host', description: 'Disconnect host from network immediately.', category: 'containment', requiresEvidence: false, estimatedMinutes: 5 },
      { id: 'm2', order: 2, title: 'Acquire Memory Dump', description: 'Dump memory for forensics.', category: 'identification', requiresEvidence: true, estimatedMinutes: 20 }
    ]
  }
}

function addTrigger() {
  form.triggers.push({ type: 'rule_group', value: '' })
}

function removeTrigger(idx) {
  form.triggers.splice(idx, 1)
}

function addStep() {
  form.steps.push({
    id: `s${Date.now()}-${form.steps.length}`,
    order: form.steps.length + 1,
    title: '',
    description: '',
    category: 'identification',
    requiresEvidence: false,
    estimatedMinutes: 10,
  })
}

function removeStep(idx) {
  form.steps.splice(idx, 1)
  // Re-order
  form.steps.forEach((s, i) => { s.order = i + 1 })
}

function moveStep(idx, direction) {
  const newIdx = idx + direction
  if (newIdx < 0 || newIdx >= form.steps.length) return
  const temp = form.steps[idx]
  form.steps[idx] = form.steps[newIdx]
  form.steps[newIdx] = temp
  // Re-order
  form.steps.forEach((s, i) => { s.order = i + 1 })
}

function save() {
  if (!form.name?.trim()) return
  emit('save', {
    name: form.name.trim(),
    description: form.description.trim(),
    createdBy: form.createdBy.trim() || 'admin',
    icon: form.icon,
    triggers: form.triggers.filter(t => t.value?.trim()),
    steps: form.steps.filter(s => s.title?.trim()).map((s, i) => ({
      ...s,
      order: i + 1,
    })),
  })
}
</script>

<style scoped>
.editor-overlay {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1100;
  padding: 20px;
}

.editor-container {
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  width: 100%;
  max-width: 700px;
  max-height: 85vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
}

.editor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border);
}
.editor-header h3 {
  font-family: var(--font-display);
  font-size: 16px;
  font-weight: 700;
}
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

.editor-body {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.editor-section {
  margin-bottom: 24px;
}
.section-label {
  font-size: 11px;
  font-weight: 600;
  color: var(--text3);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 12px;
  font-family: var(--font-mono);
  display: flex;
  align-items: center;
  gap: 8px;
}
.section-hint {
  font-weight: 400;
  font-size: 10px;
  color: var(--text3);
  text-transform: none;
  letter-spacing: normal;
}

.form-group {
  margin-bottom: 14px;
}
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
.form-group input,
.form-group textarea,
.form-group select {
  width: 100%;
  background: var(--bg3);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  color: var(--text);
  padding: 9px 12px;
  font-size: 13px;
  font-family: var(--font-body);
  resize: vertical;
}
.form-group input:focus,
.form-group textarea:focus,
.form-group select:focus {
  outline: none;
  border-color: var(--accent);
}

.row-group { display: flex; gap: 12px; }
.row-group .col { flex: 1; }

.label-row {
  display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;
}
.view-tabs {
  display: flex; gap: 8px; font-size: 11px; font-family: var(--font-mono);
}
.view-tabs span {
  cursor: pointer; padding: 2px 8px; border-radius: 4px; color: var(--text3); border: 1px solid transparent; transition: all 0.15s;
}
.view-tabs span:hover { color: var(--text); }
.view-tabs span.active { background: rgba(59,130,246,0.12); color: #60a5fa; border-color: rgba(59,130,246,0.3); }

.markdown-preview {
  background: var(--bg3);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 12px;
  color: var(--text);
  font-size: 13px;
  font-family: var(--font-body);
  min-height: 100px;
  max-height: 300px;
  overflow-y: auto;
}
.markdown-preview :deep(h1), .markdown-preview :deep(h2), .markdown-preview :deep(h3) { margin-top: 0; margin-bottom: 10px; color: var(--text); }
.markdown-preview :deep(img) { max-width: 100%; border-radius: 8px; }

.step-hint { font-size: 10px; color: var(--text3); margin-top: 4px; display: block; }
.import-hint { font-size: 11px; color: #4ade80; margin-top: 6px; }
.template-import { padding-bottom: 12px; border-bottom: 1px dashed var(--border); margin-bottom: 16px; }

/* Icon picker */
.icon-picker {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.icon-option {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 10px;
  border-radius: 6px;
  border: 1px solid var(--border);
  background: var(--bg3);
  cursor: pointer;
  transition: all 0.15s;
  font-size: 12px;
}
.icon-option:hover {
  border-color: var(--accent);
}
.icon-option.selected {
  border-color: var(--accent);
  background: rgba(59, 130, 246, 0.12);
}
.icon-label {
  font-size: 11px;
  color: var(--text2);
}

/* Triggers */
.trigger-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}
.trigger-type {
  width: 130px;
  flex-shrink: 0;
}
.trigger-value {
  flex: 1;
}

/* Steps */
.step-row {
  display: flex;
  gap: 10px;
  padding: 12px;
  background: var(--bg2);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  margin-bottom: 8px;
  align-items: flex-start;
}
.step-num {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: var(--bg3);
  border: 1px solid var(--border2);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 700;
  color: var(--accent);
  font-family: var(--font-mono);
  flex-shrink: 0;
  margin-top: 4px;
}
.step-fields {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.step-title-input,
.step-desc-input {
  width: 100%;
  background: var(--bg3);
  border: 1px solid var(--border);
  border-radius: 6px;
  color: var(--text);
  padding: 7px 10px;
  font-size: 12px;
  font-family: var(--font-body);
}
.step-desc-input {
  resize: vertical;
}
.step-title-input:focus,
.step-desc-input:focus {
  outline: none;
  border-color: var(--accent);
}

.step-meta {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}
.step-cat {
  font-size: 11px;
  padding: 4px 8px;
}
.step-ev-check {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  color: var(--text2);
  cursor: pointer;
}
.step-ev-check input[type="checkbox"] {
  width: 14px;
  height: 14px;
  accent-color: var(--accent);
}
.step-time {
  display: flex;
  align-items: center;
  gap: 4px;
}
.time-input {
  width: 50px;
  padding: 4px 6px;
  font-size: 11px;
  text-align: center;
}
.time-label {
  font-size: 10px;
  color: var(--text3);
}

.step-actions {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex-shrink: 0;
}

.btn-icon {
  width: 26px;
  height: 26px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: var(--bg3);
  color: var(--text3);
  cursor: pointer;
  font-size: 13px;
  transition: all 0.15s;
}
.btn-icon:hover:not(:disabled) {
  color: var(--text);
  border-color: var(--accent);
}
.btn-icon:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}
.btn-icon.danger:hover:not(:disabled) {
  color: #f87171;
  border-color: rgba(239, 68, 68, 0.4);
  background: rgba(239, 68, 68, 0.08);
}

.btn-sm {
  padding: 5px 12px;
  font-size: 11px;
}

.editor-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 14px 20px;
  border-top: 1px solid var(--border);
}
</style>
