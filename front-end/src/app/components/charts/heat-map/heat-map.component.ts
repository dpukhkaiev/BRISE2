import { Component, OnInit, ViewChild, ElementRef } from '@angular/core';

// Service
// import { RestService } from '../../services/worker.service';
import { WsSocketService } from '../../../core/services/ws.socket.service';
import { MainSocketService } from '../../../core/services/main.socket.service';
import { RestService as mainREST} from '../../../core/services/rest.service';

import { Event } from '../../../data/client-enums';
import { MainEvent } from '../../../data/client-enums';

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
  taskConfig: object

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

    window.onresize = () => Plotly.relayout(this.map.nativeElement, {})
  }

  zParser(data: Map<String,Number>): Array<Array<Number>> {
    // Parse the answears in to array of Y rows
    var z = []
    this.y.forEach(y => { // y - threads
      var row = [] 
      this.x.forEach(x => { // x - frequency
        row.push(data.get(String([x, y])))
      });
      z.push(row)
    });
    return z
  }
  
  render(): void {
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
        x: this.measPoints.map(arr => arr[0]),
        y: this.measPoints.map(arr => arr[1]) 
      },
      { // Best point. Solution
        type: 'scatter',
        mode: 'markers',
        marker: { color: 'Gold', size: 16, symbol: 'star' },
        x: this.solution && [this.solution.configuration[0]],
        y: this.solution && [this.solution.configuration[1]]
      }
    ];

    var layout = {
      title: 'Heat map results',
      autosize: true,
      showlegend: false,
      xaxis: {
        title: "Frequency",
        type: 'category',
        autorange: true,
        range: [Math.min(...this.x), Math.max(...this.x)],
        showgrid: true
      },
      yaxis: {
        title: "Threads",
        type: 'category',
        autorange: true,
        range: [Math.min(...this.y), Math.max(...this.y)],
        showgrid: true
      }
    };

    Plotly.react(element, data, layout);
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
        this.x = obj['task']['DomainDescription']['AllConfigurations'][0] // frequency
        this.y = obj['task']['DomainDescription']['AllConfigurations'][1] // threads
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

        this.render()
      });
  }

  // HTTP: Main-node
  startMain(): any {
    if (this.isRuning == false) {
      this.stopMain(); // Сlean the old tread experiment
      this.mainREST.startMain()
        .subscribe((res) => {
          console.log('Main start:', res)
          this.isRuning = true
        }
        );
    }
  }
  stopMain(): any {
    if (this.isRuning == true) {
      this.mainREST.stopMain()
        .subscribe((res) => {
          console.log('Main stop:', res)
          this.isRuning = false
        }
        );
    }
  }

}
