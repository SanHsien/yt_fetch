# 接手狀態

更新日期：2026-07-26

## 專案概況

`yt_fetch` 是用 `yt-dlp` 從指定 YouTube 頻道下載最新可存取影片的工具。核心為 CLI（`yt_fetch.py`），
另有薄層 Tkinter GUI（`yt_fetch_gui.py`）與可打包的 Windows EXE。維護重點：CLI/GUI 穩定性、
跨平台安裝、YouTube URL 格式支援、公開影片/Shorts/直播篩選、以頻道計的冪等下載。

## 目前入口

- CLI 主程式：`yt_fetch.py`（`yt-fetch` console script）
- GUI：`yt_fetch_gui.py`（`--gui` 或 `yt-fetch-gui`）
- 打包：`yt_fetch.spec` + `build_exe.py`；CI `.github/workflows/release.yml`（v* 標籤觸發）
- 測試：`tests/`（`test_smoke.py`、`test_gui.py`、`test_cdp_cookies.py`、
  `test_dependency_freshness.py`、`test_release_zip.py`、`test_repository_hygiene.py`、`conftest.py`）
- 文件：`README.md` / `README.en.md`、`docs/ARCHITECTURE.md`、`docs/DEVELOPMENT.md`、
  `docs/RELEASING.md`、`docs/COMPUTER_USE_VALIDATION.md`、`docs/screenshot-workflow.md`、
  `docs/planning/`
- Agent 指引：`AGENTS.md`、`CLAUDE.md`

## 近期完成（roadmap）

- ✅ GUI 桌面介面（背景執行緒下載、即時日誌、可選/開資料夾）。
- ✅ Windows 免安裝 EXE 打包與 release workflow；frozen 時不建 venv、輸出落在 exe 旁。
- ✅ 設定檔 `yt_fetch.ini`（configparser）：優先序 CLI > 環境變數 > ini > 內建；**不保存 cookies**。
- ✅ 多頻道批次下載 `--channels-file`（單一失敗不中斷整批）＋結果報表。
- ✅ 可測化：抽出 `build_channel_urls`、`filter_downloadable_entries`、`find_downloaded_file`、
  `filter_reason`、`is_non_public` 等純函式；目前測試數為 136。
- ✅ UX：`--help` 乾淨輸出、env 數字防呆、Ctrl+C 乾淨退出、cookies 安全提醒。
- ✅ 跨平台 CI（Ubuntu/Windows/macOS）＋ console script、`--help` smoke 與 Python CodeQL。
- ✅ 正確性修正：`--count` 以頻道計、Shorts 不誤殺正常短片、下載偵測 glob bug。
- ✅ v1.4.0：受控瀏覽器登入取得 cookies（解決 Chrome 127+ App-Bound Encryption，
  `chrome_cdp_cookies` 模組 + `--login` + GUI 登入按鈕）；GUI 移除手動 cookies 欄位、
  改自動沿用受控 cookies；cookies 載入失敗自動 fallback；CI 新增 `vermin -t=3.7`
  最低版本相容性檢查。
- ✅ v1.5.0：新增下載畫質選項（CLI `--quality {best,1080p,720p,480p}`、環境變數
  `YOUTUBE_QUALITY`、設定檔 `quality`、GUI「下載畫質」下拉選單）；解析度選項會選擇
  不高於指定上限的最佳可用畫質。
- ✅ v1.6.0：依賴新鮮度維護。`yt-dlp>=2026.6.9`、`imageio-ffmpeg>=0.6.0`，最低 Python
  調整為 3.10+；GUI「檢查更新」會同時提示內嵌 yt-dlp 是否落後 PyPI；新增每月
  `dependency-freshness.yml` 檢查，落後時開 issue 提醒重發 EXE。
- ✅ v1.7.0：完成 README 後續優先項。GUI 支援匯入頻道清單批次下載、ffmpeg 狀態頁、
  下載結果開檔/開資料夾/匯出紀錄、錯誤診斷提示與快速設定 profiles；核心抽出
  `build_ytdlp_options()`，release 文件補上 notes 必填欄位。
- ✅ v1.9.0：依 planning 評估後實作有價值且不破壞免安裝 EXE 的項目：標題包含／排除、
  上傳日期區間、影片長度區間等進階篩選，以及字幕／自動字幕下載；CLI、GUI、設定檔、
  README 中英文與 planning 文件同步。
- ✅ v1.9.1：GUI layout patch。預設啟動最大化、改為左右工作區，並修正字幕勾選項與登入
  cookies 說明文字在預設畫面中的截斷／不自然換行。
- ✅ v1.9.2：只接受 HTTPS YouTube URL；修正合法 cookies 下會員／Premium／需登入候選遭
  提早排除；受控 Chrome 限 loopback 並縮小 cookies 網域；更新 `yt-dlp` 至 `2026.7.4`，
  補上 CodeQL 與新版 Release Actions。

當前版本：`1.9.2`（pyproject、__version__ 與 CHANGELOG 同步；`v1.9.2` GitHub Release
已發布，正式 Windows ZIP 的 checksum、CRC、壓縮結構與解壓均已驗證）。

## 已知注意事項

- `download/`、`yt_fetch.ini`、cookies 檔皆為本機輸出，不進版控（已列入 `.gitignore`）。
- 下載真實影片不適合放入自動化測試；GUI 需顯示器，故 pytest 只測純邏輯（tkinter 延遲匯入）。
- YouTube 頁面與 yt-dlp 行為會變動，相關 bug 先確認 yt-dlp 是否為最新版；EXE 會固定打包建置當下的 yt-dlp。
- `v*` 標籤會觸發 `.github/workflows/release.yml` 建置 Windows EXE 並發佈 GitHub Release。
- `download_videos()` 仍是較大的協調函式（掛 `# noqa: C901`），新增邏輯優先抽純函式並補測試。

## 建議下一步

1. 依實際下載錯誤回報擴充核心錯誤診斷分類與提示表，讓 CLI/GUI 同步受益。
2. 若 GUI 版面再調整，重跑 `tools/generate_readme_screenshot.py` 並同步 README 中英文截圖。
3. 只有在 `yt-dlp` / `imageio-ffmpeg` 落後、YouTube 行為變動或核心修正需要使用者取得新版 EXE 時，再切 tag 重發。
