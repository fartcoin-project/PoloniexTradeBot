import { ComponentFixture, TestBed } from '@angular/core/testing';

import { HexatrailComponent } from './hexatrail.component';

describe('HexatrailComponent', () => {
  let component: HexatrailComponent;
  let fixture: ComponentFixture<HexatrailComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [HexatrailComponent]
    });
    fixture = TestBed.createComponent(HexatrailComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
