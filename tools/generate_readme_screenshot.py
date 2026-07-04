#!/usr/bin/env python3
"""產生 README 用的 GUI 主畫面截圖。

做法：建立 `yt_fetch_gui` 的視窗、填入示範資料與示範日誌，render 後擷取成
`docs/screenshots/main-window.png`。

擷取方式跨平台自動選擇：
- Windows / macOS：使用 Pillow 的 `ImageGrab`
- Linux：退回 ImageMagick 的 `import` 或 `scrot`（搭配 Xvfb 可在無實體螢幕時產生）

用法：
    # Windows / macOS（已安裝 Pillow）
    python tools/generate_readme_screenshot.py

    # Linux（無實體螢幕）
    xvfb-run -a -s "-screen 0 1180x820x24" \
        /usr/bin/python3 tools/generate_readme_screenshot.py
"""

import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "docs" / "screenshots" / "main-window.png"

DEMO_VALUES = {
    "channel": "@LinusTechTips",
    "count": "5",
    "quality": "720p",
    "retries": "3",
    "title_include": "build",
    "date_after": "20260101",
    "min_duration": "300",
    "sub_langs": "zh-Hant,en",
}

# 中性示範下載路徑（避免在公開截圖洩漏真實使用者名稱／路徑）
DEMO_DOWNLOAD_DIR = r"C:\Users\You\Downloads\yt_fetch"

DEMO_LOG = [
    "14:32:01 - INFO - ============================================================",
    "14:32:01 - INFO - YouTube 頻道影片下載工具",
    "14:32:01 - INFO - ============================================================",
    "14:32:02 - INFO - 將從 Videos 頁面獲取影片（不包含 Shorts）",
    "14:32:04 - INFO - 合併後共找到 30 支不重複影片",
    "14:32:04 - INFO - 本頻道已下載 2 支，目標 5 支，還需下載 3 支",
    "14:32:05 - INFO - [1/28] 下載 (0/3 新影片, 總計 2/5): How We Built ...",
    "14:32:31 - INFO - ✓ 完成 (1/3 新影片, 總計 3/5): How We Built [a1b2c3d4e5f].mp4",
    "14:32:32 - INFO - [2/28] 下載 (1/3 新影片, 總計 3/5): The Fastest ...",
    "14:32:58 - INFO - ✓ 完成 (2/3 新影片, 總計 4/5): The Fastest [f6g7h8i9j0k].mp4",
]

DEMO_RESULTS = [
    {
        "title": "How We Built",
        "id": "a1b2c3d4e5f",
        "path": r"C:\Users\You\Downloads\yt_fetch\How We Built [a1b2c3d4e5f].mp4",
        "duration": 600,
    },
    {
        "title": "The Fastest",
        "id": "f6g7h8i9j0k",
        "path": r"C:\Users\You\Downloads\yt_fetch\The Fastest [f6g7h8i9j0k].mp4",
        "duration": 420,
    },
]


def build_window():
    """建立並填好示範資料的 GUI 視窗，回傳 (root, app)。"""
    sys.path.insert(0, str(ROOT))
    import tkinter as tk

    import yt_fetch_gui

    root = tk.Tk()
    app = yt_fetch_gui.YtFetchGUI(root)
    root.geometry("1180x820+80+80")

    for key, value in DEMO_VALUES.items():
        app.vars[key].set(value)
    # 顯示中性示範下載路徑，避免截圖洩漏真實使用者路徑
    app.dir_var.set(DEMO_DOWNLOAD_DIR)
    app.status_var.set("下載中…")
    app.progress_var.set(66.0)
    app.progress_text_var.set(app.t("progress_percent", percent=66.0))
    app.vars["write_subs"].set(True)
    for line in DEMO_LOG:
        app._append_log(line)
    app.current_downloaded = DEMO_RESULTS
    for item in DEMO_RESULTS:
        app._append_result(item)

    root.deiconify()
    root.lift()
    root.attributes("-topmost", True)
    root.focus_force()
    root.update_idletasks()
    root.update()
    time.sleep(0.5)
    root.update()
    return root, app


def capture(root, path: Path) -> None:
    """擷取目前畫面到 path（跨平台）。"""
    path.parent.mkdir(parents=True, exist_ok=True)

    try:
        from PIL import ImageGrab  # Windows / macOS

        root.update_idletasks()
        root.update()
        if sys.platform == "win32":
            ImageGrab.grab(window=root.winfo_id()).save(str(path))
            return
        x = root.winfo_rootx()
        y = root.winfo_rooty()
        w = root.winfo_width()
        h = root.winfo_height()
        ImageGrab.grab(bbox=(x, y, x + w, y + h)).save(str(path))
        return
    except Exception:
        pass

    if shutil.which("import"):
        subprocess.run(["import", "-window", "root", str(path)], check=True)
    elif shutil.which("scrot"):
        subprocess.run(["scrot", str(path)], check=True)
    else:
        raise RuntimeError("找不到可用的截圖工具（請安裝 Pillow、ImageMagick 或 scrot）")


def main() -> None:
    root, _ = build_window()
    try:
        capture(root, OUTPUT)
        print(f"已輸出截圖：{OUTPUT}")
    finally:
        root.destroy()


if __name__ == "__main__":
    main()
