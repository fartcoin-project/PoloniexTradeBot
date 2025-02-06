import { WebPlugin } from '@capacitor/core';
import type { SharedPrefsPlugin } from './definitions';

export class SharedPrefsPluginWeb extends WebPlugin implements SharedPrefsPlugin {
  async getPreference(options: { key: string }): Promise<{ value: string }> {
    const value = localStorage.getItem(options.key) || 'default_value';
    return { value };
  }

  async setPreference(options: { key: string, value: string }): Promise<void> {
    localStorage.setItem(options.key, options.value);
  }
}

