import { ref } from 'vue'
import { defineStore } from 'pinia'
import { MainEvent } from './main.types'
import { stompClient } from '../../../shared/api/stomp.client'
import type { ExperimentDescription } from '../../experiment/model/experiment.model'
import type { IMessage } from '@stomp/stompjs'
import type { Observable } from 'rxjs'


export const useMainEventStore = defineStore('mainEvent', () => {
   const experiment_description = ref<ExperimentDescription | null>(null)
   const searchspace = ref<any>(null)
   const globalConfig = ref<any>(null)

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

   // starts the subsription to Experiment event
   function initEvent() {
      onEvent(MainEvent.EXPERIMENT)?.subscribe((message: any) => {
         if (message.headers['message_subtype'] === 'description') {
            console.log(message.body)
            const clean = message.body.replace(/:\s*Infinity/g, ': null')
            const body = JSON.parse(clean) as { experiment_description: ExperimentDescription, searchspace_description: any, global_configuration: any }
            experiment_description.value = body.experiment_description
            searchspace.value = body.searchspace_description
            globalConfig.value = body.global_configuration

         }
      })
   }

   return { globalConfig, searchspace, experiment_description, onEvent, initEvent }
})