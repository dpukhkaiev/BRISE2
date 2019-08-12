import { Component, OnInit, ViewChild, ElementRef } from '@angular/core';

// Service
// import { WorkerService } from '../../services/worker.service';
import { SocketService } from '../../services/socket.service';
import { MainSocketService } from '../../services/main-socket.service';
import { Task } from '../../data/taskData.model';
import { Event } from '../../data/client-enums';
import { MainEvent } from '../../data/client-enums';

@Component({
  selector: 'hm-2',
  templateUrl: './heat-map-2.component.html',
  styleUrls: ['./heat-map-2.component.css']
})
export class HeatMap2Component implements OnInit {
  @ViewChild('map') el: ElementRef;
  result = []
  ioConnection: any;

  constructor(private io: SocketService, private ioMain: MainSocketService) {  }

  ngOnInit() {
    this.initIoConnection();
    this.initMainConnection();
    this.render()
  }
  // Rendering
  render():void {
    const element = this.el.nativeElement
    const data = [
      {
        z: [[1, 20, 30], [20, 1, 60], [30, 60, 1]],
        // z: this.result,
        type: 'heatmap',
        colorscale: 'Jet',
      }
    ];

    var layout = {
      title: 'Heat map results'
    };

    Plotly.newPlot(element, data, layout);
  }
  // WebSocket
  private initIoConnection(): void {
    this.io.initSocket();

    // Fresh updates. Each time +1 task
    this.ioConnection = this.io.onResults()
      .subscribe((obj: JSON) => {
        var fresh: Task = new Task(obj)

        var r = fresh.hasOwnProperty('meta') && fresh['meta']['result']
        var delta = !!r && [r['threads'], r['frequency'], r['energy']]
        !this.result.includes(delta, -1) && this.result.push(delta);
        // console.log("---- Delta", delta)
      });

    // Observer for stack and all results from workers service
    this.ioConnection = this.io.onAllResults()
      .subscribe((obj: any) => {
        console.log("onAllResults ::", JSON.parse(obj))
        var data = JSON.parse(obj)
        this.result = (data.hasOwnProperty('res') && data['res'].length) ? data['res'].map((t) => new Task(t)) : [];
      });

    this.io.onEvent(Event.CONNECT)
      .subscribe(() => {
        console.log(' Socket: connected');
        // get init data
        this.io.reqForAllRes();
      });
    this.io.onEvent(Event.DISCONNECT)
      .subscribe(() => {
        console.log(' Socket: disconnected');
    });
  }

  //                            WebSocket
  // -------------------------- Main-node
  private initMainConnection(): void {
    this.ioMain.initSocket()

    this.ioMain.onEvent(MainEvent.CONNECT)
      .subscribe((obj: any) => {
        console.log(' Socket: connected', obj);
      });
    this.ioMain.onEvent(MainEvent.DISCONNECT)
      .subscribe((obj: any) => {
        console.log(' Socket: disconnected', obj);
      });

    this.ioMain.onEvent(MainEvent.DEFAULT_CONF)
      .subscribe((obj: any) => {
        var data = JSON.parse(obj)
        console.log(' Socket: DEFAULT_CONF', data);
      });

    this.ioMain.onEvent(MainEvent.MAIN_CONF)
      .subscribe((obj: any) => {
        var data = JSON.parse(obj)
        console.log(' Socket: MAIN_CONF', data);
      });
    this.ioMain.onEvent(MainEvent.BEST)
      .subscribe((obj: any) => {
        var data = JSON.parse(obj)
        console.log(' Socket: BEST', data);
      });
    this.ioMain.onEvent(MainEvent.REGRESION)
      .subscribe((obj: any) => {
        console.log(' Socket: REGRESION', obj);
      });
    this.ioMain.onEvent(MainEvent.TASK_RESULT)
      .subscribe((obj: any) => {
        console.log(' Socket: TASK_RESULT', obj);
      });
    this.ioMain.onEvent(MainEvent.INFO)
      .subscribe((obj: any) => {
        var data = JSON.parse(obj)
        console.log(' Socket: INFO', data);
      });

  }

}
