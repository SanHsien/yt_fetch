# 發布流程（Releasing）

本文件說明 `yt_fetch` 的版本規則、GitHub Release 流程，以及 PyPI 發布的可行性評估。

## 版本號規則（SemVer）

採 [語義化版本](https://semver.org/lang/zh-TW/) `MAJOR.MINOR.PATCH`：

- **MAJOR**：不相容的 CLI／行為變更（例如移除或改變既有參數語意）。
- **MINOR**：向下相容的新功能（例如新增 `--gui`、`--channels-file`、設定檔）。
- **PATCH**：向下相容的修正（bug fix、文件、測試）。

版本號維護於 `pyproject.toml` 的 `[project].version`，並對應 `CHANGELOG.md` 的區段。

## 發布前檢查清單

1. 本地檢查全綠：
   ```bash
   python -m pytest -q
   python -m black --check yt_fetch.py yt_fetch_gui.py chrome_cdp_cookies.py build_exe.py tools/ tests/
   python -m isort --check-only yt_fetch.py yt_fetch_gui.py chrome_cdp_cookies.py build_exe.py tools/ tests/
   python -m flake8 yt_fetch.py yt_fetch_gui.py chrome_cdp_cookies.py build_exe.py tools/ tests/
   vermin --eval-annotations --no-tips yt_fetch.py yt_fetch_gui.py chrome_cdp_cookies.py build_exe.py tools/ tests/
   python yt_fetch.py --help        # 應乾淨輸出
   ```
   `vermin` 輸出的 `Minimum required versions` 應不高於 `3.10`。
2. `CHANGELOG.md`：把 `[未發布]` 內容整理成新版本區段並標日期，更新底部比較連結。
3. `pyproject.toml` 的 `version` 與 CHANGELOG 版本一致。
4. 若 GUI 版面有變更，重跑截圖：
   ```bash
   xvfb-run -a -s "-screen 0 860x1020x24" python3 tools/generate_readme_screenshot.py
   ```
5. Release notes 草稿需至少列出：
   - 內建 `yt-dlp` 版本：`python -c "import yt_dlp; print(yt_dlp.version.__version__)"`
   - 主要新增/修正功能。
   - 已知限制：未簽章 EXE 可能觸發 SmartScreen、EXE 內建 `yt-dlp` 會隨 YouTube 改版而過期。
   - Windows zip 的 SHA256（以 workflow 產生的 `.sha256` 為準）。
6. 確認 `main` 上程式碼檢查與 CodeQL 均為綠。
7. 依 [`COMPUTER_USE_VALIDATION.md`](COMPUTER_USE_VALIDATION.md) 完成 Windows ZIP／SHA-256／
   解壓 round-trip 與 GUI 實機驗收；任何需要登入、cookies 或真實下載的步驟都必須由使用者
   在當輪明確授權下主持。

## 切標籤與發佈

EXE 與 Release 由標籤觸發：

```bash
git tag -a vX.Y.Z -m "yt_fetch vX.Y.Z"
git push origin vX.Y.Z
```

推送 `v*` 標籤後，`.github/workflows/release.yml` 會在 `windows-latest`：

1. `pip install -e ".[build]"` 後 `python build_exe.py` 產出 `dist/yt_fetch.exe`。
2. 打包 `yt_fetch-<版本>-windows-x64.zip` 與對應 `.sha256`。
3. 以 `softprops/action-gh-release` 發佈到 GitHub Releases（自動產生 release notes）。

> 注意：部分受限環境（例如代理只允許推送目前工作分支）無法直接 `git push` 標籤；
> 此時請以具完整權限的帳號於 GitHub UI「Draft a new release」建立 `vX.Y.Z`，同樣會觸發上述 workflow。
> 也可用 workflow_dispatch 手動觸發，僅產生可下載的 artifact（不發佈 Release）。

## 發佈後

- 驗證 Release 內含 `*.zip` 與 `*.sha256`，下載並核對雜湊。
- 記錄該版 EXE 內嵌的 `yt-dlp` 版本；若之後每月依賴新鮮度檢查提示 `yt-dlp` 落後，需評估重發版。
- 檢查 GitHub Release 文字是否含主要功能、已知限制與 SHA256；若自動 release notes 不足，手動補上。
- 於 `main` 新增空的 `[未發布]` 區段，準備下一輪。

## 依賴新鮮度檢查

`yt-dlp` 與 YouTube 行為高度耦合；Windows EXE 會固定打包建置當下版本，因此即使程式碼未變，
也可能需要重發 Release。維護分成兩層：

- 每週 Dependabot：`.github/dependabot.yml`
  - `pip`：全部 Python 執行期、開發與建置依賴；以 `increase` 策略推進 `>=` 最低版本。
  - `github-actions`：所有 workflow 使用的 Actions。
- 每月 EXE 關鍵依賴排程：`.github/workflows/dependency-freshness.yml`
  - 比較 `pyproject.toml` 宣告的 `yt-dlp`／`imageio-ffmpeg` 基線與 PyPI 最新版。
  - 落後或查詢失敗時建立／更新同一個 issue；恢復最新時自動關閉提醒。
  - 報告會顯示於該次 GitHub Actions Job Summary。
- 本地檢查：
  ```bash
  python tools/check_dependency_freshness.py
  ```
- Dependabot PR 或月報顯示依賴落後時，先確認 changelog／相容性並跑完整測試；只有需要讓
  Windows 使用者取得新內建版本時，才推進 patch 版本並切 tag 重發 EXE。

## PyPI 發布可行性評估

目前**暫不發佈到 PyPI**，理由與條件如下：

- 專案以「自帶 venv 引導 + GUI/EXE」為主要散布方式，一般使用者不需從 PyPI 安裝。
- `yt-dlp` 與 YouTube 介面變動頻繁，PyPI 上的釘版可能很快過時；目前以原始碼/EXE 隨時可更新較合適。
- 套件名稱 `yt-fetch` 在 PyPI 的可用性尚未確認。

若未來要上 PyPI，建議補齊：

1. 確認套件名稱可用並保留。
2. 以 `python -m build` 產出 `sdist` 與 `wheel`，並用 `twine check dist/*` 驗證 metadata。
3. 以 [PyPI Trusted Publishing（OIDC）](https://docs.pypi.org/trusted-publishers/) 於 GitHub Actions 自動發佈，避免長期 token。
4. 先發到 TestPyPI 驗證安裝與 `yt-fetch` 進入點，再正式發佈。
