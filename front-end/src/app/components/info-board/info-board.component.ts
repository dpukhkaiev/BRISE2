import { Component, OnInit } from '@angular/core';
// Material
import { MatSnackBar } from '@angular/material';

// Service
import {MainEventService} from '../../core/services/main.event.service';

// Constant
import { MainEvent } from '../../data/client-enums';
import { Solution } from '../../data/taskData.model';

interface NewsPoint  {
  'time': any;
  'message': string;
}

@Component({
  selector: 'info-board',
  templateUrl: './info-board.component.html',
  styleUrls: ['./info-board.component.scss']
})
export class InfoBoardComponent implements OnInit {
  // Steps for expansion. Material.angular
  panelOpenState = false;

  // Information log
  news: Set<NewsPoint> = new Set()

  solution: Solution
  configWithNones: String
  default_configuration: any

  globalConfig: object
  experimentDescription: object
  searchspace: object

  constructor(
    private ioMain: MainEventService,
    public snackBar: MatSnackBar
  ) { }

  ngOnInit() {
    this.initMainEvents()
  }

  refresh(){
    this.solution = undefined
    this.news = new Set()
  }

  private initMainEvents(): void {

    // ----                     Main events
    this.ioMain.onEvent(MainEvent.DEFAULT)
      .subscribe((message: any) => {
        if (message.headers['message_subtype'] === 'configuration') {
          let obj = JSON.parse(message.body)
          this.default_configuration = obj[0]
          let temp: NewsPoint = {'time': Date.now(), 'message': 'Default configuration results received' }
          this.snackBar.open(temp['message'], '×', {
            duration: 3000
          });
        }
      });

    this.ioMain.onEvent(MainEvent.FINAL)
      .subscribe((message: any) => {
        if (message.headers['message_subtype'] === 'configuration') {
          let obj = JSON.parse(message.body)
          this.solution = obj[0];
          this.configWithNones = String(this.solution.configurations)
          this.configWithNones = this.configWithNones.replace(",,", ",None,")
          let temp = {
            'time': Date.now(),
            'message': '★★★ The optimum result is found. The best point is reached ★★★'
          }
          this.snackBar.open(temp['message'], '×', {
            duration: 3000
          });
          this.news.add(temp)
        }
      });

    this.ioMain.onEvent(MainEvent.LOG) // For information messages
      .subscribe((message: any) => {
        if (message.headers['message_subtype'] === 'info' || message.headers['message_subtype'] === 'error') {
          let obj = JSON.parse(message.body)
          let temp = {'time': Date.now(), 'message': obj}
          this.snackBar.open(temp['message'], '×', {
            duration: 3000
          });
          this.news.add(temp)
        }
      });

    this.ioMain.onEvent(MainEvent.EXPERIMENT)
      .subscribe((message: any) => {
        if (message.headers['message_subtype'] === 'description') {
          let obj = JSON.parse(message.body)
          this.globalConfig = obj['global configuration']
          this.experimentDescription = obj['experiment description']
          this.searchspace = obj['searchspace_description']
          this.refresh()
          this.searchspace['size'] = parseFloat(this.searchspace['size'])
          let temp = {
            'time': Date.now(),
            'message': 'The main configurations of the experiment are obtained. Let\'s go! '
          }
          this.snackBar.open(temp['message'], '×', {
            duration: 3000
          });
          this.news.add(temp)
          console.log("Experiment description: ", obj)
          }
      });
    this.ioMain.onEvent(MainEvent.NEW)
      .subscribe((message: any) => {
        if (message.headers['message_subtype'] === 'configuration') {
          let configs = JSON.parse(message.body)
          configs.forEach(configuration => {
            if (configuration) {
              let temp = {
                'time': Date.now(),
                'message': 'New results for ' + String(configuration['configurations'])
              }
              this.snackBar.open(temp['message'], '×', {
                duration: 3000
              });
              this.news.add(temp)
            } else {
              console.log("Empty configuration")
            }
          })
        }
      });
    this.ioMain.onEvent(MainEvent.PREDICTIONS)
      .subscribe((message: any) => {
        if (message.headers['message_subtype'] === 'configuration') {
          let obj = JSON.parse(message.body)
          let temp = {
            'time': Date.now(),
            'message': 'Prediction obtained. ' + obj.length + ' predictions'
          }
          this.snackBar.open(temp['message'], '×', {
            duration: 3000
          });
          this.news.add(temp)
        }
      });
  }

}
