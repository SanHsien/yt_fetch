# yt_fetch 專案規格書

## 專案簡介

`yt_fetch` 是輕巧的 YouTube 頻道影片下載工具，用 `yt-dlp` 從指定頻道取得最新可存取影片，下載為 MP4，並依頻道名稱保存到 `download/<頻道名稱>/`。專案提供 CLI、Tkinter GUI 與 Windows 免安裝 EXE。

核心定位是「輕巧、可攜、具 GUI、簡潔易懂」。網路上已有很多功能相似的下載器，本專案不追求大而全，而是把常見個人備份流程做穩、做清楚。

## 使用邊界

- 僅供個人學習、研究與備份用途。
- 只處理使用者明確指定的頻道與使用者有權觀看的內容。
- cookies 只用於使用者自己的登入身分，下載自己本來就有權觀看的內容。
- 不實作繞過付費牆、會員限定、私人影片、地區限制、年齡限制或其他存取控制的功能。
- 不外傳、上傳、分享或交換 cookies、token、帳號憑證。
- 批次下載維持循序保守，不做大量平行下載或規避限流。

## 目標使用情境

- 內容創作者備份自己頻道的影片。
- 使用者備份自己有權觀看的教學、研究或參考影片。
- 以 GUI 快速抓取某頻道最新 N 支影片。
- 以 CLI 或 `--channels-file` 做可重複、可記錄的個人批次備份。
- 在 Windows 上直接使用免安裝 EXE，不需要自行安裝 Python。

## 主要入口

- CLI：`python yt_fetch.py` 或 editable install 後的 `yt-fetch`。
- GUI：`python yt_fetch.py --gui` 或 `yt-fetch-gui`。
- Windows EXE：GitHub Releases 下載 `yt_fetch-<版本>-windows-x64.zip`。
- 受控登入：GUI「登入 YouTube 取得 cookies」或 CLI `--login`。

## 主要功能

### 下載核心

- 從 YouTube 頻道下載指定數量的最新影片。
- 支援 `@handle`、頻道 ID、HTTPS YouTube URL、`/videos`、`/shorts` 與 playlist URL；
  拒絕 HTTP、外部主機、內嵌帳密與非標準連接埠。
- 預設排除 Shorts，可用 `--include-shorts` 包含。
- 排除 live、upcoming、was_live 等直播與預告項目。
- 支援 `best`、`1080p`、`720p`、`480p` 下載畫質。
- 支援標題包含／排除、上傳日期區間、影片長度區間等進階篩選。
- 可選擇同時下載字幕／自動字幕。
- 使用 ffmpeg 合併影片與音訊，輸出 MP4。
- 以 yt-dlp archive 與檔名 video id 避免重複下載。
- 清單擷取採 flat extraction；沒有 cookies 時只保留公開候選，有合法 cookies 時由 YouTube
  驗證會員／Premium／需登入候選的帳號權限；失敗候選會往後補。

### GUI

- 提供下載設定、批次清單、輸出資料夾、下載結果與執行日誌分區。
- 背景執行下載，不阻塞視窗。
- 顯示進度條、即時日誌、下載結果。
- 可選擇／開啟下載資料夾。
- 可開啟下載檔案、開啟所在資料夾、匯出紀錄。
- 可匯入頻道清單做循序批次下載。
- 提供快速設定 profiles 與 ffmpeg 狀態頁。
- 提供更新檢查與內嵌 yt-dlp 新鮮度提醒。

### cookies 與登入

- CLI 保留 `--cookies-from-browser` 與 `--cookies`，供進階使用。
- Windows/Chrome 以受控瀏覽器登入解決 Chrome 127+ App-Bound Encryption。
- 受控 cookies 保存於本機 `%LOCALAPPDATA%\yt_fetch\cookies.txt`。
- 受控 Chrome 的 CDP 只監聽 `127.0.0.1`，且只匯出 YouTube 登入所需網域的 cookies。
- GUI 不提供手動 cookies 欄位，避免一般使用者混淆；需要登入時按登入按鈕。
- 設定檔不保存 cookies。

### 批次與設定

- `--channels-file` 支援每行一個頻道，`#` 開頭為註解。
- 每個頻道各自達成 `--count` 目標。
- 單一頻道失敗不會中斷整批，結束時輸出結果報表。
- `yt_fetch.ini` 保存常用設定，但不保存 cookies。
- CLI、環境變數、設定檔與內建預設依序套用。

## CLI 參數

| 參數 | 說明 |
|------|------|
| `--channel` | 頻道 URL、ID 或 `@handle` |
| `--count` | 每個頻道目標影片數 |
| `--include-shorts` | 包含 Shorts |
| `--quality` | `best`、`1080p`、`720p`、`480p` |
| `--retries` | yt-dlp 重試次數 |
| `--cookies-from-browser` | 從瀏覽器讀取 cookies；Windows/Chrome 會優先走受控 cookies |
| `--cookies` | Netscape 格式 cookies 檔案路徑 |
| `--ratelimit` | 下載速率限制，單位 MB/s |
| `--sleep` | 每支影片下載間隔秒數 |
| `--title-include` | 只下載標題包含指定文字的影片 |
| `--title-exclude` | 排除標題包含指定文字的影片 |
| `--date-after` | 只下載此日期之後（含）的影片，格式 YYYYMMDD |
| `--date-before` | 只下載此日期之前（含）的影片，格式 YYYYMMDD |
| `--min-duration` | 只下載長度不少於指定秒數的影片 |
| `--max-duration` | 只下載長度不超過指定秒數的影片 |
| `--write-subs` | 同時下載字幕／自動字幕 |
| `--sub-langs` | 字幕語言，逗號分隔 |
| `--channels-file` | 批次頻道清單 |
| `--gui` | 啟動 GUI |
| `--login` | 開啟受控瀏覽器登入 YouTube |

## 互動式流程

未提供 `--channel` 且不是 GUI 時，CLI 會詢問：

```text
頻道: @channel_handle
數量: 5
包含 Shorts: n
下載畫質: best
重試次數: 3
```

## 輸出結構

```text
download/
├── .download_archive.txt
└── <頻道名稱>/
    └── <影片標題> [<video_id>].mp4
```

EXE 模式下，`download/` 建在 EXE 所在目錄旁；原始碼模式下，預設建在專案根目錄，可由 GUI 或設定調整。

## 架構概要

- `yt_fetch.py`：核心 CLI、下載流程、設定、版本與更新檢查。
- `yt_fetch_gui.py`：Tkinter GUI 薄層，共用核心下載邏輯。
- `chrome_cdp_cookies.py`：Windows/Chrome 受控瀏覽器 cookies。
- `build_exe.py`、`yt_fetch.spec`：PyInstaller 打包。
- `tools/`：截圖產生、依賴新鮮度檢查等維護工具。
- `tests/`：純邏輯與 GUI 表單測試。
- `docs/`：架構、開發、發行、截圖流程與 planning 文件。

## 維護規格

- Python 3.10+。
- 核心相依：`yt-dlp`、`imageio-ffmpeg`。
- 修改下載行為時，優先改 helper 並補測試。
- CLI/GUI 錯誤診斷必須共用核心分類與提示表。
- README 截圖需由 `tools/generate_readme_screenshot.py` 重新產生。
- 發行新版 EXE 時，以 `v*` tag 觸發 release workflow，並確認 zip 與 `.sha256`。

## 暫不納入

- Web UI 或常駐服務。
- 新影片提醒、下載完成系統通知、排程守護程式。
- 大量平行下載或限流規避。
- 雲端同步或第三方儲存整合。
- 存取使用者無權觀看的內容。

## 可選未來項目

- 額外輸出格式或後處理。

這些項目只有在需求明確、且不破壞 GUI 簡潔度與專案邊界時才會加入。

**文件版本**：1.9.2
**最後更新**：2026-07-26
**維護者**：San-Hsien
