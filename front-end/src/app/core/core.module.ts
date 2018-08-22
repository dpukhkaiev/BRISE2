import { NgModule, Optional, SkipSelf } from '@angular/core';
import { CommonModule } from '@angular/common';

/* Shared Service */
import { RestService } from './services/rest.service';
import { WsSocketService } from './services/ws.socket.service';
import { MainSocketService } from './services/main.socket.service';

@NgModule({
  imports: [],
  providers: [
    { provide: RestService, useClass: RestService },
    { provide: WsSocketService, useClass: WsSocketService },
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
