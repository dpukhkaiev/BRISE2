import { computed, ref, shallowRef } from 'vue'
import type { Solution } from '../../../entities/task/model/task-data.model'


export interface NewsEntry {
  id: number
  time: number
  message: string
}

let nextNewsId = 0

export function useInfoBoard() {
  // information log
  const news = ref<NewsEntry[]>([])
  const newsExpanded = ref(false)
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
    news.value = [...news.value, { id: nextNewsId++, time: Date.now(), message }]
  }

  const visibleNews = computed<NewsEntry[]>(() =>
    newsExpanded.value ? news.value : news.value.slice(-30)
  )

  function toggleNewsExpanded(): void {
    newsExpanded.value = !newsExpanded.value
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
    newsExpanded.value = false
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
    visibleNews,
    newsExpanded,
    snackbar,
    snackbarMsg,
    solutionState,
    sol,
    dc,
    default_configuration,
    pushNews,
    toggleNewsExpanded,
    triggerSnackbar,
    refresh,
    formatPercent,
    computeQualityGain
  }
}