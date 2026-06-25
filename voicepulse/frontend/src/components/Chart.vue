<template>
  <div class="chart-card">
    <div class="chart-header">
      <h3>{{ title }}</h3>
      <button @click="download">PNG</button>
    </div>
    <div class="chart-body">
      <component :is="chartComp" :data="data" :options="opts" ref="chartRef" />
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { Bar, Line, Doughnut } from 'vue-chartjs'
import {
  Chart as ChartJS, CategoryScale, LinearScale, BarElement,
  PointElement, LineElement, ArcElement, Title, Tooltip, Legend
} from 'chart.js'

ChartJS.register(CategoryScale, LinearScale, BarElement, PointElement, LineElement, ArcElement, Title, Tooltip, Legend)

const props = defineProps({ title: String, type: String, data: Object })
const chartRef = ref(null)
const map = { bar: Bar, line: Line, doughnut: Doughnut }
const chartComp = computed(() => map[props.type] || Bar)
const opts = computed(() => ({
  responsive: true,
  maintainAspectRatio: true,
  plugins: { legend: { display: props.type !== 'bar' } }
}))

function download() {
  const canvas = chartRef.value?.chart?.canvas
  if (!canvas) return
  const link = document.createElement('a')
  link.download = `${props.title.replace(/\s+/g, '_')}.png`
  link.href = canvas.toDataURL('image/png')
  link.click()
}
</script>

<style scoped>
.chart-card { background: #fafcfd; border-radius: 10px; padding: 1rem; box-shadow: 0 1px 3px rgba(0,0,0,0.06); border: 1px solid #eef0f2; }
.chart-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.6rem; }
.chart-header h3 { font-size: 0.92rem; font-weight: 600; color: #2c3e50; }
.chart-header button {
  padding: 0.28rem 0.65rem; border: 1px solid #dce2e8; background: #fff;
  border-radius: 6px; cursor: pointer; font-size: 0.72rem; color: #6c757d; font-weight: 500;
  transition: all 0.15s;
}
.chart-header button:hover { background: #f0f3f6; border-color: #c8d6e5; color: #495057; }
.chart-body { position: relative; }
</style>
