---
name: yt-fetch
description: 從指定 YouTube 頻道抓取最新公開影片，透過 yt-dlp 下載到本機 download/。支援 @handle、頻道 ID、URL、Shorts 過濾、cookies 參數、速率限制與重試。
---

# yt-fetch

## 何時使用

使用者要下載自己有權存取的 YouTube 頻道公開影片，或要維護 `SanHsien/yt_fetch` 專案。

適合的任務：

- 下載指定頻道最新 N 支公開影片。
- 排除或包含 Shorts。
- 調整重試、速率限制、下載間隔。
- 修復 CLI、URL 正規化、公開影片判斷、冪等下載、測試與文件。

不適合的任務：

- 下載私人、會員限定、付費、無權存取或受限制內容。
- 繞過 YouTube 存取控制、限制或 DRM。
- 取得、破解、分享 cookies、token 或帳號憑證。

## 前置

```bash
python -m venv .venv
.venv\Scripts\python -m pip install -e ".[dev]"
```

如果只要執行工具，也可直接：

```bash
python yt_fetch.py --channel "@channel_handle"
```

腳本會嘗試建立 `.venv` 並安裝必要套件。

## 常用操作

```bash
# 下載最新 5 支公開影片
python yt_fetch.py --channel "@channel_handle"

# 指定數量
python yt_fetch.py --channel "@channel_handle" --count 10

# 包含 Shorts
python yt_fetch.py --channel "@channel_handle" --include-shorts

# 使用 cookies 檔案或瀏覽器 cookies
python yt_fetch.py --channel "@channel_handle" --cookies cookies.txt
python yt_fetch.py --channel "@channel_handle" --cookies-from-browser chrome

# 限速與延遲
python yt_fetch.py --channel "@channel_handle" --ratelimit 5 --sleep 2
```

## 開發驗證

```bash
.venv\Scripts\python -m pytest -q
.venv\Scripts\python -m black --check yt_fetch.py tests/
.venv\Scripts\python -m isort --check-only yt_fetch.py tests/
.venv\Scripts\python -m flake8 yt_fetch.py tests/
```

## 回報

完成維護後，告知使用者：

- 修改了哪些文件或程式。
- 是否已建置 `.venv`。
- 測試與格式檢查結果。
- 是否已推送到 `main`。

若驗證失敗，直接列出失敗指令與原因。
