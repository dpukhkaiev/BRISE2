import { Injectable } from '@angular/core';
import { Http } from '@angular/http';
import { Observable } from 'rxjs/Observable';
import 'rxjs/add/operator/map';
import 'rxjs/add/operator/catch';
import 'rxjs/add/observable/throw';

// User
import { Task } from '../../data/taskData.model';

import { environment } from '../../../environments/environment';
const SERVICE_URL = environment.workerService;
const MAIN_URL = environment.mainNode;

@Injectable()
export class RestService {

  tasks: Task[] = [];

  constructor(private http: Http) {
  }
  private handleError(error: Response | any) {
    console.error('Handle Error:', error);
    return Observable.throw(error);
  }
  // ---------------------------------
  //                    Worker Service

  // GET /stack /* Observable<Task[]> */
  public getStack(): any {
    return this.http
      .get(SERVICE_URL + '/stack')
      .map(response => {
        const tasks = response.json();
        return tasks/*.map((t) => new Task(t))*/;
      })
      .catch(this.handleError);
  }

  // GET all result
  getAllResult(): any {
    return this.http
      .get(SERVICE_URL + '/result/all')
      .map(response => {
        const res = response.json();
        return res/*.map((t) => new Task)/*/;
      })
      .catch(this.handleError);
  }
// -----------------------------
//                    Main-node
  startMain(): any {
    return this.http
      .get(MAIN_URL + '/main_start')
      .map(response => {
        const res = response.json();
        return res;
      })
      .catch(this.handleError);
  }
  getMainStatus(): any {
    return this.http
      .get(MAIN_URL + '/status')
      .map(response => {
        const res = response.json();
        return res;
      })
      .catch(this.handleError);
  }
  stopMain(): any {
    return this.http
      .get(MAIN_URL + '/main_stop')
      .map(response => {
        const res = response.json();
        return res;
      })
      .catch(this.handleError);
  }
  downloadDump(format='pkl'): any {
    return this.http
      .get(MAIN_URL + '/download_dump/' + format)
      .map(response => {
        return response
      })
      .catch(this.handleError);
  }


}
