import { Component, OnInit, ElementRef, ViewChild } from '@angular/core';

// Service
import { MainSocketService } from '../../../core/services/main.socket.service';

// Events
import { MainEvent } from '../../../data/client-enums';
import { Task } from '../../../data/taskData.model';
import { TaskConfig } from '../../../data/taskConfig.model';
import { Solution } from '../../../data/taskData.model';



@Component({
  selector: 'multi-dim',
  templateUrl: './multi-dim.component.html',
  styleUrls: ['./multi-dim.component.scss']
})
export class MultiDimComponent implements OnInit {

  // The experements results
  result = new Map()
  // Best point 
  solution: Solution
  default_task

  globalConfig: object
  taskConfig: TaskConfig

  dimensions: Array<any>

  resetRes() {
    this.result.clear()
    this.solution = undefined
  }

  // poiner to DOM element #map
  @ViewChild('multi') multi: ElementRef;

  constructor(private ioMain: MainSocketService) { }

  ngOnInit() {
    this.initMainEvents()
  }

  render() {
    const element = this.multi.nativeElement
    var trace = {
      type: 'parcoords',
      line: {
        color: 'blue'
      },
      dimensions: [{
        range: [1, 5],
        constraintrange: [1, 2],
        label: 'A',
        values: [1,4]
      }, {    
        range: [1,5],
        label: 'B',
        values: [3,1.5],
        tickvals: [1.5,3,4.5]
      }, {
        range: [1, 5],
        label: 'C',
        values: [2,4],
        tickvals: [1,2,4,5],
        ticktext: ['text 1','text 2','text 4','text 5']
      }, {
        range: [1, 5],
        label: 'D',
        values: [4,2]
      }]
    };

    var data = [trace]
    Plotly.plot(element, data);
  }
  // main-node socket events
  private initMainEvents(): void {
    this.ioMain.onEvent(MainEvent.BEST)
      .subscribe((obj: any) => {
        this.solution = obj['best point']
      });

    this.ioMain.onEvent(MainEvent.MAIN_CONF)
      .subscribe((obj: any) => {
        this.globalConfig = obj['global_config']
        this.taskConfig = obj['task']
        this.dimensions = this.taskConfig.ExperimentsConfiguration.ResultStructure
        this.resetRes() // Clear the old data and results
      });
    this.ioMain.onEvent(MainEvent.DEFAULT_CONF)
      .subscribe((obj: any) => {
        this.default_task = obj
        this.result.set(String(obj['configuration']), obj['result'])
        this.render()
      });
    this.ioMain.onEvent(MainEvent.TASK_RESULT)
      .subscribe((obj: any) => {
        this.result.set(String(obj['configuration']), obj['result'])
        this.render()
      });
  }

}
