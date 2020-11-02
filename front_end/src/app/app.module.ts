import { BrowserModule } from '@angular/platform-browser';
import { NgModule } from '@angular/core';
import { HttpModule } from '@angular/http';

// Modules
import { CoreModule } from './core/core.module';
import { SharedModule } from './shared/shared.module';
import { FormsModule } from '@angular/forms';

// Intro
import { AppComponent } from './app.component';
/* Charts */ 
import { HeatMapComponent } from './components/charts/heat-map/heat-map.component';
import { HeatMapRegComponent } from './components/charts/heat-map-reg/heat-map-reg.component';

import { TaskListComponent } from './components/task-list/task-list.component';
import { InfoBoardComponent } from './components/info-board/info-board.component';
import { ImpResComponent } from './components/charts/imp-res/imp-res.component';
import { FooterComponent } from './components/footer/footer.component';
import { MultiDimComponent } from './components/charts/multi-dim/multi-dim.component';
import { LaunchControlBarComponent } from './components/launch-control-bar/launch-control-bar.component';
import { DownloadPopUp } from './components/download-pop-up/download-pop-up.component';
import { MainComponent } from './components/main/main.component';


@NgModule({ 
  declarations: [
    AppComponent,
    TaskListComponent,
    HeatMapComponent,
    HeatMapRegComponent,
    InfoBoardComponent,
    ImpResComponent,
    FooterComponent,
    MultiDimComponent,
    LaunchControlBarComponent,
    DownloadPopUp,
    MainComponent
  ],
  imports: [
    BrowserModule, HttpModule,
    CoreModule,
    SharedModule,
    FormsModule
  ],
  entryComponents: [
    DownloadPopUp
  ],
  providers: [],
  bootstrap: [AppComponent]
})
export class AppModule { }
