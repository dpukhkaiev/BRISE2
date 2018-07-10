import { Component, OnInit, ViewChild, ElementRef } from '@angular/core';
// import { DataService } from 'service'
import * as _ from 'lodash'

@Component({
  selector: 'reg-chart',
  templateUrl: './reg-chart.component.html',
  styleUrls: ['./reg-chart.component.css']
})
export class RegChartComponent implements OnInit {

  @ViewChild('chart1') el1: ElementRef;
  @ViewChild('chart2') el2: ElementRef;
  constructor() { }

  ngOnInit() {
    this.basicChart()
    this.heatMap()
  }

  basicChart() {
    const element = this.el1.nativeElement

    const data = [{
      x: [1, 2, 3, 4, 5],
      y: [1, 2, 4, 8, 16]
    }]

    const style = {
      margin: { t: 0 }
    }

    Plotly.plot(element, data, style)
  }

  heatMap() {
    const element = this.el2.nativeElement
    const data = [
      {
        z: [
          [1, 13, 30, 50, 1, 50], [20, 1, 60, 80, 30, 50], [30, 60, 1, -10, 20, 50],
          [1, 32, 30, 50, 31, 25], [56, 1, 60, 80, 30, 41], [30, 60, 1, -10, 20, 93],
          [1, 20, 45, 21, 52, 50], [29, 1, 23, 40, 60, 100], [30, 60, 1, -10, 20, 50],
          [1, 43, 30, 31, 71, 92], [23, 1, 32, 80, 13, 85], [10, 13, 11, 34, 70, 53],
          [1, 41, 67, 5, 1, 75], [20, 1, 56, 23, 30, 68]
        ],
        x: ['t-1', 't-2', 't-4', 't-8', 't-16', 't-32'],
        y: ['f-1200', 'f-1300', 'f-1400', 'f-1500', 'f-1600', 'f-1700', 'f-1800', 'f-1900', 'f-2000', 'f-2200', 'f-2400', 'f-2500', 'f-2600', 'f-2700'],
        type: 'heatmap'
        // colorscale: 'Jet',
      }
    ];

    var layout = {
      title: 'Heat map 2'
    };

    Plotly.newPlot(element, data, layout);
  }
  

}
