package com.omariskandarani.tradebot;

import android.os.Bundle
import com.example.tradebot.LocalServer
import com.getcapacitor.BridgeActivity

class MainActivity : BridgeActivity() {
  override fun onCreate(savedInstanceState: Bundle?) {
    super.onCreate(savedInstanceState)
    LocalServer.startServer() // Start the local API server
  }
}
