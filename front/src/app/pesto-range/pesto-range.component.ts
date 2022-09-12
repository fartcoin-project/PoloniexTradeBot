import { Component } from '@angular/core';

@Component({
  selector: 'range',
  templateUrl: './pesto-range.component.html',
  styleUrls: ['./pesto-range.component.scss']
})
export class PestoRangeComponent {
    autoTicks = false;
    disabled = false;
    invert = false;
    max = 100;
    min = 0;
    showTicks = false;
    step = 1;
    thumbLabel = true;
    value = 0;
    vertical = false;
    tickInterval = 1;

    getSliderTickInterval(): number | 'auto' {
        if (this.showTicks) {
            return this.autoTicks ? 'auto' : this.tickInterval;
        }

        return 0;
    }
}

