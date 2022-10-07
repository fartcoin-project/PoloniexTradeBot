import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import {ShowDataComponent} from "./show-data/show-data.component";
import {PestoRangeComponent} from "./pesto-range/pesto-range.component";
import {HomeComponent} from "./home/home.component";
import {FormlyJsonComponent} from "./formly-json/formly-json.component";

export const routes: Routes = [
    {path: '', component: HomeComponent},
    {path: 'showdata', component: ShowDataComponent},
    {path: 'Range', component: PestoRangeComponent},
    {path: 'formly-json', component: FormlyJsonComponent},


  ];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }
