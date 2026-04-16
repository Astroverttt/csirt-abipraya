/**
 * Centralized API client for PatchOps Backend.
 *
 * All requests go through the FastAPI backend.
 * JWT token is stored in memory only (not localStorage) for XSS safety.
 */
import axios from 'axios'

const API_BASE = '/api'

let _token = null

const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
})

// ── Attach JWT to every request ──────────────────────────────────────────────
api.interceptors.request.use((config) => {
  if (_token) {
    config.headers.Authorization = `Bearer ${_token}`
  }
  return config
})

// ── Handle 401 globally ──────────────────────────────────────────────────────
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      _token = null
      // Redirect to login if not already there
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    }
    return Promise.reject(err)
  }
)

// ── Token management ─────────────────────────────────────────────────────────

export function setToken(token) {
  _token = token
}

export function getToken() {
  return _token
}

export function clearToken() {
  _token = null
}

export function isAuthenticated() {
  return !!_token
}

export default api
