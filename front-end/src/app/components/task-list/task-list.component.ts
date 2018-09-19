import { Component, OnInit } from '@angular/core';

// Service
import { RestService } from '../../core/services/rest.service';
import { WsSocketService } from '../../core/services/ws.socket.service';
import { Task } from '../../data/taskData.model';
import { Event } from '../../data/client-enums';
// import { resolve } from 'path';

@Component({
  selector: 'app-task-list',
  templateUrl: './task-list.component.html',
  styleUrls: ['./task-list.component.scss']  
})
export class TaskListComponent implements OnInit {
  
  stack = []
  result = [] 
  focus
  ioConnection: any;

  constructor(private ws: RestService, private io: WsSocketService) { }

  ngOnInit() {
    this.initIoConnection();
  }

  clearFocus():void {
    this.focus = null
  }

  // --------------------- SOCKET ---------------
  private initIoConnection(): void {
    this.io.initSocket();

    // Fresh updates. Each time +1 task
    this.ioConnection = this.io.onResults()
      .subscribe((obj: JSON) => {
        var fresh: Task = new Task(obj)
        !this.result.includes(fresh, -1) && this.result.push(fresh);
        // console.log(' Object:', obj);
      });
    // Rewrite task stack
    this.ioConnection = this.io.stack()
      .subscribe((obj: Array<Object>) => {
        this.stack = obj;
        // console.log(' Stack:', obj);
      });

    // Observer for stack and all results from workers service
    this.ioConnection = this.io.onAllResults()
      .subscribe((obj: any) => {
        console.log("onAllResults ::", JSON.parse(obj))
        var data = JSON.parse(obj)
        this.result = (data.hasOwnProperty('res') && data['res'].length) ? data['res'].map((t) => new Task(t)) : [];
        this.stack = (data.hasOwnProperty('stack') && data['stack'].length) ? data['stack'].map((t) => new Task(t)) : [];
      });

    this.io.onEvent(Event.CONNECT)
      .subscribe(() => {
        console.log(' task-list: connected');
        // get init data
        this.io.reqForAllRes();
      });
    this.io.onEvent(Event.DISCONNECT)
      .subscribe(() => {
        console.log(' task-list: disconnected');
      });
  }

  // ____________________________ HTTP _____
  taskInfo(id: string): any {
     this.ws.getTaskById(id)
      .subscribe((res) => {
        this.focus = res["result"];
        this.focus.time = res["time"]
      }
      );
  }

}
