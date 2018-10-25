import { Component, OnInit, ElementRef, ViewChild } from '@angular/core';

// Service
import { MainSocketService } from '../../../core/services/main.socket.service';

// Events
import { MainEvent } from '../../../data/client-enums';
import { Task } from '../../../data/taskData.model';
import { TaskConfig } from '../../../data/taskConfig.model';
import { Solution } from '../../../data/taskData.model';

interface PointExp {
  laplace_correction: any
  estimation_mode: any
  bandwidth_selection: any
  bandwidth: any
  minimum_bandwidth: any
  number_of_kernels: any
  use_application_grid: any
  application_grid_size: any

  accuracy: any;
}


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
  default_task: any

  globalConfig: object
  taskConfig: TaskConfig

  dimensions: Array<any>

  // TODO: Rewrite the structure for a valid answer. Use the appropriate pattern
  ranges: {
    'laplace_correction': {
      'length': any,
      'parameters_digits': Array<any>,
      'parameters_names': Array<any>
    },
    'estimation_mode': {
      'length': any,
      'parameters_digits': Array<any>,
      'parameters_names': Array<any>
    },
    'bandwidth_selection': {
      'length': any,
      'parameters_digits': Array<any>,
      'parameters_names': Array<any>
    },
    'use_application_grid': {
      'length': any,
      'parameters_digits': Array<any>,
      'parameters_names': Array<any>
    }
  }

  allRes = new Set<PointExp>()
  BestPoint = new Set<PointExp>()

  isModelType(type: String) {
    return this.taskConfig && this.taskConfig.ModelConfiguration.ModelType == type
  }

  resetRes() {
    this.result.clear()
    this.solution = undefined
  }

  // poiner to DOM element #multi
  @ViewChild('multi') multi: ElementRef;

  constructor(private ioMain: MainSocketService) { }

  ngOnInit() {
    this.initMainEvents()
  }


  // main-node socket events
  private initMainEvents(): void {
    this.ioMain.onEvent(MainEvent.BEST)
      .subscribe((obj: any) => {
        this.solution = obj['best point']
        let tmp: PointExp = {
          'laplace_correction': obj['best point']['configuration'][0],
          'estimation_mode': obj['best point']['configuration'][1],
          'bandwidth_selection': obj['best point']['configuration'][2],
          'bandwidth': obj['best point']['configuration'][3],
          'minimum_bandwidth': obj['best point']['configuration'][4],
          'number_of_kernels': obj['best point']['configuration'][5],
          'use_application_grid': obj['best point']['configuration'][6],
          'application_grid_size': obj['best point']['configuration'][7],

          'accuracy': obj['best point']['result']
        }
        this.BestPoint.add(tmp)
        this.render()
      });

    this.ioMain.onEvent(MainEvent.MAIN_CONF)
      .subscribe((obj: any) => {
        this.globalConfig = obj['global_config']
        this.taskConfig = obj['task']
        this.dimensions = obj['task']['DomainDescription']['AllConfigurations']
        // this.resetRes() // Clear the old data and results
        this.ranges = {
          'laplace_correction': {
            'length': obj['task']['DomainDescription']['AllConfigurations'][0].length,
            'parameters_digits': Array.apply(null, {length: obj['task']['DomainDescription']['AllConfigurations'][0].length}).map(Number.call, Number),
            'parameters_names': obj['task']['DomainDescription']['AllConfigurations'][0]
          },
          'estimation_mode': {
            'length': obj['task']['DomainDescription']['AllConfigurations'][1].length,
            'parameters_digits': Array.apply(null, {length: obj['task']['DomainDescription']['AllConfigurations'][1].length}).map(Number.call, Number),
            'parameters_names': obj['task']['DomainDescription']['AllConfigurations'][1]
          },
          'bandwidth_selection': {
            'length': obj['task']['DomainDescription']['AllConfigurations'][2].length,
            'parameters_digits': Array.apply(null, {length: obj['task']['DomainDescription']['AllConfigurations'][2].length}).map(Number.call, Number),
            'parameters_names': obj['task']['DomainDescription']['AllConfigurations'][2]
          },
          'use_application_grid': {
            'length': obj['task']['DomainDescription']['AllConfigurations'][6].length,
            'parameters_digits': Array.apply(null, {length: obj['task']['DomainDescription']['AllConfigurations'][6].length}).map(Number.call, Number),
            'parameters_names': obj['task']['DomainDescription']['AllConfigurations'][6]
          }
        }
      });
    this.ioMain.onEvent(MainEvent.DEFAULT_CONF)
      .subscribe((obj: any) => {
        this.default_task = obj
        this.result.set(String(obj['configuration']), obj['result'])
      });

    this.ioMain.onEvent(MainEvent.TASK_RESULT)
      .subscribe((obj: any) => {
        this.result.set(String(obj['configuration']), obj['result'])

        let tmp: PointExp = {
          'laplace_correction': this.ranges['laplace_correction']['parameters_names'].indexOf(obj['configuration'][0]),
          'estimation_mode': this.ranges['estimation_mode']['parameters_names'].indexOf(obj['configuration'][1]),
          'bandwidth_selection': this.ranges['bandwidth_selection']['parameters_names'].indexOf(obj['configuration'][2]),
          'bandwidth': obj['configuration'][3],
          'minimum_bandwidth': obj['configuration'][4],
          'number_of_kernels': obj['configuration'][5],
          'use_application_grid': this.ranges['use_application_grid']['parameters_names'].indexOf(obj['configuration'][6]),
          'application_grid_size': obj['configuration'][7],

          'accuracy': (obj['result'])
        }
        this.allRes.add(tmp)
        this.render()
      });
    // this.ioMain.onEvent(MainEvent.MAIN_CONF)
    //   .subscribe((obj: any) => {
    //     this.allRes.clear()
    //     this.solution = undefined
    //   });
  }
  render() {
    const element = this.multi.nativeElement
    var trace = [{
      type: 'parcoords',
      line: {
        showscale: true,
        reversescale: true,
        colorscale: 'Jet',
        cmin: 0,
        cmax: 1,
        color: Array.from(this.allRes).map(i => Number(i['accuracy']))
      },
      dimensions: [{
        label: 'laplace_correction',
        range: [0, this.ranges['laplace_correction']['length'] - 1],
        values: Array.from(this.allRes).map(i =>  Number(i['laplace_correction'])),
        tickvals: this.ranges['laplace_correction']['parameters_digits'],
        ticktext: this.ranges['laplace_correction']['parameters_names']
      }, {
        label: 'estimation_mode',
        range: [0, this.ranges['estimation_mode']['length'] - 1],
        values: Array.from(this.allRes).map(i =>  Number(i['estimation_mode'])),
        tickvals: this.ranges['estimation_mode']['parameters_digits'],
        ticktext: this.ranges['estimation_mode']['parameters_names']
      }, {
        label: 'bandwidth_selection',
        range: [0, this.ranges['bandwidth_selection']['length'] - 1],
        values: Array.from(this.allRes).map(i =>  Number(i['bandwidth_selection'])),
        tickvals: this.ranges['bandwidth_selection']['parameters_digits'],
        ticktext: this.ranges['bandwidth_selection']['parameters_names']
      }, {
        label: 'bandwidth',
        range: [Math.min(...Array.from(this.allRes).map(i =>  Number(i['bandwidth']))), Math.max(...Array.from(this.allRes).map(i =>  Number(i['bandwidth'])))],
        values: Array.from(this.allRes).map(i =>  Number(i['bandwidth']))
      }, {
        label: 'minimum_bandwidth',
        range: [Math.min(...Array.from(this.allRes).map(i =>  Number(i['minimum_bandwidth']))), Math.max(...Array.from(this.allRes).map(i =>  Number(i['minimum_bandwidth'])))],
        values: Array.from(this.allRes).map(i =>  Number(i['minimum_bandwidth']))
      }, {
        label: 'number_of_kernels',
        range: [Math.min(...Array.from(this.allRes).map(i =>  Number(i['number_of_kernels']))), Math.max(...Array.from(this.allRes).map(i =>  Number(i['number_of_kernels'])))],
        values: Array.from(this.allRes).map(i =>  Number(i['number_of_kernels']))
      }, {
        label: 'use_application_grid',
        range: [0, this.ranges['use_application_grid']['length'] - 1],
        values: Array.from(this.allRes).map(i =>  Number(i['use_application_grid'])),
        tickvals: this.ranges['use_application_grid']['parameters_digits'],
        ticktext: this.ranges['use_application_grid']['parameters_names']
      },{
        label: 'application_grid_size',
        range: [Math.min(...Array.from(this.allRes).map(i =>  Number(i['application_grid_size']))), Math.max(...Array.from(this.allRes).map(i =>  Number(i['application_grid_size'])))],
        values: Array.from(this.allRes).map(i =>  Number(i['application_grid_size']))
      }]
    }];

    Plotly.react(element, trace)
  }

}
