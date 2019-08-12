import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { Ch1Component } from './ch-1.component';

describe('Ch1Component', () => {
  let component: Ch1Component;
  let fixture: ComponentFixture<Ch1Component>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ Ch1Component ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(Ch1Component);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
