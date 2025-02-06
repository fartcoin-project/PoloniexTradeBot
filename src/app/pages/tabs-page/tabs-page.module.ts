import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { IonicModule } from '@ionic/angular';

import { TabsPage } from './tabs-page';
import { TabsPageRoutingModule } from './tabs-page-routing.module';
import {AccountPage} from "../account/account";
import {IFrameToggler} from "../../iframe/iframe-toggler.component";


@NgModule({
  imports: [
    CommonModule,
    IonicModule,
    TabsPageRoutingModule,
    AccountPage,
    IFrameToggler,
    TabsPage
  ],
  declarations: []
})
export class TabsModule { }
