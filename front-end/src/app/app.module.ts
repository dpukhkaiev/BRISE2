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
import { HeatMapRegComponent } from './components/charts/heat-map-reg/heat-map-reg.component';

import { TaskListComponent } from './components/task-list/task-list.component';
import { InfoBoardComponent } from './components/info-board/info-board.component';
import { ImpResComponent } from './components/charts/imp-res/imp-res.component';
import { FooterComponent } from './components/footer/footer.component';


@NgModule({ 
  declarations: [
    AppComponent,
    TaskListComponent,
    HeatMapComponent,
    HeatMapComponent,
    HeatMapRegComponent,
    InfoBoardComponent,
    ImpResComponent,
    FooterComponent
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
