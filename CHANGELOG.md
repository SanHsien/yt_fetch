# 更新日誌

所有重要的變更都會記錄在這個檔案中。

格式基於 [Keep a Changelog](https://keepachangelog.com/zh-TW/1.0.0/)，
本專案遵循 [語義化版本](https://semver.org/lang/zh-TW/)。

## [未發布]

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

[未發布]: https://github.com/SanHsien/yt_fetch/compare/v1.1.0...HEAD
[1.1.0]: https://github.com/SanHsien/yt_fetch/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/SanHsien/yt_fetch/releases/tag/v1.0.0

