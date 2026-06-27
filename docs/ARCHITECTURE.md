# 架構概要

`yt_fetch` 目前是單檔 Python CLI。維護時先理解 `yt_fetch.py` 的資料流，不要急著拆模組。

## 模組與責任

| 位置 | 責任 |
| --- | --- |
| `yt_fetch.py` | CLI、環境檢查、ffmpeg 檢查、頻道 URL 正規化、影片篩選、下載流程 |
| `tests/` | 基本 smoke test 與關鍵 helper 測試 |
| `README.md` | 使用者操作說明 |
| `CONTRIBUTING.md` | 貢獻流程與本地檢查指令 |
| `.github/workflows/code-check.yml` | GitHub Actions 驗證 |

## 執行流程

1. `main()` 進入程式。
2. `ensure_venv_and_restart()` 確認虛擬環境與必要套件。
3. `parse_args()` 解析 CLI 參數。
4. 參數不足時，`prompt_user_input()` 改用互動輸入。
5. `normalize_channel_url()` 將輸入轉為 YouTube videos 頁面。
6. `check_ffmpeg()` / `install_ffmpeg()` 確保可合併最佳影音格式。
7. `download_videos()` 使用 `yt-dlp` 擷取影片列表、過濾非公開內容與 Shorts，並下載目標數量。
8. `get_downloaded_ids()` 讀取 archive 與既有檔名，避免重複下載。

## 輸出與狀態

- 影片輸出：`download/`
- 下載紀錄：`download/.download_archive.txt`
- 檔名格式：`%(title)s [%(id)s].mp4`

`download/` 內的影片、archive、cookies、log 都不應提交。

## 變更風險

高風險區域：

- `download_videos()`：牽涉 yt-dlp options、公開影片判斷、Shorts 篩選與下載數量。
- `normalize_channel_url()`：會影響所有頻道輸入格式。
- cookies 相關參數：必須維持使用者自有合法存取前提。
- ffmpeg 自動安裝與 PATH 修改：跨平台差異明顯。

低風險區域：

- README 範例文字。
- GitHub issue / PR 模板。
- 單純新增測試。

## 拆分模組時機

目前不需要拆模組。只有在同時出現以下情況時才考慮：

- `yt_fetch.py` 持續增長且測試難以針對 helper 撰寫。
- 下載邏輯、URL 正規化、設定讀取需要獨立演進。
- CI 與使用者安裝流程已能覆蓋拆分後的 entry point。
