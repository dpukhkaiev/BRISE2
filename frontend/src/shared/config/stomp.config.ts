import type { RxStompConfig } from "@stomp/rx-stomp";

export const stompConfig: RxStompConfig = {

  // connection
  brokerURL: `ws://${import.meta.env.VITE_EVENT_SERVICE_HOST}:${import.meta.env.VITE_EVENT_SERVICE_PORT}/ws`,
  // login data
  connectHeaders: {
    login: 'guest',
    passcode: 'guest'
  },
  heartbeatIncoming: 0,
  heartbeatOutgoing: 20000,
  reconnectDelay: 200,
  debug: import.meta.env.DEV
    ? (msg: string): void => {
        console.log('[STOMP]', msg);
      }
    : (): void => {}
}