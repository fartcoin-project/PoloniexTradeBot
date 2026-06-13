# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec — build a single TradeBot.exe
#
#   cd tradebot
#   pip install -r requirements-build.txt
#   pyinstaller tradebot.spec

from pathlib import Path

from PyInstaller.utils.hooks import collect_all

block_cipher = None
root = Path(SPECPATH)
project_root = root.parent

# Output directory is set by build_exe.ps1 (--distpath project root).
# Manual build from this folder: pyinstaller tradebot.spec --noconfirm --distpath ..
workpath = str(root / "build")

qt_datas, qt_binaries, qt_hidden = collect_all("PySide6")

a = Analysis(
    ["run_gui.py"],
    pathex=[str(root)],
    binaries=qt_binaries,
    datas=qt_datas + [
        (str(root / "tradebot_config.EXAMPLE.py"), "."),
    ],
    hiddenimports=[
        "tradebot",
        "runtime_paths",
        "api_compat",
        "budget_helpers",
        "quote_config",
        "gui",
        "gui.app",
        "gui.service",
        "gui.log_stream",
        "gui.paths",
        "gui.panels",
        "gui.data_store",
        "gui.budget_config",
        "gui.theme",
        "gui.widgets",
        "gui.cancel",
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
        "__main__",  # PyInstaller adds this internally; include it so cache checks match
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="TradeBot",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
