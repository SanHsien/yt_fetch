# AGENTS.md

給 Codex 在本專案工作時的指引。

## 專案宗旨與邊界

`yt_fetch` 是輕巧的 YouTube 頻道影片下載工具：核心為 CLI（`yt_fetch.py`），另有薄層 Tkinter GUI（`yt_fetch_gui.py`）與受控登入 cookies 模組（`chrome_cdp_cookies.py`），用來從指定 YouTube 頻道抓取最新可存取影片，並透過 `yt-dlp` 下載到本機 `download/` 資料夾。

本專案只處理使用者明確指定的頻道與公開可存取影片，目標是個人學習、研究與備份用途。

**硬性邊界（不可違反）**：

- 不加入任何繞過 YouTube 付費牆、會員限定、私人影片、地區限制、年齡限制或其他存取控制的功能
  （即存取使用者「無權觀看」的內容）。以使用者自己的登入身分下載其「本來就有權觀看」的內容
  （例如自己付費／訂閱的會員影片、年齡限制影片）屬已授權存取，不在此限。
- 不破解、外傳、分享或濫用他人或第三方的 cookies、token、帳號憑證。受控登入（chrome_cdp_cookies）
  只在使用者本機抽取並使用其「自己的」cookies、存於本機、絕不外傳。
- `--cookies`、`--cookies-from-browser` 與受控登入只可用於使用者自己有權存取的內容，文件與提示都必須維持這個前提。
- 不移除授權提醒，不鼓勵侵害著作權或違反 YouTube 服務條款。
- 若需求往「下載無權存取內容」、「規避限制」、「大量爬取造成服務壓力」方向走，停下來告知使用者，不要自行實作。

## 技術

- Python 3.10+。
- 核心邏輯集中在 `yt_fetch.py`；GUI 薄層在 `yt_fetch_gui.py`；受控登入在 `chrome_cdp_cookies.py`。
- 核心相依：
  - `yt-dlp`：擷取頻道資訊與下載影片；EXE 會固定打包建置當下版本，需定期檢查更新。
  - `imageio-ffmpeg`：在沒有系統 ffmpeg 時提供可用的 ffmpeg 執行檔。
- 下載輸出在 `download/`，並依頻道名稱分子目錄：`download/<頻道名稱>/`。
- 已下載紀錄使用 `download/.download_archive.txt`，並補充掃描檔名中的 YouTube video id，避免重複下載。
- 可直接執行 `python yt_fetch.py`，也可透過 editable install 取得 `yt-fetch` 指令。

## 主要資料流

1. `parse_args()` 讀取 CLI 參數。
2. 未提供參數時，`prompt_user_input()` 進入互動輸入。
3. `normalize_channel_url()` 將 `@handle`、頻道 ID 或 URL 正規化為 YouTube videos 頁面。
4. `download_videos()` 呼叫 `yt-dlp` 擷取清單、過濾非公開影片與 Shorts，再下載目標數量。
5. `get_downloaded_ids()` 與 yt-dlp archive 檔共同維持冪等性。

## 開發原則

- 最小干預：維持「單檔核心 + 薄層 GUI」架構，除非需求明確需要再拆模組。
- 不主動重構大段程式；修 bug 時優先補測試。
- 使用繁體中文回覆與撰寫使用者文件。
- 對使用條款、著作權、cookies、速率限制相關修改要保守。
- 不提交 `download/` 內的影片、cookies、log、虛擬環境或本機暫存檔。
- **修 bug 必回註 `REPO_REVIEW.md`（適用所有 AI agent：Claude、Codex、Gemini 等，維護者 2026-07-19 指示，常態慣例）**：每修復 `REPO_REVIEW.md` 列出的問題，須回到對應項目標註修復 commit hash 與日期；修復過程中額外發現並修掉的 bug 也要補註。review 維持 latest-only，但修復狀態必須跟上現況。

## 常用指令

```bash
python -m venv .venv
.venv\Scripts\python -m pip install -e ".[dev]"
.venv\Scripts\python -m pytest -q
.venv\Scripts\python -m black --check yt_fetch.py yt_fetch_gui.py chrome_cdp_cookies.py build_exe.py tools/ tests/
.venv\Scripts\python -m isort --check-only yt_fetch.py yt_fetch_gui.py chrome_cdp_cookies.py build_exe.py tools/ tests/
.venv\Scripts\python -m flake8 yt_fetch.py yt_fetch_gui.py chrome_cdp_cookies.py build_exe.py tools/ tests/
```

Windows PowerShell 若不使用 venv 啟動腳本，可直接執行：

```bash
python yt_fetch.py --channel "@channel_handle"
```

## 文件入口

- 使用者說明：`README.md`
- 貢獻流程：`CONTRIBUTING.md`
- 安全回報：`SECURITY.md`
- 接手狀態：`docs/HANDOFF.md`
- 架構概要：`docs/ARCHITECTURE.md`
- 開發驗證：`docs/DEVELOPMENT.md`
- Windows／Computer Use 實機驗證：`docs/COMPUTER_USE_VALIDATION.md`
- 第三方工具與風險：`docs/third-party-youtube-tooling.md`
- 規劃與歷史規格：`docs/planning/`
