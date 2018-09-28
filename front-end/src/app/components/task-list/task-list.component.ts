import { Component, OnInit, ViewChild } from '@angular/core';

import { MatPaginator, MatTable, MatSort, MatTableDataSource } from '@angular/material';
import { animate, state, style, transition, trigger } from '@angular/animations';

// Service
import { RestService } from '../../core/services/rest.service';
import { WsSocketService } from '../../core/services/ws.socket.service';
import { MainSocketService } from '../../core/services/main.socket.service';


import { Task } from '../../data/taskData.model';
import { Event } from '../../data/client-enums';
import { TaskConfig } from '../../data/taskConfig.model';

import { MainEvent } from '../../data/client-enums';

// import { resolve } from 'path';

@Component({
  selector: 'app-task-list',
  templateUrl: './task-list.component.html',
  styleUrls: ['./task-list.component.scss'],
  animations: [
    trigger('detailExpand', [
      state('collapsed', style({ height: '0px', minHeight: '0', display: 'none' })),
      state('expanded', style({ height: '*' })),
      transition('expanded <=> collapsed', animate('225ms cubic-bezier(0.4, 0.0, 0.2, 1)')),
    ]),
  ],  
})
export class TaskListComponent implements OnInit {

  @ViewChild('table') table: MatTable<Element>;
  @ViewChild(MatPaginator) paginator: MatPaginator;
  @ViewChild(MatSort) sort: MatSort;
  
  stack: Array<any> = []
  result: Array<Task> = []
  // [new Task({'id': 1, 'run': {'start': 'da--'}, 'conf': {'sds': 1234}, 'meta': {'gogogogog': 1212}}), 
  // new Task({ 'id': 1, 'run': { 'start2': 'daqq--' }, 'conf': { 'sds2': 1234 }, 'meta': { 'gogogogog2': 92 } })] 
  focus: any
  displayedColumns: string[] = ['id', 'run', 'file', 'result', 'time'];
  ioConnection: any;

  taskConfig: TaskConfig

  public resultData: MatTableDataSource<Task>

  constructor(private ws: RestService, private io: WsSocketService, private ioMain: MainSocketService) {
    this.resultData = new MatTableDataSource(this.result);

    this.resultData.filterPredicate = (task, filter) => {
      const dataStr = task.id + 
      task.run.param.frequency + 
      task.run.param.threads + 
      task.config.ws_file + 
      task.meta.result.energy +
      task.meta.result.time;
      // JSON.stringify(task).includes(filter)
      return dataStr.indexOf(filter) != -1;
    }
  }

  ngOnInit() {
    this.resultData.paginator = this.paginator;
    this.resultData.sort = this.sort;
    this.resultData.sortingDataAccessor = this.sortingDataAccessor;
    this.initIoConnection();
    this.initMainEvents()

  }

  clearFocus():void {
    this.focus = null
  }
  isModelType(type: String) {
    return this.taskConfig && this.taskConfig.ModelConfiguration.ModelType == type
  }
  applyFilter(filterValue: string) {
    this.resultData.filter = filterValue.trim().toLowerCase();

    if (this.resultData.paginator) {
      this.resultData.paginator.firstPage();
    }
  }
  sortingDataAccessor(data, sortHeaderId) {
    switch (sortHeaderId) {
      case 'id': return data.id ? data.id : null;
      case 'run': return data.run.param.frequency ? data.run.param.frequency : null;
      case 'file': return data.config.ws_file ? data.config.ws_file : null;
      case 'result': return data.meta ? Number(data.meta.result.energy) : null;
      case 'time': return data.meta ? String(data.meta.result.time) : null;
      default: return data[sortHeaderId];
    }
  }

  searchTasks(search: Array<any>) {
    let select:Array<Task> = [] 
    if (arguments.length && this.result.length) {
      this.result.map(task => {
        let paramsValues = task.meta && Object.values(task.meta.result) 
        let union = new Set(paramsValues.concat(search))
        if (union.size == paramsValues.length) { // all or more searching parametrs in task
          select.push(task)
        }
      })
    } 
    return select 
  }

  getAverageResult(search: Array<any>) {
    let sum: Array<number> = []
    let select = this.searchTasks(search)
    select && select.map(task => {
      task.meta && sum.push(Number(task.meta.result.energy))
    })
    return sum && sum.reduce((a, b) => a + b, 0)/sum.length
  }

  // --------------------- SOCKET ---------------
  private initMainEvents(): void {
    this.ioMain.onEvent(MainEvent.MAIN_CONF)
      .subscribe((obj: any) => {
        this.taskConfig = obj['task']
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
        // console.log(' Stack:', obj);
      });

    // Observer for stack and all results from workers service
    this.ioConnection = this.io.onAllResults()
      .subscribe((obj: any) => {
        console.log("onAllResults ::", JSON.parse(obj))
        var data = JSON.parse(obj)
        // this.result = (data.hasOwnProperty('res') && data['res'].length) ? data['res'].map((t) => new Task(t)) : [];
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
