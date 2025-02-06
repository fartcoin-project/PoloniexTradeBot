import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { TabsPage } from './tabs-page';



const routes: Routes = [
  {
    path: 'tabs',
    component: TabsPage,
    children: [
      {
        path: 'account',
        children: [
          {
            path: '',
            loadChildren: () => import('../account/account.module').then(m => m.AccountModule)
          }
        ]
      },
      {
        path: 'vlc',
        children: [
          {
            path: '',
            loadChildren: () => import('../vlc/vlc.module').then(m => m.VlcModule)
          }
        ]
      },
      {
        path: '',
        redirectTo: '/app/tabs/vlc',
        pathMatch: 'full'
      }
    ]
  }
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class TabsPageRoutingModule { }
