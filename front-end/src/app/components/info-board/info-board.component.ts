import { Component, OnInit } from '@angular/core';
// Material
import { MatSnackBar } from '@angular/material';

// Service
import { WsSocketService } from '../../core/services/ws.socket.service';
import { MainSocketService } from '../../core/services/main.socket.service';

// Constant
import { MainEvent } from '../../data/client-enums';
import { Solution } from '../../data/taskData.model';


@Component({
  selector: 'info-board',
  templateUrl: './info-board.component.html',
  styleUrls: ['./info-board.component.scss']
})
export class InfoBoardComponent implements OnInit {
  // Steps for expansion. Material.angular
  panelOpenState = false;

  // Information log
  news = new Set()
  
  solution: Solution
  default_task: any

  globalConfig: object
  taskConfig: object

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
    this.ioMain.onEvent(MainEvent.DEFAULT_CONF)
      .subscribe((obj: any) => {
        this.default_task = obj
        let temp = { 'time': Date.now(), 'message': 'Measured default configuration'}
        this.snackBar.open(temp['message'], '×', {
          duration: 3000
        });
        this.news.add(temp) 
      });
    this.ioMain.onEvent(MainEvent.BEST)
      .subscribe((obj: any) => {
        this.solution = obj['best point']
        let temp = { 
          'time': Date.now(), 
          'message': '★★★ The optimum result is found. The best point is reached ★★★'
        }
        this.snackBar.open(temp['message'], '×', {
          duration: 3000
        });
        this.news.add(temp)
      });

    this.ioMain.onEvent(MainEvent.INFO)
      .subscribe((obj: any) => {
        console.log(' Socket: INFO', obj);
        let temp = { 'time': Date.now(), 'message': obj['message'] }
        this.snackBar.open(temp['message'], '×', {
          duration: 3000
        });
        this.news.add(temp)
      });

    this.ioMain.onEvent(MainEvent.MAIN_CONF)
      .subscribe((obj: any) => {
        this.globalConfig = obj['global_config']
        this.taskConfig = obj['task']
        let temp = {
          'time': Date.now(), 
          'message': 'The main configurations of the experiment are obtained.Let\'s go!'
        }
        this.snackBar.open(temp['message'], '×', {
          duration: 3000
        });
        this.news.add(temp) 
      });
    this.ioMain.onEvent(MainEvent.TASK_RESULT)
      .subscribe((obj: any) => {
        let temp = { 
          'time': Date.now(), 
          'message': 'New results for ' + String(obj['configuration']) 
        }
        this.snackBar.open(temp['message'], '×', {
          duration: 3000
        });
        this.news.add(temp)
      });
    this.ioMain.onEvent(MainEvent.REGRESION)
      .subscribe((obj: any) => {
        let temp = { 
          'time': Date.now(), 
          'message': 'Regression obtained. ' + obj['regression'].length + ' predictions' 
        }
        this.snackBar.open(temp['message'], '×', {
          duration: 3000
        });
        this.news.add(temp)
      });
  }

}
