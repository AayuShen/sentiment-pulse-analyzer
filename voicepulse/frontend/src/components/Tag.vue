<template>
  <span class="tag" :style="{ background: bg, color: fg }">{{ tag }}</span>
</template>

<script setup>
import { computed } from 'vue'
const props = defineProps({ tag: String })
const palette = {
  Positive: ['rgba(39,174,96,0.12)', '#27ae60'],
  Negative: ['rgba(231,76,60,0.12)', '#e74c3c'],
  Neutral: ['rgba(149,165,166,0.12)', '#7f8c8d'],
  Frustrated: ['rgba(243,156,18,0.12)', '#e67e22'],
  Satisfied: ['rgba(52,152,219,0.12)', '#2980b9']
}
const bg = computed(() => palette[props.tag]?.[0] || '#f5f5f5')
const fg = computed(() => palette[props.tag]?.[1] || '#333')
</script>

<style scoped>
.tag {
  display: inline-block; padding: 0.2rem 0.6rem; border-radius: 12px;
  font-size: 0.78rem; font-weight: 600; white-space: nowrap;
}
</style>
