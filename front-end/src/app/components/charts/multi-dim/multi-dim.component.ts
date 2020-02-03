import { Component, OnInit, ElementRef, ViewChild } from '@angular/core';

// Service
import {MainEventService} from '../../../core/services/main.event.service';

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
  searchspace: object
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
    private ioMain: MainEventService,
  ) { }

  ngOnInit() {
    this.initMainEvents();
  }

  isModelType(type: String) {
    // used in HTML template
    return this.experimentDescription && this.experimentDescription.ModelConfiguration.ModelType == type
  }

  // --------------------------   Main-node
  private initMainEvents(): void {

    //                            Main events
    this.ioMain.onEvent(MainEvent.EXPERIMENT)
      .subscribe((message: any) => {
        if (message.headers['message_subtype'] === 'description') {
          let obj = JSON.parse(message.body)
          this.resetRes()
          this.experimentDescription = obj['experiment description']
          this.searchspace = obj['searchspace_description']
          let resultParams = this.experimentDescription['TaskConfiguration']['TaskParameters']
          let rangeValues = Object.values(this.searchspace["boundaries"])

          this.resultParamsRange = this.zip(resultParams, rangeValues)
          this.resultParamsRange.set('result', undefined) // range for results is undefined
        }

      });

    this.ioMain.onEvent(MainEvent.DEFAULT) // Default configuration
      .subscribe((message: any) => {
        if (message.headers['message_subtype'] === 'configuration') {
          let configs = JSON.parse(message.body)
          configs.forEach(configuration => {
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
          console.log('Default:', configs)
        }
      });

    this.ioMain.onEvent(MainEvent.NEW) // New task results
      .subscribe((message: any) => {
        if (message.headers['message_subtype'] === 'configuration') {
          let configs = JSON.parse(message.body)
          configs.forEach(configuration => {
        if (configuration) {
            let boundaries = Object.values(this.searchspace['boundaries'])
            for (let i = 0; i < this.experimentDescription.DomainDescription.HyperparameterNames.length; ++i){
              if (configuration['configurations'][i] == null){
                configuration['configurations'][i] = boundaries[i][0]
              }
            }
            let point = this.zip(this.experimentDescription['TaskConfiguration']['TaskParameters'], configuration['configurations'])
            point.set('result', configuration.results[0])
            this.allPoints.add(point)
            this.render()
          }
          else {
            console.log("Empty task")
          }
          })
        }
      });
    this.ioMain.onEvent(MainEvent.FINAL) // The final configuration, suggested by BRISE.
      .subscribe((message: any) => {
        if (message.headers['message_subtype'] === 'configuration') {
          let configs = JSON.parse(message.body)
          configs.forEach(configuration => {
            if (configuration) {
              this.solution = configuration // In case if only one point solution
              console.log('Final:', configs)
            } else {
              console.log("Empty solution")
            }
          })
        }
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
