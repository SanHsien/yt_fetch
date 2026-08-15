---
name: yt-fetch
description: 維護 SanHsien/yt_fetch：以 yt-dlp 為核心的輕量 YouTube 頻道下載工具，提供 CLI、Tkinter GUI、批次頻道、篩選與使用者自己的授權登入 cookies。
---

# yt_fetch quick index

## 何時使用

使用者要維護 `SanHsien/yt_fetch`，或調整：

- 頻道 URL / `@handle` 正規化
- 最新 N 支影片、Shorts、畫質、日期、標題、長度、字幕篩選
- CLI / GUI 共用下載流程
- 批次頻道下載與下載紀錄
- 使用者自己的 cookies / 受控 Chrome 登入
- Windows EXE、測試或文件

## 先讀

1. [`AGENTS.md`](AGENTS.md)：主要規則與安全邊界
2. [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)：資料流與模組關係
3. 涉及 cookies 時讀 [`SECURITY.md`](SECURITY.md)
4. 涉及 GUI / Release 時讀 [`docs/COMPUTER_USE_VALIDATION.md`](docs/COMPUTER_USE_VALIDATION.md)

## 核心檔案

- `yt_fetch.py`：CLI、設定、候選影片與下載核心
- `yt_fetch_gui.py`：Tkinter GUI 與批次工作流
- `chrome_cdp_cookies.py`：Windows 受控 Chrome 登入
- `build_exe.py`：Windows PyInstaller build
- `tests/`：自動測試

## 不可做

- 繞過付費牆、會員資格、私人影片、DRM 或其他存取控制
- 使用、提交或分享不是使用者自己的 cookies / token / 帳密
- 把 GUI 與 CLI 拆成兩套不同的下載規則

## 驗證

```bash
python -m pip install -e ".[dev]"
python -m pytest -q
python -m black --check yt_fetch.py yt_fetch_gui.py chrome_cdp_cookies.py build_exe.py tools/ tests/
python -m isort --check-only yt_fetch.py yt_fetch_gui.py chrome_cdp_cookies.py build_exe.py tools/ tests/
python -m flake8 yt_fetch.py yt_fetch_gui.py chrome_cdp_cookies.py build_exe.py tools/ tests/
```

實機登入、GUI、Release ZIP 的驗證範圍依 `AGENTS.md` 與 `docs/COMPUTER_USE_VALIDATION.md` 執行。
