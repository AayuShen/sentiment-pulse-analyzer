<template>
  <div id="app" :class="{ dark: store.darkMode }">
    <!-- Sidebar -->
    <aside class="sidebar">
      <div class="sb-brand">
        <span class="sb-logo">◈</span>
        <div>
          <div class="sb-name">Sentiment</div>
          <div class="sb-sub">Pulse Analyzer</div>
        </div>
      </div>
      <nav class="sb-nav">
        <router-link to="/" class="sb-link" exact-active-class="active">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/></svg>
          <span>Dashboard</span>
        </router-link>
        <router-link to="/upload" class="sb-link" active-class="active">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
          <span>Upload</span>
        </router-link>
        <router-link to="/graphs" class="sb-link" active-class="active">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>
          <span>Graphs</span>
        </router-link>
        <router-link to="/critique" class="sb-link" active-class="active">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>
          <span>Critique</span>
        </router-link>
        <router-link to="/customers" class="sb-link" active-class="active">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 00-3-3.87"/><path d="M16 3.13a4 4 0 010 7.75"/></svg>
          <span>Intel</span>
        </router-link>
        <router-link to="/agents" class="sb-link" active-class="active">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M16 21v-2a4 4 0 00-4-4H6a4 4 0 00-4-4v-2"/><circle cx="9" cy="7" r="4"/><polyline points="17 11 20 14 23 11"/></svg>
          <span>Agents</span>
        </router-link>
      </nav>
      <div class="sb-footer">
        <select v-model="store.langFilter" class="sb-select">
          <option value="all">🌐 All Languages</option>
          <option value="en">English</option>
          <option value="hi">Hindi</option>
          <option value="te">Telugu</option>
          <option value="ta">Tamil</option>
        </select>
      </div>
    </aside>

    <!-- Main content -->
    <div class="main-wrap">
      <header class="topbar">
        <div class="topbar-right">
          <button class="tb-icon" @click="store.toggleDark" :title="store.darkMode ? 'Light mode' : 'Dark mode'">
            {{ store.darkMode ? '☀' : '☾' }}
          </button>
        </div>
      </header>
      <main>
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </main>
    </div>

    <!-- Toast container -->
    <div class="toast-container" v-if="toasts.length">
      <div v-for="t in toasts" :key="t.id" :class="['toast', t.type]">
        {{ t.msg }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAppStore } from './stores/app.js'

const store = useAppStore()
const route = useRoute()
const toasts = ref([])
let toastId = 0

const pageTitle = computed(() => {
  const map = { '/': 'Dashboard', '/upload': 'Upload Recordings', '/graphs': 'Graphs & Trends', '/critique': 'Critique & Improvements', '/customers': 'Customer Intel', '/agents': 'Agent Performance' }
  return map[route.path] || 'Sentiment Pulse Analyzer'
})

function showToast(type, msg) {
  const id = ++toastId
  toasts.value.push({ id, type, msg })
  setTimeout(() => {
    toasts.value = toasts.value.filter(t => t.id !== id)
  }, 3500)
}

onMounted(() => {
  window._toast = showToast
})
</script>

<style>
/* === Reset & Base === */
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: 'Inter', system-ui, -apple-system, sans-serif; background: #e8ecf1; color: #343a40; }
body.dark { background: #1a1a2e; color: #cbd5e1; }

#app { display: flex; min-height: 100vh; width: 100vw; max-width: 100%; }

/* === Sidebar (Stellar dark) === */
.sidebar {
  width: 240px; min-width: 240px; background: #1a1a2e;
  display: flex; flex-direction: column; position: sticky; top: 0; height: 100vh;
  z-index: 50;
}

.sb-brand {
  display: flex; align-items: center; gap: 0.7rem; padding: 1.5rem 1.3rem;
  border-bottom: 1px solid rgba(255,255,255,0.08);
}
.sb-logo { font-size: 1.7rem; color: #27ae60; }
.sb-name { font-size: 0.95rem; font-weight: 700; color: #fff; line-height: 1.2; }
.sb-sub { font-size: 0.7rem; color: rgba(255,255,255,0.45); line-height: 1.2; }

.sb-nav { flex: 1; padding: 1rem 0.8rem; display: flex; flex-direction: column; gap: 0.15rem; }
.sb-link {
  display: flex; align-items: center; gap: 0.65rem; padding: 0.6rem 0.9rem;
  text-decoration: none; color: rgba(255,255,255,0.55); font-size: 0.84rem; font-weight: 500;
  border-radius: 6px; transition: all 0.2s;
  border-left: 3px solid transparent;
}
.sb-link:hover { background: rgba(255,255,255,0.05); color: rgba(255,255,255,0.85); }
.sb-link.active {
  background: rgba(39,174,96,0.12); color: #27ae60;
  border-left-color: #27ae60;
}

.sb-footer { padding: 1rem 1.2rem; border-top: 1px solid rgba(255,255,255,0.08); }
.sb-select {
  width: 100%; padding: 0.5rem 0.7rem; border: 1px solid rgba(255,255,255,0.12);
  border-radius: 6px; font-size: 0.8rem; background: rgba(255,255,255,0.05);
  color: rgba(255,255,255,0.7); cursor: pointer;
}
.sb-select:focus { outline: none; border-color: #27ae60; }

/* === Top Bar === */
.main-wrap { flex: 1; display: flex; flex-direction: column; min-width: 0; }
.topbar {
  padding: 0.45rem 1.5rem; background: #fff;
  border-bottom: 1px solid #e9ecef; box-shadow: 0 1px 3px rgba(0,0,0,0.04);
  display: flex; justify-content: flex-end; align-items: center;
  position: sticky; top: 0; z-index: 40;
}
.dark .topbar { background: #16213e; border-color: #0f3460; }
.topbar-title { font-size: 1.2rem; font-weight: 600; color: #2c3e50; }
.dark .topbar-title { color: #e2e8f0; }
.topbar-right { display: flex; align-items: center; gap: 0.8rem; }
.tb-icon {
  width: 36px; height: 36px; border: 1px solid #e9ecef; border-radius: 8px;
  background: #f8f9fa; cursor: pointer; font-size: 1rem; color: #6c757d;
  display: flex; align-items: center; justify-content: center; transition: all 0.15s;
}
.tb-icon:hover { background: #e9ecef; color: #2c3e50; }
.dark .tb-icon { background: rgba(255,255,255,0.06); border-color: rgba(255,255,255,0.1); color: #94a3b8; }
.dark .tb-icon:hover { background: rgba(255,255,255,0.12); color: #e2e8f0; }

/* === Main Content === */
main { flex: 1; padding: 0; width: 100%; max-width: 100%; }
main > * { min-height: 100%; width: 100%; }

/* === Page Transitions === */
.fade-enter-active, .fade-leave-active { transition: opacity 0.15s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }

/* === Toast Notifications === */
.toast-container { position: fixed; top: 20px; right: 20px; z-index: 1000; display: flex; flex-direction: column; gap: 0.5rem; }
.toast {
  padding: 0.8rem 1.2rem; border-radius: 8px; font-size: 0.84rem; font-weight: 500;
  animation: slideIn 0.3s ease; min-width: 280px;
  box-shadow: 0 4px 16px rgba(0,0,0,0.12);
}
.toast.warning { background: #fff3cd; color: #856404; border-left: 4px solid #f39c12; }
.toast.error { background: #f8d7da; color: #721c24; border-left: 4px solid #e74c3c; }
.toast.success { background: #d4edda; color: #155724; border-left: 4px solid #27ae60; }
.toast.info { background: #d1ecf1; color: #0c5460; border-left: 4px solid #3498db; }
.dark .toast.warning { background: #3e2f00; color: #fde68a; }
.dark .toast.error { background: #4a1515; color: #fca5a5; }
.dark .toast.success { background: #0a2e1a; color: #86efac; }
.dark .toast.info { background: #0a2140; color: #93c5fd; }
@keyframes slideIn { from { transform: translateX(100%); opacity: 0; } to { transform: translateX(0); opacity: 1; } }
</style>
