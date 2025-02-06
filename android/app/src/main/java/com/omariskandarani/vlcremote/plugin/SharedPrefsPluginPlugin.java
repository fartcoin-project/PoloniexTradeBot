package com.omariskandarani.tradebot.plugin;

import android.content.Context;
import android.content.SharedPreferences;
import com.getcapacitor.JSObject;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;
import com.getcapacitor.Plugin;

@CapacitorPlugin(name = "SharedPrefsPlugin")
public class SharedPrefsPluginPlugin extends Plugin {

  @PluginMethod
  public void getPreference(PluginCall call) {
    String key = call.getString("key");
    Context context = getContext();
    SharedPreferences sharedPreferences = context.getSharedPreferences("MyPreferences", Context.MODE_PRIVATE);
    String value = sharedPreferences.getString(key, "pass not fetched");
    JSObject result = new JSObject();
    result.put("value", value);
    call.resolve(result);
  }
  @PluginMethod
  public void setPreference(PluginCall call) {
    String key = call.getString("key");
    String value = call.getString("value");
    Context context = getContext();
    SharedPreferences sharedPreferences = context.getSharedPreferences("MyPreferences", Context.MODE_PRIVATE);
    SharedPreferences.Editor editor = sharedPreferences.edit();
    editor.putString(key, value);
    editor.apply();
    call.resolve();
  }
}
