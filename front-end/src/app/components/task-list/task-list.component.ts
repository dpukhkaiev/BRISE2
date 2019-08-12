import { Component, OnInit, ViewChild } from '@angular/core';

import { MatPaginator, MatTable, MatSort, MatTableDataSource } from '@angular/material';
import { animate, state, style, transition, trigger } from '@angular/animations';

// Service
import { RestService } from '../../core/services/rest.service';
import { MainSocketService } from '../../core/services/main.socket.service';


import { Task } from '../../data/taskData.model';
import { Event } from '../../data/client-enums';
import { ExperimentDescription } from '../../data/experimentDescription.model';

import { MainEvent } from '../../data/client-enums';

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
  focus: any
  displayedColumns: string[] = ['id', 'run', 'result'];

  experimentDescription: ExperimentDescription

  public resultData: MatTableDataSource<Task>

  constructor(private ws: RestService, private ioMain: MainSocketService) {
    this.resultData = new MatTableDataSource(this.result);

    this.resultData.filterPredicate = (task, filter) => {
      const dataStr = task.id + 
      task.run.param.frequency + 
      task.run.param.threads + 
      task.config.ws_file + 
      task.meta.result.energy +
      task.meta.result.time;
      return dataStr.indexOf(filter) != -1;
    }
  }

  ngOnInit() {
    this.resultData.paginator = this.paginator;
    this.resultData.sort = this.sort;
    this.resultData.sortingDataAccessor = this.sortingDataAccessor;
    this.initMainEvents()

  }

  clearFocus():void {
    this.focus = null
  }
  isModelType(type: String) {
    return this.experimentDescription && this.experimentDescription.ModelConfiguration.ModelType == type
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
      case 'result': return data.meta ? Number(data.meta.result.energy) : null;
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
    this.ioMain.onEvent(MainEvent.EXPERIMENT)
      .subscribe((obj: any) => {
        this.experimentDescription = obj['description']['experiment description']
      });
    
    this.ioMain.onEvent(MainEvent.NEW)
      .subscribe((obj: JSON) => {
        if (obj["task"]) {
          var fresh: Task = new Task(obj)
          // add a new task if it is not in the this.result
          !this.result.includes(fresh, -1) && this.result.push(fresh);

          this.resultData.data = this.result;
        }
      });
  }
}
