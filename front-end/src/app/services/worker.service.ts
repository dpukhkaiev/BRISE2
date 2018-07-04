import { Injectable, AnimationStyleMetadata } from '@angular/core';
import { Http } from '@angular/http';
import { Observable } from 'rxjs/Observable';
import 'rxjs/add/operator/map';
import 'rxjs/add/operator/catch';
import 'rxjs/add/observable/throw';

// User
import { Task } from '../data/taskData.model';

import { environment } from '../../environments/environment';
const API_URL = environment.apiUrl;

@Injectable()
export class WorkerService {

  // Placeholder for last id so we can simulate
  // automatic incrementing of ids
  lastId: number = 0;

  // Placeholder for todos
  tasks: Task[] = [];

  constructor(private http: Http) {
  }
  private handleError(error: Response | any) {
    console.error('WorkerService::handleError', error);
    return Observable.throw(error);
  }

  // GET /stack /* Observable<Task[]> */
  public getStack(): any {
    return this.http
      .get(API_URL + '/stack')
      .map(response => {
        const tasks = response.json();
        return tasks/*.map((t) => new Task(t))*/;
      })
      .catch(this.handleError);
  }

  // GET /result/:id
  getTaskById(id: string): any {
    return this.http
      .get(API_URL + '/result/'+ id)
      .map(response => {
        const task = response.json();
        return task/*.map((t) => new Task)/*/;
      })
      .catch(this.handleError);
  }

  // GET all result
  getAllResult(): any {
    return this.http
      .get(API_URL + '/result/all')
      .map(response => {
        const res = response.json();
        return res/*.map((t) => new Task)/*/;
      })
      .catch(this.handleError);
  }


}
