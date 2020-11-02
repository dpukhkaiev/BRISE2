import { Injectable } from '@angular/core';
import { Observable } from 'rxjs/Observable';

import * as socketIo from 'socket.io-client';

import { MainEvent } from '../../data/client-enums';

import { environment } from '../../../environments/environment';
import {RxStompService} from "@stomp/ng2-stompjs";
import {Message} from "@stomp/stompjs";

@Injectable({
  providedIn: 'root',
})
export class MainEventService {
  private socket;
  private ong;
  private listeners: { [id: string]: Observable<object>; } = {}

  constructor(private rxStompService: RxStompService) {
    this.listeners[MainEvent.EXPERIMENT] = this.rxStompService.watch('front_experiment_queue', {'x-message-ttl': '1000'});
    this.listeners[MainEvent.DEFAULT] = this.rxStompService.watch('front_default_queue', {'x-message-ttl': '1000'});
    this.listeners[MainEvent.NEW] = this.rxStompService.watch('front_new_queue', {'x-message-ttl': '1000'});
    this.listeners[MainEvent.PREDICTIONS] = this.rxStompService.watch('front_predictions_queue', {'x-message-ttl': '1000'});
    this.listeners[MainEvent.FINAL] = this.rxStompService.watch('front_final_queue', {'x-message-ttl': '1000'});
    this.listeners[MainEvent.LOG] = this.rxStompService.watch('front_log_queue', {'x-message-ttl': '1000'});
  }

  public onEvent(event: MainEvent): Observable<any> {
    return this.listeners[String(event)]
  }
  public onEmptyEvent(event: MainEvent): Observable<any> {
    return new Observable<MainEvent>(observer => {
      this.socket.on(event, () => observer.next());
    });
  }
}
