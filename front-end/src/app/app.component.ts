import { Component, OnInit } from '@angular/core';
import { TaskConfig } from './data/taskConfig.model';
import { MainEvent } from './data/client-enums';
import {RestService as mainREST, RestService} from "./core/services/rest.service";
import {WsSocketService} from "./core/services/ws.socket.service";
import {MainSocketService} from "./core/services/main.socket.service";
import {MatTableDataSource} from "@angular/material";


@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss']
})
export class AppComponent implements OnInit {
  // constructor() { }
  // Flag for runing main-node
  isRuning: boolean = false

  constructor(private mainREST: mainREST, private ws: RestService, private io: WsSocketService, private ioMain: MainSocketService) {

  }
  public ngOnInit() {
    this.initMainEvents()
  }

  taskConfig: TaskConfig
  isModelType(type: String) {
    return this.taskConfig && this.taskConfig.ModelConfiguration.ModelType == type
  }
  // --------------------- SOCKET ---------------
  private initMainEvents(): void {
    this.ioMain.onEvent(MainEvent.MAIN_CONF)
      .subscribe((obj: any) => {
        this.taskConfig = obj['task']
        this.isRuning = false
      });
  }


  // HTTP: Main-node
  startMain(): any {
    if (this.isRuning == false) {
      this.stopMain(); // Сlean the old tread experiment
      this.mainREST.startMain()
        .subscribe((res) => {
            console.log('Main start:', res)
            this.isRuning = true
          }
        );
    }
  }
  stopMain(): any {
    if (this.isRuning == true) {
      this.mainREST.stopMain()
        .subscribe((res) => {
            console.log('Main stop:', res)
            this.isRuning = false
          }
        );
    }
  }

}
