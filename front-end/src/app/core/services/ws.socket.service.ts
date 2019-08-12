import { Injectable } from '@angular/core';
import { Observable } from 'rxjs/Observable';
// import { Observer } from 'rxjs/Observer';

import * as socketIo from 'socket.io-client';

// User
import { Task } from '../../data/taskData.model';
import { Event } from '../../data/client-enums';

// Variables
import { environment } from '../../../environments/environment';
const SERVER_URL = environment.workerService;
const NAME_SPACE = environment.nameSpace;


@Injectable({
  providedIn: 'root',
})
export class WsSocketService {
  private socket;
  constructor() { }

  public initSocket(): void {
    this.socket = socketIo(SERVER_URL + NAME_SPACE);
    this.socket.emit('join', {'room': NAME_SPACE});
  }

  public reqForAllRes(): void {
    this.socket.emit('all result');
  }

  public onResults(): Observable<JSON> {
    return new Observable<JSON>(observer => {
      this.socket.on('result', (data: JSON) => observer.next(data));
    });
  }

  public stack(): Observable<Array<Object>> {
    return new Observable<Array<Object>>(observer => {
      this.socket.on('stack', (data: Array<Object>) => observer.next(data));
    });
  }

  public onAllResults(): Observable<object> {
    return new Observable<object>(observer => {
      this.socket.on('all result', (data: object) => observer.next(data));
    });
  }

  public onEvent(event: Event): Observable<any> {
    return new Observable<Event>(observer => {
      this.socket.on(event, () => observer.next());
    });
  }

}
