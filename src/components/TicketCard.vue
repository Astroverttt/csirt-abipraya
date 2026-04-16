<template>
  <div class="ticket-card" :class="[`sev-${ticket.severity?.toLowerCase()}`, `st-${ticket.status}`]" @click="$emit('click')">
    <div class="tc-header">
      <span class="mono tc-id">{{ ticket.id }}</span>
      <span class="badge" :class="`badge-${ticket.severity?.toLowerCase()}`">{{ ticket.severity || 'N/A' }}</span>
      <span class="badge status-badge" :class="`status-${ticket.status}`">{{ formatStatus(ticket.status) }}</span>
      <span class="tc-age">{{ timeAgo(ticket.createdAt) }}</span>
    </div>

    <div class="tc-body">
      <div class="tc-agent">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="2" y="3" width="20" height="14" rx="2"/><path d="M8 21h8M12 17v4"/></svg>
        <span>{{ ticket.agentName || '-' }}</span>
        <span class="mono tc-ip">{{ ticket.agentIp || '' }}</span>
      </div>
      <p class="tc-rule">{{ truncate(ticket.ruleDescription, 90) }}</p>
      <div class="tc-meta">
        <a v-if="ticket.cveId" :href="`https://nvd.nist.gov/vuln/detail/${ticket.cveId}`" target="_blank" class="cve-link" @click.stop>
          {{ ticket.cveId }}
        </a>
        <span v-if="ticket.packageName" class="pkg-chip">{{ ticket.packageName }} {{ ticket.packageVersion }}</span>
        <span v-if="ticket.assignee" class="assignee-chip">
          <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
          {{ ticket.assignee }}
        </span>
        <span v-if="ticket.tags?.length" class="tags-preview">
          <span v-for="tag in ticket.tags.slice(0, 3)" :key="tag" class="tag-mini">{{ tag }}</span>
        </span>
      </div>
    </div>

    <div class="tc-footer" @click.stop>
      <select 
        @change="$emit('status-change', { id: ticket.id, status: $event.target.value })"
        :value="ticket.status" 
        class="status-select"
      >
        <option value="open">Open</option>
        <option value="in_progress">In Progress</option>
        <option value="solved">Solved</option>
        <option value="closed">Closed</option>
        <option value="false_positive">False Positive</option>
      </select>
      <button class="btn btn-ghost btn-xs" @click="$emit('click')">Detail →</button>
      <button class="btn btn-ghost btn-xs" @click="$emit('export-pdf', ticket)">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>
        PDF
      </button>
    </div>
  </div>
</template>

<script setup>
defineProps({
  ticket: { type: Object, required: true }
})

defineEmits(['click', 'status-change', 'export-pdf'])

function formatStatus(s) {
  const map = {
    open: 'Open',
    in_progress: 'In Progress',
    solved: 'Solved',
    closed: 'Closed',
    false_positive: 'False Positive'
  }
  return map[s] || s
}

function truncate(str, len) {
  if (!str) return '-'
  return str.length > len ? str.slice(0, len) + '...' : str
}

function timeAgo(dateStr) {
  if (!dateStr) return ''
  const diff = Math.floor((Date.now() - new Date(dateStr).getTime()) / 1000)
  if (diff < 60) return `${diff}s ago`
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`
  return `${Math.floor(diff / 86400)}d ago`
}
</script>

<style scoped>
.ticket-card {
  background: var(--bg2);
  border: 1px solid var(--border);
  border-left: 3px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 14px 18px;
  cursor: pointer;
  transition: all 0.2s ease;
}
.ticket-card:hover {
  border-color: var(--accent);
  transform: translateY(-1px);
  box-shadow: 0 4px 20px rgba(0,0,0,0.15);
}
.ticket-card.sev-critical { border-left-color: var(--critical); }
.ticket-card.sev-high { border-left-color: var(--high); }
.ticket-card.sev-medium { border-left-color: var(--medium); }
.ticket-card.sev-low { border-left-color: var(--low); }

.tc-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}
.tc-id { font-size: 12px; color: var(--accent); font-weight: 600; }
.tc-age { margin-left: auto; font-size: 10px; color: var(--text3); font-family: var(--font-mono); }

.tc-body { margin-bottom: 12px; }
.tc-agent {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 500;
  color: var(--text);
  margin-bottom: 6px;
}
.tc-ip { font-size: 11px; color: var(--text3); }
.tc-rule {
  font-size: 12px;
  color: var(--text2);
  line-height: 1.5;
  margin: 0 0 8px 0;
}
.tc-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.cve-link {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--accent);
}
.cve-link:hover { text-decoration: underline; }
.pkg-chip {
  font-family: var(--font-mono);
  font-size: 10px;
  background: var(--bg3);
  padding: 2px 8px;
  border-radius: 4px;
  color: var(--info);
}
.assignee-chip {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 10px;
  color: var(--text3);
  background: var(--bg3);
  padding: 2px 8px;
  border-radius: 4px;
}
.tags-preview { display: flex; gap: 4px; }
.tag-mini {
  font-size: 9px;
  padding: 1px 6px;
  border-radius: 3px;
  background: rgba(59,130,246,0.1);
  color: #60a5fa;
  font-family: var(--font-mono);
}

.tc-footer {
  display: flex;
  align-items: center;
  gap: 8px;
  padding-top: 10px;
  border-top: 1px solid var(--border);
}
.status-select {
  font-size: 11px;
  padding: 4px 8px;
  background: var(--bg3);
  border: 1px solid var(--border);
  border-radius: 4px;
  color: var(--text);
  cursor: pointer;
}
.btn-xs { padding: 4px 10px !important; font-size: 11px !important; }

/* Status badges */
.status-badge {
  font-size: 10px;
  padding: 2px 8px;
  border-radius: 4px;
  font-weight: 500;
}
.status-open { background: rgba(234,179,8,0.15); color: #fbbf24; border: 1px solid rgba(234,179,8,0.3); }
.status-in_progress { background: rgba(59,130,246,0.15); color: #60a5fa; border: 1px solid rgba(59,130,246,0.3); }
.status-solved { background: rgba(34,197,94,0.15); color: #4ade80; border: 1px solid rgba(34,197,94,0.3); }
.status-closed { background: rgba(100,116,139,0.15); color: #94a3b8; border: 1px solid rgba(100,116,139,0.3); }
.status-false_positive { background: rgba(249,115,22,0.15); color: #fb923c; border: 1px solid rgba(249,115,22,0.3); }
</style>
