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

  const default_configuration = ref<any>(null)
  // reactive to make them more robust
  let sol= ref<number[]>([])
  let dc = ref<number[]>([])

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
    default_configuration.value = null
    news.value = []
  }

  function computeQualityGain(dcValue: number, solValue: number, isMinimization: boolean): number | null {
    if (dcValue === 0) {
      return null
    }
    const diff = isMinimization ? dcValue - solValue : solValue - dcValue
    return 100 * diff / dcValue
  }

// decimalPipe alternative
function formatPercent(value: number | null): string {
    if (value === null || !Number.isFinite(value)) {
      return 'N/A'
    }
    return value.toFixed(2)
}

  return {
    news,
    snackbar,
    snackbarMsg,
    solutionState,
    sol,
    dc,
    default_configuration,
    pushNews,
    triggerSnackbar,
    refresh,
    formatPercent,
    computeQualityGain
  }
}