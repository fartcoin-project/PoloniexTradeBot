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

Logs: `tradebot/logs/tradebot.log`. Override budget for one run: `python run_scheduled.py --budget 5.0`.

## Build single .exe

From project root:

```powershell
.\build_exe.ps1
```

Or from `tradebot/`:

```powershell
cd tradebot
.\build_exe.ps1
```

See [tradebot/BUILD.md](tradebot/BUILD.md). Output: **`TradeBot.exe`** in the project root.

## Layout

```
tradebot/
  tradebot.py              # Core engine (CLI)
  runtime_paths.py         # Dev + frozen exe paths
  run_gui.py               # GUI entry
  tradebot_config.EXAMPLE.py
  gui/                     # Qt desktop UI (PySide6)
  build_exe.ps1
  tradebot.spec
  BUILD.md
  LICENSE
  requirements.txt
```

Runtime data (gitignored): `config.json`, `json/`, `orderbooks/`, `tradebot_config.py`

## Requirements

- Python 3.10+
- Poloniex API key with trading permissions
- Minimum order: ₿ 0.0001
