import { ComponentFixture, TestBed } from '@angular/core/testing';

import { PestoRangeComponent } from './pesto-range.component';

describe('PestoRangeComponent', () => {
  let component: PestoRangeComponent;
  let fixture: ComponentFixture<PestoRangeComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ PestoRangeComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(PestoRangeComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
