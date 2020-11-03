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
  parameter_names: any
  keyParam: any
  rootParam: any
  currentDiagram: any
  experiment: any

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


  constructor(
    private ioMain: MainEventService,
  ) { }

  ngOnInit() {
    this.initMainEvents();
  }

  isModelType(type: String) {
    // used in HTML template
    return this.experimentDescription && this.experimentDescription.Predictor.models[0].Type == type
  }

  // --------------------------   Main-node
  private initMainEvents(): void {

    //                            Main events
    this.ioMain.onEvent(MainEvent.EXPERIMENT)
      .subscribe((message: any) => {
        if (message.headers['message_subtype'] === 'description') {
          let obj = JSON.parse(message.body)
          this.resetRes()
          this.experimentDescription = obj['experiment_description']
          this.searchspace = obj['searchspace_description']
          this.rootParam = this.searchspace["root_parameters_list"]
          this.experiment = this.searchspace["name"]
          let priorities = this.experimentDescription["TaskConfiguration"]["ObjectivesPriorities"]
          let i = priorities.indexOf(Math.max(...priorities));
          this.keyParam = this.experimentDescription["TaskConfiguration"]["Objectives"][i]
        }

      });

    this.ioMain.onEvent(MainEvent.DEFAULT) // Default configuration
      .subscribe((message: any) => {
        if (message.headers['message_subtype'] === 'configuration') {
          let configs = JSON.parse(message.body)
          configs.forEach(configuration => {
            if (configuration) {
              this.chose(configuration)
              this.defaultPoint = configuration // In case if only one point default
              var alphas = new Array();;
              this.parameter_names.forEach(key => {
                alphas.push(configuration.configurations[key])
              })
              let point = this.zip(this.parameter_names, alphas)
              point.set('result', configuration.results[this.keyParam])
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
            this.chose(configuration)
            var alphas = new Array();;
            this.parameter_names.forEach(key => {
              alphas.push(configuration.configurations[key])
            })
            let point = this.zip(this.parameter_names, alphas)
            point.set('result', configuration.results[this.keyParam])
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
    const element = document.getElementById(this.currentDiagram)
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

    var layout = {
      title: {
        text: this.currentDiagram,
        font: {
          size: 20
        },
        xref: 'paper',
        x: 0.05,
      }
    }

    Plotly.react(element, trace, layout)
  }

  dimmensionsData() {
    let data = [] // accommodate dimensional obj
    this.resultParamsRange.size && this.resultParamsRange.forEach((range: Array<any>, param: String)=>{
      if (param != this.experiment){
        let dim = this.factoryDimension(param, range) // make dimensional object through all results by one parameter
        data.push(dim) // add new dimension object for plotting
      }
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
      dim.tickvals = Array.from(Array(valuesRange.length).keys())
      dim.ticktext = valuesRange
      dim.values = dimValues.map(value => dim.tickvals[dim.ticktext.indexOf(value)])
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
  chose(configuration){
    this.currentDiagram = configuration.configurations[this.experiment]
    let index = this.rootParam.indexOf(this.currentDiagram)
    this.parameter_names = Object.keys(this.searchspace["boundaries"][index]["Boundaries"])
    let rangeValues = Object.values(this.searchspace["boundaries"][index]["Boundaries"])
    this.resultParamsRange = this.zip(this.parameter_names, rangeValues)
    this.resultParamsRange.set('result', undefined) // range for results is undefined
  }
}
