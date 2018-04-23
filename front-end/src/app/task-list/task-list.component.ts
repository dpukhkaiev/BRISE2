import { Component, OnInit } from '@angular/core';

// Service
import { WorkerService } from '../services/worker.service';
import { Task } from '../data/taskData.model';

@Component({
  selector: 'app-task-list',
  templateUrl: './task-list.component.html',
  styleUrls: ['./task-list.component.css'],
  providers: [WorkerService]
  
})
export class TaskListComponent implements OnInit {
  
  stack 
  result 
  focus
  // inject the dependency associated 
  // with the dependency injection token `WorkerService`
  constructor(private ws: WorkerService) { }

  ngOnInit() {
    this.stackList()
    this.resList()
  }

  stackList() {
    // upd stack
    this.ws.getStack()
      .subscribe((stack) => {
        console.log("Stack:", stack);
        this.stack = stack;
      }
    );
  }
  resList() {
    // upd results
    this.ws.getAllResult()
      .subscribe((res) => {
        this.result = Object.values(res["results"]).map((t) => new Task(t));
      }
    );
  }

  taskInfo(id: string): any {
     this.ws.getTaskById(id)
      .subscribe((res) => {
        this.focus = res["result"];
        this.focus.time = res["time"]
      }
      );
  }

}
