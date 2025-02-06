import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';

import { TradebotComponent } from './tradebot.component';

const routes: Routes = [
  {
    path: '',
    component: TradebotComponent
  }
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class TradebotRoutingModule { }
