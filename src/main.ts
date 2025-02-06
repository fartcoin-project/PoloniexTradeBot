import { enableProdMode } from '@angular/core';
import { platformBrowserDynamic } from '@angular/platform-browser-dynamic';

import { AppModule } from './app/app.module';
import { environment } from './environments/environment';

import { defineCustomElements } from '@ionic/pwa-elements/loader';



import { defineCustomElements as pwaElements} from '@ionic/pwa-elements/loader';
import { Capacitor } from '@capacitor/core';

import './polyfills';



if (environment.production) {
  enableProdMode();
}


// --> Below only required if you want to use a web platform
const platform = Capacitor.getPlatform();
if(platform === "web") {
  // Web platform
  // required for toast component in Browser
  pwaElements(window);

}
// Above only required if you want to use a web platform <--


platformBrowserDynamic().bootstrapModule(AppModule)
  .catch(err => console.error(err));

  defineCustomElements(window);
