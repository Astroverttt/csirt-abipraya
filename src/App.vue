<template>
  <div v-if="route.meta.public">
    <router-view />
  </div>
  <div v-else class="layout">
    <aside class="sidebar">
      <div class="sidebar-logo">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none"><path d="M12 2L3 7v5c0 5.25 3.75 10.15 9 11.35C17.25 22.15 21 17.25 21 12V7L12 2z" fill="#3b82f6" opacity="0.9"/><path d="M9 12l2 2 4-4" stroke="#fff" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
        <span class="logo-text">PatchOps</span>
      </div>

      <nav class="sidebar-nav">
        <template v-for="item in navItems" :key="item.label || item.to">
          <!-- Top-level item -->
          <router-link v-if="!item.children" :to="item.to" class="nav-item" :class="{ active: isActive(item) }">
            <span class="nav-icon" v-html="item.icon"></span>
            <span class="nav-label">{{ item.label }}</span>
            <span v-if="item.badge" class="nav-badge">{{ item.badge }}</span>
          </router-link>

          <!-- Group -->
          <div v-else class="nav-group">
            <div class="nav-item group-header" @click="toggleGroup(item.label)" :class="{ 'group-active': isGroupActive(item) }">
              <span class="nav-icon" v-html="item.icon"></span>
              <span class="nav-label">{{ item.label }}</span>
              <svg class="chevron" :class="{ expanded: expandedGroups.includes(item.label) }" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"/></svg>
            </div>
            
            <div v-show="expandedGroups.includes(item.label)" class="nav-subitems">
              <router-link v-for="sub in item.children" :key="sub.to" :to="sub.to" class="nav-subitem" :class="{ active: isActive(sub) }">
                <span class="nav-label">{{ sub.label }}</span>
                <span v-if="sub.badge" class="nav-badge">{{ sub.badge }}</span>
              </router-link>
            </div>
          </div>
        </template>
      </nav>

      <div class="sidebar-footer">
        <div class="conn-status" :class="store.authenticated ? 'ok' : 'err'">
          <span class="dot"></span>
          <span>{{ store.authenticated ? 'Connected' : 'Disconnected' }}</span>
        </div>
        <button class="btn btn-ghost" style="width:100%; justify-content: center; margin-top: 8px;" @click="handleLogout">
          Logout
        </button>
      </div>
    </aside>

    <main class="main-content">
      <transition name="fade" mode="out-in">
        <router-view />
      </transition>
    </main>
  </div>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAppStore } from './stores/app'
import { logout } from './utils/wazuhApi'
import { clearToken } from './utils/api'

const route = useRoute()
const router = useRouter()
const store = useAppStore()

const navItems = computed(() => [
  { to: '/', label: 'Dashboard', icon: iconDash, exact: true },
  {
    label: 'Endpoints',
    icon: iconAgent,
    children: [
      { to: '/agents', label: 'Agents', badge: store.totalAgents || null },
      { to: '/packages', label: 'Packages' },
    ]
  },
  {
    label: 'Security',
    icon: iconVuln,
    children: [
      { to: '/vulnerabilities', label: 'Vulnerabilities', badge: store.criticalCount > 0 ? store.criticalCount : null },
      { to: '/insights', label: 'Insights' },
    ]
  },
  {
    label: 'Response (DFIR)',
    icon: iconTicket,
    children: [
      { to: '/tickets', label: 'Tickets', badge: store.openTicketsCount || null },
      { to: '/playbooks', label: 'Playbooks' },
    ]
  },
  { to: '/reports', label: 'Reports', icon: iconReport },
])

const expandedGroups = ref(['Endpoints', 'Security', 'Response (DFIR)']) // Default open

function toggleGroup(label) {
  const index = expandedGroups.value.indexOf(label)
  if (index > -1) {
    expandedGroups.value.splice(index, 1)
  } else {
    expandedGroups.value.push(label)
  }
}

function isGroupActive(item) {
  if (item.children) {
    return item.children.some(child => isActive(child))
  }
  return isActive(item)
}

function isActive(item) {
  if (item.exact) return route.path === item.to
  return route.path.startsWith(item.to)
}

function handleLogout() {
  logout()
  clearToken()
  store.setAuthenticated(false)
  router.push('/login')
}

const iconDash = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/></svg>`
const iconAgent = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="3" width="20" height="14" rx="2"/><path d="M8 21h8M12 17v4"/></svg>`
const iconVuln = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2L3 7v5c0 5.25 3.75 10.15 9 11.35C17.25 22.15 21 17.25 21 12V7L12 2z"/><path d="M12 8v4M12 16h.01"/></svg>`
const iconPkg = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 16V8a2 2 0 00-1-1.73l-7-4a2 2 0 00-2 0l-7 4A2 2 0 003 8v8a2 2 0 001 1.73l7 4a2 2 0 002 0l7-4A2 2 0 0021 16z"/><polyline points="3.27 6.96 12 12.01 20.73 6.96"/><line x1="12" y1="22.08" x2="12" y2="12"/></svg>`
const iconReport = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>`
const iconInsight = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 11.5a8.38 8.38 0 01-.9 3.8 8.5 8.5 0 01-7.6 4.7 8.38 8.38 0 01-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 01-.9-3.8 8.5 8.5 0 014.7-7.6 8.38 8.38 0 013.8-.9h.5a8.48 8.48 0 018 8v.5z"/></svg>`
const iconTicket = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M15 5v2M15 11v2M15 17v2M5 5h14a2 2 0 012 2v3a2 2 0 000 4v3a2 2 0 01-2 2H5a2 2 0 01-2-2v-3a2 2 0 000-4V7a2 2 0 012-2z"/></svg>`
const iconPlaybook = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11"/></svg>`
</script>

<style scoped>
.layout { display: flex; height: 100vh; overflow: hidden; }

.sidebar {
  width: 220px; flex-shrink: 0;
  background: var(--bg2); border-right: 1px solid var(--border);
  display: flex; flex-direction: column; padding: 0;
  overflow: hidden;
}

.sidebar-logo {
  display: flex; align-items: center; gap: 10px;
  padding: 20px 18px 18px; border-bottom: 1px solid var(--border);
}
.logo-text { font-family: var(--font-display); font-size: 16px; font-weight: 700; letter-spacing: -0.01em; color: var(--text); }

.sidebar-nav { flex: 1; padding: 12px 10px; overflow-y: auto; display: flex; flex-direction: column; gap: 2px; }

.nav-item {
  display: flex; align-items: center; gap: 10px;
  padding: 9px 10px; border-radius: var(--radius);
  color: var(--text2); font-size: 13px; font-weight: 400;
  transition: all 0.15s; cursor: pointer;
}
.nav-item:hover { background: var(--bg3); color: var(--text); }
.nav-item.active { background: rgba(59,130,246,0.12); color: #60a5fa; }
.nav-item.active .nav-icon { color: #60a5fa; }
.nav-icon { display: flex; opacity: 0.7; }
.nav-item.active .nav-icon { opacity: 1; }
.nav-label { flex: 1; }
.nav-badge {
  background: rgba(239,68,68,0.18); color: #f87171;
  font-size: 10px; font-weight: 600; padding: 2px 7px; border-radius: 10px;
  font-family: var(--font-mono);
}

.nav-group {
  display: flex;
  flex-direction: column;
}
.group-header {
  user-select: none;
}
.group-header.group-active {
  color: var(--text);
}
.group-active .nav-icon {
  color: #60a5fa;
  opacity: 1;
}
.chevron {
  opacity: 0.5;
  transition: transform 0.2s ease;
}
.chevron.expanded {
  transform: rotate(180deg);
}

.nav-subitems {
  display: flex;
  flex-direction: column;
  gap: 2px;
  margin-top: 2px;
  margin-bottom: 4px;
}
.nav-subitem {
  display: flex; align-items: center; justify-content: space-between;
  padding: 8px 10px 8px 38px;
  border-radius: var(--radius);
  color: var(--text3); font-size: 13px; font-weight: 400;
  transition: all 0.15s; cursor: pointer;
  text-decoration: none;
}
.nav-subitem:hover { color: var(--text); }
.nav-subitem.active {
  background: rgba(59,130,246,0.08);
  color: #60a5fa;
  font-weight: 500;
}

.sidebar-footer { padding: 14px 12px; border-top: 1px solid var(--border); }
.conn-status { display: flex; align-items: center; gap: 8px; font-size: 12px; color: var(--text3); }
.conn-status .dot { width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0; }
.conn-status.ok .dot { background: var(--low); box-shadow: 0 0 6px var(--low); }
.conn-status.err .dot { background: var(--critical); }
.conn-status.ok { color: var(--text2); }

.main-content { flex: 1; overflow-y: auto; background: var(--bg); }
</style>
