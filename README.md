# TradeBot

Desktop Poloniex trading bot — **Qt (PySide6)** GUI + optional single `.exe`. No web app, no Android.

Poloniex trading bot — automatically buy/sell altcoins toward a target BTC value per coin.

Use referral code **F8GSBSS5** when signing up for Poloniex (10% fee discount).

## Quick start (GUI)

```powershell
cd tradebot
pip install -r requirements.txt
copy tradebot_config.EXAMPLE.py tradebot_config.py
# Edit tradebot_config.py with your Poloniex API key and secret
python run_gui.py
```

## Quick start (CLI)

```powershell
cd tradebot
python tradebot.py
```

CLI flags: `-run`, `-log`, `--budget 0.0001`, `--sell` / `--no-sell`, `--excl COIN1 COIN2`

## Scheduled runs (Windows Task Scheduler)

For **daily automation at a fixed time** (e.g. 18:00 with a fixed budget), use **Task Scheduler** — not a Windows Service. A service runs continuously; a scheduled task runs once per day, which fits rebalancing.

1. Set budget, markets, buy/sell mode, and excludes in the GUI → **Save settings** (`config.json`).
2. Test a headless run:

```powershell
cd tradebot
python run_scheduled.py
```

3. Register a daily task (default 18:00):

```powershell
cd tradebot
.\scripts\register_scheduled_task.ps1
```

Or with the built exe: `TradeBot.exe --scheduled` (same as `run_scheduled.py`).

Logs (dev): `tradebot/logs/tradebot.log`. Installed exe: `%LOCALAPPDATA%\TradeBot\logs\tradebot.log`. Override budget for one run: `python run_scheduled.py --budget 5.0`.

## Build installer (self-contained)

From project root:

```powershell
.\build_setup.ps1
```

Output: **`setup-v0.2.1.exe`** (onedir: `TradeBot.exe` + `_internal`). No Python required on the target PC.

- Installs to `%LOCALAPPDATA%\Programs\TradeBot`
- Stores config, API keys, logs, and caches in `%LOCALAPPDATA%\TradeBot`
- Uses `icon.png` for the app / window / taskbar icon and `art.png` for the setup wizard

See [tradebot/BUILD.md](tradebot/BUILD.md). For a bare exe only: `.\build_exe.ps1`.

## Layout

```
tradebot/
  tradebot.py              # Core engine (CLI)
  runtime_paths.py         # Dev + frozen exe paths
  run_gui.py               # GUI entry
  tradebot_config.EXAMPLE.py
  gui/                     # Qt desktop UI (PySide6)
  build_exe.ps1
  build_setup.ps1
  tradebot.spec
  BUILD.md
  LICENSE
  requirements.txt
installer/
  TradeBot.iss
icon.png
art.png
```

Installed app data: `%LOCALAPPDATA%\TradeBot` (`config.json`, `json/`, `orderbooks/`, `tradebot_config.py`, `logs/`). Dev mode still uses files under `tradebot/`.

## Requirements

- Python 3.10+
- Poloniex API key with trading permissions
- Minimum order: ₿ 0.0001
