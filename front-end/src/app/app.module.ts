import { BrowserModule } from '@angular/platform-browser';
import { NgModule } from '@angular/core';
import { HttpModule } from '@angular/http';

// Modules
import { CoreModule } from './core/core.module';
import { SharedModule } from './shared/shared.module';

// Intro
import { AppComponent } from './app.component';
/* Charts */ 
import { HeatMapComponent } from './components/charts/heat-map/heat-map.component';
import { RegChartComponent } from './components/charts/reg-chart/reg-chart.component';
import { Ch1Component } from './components/charts/ch-1/ch-1.component';
import { HeatMap2Component } from './components/charts/heat-map-2/heat-map-2.component';
import { HeatMapRegComponent } from './components/charts/heat-map-reg/heat-map-reg.component';

import { TaskListComponent } from './components/task-list/task-list.component';



@NgModule({ 
  declarations: [
    AppComponent,
    TaskListComponent,
    HeatMapComponent,
    RegChartComponent,
    Ch1Component,
    HeatMap2Component,
    HeatMapRegComponent
  ],
  imports: [
    BrowserModule, HttpModule,
    CoreModule,
    SharedModule
  ],
  providers: [],
  bootstrap: [AppComponent]
})
export class AppModule { }
