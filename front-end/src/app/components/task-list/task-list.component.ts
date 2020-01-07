import { Component, OnInit, ViewChild } from '@angular/core';

import { MatPaginator, MatTable, MatSort, MatTableDataSource } from '@angular/material';
import { animate, state, style, transition, trigger } from '@angular/animations';

// Service
import { RestService } from '../../core/services/rest.service';
import { MainSocketService } from '../../core/services/main.socket.service';


import { Task } from '../../data/taskData.model';

import { MainEvent } from '../../data/client-enums';

import { ExperimentDescription } from '../../data/experimentDescription.model';


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
  displayedColumns: String[] =  ['id', 'run', 'result'];
  experimentDescription: ExperimentDescription
  update: boolean

  public resultData: MatTableDataSource<Task>

  constructor(private ws: RestService, private ioMain: MainSocketService) {
    this.resultData = new MatTableDataSource(this.result);

    this.resultData.filterPredicate = (task, filter) => {
      let params: String
      let results: String
      task.run.param.forEach(param => {
        params = params + param
      });
      Object.values(task.meta.result).forEach(result => {
        results = results + String(result)
      });
      const dataStr = task.id +
        params + 
        results;
      return dataStr.indexOf(filter) != -1;
    }
  }

  ngOnInit() {
    this.resultData.paginator = this.paginator;
    this.resultData.sort = this.sort;
    this.resultData.sortingDataAccessor = this.sortingDataAccessor;
    this.initMainEvents()

  }

  refresh() {
    this.result = []
    this.resultData = new MatTableDataSource([])
    this.update = true
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

  sortingDataAccessor(data, sortHeaderId) {
    switch (sortHeaderId) {
      case 'id': return data.id ? data.id : null;
      case 'run': return Object.values(data.run.param)[0] ? Object.values(data.run.param)[0] : null;
      case 'result': return Object.values(data.meta.res_config)[0] ? Number(Object.values(data.meta.res_config)[0]) : null;
      default: return data[sortHeaderId];
    }
  }

  searchTasks(search: Array<any>) {
    let search_without_Nones = this.replaceNones(search)
    let select: Array<Task> = []
    if (arguments.length && this.result.length) {
      this.result.map(task => {
        let paramsValues = this.replaceNones(task.config && Object.values(task.config))
        let count_diff = 0
        for (let i = 0; i < search_without_Nones.length; ++i){
          if (search_without_Nones[i] != paramsValues[i]){
            count_diff = count_diff + 1
          }
        }
        if(count_diff == 0){
          select.push(task)
        }
      })
    }
    return select
  }

  replaceNones(config: Array<any>){
    let res_config = new Array<any>()
    config.forEach(param => {
      if(param == '' || param == null){
        res_config.push('None')
      }
      else{
        res_config.push(param)
      }
    });
    return res_config
  }

  getAverageResult(search: Array<any>) {
    let select = this.searchTasks(search)
    let avg_res:any[] = new Array<any>() 
    let sum = new Array<Array<any>>()
    for (let i = 0; i < Object.values(select[0].meta.result).length; i++) {
      sum[i]  = new Array<any>(); 
    }
    select && select.map(task => {
      for (let i = 0; i < Object.values(task.meta.result).length; i++) {
        task.meta && sum[i].push(Number(Object.values(task.meta.result)[i]))
      }
    })
    for (let i = 0; i < Object.values(select[0].meta.result).length; i++) {
      avg_res[i] = sum[i].reduce((a, b) => a + b, 0)/sum[i].length
    }
    return avg_res
  }

  // --------------------- SOCKET ---------------
  private initMainEvents(): void {
    this.ioMain.onEvent(MainEvent.EXPERIMENT)
      .subscribe((obj: any) => {
        this.experimentDescription = obj['description']['experiment description']
        this.update = false
        this.refresh()
      });

    this.ioMain.onEvent(MainEvent.NEW)
      .subscribe((obj: JSON) => {
        if (obj["task"]) {
          var fresh: Task = new Task(obj)
          var params_array = String(fresh.config).split(',')
          fresh.stub_config = this.replaceNones(params_array)
          // add a new task if it is not in the this.result
          !this.result.includes(fresh, -1) && this.result.push(fresh);

          this.resultData.data = this.result;
        }
      });
  }
}
