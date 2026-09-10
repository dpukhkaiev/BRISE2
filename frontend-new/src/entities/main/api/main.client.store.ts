import { stompClient } from '../../../shared/api/stomp.client'
import { RxStompRPC } from '@stomp/rx-stomp'
import { firstValueFrom } from 'rxjs';

// return a promise

const rxStompRPC = new RxStompRPC(stompClient)
export function startMain(description: any): void {
    const myServiceEndPoint = 'main_start_queue';
    const request = JSON.stringify({ "Method": "GET", "Description": description })
    const headers = { 'body_type': 'json' }
    // stompClient.publish({destination: myServiceEndPoint, body: request, headers})  
    // firstValueFrom instead of toPromise (deprecated) 
    console.log('startMain called')
    firstValueFrom(rxStompRPC.rpc({ destination: myServiceEndPoint, body: request, headers })
    ).then(() => console.log('startMain sent'))
        .catch(err => console.error('startMain error: ', err))

}

export function getMainStatus(): void {
    const myServiceEndPoint = 'main_status_queue'
    firstValueFrom(rxStompRPC.rpc({ destination: myServiceEndPoint, body: '' })
    ).catch(err => console.error('getMainStatus error: ', err))
}

export function stopMain(): void {
    const myServiceEndPoint = 'main_stop_queue'
    //stompClient.publish({destination: myServiceEndPoint, body:''}) 
    firstValueFrom(rxStompRPC.rpc({ destination: myServiceEndPoint, body: '' })
    ).catch(err => console.error('stopMain error: ', err))
} 

export async function downloadDump(format = 'pkl'): Promise<any> {
    const myServiceEndPoint = 'main_download_dump_queue'
    const request = `{"format": "${format}"}`
    const response = await firstValueFrom(rxStompRPC.rpc({ destination: myServiceEndPoint, body: request }))
    const object = JSON.parse(response.body)
    // decoding the strings
    if (object['status'] === 'ok') {
        object['object'] = atob(object['body'])
    }
    return object
}


// namespace export for importing functions all at once
export const MainClientApi = {
    startMain,
    stopMain,
    getMainStatus,
    downloadDump
}