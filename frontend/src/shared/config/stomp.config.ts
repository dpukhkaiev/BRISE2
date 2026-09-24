import type { RxStompConfig } from "@stomp/rx-stomp";

export const stompConfig: RxStompConfig = {

  // connection 
  brokerURL: 'ws://localhost:15674/ws',
  // login data
  connectHeaders: {
    login: 'guest',
    passcode: 'guest'
  },
  heartbeatIncoming: 0,
  heartbeatOutgoing: 20000,
  reconnectDelay: 200,
  debug: (msg: string): void => {
    console.log('[STOMP]', msg);
  }
}