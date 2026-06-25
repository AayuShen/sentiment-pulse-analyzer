<template>
  <div class="dash">
    <!-- Welcome Banner -->
    <div class="welcome-banner">
      <div class="wb-left">
        <div class="wb-icon">
          <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>
        </div>
        <div>
          <h2>Sentiment Pulse Dashboard</h2>
          <p>Real-time voice sentiment analysis across 6 Indian languages</p>
        </div>
      </div>
      <div class="wb-right">
        <div class="wb-stat">
          <span class="wb-val">{{ stats.total }}</span>
          <span class="wb-lbl">Calls Analyzed</span>
        </div>
        <div class="wb-stat">
          <span class="wb-val">{{ stats.unique_customers || '—' }}</span>
          <span class="wb-lbl">Customers</span>
        </div>
        <div class="wb-stat">
          <span class="wb-val">{{ stats.avg_score }}</span>
          <span class="wb-lbl">Confidence</span>
        </div>
      </div>
    </div>

    <!-- Controls -->
    <div class="dash-controls">
      <div class="filters">
        <select v-model="lang" @change="loadAll">
          <option value="all">All Languages</option>
          <option value="en">English</option>
          <option value="hi">Hindi</option>
          <option value="te">Telugu</option>
          <option value="ta">Tamil</option>
        </select>
        <input type="date" v-model="from" @change="loadAll" />
        <input type="date" v-model="to" @change="loadAll" />
      </div>
    </div>

    <!-- Skeleton -->
    <div v-if="loading" class="skel-row">
      <div class="skel-kpi" v-for="i in 5" :key="i"></div>
    </div>

    <!-- KPI Cards -->
    <div v-else class="kpi-row">
      <div class="kpi-card kpi-green">
        <div class="kpi-icon">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>
        </div>
        <div class="kpi-body">
          <span class="kpi-val">{{ stats.total }}</span>
          <span class="kpi-lbl">Total Calls</span>
        </div>
        <span v-if="stats.total > 0" class="kpi-trend up">+{{ stats.total }}</span>
      </div>

      <div class="kpi-card kpi-blue">
        <div class="kpi-icon">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 00-3-3.87"/><path d="M16 3.13a4 4 0 010 7.75"/></svg>
        </div>
        <div class="kpi-body">
          <span class="kpi-val">{{ stats.unique_customers || stats.total }}</span>
          <span class="kpi-lbl">Unique Customers</span>
        </div>
      </div>

      <div class="kpi-card kpi-orange">
        <div class="kpi-icon">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
        </div>
        <div class="kpi-body">
          <span class="kpi-val">{{ stats.avg_score }}</span>
          <span class="kpi-lbl">Avg Confidence</span>
        </div>
      </div>

      <div class="kpi-card kpi-red">
        <div class="kpi-icon">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="20" x2="12" y2="10"/><line x1="18" y1="20" x2="18" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>
        </div>
        <div class="kpi-body">
          <span class="kpi-val">{{ stats.negative_pct }}%</span>
          <span class="kpi-lbl">Negative This Week</span>
        </div>
        <span v-if="stats.negative_pct > 0" class="kpi-trend down">{{ stats.negative_pct }}%</span>
      </div>

      <div class="kpi-card kpi-teal">
        <div class="kpi-icon">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>
        </div>
        <div class="kpi-body">
          <span class="kpi-val">{{ stats.positive_pct || '—' }}%</span>
          <span class="kpi-lbl">Positive This Week</span>
        </div>
        <span v-if="stats.positive_pct" class="kpi-trend up">+{{ stats.positive_pct }}%</span>
      </div>
    </div>

    <!-- Sentiment Gauge -->
    <div v-if="!loading && stats.total > 0" class="sentiment-gauge">
      <div class="gauge-section">
        <h3>Sentiment Distribution</h3>
        <div class="gauge-bars">
          <div class="gauge-item" v-for="tag in tags" :key="tag">
            <div class="gauge-label"><span class="gauge-tag">{{ tag }}</span><span class="gauge-count">{{ stats.tag_counts?.[tag] || 0 }}</span></div>
            <div class="gauge-track">
              <div class="gauge-fill" :style="{ width: stats.total ? ((stats.tag_counts?.[tag] || 0) / stats.total * 100) + '%' : '0%', background: colors[tags.indexOf(tag)] }"></div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Sentiment Heatmap -->
    <div v-if="!loading && stats.total > 0" class="card heatmap-card">
      <div class="card-hd"><h3>📅 Sentiment Heatmap</h3><span class="heatmap-legend"><span class="hl-dot hl-pos"></span> Positive <span class="hl-dot hl-neg"></span> Negative <span class="hl-dot hl-neu"></span> Neutral</span></div>
      <div class="heatmap-grid">
        <div class="heatmap-months" :style="{ gridTemplateColumns: `28px repeat(${heatmapTotalWeeks}, 14px)` }">
          <span v-for="m in heatmapMonths" :key="m.label" :style="{ gridColumn: m.col + 1 }">{{ m.label }}</span>
        </div>
        <div class="heatmap-days">
          <span v-for="d in dayLabels" :key="d" class="hm-day-label">{{ d }}</span>
        </div>
        <div class="heatmap-cells" :style="{ gridTemplateColumns: `repeat(${heatmapTotalWeeks}, 14px)` }">
          <div v-for="(cell, i) in heatmapCells" :key="i"
               class="hm-cell"
               :class="cell.cls"
               :title="cell.title">
          </div>
        </div>
      </div>
    </div>

    <!-- Charts Row -->
    <div class="grid-2" v-if="!loading">
      <div class="card">
        <div class="card-hd"><h3>Sentiment This Week</h3></div>
        <Chart type="doughnut" :data="thisWeekData" ref="mainDonut" />
      </div>
      <div class="card">
        <div class="card-hd"><h3>Quick Overview</h3></div>
        <div class="quick-grid">
          <div class="quick-item qi-1">
            <span class="quick-val">{{ fmtDuration(quickStats.totalDuration) }}</span>
            <span class="quick-lbl">Total Talk Time</span>
          </div>
          <div class="quick-item qi-2">
            <span class="quick-val">{{ fmtDuration(quickStats.avgDuration) }}</span>
            <span class="quick-lbl">Avg Call Length</span>
          </div>
          <div class="quick-item qi-3">
            <span class="quick-val">{{ quickStats.busiestDay || '—' }}</span>
            <span class="quick-lbl">Busiest Day</span>
          </div>
          <div class="quick-item qi-4">
            <span class="quick-val" :class="quickStats.topTag.toLowerCase()">{{ quickStats.topTag || '—' }}</span>
            <span class="quick-lbl">Dominant Sentiment</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Customer Voice -->
    <div v-if="!loading && quotes.length" class="card">
      <div class="card-hd"><h3>💬 Customer Voice</h3></div>
      <div class="quotes-grid">
        <div v-for="q in quotes" :key="q._id" class="quote-item" :class="q.type">
          <div class="quote-meta">
            <span class="quote-badge">{{ q.type }}</span>
            <span class="quote-cust">{{ q.cid }}</span>
          </div>
          <p>"{{ q.text?.substring(0, 200) }}{{ q.text?.length > 200 ? '...' : '' }}"</p>
        </div>
      </div>
    </div>

    <!-- Leaderboard + Table row -->
    <div class="grid-2" v-if="!loading">
      <div class="card">
        <div class="card-hd"><h3>Customer Leaderboard</h3></div>
        <div class="lb-list" v-if="leaderboard.length">
          <div v-for="(c, i) in leaderboard" :key="c.cid" class="lb-item">
            <span class="lb-rank">{{ i + 1 }}</span>
            <div class="lb-info">
              <span class="lb-name">{{ c.name || c.cid }}</span>
              <span class="lb-detail">{{ c.total_calls }} calls</span>
            </div>
            <div class="lb-right">
              <Tag :tag="c.tag" />
              <span class="lb-score">{{ c.avg_sentiment }}</span>
            </div>
          </div>
        </div>
        <p v-else class="empty-note">No customer data yet</p>
      </div>

      <div class="card">
        <div class="card-hd"><h3>Recent Calls</h3></div>
        <div class="call-list" v-if="recentCalls.length">
          <div v-for="c in recentCalls.slice(0, 6)" :key="c._id" class="call-item">
            <div class="call-left">
              <span class="call-date">{{ c.call_date || (c.processed_at ? new Date(c.processed_at).toLocaleDateString() : '—') }}</span>
              <span class="call-cust">{{ c.customer_name || c.cid }}</span>
            </div>
            <div class="call-mid">
              <span class="call-dur">{{ fmtDuration(c.duration_secs || 0) }}</span>
            </div>
            <div class="call-right">
              <Tag :tag="c.tag" />
            </div>
          </div>
        </div>
        <p v-else class="empty-note">No calls yet. Upload audio files to get started.</p>
        <router-link to="/upload" class="card-link" v-if="!recentCalls.length">Go to Upload →</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import Chart from '../components/Chart.vue'
import Tag from '../components/Tag.vue'

const lang = ref('all')
const from = ref('')
const to = ref('')
const loading = ref(true)
const stats = ref({ total: 0, negative_pct: 0, positive_pct: 0, avg_score: 0, unique_customers: 0, tag_counts: {} })
const trend = ref([])
const recentCalls = ref([])
const leaderboard = ref([])
const quotes = ref([])
const mainDonut = ref(null)

const quickStats = ref({ totalDuration: 0, avgDuration: 0, busiestDay: '', topTag: '' })

// ── Heatmap (GitHub-style: 12 weeks × 7 days) ──
const heatmapCells = ref([])
const heatmapMonths = ref([])
const heatmapTotalWeeks = ref(12)
const dayLabels = ['Mon','','Wed','','Fri','','']

function buildHeatmap(daily) {
  const now = new Date()
  const WEEKS = 13  // extra week to cover current + future dates
  // End on Saturday of current week (so any date in current week shows)
  const endDate = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  endDate.setDate(endDate.getDate() + (6 - endDate.getDay()))  // next Saturday
  const startDate = new Date(endDate)
  startDate.setDate(startDate.getDate() - WEEKS * 7 + 1)

  const cells = []
  const months = []
  let lastMonth = -1
  let colIdx = 0

  // Fill day-then-week so CSS grid (row-first) lays out correctly:
  // columns = weeks, rows = days (Mon→Sun top-to-bottom)
  for (let w = 0; w < WEEKS; w++) {
    for (let d = 0; d < 7; d++) {
      const date = new Date(startDate)
      date.setDate(date.getDate() + w * 7 + d)
      const key = date.toISOString().slice(0, 10)
      const dayData = daily[key] || {}

      let domTag = ''; let domCount = 0
      for (const [tag, count] of Object.entries(dayData)) {
        // Normalize old tags
        const norm = tag === 'Frustrated' ? 'Negative' : tag === 'Satisfied' ? 'Positive' : tag
        if (count > domCount) { domTag = norm; domCount = count }
      }

      let cls = 'hm-none'
      if (domTag === 'Positive') cls = 'hm-pos'
      else if (domTag === 'Negative') cls = 'hm-neg'
      else if (domTag === 'Neutral') cls = 'hm-neu'

      const total = Object.values(dayData).reduce((a, b) => a + b, 0)
      cells.push({
        cls,
        title: `${key}: ${total} call${total !== 1 ? 's' : ''}${domTag ? ' — ' + domTag : ''}`
      })

      // Track first occurrence of each month for header
      const m = date.getMonth()
      if (m !== lastMonth) {
        const monLabel = date.toLocaleDateString('en-US', { month: 'short' })
        months.push({ label: monLabel, col: w + 1 })
        lastMonth = m
      }
    }
  }

  heatmapCells.value = cells
  heatmapMonths.value = months
  heatmapTotalWeeks.value = WEEKS
}

const tags = ['Positive', 'Negative', 'Neutral', 'Frustrated', 'Satisfied']
const colors = ['#27ae60', '#e74c3c', '#95a5a6', '#f39c12', '#3498db']
const thisWeekData = ref({})

function fmtDuration(sec) {
  if (!sec || sec <= 0) return '—'
  const m = Math.floor(sec / 60)
  const s = Math.round(sec % 60)
  return m > 0 ? `${m}m ${s}s` : `${s}s`
}

async function loadAll() {
  loading.value = true
  const params = { lang: lang.value }
  if (from.value) params.frm = from.value
  if (to.value) params.to = to.value

  const [s, t, calls, custs, crits, dailySent] = await Promise.all([
    axios.get('/api/analytics/summary', { params }),
    axios.get('/api/analytics/trend', { params }),
    axios.get('/api/mongo/calls', { params: { lang: lang.value, limit: 50 } }),
    axios.get('/api/mongo/customers'),
    axios.get('/api/mongo/critiques', { params: { limit: 20 } }),
    axios.get('/api/analytics/daily-sentiment', { params })
  ])

  stats.value = s.data
  trend.value = t.data
  recentCalls.value = calls.data
  buildHeatmap(dailySent.data)

  const cs = calls.data
  const totalDur = cs.reduce((a, c) => a + (c.duration_secs || 0), 0)
  const avgDur = cs.length ? Math.round(totalDur / cs.length) : 0

  const dayCounts = {}
  cs.forEach(c => {
    const d = c.call_date || (c.processed_at ? new Date(c.processed_at).toISOString().slice(0, 10) : null)
    if (d) dayCounts[d] = (dayCounts[d] || 0) + 1
  })
  const busiestDay = Object.entries(dayCounts).sort((a, b) => b[1] - a[1])[0]

  const tagCounts = {}
  cs.forEach(c => { tagCounts[c.tag] = (tagCounts[c.tag] || 0) + 1 })
  const topTag = Object.entries(tagCounts).sort((a, b) => b[1] - a[1])[0]

  quickStats.value = {
    totalDuration: totalDur,
    avgDuration: avgDur,
    busiestDay: busiestDay ? new Date(busiestDay[0]).toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' }) : '',
    topTag: topTag ? topTag[0] : ''
  }

  quotes.value = (crits.data || [])
    .filter(c => c.text && (c.type === 'suggestion' || c.type === 'feedback'))
    .slice(0, 4)

  leaderboard.value = custs.data
    .filter(c => c.avg_sentiment != null)
    .sort((a, b) => (b.avg_sentiment || 0) - (a.avg_sentiment || 0))
    .slice(0, 6)
    .map(c => ({
      ...c,
      tag: (c.avg_sentiment || 0) > 0.6 ? 'Positive' : (c.avg_sentiment || 0) < 0.4 ? 'Negative' : 'Neutral'
    }))

  const now = new Date()
  const weekStart = new Date(now); weekStart.setDate(now.getDate() - now.getDay())
  const thisWeek = t.data.filter(p => {
    const [y, w] = p.week.split('-W').map(Number)
    const d = new Date(y, 0, (w - 1) * 7)
    return d >= weekStart
  })
  thisWeekData.value = {
    labels: tags,
    datasets: [{ data: tags.map(tg => thisWeek.filter(p => p.tag === tg).reduce((a, b) => a + b.count, 0)), backgroundColor: colors }]
  }

  loading.value = false
}

onMounted(loadAll)
</script>

<style scoped>
.dash {
  display: flex; flex-direction: column; gap: 1.5rem; padding: 1rem 1.5rem;
  min-height: 100vh; width: 100%;
  background: #fff;
}

/* === Welcome Banner === */
.welcome-banner {
  background: linear-gradient(135deg, #27ae60 0%, #1abc9c 40%, #3498db 100%);
  margin: -1rem -1.5rem 0 -1.5rem; padding: 1.4rem 1.8rem;
  display: flex; justify-content: space-between; align-items: center;
  box-shadow: 0 4px 20px rgba(39,174,96,0.18);
  border-radius: 0;
}
.wb-left { display: flex; align-items: center; gap: 1rem; }
.wb-icon {
  width: 48px; height: 48px; border-radius: 50%;
  background: rgba(255,255,255,0.18); color: #fff;
  display: flex; align-items: center; justify-content: center;
}
.wb-left h2 { font-size: 1.15rem; font-weight: 700; color: #fff; line-height: 1.3; }
.wb-left p { font-size: 0.78rem; color: rgba(255,255,255,0.8); margin-top: 0.15rem; }
.wb-right { display: flex; gap: 1.8rem; }
.wb-stat { text-align: center; }
.wb-val { font-size: 1.3rem; font-weight: 700; color: #fff; display: block; }
.wb-lbl { font-size: 0.68rem; color: rgba(255,255,255,0.7); text-transform: uppercase; letter-spacing: 0.04em; }

/* === Controls === */
.dash-controls { display: flex; justify-content: flex-end; }
.filters { display: flex; gap: 0.5rem; align-items: center; }
.filters select, .filters input {
  padding: 0.45rem 0.85rem; border: 1px solid #e0e3e8; border-radius: 6px;
  font-size: 0.83rem; background: #fafcfd; color: #495057;
}
.filters input { width: 140px; }

/* === KPI Row === */
.kpi-row { display: grid; grid-template-columns: repeat(5, 1fr); gap: 1rem; }
.kpi-card {
  border-radius: 10px; padding: 1.2rem;
  box-shadow: 0 2px 10px rgba(0,0,0,0.04); display: flex; align-items: center; gap: 0.85rem;
  position: relative; transition: all 0.25s; border: 1px solid transparent;
  overflow: hidden;
}
.kpi-card::before {
  content: ''; position: absolute;
  width: 100px; height: 100px; border-radius: 50%;
  top: -35px; right: -25px; opacity: 0.25; pointer-events: none;
}
.kpi-card::after {
  content: ''; position: absolute;
  width: 55px; height: 55px; border-radius: 50%;
  bottom: -15px; left: 70px; opacity: 0.18; pointer-events: none;
}
.kpi-green::before, .kpi-green::after { background: #27ae60; }
.kpi-blue::before, .kpi-blue::after { background: #3498db; }
.kpi-orange::before, .kpi-orange::after { background: #f39c12; }
.kpi-red::before, .kpi-red::after { background: #e74c3c; }
.kpi-teal::before, .kpi-teal::after { background: #1abc9c; }
.kpi-card:hover { box-shadow: 0 6px 20px rgba(0,0,0,0.1); transform: translateY(-2px); }

.kpi-green { background: linear-gradient(135deg, #f0faf4 0%, #e0f5e9 100%); border-color: #c3e8d1; }
.kpi-green .kpi-icon { background: rgba(39,174,96,0.14); color: #27ae60; }

.kpi-blue { background: linear-gradient(135deg, #f2f7fd 0%, #e3f0f9 100%); border-color: #c3d9f2; }
.kpi-blue .kpi-icon { background: rgba(52,152,219,0.14); color: #3498db; }

.kpi-orange { background: linear-gradient(135deg, #fef8f2 0%, #fef0e0 100%); border-color: #f0d9b8; }
.kpi-orange .kpi-icon { background: rgba(243,156,18,0.14); color: #f39c12; }

.kpi-red { background: linear-gradient(135deg, #fef5f4 0%, #fde8e5 100%); border-color: #f0c4bf; }
.kpi-red .kpi-icon { background: rgba(231,76,60,0.14); color: #e74c3c; }

.kpi-teal { background: linear-gradient(135deg, #f2fdf9 0%, #e0f7f2 100%); border-color: #b8e8d8; }
.kpi-teal .kpi-icon { background: rgba(26,188,156,0.14); color: #1abc9c; }

.kpi-icon {
  width: 42px; height: 42px; border-radius: 50%; display: flex;
  align-items: center; justify-content: center; flex-shrink: 0;
}
.kpi-body { display: flex; flex-direction: column; }
.kpi-val { font-size: 1.35rem; font-weight: 700; color: #2c3e50; line-height: 1.2; }
.kpi-lbl { font-size: 0.72rem; color: #7f8c8d; margin-top: 0.12rem; font-weight: 500; }
.kpi-trend {
  position: absolute; top: 0.7rem; right: 1rem;
  font-size: 0.68rem; font-weight: 600; padding: 0.12rem 0.45rem; border-radius: 4px;
}
.kpi-trend.up { background: rgba(39,174,96,0.12); color: #27ae60; }
.kpi-trend.down { background: rgba(231,76,60,0.12); color: #e74c3c; }

/* === Sentiment Gauge === */
.sentiment-gauge {
  background: #fafcfd; border-radius: 10px; padding: 1.3rem 1.5rem;
  box-shadow: 0 2px 10px rgba(0,0,0,0.04); border: 1px solid #eef0f2;
  position: relative; overflow: hidden;
}
.sentiment-gauge::before {
  content: ''; position: absolute;
  width: 95px; height: 95px; border-radius: 50%;
  top: -30px; right: -22px; opacity: 0.09; pointer-events: none;
  background: #3498db;
}
.sentiment-gauge::after {
  content: ''; position: absolute;
  width: 50px; height: 50px; border-radius: 50%;
  bottom: -12px; left: 50px; opacity: 0.08; pointer-events: none;
  background: #27ae60;
}
.sentiment-gauge h3 { font-size: 0.92rem; font-weight: 600; color: #2c3e50; margin-bottom: 0.9rem; }
.gauge-bars { display: flex; flex-direction: column; gap: 0.55rem; }
.gauge-item { display: flex; flex-direction: column; gap: 0.2rem; }
.gauge-label { display: flex; justify-content: space-between; }
.gauge-tag { font-size: 0.78rem; font-weight: 600; color: #495057; }
.gauge-count { font-size: 0.74rem; font-weight: 600; color: #7f8c8d; }
.gauge-track { height: 10px; background: #eef0f2; border-radius: 5px; overflow: hidden; }
.gauge-fill { height: 100%; border-radius: 5px; transition: width 0.6s ease; min-width: 2px; }

/* === Card === */
.card {
  background: #fafcfd; border-radius: 10px; padding: 1.3rem;
  box-shadow: 0 2px 10px rgba(0,0,0,0.04); border: 1px solid #eef0f2;
  position: relative; overflow: hidden;
}
.card::before {
  content: ''; position: absolute;
  width: 90px; height: 90px; border-radius: 50%;
  top: -28px; right: -20px; opacity: 0.1; pointer-events: none;
  background: #3498db;
}
.card::after {
  content: ''; position: absolute;
  width: 45px; height: 45px; border-radius: 50%;
  bottom: -10px; left: 55px; opacity: 0.08; pointer-events: none;
  background: #1abc9c;
}
.card-hd { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; padding-bottom: 0.6rem; border-bottom: 1px solid #eef0f2; }
.card-hd h3 { font-size: 0.92rem; font-weight: 600; color: #2c3e50; }
.card-link { display: inline-block; margin-top: 0.8rem; color: #27ae60; font-size: 0.84rem; font-weight: 500; text-decoration: none; }
.card-link:hover { text-decoration: underline; }

/* === Grid === */
.grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; }

/* === Quick Stats === */
.quick-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.7rem; }
.quick-item {
  text-align: center; padding: 0.8rem; border-radius: 8px;
  position: relative; overflow: hidden;
}
.quick-item::before {
  content: ''; position: absolute;
  width: 55px; height: 55px; border-radius: 50%;
  top: -18px; right: -14px; opacity: 0.2; pointer-events: none;
}
.quick-item.qi-1 { background: linear-gradient(135deg, #f0faf4, #e8f5e9); }
.quick-item.qi-1::before { background: #27ae60; }
.quick-item.qi-2 { background: linear-gradient(135deg, #f2f7fd, #e8f0f8); }
.quick-item.qi-2::before { background: #3498db; }
.quick-item.qi-3 { background: linear-gradient(135deg, #fef8f2, #fef1e4); }
.quick-item.qi-3::before { background: #f39c12; }
.quick-item.qi-4 { background: linear-gradient(135deg, #fdf4f8, #f8e8f2); }
.quick-item.qi-4::before { background: #e91e63; }
.quick-val { font-size: 1.05rem; font-weight: 700; color: #2c3e50; display: block; }
.quick-val.positive { color: #27ae60; }
.quick-val.negative { color: #e74c3c; }
.quick-val.neutral { color: #6c757d; }
.quick-lbl { font-size: 0.7rem; color: #8d96a0; margin-top: 0.18rem; display: block; font-weight: 500; }

/* === Customer Voice === */
.quotes-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 0.8rem; }
.quote-item {
  background: linear-gradient(135deg, #fafcfd 0%, #f6f8fa 100%);
  border-radius: 8px; padding: 0.9rem 1rem; border-left: 3px solid #dee2e6;
}
.quote-item.suggestion { border-left-color: #3498db; background: linear-gradient(135deg, #f5fafd 0%, #eef6fc 100%); }
.quote-item.feedback { border-left-color: #f39c12; background: linear-gradient(135deg, #fefaf5 0%, #fdf4ea 100%); }
.quote-meta { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.35rem; }
.quote-badge {
  font-size: 0.66rem; font-weight: 600; text-transform: capitalize; padding: 0.1rem 0.45rem; border-radius: 4px;
}
.quote-item.suggestion .quote-badge { background: rgba(52,152,219,0.12); color: #2980b9; }
.quote-item.feedback .quote-badge { background: rgba(243,156,18,0.12); color: #e67e22; }
.quote-cust { font-size: 0.7rem; color: #adb5bd; }
.quote-item p { font-size: 0.82rem; line-height: 1.5; color: #495057; font-style: italic; }

/* === Leaderboard === */
.lb-list { display: flex; flex-direction: column; gap: 0.3rem; }
.lb-item {
  display: flex; align-items: center; gap: 0.65rem; padding: 0.55rem 0.65rem;
  border-radius: 8px; background: linear-gradient(135deg, #f8f9fb 0%, #f3f5f8 100%);
  transition: background 0.15s;
}
.lb-item:hover { background: linear-gradient(135deg, #f0f3f6 0%, #e9ecf0 100%); }
.lb-rank { width: 20px; text-align: center; font-size: 0.76rem; font-weight: 700; color: #adb5bd; }
.lb-info { flex: 1; min-width: 0; }
.lb-name { font-size: 0.83rem; font-weight: 600; color: #2c3e50; display: block; }
.lb-detail { font-size: 0.7rem; color: #8d96a0; }
.lb-right { display: flex; align-items: center; gap: 0.5rem; }
.lb-score { font-size: 0.78rem; font-weight: 600; color: #6c757d; }

/* === Call List === */
.call-list { display: flex; flex-direction: column; gap: 0.25rem; }
.call-item {
  display: flex; align-items: center; padding: 0.5rem 0.65rem;
  border-radius: 8px; background: linear-gradient(135deg, #f8f9fb 0%, #f3f5f8 100%);
  gap: 0.8rem; transition: all 0.15s;
}
.call-item:hover { background: linear-gradient(135deg, #f0f3f6 0%, #e9ecf0 100%); transform: translateX(2px); }
.call-left { flex: 1; min-width: 0; }
.call-date { font-size: 0.78rem; font-weight: 600; color: #2c3e50; display: block; }
.call-cust { font-size: 0.7rem; color: #8d96a0; }
.call-mid { flex-shrink: 0; }
.call-dur { font-size: 0.76rem; color: #6c757d; }
.call-right { flex-shrink: 0; }

/* === Skeleton === */
.skel-row { display: grid; grid-template-columns: repeat(5, 1fr); gap: 1rem; }
.skel-kpi { height: 88px; border-radius: 10px; background: linear-gradient(90deg, #f1f3f5 25%, #e9ecef 50%, #f1f3f5 75%); background-size: 200% 100%; animation: shimmer 1.5s infinite; }
@keyframes shimmer { 0% { background-position: 200% 0; } 100% { background-position: -200% 0; } }

.empty-note { color: #adb5bd; font-size: 0.84rem; text-align: center; padding: 1.5rem 0; }

/* === Heatmap === */
.heatmap-card { overflow: visible; }
.heatmap-legend { display: flex; align-items: center; gap: 0.3rem; font-size: 0.72rem; color: #8d96a0; }
.hl-dot { width: 10px; height: 10px; border-radius: 3px; display: inline-block; margin-right: 0.15rem; }
.hl-pos { background: #27ae60; }
.hl-neg { background: #e74c3c; }
.hl-neu { background: #cbd5e1; }
.heatmap-grid { display: flex; gap: 0; margin-top: 0.3rem; }
.heatmap-months {
  display: grid; gap: 2px; font-size: 0.65rem; color: #8d96a0; margin-bottom: 2px;
}
.heatmap-months span { text-align: left; }
.heatmap-days {
  display: flex; flex-direction: column; gap: 2px; margin-right: 4px;
}
.hm-day-label { font-size: 0.6rem; color: #adb5bd; height: 14px; line-height: 14px; }
.heatmap-cells {
  display: grid; grid-template-rows: repeat(7, 14px); gap: 2px;
}
.hm-cell {
  width: 14px; height: 14px; border-radius: 3px;
}
.hm-none { background: #eef0f2; }
.hm-pos { background: #27ae60; }
.hm-neg { background: #e74c3c; }
.hm-neu { background: #cbd5e1; }
</style>
