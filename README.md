# ChannelDepot

[English](README.en.md)

[![Release](https://img.shields.io/github/v/release/SanHsien/yt_fetch?sort=semver&display_name=tag)](https://github.com/SanHsien/yt_fetch/releases/latest)
[![CI](https://github.com/SanHsien/yt_fetch/actions/workflows/code-check.yml/badge.svg?branch=main)](https://github.com/SanHsien/yt_fetch/actions/workflows/code-check.yml)
[![CodeQL](https://github.com/SanHsien/yt_fetch/actions/workflows/codeql.yml/badge.svg?branch=main)](https://github.com/SanHsien/yt_fetch/actions/workflows/codeql.yml)
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Source-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)](#platform-support)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**ChannelDepot** 是一個輕巧、可攜的 YouTube 頻道影片保存工具。指定頻道與數量後，它會透過 `yt-dlp` 取得最新可存取影片，套用 Shorts／畫質／日期／標題／長度等篩選條件，再下載到本機。

Windows 使用者可直接下載免安裝 GUI；進階使用者也能使用 CLI、批次頻道清單與自己的登入 cookies。

> 專案原名為 `yt_fetch`。為避免破壞既有使用者，`yt_fetch.py`、`yt-fetch`、`yt-fetch-gui` 與目前 Windows Release 檔名暫時保留舊名稱。

> 僅用於你有權下載或備份的內容。登入功能不繞過付費牆、會員資格、私人影片或其他 YouTube 存取控制。

## 畫面

[![ChannelDepot 主畫面](docs/screenshots/main-window.png)](docs/screenshots/main-window.png)

GUI 會在背景下載並顯示進度、日誌與結果；可匯入多個頻道、切換常用畫質設定、套用進階篩選並匯出本次下載紀錄。

## 下載 Windows 免安裝版

1. 到 [Latest Release](https://github.com/SanHsien/yt_fetch/releases/latest)。
2. 下載 `yt_fetch-vX.Y.Z-windows-x64.zip`。
3. 解壓後執行 `yt_fetch.exe`。
4. 預設下載位置為程式旁的 `download/`；Release 同時提供 `.sha256` 校驗檔。

目前 Windows EXE 未做程式碼簽章，因此首次執行可能出現 SmartScreen 提示。請只從本專案 Releases 取得執行檔並核對來源。

> Windows EXE 會封裝發行當下的 `yt-dlp`。YouTube 改版後若舊版突然無法下載，先檢查是否已有新版 Release。

## 為什麼用 ChannelDepot

- **GUI 與 CLI 共用同一套下載核心**：新手直接點選，進階使用者可自動化。
- **頻道導向**：適合「備份某頻道最新 N 支影片」，而不是做成大而全的萬用下載器。
- **批次工作流**：GUI 可匯入頻道清單，單一頻道失敗不會中斷整批。
- **實用篩選**：Shorts、畫質上限、標題、日期、影片長度、字幕語言。
- **避免重複下載**：下載 archive 加上檔名中的 YouTube video id 維持冪等性。
- **ffmpeg 自動補強**：優先使用系統 ffmpeg，沒有時可由 `imageio-ffmpeg` 提供。
- **登入仍遵守存取權限**：可使用自己的 cookies 處理自己本來就有權觀看的內容。
- **可診斷**：針對 cookies、資格、限流、ffmpeg、磁碟權限等常見問題提供下一步。

## 快速開始

### GUI

從原始碼執行：

```bash
python yt_fetch.py --gui
```

若已用 editable install 安裝：

```bash
yt-fetch-gui
```

### CLI

下載某頻道最新 5 支一般影片：

```bash
python yt_fetch.py --channel "@channel_handle"
```

指定數量與畫質：

```bash
python yt_fetch.py --channel "@channel_handle" --count 10 --quality 720p
```

包含 Shorts：

```bash
python yt_fetch.py --channel "@channel_handle" --include-shorts
```

限制下載速度並增加間隔：

```bash
python yt_fetch.py --channel "@channel_handle" --ratelimit 5 --sleep 2
```

完整參數請執行：

```bash
python yt_fetch.py --help
```

## 使用自己的登入狀態

公開影片通常不需要登入。若內容需要 YouTube 驗證登入，而你的帳號**本來就具有觀看資格**，可使用：

```bash
python yt_fetch.py --channel "@channel_handle" --cookies cookies.txt
python yt_fetch.py --channel "@channel_handle" --cookies-from-browser chrome:Default
```

Windows GUI 另提供受控 Chrome 登入流程，可在本機取得目前使用者自己的 YouTube cookies。這項功能用來處理已授權內容，例如自己的會員資格或年齡驗證；它不會替你取得未購買的會員內容，也不會開啟私人／未授權影片。

安全邊界：

- cookies、token 與帳號憑證不得提交到 repository。
- 受控登入只應匯出自己的 cookies，並只在本機使用。
- 工具不提供 DRM 移除、付費牆繞過或未授權內容存取功能。
- 使用者仍應自行確認 YouTube 服務條款、著作權與內容授權條件。

更多安全說明見 [SECURITY.md](SECURITY.md)。

## 安裝原始碼版本

需要 Python 3.10+：

```bash
git clone https://github.com/SanHsien/yt_fetch.git
cd yt_fetch
python -m venv .venv
```

啟用虛擬環境後：

```bash
pip install -e .
```

之後可使用：

```bash
yt-fetch --channel "@channel_handle"
yt-fetch-gui
```

`yt_fetch.py` 也保留自動建立 `.venv`／安裝必要套件的便利流程，適合直接執行腳本的使用者。

## 平台支援

| 使用方式 | Windows | macOS | Linux |
|---|---:|---:|---:|
| Windows 免安裝 EXE | 是 | 否 | 否 |
| Python CLI | 是 | 是 | 是 |
| Tkinter GUI | 是 | 是 | 是* |
| 受控 Chrome 登入 | 主要支援 | 依瀏覽器方式而定 | 依瀏覽器方式而定 |

\* 部分精簡 Linux 發行版需額外安裝 `python3-tk`。

## 開發與驗證

```bash
python -m pip install -e ".[dev]"
python -m pytest -q
python -m black --check yt_fetch.py yt_fetch_gui.py chrome_cdp_cookies.py build_exe.py tools/ tests/
python -m isort --check-only yt_fetch.py yt_fetch_gui.py chrome_cdp_cookies.py build_exe.py tools/ tests/
python -m flake8 yt_fetch.py yt_fetch_gui.py chrome_cdp_cookies.py build_exe.py tools/ tests/
```

正式版由 GitHub Actions 建置 Windows ZIP，並驗證 ZIP、SHA-256 與必要檔案。發行流程見 [docs/RELEASING.md](docs/RELEASING.md)。

## 文件

- [CONTRIBUTING.md](CONTRIBUTING.md)：貢獻方式
- [SECURITY.md](SECURITY.md)：安全與 cookies 回報邊界
- [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md)：開發與測試
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)：程式結構與資料流
- [docs/COMPUTER_USE_VALIDATION.md](docs/COMPUTER_USE_VALIDATION.md)：Windows GUI／Release 實機驗證
- [docs/RELEASING.md](docs/RELEASING.md)：發行流程
- [CHANGELOG.md](CHANGELOG.md)：版本歷史

## 授權

本專案採 [MIT License](LICENSE)。第三方元件與補充聲明見 [NOTICE.md](NOTICE.md)。
