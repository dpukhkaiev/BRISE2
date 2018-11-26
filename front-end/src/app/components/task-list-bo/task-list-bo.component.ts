import { Component, OnInit, ViewChild } from '@angular/core';

import { MatPaginator, MatTable, MatSort, MatTableDataSource } from '@angular/material';
import { animate, state, style, transition, trigger } from '@angular/animations';

// Service
import { RestService } from '../../core/services/rest.service';
import { WsSocketService } from '../../core/services/ws.socket.service';
import { MainSocketService } from '../../core/services/main.socket.service';


import { Task } from '../../data/taskData.model';
import { Event } from '../../data/client-enums';
import { MainEvent } from '../../data/client-enums';

// import { resolve } from 'path';
import { TaskConfig } from '../../data/taskConfig.model';


@Component({
  selector: 'task-list-bo',
  templateUrl: './task-list-bo.component.html',
  styleUrls: ['./task-list-bo.component.scss'],
  animations: [
    trigger('detailExpand', [
      state('collapsed', style({ height: '0px', minHeight: '0', display: 'none' })),
      state('expanded', style({ height: '*' })),
      transition('expanded <=> collapsed', animate('225ms cubic-bezier(0.4, 0.0, 0.2, 1)')),
    ]),
  ],  
})
export class TaskListBoComponent implements OnInit {

  @ViewChild('table') table: MatTable<Element>;
  @ViewChild(MatPaginator) paginator: MatPaginator;
  @ViewChild(MatSort) sort: MatSort;
  
  stack: Array<any> = []
  result: Array<Task> = []
  // [new Task({'id': 1, 'run': {'start': 'da--'}, 'conf': {'sds': 1234}, 'meta': {'gogogogog': 1212}}), 
  // new Task({ 'id': 1, 'run': { 'start2': 'daqq--' }, 'conf': { 'sds2': 1234 }, 'meta': { 'gogogogog2': 92 } })] 
  focus: any
  displayedColumns: string[] = ['id', 'run', 'file', 'result'];
  ioConnection: any;
  taskConfig: TaskConfig

  public resultData: MatTableDataSource<Task>

  constructor(private ws: RestService, private io: WsSocketService, private ioMain: MainSocketService) {
    this.resultData = new MatTableDataSource(this.result);

    this.resultData.filterPredicate = (task, filter) => {
      return JSON.stringify(task).includes(filter)
    }
  }

  ngOnInit() {
    this.resultData.paginator = this.paginator;
    this.resultData.sort = this.sort;
    this.initIoConnection();
    this.initMainEvents()
  }

  isModelType(type: String) {
    return this.taskConfig && this.taskConfig.ModelConfiguration.ModelType == type
  }

  clearFocus():void {
    this.focus = null
  }
  applyFilter(filterValue: string) {
    this.resultData.filter = filterValue.trim().toLowerCase();

    if (this.resultData.paginator) {
      this.resultData.paginator.firstPage();
    }
  }


  // --------------------- SOCKET ---------------
  private initMainEvents(): void {
    this.ioMain.onEvent(MainEvent.EXPERIMENT)
      .subscribe((obj: any) => {
        this.taskConfig = obj['configuration']['experiment configuration']
      });
  }
  private initIoConnection(): void {
    this.io.initSocket();

    // Fresh updates. Each time +1 task
    this.ioConnection = this.io.onResults()
      .subscribe((obj: JSON) => {
        var fresh: Task = new Task(obj)
        !this.result.includes(fresh, -1) && this.result.push(fresh);

        this.resultData.data = this.result;
        // this.table.renderRows();
      });
    // Rewrite task stack
    this.ioConnection = this.io.stack()
      .subscribe((obj: Array<Object>) => {
        this.stack = obj.map(i => new Task(i));
      });

    // Observer for stack and all results from workers service
    this.ioConnection = this.io.onAllResults()
      .subscribe((obj: any) => {
        var data = JSON.parse(obj)
        // this.result = (data.hasOwnProperty('res') && data['res'].length) ? data['res'].map((t) => new Task(t)) : [];
        this.stack = (data.hasOwnProperty('stack') && data['stack'].length) ? data['stack'].map((t) => new Task(t)) : [];
      });

    this.io.onEvent(Event.CONNECT)
      .subscribe(() => {
        this.io.reqForAllRes();
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
