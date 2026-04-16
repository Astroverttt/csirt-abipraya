<template>
  <div class="login-wrap">
    <div class="login-box">
      <div class="login-header">
        <svg width="36" height="36" viewBox="0 0 24 24" fill="none"><path d="M12 2L3 7v5c0 5.25 3.75 10.15 9 11.35C17.25 22.15 21 17.25 21 12V7L12 2z" fill="#3b82f6"/><path d="M9 12l2 2 4-4" stroke="#fff" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
        <h1>PatchOps</h1>
        <p>Wazuh Patch Management</p>
      </div>

      <form @submit.prevent="handleLogin">
        <div class="field">
          <label>Username</label>
          <input v-model="form.username" type="text" placeholder="wazuh" required />
        </div>
        <div class="field">
          <label>Password</label>
          <input v-model="form.password" type="password" placeholder="••••••••" required />
        </div>
        <div v-if="error" class="error-msg">{{ error }}</div>
        <button class="btn btn-primary" type="submit" :disabled="loading" style="width: 100%; justify-content: center; margin-top: 8px;">
          <span v-if="loading">Connecting...</span>
          <span v-else>Connect to Wazuh</span>
        </button>
      </form>

      <div class="login-note">
        <strong>Secure:</strong> Credentials are validated against Wazuh API and never stored in the browser.
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { login } from '../utils/wazuhApi'
import { useAppStore } from '../stores/app'

const router = useRouter()
const store = useAppStore()
const loading = ref(false)
const error = ref('')
const form = ref({ username: 'wazuh', password: '' })

async function handleLogin() {
  loading.value = true
  error.value = ''
  try {
    await login(form.value.username, form.value.password)
    store.setAuthenticated(true)
    await store.initialize()
    router.push('/')
  } catch (e) {
    error.value = e.response?.data?.detail || 'Koneksi gagal. Cek kredensial Anda.'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-wrap {
  min-height: 100vh; display: flex; align-items: center; justify-content: center;
  background: var(--bg);
  background-image: radial-gradient(ellipse 60% 50% at 50% -20%, rgba(59,130,246,0.08) 0%, transparent 70%);
}
.login-box { width: 100%; max-width: 400px; padding: 0 20px; }
.login-header { text-align: center; margin-bottom: 32px; display: flex; flex-direction: column; align-items: center; gap: 10px; }
.login-header h1 { font-family: var(--font-display); font-size: 26px; font-weight: 700; letter-spacing: -0.02em; }
.login-header p { color: var(--text3); font-size: 13px; }

form { background: var(--bg2); border: 1px solid var(--border); border-radius: var(--radius-lg); padding: 24px; display: flex; flex-direction: column; gap: 16px; }

.field { display: flex; flex-direction: column; gap: 6px; }
.field label { font-size: 12px; font-weight: 500; color: var(--text2); letter-spacing: 0.03em; }
.field input { width: 100%; }

.error-msg { background: rgba(239,68,68,0.1); border: 1px solid rgba(239,68,68,0.3); color: #f87171; padding: 10px 12px; border-radius: var(--radius); font-size: 13px; }

.login-note { margin-top: 16px; padding: 12px 14px; background: var(--bg3); border: 1px solid var(--border); border-radius: var(--radius); font-size: 12px; color: var(--text3); line-height: 1.7; }
</style>
