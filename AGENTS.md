# AGENTS.md

本檔是 **ChannelDepot**（目前 repository slug：`SanHsien/yt_fetch`）的 AI coding agent 主要維護規則。Claude Code 的工具專屬補充見 [`CLAUDE.md`](CLAUDE.md)；衝突時以本檔為準。

## 專案定位

**ChannelDepot** 是輕巧的 YouTube 頻道影片保存工具：核心 CLI 在 `yt_fetch.py`，Tkinter GUI 在 `yt_fetch_gui.py`，Windows 受控 Chrome 登入在 `chrome_cdp_cookies.py`。工具透過 `yt-dlp` 取得指定頻道最新可存取影片，套用篩選後下載到本機。

專案原名為 `yt_fetch`。在沒有明確 major-version 遷移計畫前，既有模組、CLI 與 Release 檔名屬相容性介面，不因品牌改名而任意更名。

維持「**單檔核心 + 薄層 GUI**」架構；沒有明確需求時，不主動拆成大型框架。

## 不可破壞的邊界

- 不實作存取使用者**無權觀看**內容的功能，包括未購買的會員內容、私人影片、付費牆或其他存取控制繞過。
- 使用自己的登入狀態處理自己本來就有權觀看的內容屬已授權存取；cookies 只可在本機處理，不提交、不外傳。
- 不加入 DRM 移除、帳號憑證竊取、cookies 分享或高壓大量爬取機制。
- 不提交 `download/`、cookies、token、log、虛擬環境或本機暫存資料。
- 變更存取、cookies、URL 驗證或下載限制時採保守策略並補測試。

## 架構與資料流

1. `parse_args()` / GUI 取得使用者設定。
2. `normalize_channel_url()` 正規化頻道 URL、ID 或 `@handle`。
3. `download_videos()` 透過 `yt-dlp` 取得候選影片。
4. 套用 Shorts、畫質、日期、標題、長度與授權存取條件。
5. `get_downloaded_ids()` 與 download archive 避免重複下載。
6. GUI 只負責互動、批次工作流、進度與結果呈現，下載規則應留在核心。

## 開發規則

- Python 3.10+；新語法必須維持宣告的最低版本相容性。
- 修 bug 優先補測試，不做無關的大型重構。
- CLI / GUI 若共享同一行為，避免複製兩套商業邏輯。
- `yt-dlp` 與 YouTube 行為會快速變動；更新下載核心時確認 release note、測試與 Windows build。
- 依賴、Release 與 security workflow 已存在；沒有具體問題時不要再增加新的治理 workflow。
- 使用者文件以繁體中文為主；英文 README 同步維護。
- **合併任何 PR 前先讀 diff**（包含 Dependabot 開的）：`gh pr diff <編號>`。CI 綠燈證明的是「測試沒紅」，不是「改了什麼、該不該進 main」——lockfile 的連鎖升級、transitive major、跨出宣告範圍的變更，只有讀 diff 看得到。核准或合併訊息要寫出讀到什麼、為什麼可接受。`dependabot-merge.yml` 依政策自動核准的低風險類別是唯一例外——那條路徑的把關是分類器與必要 checks；只要是人或 agent 手動按下 merge，就適用本條。

## REVIEW / CHANGELOG

`REPO_REVIEW.md` 是風險快照，不是每個 bug 的流水帳。

只有以下情況才更新它：

1. 修正的是 `REPO_REVIEW.md` 已列出的問題；或
2. 新發現的缺陷會改變目前 review 的風險判斷。

一般 bug 以測試、PR 與必要時 `CHANGELOG.md` 記錄即可。

## 驗證

```bash
python -m pip install -e ".[dev]"
python -m pytest -q
python -m black --check yt_fetch.py yt_fetch_gui.py chrome_cdp_cookies.py build_exe.py tools/ tests/
python -m isort --check-only yt_fetch.py yt_fetch_gui.py chrome_cdp_cookies.py build_exe.py tools/ tests/
python -m flake8 yt_fetch.py yt_fetch_gui.py chrome_cdp_cookies.py build_exe.py tools/ tests/
```

涉及 GUI、受控登入、Release ZIP 或 Windows 特定行為時，再依 [`docs/COMPUTER_USE_VALIDATION.md`](docs/COMPUTER_USE_VALIDATION.md) 做對應實機驗證；不要以純單元測試宣稱已驗證真實登入或下載。

## 文件分工

- `README.md` / `README.en.md`：產品入口與高頻使用方式
- `CONTRIBUTING.md`：貢獻流程
- `SECURITY.md`：安全與 cookies 邊界
- `docs/DEVELOPMENT.md`：開發與自動測試
- `docs/ARCHITECTURE.md`：架構與資料流
- `docs/COMPUTER_USE_VALIDATION.md`：Windows／GUI／Release 實機驗證
- `docs/RELEASING.md`：發行流程
- `CHANGELOG.md`：版本歷史
- `REPO_REVIEW.md`：最新風險快照
