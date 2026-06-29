# 發展路線圖

本路線圖用來協助維護者判斷 `yt_fetch` 接下來要做什麼、先做什麼，以及哪些事情暫時不做。

## 產品定位

`yt_fetch` 是一個小型、可直接執行的 YouTube 頻道影片下載 CLI 工具。核心目標是：指定頻道、選擇數量、下載公開可存取影片，並避免重複下載。

維護方向：

- 保持安裝與使用簡單。
- 優先穩定支援公開影片下載、Shorts 篩選、冪等下載。
- 遇到 YouTube 或 `yt-dlp` 行為變動時，快速修復使用者實際會遇到的問題。
- 不擴張到繞過存取限制、帳號憑證管理或大量爬取。

## 近期目標

### 1. 測試補強

優先補純邏輯測試，不依賴真實 YouTube 網路回應。

- `normalize_channel_url()` 支援格式測試：
  - `@handle`
  - `handle`
  - `UC...` 頻道 ID
  - `/videos`、`/shorts`、playlist URL
- 已下載 ID 解析測試：
  - `download/.download_archive.txt`
  - 既有檔名中的 `[video_id]`
- Shorts 與直播過濾測試。
- cookies、ratelimit、sleep 參數解析測試。

完成標準：

- 主要 helper 函式有測試。
- CI 不需要連線 YouTube。
- 修 CLI 行為時能靠測試快速發現回歸。

### 2. 下載流程可測化

目前主要流程集中在 `download_videos()`。短期不急著大拆，但可先抽出低風險 helper。

可抽出的區塊：

- 頻道 URL 清單組裝。
- `yt-dlp` options 組裝。
- entries 去重與篩選。
- 下載成功判斷。

完成標準：

- `download_videos()` 保留協調流程。
- helper 可用單元測試覆蓋。
- 不改變現有 CLI 介面與預設行為。

### 3. 使用者體驗修正

優先處理會讓新手卡住的問題。

- `--help` 不應輸出啟動 banner 或多餘 log。
- ffmpeg 未安裝時的錯誤訊息保持明確。
- cookies 相關說明補上安全提醒。
- 下載失敗時整理更清楚的下一步建議。

完成標準：

- `yt-fetch --help` 輸出乾淨。
- 常見錯誤能從訊息直接知道如何處理。

## 中期目標

### 4. 設定檔支援

在不破壞 CLI 的前提下，評估加入簡單設定檔。

可能格式：

- `yt_fetch.toml`
- `yt_fetch.json`

可設定項：

- 預設頻道。
- 預設下載數量。
- 是否包含 Shorts。
- 速率限制與下載間隔。
- cookies 來源。

完成標準：

- CLI 參數仍優先於設定檔。
- 未建立設定檔時行為完全不變。
- 設定檔不包含敏感資訊，cookies 檔案只保存路徑。

### 5. 多頻道批次下載

加入多頻道支援前，先確認單頻道流程穩定。

可能形式：

- `--channels-file channels.txt`
- 每行一個頻道 URL、ID 或 `@handle`

完成標準：

- 單一頻道失敗不會中斷全部批次。
- 每個頻道有清楚結果摘要。
- 預設仍保持保守速率，不新增平行大量下載。

### 6. 結果報表

下載結束後產出簡單人可讀報表。

內容可包含：

- 已下載影片。
- 已跳過影片。
- 失敗影片與原因。
- archive 路徑。

完成標準：

- 報表不含 cookies 或敏感資訊。
- 報表檔案預設放在 `download/`。

## 長期方向

### 7. 套件發布整理

如果使用者需求增加，可整理正式發版流程。

- 明確版本號規則。
- GitHub Release checklist。
- PyPI 發布可行性評估。
- Windows/macOS/Linux 安裝文件更新。

### 8. 更完整的跨平台驗證

目前 CI 已覆蓋多個 Python 版本。後續可補：

- Windows runner。
- macOS runner。
- `yt-fetch --help` smoke test。
- editable install 檢查。

## 暫不做

以下項目不納入路線圖：

- 繞過 YouTube 付費牆、會員限定、私人影片、地區限制或其他存取控制。
- 管理、交換、抽取或分享使用者 cookies/token。
- 大量平行下載或規避限流。
- GUI 桌面版。
- 自動上傳雲端硬碟或第三方儲存服務。

## 維護優先順序

1. 安全與合法使用邊界。
2. 現有 CLI 不破壞。
3. 測試與 CI 維持綠燈。
4. 使用者常見失敗情境。
5. 新功能。
