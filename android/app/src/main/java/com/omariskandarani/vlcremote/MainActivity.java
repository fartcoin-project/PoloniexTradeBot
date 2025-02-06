package com.omariskandarani.tradebot;

import com.omariskandarani.tradebot.plugin.*;
import android.content.SharedPreferences;
import com.getcapacitor.BridgeActivity;
import com.getcapacitor.BridgeWebViewClient;
import android.os.Bundle;
import android.webkit.CookieManager;
import android.webkit.WebSettings;
import android.webkit.HttpAuthHandler;
import android.webkit.WebView;

public class MainActivity extends BridgeActivity {

    @Override
  public void onCreate(Bundle savedInstanceState) {
    super.onCreate(savedInstanceState);

    this.registerPlugin(SharedPrefsPluginPlugin.class);

    // Enable cookies
    CookieManager.getInstance().setAcceptCookie(true);

    // Get WebView settings
    WebView webView = this.getBridge().getWebView();

    webView.setWebViewClient(new BridgeWebViewClient(bridge){
      // Automatic input the alert box
      @Override
      public void onReceivedHttpAuthRequest(WebView view, HttpAuthHandler handler, String host, String realm) {
        // Access SharedPreferences
        SharedPreferences sharedPreferences = getSharedPreferences("MyPreferences", MODE_PRIVATE);
        String passValue = sharedPreferences.getString("pass", "pass not fetched");

        // Print or use the retrieved value
        System.out.println("Pass value from SharedPreferences: " + passValue);
        handler.proceed("", passValue);
      }
    });
    WebSettings webSettings = webView.getSettings();

    // Enable JavaScript (if needed)
    webSettings.setJavaScriptEnabled(true);
  }
}
