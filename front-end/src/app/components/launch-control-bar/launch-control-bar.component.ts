import { Component, OnInit } from '@angular/core';

import { RestService as mainREST } from '../../core/services/rest.service';
import { MainSocketService } from '../../core/services/main.socket.service';

import { MainEvent } from '../../data/client-enums';

import { ExperimentDescription } from '../../data/experimentDescription.model';

@Component({
  selector: 'launch-control-bar',
  templateUrl: './launch-control-bar.component.html',
  styleUrls: ['./launch-control-bar.component.scss']
})
export class LaunchControlBarComponent implements OnInit {

  // Flag for runing main-node
  isRuning: boolean = false
  experimentDescription: ExperimentDescription
  constructor(private mainREST: mainREST, private ioMain: MainSocketService) { }

  ngOnInit() {
    this.initMainEvents()
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

  private initMainEvents(): void {
    this.ioMain.onEvent(MainEvent.EXPERIMENT)
      .subscribe((obj: any) => {
        this.experimentDescription = obj['description']['experiment description'];
      });
  }

}
