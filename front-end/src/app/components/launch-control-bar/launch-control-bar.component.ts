import { Component, OnInit } from '@angular/core';

import { MatBottomSheet } from '@angular/material';

// Enums
import { MainEvent } from '../../data/client-enums';
import { ExperimentDescription } from '../../data/experimentDescription.model';

// Service
import { RestService as mainREST } from '../../core/services/rest.service';
import { MainSocketService } from '../../core/services/main.socket.service';

// Download Popup
import {DownloadPopUp} from '../download-pop-up/download-pop-up.component'


// -- Main
@Component({
  selector: 'launch-control-bar',
  templateUrl: './launch-control-bar.component.html',
  styleUrls: ['./launch-control-bar.component.scss']
})
export class LaunchControlBarComponent implements OnInit {

  // Flag for runing main-node
  isRuning: boolean = false
  // Flag for finish experiment
  isFinish: boolean = false

  experimentDescription: ExperimentDescription

  constructor(
    private mainREST: mainREST, 
    private ioMain: MainSocketService,
    private DownloadOption: MatBottomSheet
  ) { }

  ngOnInit() {
    this.initMainEvents();
  }

  openDownloadOption(): void {
    this.DownloadOption.open(DownloadPopUp);
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

  // Socket
  private initMainEvents(): void {
    this.ioMain.onEvent(MainEvent.FINAL) 
    .subscribe((obj: any) => {
      this.isRuning = false
      this.isFinish = true
    });
    this.ioMain.onEvent(MainEvent.EXPERIMENT)
      .subscribe((obj: any) => {
        this.experimentDescription = obj['description']['experiment description'];
      });
  }

}
