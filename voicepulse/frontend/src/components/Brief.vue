<template>
  <div class="brief-card">
    <h4>Approach Brief</h4>
    <p>{{ text }}</p>
  </div>
</template>

<script setup>
defineProps({ text: String })
</script>

<style scoped>
.brief-card {
  background: linear-gradient(135deg, #e8f0fe, #f3e8fd);
  border-radius: 10px; padding: 1.2rem; margin-bottom: 1rem;
}
.brief-card h4 { font-size: 0.9rem; color: #1967d2; margin-bottom: 0.5rem; }
.brief-card p { font-size: 0.88rem; line-height: 1.5; color: #333; }
</style>
