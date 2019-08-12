import { Component, OnInit } from '@angular/core';

@Component({
  selector: 'h-map',
  templateUrl: './heat-map.component.html',
  styleUrls: ['./heat-map.component.css']
})
export class HeatMapComponent implements OnInit {
  param_x = [1, 2, 4, 8, 16, 32]
  param_y = [1200, 1300, 1400, 1500, 1600, 1700, 1800, 1900, 2000, 2200, 2400, 2500, 2600, 2700]
  constructor() { }

  ngOnInit() { }
  
}
