import { Component, OnInit, ViewChild, ElementRef } from '@angular/core';

// Service
// import { WorkerService } from '../../services/worker.service';
import { SocketService } from '../../../core/services/socket.service';
import { MainSocketService } from '../../../core/services/main-socket.service';
import { WorkerService } from '../../../core/services/worker.service';

import { Event } from '../../../data/client-enums';
import { MainEvent } from '../../../data/client-enums';

// Plot
import { PlotType as type } from '../../../data/client-enums';
import { Color as colors } from '../../../data/client-enums';
import { Smooth as smooth } from '../../../data/client-enums';


@Component({
  selector: 'hm-2',
  templateUrl: './heat-map.component.html',
  styleUrls: ['./heat-map.component.css']
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
  info

  // Best point 
  solution = { 'x': undefined, 'y': undefined }
  // Measured points for the Regresion model from worker-service
  measPoints: Array<Array<number>> = []

  // Rendering axises
  y: Array<number>
  x: Array<number>

  // Default theme
  theme = {
    type: type[0],
    color: colors[0],
    smooth: smooth[0]
  }
  public type = type
  public colors = colors
  public smooth = smooth

  // poiner to DOM element #map
  @ViewChild('map') map: ElementRef;

  constructor(
    private ws: WorkerService, 
    private io: SocketService, 
    private ioMain: MainSocketService,
  ) {  }

  ngOnInit() {
    this.initWsEvents();
    this.initMainEvents();
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
      { // Best point. Solution
        type: 'scatter',
        mode: 'markers',
        marker: { color: 'Gold', size: 16, symbol: 'star-dot' },
        x: [this.solution.x],
        y: [this.solution.y]
      },
      { // Measured points
        type: 'scatter',
        mode: 'markers',
        marker: { color: 'grey', size: 7, symbol: 'cross' },
        x: this.measPoints.map(arr => arr[0]),
        y: this.measPoints.map(arr => arr[1]) 
      }
    ];

    var layout = {
      title: 'Heat map results',
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

    Plotly.newPlot(element, data, layout);
  }




  //                              WebSocket
  // --------------------------   Worker-service
  private initWsEvents(): void {
    this.io.initSocket();

    // Fresh updates. Each time +1 task
    // this.ioConnection = this.io.onResults()
    //   .subscribe((obj: JSON) => {
    //     var fresh: Task = new Task(obj)

    //     var r = fresh.hasOwnProperty('meta') && fresh['meta']['result']
    //     var delta = !!r && [r['threads'], r['frequency'], r['energy']]
    //     !this.result.includes(delta, -1) && this.result.push(delta);
    //     // console.log("---- Delta", delta)
    //   });

    // Observer for stack and all results from workers service
    // this.ioConnection = this.io.onAllResults()
    //   .subscribe((obj: any) => {
    //     console.log("onAllResults ::", JSON.parse(obj))
    //     var data = JSON.parse(obj)
    //     this.result = (data.hasOwnProperty('res') && data['res'].length) ? data['res'].map((t) => new Task(t)) : [];
    //   });

    this.io.onEvent(Event.CONNECT)
      .subscribe(() => {
        console.log(' hm2.workerService: connected');
        this.io.reqForAllRes();
      });
    this.io.onEvent(Event.DISCONNECT)
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
    this.ioMain.onEvent(MainEvent.DEFAULT_CONF)
      .subscribe((obj: any) => {
        console.log(' Socket: DEFAULT_task', obj);
        this.measPoints.push(obj['conf'])
        this.render()
      });
    this.ioMain.onEvent(MainEvent.BEST)
      .subscribe((obj: any) => {
        console.log(' Socket: BEST', obj);
        this.solution.x = obj['best point']['configuration'][0]
        this.solution.y = obj['best point']['configuration'][1]
        this.render()
      });

    this.ioMain.onEvent(MainEvent.INFO)
      .subscribe((obj: any) => {
        console.log(' Socket: INFO', obj);
        this.info = obj
      });

    this.ioMain.onEvent(MainEvent.MAIN_CONF)
      .subscribe((obj: any) => {
        this.globalConfig = obj['global_config']
        this.taskConfig = obj['task']
        this.x = obj['task']['DomainDescription']['AllConfigurations'][0] // frequency
        this.y = obj['task']['DomainDescription']['AllConfigurations'][1] // threads
        console.log(' Socket: MAIN_CONF', obj);
        console.log(' MAIN_CONF: this.x', this.x);
        console.log(' MAIN_CONF: this.y', this.y);
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
      this.ws.startMain()
        .subscribe((res) => {
          console.log('Main start:', res)
          this.isRuning = true
        }
        );
    }
  }
  stopMain(): any {
    if (this.isRuning == true) {
      this.ws.stopMain()
        .subscribe((res) => {
          console.log('Main stop:', res)
          this.isRuning = false
        }
        );
    }
  }

}
