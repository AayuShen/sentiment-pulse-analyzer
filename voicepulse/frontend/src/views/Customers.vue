<template>
  <div class="cust-page">
    <!-- Gradient Banner -->
    <div class="cust-banner">
      <div class="bnr-left">
        <div class="bnr-icon">
          <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 00-3-3.87"/><path d="M16 3.13a4 4 0 010 7.75"/></svg>
        </div>
        <div>
          <h2>Customer Intel</h2>
          <p>Behavioral profiles, call history &amp; AI-generated briefs per customer</p>
        </div>
      </div>
      <div class="bnr-right">
        <div class="bnr-stat">
          <span class="bnr-val">{{ profiles.length }}</span>
          <span class="bnr-lbl">Customers</span>
        </div>
        <div class="bnr-stat">
          <span class="bnr-val">{{ totalCalls }}</span>
          <span class="bnr-lbl">Total Calls</span>
        </div>
      </div>
    </div>

    <!-- Search + Filters -->
    <div class="ctl-row">
      <div class="search-wrap">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
        <input v-model="search" placeholder="Search by customer name..." class="search-inp" @input="debounceSearch" />
      </div>
      <div class="filter-group">
        <input type="date" v-model="dateFrom" @change="loadData" title="From date" />
        <input type="date" v-model="dateTo" @change="loadData" title="To date" />
        <select v-model="callType" @change="loadData">
          <option value="">All Call Types</option>
          <option value="praise">Praise</option>
          <option value="complaint">Complaint</option>
          <option value="enquiry">Enquiry</option>
          <option value="suggestion">Suggestion</option>
          <option value="feedback">Feedback</option>
        </select>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="skel-list">
      <div class="skel-card" v-for="i in 4" :key="i"></div>
    </div>

    <!-- Empty -->
    <div v-else-if="filteredProfiles.length === 0" class="empty-state">
      <div class="empty-icon">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/><line x1="18" y1="11" x2="18" y2="17"/><line x1="15" y1="14" x2="21" y2="14"/></svg>
      </div>
      <h3>No customers found</h3>
      <p>Upload and process some calls to start building customer profiles.</p>
    </div>

    <!-- Customer Cards -->
    <div v-else class="cust-list">
      <div v-for="prof in filteredProfiles" :key="prof.cid" class="cust-card" :class="{ expanded: expandedId === prof.cid }">
        <!-- Card Header (clickable) -->
        <div class="card-head" @click="toggleExpand(prof.cid)">
          <div class="head-main">
            <div class="head-avatar">{{ prof.name.charAt(0).toUpperCase() }}</div>
            <div class="head-info">
              <div class="head-name">{{ prof.name }}</div>
              <div class="head-cid">{{ prof.cid }}</div>
            </div>
          </div>
          <div class="head-meta">
            <div class="meta-chip" v-for="ct in prof.call_types" :key="ct" :class="chipClass(ct)">
              {{ ct }}
            </div>
            <span v-if="prof.tags?.length" class="tag-dot-row">
              <span v-for="t in prof.tags" :key="t" class="tag-dot" :class="dotClass(t)" :title="t"></span>
            </span>
          </div>
          <div class="head-stats">
            <div class="hstat">
              <span class="hstat-val">{{ prof.total_calls }}</span>
              <span class="hstat-lbl">calls</span>
            </div>
            <div class="hstat">
              <span class="hstat-val" :class="scoreClass(prof.avg_sentiment)">{{ (prof.avg_sentiment * 100).toFixed(0) }}%</span>
              <span class="hstat-lbl">avg score</span>
            </div>
            <div class="hstat">
              <span class="hstat-val">{{ fmtDate(prof.last_call_date) }}</span>
              <span class="hstat-lbl">last call</span>
            </div>
          </div>
          <span class="expand-arrow">{{ expandedId === prof.cid ? '▴' : '▾' }}</span>
        </div>

        <!-- Expanded: Call History -->
        <div v-if="expandedId === prof.cid" class="card-body">
          <!-- AI Brief / Notes -->
          <div v-if="latestBrief(prof)" class="brief-box">
            <div class="brief-label">🤖 AI Customer Brief</div>
            <p>{{ latestBrief(prof) }}</p>
          </div>
          <div v-else class="brief-box brief-empty">
            <div class="brief-label">🤖 AI Customer Brief</div>
            <p>No brief generated yet. Process more calls with this customer to generate behavioral insights.</p>
          </div>

          <!-- Customer Tags -->
          <div class="tags-section">
            <div class="tags-label">🏷️ Labels</div>
            <div class="tags-row">
              <span v-for="(t, ti) in prof.tags" :key="ti" class="tag-chip" :class="dotClass(t)">
                {{ t }}
                <button class="tag-rm" @click.stop="removeTag(prof, ti)">&times;</button>
              </span>
              <input
                v-model="tagInputs[prof.cid]"
                class="tag-inp"
                placeholder="+ Add label..."
                @keydown.enter.prevent="addTag(prof)"
                @keydown.backspace="maybeRemoveLast(prof, $event)"
              />
            </div>
          </div>

          <!-- Call List -->
          <h4>Call History ({{ prof.calls.length }})</h4>
          <div class="call-table-wrap">
            <table class="call-table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Type</th>
                  <th>Sentiment</th>
                  <th>Score</th>
                  <th>Duration</th>
                  <th>Summary</th>
                  <th>Topics</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="call in prof.calls" :key="call._id">
                  <td class="td-date">{{ call.call_date || fmtDate(call.processed_at) }}</td>
                  <td><span class="type-badge" :class="typeClass(call)">{{ call.call_type }}</span></td>
                  <td><span class="tag-badge" :class="tagClass(call.tag)">{{ call.tag }}</span></td>
                  <td class="td-score">{{ (call.score * 100).toFixed(0) }}%</td>
                  <td class="td-dur">{{ fmtDuration(call.duration_secs) }}</td>
                  <td class="td-summary">{{ call.summary || '—' }}</td>
                  <td class="td-topics">
                    <span v-if="call.topics.length">{{ call.topics.join(', ') }}</span>
                    <span v-else>—</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'

const profiles = ref([])
const loading = ref(true)
const search = ref('')
const dateFrom = ref('')
const dateTo = ref('')
const callType = ref('')
const expandedId = ref(null)
const tagInputs = ref({})

let searchTimer = null

const filteredProfiles = computed(() => {
  if (!search.value) return profiles.value
  const q = search.value.toLowerCase()
  return profiles.value.filter(p =>
    (p.name || '').toLowerCase().includes(q) ||
    (p.cid || '').toLowerCase().includes(q)
  )
})

const totalCalls = computed(() =>
  profiles.value.reduce((a, p) => a + (p.total_calls || 0), 0)
)

function debounceSearch() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(loadData, 300)
}

function toggleExpand(cid) {
  expandedId.value = expandedId.value === cid ? null : cid
}

function fmtDate(d) {
  if (!d) return '—'
  try { return new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) } catch { return d }
}

function fmtDuration(sec) {
  if (!sec) return '—'
  const m = Math.floor(sec / 60)
  const s = Math.round(sec % 60)
  return m > 0 ? `${m}m ${s}s` : `${s}s`
}

function latestBrief(prof) {
  for (const c of prof.calls) {
    if (c.brief) return c.brief
  }
  return ''
}

function chipClass(ct) {
  const m = {
    Praise: 'chip-praise', Complaint: 'chip-complaint',
    Enquiry: 'chip-enquiry', Suggestion: 'chip-suggestion', Feedback: 'chip-feedback'
  }
  return m[ct] || 'chip-default'
}

function dotClass(tag) {
  const lower = (tag || '').toLowerCase()
  if (lower.includes('vip')) return 'dot-vip'
  if (lower.includes('risk') || lower.includes('angry')) return 'dot-risk'
  if (lower.includes('new') || lower.includes('lead')) return 'dot-new'
  if (lower.includes('follow') || lower.includes('pending')) return 'dot-follow'
  if (lower.includes('churn') || lower.includes('lost')) return 'dot-churn'
  return 'dot-default'
}

async function addTag(prof) {
  const inp = tagInputs.value[prof.cid]
  if (!inp || !inp.trim()) return
  const tag = inp.trim()
  if (!prof.tags) prof.tags = []
  if (!prof.tags.includes(tag)) {
    prof.tags.push(tag)
    await saveTags(prof)
  }
  tagInputs.value[prof.cid] = ''
}

function removeTag(prof, idx) {
  prof.tags.splice(idx, 1)
  saveTags(prof)
}

function maybeRemoveLast(prof, e) {
  if (!tagInputs.value[prof.cid] && prof.tags?.length) {
    prof.tags.pop()
    saveTags(prof)
  }
}

async function saveTags(prof) {
  try {
    await axios.patch(`/api/mongo/customers/${prof.cid}/tags`, { tags: prof.tags || [] })
  } catch (e) {
    console.error('Failed to save tags:', e)
  }
}

function typeClass(call) {
  return `type-${(call.call_type || 'enquiry').toLowerCase()}`
}

function tagClass(tag) {
  const m = { Positive: 'tag-pos', Satisfied: 'tag-pos', Negative: 'tag-neg', Frustrated: 'tag-neg', Neutral: 'tag-neu' }
  return m[tag] || 'tag-neu'
}

function scoreClass(score) {
  if (score >= 0.7) return 'score-high'
  if (score >= 0.4) return 'score-mid'
  return 'score-low'
}

async function loadData() {
  loading.value = true
  const params = {}
  if (dateFrom.value) params.date_from = dateFrom.value
  if (dateTo.value) params.date_to = dateTo.value
  if (callType.value) params.call_type = callType.value
  if (search.value) params.search = search.value

  try {
    const { data } = await axios.get('/api/mongo/customer-profiles', { params })
    profiles.value = data || []
  } catch (e) {
    console.error('Failed to load customer profiles:', e)
    profiles.value = []
  }
  loading.value = false
}

onMounted(loadData)
</script>

<style scoped>
.cust-page {
  display: flex; flex-direction: column; gap: 1.5rem;
  padding: 1rem 1.5rem; min-height: 100vh; width: 100%;
  background: #fff;
}

/* === Gradient Banner (Pink → Magenta → Rose) === */
.cust-banner {
  background: linear-gradient(135deg, #e91e63 0%, #c2185b 50%, #880e4f 100%);
  margin: -1rem -1.5rem 0 -1.5rem; padding: 1.4rem 1.8rem;
  display: flex; justify-content: space-between; align-items: center;
  box-shadow: 0 4px 20px rgba(233,30,99,0.22);
  border-radius: 0;
}
.bnr-left { display: flex; align-items: center; gap: 1rem; }
.bnr-icon {
  width: 48px; height: 48px; border-radius: 50%;
  background: rgba(255,255,255,0.18); color: #fff;
  display: flex; align-items: center; justify-content: center;
}
.bnr-left h2 { font-size: 1.15rem; font-weight: 700; color: #fff; line-height: 1.3; margin: 0; padding: 0; border: none; }
.bnr-left p { font-size: 0.78rem; color: rgba(255,255,255,0.8); margin-top: 0.15rem; }
.bnr-right { display: flex; gap: 1.8rem; }
.bnr-stat { text-align: center; }
.bnr-val { font-size: 1.3rem; font-weight: 700; color: #fff; display: block; }
.bnr-lbl { font-size: 0.68rem; color: rgba(255,255,255,0.7); text-transform: uppercase; letter-spacing: 0.04em; }

/* === Search + Filters === */
.ctl-row {
  display: flex; gap: 1rem; align-items: center; flex-wrap: wrap;
}
.search-wrap {
  display: flex; align-items: center; gap: 0.5rem;
  padding: 0.5rem 0.85rem; border: 1px solid #e0e3e8; border-radius: 8px;
  background: #fafcfd; flex: 1; min-width: 220px;
}
.search-wrap svg { color: #adb5bd; flex-shrink: 0; }
.search-inp {
  border: none; background: none; font-size: 0.86rem; color: #2c3e50;
  outline: none; flex: 1;
}
.search-inp::placeholder { color: #b0b8c1; }
.filter-group { display: flex; gap: 0.5rem; }
.filter-group input[type="date"],
.filter-group select {
  padding: 0.5rem 0.75rem; border: 1px solid #e0e3e8; border-radius: 8px;
  font-size: 0.83rem; background: #fafcfd; color: #495057; cursor: pointer;
}

/* === Skeleton === */
.skel-list { display: flex; flex-direction: column; gap: 0.7rem; }
.skel-card {
  height: 72px; border-radius: 10px;
  background: linear-gradient(90deg, #f1f3f5 25%, #e9ecef 50%, #f1f3f5 75%);
  background-size: 200% 100%; animation: shimmer 1.5s infinite;
}
@keyframes shimmer { 0% { background-position: 200% 0; } 100% { background-position: -200% 0; } }

/* === Empty === */
.empty-state {
  text-align: center; padding: 4rem 2rem;
  background: linear-gradient(135deg, #fafcfd 0%, #f3f6f9 100%);
  border-radius: 10px; border: 2px dashed #d4dce4;
  color: #8d96a0;
}
.empty-icon { margin-bottom: 1rem; color: #adb5bd; }
.empty-state h3 { font-size: 1.1rem; color: #2c3e50; margin-bottom: 0.5rem; }
.empty-state p { font-size: 0.88rem; }

/* === Customer Cards === */
.cust-list { display: flex; flex-direction: column; gap: 0.7rem; }

.cust-card {
  background: #fafcfd; border-radius: 10px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.04); border: 1px solid #eef0f2;
  overflow: hidden; transition: box-shadow 0.2s;
}
.cust-card:hover { box-shadow: 0 4px 16px rgba(0,0,0,0.08); }
.cust-card.expanded { border-color: #e91e63; box-shadow: 0 4px 20px rgba(233,30,99,0.1); }

.card-head {
  display: flex; align-items: center; gap: 0.8rem;
  padding: 0.9rem 1.3rem; cursor: pointer; user-select: none;
  transition: background 0.15s;
}
.card-head:hover { background: linear-gradient(135deg, #fdf2f8 0%, #fce4ec 100%); }

.head-main { display: flex; align-items: center; gap: 0.7rem; min-width: 0; }
.head-avatar {
  width: 42px; height: 42px; border-radius: 50%;
  background: linear-gradient(135deg, #e91e63, #c2185b);
  color: #fff; font-weight: 700; font-size: 1.1rem;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.head-name { font-size: 0.92rem; font-weight: 600; color: #2c3e50; white-space: nowrap; }
.head-cid { font-size: 0.72rem; color: #8d96a0; margin-top: 0.08rem; }

.head-meta { display: flex; gap: 0.35rem; flex-wrap: wrap; flex-shrink: 1; }
.meta-chip {
  padding: 0.18rem 0.55rem; border-radius: 6px;
  font-size: 0.7rem; font-weight: 600; text-transform: capitalize;
}
.chip-praise { background: rgba(39,174,96,0.1); color: #27ae60; }
.chip-complaint { background: rgba(231,76,60,0.1); color: #e74c3c; }
.chip-enquiry { background: rgba(52,152,219,0.1); color: #2980b9; }
.chip-suggestion { background: rgba(155,89,182,0.1); color: #8e44ad; }
.chip-feedback { background: rgba(243,156,18,0.1); color: #e67e22; }
.chip-default { background: #f3f5f8; color: #6c757d; }

/* Tag dots (card header) */
.tag-dot-row { display: flex; gap: 3px; align-items: center; margin-left: 2px; }
.tag-dot { width: 8px; height: 8px; border-radius: 50%; }
.dot-vip { background: #f39c12; }
.dot-risk { background: #e74c3c; }
.dot-new { background: #3498db; }
.dot-follow { background: #9b59b6; }
.dot-churn { background: #6c757d; }
.dot-default { background: #95a5a6; }

/* Tags section (expanded) */
.tags-section { margin-bottom: 0.8rem; }
.tags-label { font-size: 0.8rem; font-weight: 600; color: #495057; margin-bottom: 0.4rem; }
.tags-row { display: flex; gap: 0.4rem; align-items: center; flex-wrap: wrap; }
.tag-chip {
  display: inline-flex; align-items: center; gap: 0.3rem;
  padding: 0.22rem 0.55rem; border-radius: 6px;
  font-size: 0.73rem; font-weight: 600;
}
.tag-chip.dot-vip { background: rgba(243,156,18,0.12); color: #e67e22; }
.tag-chip.dot-risk { background: rgba(231,76,60,0.1); color: #e74c3c; }
.tag-chip.dot-new { background: rgba(52,152,219,0.1); color: #2980b9; }
.tag-chip.dot-follow { background: rgba(155,89,182,0.1); color: #8e44ad; }
.tag-chip.dot-churn { background: rgba(108,117,125,0.1); color: #6c757d; }
.tag-chip.dot-default { background: #f3f5f8; color: #6c757d; }
.tag-rm {
  background: none; border: none; cursor: pointer; font-size: 1rem; line-height: 1;
  padding: 0; color: inherit; opacity: 0.5; transition: opacity 0.15s;
}
.tag-rm:hover { opacity: 1; }
.tag-inp {
  border: 1px dashed #d4dce4; border-radius: 6px; padding: 0.22rem 0.55rem;
  font-size: 0.73rem; outline: none; background: transparent; color: #495057;
  min-width: 120px;
}
.tag-inp:focus { border-color: #e91e63; border-style: solid; }
.tag-inp::placeholder { color: #b0b8c1; }

.head-stats { display: flex; gap: 1.2rem; flex-shrink: 0; margin-left: auto; }
.hstat { text-align: center; }
.hstat-val { font-size: 0.92rem; font-weight: 700; color: #2c3e50; display: block; }
.hstat-lbl { font-size: 0.66rem; color: #8d96a0; text-transform: uppercase; letter-spacing: 0.03em; }
.score-high { color: #27ae60; }
.score-mid { color: #f39c12; }
.score-low { color: #e74c3c; }

.expand-arrow { font-size: 1.1rem; color: #adb5bd; flex-shrink: 0; transition: transform 0.2s; }

/* === Expanded Body === */
.card-body {
  padding: 0 1.3rem 1.2rem; border-top: 1px solid #f0d0d8;
}

/* Brief Box */
.brief-box {
  background: linear-gradient(135deg, #fdf2f8 0%, #f8e4f0 100%);
  border-left: 3px solid #e91e63; border-radius: 8px;
  padding: 0.9rem 1.1rem; margin-bottom: 1rem;
}
.brief-box.brief-empty { background: linear-gradient(135deg, #f8f9fa 0%, #f3f5f8 100%); border-left-color: #d4dce4; }
.brief-label { font-size: 0.78rem; font-weight: 600; color: #c2185b; margin-bottom: 0.35rem; }
.brief-empty .brief-label { color: #8d96a0; }
.brief-box p { font-size: 0.84rem; line-height: 1.55; color: #495057; }
.brief-empty p { color: #adb5bd; font-style: italic; }

.card-body h4 {
  font-size: 0.85rem; font-weight: 600; color: #495057;
  margin-bottom: 0.6rem; padding-bottom: 0.4rem; border-bottom: 1px solid #eef0f2;
}

/* Call History Table */
.call-table-wrap { overflow-x: auto; }
.call-table { width: 100%; border-collapse: collapse; font-size: 0.81rem; }
.call-table th {
  text-align: left; padding: 0.5rem 0.65rem; font-weight: 600;
  font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.04em;
  color: #8d96a0; background: linear-gradient(135deg, #f5f7fa, #eef1f5);
  border-bottom: 2px solid #dce2e8; white-space: nowrap;
}
.call-table td {
  padding: 0.5rem 0.65rem; border-bottom: 1px solid #f0f2f5;
  vertical-align: middle; color: #495057;
}
.call-table tr:last-child td { border-bottom: none; }
.call-table tr:hover td { background: rgba(233,30,99,0.02); }
.td-date { white-space: nowrap; color: #8d96a0; font-size: 0.8rem; }
.td-score { font-weight: 600; white-space: nowrap; }
.td-dur { white-space: nowrap; color: #6c757d; font-size: 0.78rem; }
.td-summary { max-width: 260px; line-height: 1.45; }
.td-topics { max-width: 180px; font-size: 0.78rem; color: #6c757d; }

/* Badges */
.type-badge {
  display: inline-block; padding: 0.18rem 0.55rem; border-radius: 6px;
  font-size: 0.7rem; font-weight: 700; text-transform: capitalize;
  white-space: nowrap;
}
.type-praise { background: rgba(39,174,96,0.12); color: #27ae60; }
.type-complaint { background: rgba(231,76,60,0.12); color: #e74c3c; }
.type-enquiry { background: rgba(52,152,219,0.12); color: #2980b9; }
.type-suggestion { background: rgba(155,89,182,0.12); color: #8e44ad; }
.type-feedback { background: rgba(243,156,18,0.12); color: #e67e22; }

.tag-badge {
  display: inline-block; padding: 0.18rem 0.55rem; border-radius: 6px;
  font-size: 0.7rem; font-weight: 600; white-space: nowrap;
}
.tag-pos { background: rgba(39,174,96,0.1); color: #219a52; }
.tag-neg { background: rgba(231,76,60,0.1); color: #c0392b; }
.tag-neu { background: rgba(108,117,125,0.1); color: #6c757d; }
</style>
