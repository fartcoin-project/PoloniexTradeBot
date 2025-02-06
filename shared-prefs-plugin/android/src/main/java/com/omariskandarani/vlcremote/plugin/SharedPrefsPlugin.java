package com.omariskandarani.vlcremote.plugin;

import android.content.Context;
import android.content.SharedPreferences;
import com.getcapacitor.BridgeActivity;
import com.getcapacitor.JSObject;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;
import com.getcapacitor.Plugin;
import com.getcapacitor.annotation.Permission;

@CapacitorPlugin(name = "SharedPrefsPlugin")
public class SharedPrefsPlugin extends Plugin {

  @PluginMethod
  public void getPreference(PluginCall call) {
    String key = call.getString("key");
    Context context = getContext();
    SharedPreferences sharedPreferences = context.getSharedPreferences("MyPreferences", Context.MODE_PRIVATE);
    String value = sharedPreferences.getString(key, "pass not fetched");

    // Create a JSObject to return the value
    JSObject result = new JSObject();
    result.put("value", value);

    // Resolve the call with the JSObject
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
