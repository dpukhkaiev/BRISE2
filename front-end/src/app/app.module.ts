import { BrowserModule } from '@angular/platform-browser';
import { NgModule } from '@angular/core';
import { HttpModule } from '@angular/http';


import { AppComponent } from './app.component';
import { TaskListComponent } from './task-list/task-list.component';

// ------------------ USER --------------------
// Animation
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
// Material
import { MatButtonModule, MatCheckboxModule, MatCardModule, MatListModule, MatIconModule, MatTabsModule, MatTooltipModule} from '@angular/material';

/* Shared Service */
import { WorkerService } from './services/worker.service';
import { HeatMapComponent } from './heat-map/heat-map.component';
import { RegChartComponent } from './reg-chart/reg-chart.component';


@NgModule({ 
  declarations: [
    AppComponent,
    TaskListComponent,
    HeatMapComponent,
    RegChartComponent
  ],
  imports: [
    BrowserModule, HttpModule, 
    BrowserAnimationsModule, 
    MatButtonModule, 
    MatCheckboxModule, 
    MatCardModule, 
    MatListModule, 
    MatIconModule,
    MatTabsModule,
    MatTooltipModule
  ],
  providers: [{ provide: WorkerService, useClass: WorkerService }],
  bootstrap: [AppComponent]
})
export class AppModule { }
