import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useAppStore = defineStore('app', () => {
  // Language filter shared across tabs
  const langFilter = ref('all')
  const darkMode = ref(false)

  function setLang(lang) {
    langFilter.value = lang
  }

  function toggleDark() {
    darkMode.value = !darkMode.value
    document.documentElement.classList.toggle('dark', darkMode.value)
  }

  return { langFilter, darkMode, setLang, toggleDark }
})
