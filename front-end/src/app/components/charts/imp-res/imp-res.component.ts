import { Component, OnInit, ViewChild, ElementRef } from '@angular/core';

// Service
import { MainSocketService } from '../../../core/services/main.socket.service';

import { Solution } from '../../../data/taskData.model';
import { MainEvent } from '../../../data/client-enums';

interface PointExp {
  configuration: any;
  result: any;
  time: any;
} 

@Component({
  selector: 'imp-res',
  templateUrl: './imp-res.component.html',
  styleUrls: ['./imp-res.component.scss']
})
export class ImpResComponent implements OnInit {
  // The experements results
  bestRes = new Set<PointExp>()
  // Best point 
  solution: Solution

  // poiner to DOM element #map
  @ViewChild('improvement') impr: ElementRef;

  constructor(private ioMain: MainSocketService) { }

  ngOnInit() {
    this.initMainEvents();
  }
  //                              WebSocket
  // --------------------------   Main-node
  private initMainEvents(): void {

    this.ioMain.onEvent(MainEvent.BEST)
      .subscribe((obj: any) => {
        this.solution = obj['best point']
        let time = new Date()
        let temp: PointExp = {
          'configuration': obj['best point']['configuration'],
          'result': obj['best point']['result'],
          'time': time.getMinutes() + 'min ' + time.getSeconds()
        } 
        this.bestRes.add(temp) // There is no check if this solution is the best decision
        this.render() // Render chart when all points got
      });
    this.ioMain.onEvent(MainEvent.TASK_RESULT)
      .subscribe((obj: any) => {
        let time = new Date()
        let temp: PointExp = {
          'configuration': obj['configuration'],
          'result': obj['result'],
          'time': time.getMinutes() + 'min ' + time.getSeconds()
        } 

        this.bestRes.forEach(function(resItem){
          if (temp.result > resItem.result) {
            temp.result = resItem.result
            temp.configuration = resItem.configuration
          }
        })  

        this.bestRes.add(temp)
      });
  }

  render() {
    // DOM element. Render point
    const element = this.impr.nativeElement

    // X-axis data
    const xData = Array.from(this.bestRes).map(i => i["time"]);
    // Results
    const yData = Array.from(this.bestRes).map(i => i["result"]);

    console.log(" - X", xData)
    console.log(" - Y", yData)


    var colors = ['rgba(67,67,67,1)'];

    const data = [ // Full data set
      {
        x: xData,
        y: yData,
        type: 'scatter',
        mode: 'lines',
        line: { color: colors[0], width: 2 }
      },
      {
        x: [xData[0], xData[xData.length-1]],
        y: [yData[0], yData[yData.length-1]],
        type: 'scatter',
        mode: 'markers',
        marker: { color: 'rgba(255,64,129,1)', size: 10 }
      }
    ];

    var layout = {
      showlegend: false,
      title: 'Best results for time',
      xaxis: {
        showline: true,
        showgrid: false,
        showticklabels: true,
        linecolor: 'rgb(204,204,204)',
        linewidth: 2,
        autotick: false,
        ticks: 'outside',
        tickcolor: 'rgb(204,204,204)',
        tickwidth: 2,
        ticklen: 5,
        tickfont: {
          family: 'Roboto',
          size: 12,
          color: 'rgb(82, 82, 82)'
        }
      },
      yaxis: {
        showgrid: false,
        zeroline: false,
        showline: false,
        showticklabels: false
      },
      // autosize: false,
      // margin: {
      //   autoexpand: false,
      //   l: 100,
      //   r: 20,
      //   t: 100
      // },
      annotations: [
        // {
        //   xref: 'paper',
        //   yref: 'paper',
        //   x: 0.05,
        //   y: 1.05,
        //   xanchor: 'center',
        //   yanchor: 'bottom',
        //   text: 'Best results for time',
        //   font: {
        //     family: 'Roboto',
        //     size: 20,
        //     color: 'rgb(37,37,37)'
        //   },
        //   showarrow: false
        // },
        {
          xref: 'paper',
          yref: 'paper',
          x: 0.5,
          y: -0.1,
          xanchor: 'center',
          yanchor: 'top',
          text: 'Time',
          showarrow: false,
          font: {
            family: 'Roboto',
            size: 15,
            color: 'rgb(150,150,150)'
          }
        }
      ]
    };

    Plotly.newPlot(element, data, layout);
  }

}
