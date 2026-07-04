# 截圖產生流程

README 的 GUI 主畫面截圖（`docs/screenshots/main-window.png`）由
`tools/generate_readme_screenshot.py` 產生，流程刻意可重現，避免每次手動截圖造成尺寸／內容不一致。

## 原理

1. 建立 `yt_fetch_gui.YtFetchGUI` 視窗。
2. 填入示範參數（頻道、數量、畫質、重試、進階篩選、字幕語言）、示範下載結果，並注入一段示範日誌，狀態設為「下載中…」，進度條設為 66%。
   下載資料夾顯示為中性示範路徑（`C:\Users\You\Downloads\yt_fetch`），避免洩漏真實使用者名稱／路徑。
3. `update()` 完成繪製後擷取畫面：
   - Windows / macOS：使用 Pillow 的 `ImageGrab`。
   - Linux：退回 ImageMagick 的 `import` 或 `scrot`。
4. 輸出到 `docs/screenshots/main-window.png`。

> 截圖內容為示範資料，不含任何真實 cookies 或個人資訊。

## 產生方式

### Windows / macOS

```bash
pip install pillow
python tools/generate_readme_screenshot.py
```

### Linux（無實體螢幕，使用 Xvfb）

```bash
sudo apt-get install -y python3-tk xvfb imagemagick   # 或 scrot
xvfb-run -a -s "-screen 0 1180x820x24" \
    python3 tools/generate_readme_screenshot.py
```

## 注意

- 視窗尺寸固定為 `1180x820`；Windows / macOS 會只擷取 GUI 視窗範圍，Linux/Xvfb 則建議維持相同螢幕尺寸。
- 若調整 GUI 版面，重新執行腳本更新截圖即可。
