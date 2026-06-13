# TradeBot — build & run

## GUI (development)

```powershell
cd tradebot
python run_gui.py
```

## Single-file exe

From project root:

```powershell
.\build_exe.ps1
```

Or from this folder:

```powershell
cd tradebot
.\build_exe.ps1
```

Output: **`../TradeBot.exe`** (project root)

### First run (end user)

1. Copy `TradeBot.exe` to any folder.
2. Launch — creates `tradebot_config.py`, `config.json`, `json/`, `orderbooks/` beside the exe.
3. Edit `tradebot_config.py` with Poloniex API keys, restart.

**API keys are never embedded in the exe** — they load from `tradebot_config.py` next to the executable.

### Distribution layout

```
MyTradeBot/
  TradeBot.exe
  tradebot_config.py
  config.json
  json/
  orderbooks/
```

### Manual build

Close any running `TradeBot.exe` first (the build script stops them automatically).

```powershell
pip install -r requirements-build.txt
pyinstaller tradebot.spec --noconfirm --distpath ..
```

Output: **`TradeBot.exe`** in the project root (same as `build_exe.ps1`).

### Tips

- Set `console=True` in `tradebot.spec` to debug with a terminal window.
- Add `icon='assets/tradebot.ico'` when you have an icon file.
- Expect ~50–80 MB exe size (Python + ccxt + Qt bundled).
