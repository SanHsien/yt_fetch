# YouTube 頻道影片下載工具

[English](README.en.md)

[![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![GitHub](https://img.shields.io/badge/GitHub-SanHsien%2Fyt_fetch-lightgrey.svg)](https://github.com/SanHsien/yt_fetch)
[![GitHub stars](https://img.shields.io/github/stars/SanHsien/yt_fetch.svg?style=social&label=Star)](https://github.com/SanHsien/yt_fetch)
[![GitHub forks](https://img.shields.io/github/forks/SanHsien/yt_fetch.svg?style=social&label=Fork)](https://github.com/SanHsien/yt_fetch)
[![GitHub issues](https://img.shields.io/github/issues/SanHsien/yt_fetch.svg)](https://github.com/SanHsien/yt_fetch/issues)
[![GitHub last commit](https://img.shields.io/github/last-commit/SanHsien/yt_fetch.svg)](https://github.com/SanHsien/yt_fetch)

從指定 YouTube 頻道取得最新的 N 支影片並下載為 mp4，儲存到 `download/` 資料夾。

> ⚠️ **重要提醒**：本工具僅供個人學習與研究使用。請遵守 YouTube 服務條款與著作權法。

## 功能特色

- ✅ **自動環境管理**：自動建立虛擬環境並安裝所需套件
- ✅ **跨平台支援**：Windows、macOS、Linux 皆可使用
- ✅ **互動式與命令列雙模式**：可直接執行互動詢問參數，或使用命令列參數快速執行
- ✅ **智能格式選擇**：自動檢測並安裝 ffmpeg，合併最佳畫質和音質
- ✅ **冪等性保證**：重複執行不會下載已存在的影片
- ✅ **僅下載公開影片**：自動過濾私人、未列出、訂閱者專屬等非公開影片
- ✅ **Shorts 過濾**：預設排除 Shorts，可選包含（支援 YouTube 頻道 Videos/Shorts 分頁）
- ✅ **詳細日誌**：完整的下載過程記錄和結果清單
- ✅ **錯誤處理**：友善的錯誤提示和安裝指引

## 系統需求

- Python 3.7 或更高版本
- **ffmpeg**（必需）：用於合併最佳畫質和音質的影片

## 安裝

### 方法一：自動安裝（推薦）

腳本會自動建立虛擬環境並安裝所需套件，無需手動安裝：

```bash
python yt_fetch.py --channel "@channel_handle"
```

### 方法二：手動安裝

如果您想手動管理依賴：

```bash
# 建立虛擬環境
python -m venv .venv

# 啟動虛擬環境
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# 安裝依賴
pip install -r requirements.txt
```

### 方法三：以套件方式安裝（可取得 `yt-fetch` 指令）

若以可編輯模式安裝專案，可使用 `yt-fetch` 指令：

```bash
pip install -e .
yt-fetch --channel "@channel_handle"
```

`yt-fetch` 的參數與 `python yt_fetch.py` 相同。

## 使用方法

### 方法一：互動式執行（推薦新手）

直接執行腳本，會以互動方式詢問所有必要參數：

```bash
python yt_fetch.py
```

執行後會依次詢問：
- **頻道**：YouTube 頻道 URL、ID 或 @handle（必填）
- **目標檔案數**：要下載的影片數量（預設：5，直接按 Enter 使用預設值）
- **是否包含 Shorts**：y/n（預設：n，直接按 Enter 使用預設值）
- **重試次數**：下載失敗時的重試次數（預設：3，直接按 Enter 使用預設值）

### 方法二：命令列參數執行（推薦進階用戶）

直接使用命令列參數執行，無需互動輸入：

```bash
python yt_fetch.py --channel "@channel_handle"
```

### 命令列參數

| 參數 | 說明 | 預設值 | 範例 |
|------|------|--------|------|
| `--channel` | 頻道 URL、ID 或 @handle（未提供時會以輸入視窗詢問） | - | `--channel "@pewdiepie"` |
| `--count` | 下載數量 | 5 | `--count 10` |
| `--include-shorts` | 包含 Shorts（預設排除） | False | `--include-shorts` |
| `--retries` | 重試次數 | 3 | `--retries 5` |
| `--cookies-from-browser` | 從瀏覽器讀取 cookies（處理年齡/地區限制） | - | `--cookies-from-browser chrome` |
| `--cookies` | cookies 檔案路徑（Netscape 格式） | - | `--cookies cookies.txt` |
| `--ratelimit` | 下載速率限制（MB/s，0 表示無限制） | 0 | `--ratelimit 5` |
| `--sleep` | 每次下載之間的延遲秒數（減少被限流） | 0 | `--sleep 2` |

### 環境變數

所有參數都可以透過環境變數設定：

```bash
# Windows (PowerShell)
$env:YOUTUBE_CHANNEL="@channel_handle"
$env:YOUTUBE_COUNT="10"
$env:YOUTUBE_INCLUDE_SHORTS="1"
$env:YOUTUBE_RETRIES="5"
$env:YOUTUBE_COOKIES_BROWSER="chrome"
$env:YOUTUBE_RATELIMIT="5"
$env:YOUTUBE_SLEEP="2"
python yt_fetch.py

# macOS/Linux
export YOUTUBE_CHANNEL="@channel_handle"
export YOUTUBE_COUNT=10
export YOUTUBE_INCLUDE_SHORTS=1
export YOUTUBE_RETRIES=5
export YOUTUBE_COOKIES_BROWSER=chrome
export YOUTUBE_RATELIMIT=5
export YOUTUBE_SLEEP=2
python yt_fetch.py
```

### 頻道 URL 格式

支援多種頻道識別方式：

- **@handle 格式**：`@channel_handle`
- **完整 URL**：`https://www.youtube.com/@channel_handle`
- **頻道 ID**：`UCxxxxxxxxxxxxxxxxxxxxxx`
- **頻道 URL**：`https://www.youtube.com/channel/UCxxxxxxxxxxxxxxxxxxxxxx`

### 使用範例

#### 互動式執行範例

```bash
# 直接執行，會以互動方式詢問所有參數
python yt_fetch.py

# 執行後會詢問：
# 頻道: @channel_handle
# 數量: 10          （直接按 Enter 使用預設值 5）
# 包含 Shorts: n    （直接按 Enter 使用預設值 n）
# 重試次數: 5       （直接按 Enter 使用預設值 3）
```

#### 命令列參數執行範例

```bash
# 下載最新 5 支影片（指定頻道，其他使用預設值）
python yt_fetch.py --channel "@channel_handle"

# 下載最新 10 支影片
python yt_fetch.py --channel "@channel_handle" --count 10

# 包含 Shorts
python yt_fetch.py --channel "@channel_handle" --include-shorts

# 使用完整 URL
python yt_fetch.py --channel "https://www.youtube.com/@channel_handle/videos"

# 使用瀏覽器 cookies 處理年齡/地區限制
python yt_fetch.py --channel "@channel_handle" --cookies-from-browser chrome

# 使用 cookies 檔案
python yt_fetch.py --channel "@channel_handle" --cookies cookies.txt

# 限制下載速率並添加延遲（減少被限流）
python yt_fetch.py --channel "@channel_handle" --ratelimit 5 --sleep 2

# 增加重試次數（網路不穩定時）
python yt_fetch.py --channel "@channel_handle" --retries 5

# 完整參數範例
python yt_fetch.py --channel "@channel_handle" --count 10 --include-shorts --retries 5 --ratelimit 5 --sleep 2
```

## 輸出

下載的影片會儲存在 `download/` 資料夾中，檔名格式為：

```
%(title)s [%(id)s].mp4
```

例如：`我的影片標題 [dQw4w9WgXcQ].mp4`

## 冪等性

腳本會自動記錄已下載的影片，重複執行時不會重複下載：

- 使用 yt-dlp 的 download archive（`download/.download_archive.txt`）
- 檢查檔案名稱中的影片 ID

如果影片已存在，腳本會跳過並顯示「沒有需要下載的新影片」。

## ffmpeg 安裝（必需）

ffmpeg 是必需的，用於合併最佳畫質和音質的影片（會自動合併最佳影片和音訊流）。如果未安裝，腳本會提示錯誤並退出。

### Windows

```bash
# 使用 Chocolatey
choco install ffmpeg

# 或從官網下載
# https://ffmpeg.org/download.html
```

### macOS

```bash
brew install ffmpeg
```

### Linux

```bash
# Debian/Ubuntu
sudo apt-get install ffmpeg

# CentOS/RHEL
sudo yum install ffmpeg

# Fedora
sudo dnf install ffmpeg
```

**注意**：ffmpeg 是必需的，未安裝時腳本會報錯退出。請務必先安裝 ffmpeg。

## 常見問題

### Q: 出現 "ffmpeg not found" 錯誤？

**A:** ffmpeg 是必需的。請安裝 ffmpeg（見上方安裝指引）。腳本會自動檢測並在未找到時提示安裝方法。

### Q: 找不到影片？

**A:** 請確認：
- 頻道 URL 是否正確
- 頻道是否為公開
- 嘗試使用 `@handle` 格式而非完整 URL

### Q: 為什麼有些影片沒有下載？

**A:** 本工具僅下載「可公開觀看的 VOD」，會自動跳過：
- 私人影片
- 未列出影片
- 訂閱者專屬影片
- Premium 專屬影片
- 需要認證的影片
- 直播中（live）、預告（upcoming）、已結束直播（was_live）等 Live 內容

這是為了確保只下載合法可存取、且非直播的公開內容。

### Q: 下載失敗或網路錯誤？

**A:** 嘗試增加重試次數：
```bash
python yt_fetch.py --channel "@channel" --retries 5
```

### Q: 權限錯誤？

**A:** 確保您有寫入 `download/` 資料夾的權限。

### Q: 如何排除 Shorts？會下載直播嗎？

**A:** 預設已排除 Shorts，也不會下載直播。YouTube 從 2022 年起將頻道分為 Videos、Shorts、Live 三個分頁：
- `/videos` 頁面只包含長片（本工具預設只從這裡下載）
- `/shorts` 頁面只包含 Shorts（只有在 `--include-shorts` 時才額外抓取）
- `/live` 與相關直播內容會透過 `live_status` 自動排除，僅保留 VOD

行為說明：
- 當 **不包含 Shorts**（預設）時，本工具只從 `/videos` 頁面獲取，並使用 `match_filter` 進一步排除時長 < 60 秒的影片
- 當 **包含 Shorts**（`--include-shorts`）時，本工具會同時從 `/videos` 和 `/shorts` 兩個頁面獲取，再合併與去重

如需包含 Shorts，使用 `--include-shorts` 參數；直播影片一律不下載。

### Q: 遇到年齡限制或地區限制的影片？

**A:** 使用 `--cookies-from-browser chrome`（或其他瀏覽器）或 `--cookies cookies.txt` 來提供登入 cookies，可以處理年齡/地區限制。注意：這不會繞過付費牆。

### Q: 如何減少被 YouTube 限流？

**A:** 可以使用以下策略：
- `--ratelimit 5`：限制下載速率為 5 MB/s
- `--sleep 2`：每次下載之間等待 2 秒
- 兩者結合使用效果更好

### Q: 如何清除下載記錄？

**A:** 刪除 `download/.download_archive.txt` 檔案即可。

## 退出碼

- `0`：成功（有下載或已冪等）
- `1`：參數錯誤或網路錯誤
- `2`：需要 ffmpeg 但未安裝且無法回退

## 發展路線圖

`yt_fetch` 會維持簡單可用的 CLI，同時優先補上 GUI，讓不熟命令列的使用者也能選頻道、設定數量、查看進度與下載結果。

### 近期目標

#### 1. GUI 桌面介面（最高優先）

目標是做一個薄層桌面介面，沿用現有下載邏輯，不重寫核心流程。

- 輸入頻道 URL、ID 或 `@handle`
- 設定下載數量、是否包含 Shorts、重試次數
- 設定 cookies 來源、下載速率限制、下載間隔
- 選擇或開啟 `download/` 資料夾
- 顯示目前狀態、下載進度、成功/失敗摘要
- 保留 CLI 作為穩定後備入口

完成標準：

- Windows 可直接啟動 GUI。
- GUI 不阻塞主視窗，下載時可看進度。
- 下載行為與 CLI 一致。
- 不保存 cookies 內容，只保存必要設定或路徑。

#### 2. 測試補強

優先補純邏輯測試，不依賴真實 YouTube 網路回應。

- `normalize_channel_url()` 支援格式測試：`@handle`、`handle`、`UC...` 頻道 ID、`/videos`、`/shorts`、playlist URL
- 已下載 ID 解析測試：`download/.download_archive.txt` 與既有檔名中的 `[video_id]`
- Shorts 與直播過濾測試
- cookies、ratelimit、sleep 參數解析測試

完成標準：

- 主要 helper 函式有測試。
- CI 不需要連線 YouTube。
- 修 CLI 或 GUI 行為時能靠測試快速發現回歸。

#### 3. 下載流程可測化

目前主要流程集中在 `download_videos()`。短期先抽出低風險 helper，讓 GUI 與 CLI 能共用。

- 頻道 URL 清單組裝
- `yt-dlp` options 組裝
- entries 去重與篩選
- 下載成功判斷

完成標準：

- `download_videos()` 保留協調流程。
- helper 可用單元測試覆蓋。
- 不改變現有 CLI 介面與預設行為。

### 中期目標

#### 4. 使用者體驗修正

- `--help` 不應輸出啟動 banner 或多餘 log。
- ffmpeg 未安裝時的錯誤訊息保持明確。
- cookies 相關說明補上安全提醒。
- 下載失敗時整理更清楚的下一步建議。

#### 5. 設定檔支援

在不破壞 CLI 的前提下，評估加入簡單設定檔，例如 `yt_fetch.toml` 或 `yt_fetch.json`。

可設定項：

- 預設頻道
- 預設下載數量
- 是否包含 Shorts
- 速率限制與下載間隔
- cookies 來源路徑

#### 6. 多頻道批次下載

可能形式：

- `--channels-file channels.txt`
- 每行一個頻道 URL、ID 或 `@handle`

完成標準：

- 單一頻道失敗不會中斷全部批次。
- 每個頻道有清楚結果摘要。
- 預設仍保持保守速率，不新增平行大量下載。

#### 7. 結果報表

下載結束後產出簡單人可讀報表：

- 已下載影片
- 已跳過影片
- 失敗影片與原因
- archive 路徑

### 長期方向

- 套件發布整理：版本號規則、GitHub Release checklist、PyPI 發布可行性評估。
- 更完整的跨平台驗證：Windows runner、macOS runner、`yt-fetch --help` smoke test、editable install 檢查。

### 暫不做

- 繞過 YouTube 付費牆、會員限定、私人影片、地區限制或其他存取控制。
- 管理、交換、抽取或分享使用者 cookies/token。
- 大量平行下載或規避限流。
- 自動上傳雲端硬碟或第三方儲存服務。

## 貢獻

歡迎貢獻！請查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解如何參與專案。

## 安全

如果您發現安全漏洞，請查看 [SECURITY.md](SECURITY.md) 了解如何回報。

## 授權

本專案採用 [MIT License](LICENSE) 授權。

## 免責聲明

本工具僅供個人學習與研究使用。下載內容請遵守：

- YouTube 服務條款
- 著作權法
- 相關法律法規

使用者需自行承擔使用本工具的所有責任。

## 技術細節

- **依賴套件**：yt-dlp、imageio-ffmpeg
- **Python 版本**：3.7+
- **虛擬環境**：自動建立 `.venv`
- **CLI 指令**：`pip install -e .` 後可使用 `yt-fetch`
- **下載目錄**：`download/`
- **Archive 檔案**：`download/.download_archive.txt`

## 疑難排解

如果遇到問題，請檢查：

1. Python 版本是否為 3.7 或更高
2. 網路連線是否正常
3. 頻道是否為公開且可存取
4. 是否有足夠的磁碟空間
5. 查看日誌輸出的詳細錯誤訊息

## 更新日誌

詳細的更新記錄請查看 [CHANGELOG.md](CHANGELOG.md)。

### 主要功能

- 自動環境管理
- 跨平台支援
- 智能格式選擇（需 ffmpeg）
- 冪等性保證
- Shorts 過濾功能（支援 YouTube 頻道分頁：Videos/Shorts/Live，預設只從 Videos 頁面獲取）
- 僅下載公開影片功能（自動過濾非公開內容）
- 限制播放清單提取數量，避免觸發 YouTube 限流
- 強制使用 watch URL 下載，避免 m3u8 格式問題
- 使用 progress hook 追蹤實際下載檔名，確保檔案正確識別
- 互動式輸入視窗（未提供 --channel 時會詢問）
- Cookies 支援（處理年齡/地區限制）
- 下載速率限制和延遲策略（減少被限流）

