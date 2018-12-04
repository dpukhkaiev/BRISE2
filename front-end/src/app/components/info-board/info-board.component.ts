import { Component, OnInit } from '@angular/core';
// Material
import { MatSnackBar } from '@angular/material';

// Service
import { WsSocketService } from '../../core/services/ws.socket.service';
import { MainSocketService } from '../../core/services/main.socket.service';

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
  default_configuration: any

  globalConfig: object
  experimentDescription: object

  constructor(
    private ioWs: WsSocketService,
    private ioMain: MainSocketService,
    public snackBar: MatSnackBar
  ) { }

  ngOnInit() {
    this.initMainEvents()
  }


  private initMainEvents(): void {

    this.ioMain.onEmptyEvent(MainEvent.CONNECT)
      .subscribe(() => {
        console.log(' info.main: connected');
      });
    this.ioMain.onEmptyEvent(MainEvent.DISCONNECT)
      .subscribe(() => {
        console.log(' info.main: disconnected');
      });

    // ----                     Main events
    this.ioMain.onEvent(MainEvent.DEFAULT)
      .subscribe((obj: any) => {
        if (obj['configuration']) {
          this.default_configuration = obj['configuration'][0]
          let temp: NewsPoint = {'time': Date.now(), 'message': 'Default configuration results received' }
          this.snackBar.open(temp['message'], '×', {
            duration: 3000
          });
          // this.news.add(temp) 
        }
      });

    this.ioMain.onEvent(MainEvent.FINAL)
      .subscribe((obj: any) => {
        if (obj['configuration']) {
          this.solution = obj['configuration'][0]
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
      .subscribe((obj: any) => {
        if (obj['info']) {
          let temp = { 'time': Date.now(), 'message': obj['info'] }
          this.snackBar.open(temp['message'], '×', {
            duration: 3000
          });
          this.news.add(temp)
        }
      });

    this.ioMain.onEvent(MainEvent.EXPERIMENT)
      .subscribe((obj: any) => {
        this.globalConfig = obj['description']['global configuration']
        this.experimentDescription = obj['description']['experiment description']
        let temp = {
          'time': Date.now(), 
          'message': 'The main configurations of the experiment are obtained. Let\'s go! '
        }
        this.snackBar.open(temp['message'], '×', {
          duration: 3000
        });
        this.news.add(temp) 
      });
    this.ioMain.onEvent(MainEvent.NEW)
      .subscribe((obj: any) => {
        obj["task"] && obj["task"].forEach(task => {
          if (task) {
            let temp = {
              'time': Date.now(),
              'message': 'New results for ' + String(task['configurations'])
            }
            this.snackBar.open(temp['message'], '×', {
              duration: 3000
            });
            this.news.add(temp)
          } else {
            console.log("Empty task")
          }
        })
      });
    this.ioMain.onEvent(MainEvent.PREDICTIONS)
      .subscribe((obj: any) => {
        if (obj['configurations']) {
          let temp = {
            'time': Date.now(),
            'message': 'Regression obtained. ' + obj['configurations'].length + ' predictions'
          }
          this.snackBar.open(temp['message'], '×', {
            duration: 3000
          });
          this.news.add(temp)
        }
      });
  }

}
