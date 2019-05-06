import { Component, OnInit, ElementRef, ViewChild } from '@angular/core';

// Service
import { MainSocketService } from '../../../core/services/main.socket.service';

import { Event as SocketEvent } from '../../../data/client-enums';
import { MainEvent } from '../../../data/client-enums';
import { ExperimentDescription } from '../../../data/experimentDescription.model';
import { Solution } from '../../../data/taskData.model';

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

  list_of_parameters = []
  experimentDescription: ExperimentDescription
  default_configuration: PointExp

  ranges: {[key: string]: string_parameters;} = {}

  allRes = new Set<PointExp>()

  // Best point
  solution: Solution

  resetRes() {
    this.list_of_parameters = []
    this.experimentDescription = undefined
    this.default_configuration = undefined
    this.ranges = {}
    this.allRes.clear()
    this.solution = undefined
  }

  // poiner to DOM element #multi
  @ViewChild('multi') multi: ElementRef;

  constructor(
    private ioMain: MainSocketService,
  ) {  }

  ngOnInit() {
    this.initMainEvents();
  }

  isModelType(type: String) {
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

        this.list_of_parameters = this.experimentDescription['TaskConfiguration']['TaskParameters']
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

    this.ioMain.onEvent(MainEvent.DEFAULT) // Default configuration
      .subscribe((obj: any) => {
        obj["configuration"] && obj["configuration"].forEach(configuration => {
          if (configuration) {
            this.default_configuration = configuration // In case if only one point default
            let chart_dimensions = this.add_dimensions_data(configuration)
            this.render(chart_dimensions)
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
            console.log('New:', configuration)

            let chart_dimensions = this.add_dimensions_data(configuration)

            this.render(chart_dimensions)
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

  add_dimensions_data(configuration) {
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
          values: Array.from(this.allRes).map(i => Number(i[this.list_of_parameters[index]]))
        }
      }
      chart_dimensions.add(dict_dimension)
    }
    let dict_result = {
      label: 'result',
      values: Array.from(this.allRes).map(i => Number(i['result']))
    }
    chart_dimensions.add(dict_result)

    return chart_dimensions
  }



  render(chart_dimensions) {
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
      dimensions: Array.from(chart_dimensions)
    }];

    Plotly.react(element, trace)
  }

}
