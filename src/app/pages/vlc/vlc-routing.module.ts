import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';

import { VlcComponent } from './vlc.component';

const routes: Routes = [
  {
    path: '',
    component: VlcComponent
  }
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class VlcRoutingModule { }
