import { ref, onUnmounted } from 'vue'
import { storeToRefs } from 'pinia'
import { useMainEventStore, MainClientApi } from '../../../entities/main'
//data
import { MainEvent } from '../../../entities/main'
import { Subscription } from 'rxjs'
  const isRunning = ref(false)
  // Flag for finish experiment
  const isFinish = ref(false)
  const showDownload = ref(false)
  const selectedFile = ref<File | null>(null)

export function useLaunchControl() {
    // create a store 
  const store = useMainEventStore()
  // destructure reactive value from main.event.store
  const { experiment_description, searchspace, isConnected } = storeToRefs(store)

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
      MainClientApi.startMain(JSON.parse(JSON.stringify(experiment_description.value)));
      isRunning.value = true
      isFinish.value = false
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
        const clean = (reader.result as string).replace(/:\s*Infinity/g, ': 1e308')
        const parsed = JSON.parse(clean)
        store.experiment_description = parsed
        store.searchspace = parsed?.["Context"]?.["SearchSpace"]
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
    experiment_description,
    isConnected,
    openDownloadOption,
    closeDownloadOption,
    startMainControl,
    stopMainControl,
    uploadFile
  }
}