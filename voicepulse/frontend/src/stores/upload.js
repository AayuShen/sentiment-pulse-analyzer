import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'

export const useUploadStore = defineStore('upload', () => {
  const customers = ref([])
  const processing = ref(false)
  const custInputs = {}
  let nextCustId = 1
  let nextFileId = 1

  const totalFiles = computed(() =>
    customers.value.reduce((s, c) => s + c.files.length, 0)
  )

  const pendingFiles = computed(() =>
    customers.value.reduce((s, c) =>
      s + c.files.filter(f => f.status !== 'SUCCESS').length, 0
    )
  )

  const allDone = computed(() =>
    customers.value.every(c =>
      c.files.length > 0 && c.files.every(f => f.status === 'SUCCESS')
    )
  )

  function addCustomer(name = '') {
    customers.value.push({
      id: nextCustId++,
      cid: '',
      name,
      lang: 'en',
      files: [],
      dragging: false,
      uploading: false,
      completed: false,
      results: []
    })
  }

  function removeCustomer(ci) {
    if (customers.value[ci]?.uploading) return
    customers.value.splice(ci, 1)
  }

  function addFilesToCustomer(ci, fileList) {
    const cust = customers.value[ci]
    if (!cust) return
    for (const f of fileList) {
      // Dedup: skip same name already in this customer
      if (cust.files.some(ex => ex.name === f.name)) {
        window._toast?.('warning', `File "${f.name}" already added`)
        continue
      }
      // Max 5 files total
      if (totalFiles.value >= 5) {
        window._toast?.('error', 'Maximum 5 files allowed')
        break
      }
      cust.files.push({
        uid: nextFileId++,
        name: f.name,
        file: f,
        lang: cust.lang,
        jobId: '',
        progress: 0,
        status: '',
        result: null,
        callDate: '',
        callTime: '',
        duration: 0,
        customerName: '',
        agentLabel: 'Agent'
      })
    }
  }

  function removeFile(ci, fi) {
    customers.value[ci].files.splice(fi, 1)
  }

  function setProcessing(val) {
    processing.value = val
  }

  function updateFileResult(ci, fi, updates) {
    const f = customers.value[ci]?.files[fi]
    if (f) Object.assign(f, updates)
  }

  function markCustomerComplete(ci) {
    customers.value[ci].uploading = false
    customers.value[ci].completed = true
  }

  function getUploadedFiles() {
    const all = []
    for (const c of customers.value) {
      for (const f of c.files) {
        if (f.status === 'SUCCESS') all.push({ ...f, cid: c.cid, custName: c.name })
      }
    }
    return all
  }

  async function loadCompletedFiles() {
    try {
      const { data } = await axios.get('/api/mongo/calls', { params: { limit: 100 } })
      const calls = Array.isArray(data) ? data : (data.calls || [])
      if (!calls.length) return
      // Group by customer ID
      const groups = {}
      for (const call of calls) {
        const cid = call.cid || 'UNKNOWN'
        if (!groups[cid]) groups[cid] = []
        groups[cid].push(call)
      }
      // Populate store
      for (const [cid, callList] of Object.entries(groups)) {
        const cust = {
          id: nextCustId++,
          cid,
          name: callList[0]?.customer_name || cid,
          lang: (callList[0]?.language || 'en').toLowerCase(),
          files: [],
          dragging: false,
          uploading: false,
          completed: true
        }
        for (const call of callList) {
          const fname = (call.filename || `${cid}_call.mp3`).replace(/^.*[\\/]/, '')
          cust.files.push({
            uid: nextFileId++,
            name: fname,
            file: null,
            lang: call.language || 'en',
            jobId: call.job_id || '',
            progress: 100,
            status: 'SUCCESS',
            result: call,
            duration: call.duration || 0,
            customerName: call.customer_name || '',
            agentLabel: 'Agent',
            callDate: call.call_date || '',
            callTime: call.call_time || '',
            resultTag: call.tag || '',
            resultScore: call.score || 0,
            resultCustomer: call.customer_name || '',
            resultTopics: call.topics || [],
            resultShift: call.shift || '',
            resultSummary: call.brief || ''
          })
        }
        customers.value.push(cust)
      }
    } catch (e) {
      console.error('Failed to load completed files:', e)
    }
  }

  return {
    customers, processing, totalFiles, pendingFiles, allDone, custInputs,
    addCustomer, removeCustomer, addFilesToCustomer, removeFile,
    setProcessing, updateFileResult, markCustomerComplete,
    getUploadedFiles, loadCompletedFiles
  }
})
