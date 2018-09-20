import { Component, OnInit, ViewChild, ElementRef } from '@angular/core';

// Service
// import { RestService } from '../../services/worker.service';
import { WsSocketService } from '../../../core/services/ws.socket.service';
import { MainSocketService } from '../../../core/services/main.socket.service';
import { RestService as mainREST} from '../../../core/services/rest.service';

import { Event } from '../../../data/client-enums';
import { MainEvent } from '../../../data/client-enums';
import { TaskConfig } from '../../../data/taskConfig.model';

// Plot
import { PlotType as type } from '../../../data/client-enums';
import { Color as colors } from '../../../data/client-enums';
import { Smooth as smooth } from '../../../data/client-enums';
import { Solution } from '../../../data/taskData.model';

interface Configuration {
  configuration: Array<any>;
  result: any;
}

@Component({
  selector: 'hm-2',
  templateUrl: './heat-map.component.html',
  styleUrls: ['./heat-map.component.scss']
})
export class HeatMapComponent implements OnInit {
  
  // The experements results
  result = new Map()

  // The prediction results from model
  prediction = new Map()

  // Flag for runing main-node
  isRuning: boolean = false

  globalConfig: object 
  taskConfig: TaskConfig

  // Best point 
  solution: Solution
  // Measured points for the Regresion model from worker-service
  measPoints: Array<Array<number>> = []
  default_task: Configuration

  // Rendering axises
  y: Array<number>
  x: Array<number>

  resetRes() {
    this.result.clear()
    this.prediction.clear()
    this.solution = undefined
    this.measPoints = []
    this.default_task = undefined
  }


  // Default theme
  theme = {
    type: type[0],
    color: colors[0],
    smooth: smooth[0]
  }

  // Values that possible to use
  public type = type
  public colors = colors
  public smooth = smooth

  // poiner to DOM element #map
  @ViewChild('map') map: ElementRef;

  constructor(
    private mainREST: mainREST, 
    private ioWs: WsSocketService, 
    private ioMain: MainSocketService,
  ) {  }

  ngOnInit() {
    this.initWsEvents();
    this.initMainEvents();

    // window.onresize = () => Plotly.relayout(this.map.nativeElement, {})
  }
  isModelType(type: String) {
    return this.taskConfig && this.taskConfig.ModelConfiguration.ModelType == type
  }

  zParser(data: Map<String,Number>): Array<Array<Number>> {
    // Parse the answears in to array of Y rows
    var z = []
    this.x && 
    this.y && 
    this.y.forEach(y => { // y - threads
      var row = [] 
      this.x.forEach(x => { // x - frequency
        row.push(data.get(String([y, x]))) // change [x,y] or [y,x] if require horizontal or vertical orientation
      });
      z.push(row)
    });
    return z
  }
  
  render(): void {
    if (this.taskConfig.ModelConfiguration.ModelType == "regression") {
      const element = this.map.nativeElement
      const data = [
        { // defined X and Y axises with data, type and color
          z: this.zParser(this.result),
          x: this.x.map(String),
          y: this.y.map(String),
          type: this.theme.type,
          colorscale: this.theme.color,
          zsmooth: this.theme.smooth
        }, 
        { // Measured points
          type: 'scatter',
          mode: 'markers',
          marker: { color: 'grey', size: 7, symbol: 'cross' },
          x: this.measPoints.map(arr => arr[1]),
          y: this.measPoints.map(arr => arr[0]) 
        },
        { // Best point. Solution
          type: 'scatter',
          mode: 'markers',
          hoverinfo: 'none',
          showlegend: false,
          marker: { color: 'Gold', size: 16, symbol: 'star' },
          x: this.solution && [this.solution.configuration[1]],
          y: this.solution && [this.solution.configuration[0]]
        }
      ];

      var layout = {
        title: 'Heat map results',
        autosize: true,
        showlegend: false,
        xaxis: {
          title: "Threads",
          type: 'category',
          autorange: true,
          range: [Math.min(...this.x), Math.max(...this.x)],
          showgrid: true
        },
        yaxis: {
          title: "Frequency",
          type: 'category',
          autorange: true,
          range: [Math.min(...this.y), Math.max(...this.y)],
          showgrid: true
        }
      };

      Plotly.react(element, data, layout);
    }
  }




  //                              WebSocket
  // --------------------------   Worker-service
  private initWsEvents(): void {
    this.ioWs.initSocket();
    this.ioWs.onEvent(Event.CONNECT)
      .subscribe(() => {
        console.log(' hm2.workerService: connected');
        this.ioWs.reqForAllRes();
      });
    this.ioWs.onEvent(Event.DISCONNECT)
      .subscribe(() => {
        console.log(' hm2.workerService: disconnected');
    });
  }

  //                              WebSocket
  // --------------------------   Main-node
  private initMainEvents(): void {

    this.ioMain.onEmptyEvent(MainEvent.CONNECT)
      .subscribe(() => {
        console.log(' hm.main: connected');
      });
    this.ioMain.onEmptyEvent(MainEvent.DISCONNECT)
      .subscribe(() => {
        console.log(' hm.main: disconnected');
      });

    // ----                     Main events
    this.ioMain.onEvent(MainEvent.BEST)
      .subscribe((obj: any) => {
        console.log(' Socket: BEST', obj);
        this.solution = obj['best point']
        this.render()
        this.isRuning = false 
      });

    this.ioMain.onEvent(MainEvent.INFO)
      .subscribe((obj: any) => {
        console.log(' Socket: INFO', obj);
      });

    this.ioMain.onEvent(MainEvent.MAIN_CONF)
      .subscribe((obj: any) => {
        this.globalConfig = obj['global_config']
        this.taskConfig = obj['task']
        this.y = obj['task']['DomainDescription']['AllConfigurations'][0] // frequency
        this.x = obj['task']['DomainDescription']['AllConfigurations'][1] // threads
        this.resetRes() // Clear the old data and results
        console.log(' Socket: MAIN_CONF', obj);
      });
    this.ioMain.onEvent(MainEvent.DEFAULT_CONF)
      .subscribe((obj: any) => {
        console.log(' Socket: DEFAULT_task', obj);
        this.default_task = obj
        this.result.set(String(obj['configuration']), obj['result'])
        this.measPoints.push(obj['configuration'])
        this.render()
      });
    this.ioMain.onEvent(MainEvent.TASK_RESULT)
      .subscribe((obj: any) => {
        this.result.set(String(obj['configuration']), obj['result'])
        this.measPoints.push(obj['configuration'])
        console.log('TaskRes:', obj)
        this.render()
      });
  }

}
