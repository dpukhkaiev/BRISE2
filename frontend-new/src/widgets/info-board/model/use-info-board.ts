import { ref, shallowRef } from 'vue'
import type { Solution } from '../../../entities/task/model/task-data.model'

export interface NewsPoint {
  time: number
  message: string
}

export function useInfoBoard() {
  // information log
  const news = ref<NewsPoint[]>([])
  const snackbar = ref(false)
  const snackbarMsg = ref('')

  // new: shallowRef to imporve performance, 1 shallowRef, 1 render
  const solutionState = shallowRef<{
    solution: Solution | undefined
    configWithNones: string
    result: string
  }>({ solution: undefined, configWithNones: '', result: '' })

 // threshold for event news messages
  function pushNews(message: string): void {
    const updated = [...news.value, { time: Date.now(), message }]
    news.value = updated.length > 30 ? updated.slice(-30) : updated
  }

  function triggerSnackbar(msg: string): void {
    snackbarMsg.value = msg
    snackbar.value = true
  }

  function refresh(): void {
    solutionState.value = {
      solution: undefined,
      configWithNones: '',
      result: ''
    }
    news.value = []
  }

// decimalPipe alternative
function formatPercent(value: number): string {
    return value.toFixed(2)
}

  return {
    news,
    snackbar,
    snackbarMsg,
    solutionState,
    pushNews,
    triggerSnackbar,
    refresh,
    formatPercent
  }
}