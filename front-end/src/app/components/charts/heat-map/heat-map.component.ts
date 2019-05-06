import { Component, OnInit, ViewChild, ElementRef } from '@angular/core';

// Service
import { MainSocketService } from '../../../core/services/main.socket.service';

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
  
  // The experements results
  result = new Map()

  // The prediction results from model
  prediction = new Map()

  globalConfig: object 
  experimentDescription: ExperimentDescription

  // Best point 
  solution: Solution
  // Measured points for the Regresion model from worker-service
  measPoints: Array<Array<number>> = []
  defaultConfiguration: Configuration

  // Rendering axises
  y: Array<number>
  x: Array<number>

  resetRes() {
    this.result.clear()
    this.prediction.clear()
    this.solution = undefined
    this.measPoints = []
    this.defaultConfiguration = undefined
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
    private ioMain: MainSocketService,
  ) {  }

  ngOnInit() {
    this.initMainEvents();
  }
  
  isModelType(type: String) {
    return this.experimentDescription && this.experimentDescription.ModelConfiguration.ModelType == type
  }

  zParser(data: Map<String,Number>): Array<Array<Number>> {
    // Parse the answears in to array of Y rows
    var z = []
    this.x && 
    this.y && 
    this.y.forEach(y => { // y - threads
      var row = [] 
      this.x.forEach(x => { // x - frequency
        let results = data.get(String([y, x])) // To get horizontal orientation - change to [x,y], vertical - [y,x]
        row.push(results && results[0]) // Get the first result from an array or mark it as undefined.

      });
      z.push(row)
    });
    return z
  }
  
  render(): void {
    if (this.experimentDescription.ModelConfiguration.ModelType == "regression") {
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
          x: this.solution && [this.solution.configurations[1]],
          y: this.solution && [this.solution.configurations[0]]
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
  // --------------------------   Main-node
  private initMainEvents(): void {

    this.ioMain.onEmptyEvent(MainEvent.CONNECT)
      .subscribe(() => {
        console.log(' heat-map: connected');
      });
    this.ioMain.onEmptyEvent(MainEvent.DISCONNECT)
      .subscribe(() => {
        console.log(' heat-map: disconnected');
      });

    //                            Main events

    this.ioMain.onEvent(MainEvent.EXPERIMENT)
      .subscribe((obj: any) => {
        this.resetRes()
        this.globalConfig = obj['description']['global configuration']
        this.experimentDescription = obj['description']['experiment description']
        this.y = this.experimentDescription['DomainDescription']['AllConfigurations'][0] // frequency
        this.x = this.experimentDescription['DomainDescription']['AllConfigurations'][1] // threads
      });

    this.ioMain.onEvent(MainEvent.NEW) // New configuration results
      .subscribe((obj: any) => {
        obj["configuration"] && obj["configuration"].forEach(configuration => {
          if (configuration) {
            this.result.set(String(configuration['configurations']), configuration['results'])
            this.measPoints.push(configuration['configurations'])
            console.log('New configuration:', configuration)
          } else {
            console.log("Empty configuration")
          }
        })
        this.render()
      });
    this.ioMain.onEvent(MainEvent.FINAL) // The final configuration, suggested by BRISE.
      .subscribe((obj: any) => {
        obj["configuration"] && obj["configuration"].forEach(configuration => {
          if (configuration) {
            this.solution = configuration // In case if only one point solution
            console.log('Final:', obj["configuration"])
          } else {
            console.log("Empty solution")
          }
        })
        this.render()
      });
    this.ioMain.onEvent(MainEvent.DEFAULT) // Default configuration
      .subscribe((obj: any) => {
        obj["configuration"] && obj["configuration"].forEach(configuration => {
          if (configuration) {
            this.defaultConfiguration = configuration // In case if only one point default
            this.result.set(String(configuration['configurations']), configuration['results'])
            this.measPoints.push(configuration['configurations'])
          } else {
            console.log("Empty default")
          }
        })
        console.log('Default:', obj["configuration"])
        this.render()
      });

  }

}
