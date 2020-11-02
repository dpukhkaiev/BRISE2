import {Injectable} from '@angular/core';
import {Http} from '@angular/http';
import {Observable} from 'rxjs/Observable';
import 'rxjs/add/operator/map';
import 'rxjs/add/operator/catch';
import 'rxjs/add/observable/throw';
import {RxStompService, RxStompRPCService} from '@stomp/ng2-stompjs';
import {Message} from '@stomp/stompjs';
import {IMessage, publishParams,} from '@stomp/stompjs';

import {myRxStompConfig} from './my-rx-stomp.config';
// User
import {Task} from '../../data/taskData.model';

@Injectable()
export class MainClientService {
  tasks: Task[] = [];

  constructor(private rxStompService: RxStompService) {
  }

// -----------------------------
//                    Main-node
  startMain(): any {
    const rxStompRPC = new RxStompRPCService(this.rxStompService);
    const myServiceEndPoint = 'main_start_queue';

    const request = '{"Method":"GET"}';
    const headers = {'body_type': 'json'};
    // It accepts a optional third argument a Hash of headers to be sent as part of the request
    rxStompRPC.rpc({destination: myServiceEndPoint, body: request, headers}).subscribe((message: Message) => {
      // Consume the response
      return message.body;
    });
  }

  getMainStatus(): any {
    const rxStompRPC = new RxStompRPCService(this.rxStompService);
    const myServiceEndPoint = 'main_status_queue';
    // It accepts a optional third argument a Hash of headers to be sent as part of the request
    rxStompRPC.rpc({destination: myServiceEndPoint, body: ''}).subscribe((message: Message) => {
      // Consume the response
      return message.body;
    });
  }

  stopMain(): any {
    const rxStompRPC = new RxStompRPCService(this.rxStompService);
    const myServiceEndPoint = 'main_stop_queue';
    // It accepts a optional third argument a Hash of headers to be sent as part of the request
    rxStompRPC.rpc({destination: myServiceEndPoint, body: ''}).subscribe((message: Message) => {
      // Consume the response
      return message.body;
    });
  }

  async downloadDump(format = 'pkl'): Promise<any> {
    const rxStompRPC = new RxStompRPCService(this.rxStompService);
    const myServiceEndPoint = 'main_download_dump_queue';
    const request = `{"format": "${format}"}`;
    const message = await rxStompRPC.rpc({destination: myServiceEndPoint, body: request}).toPromise();
    const obj = JSON.parse(message.body);
    if (obj['status'] === 'ok') {
      obj['body'] = atob(obj['body']);
    }
    return obj;
  }


}
