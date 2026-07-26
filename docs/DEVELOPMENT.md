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

Windows GUI、Release ZIP 與 Computer Use 的實機驗收規範見
[`COMPUTER_USE_VALIDATION.md`](COMPUTER_USE_VALIDATION.md)。它和下列本地 smoke test
互補：自動化檢查通過不等於桌面 UI 或使用者下載到的 EXE 已實際驗收。

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
- `python -m py_compile yt_fetch.py yt_fetch_gui.py chrome_cdp_cookies.py build_exe.py tools/generate_readme_screenshot.py tools/check_dependency_freshness.py tools/classify_dependabot_update.py tools/verify_release_zip.py`。
- `pytest`。
- vermin 最低版本相容性檢查（`Minimum required versions` 不得高於 3.10）。
- `black --check yt_fetch.py yt_fetch_gui.py chrome_cdp_cookies.py build_exe.py tools/ tests/`。
- `isort --check-only yt_fetch.py yt_fetch_gui.py chrome_cdp_cookies.py build_exe.py tools/ tests/`。
- `flake8 yt_fetch.py yt_fetch_gui.py chrome_cdp_cookies.py build_exe.py tools/ tests/`。
- Ubuntu／Python 3.12 另跑 `pre-commit run --all-files` 與乾淨 wheel build，直接驗證
  hook runner、`setuptools` 與 `wheel` 更新。
- 獨立的 Python CodeQL `security-extended` workflow 會在 push、PR 與每週排程建立 SAST 基線。
- Dependabot 每週檢查 Python 直接依賴與 GitHub Actions；依賴新鮮度 workflow 每月檢查
  `yt-dlp`／`imageio-ffmpeg` 的 repo 宣告基線，並在需注意時維護提醒 issue。
- Dependabot PR 會由 `dependabot-review.yml` 判斷變更是否被必要 CI 直接覆蓋；核可後由
  `dependabot-merge.yml` 等五平台 CI、Pre-commit、wheel build 與 CodeQL 全數成功，再自動
  Approve，並透過全域序列在必要時 rebase，再 squash merge、關閉 PR 並刪除分支。自動
  合併會 explicit dispatch freshness；人工合併或直接更新 manifest 由 `main` push 重驗。
  固定 reopen／更新並指派同一個維護 issue；追蹤依賴最新且無 open Dependabot PR 才關閉。

本機若使用 Python 3.14，可能比 CI 更嚴格。遇到 packaging 或工具相容問題時，以 CI 支援版本與專案 `pyproject.toml` 為準。

## 維護習慣

- 先 `git fetch origin main` 確認本機 main 沒落後。
- 修改 CLI 行為時同步更新 `README.md` 與測試。
- 修改安全或使用條款相關描述時同步檢查 `NOTICE.md`、`SECURITY.md`、`AGENTS.md`。
- 不提交 `.venv/`、`download/`、cookies、log、暫存檔。
