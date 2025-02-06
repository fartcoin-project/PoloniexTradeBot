import {Component, EventEmitter, Input, OnInit, Output} from '@angular/core';
import {IonicModule} from "@ionic/angular";
import {NgClass} from "@angular/common";

@Component({
  selector: 'iframe-button',
  standalone: true,
  imports: [
    IonicModule,
    NgClass
  ],
  template: `
    <ion-badge [id]="frameName" [ngClass]="{'frame-hidden': isHidden}"  (click)="onIframeToggle()">
      <em [class]="awesomeLogo"></em>
      <span> {{ buttonText }}</span>
    </ion-badge>
  `,
  styleUrls: ['./iframe.component.scss'],
})
export class IFrameToggler implements OnInit{
  @Input() frameName: string = '';
  @Input() awesomeLogo: string = 'fas fa-cat';
  @Input() buttonText: string = '';
  @Input() isHidden: boolean = false;
  @Output() iframeToggle: EventEmitter<string> = new EventEmitter<string>();

  ngOnInit() {
    let matchedText;

    const pcMatch = this.frameName.match(/\d+\.\d+\.\d+\.(\d+)/);  // Matches the last octet
    const portMatch = this.frameName.match(/:(\d{4})/);  // Matches the first two digits of the port (81)

    const pc = pcMatch ? pcMatch[1] : null;
    const port = portMatch ? portMatch[1].slice(-2)  : null;

    if (pc && port) {
      matchedText = pc + ': ' + port;

      this.buttonText = matchedText;
    } else {
      this.buttonText = this.frameName;  // Fallback if no match is found
    }
  }

  onIframeToggle() {
    this.iframeToggle.emit(this.frameName);
    console.log("%c 1 --> this.frameName: ","color:#f0f;", this.frameName);
  }
}
