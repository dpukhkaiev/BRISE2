import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { RegChartComponent } from './reg-chart.component';

describe('RegChartComponent', () => {
  let component: RegChartComponent;
  let fixture: ComponentFixture<RegChartComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ RegChartComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(RegChartComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
