import { Component, OnInit, ViewChild, ElementRef } from '@angular/core';

// Service
import {MainEventService} from '../../../core/services/main.event.service';

// Model
import { MainEvent } from '../../../data/client-enums';
import { ExperimentDescription } from '../../../data/experimentDescription.model';

// Plot
import { PlotType as type } from '../../../data/client-enums';
import { Color as colors } from '../../../data/client-enums';
import { Smooth as smooth } from '../../../data/client-enums';

import { Solution } from '../../../data/taskData.model';


@Component({
  selector: 'hm-reg',
  templateUrl: './heat-map-reg.component.html',
  styleUrls: ['./heat-map-reg.component.scss']
})
export class HeatMapRegComponent implements OnInit {

  // Variables
  prediction = new Map()
  solution: Solution
  measPoints: Array<Array<any>> = []

  resetRes() {
    this.prediction.clear()
    this.solution = undefined
    this.measPoints = []
  }

  @ViewChild('reg') reg: ElementRef;

  globalConfig: object
  experimentDescription: ExperimentDescription
  searchspace: object
  // Rendering axises
  y: Array<any>
  x: Array<any>

  // Default theme
  theme = {
    type: type[0],
    color: colors[0],
    smooth: smooth[0]
  }
  public type = type
  public colors = colors
  public smooth = smooth

  constructor(private ioMain: MainEventService) {
  }

  ngOnInit() {
    this.initMainConnection();
    // window.onresize = () => Plotly.relayout(this.reg.nativeElement, {})
  }

  isModelType(type: String) {
    return this.experimentDescription && this.experimentDescription.Predictor.models[0].Type == type
  }

  // Rendering
  regrRender(): void {
    let regression = this.reg.nativeElement
    const data = [
      {
        z: this.zParser(this.prediction),
        x: this.x,
        y: this.y,
        type: this.theme.type,
        colorscale: this.theme.color,
        zsmooth: this.theme.smooth
      },
      {
        type: 'scatter',
        mode: 'markers',
        name: 'measured points',
        marker: { color: 'grey', size: 8, symbol: 'x' },
        x: this.measPoints.map(arr => arr[1]),
        y: this.measPoints.map(arr => arr[0])
      },
      {
        type: 'scatter',
        mode: 'markers',
        name: 'solution',
        marker: { color: 'Gold', size: 16, symbol: 'star' },
        x: this.solution && [this.solution.configurations[1]],
        y: this.solution && [this.solution.configurations[0]]
      }
    ];

    var layout = {
      title: 'Regression',
      autosize: true,
      showlegend: false,
      xaxis: { title: "Threads",
        type: 'category',
        autorange: true,
        range: [Math.min(...this.x), Math.max(...this.x)]
      },
      yaxis: { title: "Frequency",
        type: 'category',
        autorange: true,
        range: [Math.min(...this.y), Math.max(...this.y)]  }
    };

    Plotly.react(regression, data, layout);
  }
  zParser(data: Map<String, any>): Array<Array<any>> {
    var z = []
    this.y.forEach(y => {
      var row = []
      this.x.forEach(x => {
        row.push(data.get(String([y, x]))[0]) // change [x,y] or [y,x] if require horizontal or vertical orientation
                                          // Get the first result from an array
      });
      z.push(row)
    });
    return z
  }

  // Init conection
  private initMainConnection(): void {
    // ---- Main events

    this.ioMain.onEvent(MainEvent.FINAL)
      .subscribe((message: any) => {
        if (message.headers['message_subtype'] === 'configuration') {
          let configs = JSON.parse(message.body)
          if (configs.length > 1) console.log("WARNING! More than one solution received!")
          let result = configs[0]
          if (result) {
              this.solution = result // In case if only one point solution
              this.measPoints.push(result['configurations'])
              console.log("Measured", this.measPoints.length)
              this.prediction.size && this.regrRender()
            } else { console.log("Empty solution") }
        }
      });

    this.ioMain.onEvent(MainEvent.EXPERIMENT)
      .subscribe((message: any) => {
        if (message.headers['message_subtype'] === 'description') {
          const obj = JSON.parse(message.body);
          this.resetRes();
          this.globalConfig = obj['global_configuration'];
          this.experimentDescription = obj['experiment_description'];
          this.searchspace = obj['searchspace_description'];
          let boundaryObj: Object;
          boundaryObj = this.searchspace['boundaries'];
          this.x = Object.values(boundaryObj)[1];
          this.y = Object.values(boundaryObj)[0];
        }
      });

    this.ioMain.onEvent(MainEvent.PREDICTIONS)
      .subscribe((message: any) => {
        if (message.headers['message_subtype'] === 'configuration') {
          const configs = JSON.parse(message.body)
          configs.forEach(point => {
            if (point) {
              this.prediction.set(String(point['configurations']), point['results']);
            } else {
              console.log('Empty prediction point')
            }
          });
          console.log(' Prediction points:', configs.length);
          this.prediction.size && this.regrRender();
        }
      });

  }

}
