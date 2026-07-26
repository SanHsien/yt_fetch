# 專案覆核與建議

覆核日期：2026-07-26（Asia/Taipei）
覆核基準：`main` `b90816f`（文件提交前；遠端同步狀態於推送後重驗）

## 結論

專案的核心分層、測試與 Release 流程清楚；本輪已補齊下載產物隔離、CLI 數值防呆與可重跑的
Release ZIP 驗證。但尚不應把目前狀態視為可放心重發 Release：兩項 P1 仍會讓實作偏離
「僅處理 YouTube 且保留使用者既有授權」的邊界，而 Windows EXE 的下載核心已落後 PyPI。
應先補測試並最小修正，再進行使用者主持的實機下載驗收。

## 本次已驗證

- 工作開始時 `HEAD == origin/main == 784bf16` 且工作樹乾淨；推送後同步狀態另於交付前重驗。
- `pytest -q`：**115 passed**；Black、isort、flake8、`py_compile`、vermin（最低需求 3.8）
  與 CLI `--help` 通過。
- GitHub「程式碼檢查」（`925153b`）五個 OS／Python 矩陣均成功。
- `v1.9.1` Release ZIP 已下載到暫存驗證：SHA-256 為
  `f7398cff51369258b7cab9d9e631d87865fd9ddb5327cf454bd299649cf1fb2c`，Windows
  `Expand-Archive` 成功；新增驗證器也確認 CRC 正常，且 ZIP 僅含根目錄下一個非空的
  `yt_fetch.exe`（55,523,515 bytes）。
- 以既有本機 EXE 進行無帳號 GUI smoke：主視窗、說明／語言選單可開啟，關閉後無殘留視窗。
  未執行剛下載的 EXE、登入或真實下載；這些需要使用者當輪授權。
- Dependabot open alerts 為 0。GitHub Code Scanning API 回報尚無分析結果；Secret Scanning API
  因本機 GitHub token 缺少 `admin:repo_hook` scope 無法驗證，不能宣稱其為零。
- 本輪已新增 [`docs/COMPUTER_USE_VALIDATION.md`](docs/COMPUTER_USE_VALIDATION.md)，並同步
  `DEVELOPMENT`、`RELEASING`、`HANDOFF`、`AGENTS` 與 `CLAUDE` 的驗收入口。

## 本輪已修正

- **下載產物隔離不完整**：原 `.gitignore` 只排除 `download/` 根目錄下少數影音副檔名，
  實際的 `download/<頻道名稱>/` 影片、字幕與報告可能被誤提交。已改為排除整個
  `download/`，並加入巢狀輸出回歸測試。修復：`cafb8c6`（2026-07-26）。
- **Release 驗證可能誤用舊暫存內容**：原驗收指令重用固定目錄並允許覆寫，且未獨立驗證
  CRC 與 ZIP 版面。已改用每次唯一目錄，新增 `tools/verify_release_zip.py` 及危險路徑、
  CRC、唯一根目錄 EXE、非空內容測試，並對 `v1.9.1` 資產實跑。修復：`cafb8c6`
  （2026-07-26）。
- **CLI 接受無效執行參數**：`--retries` 可為 0／負數，`--ratelimit` 與 `--sleep` 可為
  負數。現在由 argparse 明確拒絕，並加入四個回歸案例。修復：`cafb8c6`（2026-07-26）。
- **桌面驗收基線少一項 CI gate**：實機文件未列 vermin，且 `py_compile` 不含新驗證工具。
  已與 CI／開發文件同步。修復：`cafb8c6`（2026-07-26）。
- **GitHub Actions 使用淘汰的 Node.js 20 runtime**：推送後 CI 雖成功，但
  `actions/checkout@v4` 與 `actions/setup-python@v5` 產生 runtime 淘汰警告。已依官方最新
  release 將三個 workflow 統一升級至 v7；最終 CI 狀態於交付前重驗。修復：`b90816f`
  （2026-07-26）。

## 未解決問題

### P1：已授權會員內容會在下載前被排除

`_extract_entries()` 固定以 flat 模式取得清單，之後 `filter_downloadable_entries()` 呼叫
`is_public_video()`；後者與其單元測試明確把 `availability="subscriber_only"` 視為不可下載。
因此使用者原本有權觀看的會員內容不會進入 yt-dlp 的實際權限驗證，和 README 所稱的已授權
會員下載及 v1.7.2 的設計意圖衝突。

建議：將「私人／刪除」與「需要登入才可能可下載」分開；後者僅在提供合法 cookies 時保留到
yt-dlp 實際驗證，未授權時仍由服務端拒絕。先補 `subscriber_only` 的有／無 cookies、private
永不嘗試、成功後回填的回歸測試。

### P1：`--channel` 接受任何 HTTP URL

`normalize_channel_url()` 只要字串以 `http` 開頭就原樣回傳，非 YouTube 網域也會交給 yt-dlp。
這違反本專案僅處理指定 YouTube 頻道的範圍，並使使用條款、輸出結構與錯誤提示可能被套用到
其他網站。

建議：以 `urllib.parse.urlparse()` 驗證 HTTPS 與允許的 YouTube host（含必要短網址）；拒絕
`http`、`youtube.com.example` 與其他站點，同時保留 `@handle`、`UC...`、channel／playlist URL。
先補正常與拒絕案例的單元測試。

### P2：受控登入未採最小權限處理 cookies

兩個 Chrome 啟動路徑都傳入 `--remote-allow-origins=*`，且 `Storage.getCookies`／
`Network.getAllCookies` 的結果會完整寫入本機 cookies 檔。雖使用隨機本機連接埠，仍應明確
限制 remote-debugging address 至 `127.0.0.1`、驗證可移除萬用 origin，並把寫入範圍縮到
YouTube 登入真正需要的網域。這是憑證防護強化，非已知外洩事件。

### P2：已發布 EXE 的 `yt-dlp` 已落後

本機依賴檢查顯示已打包／安裝的 `yt-dlp` 為 `2026.6.9`，PyPI 最新為 `2026.7.4`；
`imageio-ffmpeg` 仍是最新。因 YouTube 介面變動頻繁，應更新依賴、跑本文件的自動與
使用者主持驗收後切新的 tag。`>=` 只會幫新安裝取得新版，不會更新既有 EXE。

### P2：缺少可驗證的程式碼掃描基線

Code Scanning API 回 `no analysis found`，目前 workflows 也沒有 Python CodeQL／等效 SAST。
Dependabot 為零不代表程式碼層安全掃描已完成，尤其本專案處理本機 cookies 與 CDP。

建議：新增最小 Python CodeQL workflow，或明確採用其他可在 CI 留存結果的 SAST；另用有足夠
權限的維護者 token 確認 Secret Scanning 的啟用與目前狀態。

### P3：yt-dlp options 有重複鍵值，GUI 自動化可觀測性不足

`build_ytdlp_options()` 重複宣告 retries、archive、字幕、progress hook 與 playlist 相關鍵值；
目前後者覆寫前者而未造成行為差異，但會提高未來修改風險。另本次 Computer Use 實測中，Tk
選單子項只提供 Automation ID、未提供可讀名稱，代理不能僅以 accessibility tree 判斷操作結果。

建議：刪除重複 options；GUI 方面保留本輪新增文件的「每步重新截圖」規則，並在後續 UI 調整時
評估補可讀的 accessibility name 或可觀測的狀態文字。

## 建議順序

1. 先以測試修正兩項 P1，再同步 README／中英文說明與安全提示。
2. 收緊 CDP cookies 範圍，加入 SAST，更新 `yt-dlp` 至 `2026.7.4`。
3. 建置候選 EXE，依 `COMPUTER_USE_VALIDATION.md` 先做無帳號 smoke。
4. 由使用者以自己的公開或已授權內容，完成單支下載、冪等、未授權拒絕與（若需要）登入驗收。
5. 所有必要項目 PASS 後才切新 tag；修 bug 時回註本檔的修復 commit 與日期。
