<template>
  <div class="agent-page">
    <!-- Gradient Banner -->
    <div class="agent-banner">
      <div class="ab-left">
        <div class="ab-icon">
          <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M16 21v-2a4 4 0 00-4-4H6a4 4 0 00-4-4v-2"/>
            <circle cx="9" cy="7" r="4"/>
            <polyline points="17 11 20 14 23 11"/>
          </svg>
        </div>
        <div>
          <h2>Agent Performance</h2>
          <p>Talk-time ratios, sentiment outcomes, and call-by-call breakdown</p>
        </div>
      </div>
      <div class="ab-right" v-if="!loading">
        <div class="ab-stat">
          <span class="ab-val">{{ summary.total }}</span>
          <span class="ab-lbl">Calls</span>
        </div>
        <div class="ab-stat ab-stat-talk">
          <span class="ab-val">{{ summary.avg_talk_ratio }}%</span>
          <span class="ab-lbl">Avg Talk Ratio</span>
        </div>
        <div class="ab-stat ab-stat-pos">
          <span class="ab-val">{{ summary.positive_calls }}</span>
          <span class="ab-lbl">Positive</span>
        </div>
        <div class="ab-stat ab-stat-neg">
          <span class="ab-val">{{ summary.negative_calls }}</span>
          <span class="ab-lbl">Negative</span>
        </div>
      </div>
    </div>

    <!-- Language Toggle -->
    <div class="lang-bar">
      <button
        v-for="opt in langs"
        :key="opt.value"
        class="lang-btn"
        :class="{ active: lang === opt.value }"
        @click="lang = opt.value; load()"
      >{{ opt.label }}</button>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="loading-row">
      <div class="skel-line" v-for="i in 5" :key="i" :style="{ width: (70 + Math.random() * 30) + '%' }"></div>
    </div>

    <!-- Empty -->
    <div v-else-if="!calls.length" class="card empty-note">
      No agent performance data yet. Process audio files to see talk-time metrics.
    </div>

    <!-- Calls Table -->
    <div v-else class="card">
      <div class="card-hd">
        <h3>📋 Call-by-Call Breakdown</h3>
        <span class="card-sub">Showing {{ calls.length }} calls</span>
      </div>
      <div class="perf-table">
        <div class="perf-row perf-head">
          <span class="perf-col perf-cust">Customer</span>
          <span class="perf-col perf-date">Date</span>
          <span class="perf-col perf-sent">Tag</span>
          <span class="perf-col perf-score">Score</span>
          <span class="perf-col perf-talk">Talk Ratio</span>
          <span class="perf-col perf-dur">Duration</span>
          <span class="perf-col perf-ab">A↔C</span>
        </div>
        <div v-for="c in calls" :key="c.call_id" class="perf-row">
          <span class="perf-col perf-cust">
            <span class="pcust-name">{{ c.customer_name || c.cid }}</span>
            <span class="pcust-cid">{{ c.cid }}</span>
          </span>
          <span class="perf-col perf-date">{{ fmtDate(c.processed_at) }}</span>
          <span class="perf-col perf-sent">
            <span class="psent-chip" :class="sentClass(c.tag)">{{ c.tag }}</span>
          </span>
          <span class="perf-col perf-score">
            <span class="pscore" :class="scoreClass(c.score)">{{ (c.score * 100).toFixed(0) }}%</span>
          </span>
          <span class="perf-col perf-talk">
            <div class="talk-bar-wrap">
              <div class="talk-bar">
                <div class="talk-fill-agent" :style="{ width: c.talk_ratio_pct + '%' }"></div>
              </div>
              <div class="talk-labels">
                <span>A·{{ c.talk_ratio_pct }}%</span>
                <span>C·{{ 100 - c.talk_ratio_pct }}%</span>
              </div>
            </div>
          </span>
          <span class="perf-col perf-dur">{{ fmtDuration(c.duration_secs) }}</span>
          <span class="perf-col perf-ab">
            <span class="ab-num">{{ c.agent_blocks }}</span> / <span class="ab-num">{{ c.customer_blocks }}</span>
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch } from 'vue'
import axios from 'axios'

const lang = ref('all')
const langs = [
  { label: 'All', value: 'all' },
  { label: 'Hindi', value: 'hi' },
  { label: 'Tamil', value: 'ta' },
  { label: 'Telugu', value: 'te' },
  { label: 'Kannada', value: 'kn' },
  { label: 'Malayalam', value: 'ml' },
  { label: 'Marathi', value: 'mr' },
]

const loading = ref(true)
const calls = ref([])
const summary = reactive({ total: 0, avg_talk_ratio: 0, positive_calls: 0, negative_calls: 0 })

function sentClass(tag) {
  if (tag === 'Positive' || tag === 'Satisfied') return 'sent-pos'
  if (tag === 'Negative' || tag === 'Frustrated') return 'sent-neg'
  return 'sent-neu'
}

function scoreClass(s) {
  if (s >= 0.7) return 'score-hi'
  if (s >= 0.4) return 'score-mid'
  return 'score-lo'
}

function fmtDate(d) {
  if (!d) return '—'
  return new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

function fmtDuration(secs) {
  if (!secs) return '0:00'
  const m = Math.floor(secs / 60)
  const s = Math.floor(secs % 60)
  return `${m}:${s.toString().padStart(2, '0')}`
}

async function load() {
  loading.value = true
  try {
    const { data } = await axios.get('/api/analytics/agent-performance', {
      params: { lang: lang.value, limit: 50 }
    })
    calls.value = data.calls || []
    Object.assign(summary, data.summary || { total: 0, avg_talk_ratio: 0, positive_calls: 0, negative_calls: 0 })
  } finally {
    loading.value = false
  }
}

onMounted(load)
watch(lang, load)
</script>

<style scoped>
/* === Banner === */
.agent-banner {
  display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap;
  gap: 1rem; padding: 1.5rem 1.8rem; border-radius: 16px;
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #7c3aed 100%);
  color: #fff; margin-bottom: 1.4rem; box-shadow: 0 4px 20px rgba(99,102,241,0.25);
}
.ab-left { display: flex; align-items: center; gap: 0.9rem; }
.ab-icon { opacity: 0.85; }
.ab-left h2 { font-size: 1.25rem; font-weight: 700; margin: 0; }
.ab-left p { font-size: 0.78rem; color: rgba(255,255,255,0.72); margin: 0.15rem 0 0; }
.ab-right { display: flex; gap: 1.6rem; }
.ab-stat { text-align: center; }
.ab-val { font-size: 1.35rem; font-weight: 800; display: block; line-height: 1.2; }
.ab-lbl { font-size: 0.68rem; color: rgba(255,255,255,0.62); text-transform: uppercase; letter-spacing: 0.04em; }
.ab-stat-talk .ab-val { color: #c7d2fe; }
.ab-stat-pos .ab-val { color: #a7f3d0; }
.ab-stat-neg .ab-val { color: #fecaca; }

/* === Lang bar === */
.lang-bar { display: flex; gap: 0.4rem; margin-bottom: 1rem; flex-wrap: wrap; }
.lang-btn {
  border: none; border-radius: 8px; padding: 0.3rem 0.8rem;
  font-size: 0.73rem; font-weight: 600; cursor: pointer;
  background: #f3f5f8; color: #6c757d; transition: all 0.15s;
}
.lang-btn.active { background: #6366f1; color: #fff; }
.lang-btn:hover:not(.active) { background: #e8eaef; }

/* === Loading === */
.loading-row { display: flex; flex-direction: column; gap: 0.7rem; }
.skel-line {
  height: 40px; border-radius: 10px;
  background: linear-gradient(90deg, #f3f5f8 25%, #e8eaef 50%, #f3f5f8 75%);
  background-size: 200% 100%; animation: shimmer 1.2s infinite;
}
@keyframes shimmer { 0% { background-position: 200% 0; } 100% { background-position: -200% 0; } }

/* === Card === */
.card { background: #fff; border-radius: 14px; border: 1px solid #eef0f2; padding: 1.4rem; margin-bottom: 1rem; }
.card-hd { display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.8rem; }
.card-hd h3 { font-size: 0.95rem; font-weight: 700; color: #2c3e50; margin: 0; }
.card-sub { font-size: 0.7rem; color: #adb5bd; }
.empty-note { color: #adb5bd; font-size: 0.84rem; text-align: center; padding: 1.5rem 0; }

/* === Table === */
.perf-table { width: 100%; }
.perf-row {
  display: grid;
  grid-template-columns: 1.4fr 0.7fr 0.6fr 0.4fr 1.2fr 0.5fr 0.4fr;
  align-items: center; padding: 0.55rem 0; border-bottom: 1px solid #f3f5f8;
  font-size: 0.78rem; color: #495057;
}
.perf-head { font-size: 0.7rem; color: #8d96a0; font-weight: 600; text-transform: uppercase; letter-spacing: 0.03em; padding-bottom: 0.5rem; }
.perf-col { padding: 0 0.3rem; }
.perf-cust { display: flex; flex-direction: column; gap: 1px; }
.pcust-name { font-weight: 600; color: #2c3e50; font-size: 0.8rem; }
.pcust-cid { font-size: 0.67rem; color: #adb5bd; }

/* Sentiment chip */
.psent-chip {
  display: inline-block; padding: 0.15rem 0.5rem; border-radius: 5px;
  font-size: 0.68rem; font-weight: 600;
}
.sent-pos { background: rgba(39,174,96,0.1); color: #27ae60; }
.sent-neg { background: rgba(231,76,60,0.1); color: #e74c3c; }
.sent-neu { background: rgba(149,165,166,0.1); color: #95a5a6; }

/* Score */
.pscore { font-weight: 700; font-size: 0.82rem; }
.score-hi { color: #27ae60; }
.score-mid { color: #f39c12; }
.score-lo { color: #e74c3c; }

/* Talk ratio bar */
.talk-bar-wrap { width: 100%; }
.talk-bar { height: 6px; border-radius: 3px; background: #eef0f2; overflow: hidden; margin-bottom: 2px; }
.talk-fill-agent { height: 100%; border-radius: 3px; background: linear-gradient(90deg, #6366f1, #8b5cf6); transition: width 0.3s; }
.talk-labels { display: flex; justify-content: space-between; font-size: 0.62rem; color: #adb5bd; }

/* AB numbers */
.ab-num { font-weight: 600; color: #6366f1; }

@media (max-width: 768px) {
  .perf-row { grid-template-columns: 1fr 1fr; gap: 0.3rem; }
  .perf-head { display: none; }
}
</style>
