import { NgModule, Optional, SkipSelf } from '@angular/core';
import { CommonModule } from '@angular/common';

/* Shared Service */
import { WorkerService } from './services/worker.service';
import { SocketService } from './services/socket.service';
import { MainSocketService } from './services/main-socket.service';

@NgModule({
  imports: [],
  providers: [
    { provide: WorkerService, useClass: WorkerService },
    { provide: SocketService, useClass: SocketService },
    { provide: MainSocketService, useClass: MainSocketService }
  ],
  declarations: []
})
export class CoreModule {
  /* make sure CoreModule is imported only by one NgModule the AppModule */
  constructor(
    @Optional() @SkipSelf() parentModule: CoreModule
  ) {
    if (parentModule) {
      throw new Error('CoreModule is already loaded. Import only in AppModule');
    }
  }
}
