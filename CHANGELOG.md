# 更新日誌

所有重要的變更都會記錄在這個檔案中。

格式基於 [Keep a Changelog](https://keepachangelog.com/zh-TW/1.0.0/)，
本專案遵循 [語義化版本](https://semver.org/lang/zh-TW/)。

## [未發布]

### 修正
- 修正依賴新鮮度排程安裝最新版後再與 PyPI 最新版比較、因而可能長期誤報 `OK` 的問題；
  現在會比較 repo 宣告的版本基線，查詢失敗也會建立維護提醒。

### 維護
- 新增每週 Dependabot 檢查，涵蓋 Python 執行期／開發／建置依賴及 GitHub Actions。
- 依賴新鮮度報告會寫入 Actions Job Summary，依賴恢復最新時自動關閉既有提醒 issue。
- 新增 Dependabot 風險判斷與守門合併：CI 直接覆蓋的低風險開發工具或 Actions patch、minor 更新，僅在
  五平台 CI 與 CodeQL 全數通過後自動核准並 squash merge；重大版本、執行期依賴、未知
  metadata、發布／打包工具或超出預期檔案範圍仍須人工審查。
- 合併前再次讀取最新標籤與政策 Check，允許維護者在 workflow 已啟動後撤銷自動合併。

## [1.9.2] - 2026-07-26

### 修正
- 完整排除 `download/` 及其頻道子目錄，避免影片、字幕、報告或下載紀錄誤入 Git。
- CLI 拒絕小於 1 的重試次數，以及負數速率限制與等待秒數。
- 修正使用合法 cookies 時，會員／Premium／需登入候選會在 yt-dlp 驗證帳號資格前遭提早
  排除的問題；私人與未列出影片仍一律拒絕，cookies 載入失敗回退公開模式時也會立即恢復
  公開內容過濾。
- 頻道 URL 只接受 HTTPS YouTube 主機，拒絕 HTTP、外部主機、內嵌帳密與非標準連接埠。
- 排除依賴新鮮度工具產生的 Markdown 報告，避免本機維護產物誤入 Git。

### 安全
- 受控 Chrome 的 CDP 只監聽 `127.0.0.1`，移除萬用 remote origin。
- cookies 匯出只保留 YouTube 登入所需的 `youtube.com`、`google.com` 與
  `googlevideo.com` 網域，不再寫入其他瀏覽紀錄。
- 新增 Python CodeQL `security-extended` 掃描，建立可在 GitHub 留存的 SAST 基線。

### 依賴
- 將 `yt-dlp` 最低版本更新至 `2026.7.4`。
- Release workflow 更新至 `actions/upload-artifact@v7` 與
  `softprops/action-gh-release@v3`。

### 驗證
- 新增 Release ZIP 驗證工具與測試，檢查 CRC、危險／重複路徑、唯一根目錄 EXE 與非空內容。
- Windows 實機驗收改用每次唯一的暫存目錄，並納入 ZIP 版面與 Python 3.10 相容性檢查。
- GitHub Actions 升級至 Node.js 24 runtime 的 `checkout`／`setup-python` v7。
- 補上 URL 邊界、已授權候選、cookies fallback、CDP 監聽與 cookies 網域最小化的回歸測試。

## [1.9.1] - 2026-07-04

### GUI
- GUI 改為啟動時預設最大化；主畫面由垂直堆疊改為左右分欄，左側放設定／批次／輸出，右側放進度、下載結果與日誌，降低預設畫面的擁擠感。
- 修正「下載字幕／自動字幕」勾選項在 GUI 中被欄位擠壓截斷的問題。
- 調整登入 cookies 說明文字為固定短句換行，避免預設視窗中出現不自然斷行。

## [1.9.0] - 2026-07-04

### 新增
- 新增進階篩選：`--title-include`、`--title-exclude`、`--date-after`、
  `--date-before`、`--min-duration`、`--max-duration`，可依標題、上傳日期與影片長度限制下載候選。
- 新增字幕下載選項：`--write-subs` 與 `--sub-langs`，可在影片提供時下載字幕／自動字幕。
- GUI 新增「進階篩選與字幕」區塊，對應 CLI 新功能且仍維持免安裝 EXE 架構。

### 修正
- 將直播／預告排除邏輯也接到 yt-dlp `match_filter`，避免 flat 清單缺少 `live_status`
  時把直播交給下載階段處理。

### 文件
- 將原 `idea/` 規劃文件併入 `docs/planning/`，避免與 IDE 設定資料夾混淆並集中專案文件入口。
- 重寫 `docs/planning/implementation-status.md` 與 `docs/planning/yt-fetch-spec.md`，移除過時的 v1.0 行號、
  Python 3.7、無 GUI、舊輸出路徑與未實作清單說法，改以目前 v1.9.0 狀態維護。
- 更新 `docs/ARCHITECTURE.md` 與 `AGENTS.md` 的輸出描述，反映 v1.8.0 起下載依頻道名稱分子目錄
  （`download/<頻道名稱>/`）。
- 更新 README 中／英文發展路線圖，明確區分已完成的維護推進與後續下載核心、錯誤診斷、
  GUI、發布維護方向。
- 將 Web UI、通知、排程守護程式、大量平行下載等項目整理為暫不納入；標題／日期／長度過濾
  與字幕下載則評估為有價值且已於 v1.9.0 實作，格式轉換保留為可選但非優先項目。

### 重構
- 繼續拆分 `download_videos()`：抽出 ffmpeg 準備、progress hook、match filter、
  候選掃描數量與下載選項日誌 helper，降低主流程維護成本。
- 抽出 yt-dlp 下載階段致命錯誤處理 helper，讓後續 CLI/GUI 共用診斷更容易推進。
- 將錯誤診斷提示文字集中到核心模組，CLI 與 GUI 共用同一套分類與提示表。
- 抽出下載候選清單整理 helper，集中處理去重、目標數、過濾與摘要日誌。

### GUI
- 以分區標題整理 GUI：下載設定、批次清單、輸出資料夾、下載結果與執行日誌，降低畫面密度。

### 測試
- 補上候選掃描數量、progress hook 與 ffmpeg 準備 helper 測試。
- 補上 yt-dlp 下載錯誤處理 helper 測試。
- 補上共用錯誤診斷提示與下載候選清單整理 helper 測試。

## [1.8.0] - 2026-07-04

### 變更
- 下載改為依**頻道名稱**分子目錄：`download/<頻道名稱>/%(title)s [%(id)s].mp4`，
  避免多個頻道的影片混在同一層。下載紀錄 `download/.download_archive.txt` 仍為共用；
  已下載偵測改為遞迴掃描所有子目錄，並相容舊版直接放在 `download/` 根目錄的檔案。（附測試）

## [1.7.2] - 2026-07-04

### 修正
- 修正頻道抽清單在頻道含大量會員限定影片、或目標數量較大（playlistend 較大）時，
  常整批回傳 0 支、報「無法取得頻道資訊」的問題。原因是抽清單用非 flat（逐支完整解析），
  遇會員限定影片會逐支解析失敗、且大量逐支解析易被 YouTube 節流。改為抽清單一律用
  flat（`extract_flat="in_playlist"`，只取影片清單），是否公開／會員／直播的判斷與實際
  下載一起留到下載階段處理——公開影片照常下載，會員影片在你已登入（且為該頻道會員）時
  才會成功、否則跳過該支不影響整批。（附回歸測試）
- 下載遇到跳過（會員限定、非公開、失敗等）時會往後補下載後續影片，直到達成使用者設定的數量；
  並放寬候選掃描上限（抽清單已改 flat 很便宜）為「至少 50、約 count×5、最多 200」，
  確保會員影片較多的頻道也有足夠候選填滿目標數量。（附回填測試）

## [1.7.1] - 2026-07-02

### 修正
- 修正打包 EXE 在未偵測到系統 ffmpeg 時，`install_ffmpeg()` 會以 `sys.executable -m pip` 執行——
  frozen 模式下 `sys.executable` 是 EXE 本身，會誤啟第二個 GUI 視窗並卡住；改為 frozen 時跳過
  pip 安裝、直接使用內嵌的 imageio-ffmpeg。
- `chrome_cdp_cookies` 補上 `CloseHandle` 的 ctypes 參數型別宣告，避免 64 位元 handle 被預設的
  `c_int` 截斷。
- 移除 `get_installed_package_version()` 內給 Python 3.7 用的 `importlib_metadata` 後援
  （專案最低版本為 3.10，屬永遠不會執行的死碼）。

### 文件
- 重寫 README 中／英文發展路線圖，改為條列式，不再分短期／中期／長期，聚焦已完成基礎、維護原則與發布維護。
- 修正 CONTRIBUTING 殘留的 Python 3.7 說法（版本宣告與 vermin 目標改為 3.10，vermin 目標語法改為
  `-t=3.10-`）；SECURITY 支援版本表由 1.0.x 更新為 1.7.x。
- README 中／英文互動模式範例補上「下載畫質」詢問；修正 Shorts 過濾說明——實際只排除 URL 含
  `/shorts/` 或「時長 < 60 秒且標記為 shorts」的影片，未標記的正常短片不會被排除。
- AGENTS/CLAUDE/ARCHITECTURE/HANDOFF 對齊目前模組結構（GUI、`chrome_cdp_cookies`、tools）與
  檢查指令；HANDOFF 測試數更新為 84。
- CI 與各文件的檢查指令一致納入 `build_exe.py`（py_compile、vermin、black、isort、flake8）。

### 重構
- 抽出 entries 去重、本頻道下載目標計算與逐支下載迴圈 helper，降低 `download_videos()` 後續維護成本。
- 將常見錯誤文字分類移到核心模組，GUI 只負責顯示對應語系提示。

### 測試
- 補上錯誤分類、entries 去重、下載目標計算與逐支下載迴圈的純邏輯測試。
- 新增 frozen 模式 `install_ffmpeg()` 不執行 pip 的回歸測試。

## [1.7.0] - 2026-07-02

### 新增
- GUI 新增「匯入頻道清單」批次下載入口，對應 CLI `--channels-file`，維持循序下載與單一頻道失敗不中斷整批。
- GUI 新增「ffmpeg 狀態」選單，可顯示目前使用系統 ffmpeg 或 `imageio-ffmpeg`，以及版本與路徑。
- GUI 新增下載結果清單，可開啟單一檔案、開啟所在資料夾，並匯出本次下載紀錄。
- GUI 新增錯誤診斷提示，針對 cookies、權限/會員資格、限流、ffmpeg、磁碟權限等常見錯誤給出下一步。
- GUI 新增快速設定 profiles：最佳畫質、省空間 720p、低畫質 480p。

### 變更
- 抽出 `build_ytdlp_options()`，集中組裝 yt-dlp options，降低 `download_videos()` 後續改動風險。
- Release 流程文件補上 release notes 必填內容：內建 `yt-dlp` 版本、主要功能、已知限制與 SHA256。
- 重新產生 README GUI 截圖，顯示批次清單、快速設定與下載結果操作。

## [1.6.1] - 2026-07-02

### 修正
- 修正 README 中／英文仍殘留舊 GUI cookies 欄位說法的問題；目前 GUI 沒有手動 cookies 欄位，
  需要登入時改按「登入 YouTube 取得 cookies」，之後會自動沿用受控 cookies。
- 調整 README 對專案邊界的描述，改以「保守存取邊界」說明，避免和已授權登入 cookies 功能互相矛盾。
- 更新截圖流程文件，讓示範參數說明包含目前 GUI 的下載畫質欄位。

## [1.6.0] - 2026-07-02

### 新增
- GUI「檢查更新」同步檢查目前內嵌的 `yt-dlp` 版本與 PyPI 最新版本；若 EXE 下載核心落後，
  會提醒使用者更新 EXE 或從原始碼更新 `yt-dlp`。
- 新增 `tools/check_dependency_freshness.py` 與每月排程 `.github/workflows/dependency-freshness.yml`，
  定期檢查 `yt-dlp` / `imageio-ffmpeg` 是否落後，必要時建立或更新維護 issue。

### 變更
- 依賴下限更新為 `yt-dlp>=2026.6.9`、`imageio-ffmpeg>=0.6.0`。
- 因最新版 `yt-dlp` 已要求 Python 3.10+，專案最低 Python 版本與 CI matrix 同步調整為 Python 3.10+。
- README 中／英文 roadmap 補上依賴新鮮度、EXE 下載核心提醒，以及後續 GUI/ffmpeg/錯誤診斷優先順序。

## [1.5.0] - 2026-07-02

### 新增
- 新增下載畫質選項：CLI `--quality {best,1080p,720p,480p}`、環境變數 `YOUTUBE_QUALITY`、
  設定檔 `quality` 與 GUI「下載畫質」下拉選單。預設 `best` 維持既有行為；選擇解析度時會
  下載不高於指定上限的最佳可用畫質。
- 新增 `build_format_selector()` 純函式與測試，固定 yt-dlp format selector 的產生規則。

### 文件
- 對齊所有界線/政策文件措辭與 v1.4.0 功能一致且誠實（`AGENTS.md`、`CLAUDE.md`、`SKILL.md`、
  `SECURITY.md`、`NOTICE.md`、`docs/third-party-youtube-tooling.md`）：明確區分「繞過/存取無權內容」
  （禁止）與「以自己登入下載自己有權觀看的內容、含自己付費的會員影片」（允許）；cookies 改為
  「本機抽取自己的、絕不外傳」，不再宣稱「不取得/不處理 cookies」。
- 在 README 中／英文開頭、GUI「關於」對話框與專案描述強調亮點：**可登入下載你自己付費／訂閱的
  頻道會員影片**（已授權存取、非繞過）；同步修正 GUI 關於原本「只處理公開內容／不保存 cookies」
  的過時說法。
- 更新 README 中／英文「暫不做」界線措辭，使其與 v1.4.0 的 cookies 功能一致且誠實：
  受控登入會在「本機」抽取並使用「使用者自己」的 cookies（存於本機 `cookies.txt`、絕不外傳），
  界線改為「不外傳／分享／交換／外洩給第三方」；並澄清下載自己付費的會員影片屬「已授權存取」、非繞過。
- 更新 README 中／英文、接手文件與截圖，說明畫質選項與 GUI 下拉選單。

## [1.4.0] - 2026-06-30

### 新增
- **受控瀏覽器登入取得 cookies（Windows/Chrome）**：解決 Chrome 127+ App-Bound Encryption
  導致 yt-dlp 無法直接讀取 Chrome cookies 的問題。新增 `chrome_cdp_cookies` 模組：開一個
  本工具專屬、獨立 user-data-dir 的 Chrome 實例（不受 Chrome 136+ 對預設資料夾 remote
  debugging 的限制），讓使用者在其中登入 YouTube，再透過 Chrome DevTools Protocol 取得
  Chrome 自行解密的明文 cookies，寫成 cookies.txt 並持久重用、可 headless 自動刷新。
  - CLI：`yt_fetch --login` 進行一次性登入。
  - GUI：新增「登入 YouTube 取得 cookies」按鈕。
  - 下載時若指定 Chrome 系 `--cookies-from-browser`，會自動改用這份受控 cookies。
  - 邊界不變：僅取得使用者自己機器、自己登入、自己有權存取的 cookies；不繞過任何
    會員／付費／年齡／地區限制（伺服器端仍以帳號權限為準）。

### 變更
- GUI 移除「瀏覽器 cookies」與「cookies 檔案路徑」兩個手動輸入欄位及其相關程式碼；
  改由「登入 YouTube 取得 cookies」按鈕提供，下載時自動沿用受控登入 cookies。
  CLI 的 `--cookies-from-browser` / `--cookies` 仍保留（Firefox、自備 cookies.txt 等用途）。
  README 中／英文「cookies 怎麼填」段落改寫為 GUI（登入按鈕）vs CLI（兩個參數）。
- README 中／英文新增「受控瀏覽器登入取得 cookies」說明，含 Chrome 127+ ABE 背景、使用方式，
  以及「下載你自己付費／訂閱的會員影片」之使用情境與界線（不繞過未付費的會員／付費牆）。
- GUI 新增登入功能的選填說明文字（強調公開影片不需登入）。
- 重新產生 README GUI 截圖（含新的登入按鈕與說明）；截圖腳本改用中性示範下載路徑，
  避免洩漏真實使用者路徑；README 中／英文補上「截圖由 tools/generate_readme_screenshot.py 產生」之引用。
- 更新 README 中／英文 GUI 截圖與說明，使畫面包含目前的進度條狀態。
- 同步英文 README roadmap 與中文版完成狀態，並修正接手／貢獻文件中的本地檢查指令。
- README 與 GUI 關於視窗補上專案定位：輕巧、可攜、具 GUI、簡潔易懂的免安裝單檔程式。
- README 中／英文補充瀏覽器 cookies 與 cookies 檔案路徑差異；GUI cookies 欄位加上簡短提示。

### 修正
- 修正 `chrome_cdp_cookies.py` 一處 f-string 的 `{}` 內含反斜線（`\r\n`），這在 Python 3.12
  以前是語法錯誤，導致 CI 的 3.7／3.11 測試於 import 階段失敗（3.12+ 才允許）。
- CI 強化以避免重演：`py_compile` 與 black/isort/flake8 納入 `chrome_cdp_cookies.py` 與 `tools/`；
  新增 `vermin -t=3.7` 最低版本相容性檢查（在新版 Python 上靜態攔截 3.8+ 才有的語法）。
- 修正 `--cookies-from-browser chrome:Default` 等 profile 格式未正確傳給 yt-dlp 的問題。
- cookies 載入失敗時改為明確提示 cookies 錯誤與修復方式，不再誤報為頻道 URL 錯誤。
- cookies 載入失敗（例如 Chrome App-Bound Encryption 擋住讀取）時，不再直接以退出碼 1 中止；
  改為自動 fallback 為「無 cookies」模式重試一次，讓公開頻道仍可順利下載（公開內容本不需 cookies）。
  仍會輸出 cookies 失敗提示；若無 cookies 也無法取得清單，才回報「無法取得頻道資訊」。

## [1.3.0] - 2026-06-30

### 新增
- GUI 下載進度條：沿用 yt-dlp `progress_hooks`，由核心下載流程透過 progress callback 回報至 Tkinter 主執行緒。
- `download_videos()` mock `yt_dlp` 測試，覆蓋基本提取、下載成功判斷與 progress callback，不連線 YouTube。
- GUI 選單列：「說明 → 關於 / 檢查更新」與「語言」中／英文切換（即時套用、記憶於設定檔）。
  關於顯示版本與授權/安全聲明；檢查更新只查 GitHub 最新版本並提示，**不自動下載**
- GUI 中英文語系（`detect_language`：設定檔 > 系統語系 > 預設中文）
- 程式圖示 `assets/yt_fetch.{png,ico}`：GUI 視窗圖示與 EXE 圖示；png 隨 exe 打包
- 版本資訊 `__version__` 與更新檢查輔助（`parse_version`、`is_newer_version`、`fetch_latest_release_tag`）
- 多頻道批次下載：`--channels-file <檔案>`（或環境變數 `YOUTUBE_CHANNELS_FILE`），
  每行一個頻道 URL/ID/@handle（`#` 為註解）。單一頻道失敗（含致命錯誤）不會中斷整批，
  結束後輸出每頻道成功/失敗與下載數的總結報表（roadmap 項目 6、7）
- 單一頻道下載結束亦補上 archive 路徑於結果摘要

### 修正
- GUI 表單驗證錯誤訊息納入中／英文 i18n，英文介面不再跳出中文驗證 popup
- Windows 下含中文／`✓` 的輸出會因 cp1252 拋 `UnicodeEncodeError`：啟動時將 stdout/stderr 重設為 UTF-8，
  CI 亦設定 `PYTHONUTF8=1`（修好跨平台 CI 的 Windows job）
- README 徽章：CI 徽章釘選 `branch=main`；將永遠「no status」的 release workflow 徽章換成 release 版本徽章
- README 中／英補上 Windows EXE 內嵌 `yt-dlp` 可能過期，以及未簽章 EXE 可能觸發 SmartScreen 的說明

### 變更
- `--help` / `-h` 現在乾淨輸出：略過 venv 準備、不印啟動 banner、也不建立設定檔（roadmap UX 修正）
- `--cookies` / `--cookies-from-browser` 說明補上安全提醒（僅用於自己有權存取的內容、cookies 不被保存）
- CI 擴充跨平台驗證：新增 Windows / macOS runner（Python 3.12），統一以 bash 執行步驟；
  新增 `python yt_fetch.py --help` 與 `yt-fetch` console script 的 smoke、editable install 檢查
- 新增 `docs/RELEASING.md`：版本號規則、發布前檢查清單、GitHub Release 流程、PyPI 可行性評估
- 補測試：`--help` 乾淨輸出、`normalize_channel_url` 對 `/videos`、`/shorts`、playlist URL 的原樣保留

## [1.2.0] - 2026-06-29

### 新增
- 圖形介面（Tkinter）：`python yt_fetch.py --gui`，或安裝後的 `yt-fetch-gui` 指令。
  薄層設計，沿用 `download_videos` 核心邏輯；下載於背景執行緒、主視窗不阻塞，
  即時顯示日誌與下載結果，可選擇／開啟下載資料夾；不保存 cookies 內容
- `yt_fetch_gui.parse_form_values()` 純函式（表單值解析與驗證）及其單元測試
- Windows 免安裝 EXE 打包：`yt_fetch.spec` + `build_exe.py`（PyInstaller，內嵌 yt-dlp 與 ffmpeg），
  以及 `.github/workflows/release.yml`——推送 `v*` 標籤時在 Windows 自動建置 exe、產生 zip 與
  `.sha256` 並發佈到 Releases。新增 `[build]` 選用相依（pyinstaller）
- 設定檔（INI）持久化：程式旁的 `yt_fetch.ini`（`configparser`，零新依賴），首次執行自動產生
  附註解的預設值。GUI 啟動時讀取為初始值、按下載時寫回（記住頻道、數量、重試、是否含 Shorts、
  速率、間隔、下載資料夾）。優先序：CLI 參數 > 環境變數 > 設定檔 > 內建預設；
  **cookies（檔案路徑與瀏覽器來源）一律不寫入**，守住不保存 cookies 的硬邊界
- README（中／英）新增畫面截圖與 EXE 下載說明；`tools/generate_readme_screenshot.py`
  可重現地產生 `docs/screenshots/main-window.png`，流程記於 `docs/screenshot-workflow.md`

### 變更
- 將 `availability` 非公開判斷抽為共用的 `is_non_public()`，供 `is_public_video` 與 `filter_reason` 共用，去除重複邏輯
- `requirements.txt` 加註以 `pyproject.toml` 為依賴權威來源，降低兩處漂移風險
- `ARCHITECTURE.md` 補上抽出的可測試純函式列表

### 修正
- 打包為 exe（`sys.frozen`）時不再嘗試建立 venv／重啟，且 `download/` 等輸出改以執行檔所在目錄為基準
- 數字型環境變數（`YOUTUBE_COUNT` / `YOUTUBE_RETRIES` / `YOUTUBE_RATELIMIT` / `YOUTUBE_SLEEP`）填入非數字時，改為警告並回退預設值，不再於啟動時拋出 traceback（新增 `env_int` / `env_float`）
- 非 venv 啟動時重啟前不再先印一次橫幅，避免重複輸出
- `prompt_user_input()` 在非互動式終端機（pipe／CI／無 tty）時改為明確退出並提示改用 `--channel`，不再卡住或拋出 EOF 例外
- 主程式攔截 `KeyboardInterrupt`（Ctrl+C），以退出碼 130 乾淨結束，不再印出 traceback

## [1.1.0] - 2026-06-29

### 新增
- GitHub Actions 工作流程用於自動程式碼檢查
- Issue 和 Pull Request 模板
- CONTRIBUTING.md 貢獻指南
- CHANGELOG.md 更新日誌
- `tests/test_smoke.py` 基本 smoke test，CI 執行 pytest
- CI 加入 black / isort / flake8 風格與靜態檢查
- CONTRIBUTING 補充本地測試與風格檢查指令
- README 技術細節依賴改為 yt-dlp、imageio-ffmpeg
- `pip install -e ".[dev]"` 可安裝 pytest；`yt-fetch` CLI 指令（`pip install -e .` 後可用）
- pre-commit flake8 忽略 D（docstring）規則，避免雜訊
- 抽出可測試的純函式並補上單元測試（測試數 2 → 27）：
  `filter_reason`、`read_archive_ids`、`archive_contains`、`find_downloaded_file`、
  `build_channel_urls`、`filter_downloadable_entries`，並涵蓋 `is_public_video`、
  `get_downloaded_ids`、`normalize_channel_url`

### 修正
- `--count` 改以「該頻道」實際重疊的影片數量計算下載目標，不再被其他頻道的下載紀錄誤判為已達標而漏抓
- Shorts 篩選不再把「時長 < 60 秒但未標記 shorts」的正常短片誤殺，改以 `/shorts/` URL 與標題/描述標記為準
- 修正下載完成偵測中 `glob` 以 `[{id}]` 比對的 bug（中括號被當成字元類別，永遠比不到），改以結尾字串比對
- 修正 docstring 中「ffmpeg 缺少時回退 progressive mp4」的錯誤說明（實際為必須 ffmpeg，自動安裝失敗即中止）

### 變更
- 簡化 `download_videos()`：下載成功偵測從三段冗餘邏輯收斂為「archive 已記錄或檔案存在」，並移除未使用的 `archive_before`
- 移除頻道 URL 上已失效的 `view=0&sort=dd` query 參數（分頁本身即依最新排序）

## [1.0.0] - 2024-12-06

### 新增
- 從 YouTube 頻道下載指定數量的最新影片
- 支援多種頻道識別方式（@handle、頻道 ID、完整 URL）
- 自動下載為 MP4 格式
- 使用 ffmpeg 合併最佳畫質和音質
- 僅下載公開影片（自動過濾非公開內容）
- 預設排除 Shorts（可選包含）
- 自動排除直播內容
- 支援 YouTube 頻道分頁（Videos/Shorts）
- 冪等性保證（重複執行不會重複下載）
- 互動式和命令列雙模式
- 環境變數支援
- 自動環境管理（建立虛擬環境並安裝依賴）
- 自動檢測並安裝 ffmpeg
- 從瀏覽器讀取 cookies（處理年齡/地區限制）
- 使用 cookies 檔案
- 下載速率限制
- 下載間隔延遲（減少被限流）
- 自訂重試次數
- 詳細的下載進度日誌
- 友善的錯誤提示和安裝指引
- 下載結果清單輸出

### 技術細節
- Python 3.7+ 相容
- 跨平台支援（Windows、macOS、Linux）
- 使用 yt-dlp 作為下載引擎
- 使用 imageio-ffmpeg 自動安裝 ffmpeg

---

## 版本說明

- **主版本號**：不相容的 API 變更
- **次版本號**：向下相容的功能新增
- **修訂號**：向下相容的問題修正

[未發布]: https://github.com/SanHsien/yt_fetch/compare/v1.9.2...HEAD
[1.9.2]: https://github.com/SanHsien/yt_fetch/compare/v1.9.1...v1.9.2
[1.9.1]: https://github.com/SanHsien/yt_fetch/compare/v1.9.0...v1.9.1
[1.9.0]: https://github.com/SanHsien/yt_fetch/compare/v1.8.0...v1.9.0
[1.8.0]: https://github.com/SanHsien/yt_fetch/compare/v1.7.2...v1.8.0
[1.7.2]: https://github.com/SanHsien/yt_fetch/compare/v1.7.1...v1.7.2
[1.7.1]: https://github.com/SanHsien/yt_fetch/compare/v1.7.0...v1.7.1
[1.7.0]: https://github.com/SanHsien/yt_fetch/compare/v1.6.1...v1.7.0
[1.6.1]: https://github.com/SanHsien/yt_fetch/compare/v1.6.0...v1.6.1
[1.6.0]: https://github.com/SanHsien/yt_fetch/compare/v1.5.0...v1.6.0
[1.5.0]: https://github.com/SanHsien/yt_fetch/compare/v1.4.0...v1.5.0
[1.4.0]: https://github.com/SanHsien/yt_fetch/compare/v1.3.0...v1.4.0
[1.3.0]: https://github.com/SanHsien/yt_fetch/compare/v1.2.0...v1.3.0
[1.2.0]: https://github.com/SanHsien/yt_fetch/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/SanHsien/yt_fetch/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/SanHsien/yt_fetch/releases/tag/v1.0.0

