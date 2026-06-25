<template>
  <div class="upload-page">
    <!-- Gradient Banner -->
    <div class="upload-banner">
      <div class="ub-left">
        <div class="ub-icon">
          <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
        </div>
        <div>
          <h2>Upload Recordings</h2>
          <p>Analyze customer voice sentiment across 6 Indian languages</p>
        </div>
      </div>
      <div class="ub-right">
        <div class="ub-stat">
          <span class="ub-val">{{ store.totalFiles }}</span>
          <span class="ub-lbl">Files Queued</span>
        </div>
        <div class="ub-stat">
          <span class="ub-val">{{ store.customers.length }}</span>
          <span class="ub-lbl">Customers</span>
        </div>
        <div class="ub-stat ub-stat-green">
          <span class="ub-val">{{ successCount }}</span>
          <span class="ub-lbl">Processed</span>
        </div>
      </div>
    </div>

    <!-- Step Indicator -->
    <div class="steps-banner">
      <div class="step active">
        <div class="step-num">1</div>
        <span>Add Customer</span>
      </div>
      <div class="step-connector"></div>
      <div class="step" :class="{ active: store.totalFiles > 0 }">
        <div class="step-num">2</div>
        <span>Upload Files</span>
      </div>
      <div class="step-connector"></div>
      <div class="step" :class="{ active: successCount > 0 }">
        <div class="step-num">3</div>
        <span>Process &amp; Review</span>
      </div>
    </div>

    <div class="toolbar">
      <label>Default Language
        <select v-model="globalLang">
          <option value="en">English</option>
          <option value="hi">Hindi</option>
          <option value="te">Telugu</option>
          <option value="ta">Tamil</option>
          <option value="kn">Kannada</option>
          <option value="ml">Malayalam</option>
          <option value="bn">Bengali</option>
          <option value="pa">Punjabi</option>
        </select>
      </label>
      <span class="file-limit" :class="{ warn: store.totalFiles >= 4 }">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/></svg>
        {{ store.totalFiles }}/1 file
      </span>
      <button class="add-cust-btn" @click="addNewCust">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
        Add Customer
      </button>
      <button class="process-btn" @click="processAll" :disabled="store.processing || store.pendingFiles === 0">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 3 19 12 5 21 5 3"/></svg>
        {{ store.processing ? 'Processing...' : 'Process (' + store.pendingFiles + ' file' + (store.pendingFiles !== 1 ? 's' : '') + ')' }}
      </button>
    </div>

    <div v-if="!store.customers.length" class="empty-hero">
      <div class="empty-icon">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
      </div>
      <h3>Ready to Analyze Customer Sentiment?</h3>
      <p>Click <strong>Add Customer</strong> above, enter their details, then drop audio files to begin analysis.</p>
      <p class="hero-hint">Supports English, Hindi, Telugu, Tamil, Kannada, Malayalam, Bengali & Punjabi</p>
    </div>

    <!-- Customer Cards -->
    <div v-for="(cust, ci) in store.customers" :key="cust.id" class="cust-card">
      <div class="cust-header">
        <div class="cust-info">
          <input class="cust-input" v-model="cust.cid" placeholder="Customer ID (e.g. CUST001)" :disabled="cust.uploading" />
          <input class="cust-input name-input" v-model="cust.name" placeholder="Name (optional)" :disabled="cust.uploading" />
          <label class="cust-lang">Language
            <select v-model="cust.lang">
              <option value="en">English</option><option value="hi">Hindi</option>
              <option value="te">Telugu</option><option value="ta">Tamil</option>
              <option value="kn">Kannada</option><option value="ml">Malayalam</option>
            </select>
          </label>
          <span class="file-count">{{ cust.files.length }} file{{ cust.files.length !== 1 ? 's' : '' }}</span>
        </div>
        <button class="rm-cust" @click="store.removeCustomer(ci)" :disabled="cust.uploading">&times;</button>
      </div>

      <!-- Drop Zone -->
      <div class="drop-inner" :class="{ active: cust.dragging, disabled: !cust.cid && !cust.name }"
           @dragover.prevent="cust.dragging = true" @dragleave="cust.dragging = false"
           @drop.prevent="dropFiles($event, ci)" @click="tryOpenPicker(ci)">
        <p v-if="!cust.cid && !cust.name">Enter Customer ID or Name to enable file upload</p>
        <p v-else-if="!cust.files.length">Drop audio files here or click to add (max {{ 5 - store.totalFiles }} remaining)</p>
        <p v-else>Drop more or click to add ({{ 5 - store.totalFiles }} remaining)</p>
        <input type="file" :ref="el => { if(el) store.custInputs[ci] = el }" accept=".wav,.mp3,.m4a,.ogg"
               multiple @change="pickFiles($event, ci)" @click.stop hidden :disabled="!cust.cid && !cust.name" />
      </div>

      <!-- File Table -->
      <table v-if="cust.files.length" class="rec-table">
        <thead><tr><th>#</th><th>File</th><th>Duration</th><th>Language</th><th>Date/Time</th><th>Progress</th><th>Status</th><th></th></tr></thead>
        <tbody>
          <tr v-for="(f, fi) in cust.files" :key="f.uid">
            <td>{{ fi + 1 }}</td>
            <td class="fname" :title="f.name">{{ f.name }}</td>
            <td class="dur-cell">{{ f.duration ? fmtDuration(f.duration) : '—' }}</td>
            <td><select v-model="f.lang" :disabled="f.progress > 0">
              <option value="en">English</option><option value="hi">Hindi</option>
              <option value="te">Telugu</option><option value="ta">Tamil</option>
            </select></td>
            <td class="date-cell">
              <input type="date" v-model="f.callDate" class="date-inp" :disabled="f.progress > 0" />
              <input type="time" v-model="f.callTime" class="time-inp" :disabled="f.progress > 0" />
            </td>
            <td class="bar-cell">
              <div class="bar-track"><div class="bar-fill" :class="f.status" :style="{ width: f.progress + '%' }"></div></div>
              <span class="pct">{{ f.progress }}%</span>
            </td>
            <td><span class="badge" :class="f.status">{{ label(f) }}</span></td>
            <td><button v-if="f.progress === 0" class="rm" @click="store.removeFile(ci, fi)">&times;</button></td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Results Section (appears after all done) -->
    <div v-if="store.allDone && store.totalFiles > 0" class="results-section">
      <h2>Analysis Results</h2>
      <div v-for="(cust, ci) in store.customers" :key="'r'+cust.id" class="result-cust">
        <h3 v-if="cust.name">{{ cust.name }} ({{ cust.cid }})</h3>
        <h3 v-else>{{ cust.cid }}</h3>
        <div v-for="(f, fi) in cust.files.filter(x => x.status === 'SUCCESS')" :key="'f'+f.uid" class="result-card">
          <div class="result-header" @click="toggleExpand(f.uid)">
            <div class="result-summary">
              <span class="r-file">{{ f.name }}</span>
              <Tag :tag="f.resultTag || 'N/A'" />
              <span class="r-score">Confidence: {{ f.resultScore }}</span>
              <span class="r-dur">{{ fmtDuration(f.duration) }}</span>
              <span v-if="sanitizeName(f.resultCustomer)" class="r-cust">{{ sanitizeName(f.resultCustomer) }}</span>
            </div>
            <span class="expand-icon">{{ expanded[f.uid] ? '▾' : '▸' }}</span>
          </div>

          <!-- Expanded Details -->
          <div v-if="expanded[f.uid]" class="result-expand">
            <!-- Speaker conversation -->
            <div class="conv-blocks">
              <h4>Conversation</h4>
              <div v-for="(block, bi) in f.speakerBlocks" :key="bi" class="conv-block" :class="block.role">
                <span class="cb-speaker">{{ block.role === 'agent' ? 'Agent' : (sanitizeName(f.resultCustomer) || 'Customer') }}</span>
                <p>{{ block.text }}</p>
              </div>
              <p v-if="!f.speakerBlocks?.length" class="no-data">Transcript unavailable</p>
            </div>

            <!-- Stats -->
            <div class="result-stats">
              <div class="stat"><span>Sentiment</span><strong>{{ f.resultTag || 'N/A' }}</strong></div>
              <div class="stat"><span>Score</span><strong>{{ f.resultScore }}</strong></div>
              <div class="stat"><span>Duration</span><strong>{{ fmtDuration(f.duration) }}</strong></div>
              <div class="stat"><span>Speakers</span><strong>{{ f.speakerCount || '—' }}</strong></div>
              <div class="stat" v-if="f.callDate"><span>Date</span><strong>{{ f.callDate }} {{ f.callTime }}</strong></div>
            </div>

            <!-- Topics & Shift -->
            <div v-if="f.resultTopics?.length" class="result-meta">
              <span class="meta-label">Topics:</span> {{ f.resultTopics.join(', ') }}
            </div>
            <div v-if="f.resultShift" class="result-meta">
              <span class="meta-label">Sentiment Shift:</span> {{ f.resultShift }}
            </div>
            <div v-if="f.resultSummary" class="result-meta">
              <span class="meta-label">Summary:</span> {{ f.resultSummary }}
            </div>

            <!-- File path -->
            <div class="result-path">
              See detailed results: <code>voicepulse\results\{{ f.name.replace('.mp3','').replace('.wav','') }}_summary.json</code>
              &amp; <code>..._transcript.json</code>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import { useUploadStore } from '../stores/upload.js'
import Tag from '../components/Tag.vue'

const store = useUploadStore()
const globalLang = ref('en')
const expanded = ref({})

const successCount = computed(() => {
  return store.customers.flatMap(c => c.files).filter(f => f.status === 'SUCCESS').length
})

const STAGE_PCT = {
  PENDING: 5, STARTED: 15, TRANSCRIBING: 35, ALIGNING: 50,
  DIARIZING: 65, CLASSIFYING: 80, BRIEFING: 92, SUCCESS: 100, FAILURE: 0
}

function addNewCust() {
  store.addCustomer()
}

function fmtDuration(sec) {
  if (!sec || sec <= 0) return '—'
  const m = Math.floor(sec / 60)
  const s = Math.round(sec % 60)
  return m > 0 ? `${m}m ${s}s` : `${s}s`
}

function toggleExpand(uid) {
  expanded.value[uid] = !expanded.value[uid]
}

// Frontend backup: if backend returns a non-name word, fallback to 'Customer'
const _NAME_BLACKLIST = new Set([
  'trying','to','the','and','for','you','can','this','that',
  'what','with','have','from','your','just','like','will',
  'okay','hello','yeah','right','well','actually','please',
  'thank','thanks','sorry','about','they','there','their',
  'speaking','calling','would','could','should','need','want',
  'going','been','here','was','how','when','where','why',
])
function sanitizeName(name) {
  if (!name || name.length < 2) return ''
  if (_NAME_BLACKLIST.has(name.toLowerCase())) return ''
  return name
}

function label(f) {
  if (!f.status) return 'Queued'
  if (f.status === 'SUCCESS') return 'Done'
  if (f.status === 'FAILURE') return 'Failed'
  return f.status.charAt(0) + f.status.slice(1).toLowerCase()
}

function openPicker(ci) {
  const el = store.custInputs[ci]
  if (el) { el.value = ''; el.click() }
}

function tryOpenPicker(ci) {
  const cust = store.customers[ci]
  if (!cust.cid && !cust.name) return
  openPicker(ci)
}

function dropFiles(e, ci) {
  store.customers[ci].dragging = false
  const cust = store.customers[ci]
  if (!cust.cid && !cust.name) return
  store.addFilesToCustomer(ci, e.dataTransfer.files)
}

async function pickFiles(e, ci) {
  const files = e.target.files
  if (!files.length) return

  // Estimate duration from file size (rough ~1MB per 60s for MP3)
  for (const f of files) {
    f._estDuration = Math.round((f.size / (1024 * 1024)) * 60)
  }

  store.addFilesToCustomer(ci, files)
  e.target.value = ''
}

async function processAll() {
  store.setProcessing(true)
  for (let ci = 0; ci < store.customers.length; ci++) {
    const cust = store.customers[ci]
    if (!cust.cid) cust.cid = 'CUST' + String(cust.id).padStart(3, '0')
    cust.uploading = true
    for (let fi = 0; fi < cust.files.length; fi++) {
      const f = cust.files[fi]
      if (f.status === 'SUCCESS') continue
      const form = new FormData()
      form.append('file', f.file)
      form.append('cid', cust.cid)
      form.append('lang', f.lang)
      if (f.callDate) form.append('call_date', f.callDate)
      if (f.callTime) form.append('call_time', f.callTime)
      try {
        const { data } = await axios.post('/api/voice/upload', form)
        f.jobId = data.job_id
        f.status = 'PENDING'
        f.progress = 5
        poll(ci, fi)
      } catch (e) {
        f.status = 'FAILURE'
        f.progress = 0
        window._toast?.('error', `Failed to upload ${f.name}`)
      }
    }
  }
}

function poll(ci, fi) {
  const check = async () => {
    const f = store.customers[ci]?.files[fi]
    if (!f || !f.jobId) return
    try {
      const { data } = await axios.get('/api/voice/status/' + f.jobId)
      f.status = data.status
      const stage = (data.meta || {}).stage || data.status
      f.progress = STAGE_PCT[stage] ?? f.progress
      if (data.status === 'SUCCESS') {
        f.progress = 100
        // Fetch full result
        try {
          const r = await axios.get('/api/voice/result/' + f.jobId)
          const d = r.data
          f.resultTag = d.tag
          f.resultScore = d.score
          f.duration = d.duration || (f.file?._estDuration || 0)
          f.resultCustomer = d.customer_name || ''
          f.resultTopics = d.topics || []
          f.resultShift = d.shift || ''
          f.resultSummary = d.summary || ''
          f.speakerBlocks = d.speaker_blocks || []
          f.speakerCount = d.speaker_count || 0
        } catch (e) { /* result fetch can fail, still mark done */ }
        checkAllDone()
        return
      }
      if (data.status === 'FAILURE') { f.progress = 0; checkAllDone(); return }
    } catch (e) { /* network errors */ }
    setTimeout(check, 2000)
  }
  check()
}

function checkAllDone() {
  const allFiles = store.customers.flatMap(c => c.files)
  const pending = allFiles.filter(f => f.status !== 'SUCCESS' && f.status !== 'FAILURE')
  if (pending.length === 0) {
    store.setProcessing(false)
    store.customers.forEach(c => { c.uploading = false; c.completed = true })
    window._toast?.('success', 'All files processed!')
  }
}

onMounted(() => {
  store.loadCompletedFiles()
})
</script>

<style scoped>
.upload-page {
  padding: 1rem 1.5rem; min-height: 100vh; width: 100%;
  background: #fff;
}
h3 { font-size: 0.95rem; margin-bottom: 0.8rem; font-weight: 600; color: #495057; }
h4 { font-size: 0.88rem; margin-bottom: 0.5rem; color: #495057; font-weight: 600; }

/* === Gradient Banner === */
.upload-banner {
  background: linear-gradient(135deg, #f1c40f 0%, #f39c12 40%, #e74c3c 100%);
  margin: -1rem -1.5rem 1.2rem -1.5rem; padding: 1.4rem 1.8rem;
  display: flex; justify-content: space-between; align-items: center;
  box-shadow: 0 4px 20px rgba(231,76,60,0.2);
  border-radius: 0;
}
.ub-left { display: flex; align-items: center; gap: 1rem; }
.ub-icon {
  width: 48px; height: 48px; border-radius: 50%;
  background: rgba(255,255,255,0.18); color: #fff;
  display: flex; align-items: center; justify-content: center;
}
.ub-left h2 { font-size: 1.15rem; font-weight: 700; color: #fff; line-height: 1.3; margin: 0; padding: 0; border: none; }
.ub-left p { font-size: 0.78rem; color: rgba(255,255,255,0.8); margin-top: 0.15rem; }
.ub-right { display: flex; gap: 1.6rem; }
.ub-stat { text-align: center; }
.ub-val { font-size: 1.3rem; font-weight: 700; color: #fff; display: block; }
.ub-lbl { font-size: 0.68rem; color: rgba(255,255,255,0.7); text-transform: uppercase; letter-spacing: 0.04em; }
.ub-stat-green .ub-val { color: #ffeaa7; }

/* === Steps Banner === */
.steps-banner {
  background: linear-gradient(135deg, #fafcfd 0%, #f3f6f9 100%);
  border-radius: 10px; padding: 1rem 1.8rem; margin-bottom: 1.2rem;
  display: flex; align-items: center; justify-content: center; gap: 0;
  box-shadow: 0 2px 10px rgba(0,0,0,0.04); border: 1px solid #eef0f2;
}
.step { display: flex; align-items: center; gap: 0.55rem; opacity: 0.45; transition: opacity 0.3s; }
.step.active { opacity: 1; }
.step-num {
  width: 32px; height: 32px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 0.78rem; font-weight: 700; color: #7f8c8d;
  background: #eef0f2; transition: all 0.3s;
}
.step.active .step-num {
  background: linear-gradient(135deg, #f1c40f, #e74c3c);
  color: #fff; box-shadow: 0 2px 8px rgba(231,76,60,0.3);
}
.step span { font-size: 0.82rem; font-weight: 500; color: #7f8c8d; }
.step.active span { color: #2c3e50; font-weight: 600; }
.step-connector { flex: 0 0 60px; height: 2px; background: #e0e3e8; margin: 0 0.8rem; }

/* === Toolbar === */
.toolbar { display: flex; gap: 1rem; margin-bottom: 1.5rem; align-items: center; flex-wrap: wrap; }
.toolbar label { display: flex; gap: 0.5rem; align-items: center; font-size: 0.86rem; font-weight: 500; color: #495057; }
.toolbar select { padding: 0.5rem 0.8rem; border: 1px solid #e0e3e8; border-radius: 6px; font-size: 0.84rem; background: #fafcfd; color: #495057; }
.file-limit { font-size: 0.82rem; font-weight: 600; color: #6c757d; padding: 0.4rem 0.8rem; background: linear-gradient(135deg, #f8f9fb, #f3f5f8); border-radius: 8px; display: flex; align-items: center; gap: 0.35rem; }
.file-limit.warn { background: linear-gradient(135deg, #fff9e6, #fff3cd); color: #856404; }
.add-cust-btn {
  padding: 0.5rem 1.2rem; background: linear-gradient(135deg, #f1c40f, #e74c3c);
  color: #fff; border: none; border-radius: 8px; cursor: pointer;
  font-weight: 600; font-size: 0.86rem; transition: all 0.2s;
  display: flex; align-items: center; gap: 0.35rem;
  box-shadow: 0 2px 8px rgba(231,76,60,0.25);
}
.add-cust-btn:hover { background: linear-gradient(135deg, #f39c12, #c0392b); box-shadow: 0 4px 14px rgba(231,76,60,0.4); transform: translateY(-1px); }
.process-btn {
  margin-left: auto; padding: 0.55rem 1.5rem;
  background: linear-gradient(135deg, #f39c12, #e74c3c);
  color: #fff; border: none; border-radius: 8px; cursor: pointer;
  font-weight: 600; font-size: 0.86rem; transition: all 0.2s;
  display: flex; align-items: center; gap: 0.35rem;
  box-shadow: 0 2px 8px rgba(231,76,60,0.25);
}
.process-btn:hover:not(:disabled) { background: linear-gradient(135deg, #e67e22, #c0392b); box-shadow: 0 4px 14px rgba(231,76,60,0.4); transform: translateY(-1px); }
.process-btn:disabled { opacity: 0.5; cursor: not-allowed; transform: none; box-shadow: none; }

/* === Empty Hero === */
.empty-hero {
  text-align: center; padding: 3.5rem 2rem;
  background: linear-gradient(135deg, #fafcfd 0%, #f3f6f9 100%);
  border-radius: 12px; border: 2px dashed #d4dce4; color: #8d96a0;
}
.empty-icon { margin-bottom: 1rem; color: #adb5bd; }
.empty-hero h3 { font-size: 1.1rem; color: #2c3e50; margin-bottom: 0.5rem; }
.empty-hero p { margin-bottom: 0.4rem; font-size: 0.88rem; }
.hero-hint { font-size: 0.78rem; color: #b0b8c1; margin-top: 0.4rem; }

/* === Customer Cards === */
.cust-card {
  background: #fafcfd; border-radius: 10px; margin-bottom: 1.5rem;
  box-shadow: 0 2px 10px rgba(0,0,0,0.04); border: 1px solid #eef0f2; overflow: hidden;
  position: relative;
}
.cust-card::before {
  content: ''; position: absolute;
  width: 100px; height: 100px; border-radius: 50%;
  top: -35px; right: -25px; opacity: 0.1; pointer-events: none; z-index: 0;
  background: #27ae60;
}
.cust-card::after {
  content: ''; position: absolute;
  width: 50px; height: 50px; border-radius: 50%;
  bottom: -12px; left: 55px; opacity: 0.08; pointer-events: none; z-index: 0;
  background: #1abc9c;
}
.cust-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 0.9rem 1.3rem;
  background: linear-gradient(135deg, #f0faf4 0%, #eaf6f0 100%);
  border-bottom: 1px solid #d4e8dc;
}
.cust-info { display: flex; gap: 0.8rem; align-items: center; flex-wrap: wrap; }
.cust-input { padding: 0.5rem 0.8rem; border: 1px solid #e0e3e8; border-radius: 6px; font-size: 0.86rem; width: 180px; color: #2c3e50; background: #fff; }
.cust-input:disabled { background: #f3f5f8; color: #adb5bd; }
.cust-input:focus { outline: none; border-color: #27ae60; box-shadow: 0 0 0 3px rgba(39,174,96,0.1); }
.name-input { width: 150px; }
.cust-lang { display: flex; gap: 0.4rem; align-items: center; font-size: 0.84rem; color: #6c757d; }
.cust-lang select { padding: 0.45rem 0.7rem; border: 1px solid #e0e3e8; border-radius: 6px; font-size: 0.82rem; background: #fff; }
.file-count { font-size: 0.78rem; color: #6c757d; font-weight: 500; background: linear-gradient(135deg, #eef0f4, #e4e8ed); padding: 0.2rem 0.6rem; border-radius: 8px; }
.rm-cust { background: none; border: none; color: #adb5bd; font-size: 1.4rem; cursor: pointer; padding: 0 0.4rem; transition: color 0.15s; }
.rm-cust:hover { color: #e74c3c; }
.rm-cust:disabled { opacity: 0.3; cursor: not-allowed; }

/* === Drop Zone === */
.drop-inner {
  border: 2px dashed #c8d6e5; margin: 0.8rem 1.3rem; border-radius: 10px;
  padding: 2rem; text-align: center; cursor: pointer; transition: all 0.25s;
  background: linear-gradient(135deg, #f8fafb 0%, #f0f4f7 100%);
}
.drop-inner:hover, .drop-inner.active {
  border-color: #27ae60;
  background: linear-gradient(135deg, #f0faf4 0%, #e5f5ec 100%);
  box-shadow: inset 0 0 0 2px rgba(39,174,96,0.08);
}
.drop-inner.disabled { opacity: 0.45; cursor: not-allowed; background: #f8f9fa; border-color: #e0e3e8; }
.drop-inner.disabled:hover { border-color: #e0e3e8; background: #f8f9fa; box-shadow: none; }
.drop-inner p { color: #8d96a0; font-size: 0.86rem; margin: 0; }
.drop-inner.disabled p { color: #b0b8c1; }

/* === Table === */
.rec-table { width: 100%; border-collapse: collapse; font-size: 0.83rem; }
.rec-table thead { background: linear-gradient(135deg, #f3f6f9 0%, #eef1f5 100%); }
.rec-table th {
  text-align: left; padding: 0.6rem 0.7rem; font-weight: 600; color: #6c757d;
  border-bottom: 2px solid #dce2e8; font-size: 0.76rem; text-transform: uppercase; letter-spacing: 0.03em;
}
.rec-table td { padding: 0.55rem 0.7rem; border-bottom: 1px solid #f0f2f5; vertical-align: middle; color: #495057; }
.fname { max-width: 180px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-weight: 500; }
.dur-cell { font-size: 0.8rem; color: #adb5bd; }
.date-cell { display: flex; gap: 0.4rem; }
.date-inp, .time-inp { padding: 0.35rem 0.5rem; border: 1px solid #e0e3e8; border-radius: 4px; font-size: 0.76rem; width: 105px; }
.date-inp:disabled, .time-inp:disabled { background: #f3f5f8; }
.rec-table select { padding: 0.35rem 0.5rem; border: 1px solid #e0e3e8; border-radius: 4px; font-size: 0.78rem; }
.rec-table select:disabled { background: #f3f5f8; }

/* === Progress Bars === */
.bar-cell { display: flex; align-items: center; gap: 0.5rem; min-width: 130px; }
.bar-track { flex: 1; height: 8px; background: #e8ecf0; border-radius: 5px; overflow: hidden; }
.bar-fill { height: 100%; border-radius: 5px; transition: width 0.4s ease; background: linear-gradient(90deg, #27ae60, #2ecc71); }
.bar-fill.SUCCESS { background: linear-gradient(90deg, #27ae60, #1abc9c); }
.bar-fill.FAILURE { background: linear-gradient(90deg, #e74c3c, #c0392b); }
.pct { font-size: 0.72rem; font-weight: 600; min-width: 28px; text-align: right; color: #6c757d; }

/* === Badges === */
.badge { display: inline-block; padding: 0.2rem 0.6rem; border-radius: 8px; font-size: 0.72rem; font-weight: 600; background: #f3f5f8; color: #6c757d; }
.badge.SUCCESS { background: rgba(39,174,96,0.12); color: #27ae60; }
.badge.FAILURE { background: rgba(231,76,60,0.12); color: #e74c3c; }
.badge.PENDING { background: linear-gradient(135deg, #fff9e6, #fff3cd); color: #856404; }
.badge.TRANSCRIBING, .badge.CLASSIFYING, .badge.BRIEFING { background: rgba(52,152,219,0.12); color: #2980b9; }
.rm { background: none; border: none; color: #adb5bd; font-size: 1.1rem; cursor: pointer; padding: 0 0.3rem; }
.rm:hover { color: #e74c3c; }

/* === Results Section === */
.results-section { margin-top: 2rem; }
.results-section h2 {
  background: linear-gradient(135deg, #eafaf1 0%, #d4efdf 100%);
  padding: 0.6rem 1.2rem; border-radius: 8px; color: #1e8449;
  border-top: none; margin-top: 0; font-size: 1rem;
}
.result-cust { margin-bottom: 1rem; }
.result-card {
  background: #fafcfd; border-radius: 10px; margin-bottom: 0.6rem;
  box-shadow: 0 2px 10px rgba(0,0,0,0.04); border: 1px solid #eef0f2; overflow: hidden;
}
.result-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 0.9rem 1.3rem; cursor: pointer; transition: background 0.15s;
}
.result-header:hover { background: linear-gradient(135deg, #f5f7fa, #f0f3f6); }
.result-summary { display: flex; gap: 1rem; align-items: center; flex-wrap: wrap; }
.r-file { font-weight: 600; font-size: 0.9rem; color: #2c3e50; }
.r-score { font-size: 0.82rem; color: #6c757d; }
.r-dur { font-size: 0.8rem; color: #adb5bd; }
.r-cust { font-size: 0.82rem; color: #27ae60; font-weight: 500; }
.expand-icon { font-size: 1.2rem; color: #adb5bd; }

.result-expand { padding: 0 1.3rem 1.2rem; border-top: 1px solid #eef0f2; }

.conv-blocks { margin-bottom: 1rem; }
.conv-block { padding: 0.6rem 0.9rem; border-radius: 8px; margin-bottom: 0.35rem; }
.conv-block.agent { background: linear-gradient(135deg, #eef6fc 0%, #e3f0f8 100%); border-left: 3px solid #3498db; }
.conv-block.customer { background: linear-gradient(135deg, #fef8f2 0%, #fdf0e2 100%); border-left: 3px solid #f39c12; }
.cb-speaker { font-weight: 600; font-size: 0.78rem; color: #6c757d; display: block; margin-bottom: 0.2rem; }
.conv-block p { font-size: 0.84rem; line-height: 1.55; color: #495057; }
.no-data { color: #adb5bd; font-size: 0.85rem; font-style: italic; }

.result-stats { display: flex; gap: 1.5rem; flex-wrap: wrap; margin-bottom: 0.8rem; }
.stat { display: flex; flex-direction: column; padding: 0.4rem 0.8rem; background: linear-gradient(135deg, #f5f7fa, #eef1f5); border-radius: 6px; }
.stat span { font-size: 0.72rem; color: #8d96a0; }
.stat strong { font-size: 0.88rem; color: #2c3e50; margin-top: 0.1rem; }

.result-meta { font-size: 0.84rem; color: #495057; margin-bottom: 0.4rem; }
.meta-label { font-weight: 600; color: #6c757d; }

.result-path {
  margin-top: 0.8rem; padding-top: 0.8rem; border-top: 1px solid #eef0f2;
  font-size: 0.76rem; color: #adb5bd;
}
.result-path code { background: linear-gradient(135deg, #f0f3f6, #e8ecf0); padding: 0.15rem 0.4rem; border-radius: 4px; font-size: 0.74rem; color: #27ae60; }
</style>
