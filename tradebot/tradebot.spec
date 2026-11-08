# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec — onedir TradeBot (TradeBot.exe + _internal/)
# Output via --distpath (build scripts use project/dist — NEVER project root,
# or Windows case-insensitivity would wipe tradebot/).
#
#   cd tradebot
#   pip install -r requirements-build.txt
#   pyinstaller tradebot.spec --distpath ../dist

from pathlib import Path

from PyInstaller.utils.hooks import collect_all

block_cipher = None
root = Path(SPECPATH)
project_root = root.parent

workpath = str(root / "build")

qt_datas, qt_binaries, qt_hidden = collect_all("PySide6")

icon_png = project_root / "icon.png"
icon_ico = project_root / "installer" / "assets" / "icon.ico"
if not icon_ico.is_file():
    icon_ico = None

extra_datas = [
    (str(root / "tradebot_config.EXAMPLE.py"), "."),
]
if icon_png.is_file():
    extra_datas.append((str(icon_png), "."))

a = Analysis(
    ["run_gui.py"],
    pathex=[str(root)],
    binaries=qt_binaries,
    datas=qt_datas + extra_datas,
    hiddenimports=[
        "tradebot",
        "runtime_paths",
        "api_compat",
        "budget_helpers",
        "quote_config",
        "llm_client",
        "llm_config",
        "ai_orders",
        "ai_status",
        "colibri_manager",
        "httpx",
        "httpx._transports",
        "httpx._transports.default",
        "httpcore",
        "anyio",
        "certifi",
        "h11",
        "idna",
        "sniffio",
        "gui",
        "gui.app",
        "gui.service",
        "gui.log_stream",
        "gui.paths",
        "gui.panels",
        "gui.chat_panel",
        "gui.data_store",
        "gui.budget_config",
        "gui.theme",
        "gui.widgets",
        "gui.cancel",
        "gui.schedule",
        "gui.schedule_config",
        "ccxt",
    ] + qt_hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "matplotlib",
        "numpy",
        "pandas",
        "pytest",
        "IPython",
        "customtkinter",
        "tkinter",
        "ccxt.test",
        "ccxt.async_support",
        "ccxt.pro",
        "__main__",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="TradeBot",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(icon_ico) if icon_ico else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="TradeBot",
)
