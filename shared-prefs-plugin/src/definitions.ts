
export interface SharedPrefsPlugin {
  getPreference(options: { key: string }): Promise<{ value: string }>;
  setPreference(options: { key: string, value: string }): Promise<void>;
}

declare global {
  interface PluginRegistry {
    SharedPrefsPlugin: SharedPrefsPlugin;
  }
}
