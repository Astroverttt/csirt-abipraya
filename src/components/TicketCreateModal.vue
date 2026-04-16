<template>
  <div class="modal-overlay" @click.self="$emit('close')" @keydown.esc="$emit('close')">
    <div class="modal-container" style="max-width: 560px;">
      <div class="modal-header">
        <h3 style="font-family: var(--font-display); font-size: 16px; font-weight: 700;">Create New Ticket</h3>
        <button class="btn-close" @click="$emit('close')">✕</button>
      </div>

      <div class="modal-body">
        <div class="form-group">
          <label>Severity</label>
          <select v-model="form.severity">
            <option value="Critical">Critical</option>
            <option value="High">High</option>
            <option value="Medium">Medium</option>
            <option value="Low">Low</option>
          </select>
        </div>

        <div class="form-group">
          <label>Agent</label>
          <select v-model="form.agentId" @change="onAgentChange">
            <option value="">— Pilih Agent —</option>
            <option v-for="a in agents" :key="a.id" :value="a.id">{{ a.name }} ({{ a.ip }})</option>
          </select>
        </div>

        <div class="form-row">
          <div class="form-group" style="flex: 1;">
            <label>CVE ID (opsional)</label>
            <input v-model="form.cveId" placeholder="CVE-2024-XXXXX" />
          </div>
          <div class="form-group" style="flex: 1;">
            <label>Rule Level</label>
            <input v-model.number="form.ruleLevel" type="number" min="0" max="15" placeholder="12" />
          </div>
        </div>

        <div class="form-row">
          <div class="form-group" style="flex: 1;">
            <label>Package Name</label>
            <input v-model="form.packageName" placeholder="openssl" />
          </div>
          <div class="form-group" style="flex: 1;">
            <label>Package Version</label>
            <input v-model="form.packageVersion" placeholder="3.0.2" />
          </div>
        </div>

        <div class="form-group">
          <label>Rule / Alert Description</label>
          <textarea v-model="form.ruleDescription" rows="2" placeholder="Deskripsi singkat alert..."></textarea>
        </div>

        <div class="form-group">
          <label>Assignee (opsional)</label>
          <input v-model="form.assignee" placeholder="Nama analyst" />
        </div>

        <div class="form-group">
          <label>Catatan Awal</label>
          <textarea v-model="form.description" rows="2" placeholder="Penjelasan awal tentang insiden ini..."></textarea>
        </div>
      </div>

      <div class="modal-footer">
        <div style="flex: 1"></div>
        <button class="btn btn-ghost" @click="$emit('close')">Batal</button>
        <button class="btn btn-primary" @click="submit" :disabled="!form.ruleDescription">Buat Tiket</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  agents: { type: Array, default: () => [] }
})

const emit = defineEmits(['close', 'create'])

const form = reactive({
  severity: 'High',
  agentId: '',
  agentName: '',
  agentIp: '',
  cveId: '',
  ruleLevel: 12,
  packageName: '',
  packageVersion: '',
  ruleDescription: '',
  assignee: '',
  description: '',
  isAutoCreated: false
})

function onAgentChange() {
  const agent = props.agents.find(a => a.id === form.agentId)
  if (agent) {
    form.agentName = agent.name
    form.agentIp = agent.ip
  }
}

function submit() {
  emit('create', { ...form })
}

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
  max-height: 85vh;
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
.btn-close:hover { background: rgba(239,68,68,0.15); color: #f87171; }
.modal-body { padding: 20px; overflow-y: auto; flex: 1; }
.modal-footer {
  display: flex;
  gap: 8px;
  padding: 14px 20px;
  border-top: 1px solid var(--border);
  align-items: center;
}

.form-group { margin-bottom: 14px; }
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
  transition: border-color 0.15s;
}
.form-group input:focus,
.form-group textarea:focus,
.form-group select:focus {
  outline: none;
  border-color: var(--accent);
}

.form-row { display: flex; gap: 12px; }
</style>
