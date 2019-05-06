import { Component, OnInit, ViewChild } from '@angular/core';

import { MatPaginator, MatTable, MatSort, MatTableDataSource } from '@angular/material';
import { animate, state, style, transition, trigger } from '@angular/animations';

// Service
import { RestService } from '../../core/services/rest.service';
import { MainSocketService } from '../../core/services/main.socket.service';


import { Task } from '../../data/taskData.model';
import { Event } from '../../data/client-enums';
import { MainEvent } from '../../data/client-enums';

import { ExperimentDescription } from '../../data/experimentDescription.model';


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
 
  focus: any
  displayedColumns: string[] = ['id', 'run', 'result'];
  experimentDescription: ExperimentDescription

  public resultData: MatTableDataSource<Task>

  constructor(private ws: RestService, private ioMain: MainSocketService) {
    this.resultData = new MatTableDataSource(this.result);

    this.resultData.filterPredicate = (task, filter) => {
      return JSON.stringify(task).includes(filter)
    }

    console.log("Task list BO init")
  }

  ngOnInit() {
    this.resultData.paginator = this.paginator;
    this.resultData.sort = this.sort;
    this.initMainEvents()
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

  // --------------------- SOCKET ---------------
  private initMainEvents(): void {
    this.ioMain.onEvent(MainEvent.EXPERIMENT)
      .subscribe((obj: any) => {
        this.experimentDescription = obj['description']['experiment description'];
      });
    
    this.ioMain.onEvent(MainEvent.NEW)
      .subscribe((obj: JSON) => {
        var fresh: Task = new Task(obj)
        !this.result.includes(fresh, -1) && this.result.push(fresh);
        this.resultData.data = this.result;
      });
  }
}
