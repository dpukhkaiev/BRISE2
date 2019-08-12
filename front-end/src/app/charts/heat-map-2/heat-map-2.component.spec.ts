import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { HeatMap2Component } from './heat-map-2.component';

describe('HeatMap2Component', () => {
  let component: HeatMap2Component;
  let fixture: ComponentFixture<HeatMap2Component>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ HeatMap2Component ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(HeatMap2Component);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
