import { Component, OnInit } from '@angular/core';

import { RestService as mainREST } from '../../core/services/rest.service';


@Component({
  selector: 'launch-control-bar',
  templateUrl: './launch-control-bar.component.html',
  styleUrls: ['./launch-control-bar.component.scss']
})
export class LaunchControlBarComponent implements OnInit {

  // Flag for runing main-node
  isRuning: boolean = false

  constructor(private mainREST: mainREST, ) { }

  ngOnInit() {
  }

  // HTTP: Main-node
  startMain(): any {
    if (this.isRuning == false) {
      this.stopMain(); // Сlean the old tread experiment
      this.mainREST.startMain()
        .subscribe((res) => {
          console.log('Main start:', res)
          this.isRuning = true
        }
        );
    }
  }
  stopMain(): any {
    if (this.isRuning == true) {
      this.mainREST.stopMain()
        .subscribe((res) => {
          console.log('Main stop:', res)
          this.isRuning = false
        }
        );
    }
  }

}
