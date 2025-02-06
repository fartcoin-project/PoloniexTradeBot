import { ComponentFixture, TestBed } from '@angular/core/testing';

import { VlcComponent } from './vlc.component';

describe('VlcComponent', () => {
  let component: VlcComponent;
  let fixture: ComponentFixture<VlcComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ VlcComponent ]
    })
    .compileComponents();

    fixture = TestBed.createComponent(VlcComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
