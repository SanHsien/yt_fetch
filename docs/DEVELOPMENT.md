# 開發與驗證

本文件給接手維護者使用。

## 建置環境

Windows PowerShell：

```bash
python -m venv .venv
.venv\Scripts\python -m pip install --upgrade pip
.venv\Scripts\python -m pip install -e ".[dev]"
```

確認 CLI entry point：

```bash
.venv\Scripts\yt-fetch.exe --help
```

不安裝 editable package 時，也可以直接：

```bash
python yt_fetch.py --help
```

## 本地驗證

提交前至少跑：

```bash
.venv\Scripts\python -m pytest -q
.venv\Scripts\python -m black --check yt_fetch.py yt_fetch_gui.py chrome_cdp_cookies.py build_exe.py tools/ tests/
.venv\Scripts\python -m isort --check-only yt_fetch.py yt_fetch_gui.py chrome_cdp_cookies.py build_exe.py tools/ tests/
.venv\Scripts\python -m flake8 yt_fetch.py yt_fetch_gui.py chrome_cdp_cookies.py build_exe.py tools/ tests/
```

若已安裝 pre-commit：

```bash
.venv\Scripts\pre-commit.exe run --all-files
```

## 手動 smoke test

不要在 CI 或自動化測試裡下載真實影片。需要人工確認時，使用少量公開頻道並加上保守參數：

```bash
python yt_fetch.py --channel "@channel_handle" --count 1 --sleep 2 --ratelimit 3
```

確認項目：

- `download/` 建立成功。
- 影片檔名包含 `[video_id]`。
- 重跑同一指令不會重複下載。
- `download/.download_archive.txt` 有紀錄。

測完若不需要保留，刪除本機下載檔，不要提交。

## CI 對齊

GitHub Actions 會檢查：

- Python 3.10、3.11、3.12。
- `python -m py_compile yt_fetch.py yt_fetch_gui.py chrome_cdp_cookies.py build_exe.py tools/generate_readme_screenshot.py tools/check_dependency_freshness.py`。
- `pytest`。
- vermin 最低版本相容性檢查（`Minimum required versions` 不得高於 3.10）。
- `black --check yt_fetch.py yt_fetch_gui.py chrome_cdp_cookies.py build_exe.py tools/ tests/`。
- `isort --check-only yt_fetch.py yt_fetch_gui.py chrome_cdp_cookies.py build_exe.py tools/ tests/`。
- `flake8 yt_fetch.py yt_fetch_gui.py chrome_cdp_cookies.py build_exe.py tools/ tests/`。

本機若使用 Python 3.14，可能比 CI 更嚴格。遇到 packaging 或工具相容問題時，以 CI 支援版本與專案 `pyproject.toml` 為準。

## 維護習慣

- 先 `git fetch origin main` 確認本機 main 沒落後。
- 修改 CLI 行為時同步更新 `README.md` 與測試。
- 修改安全或使用條款相關描述時同步檢查 `NOTICE.md`、`SECURITY.md`、`AGENTS.md`。
- 不提交 `.venv/`、`download/`、cookies、log、暫存檔。
