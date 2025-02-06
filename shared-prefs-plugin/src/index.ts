import { registerPlugin } from '@capacitor/core';

import type { SharedPrefsPlugin } from './definitions';

const SharedPrefsPlugin = registerPlugin<SharedPrefsPlugin>('SharedPrefsPlugin', {
  web: () => import('./web').then(m => new m.SharedPrefsPluginWeb()),
});

export * from './definitions';
export { SharedPrefsPlugin };
