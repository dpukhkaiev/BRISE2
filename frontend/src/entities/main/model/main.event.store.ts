import { ref } from 'vue'
import { defineStore } from 'pinia'
import { MainEvent } from './main.types'
import { stompClient } from '../../../shared/api/stomp.client'
import type { ExperimentDescription } from '../../experiment/model/experiment.model'
import type { IMessage } from '@stomp/stompjs'
import type { Observable } from 'rxjs'

const isConnected = ref(false)
stompClient.connectionState$.subscribe(state => {
   isConnected.value = state === 1
})

export const useMainEventStore = defineStore('mainEvent', () => {
   const experiment_description = ref<ExperimentDescription | null>(null)
   const searchspace = ref<any>(null)
   const globalConfig = ref<any>(null)
   const plotlyInstance = ref<any>(null)
   const listeners: Record<string, Observable<IMessage>> = {
      [MainEvent.EXPERIMENT]: stompClient.watch('front_experiment_queue', { 'x-message-ttl': '1000' }),
      [MainEvent.FINAL]: stompClient.watch('front_final_queue', { 'x-message-ttl': '1000' }),
      [MainEvent.DEFAULT]: stompClient.watch('front_default_queue', { 'x-message-ttl': '1000' }),
      [MainEvent.NEW]: stompClient.watch('front_new_queue', { 'x-message-ttl': '1000' }),
      [MainEvent.PREDICTIONS]: stompClient.watch('front_predictions_queue', { 'x-message-ttl': '1000' }),
      [MainEvent.LOG]: stompClient.watch('front_log_queue', { 'x-message-ttl': '1000' })

   }

   function onEvent(event: MainEvent): Observable<IMessage> | undefined {
      return listeners[String(event)]
   }

   // load plotly async in the background
   async function loadPlotly() {
      if (!plotlyInstance.value) {
         try {
            plotlyInstance.value = await import('plotly.js-dist-min')
            console.log('Plotly successfully initialized')
         } catch (error) {
            console.error('no success', error)
         }
      }
   }

   // starts the subsription to Experiment event
   function initEvent() {
      console.log('initEvent called, subscribing to EXPERIMENT queue')
      onEvent(MainEvent.EXPERIMENT)?.subscribe((message: any) => {
         console.log('EXPERIMENT message received:', message.headers['message_subtype'])
         if (message.headers['message_subtype'] === 'description') {
            const clean = message.body.replace(/:\s*Infinity/g, ': null')
            const body = JSON.parse(clean) as { experiment_description: ExperimentDescription, searchspace_description: any, global_configuration: any }
            console.log('after the setting', experiment_description.value?.Context?.TaskConfiguration?.TaskName)
            experiment_description.value = body.experiment_description
            searchspace.value = body.searchspace_description
            globalConfig.value = body.global_configuration
         }
      })
   }



   return { globalConfig, searchspace, experiment_description, isConnected, onEvent, initEvent, loadPlotly, plotlyInstance }
})