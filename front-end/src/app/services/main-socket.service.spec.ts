import { TestBed, inject } from '@angular/core/testing';

import { MainSocketService } from './main-socket.service';

describe('MainSocketService', () => {
  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [MainSocketService]
    });
  });

  it('should be created', inject([MainSocketService], (service: MainSocketService) => {
    expect(service).toBeTruthy();
  }));
});
