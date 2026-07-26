# 第三方 YouTube 工具與風險邊界

本專案依賴第三方工具處理 YouTube 影片資訊與下載流程。維護時請把工具限制、服務條款與使用者安全放在前面。

## 使用中的工具

| 工具 | 用途 | 注意事項 |
| --- | --- | --- |
| `yt-dlp` | 擷取頻道影片資訊、下載影片、維護 download archive | YouTube 行為變動時需更新版本；EXE 會固定打包建置當下版本；不應用來規避無權存取內容 |
| `ffmpeg` | 合併最佳影片與音訊格式 | 系統可自行安裝，也可透過 `imageio-ffmpeg` 取得 |
| `imageio-ffmpeg` | 提供可用 ffmpeg 執行檔 | 只作為執行環境補強，不改變授權或使用責任 |

## 依賴新鮮度

- `yt-dlp` 是最容易因 YouTube 改版而過期的依賴；若 EXE 下載開始失敗，先檢查內嵌 yt-dlp 是否落後 PyPI。
- GUI「檢查更新」會同時檢查 GitHub Release 與 PyPI 最新 `yt-dlp`。
- 每月排程 `.github/workflows/dependency-freshness.yml` 會檢查 `yt-dlp` 與 `imageio-ffmpeg`，落後時建立或更新維護 issue。
- 本地可執行 `python tools/check_dependency_freshness.py` 產生 Markdown 報告。

## cookies 使用邊界

`yt-dlp` 支援 cookies 參數，本專案也暴露：

- `--cookies-from-browser`
- `--cookies`
- `--login`（受控登入：在本機開工具專屬瀏覽器讓使用者登入，於本機取得其自己的 cookies）

維護這些功能時必須保留以下前提：

- cookies 只供使用者存取自己有權存取的內容（含使用者自己付費／訂閱的會員影片，屬已授權存取、非繞過）。
- 不在日誌或輸出中列印 cookies 內容；取得的 cookies 只存於本機、不提交至版本控制、不外傳。
- 受控 Chrome 的 CDP 只監聽 `127.0.0.1`；匯出只保留 `youtube.com`、`google.com` 與
  `googlevideo.com` 網域，不寫入其他網站 cookies。
- 不提供偷取、破解或外傳他人 cookies 的流程。
- 不以 cookies 功能鼓勵下載使用者「無權存取」的內容。

## 速率與服務壓力

本專案提供：

- `--ratelimit`
- `--sleep`
- `--retries`

文件與預設值應鼓勵保守使用。不要新增大量平行下載、無限制重試或繞過限流的設計。

## 測試策略

自動化測試不應依賴 YouTube 真實網路回應。優先測：

- URL 正規化。
- CLI 參數解析。
- 已下載 ID 解析。
- yt-dlp options 組裝。
- 公開影片與 Shorts 判斷。

真實下載只作人工 smoke test，且應使用少量公開影片。
