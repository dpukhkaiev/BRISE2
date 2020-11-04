import {Component, OnInit} from '@angular/core';

import {MatBottomSheet} from '@angular/material';

// Enums
import {MainEvent} from '../../data/client-enums';
import {ExperimentDescription} from '../../data/experimentDescription.model';

// Service
import {MainEventService} from '../../core/services/main.event.service';
import {MainClientService} from '../../core/services/main.client.service';

// Download Popup
import {DownloadPopUp} from '../download-pop-up/download-pop-up.component';


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
    private eventService: MainClientService,
    private ioMain: MainEventService,
    private DownloadOption: MatBottomSheet,
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
      this.eventService.startMain()
      this.isRuning = true
      this.isFinish = false
    }
  }
  stopMain(): any {
    if (this.isRuning == true) {
      this.eventService.stopMain()
      this.isRuning = false
    }
  }
  private initMainEvents(): void {
    this.ioMain.onEvent(MainEvent.FINAL)
      .subscribe((message: any) => {
        this.isRuning = false
        this.isFinish = true
      });
    this.ioMain.onEvent(MainEvent.EXPERIMENT)
      .subscribe((message: any) => {
        if (message.headers['message_subtype'] === 'description') {
          this.experimentDescription = JSON.parse(message.body)['experiment_description'];
        }
      });
  }
}
