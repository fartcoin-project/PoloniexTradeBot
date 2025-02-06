import { ComponentFixture, TestBed } from '@angular/core/testing';

import { TradebotComponent } from './tradebot.component';

describe('TradebotComponent', () => {
  let component: TradebotComponent;
  let fixture: ComponentFixture<TradebotComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ TradebotComponent ]
    })
    .compileComponents();

    fixture = TestBed.createComponent(TradebotComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).to.true;
  });
});
