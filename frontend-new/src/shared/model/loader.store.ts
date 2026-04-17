import { ref } from 'vue'
import { defineStore } from 'pinia'

export const Loader = defineStore('loader', () => {
  const loaderState = ref(false)
 // should isVisible be used?
 function show() {
    loaderState.value = true;
 }

 function hide() {
   loaderState.value = false;
 }

 return {loaderState, show, hide}
})