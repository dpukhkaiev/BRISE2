import { Component, OnInit } from '@angular/core';

// Enums
import { MainEvent } from '../../data/client-enums';
import { ExperimentDescription } from '../../data/experimentDescription.model';

// Service
import {MainEventService} from '../../core/services/main.event.service';


@Component({
  selector: 'main',
  templateUrl: './main.component.html'
})
export class MainComponent implements OnInit {

  experiment: any
  selectedExperimentType: String
  experimentDescription: ExperimentDescription

  constructor(
    private ioMain: MainEventService,
  )
  {}

  public ngOnInit() {
    this.initMainEvents();
  }
  private initMainEvents(): void {
    this.ioMain.onEvent(MainEvent.EXPERIMENT)
      .subscribe((message: any) => {
        if (message.headers['message_subtype'] === 'description') {
          const obj = JSON.parse(message.body);
          this.experimentDescription = obj['experiment description'];
          this.selectedExperimentType = this.experimentDescription.ModelConfiguration.ModelType;
        }
      });

  }
}
