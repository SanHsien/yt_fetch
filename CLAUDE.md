# CLAUDE.md

給 Claude Code 在本專案工作時的指引。

## 專案宗旨與邊界

`yt_fetch` 是 YouTube 頻道影片下載工具。它接受頻道 URL、頻道 ID 或 `@handle`，抓取最新公開影片，排除或包含 Shorts，並把影片下載到 `download/`。

本專案只應支援使用者自己有權存取、YouTube 公開提供的內容。

**硬性邊界（不可違反）**：

- 不實作任何繞過私人影片、會員限定、付費牆、地區限制、年齡限制或帳號限制的功能（即存取使用者
  無權觀看的內容）。以使用者自己的登入下載其本來就有權觀看的內容（含自己付費／訂閱的會員影片）屬已授權存取，不在此限。
- 不外洩使用者帳密、cookies、token。cookies 僅在使用者本機抽取／使用其「自己的」、存於本機、絕不外傳。
- cookies 相關功能限於 `yt-dlp` 原生支援，以及本工具的受控登入（`chrome_cdp_cookies`，在本機取得使用者
  自己的 cookies）；且只用於使用者自己有權存取的內容。
- 不移除著作權與 YouTube 服務條款提醒。

## 技術

- Python 3.10+，CLI 入口 `yt_fetch.py`；GUI 為薄層 `yt_fetch_gui.py`（Tkinter，重用核心邏輯）。
- `yt-dlp` 負責解析與下載。
- `imageio-ffmpeg` 作為 ffmpeg 補強來源。
- `download/.download_archive.txt` 是下載紀錄；影片檔名中的 `[video_id]` 也會被用來判斷是否已下載。
- 測試放在 `tests/`，涵蓋核心純函式（URL 正規化、篩選、options 組裝、批次下載）、GUI 純邏輯、
  受控 cookies 純函式與依賴新鮮度工具，全部不連網、不開視窗。

## 開發原則

- 小步修改，避免無需求的大型重構。
- 新增行為時補測試；修正 CLI 參數、URL 正規化、篩選邏輯時尤其要補。
- 使用繁體中文回覆。
- 使用者文件保持實用，避免冗長背景分析。

## 常用指令

```bash
.venv\Scripts\python -m pip install -e ".[dev]"
.venv\Scripts\python -m pytest -q
.venv\Scripts\python -m black --check yt_fetch.py yt_fetch_gui.py chrome_cdp_cookies.py build_exe.py tools/ tests/
.venv\Scripts\python -m isort --check-only yt_fetch.py yt_fetch_gui.py chrome_cdp_cookies.py build_exe.py tools/ tests/
.venv\Scripts\python -m flake8 yt_fetch.py yt_fetch_gui.py chrome_cdp_cookies.py build_exe.py tools/ tests/
```

## 相關文件

- `README.md`：使用方法與 CLI 參數。
- `docs/DEVELOPMENT.md`：建置與驗證流程。
- `docs/ARCHITECTURE.md`：程式結構與資料流。
- `docs/HANDOFF.md`：接手狀態。
- `docs/planning/`：規劃與歷史規格文件。
