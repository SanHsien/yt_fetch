# 架構概要

`yt_fetch` 以單檔核心 `yt_fetch.py` 為主，外加薄層 GUI 與受控登入 cookies 模組。維護時先理解 `yt_fetch.py` 的資料流，不要急著再拆模組。

## 模組與責任

| 位置 | 責任 |
| --- | --- |
| `yt_fetch.py` | CLI、環境檢查、ffmpeg 檢查、頻道 URL 正規化、影片篩選、下載流程 |
| `yt_fetch_gui.py` | Tkinter 桌面介面（薄層，`import yt_fetch` 重用核心；背景執行緒下載） |
| `chrome_cdp_cookies.py` | 受控瀏覽器登入與 CDP cookies 擷取（CDP 限本機 loopback、只匯出 YouTube 登入所需網域；Windows） |
| `yt_fetch.spec` / `build_exe.py` | PyInstaller 打包設定與一鍵建置腳本（產出 `dist/yt_fetch.exe`） |
| `tools/generate_readme_screenshot.py` | 產生 README 用的 GUI 截圖 |
| `tools/check_dependency_freshness.py` | 檢查 `yt-dlp` / `imageio-ffmpeg` 是否落後 PyPI（供每月排程與本地使用） |
| `.github/workflows/release.yml` | 在 Windows 上自動建置 exe 並於 `v*` 標籤發佈 Release |
| `tests/` | 基本 smoke test、關鍵 helper 與 GUI 純邏輯測試 |
| `README.md` | 使用者操作說明 |
| `CONTRIBUTING.md` | 貢獻流程與本地檢查指令 |
| `.github/workflows/code-check.yml` | GitHub Actions 驗證 |
| `.github/workflows/codeql.yml` | Python CodeQL `security-extended` 程式碼掃描 |

## 執行流程

1. `main()` 進入程式。
2. `ensure_venv_and_restart()` 確認虛擬環境與必要套件。
3. `parse_args()` 解析 CLI 參數。
4. 參數不足時，`prompt_user_input()` 改用互動輸入。
5. `normalize_channel_url()` 驗證 HTTPS YouTube host，並將輸入轉為 YouTube videos 頁面。
6. `check_ffmpeg()` / `install_ffmpeg()` 確保可合併最佳影音格式。
7. `download_videos()` 使用 `yt-dlp` 擷取影片列表、過濾非公開內容與 Shorts；有合法 cookies
   時保留需登入候選給 YouTube 驗證帳號權限，再依畫質選項下載目標數量。
8. `get_downloaded_ids()` 讀取 archive 與既有檔名，避免重複下載。

## 可測試的純函式

`download_videos()` 仍是主要協調流程，但已把可單測的邏輯抽成模組層函式：

| 函式 | 責任 |
| --- | --- |
| `normalize_channel_url()` | 驗證 HTTPS YouTube host，將 URL / 頻道 ID / `@handle` 正規化 |
| `build_channel_urls()` | 依是否含 Shorts 組出要提取的分頁 URL 清單 |
| `filter_reason()` | yt-dlp `match_filter` 的判斷（非公開、Shorts） |
| `is_public_video()` | 判斷影片是否公開 |
| `filter_downloadable_entries()` | 從清單排除直播/預告、非公開、已下載 |
| `build_format_selector()` | 依 `best` / `1080p` / `720p` / `480p` 產生 yt-dlp format selector |
| `read_archive_ids()` / `archive_contains()` | 讀取／查詢下載 archive |
| `get_downloaded_ids()` | archive 與既有檔名合併出的已下載 ID |
| `find_downloaded_file()` | 依 `[video_id]` 找出已下載檔案路徑 |

## 輸出與狀態

- 影片輸出：`download/<頻道名稱>/`（依頻道名稱分子目錄，避免多頻道混在一起）
- 下載紀錄：`download/.download_archive.txt`（共用；已下載偵測遞迴掃描所有子目錄）
- 檔名格式：`download/%(channel,uploader|Unknown Channel)s/%(title)s [%(id)s].mp4`
- 設定檔：`yt_fetch.ini`（程式旁，非敏感偏好；優先序 CLI > 環境變數 > ini > 內建預設；不含 cookies，包含 `quality` 等一般偏好）

`download/` 內的影片、archive、cookies、log 都不應提交。

## 變更風險

高風險區域：

- `download_videos()`：牽涉 yt-dlp options、畫質 format selector、公開影片判斷、Shorts 篩選與下載數量。
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
