<template>
  <div class="critique">
    <!-- Gradient Banner -->
    <div class="critique-banner">
      <div class="cb-left">
        <div class="cb-icon">
          <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>
        </div>
        <div>
          <h2>Critique &amp; Improvements</h2>
          <p>AI-powered feedback analysis from customer conversations</p>
        </div>
      </div>
      <div class="cb-right">
        <div class="cb-stat">
          <span class="cb-val">{{ items.length }}</span>
          <span class="cb-lbl">Total Items</span>
        </div>
        <div class="cb-stat cb-stat-red">
          <span class="cb-val">{{ complaintCount }}</span>
          <span class="cb-lbl">Complaints</span>
        </div>
        <div class="cb-stat cb-stat-blue">
          <span class="cb-val">{{ suggestionCount }}</span>
          <span class="cb-lbl">Suggestions</span>
        </div>
        <div class="cb-stat cb-stat-purple">
          <span class="cb-val">{{ enquiryCount }}</span>
          <span class="cb-lbl">Enquiries</span>
        </div>
        <div class="cb-stat cb-stat-amber">
          <span class="cb-val">{{ happyCount }}</span>
          <span class="cb-lbl">Praise</span>
        </div>
        <div class="cb-stat cb-stat-teal">
          <span class="cb-val">{{ improvementCount }}</span>
          <span class="cb-lbl">Improvements</span>
        </div>
      </div>
    </div>

    <div class="critique-controls">
      <div class="filters">
        <select v-model="filterType" @change="loadData">
          <option value="">All Types</option>
          <option value="suggestion">Suggestions</option>
          <option value="complaint">Complaints</option>
          <option value="enquiry">Enquiries</option>
          <option value="improvement">Improvements</option>
          <option value="disappointed">Disappointed</option>
          <option value="happy">Praise / Happy</option>
        </select>
        <select v-model="filterCid" @change="loadData">
          <option value="">All Customers</option>
          <option v-for="c in customerList" :key="c.cid" :value="c.cid">{{ c.name || c.cid }}</option>
        </select>
      </div>
    </div>

    <div v-if="loading" class="skel-table">
      <div class="skel-row" v-for="i in 5" :key="i"></div>
    </div>

    <div v-else-if="items.length === 0" class="empty">
      <p>No critiques or suggestions found. Upload and process some calls to see feedback.</p>
    </div>

    <div v-else class="table-wrap">
      <table>
        <thead>
          <tr><th>Date</th><th>Customer</th><th>Type</th><th>Topic</th><th>Feedback</th></tr>
        </thead>
        <tbody>
          <tr v-for="item in items" :key="item._id">
            <td class="td-date">{{ item.processed_at ? new Date(item.processed_at).toLocaleDateString() : '—' }}</td>
            <td class="td-cust">{{ item.cid }}</td>
            <td><span class="type-badge" :class="item.type">{{ item.type }}</span></td>
            <td><span class="topic-tag" :class="item.type">{{ item.topic }}</span></td>
            <td class="td-text">{{ item.text }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'

const items = ref([])
const loading = ref(true)
const filterType = ref('')
const filterCid = ref('')
const customerList = ref([])

const complaintCount = computed(() => items.value.filter(i => i.type === 'complaint' || i.type === 'disappointed').length)
const suggestionCount = computed(() => items.value.filter(i => i.type === 'suggestion' || i.type === 'improvement').length)
const enquiryCount = computed(() => items.value.filter(i => i.type === 'enquiry').length)
const happyCount = computed(() => items.value.filter(i => i.type === 'happy').length)
const improvementCount = computed(() => items.value.filter(i => i.type === 'improvement').length)

async function loadData() {
  loading.value = true
  const params = { limit: 100 }
  if (filterType.value) params.type = filterType.value
  if (filterCid.value) params.cid = filterCid.value
  const { data } = await axios.get('/api/mongo/critiques', { params })
  items.value = data
  loading.value = false
}

onMounted(async () => {
  await loadData()
  try {
    const { data } = await axios.get('/api/mongo/customers')
    customerList.value = data
  } catch {}
})
</script>

<style scoped>
.critique {
  display: flex; flex-direction: column; gap: 1.5rem;
  padding: 1rem 1.5rem; min-height: 100vh; width: 100%;
  background: #fff;
}

/* === Gradient Banner === */
.critique-banner {
  background: linear-gradient(135deg, #e74c3c 0%, #f39c12 50%, #e67e22 100%);
  margin: -1rem -1.5rem 0 -1.5rem; padding: 1.4rem 1.8rem;
  display: flex; justify-content: space-between; align-items: center;
  box-shadow: 0 4px 20px rgba(231,76,60,0.18);
  border-radius: 0;
}
.cb-left { display: flex; align-items: center; gap: 1rem; }
.cb-icon {
  width: 48px; height: 48px; border-radius: 50%;
  background: rgba(255,255,255,0.18); color: #fff;
  display: flex; align-items: center; justify-content: center;
}
.cb-left h2 { font-size: 1.15rem; font-weight: 700; color: #fff; line-height: 1.3; margin: 0; padding: 0; border: none; }
.cb-left p { font-size: 0.78rem; color: rgba(255,255,255,0.8); margin-top: 0.15rem; }
.cb-right { display: flex; gap: 1.6rem; }
.cb-stat { text-align: center; }
.cb-val { font-size: 1.3rem; font-weight: 700; color: #fff; display: block; }
.cb-lbl { font-size: 0.68rem; color: rgba(255,255,255,0.7); text-transform: uppercase; letter-spacing: 0.04em; }
.cb-stat-red .cb-val { color: #ffcccc; }
.cb-stat-blue .cb-val { color: #cce5ff; }
.cb-stat-amber .cb-val { color: #ffe0b2; }
.cb-stat-purple .cb-val { color: #e0c8ff; }
.cb-stat-teal .cb-val { color: #b2f0e8; }

.critique-controls { display: flex; justify-content: flex-end; }
.filters { display: flex; gap: 0.6rem; }
.filters select {
  padding: 0.45rem 0.85rem; border: 1px solid #e0e3e8; border-radius: 6px;
  font-size: 0.83rem; background: #fafcfd; color: #495057; cursor: pointer;
}

.empty {
  text-align: center; padding: 4rem 2rem;
  background: linear-gradient(135deg, #fafcfd 0%, #f3f6f9 100%);
  border-radius: 10px; border: 2px dashed #d4dce4;
  color: #8d96a0; font-size: 0.9rem;
  box-shadow: 0 2px 10px rgba(0,0,0,0.04);
}

.skel-table { display: flex; flex-direction: column; gap: 0.5rem; }
.skel-row {
  height: 44px; border-radius: 8px;
  background: linear-gradient(90deg, #f1f3f5 25%, #e9ecef 50%, #f1f3f5 75%);
  background-size: 200% 100%; animation: shimmer 1.5s infinite;
}
@keyframes shimmer { 0% { background-position: 200% 0; } 100% { background-position: -200% 0; } }

.table-wrap {
  background: #fafcfd; border-radius: 10px; padding: 1.3rem;
  box-shadow: 0 2px 10px rgba(0,0,0,0.04); border: 1px solid #eef0f2; overflow-x: auto;
  position: relative; overflow: hidden;
}
.table-wrap::before {
  content: ''; position: absolute;
  width: 100px; height: 100px; border-radius: 50%;
  top: -30px; right: -25px; opacity: 0.1; pointer-events: none;
  background: #e74c3c;
}
.table-wrap::after {
  content: ''; position: absolute;
  width: 55px; height: 55px; border-radius: 50%;
  bottom: -15px; left: 60px; opacity: 0.08; pointer-events: none;
  background: #f39c12;
}
table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
th {
  text-align: left; padding: 0.7rem 0.9rem; font-weight: 600; color: #6c757d;
  font-size: 0.76rem; text-transform: uppercase; letter-spacing: 0.04em;
  background: linear-gradient(180deg, #f3f6f9 0%, #eef1f5 100%);
  border-bottom: 2px solid #dce2e8;
}
td { padding: 0.7rem 0.9rem; border-bottom: 1px solid #f0f2f5; vertical-align: top; color: #495057; }
tr:last-child td { border-bottom: none; }
tr:hover td { background: linear-gradient(135deg, #f5f7fa 0%, #eef1f5 100%); }
.td-date { white-space: nowrap; color: #8d96a0; font-size: 0.82rem; font-weight: 500; }
.td-cust { font-weight: 600; color: #2c3e50; white-space: nowrap; }
.td-text { max-width: 420px; line-height: 1.55; color: #495057; }

.type-badge {
  display: inline-block; padding: 0.22rem 0.7rem; border-radius: 10px;
  font-size: 0.72rem; font-weight: 700; text-transform: capitalize; letter-spacing: 0.02em;
}
.type-badge.suggestion { background: linear-gradient(135deg, #3498db, #5dade2); color: #fff; box-shadow: 0 2px 6px rgba(52,152,219,0.25); }
.type-badge.complaint { background: linear-gradient(135deg, #e74c3c, #f1948a); color: #fff; box-shadow: 0 2px 6px rgba(231,76,60,0.25); }
.type-badge.enquiry { background: linear-gradient(135deg, #8e44ad, #bb8fce); color: #fff; box-shadow: 0 2px 6px rgba(142,68,173,0.25); }
.type-badge.improvement { background: linear-gradient(135deg, #16a085, #48c9b0); color: #fff; box-shadow: 0 2px 6px rgba(22,160,133,0.25); }
.type-badge.disappointed { background: linear-gradient(135deg, #e67e22, #f0b27a); color: #fff; box-shadow: 0 2px 6px rgba(230,126,34,0.25); }
.type-badge.happy { background: linear-gradient(135deg, #f39c12, #f9cb6c); color: #fff; box-shadow: 0 2px 6px rgba(243,156,18,0.25); }

.topic-tag {
  display: inline-block; padding: 0.18rem 0.6rem;
  border-radius: 8px; font-size: 0.74rem; font-weight: 600;
}
.topic-tag.complaint { background: rgba(231,76,60,0.1); color: #c0392b; }
.topic-tag.suggestion { background: rgba(52,152,219,0.1); color: #2471a3; }
.topic-tag.enquiry { background: rgba(142,68,173,0.1); color: #7d3c98; }
.topic-tag.improvement { background: rgba(22,160,133,0.1); color: #0e6655; }
.topic-tag.disappointed { background: rgba(230,126,34,0.1); color: #b35900; }
.topic-tag.happy { background: rgba(243,156,18,0.1); color: #d68910; }
</style>
