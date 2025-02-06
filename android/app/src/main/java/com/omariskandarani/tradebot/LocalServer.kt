package com.example.tradebot

import io.ktor.application.*
import io.ktor.features.*
import io.ktor.response.*
import io.ktor.routing.*
import io.ktor.server.engine.*
import io.ktor.server.cio.*

object LocalServer {
  private var server: ApplicationEngine? = null

  fun startServer() {
    server = embeddedServer(CIO, port = 3001) {
      install(ContentNegotiation) {
        json()
      }
      routing {
        get("/api/trading-pairs") {
          call.respond(listOf("BTC/USDT", "ETH/USDT", "LTC/BTC"))
        }
        post("/api/start") {
          call.respond(mapOf("message" to "TradeBot started locally"))
        }
        post("/api/stop") {
          call.respond(mapOf("message" to "TradeBot stopped"))
        }
      }
    }.start(wait = false)
  }

  fun stopServer() {
    server?.stop(0, 0)
  }
}
