# YouTube 頻道影片下載工具

從指定 YouTube 頻道取得最新的 N 支影片並下載為 mp4，儲存到 `download/` 資料夾。

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

## 授權與免責聲明

本工具僅供個人學習與研究使用。下載內容請遵守：

- YouTube 服務條款
- 著作權法
- 相關法律法規

使用者需自行承擔使用本工具的所有責任。

## 技術細節

- **依賴套件**：yt-dlp
- **Python 版本**：3.7+
- **虛擬環境**：自動建立 `.venv`
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

