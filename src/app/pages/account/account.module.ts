import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { IonicModule } from '@ionic/angular';

import { AccountPage } from './account';
import { AccountPageRoutingModule } from './account-routing.module';
import {RouterModule, Routes} from "@angular/router";
import {FormsModule} from "@angular/forms";


const routes: Routes = [
  {
    path: '',
    component: AccountPage
  }
];
@NgModule({
  imports: [RouterModule.forChild(routes),
    CommonModule,
    FormsModule,
    IonicModule,
    CommonModule,
    IonicModule,
    AccountPageRoutingModule,
    AccountPage
  ],
  declarations: [  ],
  exports: [RouterModule]
})
export class AccountModule { }
