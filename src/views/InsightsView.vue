<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h2>Security Insights</h2>
        <p class="sub">Rekomendasi patch dan update CVE terbaru</p>
      </div>
      <button class="btn btn-primary" @click="refresh" :disabled="store.loading">
        {{ store.loading ? 'Syncing...' : 'Sync All Data' }}
      </button>
    </div>

    <!-- Tab switcher -->
    <div class="tabs" style="margin-bottom: 20px;">
      <button class="tab" :class="{ active: activeSection === 'recs' }" @click="activeSection = 'recs'">
        Patch Recommendations
        <span v-if="fixableVulns.length" class="tab-count">{{ fixableVulns.length }}</span>
      </button>
      <button class="tab" :class="{ active: activeSection === 'nvd' }" @click="activeSection = 'nvd'">
        CVE Updates (NVD)
        <span v-if="nvdCves.length" class="tab-count">{{ nvdCves.length }}</span>
      </button>
    </div>

    <!-- SECTION: Patch Recommendations -->
    <div v-if="activeSection === 'recs'">
      <div class="insights-grid">
        <!-- Recommendations Card -->
        <div class="card highlight-card">
          <div class="card-header">
            <div class="icon-wrap" style="background: rgba(34,197,94,0.1); color: #4ade80;">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/></svg>
            </div>
            <div>
              <h3 class="card-title">Patch Recommendations</h3>
              <p class="card-sub">{{ fixableVulns.length }} CVEs have available patches</p>
            </div>
          </div>
          
          <div class="recommendation-list">
            <div v-if="!topRecommendations.length" class="empty-state" style="padding: 20px;">
              Tidak ada CVE yang bisa dipatch saat ini. Sync data terlebih dahulu.
            </div>
            <div v-for="v in topRecommendations" :key="v.cve + v._agentId" class="rec-item">
              <div class="rec-main">
                <span class="badge" :class="`badge-${v.severity?.toLowerCase()}`">{{ v.severity }}</span>
                <span class="mono rec-cve">{{ v.cve }}</span>
                <span class="rec-pkg">{{ v.name }}</span>
              </div>
              <div class="rec-action">
                <span class="rec-fix">Fix: {{ v.condition }}</span>
                <span class="agent-link" @click="$router.push(`/agents/${v._agentId}`)">
                  {{ agentName(v._agentId) }}
                </span>
              </div>
            </div>
          </div>
        </div>

        <!-- Recent CVEs Card -->
        <div class="card">
          <h3 class="card-title" style="margin-bottom:16px;">New Vulnerabilities Found</h3>
          <div v-if="!recentVulns.length" class="empty-state">No recent vulnerabilities found.</div>
          <div v-else class="recent-list">
            <div v-for="v in recentVulns" :key="v.cve + v._agentId" class="recent-item">
              <div class="recent-meta">
                <span class="mono">{{ v.cve }}</span>
                <span class="dot"></span>
                <span class="agent-name">{{ agentName(v._agentId) }}</span>
              </div>
              <div class="recent-body">
                <span class="badge" :class="`badge-${v.severity?.toLowerCase()}`" style="font-size:10px;">{{ v.severity }}</span>
                <span class="recent-pkg">{{ v.name }} - {{ v.version }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Fixable Vulnerabilities Table -->
      <div class="card" style="margin-top: 24px; padding: 0; overflow: hidden;">
        <div style="padding: 16px 20px; border-bottom: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center;">
          <h3 class="card-title" style="margin:0;">All Fixable Vulnerabilities</h3>
          <div class="filters">
            <input v-model="search" placeholder="Cari CVE atau package..." class="small-input" />
          </div>
        </div>
        <table>
          <thead>
            <tr><th>CVE ID</th><th>Package</th><th>Severity</th><th>Condition / Fix</th><th>Agent</th></tr>
          </thead>
          <tbody>
            <tr v-if="!filteredFixable.length">
              <td colspan="5" style="text-align:center; padding: 40px; color: var(--text3);">Tidak ada rekomendasi patch ditemukan.</td>
            </tr>
            <tr v-for="v in filteredFixable" :key="v.cve + v._agentId">
              <td><a :href="`https://nvd.nist.gov/vuln/detail/${v.cve}`" target="_blank" class="cve-link">{{ v.cve }}</a></td>
              <td>{{ v.name }}</td>
              <td><span class="badge" :class="`badge-${v.severity?.toLowerCase()}`">{{ v.severity }}</span></td>
              <td><span class="mono fix-text">{{ v.condition }}</span></td>
              <td>
                <span class="agent-chip" @click="$router.push(`/agents/${v._agentId}`)">
                  {{ agentName(v._agentId) }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- SECTION: CVE Updates from NVD -->
    <div v-if="activeSection === 'nvd'">
      <div class="card" style="margin-bottom: 20px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
          <div>
            <h3 class="card-title" style="margin: 0;">CVE Feed from NVD</h3>
            <p class="card-sub" style="margin-top: 4px;">
              CVE terbaru dari National Vulnerability Database yang relevan dengan packages di environment Anda.
              <span v-if="nvdCacheInfo" class="cache-info">{{ nvdCacheInfo }}</span>
            </p>
          </div>
          <div style="display: flex; gap: 8px;">
            <button class="btn btn-ghost" @click="forceRefreshNVD" :disabled="nvdLoading">
              {{ nvdLoading ? `Loading (${nvdProgress})...` : 'Refresh CVE Feed' }}
            </button>
          </div>
        </div>

        <div v-if="nvdLoading" class="nvd-loading">
          <div class="loading-bar">
            <div class="loading-bar-fill" :style="{ width: nvdProgressPct + '%' }"></div>
          </div>
          <p class="mono" style="font-size: 11px; color: var(--text3); margin-top: 8px;">
            Querying NVD API... (rate limited: ~6s per keyword). Keyword: {{ nvdCurrentKeyword }}
          </p>
        </div>

        <div v-if="!nvdCves.length && !nvdLoading" class="empty-state" style="padding: 32px;">
          <p>Belum ada data CVE dari NVD.</p>
          <p style="font-size: 11px; margin-top: 4px;">Klik "Refresh CVE Feed" untuk mengambil CVE terbaru berdasarkan packages di agent Anda.</p>
        </div>
      </div>

      <div v-if="nvdCves.length" class="card" style="padding: 0; overflow: hidden;">
        <div style="padding: 14px 20px; border-bottom: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center;">
          <span class="count-text">{{ nvdCves.length }} CVEs found in the last 7 days</span>
          <input v-model="nvdSearch" placeholder="Search CVE..." class="small-input" />
        </div>
        <table>
          <thead>
            <tr><th>CVE ID</th><th>Score</th><th>Severity</th><th>Published</th><th>Matched Pkg</th><th>Description</th></tr>
          </thead>
          <tbody>
            <tr v-for="c in filteredNvdCves" :key="c.id">
              <td><a :href="`https://nvd.nist.gov/vuln/detail/${c.id}`" target="_blank" class="cve-link">{{ c.id }}</a></td>
              <td><span class="mono" :style="scoreColor(c.baseScore)">{{ c.baseScore ?? '-' }}</span></td>
              <td><span class="badge" :class="nvdSevClass(c.baseSeverity)">{{ c.baseSeverity || '-' }}</span></td>
              <td class="mono" style="font-size: 11px; white-space: nowrap;">{{ formatNvdDate(c.published) }}</td>
              <td><span class="agent-chip" style="cursor: default;">{{ c.matchedKeyword }}</span></td>
              <td style="max-width: 280px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: 11px; color: var(--text3);" :title="c.description">{{ truncate(c.description, 120) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAppStore } from '../stores/app'
import { fetchRecentCVEs, clearNVDCache } from '../utils/nvdApi'

const store = useAppStore()
const search = ref('')
const activeSection = ref('recs')
const nvdCves = ref([])
const nvdLoading = ref(false)
const nvdSearch = ref('')
const nvdProgress = ref('')
const nvdProgressPct = ref(0)
const nvdCurrentKeyword = ref('')
const nvdCacheInfo = ref('')

onMounted(async () => {
  if (!store.agents.length) await store.initialize()
  if (Object.keys(store.vulnsByAgent).length === 0) await store.fetchAllVulnerabilities()
  
  // Try loading cached NVD data
  try {
    const cached = await fetchRecentCVEs([], 7) // Will only return cache if exists
    if (cached && cached.length) {
      nvdCves.value = cached
      nvdCacheInfo.value = '(cached)'
    }
  } catch {}
})

const refresh = async () => {
  await store.fetchAllData()
}

// Get top package names from all agents for NVD queries
const topPackageKeywords = computed(() => {
  const pkgCount = {}
  Object.values(store.packagesByAgent).forEach(pkgs => {
    pkgs.forEach(p => {
      const name = p.name?.toLowerCase()
      if (name && name.length > 2 && !name.startsWith('lib')) {
        pkgCount[name] = (pkgCount[name] || 0) + 1
      }
    })
  })
  // Sort by frequency and pick top 10
  return Object.entries(pkgCount)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 10)
    .map(([name]) => name)
})

async function loadNVDFeed() {
  const keywords = topPackageKeywords.value
  if (!keywords.length) {
    // Fallback: use common keywords
    keywords.push('openssl', 'nginx', 'apache', 'linux kernel', 'curl')
  }
  
  nvdLoading.value = true
  nvdProgress.value = `0/${keywords.length}`
  nvdProgressPct.value = 0

  try {
    // We'll do manual fetching to show progress
    clearNVDCache()
    const allCves = []
    const seen = new Set()
    const now = new Date()
    const startDate = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000)
    const pubStartDate = startDate.toISOString().replace('Z', '')
    const pubEndDate = now.toISOString().replace('Z', '')

    for (let i = 0; i < keywords.length; i++) {
      nvdCurrentKeyword.value = keywords[i]
      nvdProgress.value = `${i + 1}/${keywords.length}`
      nvdProgressPct.value = Math.round(((i + 1) / keywords.length) * 100)

      try {
        const res = await fetch(
          `https://services.nvd.nist.gov/rest/json/cves/2.0?keywordSearch=${encodeURIComponent(keywords[i])}&pubStartDate=${pubStartDate}&pubEndDate=${pubEndDate}&noRejected&resultsPerPage=20`
        )
        if (res.ok) {
          const data = await res.json()
          for (const item of data.vulnerabilities || []) {
            const cve = item.cve
            if (seen.has(cve.id)) continue
            seen.add(cve.id)

            const cvssV31 = cve.metrics?.cvssMetricV31?.[0]?.cvssData
            const cvssV30 = cve.metrics?.cvssMetricV30?.[0]?.cvssData
            const cvssData = cvssV31 || cvssV30

            allCves.push({
              id: cve.id,
              published: cve.published,
              description: cve.descriptions?.find(d => d.lang === 'en')?.value || '',
              baseScore: cvssData?.baseScore || null,
              baseSeverity: cvssData?.baseSeverity || null,
              matchedKeyword: keywords[i]
            })
          }
        }
      } catch (err) {
        console.warn(`NVD query failed for "${keywords[i]}":`, err.message)
      }

      // Rate limiting
      if (i < keywords.length - 1) {
        await new Promise(r => setTimeout(r, 6500))
      }
    }

    allCves.sort((a, b) => (b.baseScore || 0) - (a.baseScore || 0))
    nvdCves.value = allCves
    nvdCacheInfo.value = `(updated ${new Date().toLocaleTimeString('id-ID')})`
    
    // Cache manually
    sessionStorage.setItem('nvd_cve_cache', JSON.stringify({
      timestamp: Date.now(),
      data: allCves
    }))
  } finally {
    nvdLoading.value = false
  }
}

function forceRefreshNVD() {
  clearNVDCache()
  loadNVDFeed()
}

const allVulns = computed(() => {
  return Object.entries(store.vulnsByAgent).flatMap(([agentId, vulns]) =>
    vulns.map(v => ({ ...v, _agentId: agentId }))
  )
})

const fixableVulns = computed(() => {
  return allVulns.value.filter(v => v.condition && v.condition !== '-')
})

const filteredFixable = computed(() => {
  let list = fixableVulns.value
  if (search.value) {
    const q = search.value.toLowerCase()
    list = list.filter(v => 
      v.cve?.toLowerCase().includes(q) || 
      v.name?.toLowerCase().includes(q)
    )
  }
  
  const severityOrder = { critical: 0, high: 1, medium: 2, low: 3 }
  return list.sort((a, b) => 
    (severityOrder[a.severity?.toLowerCase()] ?? 4) - (severityOrder[b.severity?.toLowerCase()] ?? 4)
  ).slice(0, 10)
})

const topRecommendations = computed(() => {
  return [...fixableVulns.value]
    .sort((a, b) => {
      const severityOrder = { critical: 0, high: 1, medium: 2, low: 3 }
      return (severityOrder[a.severity?.toLowerCase()] ?? 4) - (severityOrder[b.severity?.toLowerCase()] ?? 4)
    })
    .slice(0, 5)
})

const recentVulns = computed(() => {
  return [...allVulns.value]
    .sort((a, b) => (b.cve || '').localeCompare(a.cve || ''))
    .slice(0, 8)
})

const filteredNvdCves = computed(() => {
  if (!nvdSearch.value) return nvdCves.value
  const q = nvdSearch.value.toLowerCase()
  return nvdCves.value.filter(c =>
    c.id?.toLowerCase().includes(q) ||
    c.description?.toLowerCase().includes(q) ||
    c.matchedKeyword?.toLowerCase().includes(q)
  )
})

function agentName(id) {
  return store.agents.find(a => a.id === id)?.name || id
}

function truncate(str, len) {
  if (!str) return '-'
  return str.length > len ? str.slice(0, len) + '...' : str
}

function formatNvdDate(dateStr) {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString('id-ID', { day: '2-digit', month: 'short', year: 'numeric' })
}

function nvdSevClass(sev) {
  if (!sev) return ''
  const s = sev.toLowerCase()
  if (s === 'critical') return 'badge-critical'
  if (s === 'high') return 'badge-high'
  if (s === 'medium') return 'badge-medium'
  return 'badge-low'
}

function scoreColor(score) {
  if (!score) return ''
  if (score >= 9.0) return 'color: var(--critical); font-weight: 700;'
  if (score >= 7.0) return 'color: var(--high); font-weight: 600;'
  if (score >= 4.0) return 'color: var(--medium);'
  return 'color: var(--low);'
}
</script>

<style scoped>
.page { padding: 28px; max-width: 1200px; }
.page-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 24px; }
.page-header h2 { font-family: var(--font-display); font-size: 20px; font-weight: 700; }
.sub { color: var(--text3); font-size: 12px; margin-top: 2px; }

.tabs { display: flex; gap: 2px; border-bottom: 1px solid var(--border); }
.tab { padding: 9px 16px; font-size: 13px; color: var(--text3); cursor: pointer; background: none; border: none; border-bottom: 2px solid transparent; display: flex; align-items: center; gap: 7px; transition: all 0.15s; }
.tab:hover { color: var(--text); }
.tab.active { color: var(--accent); border-bottom-color: var(--accent); }
.tab-count { background: var(--bg3); color: var(--text3); font-family: var(--font-mono); font-size: 10px; padding: 1px 6px; border-radius: 10px; }
.tab.active .tab-count { background: rgba(59,130,246,0.15); color: #60a5fa; }

.insights-grid { display: grid; grid-template-columns: 1.5fr 1fr; gap: 20px; }

.card-header { display: flex; gap: 16px; align-items: center; margin-bottom: 20px; }
.icon-wrap { width: 42px; height: 42px; border-radius: 12px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.card-title { font-size: 13px; font-weight: 600; color: var(--text2); text-transform: uppercase; letter-spacing: 0.05em; font-family: var(--font-mono); }
.card-sub { font-size: 12px; color: var(--text3); margin-top: 2px; }

.recommendation-list { display: flex; flex-direction: column; gap: 12px; }
.rec-item { padding: 12px; background: var(--bg3); border-radius: var(--radius); border: 1px solid var(--border); transition: transform 0.2s; }
.rec-item:hover { transform: translateX(4px); border-color: var(--accent); }
.rec-main { display: flex; align-items: center; gap: 10px; margin-bottom: 6px; }
.rec-cve { font-size: 12px; color: var(--accent); }
.rec-pkg { font-size: 13px; font-weight: 500; }
.rec-action { display: flex; justify-content: space-between; align-items: center; font-size: 11px; }
.rec-fix { color: var(--low); font-family: var(--font-mono); }
.agent-link { color: var(--text3); cursor: pointer; text-decoration: underline; }
.agent-link:hover { color: var(--text); }

.recent-list { display: flex; flex-direction: column; gap: 14px; }
.recent-item { border-left: 2px solid var(--border); padding-left: 12px; }
.recent-meta { display: flex; align-items: center; gap: 8px; font-size: 11px; color: var(--text3); font-family: var(--font-mono); margin-bottom: 4px; }
.dot { width: 4px; height: 4px; border-radius: 50%; background: var(--border2); }
.recent-body { display: flex; align-items: center; gap: 8px; }
.recent-pkg { font-size: 12px; color: var(--text2); }

.fix-text { color: var(--low); font-size: 11px; }
.agent-chip { font-family: var(--font-mono); font-size: 11px; background: var(--bg3); padding: 2px 8px; border-radius: 4px; cursor: pointer; color: var(--info); }
.agent-chip:hover { background: rgba(6,182,212,0.1); }

.small-input { padding: 6px 12px; font-size: 12px; width: 200px; }
.cve-link { color: var(--accent); font-family: var(--font-mono); font-size: 12px; }
.cve-link:hover { text-decoration: underline; }
.count-text { font-size: 11px; color: var(--text3); font-family: var(--font-mono); }
.cache-info { font-family: var(--font-mono); font-size: 10px; color: var(--info); margin-left: 4px; }

.nvd-loading { padding: 8px 0; }
.loading-bar { height: 4px; background: var(--bg3); border-radius: 2px; overflow: hidden; }
.loading-bar-fill { height: 100%; background: linear-gradient(90deg, var(--accent), #818cf8); border-radius: 2px; transition: width 0.5s ease; }
</style>
