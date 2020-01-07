import { Component, OnInit } from '@angular/core';

// Enums
import { MainEvent } from '../../data/client-enums';
import { ExperimentDescription } from '../../data/experimentDescription.model';

// Service
import { MainSocketService } from '../../core/services/main.socket.service';


@Component({
  selector: 'main',
  templateUrl: './main.component.html'
})
export class MainComponent implements OnInit {

  experiment: any
  selectedExperimentType: String
  experimentDescription: ExperimentDescription

  constructor(
    private ioMain: MainSocketService,
  )
  {}

  public ngOnInit() {
    this.initMainEvents();
  }

  // HTTP: Main-node
  // Socket
  private initMainEvents(): void {
    this.ioMain.onEvent(MainEvent.FINAL)
    .subscribe((obj: any) => {
    });
    this.ioMain.onEvent(MainEvent.EXPERIMENT)
      .subscribe((obj: any) => {
        this.experimentDescription = obj['description']['experiment description'];
        this.selectedExperimentType = this.experimentDescription.ModelConfiguration.ModelType
      });
  }
}
