import { CUSTOM_ELEMENTS_SCHEMA, ErrorHandler, NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { HttpClient, provideHttpClient, withInterceptorsFromDi } from "@angular/common/http";
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { AppRoutingModule } from './app-routing.module';
import { AppComponent } from './app.component';

import { environment } from "../environments/environment";
import { InAppBrowser } from '@awesome-cordova-plugins/in-app-browser/ngx';
import { ServiceWorkerModule } from '@angular/service-worker';
import { IonicStorageModule } from "@ionic/storage-angular";

import { IonicModule, IonicRouteStrategy } from '@ionic/angular';
import { defineCustomElements } from '@ionic/core/loader/index.js';
import { NativeHttpModule } from 'ionic-native-http-connection-backend';
import { RouteReuseStrategy } from "@angular/router";
import { CustomErrorHandler } from "./custom-error-handler";
import { IframeComponent } from "./iframe/iframe.component";

@NgModule({
  declarations: [
    AppComponent
  ],
  bootstrap: [AppComponent],
  schemas: [CUSTOM_ELEMENTS_SCHEMA],
  imports: [
    CommonModule,
    BrowserModule,
    AppRoutingModule,
    FormsModule,
    IonicModule.forRoot(),
    IonicStorageModule.forRoot(),
    ServiceWorkerModule.register('ngsw-worker.js', {
      enabled: environment.production
    }),
    NativeHttpModule,
    IframeComponent
  ],
  providers: [
    HttpClient,
    InAppBrowser,
    { provide: RouteReuseStrategy, useClass: IonicRouteStrategy },
    { provide: ErrorHandler, useClass: CustomErrorHandler },
    provideHttpClient(withInterceptorsFromDi())
  ]
})
export class AppModule { }
