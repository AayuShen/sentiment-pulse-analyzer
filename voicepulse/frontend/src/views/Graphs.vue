<template>
  <div class="graphs">
    <!-- Gradient Banner -->
    <div class="graphs-banner">
      <div class="gb-left">
        <div class="gb-icon">
          <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>
        </div>
        <div>
          <h2>Graphs &amp; Trends</h2>
          <p>Visualize sentiment patterns and track changes over time</p>
        </div>
      </div>
      <div class="gb-right">
        <div class="gb-stat">
          <span class="gb-val">{{ stats.total || 0 }}</span>
          <span class="gb-lbl">Total Calls</span>
        </div>
        <div class="gb-stat">
          <span class="gb-val">{{ stats.unique_customers || '—' }}</span>
          <span class="gb-lbl">Customers</span>
        </div>
        <div class="gb-stat gb-stat-green">
          <span class="gb-val">{{ stats.positive_pct || 0 }}%</span>
          <span class="gb-lbl">Positive</span>
        </div>
        <div class="gb-stat gb-stat-red">
          <span class="gb-val">{{ stats.negative_pct || 0 }}%</span>
          <span class="gb-lbl">Negative</span>
        </div>
      </div>
    </div>

    <div class="graphs-controls">
      <div class="filters">
        <select v-model="lang" @change="loadAll">
          <option value="all">All Languages</option>
          <option value="en">English</option>
          <option value="hi">Hindi</option>
          <option value="te">Telugu</option>
          <option value="ta">Tamil</option>
        </select>
      </div>
    </div>

    <div v-if="loading" class="skeleton-grid">
      <div class="skel" v-for="i in 4" :key="i"></div>
    </div>

    <div v-else class="graphs-content">
      <div class="charts-row">
        <div class="card"><div class="card-hd"><h3>Sentiment Distribution</h3></div><Chart type="bar" :data="barData" ref="barChart" /></div>
        <div class="card"><div class="card-hd"><h3>Weekly Trend</h3></div><Chart type="line" :data="lineData" ref="lineChart" /></div>
      </div>
      <div class="charts-row">
        <div class="card"><div class="card-hd"><h3>This Week</h3></div><Chart type="doughnut" :data="thisWeekData" ref="donut1" /></div>
        <div class="card"><div class="card-hd"><h3>Last Week</h3></div><Chart type="doughnut" :data="lastWeekData" ref="donut2" /></div>
      </div>

      <div v-if="topicData?.labels?.length" class="card topic-chart">
        <div class="card-hd"><h3>Topic Distribution</h3></div>
        <Chart type="bar" :data="topicData" ref="topicChart" />
      </div>

      <div class="insights-row">
        <div class="insight-card negative">
          <div class="insight-head">
            <span class="insight-icon">⚠</span>
            <h3>Critical Negative Points</h3>
          </div>
          <div v-if="critiques.filter(c => c.type === 'complaint').length">
            <div v-for="c in critiques.filter(c => c.type === 'complaint').slice(0, 5)" :key="c._id" class="insight-item">
              <span class="insight-topic">{{ c.topic }}</span>
              <p>{{ c.text?.substring(0, 120) }}{{ c.text?.length > 120 ? '...' : '' }}</p>
            </div>
          </div>
          <p v-else class="empty-note">No complaints detected</p>
        </div>

        <div class="insight-card positive">
          <div class="insight-head">
            <span class="insight-icon">💡</span>
            <h3>Positive Suggestions</h3>
          </div>
          <div v-if="critiques.filter(c => c.type === 'suggestion').length">
            <div v-for="c in critiques.filter(c => c.type === 'suggestion').slice(0, 5)" :key="c._id" class="insight-item">
              <span class="insight-topic">{{ c.topic }}</span>
              <p>{{ c.text?.substring(0, 120) }}{{ c.text?.length > 120 ? '...' : '' }}</p>
            </div>
          </div>
          <p v-else class="empty-note">No suggestions detected</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import Chart from '../components/Chart.vue'

const lang = ref('all')
const loading = ref(true)
const stats = ref({})
const trend = ref([])
const critiques = ref([])
const barChart = ref(null)

const tags = ['Positive', 'Negative', 'Neutral', 'Frustrated', 'Satisfied']
const colors = ['#27ae60', '#e74c3c', '#7f8c8d', '#f39c12', '#3498db']
const fillColors = ['rgba(39,174,96,0.75)', 'rgba(231,76,60,0.75)', 'rgba(127,140,141,0.75)', 'rgba(243,156,18,0.75)', 'rgba(52,152,219,0.75)']

const barData = ref({})
const lineData = ref({})
const thisWeekData = ref({})
const lastWeekData = ref({})
const topicData = ref({})

async function loadAll() {
  loading.value = true
  const [s, t, c] = await Promise.all([
    axios.get('/api/analytics/summary', { params: { lang: lang.value } }),
    axios.get('/api/analytics/trend', { params: { lang: lang.value } }),
    axios.get('/api/mongo/critiques', { params: { limit: 100 } })
  ])
  stats.value = s.data
  trend.value = t.data
  critiques.value = c.data

  barData.value = {
    labels: tags,
    datasets: [{
      label: 'Calls',
      data: tags.map(tg => s.data.tag_counts?.[tg] || 0),
      backgroundColor: fillColors,
      borderColor: colors,
      borderWidth: 2,
      borderRadius: 6,
      borderSkipped: false,
    }]
  }

  const weeks = [...new Set(t.data.map(p => p.week))].sort()
  lineData.value = {
    labels: weeks,
    datasets: tags.map((tag, i) => ({
      label: tag,
      data: weeks.map(w => t.data.find(p => p.week === w && p.tag === tag)?.count || 0),
      borderColor: colors[i],
      borderWidth: 2.5,
      tension: 0.35,
      pointBackgroundColor: colors[i],
      pointBorderColor: '#fff',
      pointBorderWidth: 2,
      pointRadius: 3,
      pointHoverRadius: 6,
      fill: false
    }))
  }

  const now = new Date()
  const weekStart = new Date(now); weekStart.setDate(now.getDate() - now.getDay())
  const lastWeekStart = new Date(weekStart); lastWeekStart.setDate(weekStart.getDate() - 7)

  const thisWeek = t.data.filter(p => {
    const [y, w] = p.week.split('-W').map(Number)
    const d = new Date(y, 0, (w - 1) * 7)
    return d >= weekStart
  })
  const lastWeek = t.data.filter(p => {
    const [y, w] = p.week.split('-W').map(Number)
    const d = new Date(y, 0, (w - 1) * 7)
    return d >= lastWeekStart && d < weekStart
  })

  thisWeekData.value = {
    labels: tags,
    datasets: [{ data: tags.map(tg => thisWeek.filter(p => p.tag === tg).reduce((a, b) => a + b.count, 0)), backgroundColor: fillColors, borderColor: colors, borderWidth: 2 }]
  }
  lastWeekData.value = {
    labels: tags,
    datasets: [{ data: tags.map(tg => lastWeek.filter(p => p.tag === tg).reduce((a, b) => a + b.count, 0)), backgroundColor: fillColors, borderColor: colors, borderWidth: 2 }]
  }

  // Topic distribution from critiques
  const topicCounts = {}
  c.data.forEach(item => {
    const t = item.topic || 'Other'
    topicCounts[t] = (topicCounts[t] || 0) + 1
  })
  const sortedTopics = Object.entries(topicCounts).sort((a, b) => b[1] - a[1]).slice(0, 8)
  const topicColors = ['#3498db','#9b59b6','#f39c12','#e74c3c','#27ae60','#1abc9c','#e67e22','#2980b9']
  const topicFills = ['rgba(52,152,219,0.75)','rgba(155,89,182,0.75)','rgba(243,156,18,0.75)','rgba(231,76,60,0.75)','rgba(39,174,96,0.75)','rgba(26,188,156,0.75)','rgba(230,126,34,0.75)','rgba(41,128,185,0.75)']
  if (sortedTopics.length) {
    topicData.value = {
      labels: sortedTopics.map(([t]) => t),
      datasets: [{
        label: 'Mentions',
        data: sortedTopics.map(([, c]) => c),
        backgroundColor: topicFills.slice(0, sortedTopics.length),
        borderColor: topicColors.slice(0, sortedTopics.length),
        borderWidth: 2,
        borderRadius: 6,
        borderSkipped: false,
      }]
    }
  }

  loading.value = false
}

onMounted(loadAll)
</script>

<style scoped>
.graphs {
  display: flex; flex-direction: column; gap: 1.5rem;
  padding: 1rem 1.5rem; min-height: 100vh; width: 100%;
  background: #fff;
}

/* === Gradient Banner === */
.graphs-banner {
  background: linear-gradient(135deg, #3498db 0%, #9b59b6 60%, #8e44ad 100%);
  margin: -1rem -1.5rem 0 -1.5rem; padding: 1.4rem 1.8rem;
  display: flex; justify-content: space-between; align-items: center;
  box-shadow: 0 4px 20px rgba(52,152,219,0.2);
  border-radius: 0;
}
.gb-left { display: flex; align-items: center; gap: 1rem; }
.gb-icon {
  width: 48px; height: 48px; border-radius: 50%;
  background: rgba(255,255,255,0.18); color: #fff;
  display: flex; align-items: center; justify-content: center;
}
.gb-left h2 { font-size: 1.15rem; font-weight: 700; color: #fff; line-height: 1.3; }
.gb-left p { font-size: 0.78rem; color: rgba(255,255,255,0.8); margin-top: 0.15rem; }
.gb-right { display: flex; gap: 1.6rem; }
.gb-stat { text-align: center; }
.gb-val { font-size: 1.3rem; font-weight: 700; color: #fff; display: block; }
.gb-lbl { font-size: 0.68rem; color: rgba(255,255,255,0.7); text-transform: uppercase; letter-spacing: 0.04em; }
.gb-stat-green .gb-val { color: #a3e4bc; }
.gb-stat-red .gb-val { color: #f5b7b1; }

.graphs-controls { display: flex; justify-content: flex-end; }
.filters select {
  padding: 0.45rem 0.85rem; border: 1px solid #e0e3e8; border-radius: 6px;
  font-size: 0.83rem; background: #fafcfd; color: #495057; cursor: pointer;
}

.skeleton-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
.skel {
  height: 300px; border-radius: 10px;
  background: linear-gradient(90deg, #f1f3f5 25%, #e9ecef 50%, #f1f3f5 75%);
  background-size: 200% 100%; animation: shimmer 1.5s infinite;
}
@keyframes shimmer { 0% { background-position: 200% 0; } 100% { background-position: -200% 0; } }

.charts-row { display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; }
.topic-chart { margin-top: 0; }

/* === Card === */
.card {
  background: #fafcfd; border-radius: 10px; padding: 1.3rem;
  box-shadow: 0 2px 10px rgba(0,0,0,0.04); border: 1px solid #eef0f2;
  position: relative; overflow: hidden;
}
.card::before {
  content: ''; position: absolute;
  width: 90px; height: 90px; border-radius: 50%;
  top: -30px; right: -20px; opacity: 0.12; pointer-events: none;
  background: #3498db;
}
.card::after {
  content: ''; position: absolute;
  width: 48px; height: 48px; border-radius: 50%;
  bottom: -12px; left: 55px; opacity: 0.1; pointer-events: none;
  background: #9b59b6;
}
.card-hd { margin-bottom: 0.8rem; padding-bottom: 0.5rem; border-bottom: 1px solid #eef0f2; }
.card-hd h3 { font-size: 0.92rem; font-weight: 600; color: #2c3e50; }

/* === Insight Cards === */
.insights-row { display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; }
.insight-card {
  border-radius: 10px; padding: 1.3rem;
  box-shadow: 0 2px 10px rgba(0,0,0,0.04); border: 1px solid #eef0f2;
  position: relative; overflow: hidden;
}
.insight-card::before {
  content: ''; position: absolute;
  width: 80px; height: 80px; border-radius: 50%;
  top: -25px; right: -18px; opacity: 0.15; pointer-events: none;
}
.insight-card::after {
  content: ''; position: absolute;
  width: 42px; height: 42px; border-radius: 50%;
  bottom: -10px; left: 50px; opacity: 0.1; pointer-events: none;
}
.insight-card.negative::before { background: #e74c3c; }
.insight-card.negative::after { background: #c0392b; }
.insight-card.positive::before { background: #27ae60; }
.insight-card.positive::after { background: #1e8449; }
.insight-card.negative {
  background: linear-gradient(135deg, #fefafa 0%, #fdf5f5 100%);
  border-top: 3px solid #e74c3c; border-color: #f0d0cd #eef0f2 #eef0f2 #eef0f2;
}
.insight-card.positive {
  background: linear-gradient(135deg, #fafdfa 0%, #f2faf5 100%);
  border-top: 3px solid #27ae60; border-color: #c3e8d1 #eef0f2 #eef0f2 #eef0f2;
}
.insight-head { display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.8rem; }
.insight-icon { font-size: 1.1rem; }
.insight-head h3 { font-size: 0.9rem; font-weight: 600; color: #2c3e50; }
.insight-item { padding: 0.55rem 0; border-bottom: 1px solid #eef0f2; }
.insight-item:last-child { border-bottom: none; }
.insight-topic {
  display: inline-block; padding: 0.15rem 0.5rem;
  border-radius: 6px; font-size: 0.72rem; font-weight: 600; margin-bottom: 0.3rem;
}
.insight-card.negative .insight-topic { background: rgba(231,76,60,0.1); color: #e74c3c; }
.insight-card.positive .insight-topic { background: rgba(39,174,96,0.1); color: #27ae60; }
.insight-item p { font-size: 0.84rem; line-height: 1.5; color: #495057; }
.empty-note { color: #adb5bd; font-size: 0.85rem; text-align: center; padding: 1rem 0; }
</style>
