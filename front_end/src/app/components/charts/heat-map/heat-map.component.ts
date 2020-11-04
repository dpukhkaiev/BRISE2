import { Component, OnInit, ViewChild, ElementRef } from '@angular/core';

// Service
import {MainEventService} from '../../../core/services/main.event.service';

import { Event as SocketEvent } from '../../../data/client-enums';
import { MainEvent, SubEvent } from '../../../data/client-enums';
import { ExperimentDescription } from '../../../data/experimentDescription.model';

// Plot
import { PlotType as type } from '../../../data/client-enums';
import { Color as colors } from '../../../data/client-enums';
import { Smooth as smooth } from '../../../data/client-enums';
import { Solution } from '../../../data/taskData.model';

interface Configuration {
  configurations: Array<any>;
  results: any;
}

@Component({
  selector: 'hm',
  templateUrl: './heat-map.component.html',
  styleUrls: ['./heat-map.component.scss']
})
export class HeatMapComponent implements OnInit {

  // The experiments results
  result = new Map();

  // The prediction results from model
  prediction = new Map();

  globalConfig: object;
  experimentDescription: ExperimentDescription;
  searchspace: object;

  // Best point
  solution: Solution;
  configWithNones: String;
  // Measured points for the Regresion model from worker-service
  measPoints: Array<Array<any>> = [];
  defaultConfiguration: Configuration;
  sol: any
  dc: any
  results: String

  // Rendering axises
  y: Array<any>;
  x: Array<any>;

  resetRes() {
    this.result.clear();
    this.prediction.clear();
    this.solution = undefined;
    this.measPoints = [];
    this.defaultConfiguration = undefined;
  }

  // Default theme
  theme = {
    type: type[0],
    color: colors[0],
    smooth: smooth[0]
  };

  // Values that possible to use
  public type = type;
  public colors = colors;
  public smooth = smooth;

  // poiner to DOM element #map
  @ViewChild('map') map: ElementRef;

  constructor(
    private ioMain: MainEventService,
  ) {
  }

  ngOnInit() {
    this.initMainEvents();
  }

  isModelType(type: String) {
    return this.experimentDescription && this.experimentDescription.Predictor.models[0].Type == type
  }

  zParser(data: Map<String, any>): Array<Array<any>> {
    // Parse the answears in to array of Y rows
    const z = [];
    this.x &&
    this.y &&
    this.y.forEach(y => { // y - parameter2
      const row = [];
      this.x.forEach(x => { // x - parameter1
        const results = data.get(String([y, x])); // To get horizontal orientation - change to [x,y], vertical - [y,x]
        row.push(results && results[0]); // Get the first result from an array or mark it as undefined.

      });
      z.push(row);
    });
    return z;
  }

  render(): void {
    if (this.experimentDescription.Predictor.ModelType === 'regression') {
      const element = this.map.nativeElement;
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
          x: this.solution && [this.solution.configurations[1]],
          y: this.solution && [this.solution.configurations[0]]
        }
      ];

      const layout = {
        title: 'Heat map results',
        autosize: true,
        showlegend: false,
        xaxis: {
          title: Object.keys(this.searchspace['boundaries'])[1],
          type: 'category',
          autorange: true,
          range: [Math.min(...this.x), Math.max(...this.x)],
          showgrid: true
        },
        yaxis: {
          title: Object.keys(this.searchspace['boundaries'])[0],
          type: 'category',
          autorange: true,
          range: [Math.min(...this.y), Math.max(...this.y)],
          showgrid: true
        }
      };

      Plotly.react(element, data, layout);
    }
  }
  // --------------------------   Main-node
  private initMainEvents(): void {
    //                            Main events

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

    this.ioMain.onEvent(MainEvent.NEW) // New configuration results
      .subscribe((message: any) => {
        if (message.headers['message_subtype'] === 'configuration') {
          const configs = JSON.parse(message.body);
          configs.forEach(configuration => {
            if (configuration) {
              this.result.set(String(configuration['configurations']), configuration['results']);
              this.measPoints.push(configuration['configurations']);
              console.log('New configuration:', configuration);
            } else {
              console.log('Empty configuration');
            }
          });
          this.render();
        }
      });
    this.ioMain.onEvent(MainEvent.FINAL) // The final configuration, suggested by BRISE.
      .subscribe((message: any) => {
        if (message.headers['message_subtype'] === 'configuration') {
          const configs = JSON.parse(message.body);
          configs.forEach(configuration => {
            if (configuration) {
              this.solution = configuration; // In case if only one point solution
              this.configWithNones = JSON.stringify(this.solution.configurations, null, '\t');
              this.configWithNones = this.configWithNones.replace(',,', ',None,');
              this.results = JSON.stringify(this.solution.results)
              this.sol = Object.values(this.solution.results)
              this.dc = Object.values(this.defaultConfiguration.results) 
              console.log('Final:', configs);
            } else {
              console.log('Empty solution');
            }
          });
          this.render();
        }
      });
    this.ioMain.onEvent(MainEvent.DEFAULT) // Default configuration
      .subscribe((message: any) => {
        if (message.headers['message_subtype'] === 'configuration') {
          const configs = JSON.parse(message.body);
          configs.forEach(configuration => {
            if (configuration) {
              this.defaultConfiguration = configuration; // In case if only one point default
              this.result.set(String(configuration['configurations']), configuration['results']);
              this.measPoints.push(configuration['configurations']);
            } else {
              console.log('Empty default');
            }
          });
          console.log('Default:', message.body);
          this.render();
        }
      });

  }

}
