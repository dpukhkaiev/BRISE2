import { Component, OnInit, ViewChild, ElementRef } from '@angular/core';

// Service
// import { WorkerService } from '../../services/worker.service';
import { SocketService } from '../../../core/services/socket.service';
import { MainSocketService } from '../../../core/services/main-socket.service';
import { WorkerService } from '../../../core/services/worker.service';

import { Event } from '../../../data/client-enums';
import { MainEvent } from '../../../data/client-enums';

@Component({
  selector: 'hm-2',
  templateUrl: './heat-map-2.component.html',
  styleUrls: ['./heat-map-2.component.css']
})
export class HeatMap2Component implements OnInit {

  result = new Map()
  prediction = new Map()
  ioConnection: any;
  isRuning: boolean = false
  globalConfig: object
  taskConfig: object
  info

  solution = { 'x': undefined, 'y': undefined }
  measPoints: Array<Array<number>> = []

  y: Array<number>
  x: Array<number>

  @ViewChild('map') map: ElementRef;

  constructor(
    private ws: WorkerService, 
    private io: SocketService, 
    private ioMain: MainSocketService) {  }

  ngOnInit() {
    this.initIoConnection();
    this.initMainConnection();
  }

  zParser(data: Map<String,Number>): Array<Array<Number>> {
    var z = []
    this.y.forEach(y => { // y - threads
      var row = [] 
      this.x.forEach(x => { // x - frequency
        row.push(data.get(String([x, y])))
      });
      z.push(row)
    });
    // console.log("z:", z)
    return z
  }
  // Rendering
  
  render(): void {
    const element = this.map.nativeElement
    const data = [
      {
        z: this.zParser(this.result),
        x: this.x.map(String),
        y: this.y.map(String),
        type: 'heatmap',
        colorscale: 'Portland'
        // zsmooth: 'best'
      },
      {
        type: 'scatter',
        mode: 'markers',
        marker: { color: 'Gold', size: 14, symbol: 'star-open-dot' },
        x: [this.solution.x],
        y: [this.solution.y]
      },
      {
        type: 'scatter',
        mode: 'markers',
        marker: { color: 'grey', size: 9, symbol: 'cross' },
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
        autorange: false,
        range: [Math.min(...this.x), Math.max(...this.x)],
        showgrid: true
      },
      yaxis: {
        title: "Threads",
        type: 'category',
        autorange: false,
        range: [Math.min(...this.y), Math.max(...this.y)],
        showgrid: true
      }
    };

    Plotly.newPlot(element, data, layout);
  }




  // WebSocket
  private initIoConnection(): void {
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

  //                            WebSocket
  // -------------------------- Main-node
  private initMainConnection(): void {

    this.ioMain.onEmptyEvent(MainEvent.CONNECT)
      .subscribe(() => {
        console.log(' hm2.main: connected');
      });
    this.ioMain.onEmptyEvent(MainEvent.DISCONNECT)
      .subscribe(() => {
        console.log(' hm2.main: disconnected');
      });
    // ---- Main events

    this.ioMain.onEvent(MainEvent.DEFAULT_CONF)
      .subscribe((obj: any) => {
        // var data = JSON.parse(obj)
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
