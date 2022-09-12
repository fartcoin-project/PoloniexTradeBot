import './polyfills';

import { enableProdMode } from '@angular/core';
import { platformBrowserDynamic } from '@angular/platform-browser-dynamic';

import { FormlyJsonModule } from '../../formly-json/formly-json.module';

platformBrowserDynamic().bootstrapModule(FormlyJsonModule).then(ref => {
  // Ensure Angular destroys itself on hot reloads.
  if (window['ngRef']) {
    window['ngRef'].destroy();
  }
  window['ngRef'] = ref;

  // Otherise, log the boot error
}).catch(err => console.error(err));


/**  Copyright 2018 Google Inc. All Rights Reserved.
    Use of this source code is governed by an MIT-style license that
    can be found in the LICENSE file at http://angular.io/license */
