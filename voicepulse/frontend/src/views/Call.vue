<template>
  <div v-if="call">
    <div class="top">
      <h1>Call {{ call.cid }}</h1>
      <Tag :tag="call.tag" />
    </div>
    <div class="meta">
      <span>{{ new Date(call.processed_at).toLocaleString() }}</span>
      <span>Confidence: {{ call.score }}</span>
      <span v-if="call.topics?.length">Topics: {{ call.topics.join(', ') }}</span>
      <span v-if="call.shift">Shift: {{ call.shift }}</span>
    </div>
    <Brief v-if="call.brief" :text="call.brief" />
    <div class="summary" v-if="call.summary">
      <h3>Summary</h3>
      <p>{{ call.summary }}</p>
    </div>
    <div class="transcript">
      <h3>Transcript</h3>
      <div v-for="(turn, i) in call.turns" :key="i" class="turn" :class="turn.speaker">
        <div class="turn-head">
          <span class="speaker">{{ turn.speaker }}</span>
          <Tag :tag="turn.tag" />
        </div>
        <p>{{ turn.text }}</p>
      </div>
    </div>
  </div>
  <div v-else class="loading">Loading...</div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import axios from 'axios'
import Tag from '../components/Tag.vue'
import Brief from '../components/Brief.vue'

const route = useRoute()
const call = ref(null)

onMounted(async () => {
  const { data } = await axios.get(`/api/sentiment/history/all`)
  call.value = data.calls?.find(c => c.id === route.params.id)
  if (!call.value) {
    const r = await axios.get(`/api/sentiment/${route.params.id}`)
    call.value = r.data
  }
})
</script>

<style scoped>
.top { display: flex; align-items: center; gap: 1rem; margin-bottom: 0.5rem; }
.top h1 { font-size: 1.4rem; }
.meta { display: flex; gap: 1.5rem; font-size: 0.85rem; color: #666; margin-bottom: 1rem; flex-wrap: wrap; }
.summary { background: #fff; border-radius: 10px; padding: 1rem; margin-bottom: 1rem; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }
.summary h3 { font-size: 1rem; margin-bottom: 0.4rem; }
.transcript { background: #fff; border-radius: 10px; padding: 1rem; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }
.transcript h3 { font-size: 1rem; margin-bottom: 0.8rem; }
.turn { padding: 0.6rem 0; border-bottom: 1px solid #f0f0f0; }
.turn:last-child { border-bottom: none; }
.turn-head { display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.2rem; }
.speaker { font-weight: 600; font-size: 0.85rem; color: #555; }
.turn p { font-size: 0.9rem; line-height: 1.5; color: #333; }
.loading { text-align: center; padding: 3rem; color: #999; }
</style>
