import { NgModule, Optional, SkipSelf } from '@angular/core';

/* Shared Service */
import {MainEventService} from './services/main.event.service';
import {MainClientService} from './services/main.client.service';
import {InjectableRxStompConfig, RxStompService, rxStompServiceFactory} from "@stomp/ng2-stompjs";
import {myRxStompConfig} from "./services/my-rx-stomp.config";

@NgModule({
  imports: [],
  providers: [
    {provide: MainEventService, useClass: MainEventService},
    {provide: MainClientService, useClass: MainClientService},
    {
      provide: InjectableRxStompConfig,
      useValue: myRxStompConfig
    },
    {
      provide: RxStompService,
      useFactory: rxStompServiceFactory,
      deps: [InjectableRxStompConfig]
    }
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
