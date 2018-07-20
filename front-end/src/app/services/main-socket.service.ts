import { Injectable } from '@angular/core';
import { Observable } from 'rxjs/Observable';

import * as socketIo from 'socket.io-client';

import { MainEvent } from '../data/client-enums';

import { environment } from '../../environments/environment';
const SERVER_URL = environment.mainNode;


@Injectable()
export class MainSocketService {
  private socket;

  constructor() { }

  public initSocket(): void {
    this.socket = socketIo(SERVER_URL);
  }

  public onEvent(event: MainEvent): Observable<any> {
    return new Observable<object>(observer => {
      this.socket.on(event, (data: object) => observer.next(data));
    });
  }
}
