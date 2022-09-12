import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { HttpClientModule  } from '@angular/common/http';
import {CommonModule} from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ReactiveFormsModule } from '@angular/forms';
import { IonicModule } from '@ionic/angular';
import {platformBrowserDynamic} from '@angular/platform-browser-dynamic';
import {MatCardModule} from "@angular/material/card";
import {MatFormFieldModule} from "@angular/material/form-field";
import {MatCheckboxModule} from "@angular/material/checkbox";
import {MatSliderModule} from "@angular/material/slider";
import {MatInputModule} from "@angular/material/input";
import {MatTableModule} from '@angular/material/table';
import {MatSortModule} from '@angular/material/sort';
import {MatProgressSpinnerModule} from "@angular/material/progress-spinner";

import { AppRoutingModule } from './app-routing.module';
import { AppComponent } from './app.component';
import { ShowDataComponent } from './show-data/show-data.component';
import { HomeComponent } from './home/home.component';
import {PestoRangeComponent} from "./pesto-range/pesto-range.component";
//import {FormlyJsonComponent} from "./formly-json/formly-json.component";
import {FormlyJsonModule} from "./formly-json/formly-json.module";
import {FormlyModule} from "@ngx-formly/core";


@NgModule({
  declarations: [
    //FormlyJsonComponent,
    PestoRangeComponent,
    AppComponent,
    ShowDataComponent,
    HomeComponent
  ],
  imports: [
    HttpClientModule,
    BrowserModule,
    AppRoutingModule,
    CommonModule,
    FormsModule,
    ReactiveFormsModule,
    IonicModule,
    MatTableModule,
    MatSortModule,
    MatProgressSpinnerModule,
    MatCardModule,
    MatFormFieldModule,
    MatCheckboxModule,
    MatSliderModule,
    MatInputModule,
    FormlyModule,
    FormlyJsonModule,


  ],
  exports: [
    ShowDataComponent,
    PestoRangeComponent,

  ],
  providers: [],
  bootstrap: [ AppComponent]
})
export class AppModule { }
