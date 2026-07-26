# 功能實作狀態對照表

本文件整理 `yt_fetch` 目前相對於規格與 roadmap 的完成狀態。舊版逐行對照已移除，避免程式重構後行號失準；後續維護請以功能入口與測試覆蓋為主。

## 產品定位

- 目標是輕巧、可攜、具 GUI、簡潔易懂的 YouTube 頻道影片個人備份工具。
- CLI 是穩定入口；Tkinter GUI 是一般使用者的主要介面；Windows EXE 是免安裝發佈形式。
- 不做大型萬用下載器、Web 服務、排程守護程式或大量平行下載器。
- cookies 只用於使用者本人已授權可觀看的內容，不繞過付費牆、會員限制、私人影片或其他存取控制。

## 已完成項目

### 下載核心

- 從指定 YouTube 頻道下載最新 N 支影片。
- 支援 `@handle`、頻道 ID、HTTPS YouTube URL、`/videos`、`/shorts` 與 playlist URL 正規化；
  拒絕 HTTP、外部主機、內嵌帳密與非標準連接埠。
- 以 yt-dlp 擷取清單與下載，強制使用 watch URL 下載，降低 m3u8 與清單 URL 誤用問題。
- 支援 `best`、`1080p`、`720p`、`480p` 畫質選項，解析度選項會選擇不高於上限的最佳可用畫質。
- 使用 ffmpeg 合併影片與音訊；EXE 內可使用 `imageio-ffmpeg` 提供的 ffmpeg。
- 下載結果依頻道名稱存到 `download/<頻道名稱>/`。

### 過濾與冪等

- 預設排除 Shorts，可選擇包含 Shorts。
- 排除 live、upcoming、was_live 等直播／預告／直播回放項目。
- 以 yt-dlp archive 與檔名中的 video id 避免重複下載。
- `--count` 以單一頻道為單位計算，不會被其他頻道已下載項目影響。
- 清單改用 flat extraction；沒有 cookies 時只保留公開候選，有合法 cookies 時把會員／Premium／
  需登入候選交由 YouTube 驗證帳號資格。私人與未列出影片一律拒絕；失敗項目會往後補候選直到
  達到目標或候選耗盡。

### GUI 與 EXE

- Tkinter GUI 已完成：下載設定、批次清單、輸出資料夾、下載結果與執行日誌分區。
- GUI 下載在背景執行緒進行，保留即時進度條、日誌與結果列表。
- GUI 支援匯入頻道清單、開啟下載檔案／資料夾、匯出紀錄。
- GUI 提供快速設定 profiles 與 ffmpeg 狀態頁。
- Windows EXE 由 GitHub Actions 在 `v*` tag 自動建置並附 `.sha256` 發佈。

### cookies 與登入

- CLI 支援 `--cookies-from-browser` 與 `--cookies`。
- Windows/Chrome 支援受控瀏覽器登入，解決 Chrome 127+ App-Bound Encryption 導致外部工具不能直接讀取 cookies 的問題。
- GUI 以「登入 YouTube 取得 cookies」按鈕處理登入，不顯示手動 cookies 欄位。
- 設定檔不保存 cookies 路徑、瀏覽器來源或 cookies 內容。
- 受控 Chrome 只在 `127.0.0.1` 開啟 CDP，匯出也只保留 YouTube 登入所需網域。

### 批次、設定與維護

- 支援 `--channels-file` 多頻道循序批次下載，單一頻道失敗不會中斷整批。
- 支援 `yt_fetch.ini` 記住常用設定；優先序為 CLI > 環境變數 > ini > 內建預設。
- 支援速率限制、下載間隔、重試次數與環境變數設定。
- 依賴新鮮度 workflow 每月比較 repo 宣告的 `yt-dlp` / `imageio-ffmpeg` 基線與 PyPI；
  Dependabot 每週檢查全部 Python 直接依賴與 GitHub Actions；被必要 CI 直接覆蓋的更新會
  自動核准，並透過全域序列在必要時 rebase，再合併／關閉／刪分支。
- README 中英文、CHANGELOG、發行流程文件與接手文件已建立。

### 測試與品質

- 測試涵蓋 URL 正規化、過濾、archive、頻道目標計算、批次報表、GUI 表單解析、受控 cookies 模組、依賴新鮮度與下載流程 helper。
- 本地驗證鏈為 `pytest`、`black --check`、`isort --check-only`、`flake8`、`py_compile`、`yt_fetch.py --help`。
- CI 覆蓋 Ubuntu、Windows、macOS 與多個 Python 版本。
- CodeQL `security-extended` 在 push、PR 與每週排程建立 Python SAST 基線。

## 已收斂的原 planning 項目

- 批次處理多個頻道：已完成，入口為 `--channels-file` 與 GUI 匯入清單。
- 頻道清單檔案：已完成，每行一個頻道，`#` 為註解。
- 自動整理檔案結構：已完成，依頻道名稱建立子目錄。
- GUI 圖形介面：已完成，且可打包為免安裝 Windows EXE。
- 圖形化進度顯示：已完成，GUI 顯示進度條、日誌與結果。
- 錯誤診斷：已完成，核心分類器與提示表由 CLI/GUI 共用。
- 下載流程拆分：已完成主要 helper 拆分，後續只做局部維護。

## 暫不納入

- Web UI：會把專案推向常駐服務與部署維護，不符合目前免安裝單檔 GUI 定位。
- 下載完成通知、新影片提醒、排程監控：會引入背景常駐、系統通知與排程問題，超出目前工具邊界。
- 大量平行下載：容易造成限流與服務壓力，維持循序保守處理。
- 雲端同步／上傳：涉及第三方帳號、憑證與資料外傳風險，不納入。
- 繞過付費牆、會員限定、私人影片、地區限制或其他無權存取內容：明確禁止。

## 由可選項轉為完成

- 標題關鍵字、日期、長度等進階過濾：已在 v1.9.0 加入 CLI/GUI。
- 字幕下載：已在 v1.9.0 加入 CLI/GUI；僅在影片提供字幕或自動字幕時輸出。
## 可選但非優先

- 格式轉換：目前固定 MP4 輸出較簡單；多格式轉換會增加 ffmpeg 錯誤面與 UI 複雜度。

## 維護原則

- 修改下載行為時，優先改 `build_ytdlp_options()`、`_extract_entries()`、`dedupe_entries()`、`calculate_download_target()`、`prepare_entries_to_download()`、`download_entries_with_ytdlp()` 等 helper，並補測試。
- 新增錯誤診斷時，先改核心分類與提示表，再讓 CLI/GUI 共用。
- GUI 後續只做清晰度與狀態呈現改善，不堆疊大量進階選項；v1.9.1 已改為預設最大化與左右工作區。
- 依賴或 YouTube 行為造成實際下載問題時，才切新版 tag 重發 EXE。

## 狀態總結

- 核心下載功能：完成。
- GUI 與 EXE 發佈：完成。
- cookies 登入與安全邊界：完成。
- 批次下載與結果報表：完成。
- 維護性重構：主要項目完成。
- 剩餘項目：僅保留「可選但非優先」或「暫不納入」分類。

**文件版本**：1.9.2
**最後更新**：2026-07-26
**比對基準**：目前 `main` 分支與 v1.9.2 發行準備
