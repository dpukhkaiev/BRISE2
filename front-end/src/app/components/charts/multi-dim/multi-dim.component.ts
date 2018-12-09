import { Component, OnInit, ElementRef, ViewChild } from '@angular/core';

// Service
import { WsSocketService } from '../../../core/services/ws.socket.service';
import { MainSocketService } from '../../../core/services/main.socket.service';

import { Event as SocketEvent } from '../../../data/client-enums';
import { MainEvent, SubEvent } from '../../../data/client-enums';
import { ExperimentDescription } from '../../../data/experimentDescription.model';

// Plot
import { PlotType as type } from '../../../data/client-enums';
import { Color as colors } from '../../../data/client-enums';
import { Smooth as smooth } from '../../../data/client-enums';
import {Solution, Task} from '../../../data/taskData.model';


interface PointExp {[Key: string]: any;}

interface string_parameters {
  'length': any
  'parameters_digits': Array<any>
  'parameters_names': Array<any>
}

@Component({
  selector: 'multi-dim',
  templateUrl: './multi-dim.component.html',
  styleUrls: ['./multi-dim.component.scss']
})
export class MultiDimComponent implements OnInit {

  // The experements results
  result = new Map()

  // Best point
  solution: Solution
  // Measured points for the Regresion model from worker-service
  measPoints: Array<Array<number>> = []
  defaultConfiguration: PointExp

  globalConfig: object
  list_of_parameters = []
  experimentDescription: ExperimentDescription

  dimensions: Array<any>

  // TODO: Rewrite the structure for a valid answer. Use the appropriate pattern
  // for string parameters
  // ranges: {}



  array_for_colours: Array<any>

  ranges: {[key: string]: string_parameters;} = {}

  allRes = new Set<PointExp>()
  BestPoint = new Set<PointExp>()

  resetRes() {
    this.result.clear()
    this.solution = undefined
  }

  // poiner to DOM element #multi
  @ViewChild('multi') multi: ElementRef;

  constructor(
    private ioWs: WsSocketService,
    private ioMain: MainSocketService,
  ) {  }

  ngOnInit() {
    this.initWsEvents();
    this.initMainEvents();
  }

  isModelType(type: String) {
    return this.experimentDescription && this.experimentDescription.ModelConfiguration.ModelType == type
  }


  //                              WebSocket
  // --------------------------   Worker-service
  private initWsEvents(): void {
    this.ioWs.initSocket();
    this.ioWs.onEvent(SocketEvent.CONNECT)
      .subscribe(() => {
        console.log(' multi-dim: connected');
        this.ioWs.reqForAllRes();
      });
    this.ioWs.onEvent(SocketEvent.DISCONNECT)
      .subscribe(() => {
        console.log(' multi-dim: disconnected');
      });
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
        this.globalConfig = obj['description']['global configuration']
        this.experimentDescription = obj['description']['experiment description']

        for (let index in this.experimentDescription['TaskConfiguration']['TaskParameters']) {
          this.list_of_parameters.push(this.experimentDescription['TaskConfiguration']['TaskParameters'][index])
        }
        console.log('Name of all parameters: ' + this.list_of_parameters)

        for (let index in this.experimentDescription['DomainDescription']['AllConfigurations']) {
          if (typeof this.experimentDescription['DomainDescription']['AllConfigurations'][index][0] !== "number") {
            this.ranges[String(this.list_of_parameters[index])] = {
              'length': this.experimentDescription['DomainDescription']['AllConfigurations'][index].length,
              'parameters_digits': Array.apply(null, {length: this.experimentDescription['DomainDescription']['AllConfigurations'][index].length}).map(Number.call, Number),
              'parameters_names': this.experimentDescription['DomainDescription']['AllConfigurations'][index]
            }
          }
        }
      });

    this.ioMain.onEvent(MainEvent.NEW) // New task results
      .subscribe((obj: any) => {
        obj["configuration"] && obj["configuration"].forEach(configuration => {
          if (configuration) {
            this.result.set(String(configuration['configurations']), configuration['results'])
            this.measPoints.push(configuration['configurations'])
            console.log('New:', configuration)

            let tmp: PointExp = {}
            for (let index in this.list_of_parameters) {
              let is_exists_in_ranges = false
              for (let key in this.ranges) {
                if (key == this.list_of_parameters[index]) {
                  is_exists_in_ranges = true
                }
              }
              if (is_exists_in_ranges) {
                tmp[this.list_of_parameters[index]] = this.ranges[this.list_of_parameters[index]]['parameters_names'].indexOf(configuration['configurations'][index])
              }
              else {
                tmp[this.list_of_parameters[index]] = configuration['configurations'][index]
                // tmp.this.list_of_parameters[index] =
              }
            }
            tmp['result'] = configuration['results'][0]
            this.allRes.add(tmp)

            let chart_dimensions = new Set()
            for (let index in this.list_of_parameters) {
              let is_exists_in_ranges = false
              for (let key in this.ranges) {
                if (key == this.list_of_parameters[index]) {
                  is_exists_in_ranges = true
                }
              }
              let dict_dimension = {}
              if (is_exists_in_ranges) {
                dict_dimension = {
                  label: this.list_of_parameters[index],
                  range: [0, this.ranges[this.list_of_parameters[index]]['length'] - 1],
                  values: Array.from(this.allRes).map(i => Number(i[this.list_of_parameters[index]])),
                  tickvals: this.ranges[this.list_of_parameters[index]]['parameters_digits'],
                  ticktext: this.ranges[this.list_of_parameters[index]]['parameters_names']
                }
              }
              else {
                dict_dimension = {
                  label: this.list_of_parameters[index],
                  range: [Math.min(...Array.from(this.allRes).map(i => Number(i[this.list_of_parameters[index]]))), Math.max(...Array.from(this.allRes).map(i => Number(i[this.list_of_parameters[index]])))],
                  values: Array.from(this.allRes).map(i => Number(i[this.list_of_parameters[index]]))
                }
              }
              chart_dimensions.add(dict_dimension)
            }
            let dict_result = {
              label: 'result',
              range: [Math.min(...Array.from(this.allRes).map(i => Number(i['result']))), Math.max(...Array.from(this.allRes).map(i => Number(i['result'])))],
              values: Array.from(this.allRes).map(i => Number(i['result']))
            }
            chart_dimensions.add(dict_result)
            this.render(chart_dimensions)
          }
          else {
            console.log("Empty task")
          }
        })
      });
  }

  render(char_dimensions) {
    const element = this.multi.nativeElement
    var trace = [{
      type: 'parcoords',
      line: {
        showscale: true,
        reversescale: true,
        colorscale: 'Jet',
        cmin: Math.min(...Array.from(this.allRes).map(i => Number(i['result']))),
        cmax: Math.max(...Array.from(this.allRes).map(i => Number(i['result']))),
        color: Array.from(this.allRes).map(i => Number(i['result']))
      },
      dimensions: Array.from(char_dimensions).map(i => (i))
    }];

    Plotly.react(element, trace)
  }

}
