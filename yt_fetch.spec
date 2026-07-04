# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller 規格檔：把 yt_fetch GUI 打包成單一 Windows 執行檔。

入口為 `yt_fetch_gui.py`（雙擊 exe 直接開圖形介面），以 windowed 模式執行、
內嵌 yt-dlp 與 imageio-ffmpeg（含 ffmpeg 二進位）。

建置：
    python build_exe.py          # 等同 pyinstaller yt_fetch.spec --noconfirm
產物：
    dist/yt_fetch.exe
"""

import os

from PyInstaller.utils.hooks import collect_all

datas = []
binaries = []
# 本機延遲匯入的模組明確列入，確保被打包（yt_fetch 於執行時才 import）。
hiddenimports = ["chrome_cdp_cookies"]
for _pkg in ("yt_dlp", "imageio_ffmpeg"):
    _d, _b, _h = collect_all(_pkg)
    datas += _d
    binaries += _b
    hiddenimports += _h

# 隨附視窗圖示（執行時透過 sys._MEIPASS 取用）
if os.path.exists(os.path.join("assets", "yt_fetch.png")):
    datas += [(os.path.join("assets", "yt_fetch.png"), "assets")]

_icon = os.path.join("assets", "yt_fetch.ico")
icon = _icon if os.path.exists(_icon) else None

block_cipher = None

a = Analysis(
    ["yt_fetch_gui.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name="yt_fetch",
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
    icon=icon,
)
