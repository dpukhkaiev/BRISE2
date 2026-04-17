import { RxStomp, type RxStompConfig } from '@stomp/rx-stomp'
import { stompConfig } from '../config/stomp.config'

export const  stompClient = new RxStomp();
// configuring data for transportation 
  stompClient.configure(stompConfig)
// activate the connection
  stompClient.activate();
   