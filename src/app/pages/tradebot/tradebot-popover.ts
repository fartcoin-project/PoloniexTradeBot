
import { PopoverController } from '@ionic/angular';
import {Component, ElementRef, EventEmitter, Output, Renderer2, ViewChild} from '@angular/core';


@Component({
  templateUrl: './tradebot-popover.html',
})
export class TradebotPopoverPage {
  @Output() iframeToggle = new EventEmitter<any>();

  onIframeToggle(iframe: any) {
    this.iframeToggle.emit(iframe);
    this.popoverCtrl.dismiss();
  }
  constructor(public popoverCtrl: PopoverController) {}

  support() {
    this.popoverCtrl.dismiss();
  }

  close(url: string) {
    //window.open(url, '_blank');
    this.popoverCtrl.dismiss();
  }
}
