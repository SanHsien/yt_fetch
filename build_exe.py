#!/usr/bin/env python3
"""一鍵建置 Windows 執行檔。

實際只是呼叫 PyInstaller 套用 `yt_fetch.spec`：

    python build_exe.py

需求：
- 在 Windows 上執行（PyInstaller 不做跨平台編譯）。
- 已安裝建置相依：`pip install -e ".[build]"`（含 pyinstaller、yt-dlp、imageio-ffmpeg）。

產物：`dist/yt_fetch.exe`
"""

import subprocess
import sys
from pathlib import Path

# GitHub Windows runner 預設 stdout 可能是 cp1252；建置訊息含中文時會噴 UnicodeEncodeError。
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    except Exception:
        pass

SPEC = Path(__file__).resolve().parent / "yt_fetch.spec"


def main() -> int:
    if sys.platform != "win32":
        print("Note: PyInstaller does not cross-compile; build the Windows exe on Windows.")
        print("CI .github/workflows/release.yml builds it on windows-latest.")
    cmd = [sys.executable, "-m", "PyInstaller", str(SPEC), "--noconfirm", "--clean"]
    print("Running:", " ".join(cmd))
    result = subprocess.run(cmd)
    if result.returncode == 0:
        print("Done: dist/yt_fetch.exe")
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
