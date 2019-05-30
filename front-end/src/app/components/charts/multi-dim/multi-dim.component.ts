import { Component, OnInit, ElementRef, ViewChild } from '@angular/core';

// Service
import { MainSocketService } from '../../../core/services/main.socket.service';

import { MainEvent } from '../../../data/client-enums';
import { ExperimentDescription } from '../../../data/experimentDescription.model';
import { Solution } from '../../../data/taskData.model';

interface PointExp {[Key: string]: any}

@Component({
  selector: 'multi-dim',
  templateUrl: './multi-dim.component.html',
  styleUrls: ['./multi-dim.component.scss']
})
export class MultiDimComponent implements OnInit {

  // Experiment configurations
  experimentDescription: ExperimentDescription
  resultParamsRange: any // Map. results parameters with possible ranges

  // Best point
  allPoints = new Set<PointExp>()
  // Default point
  defaultPoint: PointExp

  // Proposed solution from model
  solution: Solution

  resetRes() {
    this.experimentDescription = undefined
    this.defaultPoint = undefined
    this.allPoints.clear()
    this.solution = undefined
  }

  // poiner to DOM element #multi
  @ViewChild('multi') multi: ElementRef;

  constructor(
    private ioMain: MainSocketService,
  ) { }

  ngOnInit() {
    this.initMainEvents();
  }

  isModelType(type: String) {
    // used in HTML template
    return this.experimentDescription && this.experimentDescription.ModelConfiguration.ModelType == type
  }

  //                              WebSocket
  // --------------------------   Main-node
  private initMainEvents(): void {

    this.ioMain.onEmptyEvent(MainEvent.CONNECT)
      .subscribe(() => {
        console.log(' multi-dim: connected');
      });
    this.ioMain.onEmptyEvent(MainEvent.DISCONNECT)
      .subscribe(() => {
        console.log(' multi-dim: disconnected');
      });


    //                            Main events
    this.ioMain.onEvent(MainEvent.EXPERIMENT)
      .subscribe((obj: any) => {
        this.resetRes()
        this.experimentDescription = obj['description']['experiment description']
        let resultParams = this.experimentDescription['TaskConfiguration']['TaskParameters']
        let rangeValues = this.experimentDescription["DomainDescription"]["AllConfigurations"]

        this.resultParamsRange = this.zip(resultParams, rangeValues)
        this.resultParamsRange.set('result', undefined) // range for results is undefined
      });

    this.ioMain.onEvent(MainEvent.DEFAULT) // Default configuration
      .subscribe((obj: any) => {
        obj["configuration"] && obj["configuration"].forEach(configuration => {
          if (configuration) {
            this.defaultPoint = configuration // In case if only one point default
            let point = this.zip(this.experimentDescription['TaskConfiguration']['TaskParameters'], configuration['configurations'])
            point.set('result', configuration.results[0])
            this.allPoints.add(point)
            this.render()
          } else {
            console.log("Empty default")
          }
        })
        console.log('Default:', obj["configuration"])
      });

    this.ioMain.onEvent(MainEvent.NEW) // New task results
      .subscribe((obj: any) => {
        obj["configuration"] && obj["configuration"].forEach(configuration => {
          if (configuration) {
            let point = this.zip(this.experimentDescription['TaskConfiguration']['TaskParameters'], configuration['configurations'])
            point.set('result', configuration.results[0])
            // console.log('New:', point)
            this.allPoints.add(point) 
            this.render()
          }
          else {
            console.log("Empty task")
          }
        })
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
      });
  }

  render(){
    const element = this.multi.nativeElement
    var trace = [{
      type: 'parcoords',
      line: {
        showscale: true,
        // reversescale: true,
        colorscale: 'Jet',
        color: this.unpack(this.allPoints, 'result')
      },
      dimensions: this.dimmensionsData()
    }];

    Plotly.react(element, trace)
  }

  dimmensionsData() {
    let data = [] // accommodate dimensional obj
    this.resultParamsRange.size && this.resultParamsRange.forEach((range: Array<any>, param: String)=>{
      let dim = this.factoryDimension(param, range) // make dimensional object through all results by one parameter
      data.push(dim) // add new dimension object for plotting
    })
    return data 
  }
  factoryDimension(parameter: String, valuesRange: Array<any> = null) {
    let dimValues = this.unpack(this.allPoints, parameter)
    let dim: any = {
      values: dimValues,
      label: parameter.replace(/_/g, " ")
    }
    // If values are not numerical.
    // TODO: reduced to one type. There are no logical transformations
    if (valuesRange && (typeof valuesRange[0] == "string" || typeof valuesRange[0] == "boolean")) {
      dim.tickvals = dimValues.map((_, i) => i)
      dim.values = dimValues.map(value => valuesRange.indexOf(value)),
      dim.ticktext = valuesRange
    }
    return dim
  }
  // Returns an array of values by key from all dictionaries
  unpack(set, key) {
    let selection = []
    set.forEach(point=>{  // point is key value store - Map
      selection.push(point.get(key));
    });
    return selection
  }
  // merge key and values arrays in key
  zip(keys:Array<any>, values:Array<any>) {
    let result = new Map()
    if (keys.length == values.length) {
      keys.forEach((key, i) => result.set(key, values[i]))
    }
    return result
  }
}
