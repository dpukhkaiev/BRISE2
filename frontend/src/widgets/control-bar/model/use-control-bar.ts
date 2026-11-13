import { computed, ref, onUnmounted } from 'vue'
import { storeToRefs } from 'pinia'
import { useMainEventStore, MainClientApi } from '../../../entities/main'
import { usePlotStore } from '../../../entities/main/model/plot.store'
//data
import { MainEvent } from '../../../entities/main'
import { Subscription } from 'rxjs'
import { parseJsonWithInfinity } from '../../../shared/lib'
  const isRunning = ref(false)
  // Flag for finish experiment
  const isFinish = ref(false)
  const showDownload = ref(false)
  const selectedFile = ref<File | null>(null)

export function useLaunchControl() {
    // create a store 
  const store = useMainEventStore()
  // destructure reactive value from main.event.store
  const { experiment_description, raw_product_configuration, searchspaceReady, isConnected } = storeToRefs(store)
  // plot selection in the frontend is allowed only once an experiment is started
  const plotStore = usePlotStore()
  const { canChangeVisibleCharts } = storeToRefs(plotStore)

  // the experiment the card shows: the uploaded file, or the running experiment if nothing was uploaded
  const shownConfiguration = computed(() => raw_product_configuration.value ?? experiment_description.value)

const subscriptions = new Subscription()
subscriptions.add(
    store.onEvent(MainEvent.FINAL)?.subscribe(() => {
      isRunning.value = false
      isFinish.value = true
    })
  )

  onUnmounted(() => {
    subscriptions.unsubscribe()
  })

  function openDownloadOption(): void {
    showDownload.value = true
  }

  function closeDownloadOption(): void {
    showDownload.value = false
  }

  function startMainControl(): void {
    if (!isRunning.value) {
      MainClientApi.startMain(raw_product_configuration.value);
      isRunning.value = true
      isFinish.value = false
      canChangeVisibleCharts.value = true
    }
  }

  function stopMainControl(): void {
    if (isRunning.value) {
      MainClientApi.stopMain()
      isRunning.value = false
    }
  }


  const uploadFile = async (): Promise<void> => {
    if (!selectedFile.value) return

    const file = selectedFile.value
    const reader = new FileReader()

    reader.onload = () => {
      try {
        const parsed = parseJsonWithInfinity(reader.result as string)
        raw_product_configuration.value = parsed
        searchspaceReady.value = false // the search space is described by the main node once the experiment starts
        // the charts of the previous experiment would stay next to the uploaded file otherwise; the selection of the
        // new one appears with its description, once the experiment has started
        plotStore.clearCharts()
        canChangeVisibleCharts.value = false
        selectedFile.value = null // reset input
      } catch (error) {
        console.error('Failed to parse experiment file:', error)
      }
    }

    reader.readAsText(file)
  }

  return {
    isRunning,
    isFinish,
    showDownload,
    selectedFile,
    shownConfiguration,
    isConnected,
    openDownloadOption,
    closeDownloadOption,
    startMainControl,
    stopMainControl,
    uploadFile
  }
}