import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { IonicModule } from '@ionic/angular';


import { VlcComponent } from './vlc.component';
import { VlcRoutingModule } from './vlc-routing.module';
import { VlcPopoverPage } from './vlc-popover';
import {HexatrailComponent} from "../../hexatrail/hexatrail.component";
import {AccountModule} from "../account/account.module";

import {IframeComponent} from "../../iframe/iframe.component";
import {IFrameToggler} from "../../iframe/iframe-toggler.component";






@NgModule({
  imports: [
    CommonModule,
    IonicModule,
    VlcRoutingModule,
    FormsModule,
    IonicModule,
    IonicModule,
    HexatrailComponent,
    AccountModule,
    IframeComponent,
    IFrameToggler,
  ],
  declarations: [
    VlcComponent, VlcPopoverPage
  ],
  bootstrap: [VlcComponent]
})
export class VlcModule { }
