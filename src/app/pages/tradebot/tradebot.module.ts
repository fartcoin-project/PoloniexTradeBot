import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { IonicModule } from '@ionic/angular';


import { TradebotComponent } from './tradebot.component';
import { TradebotRoutingModule } from './tradebot-routing.module';
import { TradebotPopoverPage } from './tradebot-popover';
import {HexatrailComponent} from "../../hexatrail/hexatrail.component";
import {AccountModule} from "../account/account.module";

import {IframeComponent} from "../../iframe/iframe.component";
import {IFrameToggler} from "../../iframe/iframe-toggler.component";






@NgModule({
  imports: [
    CommonModule,
    IonicModule,
    TradebotRoutingModule,
    FormsModule,
    IonicModule,
    IonicModule,
    HexatrailComponent,
    AccountModule,
    IframeComponent,
    IFrameToggler,
  ],
  declarations: [
    TradebotComponent, TradebotPopoverPage
  ],
  bootstrap: [TradebotComponent]
})
export class TradebotModule { }
