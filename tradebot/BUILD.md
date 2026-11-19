# TradeBot — build & run

## GUI (development)

```powershell
cd tradebot
python run_gui.py
```

Dev mode stores config, API keys, logs, and caches in this folder.

## Self-contained installer (recommended)

From project root:

```powershell
.\build_setup.ps1
```

Or from this folder:

```powershell
cd tradebot
.\build_setup.ps1
```

Output: **`../setup-v0.2.6.exe`** (project root)

The setup is fully self-contained: no Python or Qt install is required on the target PC.

### What the installer does

| Item | Location |
|------|----------|
| Application | `%LOCALAPPDATA%\Programs\TradeBot\TradeBot.exe` |
| Config, API keys, logs, caches | `%LOCALAPPDATA%\TradeBot` |
| Start menu shortcut | TradeBot |
| Desktop shortcut | optional |

Uninstall keeps AppData by default and asks whether to remove `%LOCALAPPDATA%\TradeBot`.

### Icons

- `icon.png` → app / window / taskbar icon (`TradeBot.exe` + Qt window icon)
- `art.png` → setup file icon and left-side wizard graphic

## Single-file exe only

From project root:

```powershell
.\build_exe.ps1
```

Output: **`../TradeBot.exe`** (project root)

Prefer `build_setup.ps1` for distribution. A bare exe still writes data to `%LOCALAPPDATA%\TradeBot` when frozen.

### Manual build

Close any running `TradeBot.exe` first (the build scripts stop them automatically).

```powershell
pip install -r requirements-build.txt
python build_assets.py
pyinstaller tradebot.spec --noconfirm --distpath ..
```

Then compile `installer/TradeBot.iss` with Inno Setup 6 (`ISCC`) to produce `setup-v0.2.6.exe`.

### Tips

- Set `console=True` in `tradebot.spec` to debug with a terminal window.
- Expect ~50–80 MB exe size (Python + ccxt + Qt bundled); the setup wraps that exe.
