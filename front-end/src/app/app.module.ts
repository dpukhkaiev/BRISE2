import { BrowserModule } from '@angular/platform-browser';
import { NgModule } from '@angular/core';
import { HttpModule } from '@angular/http';


import { AppComponent } from './app.component';
import { TaskListComponent } from './task-list/task-list.component';

// ------------------ USER --------------------
// Animation
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
// Material
import { MatButtonModule, 
  MatCheckboxModule, 
  MatCardModule, 
  MatListModule, 
  MatIconModule, 
  MatTabsModule, 
  MatTooltipModule,
  MatGridListModule} from '@angular/material';

/* Shared Service */
import { WorkerService } from './services/worker.service';
import { SocketService } from './services/socket.service';

/* Charts */ 
import { HeatMapComponent } from './charts/heat-map/heat-map.component';
import { RegChartComponent } from './charts/reg-chart/reg-chart.component';
import { Ch1Component } from './charts/ch-1/ch-1.component';
import { HeatMap2Component } from './charts/heat-map-2/heat-map-2.component';


@NgModule({ 
  declarations: [
    AppComponent,
    TaskListComponent,
    HeatMapComponent,
    RegChartComponent,
    Ch1Component,
    HeatMap2Component
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
    MatTooltipModule,
    MatGridListModule
  ],
  providers: [{ provide: WorkerService, useClass: WorkerService },
    { provide: SocketService, useClass: SocketService }],
  bootstrap: [AppComponent]
})
export class AppModule { }
