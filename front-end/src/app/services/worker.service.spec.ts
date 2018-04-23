import { TestBed, inject } from '@angular/core/testing';

import { WorkerServiceService } from './worker-service.service';

describe('WorkerServiceService', () => {
  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [WorkerServiceService]
    });
  });

  it('should be created', inject([WorkerServiceService], (service: WorkerServiceService) => {
    expect(service).toBeTruthy();
  }));
});
