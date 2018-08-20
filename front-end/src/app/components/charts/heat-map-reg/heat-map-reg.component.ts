import { Component, OnInit, ViewChild, ElementRef } from '@angular/core';

// Service
import { MainSocketService } from '../../../core/services/main-socket.service';

import { MainEvent } from '../../../data/client-enums';

@Component({
  selector: 'hm-reg',
  templateUrl: './heat-map-reg.component.html',
  styleUrls: ['./heat-map-reg.component.css']
})
export class HeatMapRegComponent implements OnInit {

  // Variables
  prediction = new Map()
  globalConfig: object
  taskConfig: object
  solution = { 'x': undefined, 'y': undefined }
  measured = {'x': [], 'y': []}
  theme = 'Portland'
  type = 'contour'
  y: Array<number>
  x: Array<number>
  @ViewChild('reg') reg: ElementRef;

  constructor(private ioMain: MainSocketService) { }

  ngOnInit() {
    this.initMainConnection();
  }

  // Init conection
  private initMainConnection(): void {

    this.ioMain.onEmptyEvent(MainEvent.CONNECT)
      .subscribe(() => {
        console.log(' reg.main: reg connected');
      });
    this.ioMain.onEmptyEvent(MainEvent.DISCONNECT)
      .subscribe(() => {
        console.log(' reg.main: reg disconnected');
      });
    // ---- Main events

    this.ioMain.onEvent(MainEvent.BEST)
      .subscribe((obj: any) => {
        console.log(' Socket: BEST', obj);
        this.solution.x = obj['best point']['configuration'][0]
        this.solution.y = obj['best point']['configuration'][1]

        this.measured.x = obj['best point']['measured points'].map(arr => arr[0])
        this.measured.y = obj['best point']['measured points'].map(arr => arr[1])
        console.log("Measured", this.measured.x, this.measured.y)
        this.regrRender()
      });

    this.ioMain.onEvent(MainEvent.MAIN_CONF)
      .subscribe((obj: any) => {
        this.globalConfig = obj['global_config']
        this.taskConfig = obj['task']
        this.x = obj['task']['DomainDescription']['AllConfigurations'][0] // frequency
        this.y = obj['task']['DomainDescription']['AllConfigurations'][1] // threads
      });

    this.ioMain.onEvent(MainEvent.REGRESION)
      .subscribe((obj: any) => {
        console.log(' Socket: REGRESION', obj);
        this.prediction.set(String(obj['regression']['configuration']), obj['regression']['prediction'])
        // setTimeout(this.regrRender(), 0);
        this.regrRender()
      });

  }

  // Rendering
  regrRender(): void {
    console.log("Reg render>", this.prediction)
    const regresion = this.reg.nativeElement
    const data = [
      {
        // z: [[1, 20, 30], [20, 1, 60], [30, 60, 1]],
        z: this.zParser(this.prediction),
        x: this.x.map(String),
        y: this.y.map(String),
        type: this.type,
        colorscale: this.theme
      },
      {
        type: 'scatter',
        mode: 'markers',
        marker: { color: 'Gold', size: 12, symbol: 'star-open-dot' },
        x: this.solution.x,
        y: this.solution.y
      },
      {
        type: 'scatter',
        mode: 'markers',
        marker: { color: 'grey', size: 9, symbol: 'cross' },
        x: this.measured.x,
        y: this.measured.y
      }
    ];

    var layout = {
      title: 'Regresion',
      xaxis: { title: "Frequency",
        type: 'category',
        autorange: false,
        range: [Math.min(...this.x), Math.max(...this.x)] 
      },
      yaxis: { title: "Threads",
        type: 'category',
        autorange: false,
        range: [Math.min(...this.y), Math.max(...this.y)]  }
    };

    Plotly.newPlot(regresion, data, layout);
  }
  zParser(data: Map<String, Number>): Array<Array<Number>> {
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

}
