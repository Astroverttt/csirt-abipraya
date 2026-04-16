import { createRouter, createWebHistory } from 'vue-router'
import { isAuthenticated } from '../utils/api'

const routes = [
  { path: '/login', name: 'Login', component: () => import('../views/LoginView.vue'), meta: { public: true } },
  { path: '/', name: 'Dashboard', component: () => import('../views/DashboardView.vue') },
  { path: '/agents', name: 'Agents', component: () => import('../views/AgentsView.vue') },
  { path: '/agents/:id', name: 'AgentDetail', component: () => import('../views/AgentDetailView.vue') },
  { path: '/vulnerabilities', name: 'Vulnerabilities', component: () => import('../views/VulnerabilitiesView.vue') },
  { path: '/packages', name: 'Packages', component: () => import('../views/PackagesView.vue') },
  { path: '/insights', name: 'Insights', component: () => import('../views/InsightsView.vue') },
  { path: '/reports', name: 'Reports', component: () => import('../views/ReportsView.vue') },
  { path: '/tickets', name: 'Tickets', component: () => import('../views/TicketsView.vue') },
  { path: '/playbooks', name: 'Playbooks', component: () => import('../views/PlaybookView.vue') },
  { path: '/:pathMatch(.*)*', redirect: '/' }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to) => {
  if (!to.meta.public && !isAuthenticated()) {
    return { name: 'Login' }
  }
})

export default router
