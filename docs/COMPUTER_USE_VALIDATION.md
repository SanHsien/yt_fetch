# Windows 與 Computer Use 實機驗證

本文件是 `yt_fetch` Windows GUI 與可攜 EXE 的正式實機驗收流程。目的不是只確認
pytest、PyInstaller 或 CI 綠燈，而是證明使用者實際下載的 Windows 資產能解壓、啟動、
看懂介面，並在**使用者已授權**的前提下完成少量下載。

## 判定與安全界線

- `PASS`：本次實際操作且結果符合預期，保留必要的非敏感證據。
- `FAIL`：本次實際操作但不符合預期；不能宣稱該 Release 可用。
- `BLOCKED`：缺少使用者授權、自己的可存取測試頻道、登入狀態、網路或顯示器；不能以單元測試替代。
- 自動測試、CI、程式碼閱讀與桌面驗收是不同證據，必須分開記錄。
- 不記錄、不截圖、不提交 cookies、帳號、頻道私人網址、下載檔案、完整本機路徑或 API key。
- 僅可用使用者自己有權觀看的公開內容或已授權內容；不得測試私密、未付費會員、年齡／地區繞過或大量下載。

## Computer Use 操作規則

Computer Use 是受監督的桌面驗收，不是可重播的固定座標巨集。

1. 每批開始前重新列出視窗，僅選取一個標題符合 `yt_fetch` 的目標視窗；啟用後重新擷取畫面。
2. 每次只做一個狀態轉移（點擊、輸入、切換或關閉），立即重新擷取畫面確認結果；不得重用舊畫面座標、screenshot id 或 accessibility index。
3. 代理可驗證介面呈現、非網路表單防呆、語言切換、說明／關於、結果清單與檔案總管開啟行為。
4. 登入 YouTube、輸入帳密、多因素驗證、cookies 選取／匯出，以及實際開始下載，均由使用者親自完成或在當輪明確授權後才進行。代理不得代填或讀取憑證。
5. 不確定目前焦點、對話框或下載是否已送出時，停止並重新觀察；不可盲目重試，以免重複下載或對服務造成壓力。
6. 關閉程式後確認只有本次啟動的 `yt_fetch` 程序結束；不可關閉使用者其他瀏覽器或應用程式。

## 一、自動化基線

先確認驗收對應目前遠端主線，並完成本機品質 gate：

```powershell
git fetch origin main --prune
git status --short --branch
git rev-parse HEAD
git rev-parse origin/main
.venv\Scripts\python -m pytest -q
.venv\Scripts\python -m black --check yt_fetch.py yt_fetch_gui.py chrome_cdp_cookies.py build_exe.py tools/ tests/
.venv\Scripts\python -m isort --check-only yt_fetch.py yt_fetch_gui.py chrome_cdp_cookies.py build_exe.py tools/ tests/
.venv\Scripts\python -m flake8 yt_fetch.py yt_fetch_gui.py chrome_cdp_cookies.py build_exe.py tools/ tests/
.venv\Scripts\python -m py_compile yt_fetch.py yt_fetch_gui.py chrome_cdp_cookies.py build_exe.py tools\generate_readme_screenshot.py tools\check_dependency_freshness.py tools\verify_release_zip.py
.venv\Scripts\vermin --eval-annotations --no-tips yt_fetch.py yt_fetch_gui.py chrome_cdp_cookies.py build_exe.py tools/ tests/
.venv\Scripts\python yt_fetch.py --help
```

記錄 commit、Python 版本、測試數與每個 gate 的結果。只有 `HEAD == origin/main` 且工作樹狀態已確認後，結果才能歸屬於遠端 `main`。

## 二、Release ZIP、雜湊與解壓 round-trip

Release 驗收只能針對 GitHub 下載的資產，不得用 repo 的 `dist/` 代替。以 `vX.Y.Z` 為例：

```powershell
$ValidationNonce = [Guid]::NewGuid().ToString("N")
$VerifyRoot = Join-Path $env:TEMP "yt-fetch-release-verify-vX.Y.Z-$ValidationNonce"
New-Item -ItemType Directory -Path $VerifyRoot | Out-Null

gh release download vX.Y.Z -R SanHsien/yt_fetch `
  -p "yt_fetch-vX.Y.Z-windows-x64.zip" `
  -p "yt_fetch-vX.Y.Z-windows-x64.zip.sha256" `
  -D $VerifyRoot

$Zip = Join-Path $VerifyRoot "yt_fetch-vX.Y.Z-windows-x64.zip"
$Expected = ((Get-Content "$Zip.sha256" -Raw) -split "\s+")[0].ToLowerInvariant()
$Actual = (Get-FileHash -Algorithm SHA256 -LiteralPath $Zip).Hash.ToLowerInvariant()
if ($Actual -ne $Expected) { throw "SHA-256 mismatch" }

.venv\Scripts\python tools\verify_release_zip.py $Zip

$Extract = Join-Path $VerifyRoot "expanded"
Expand-Archive -LiteralPath $Zip -DestinationPath $Extract
Get-ChildItem -LiteralPath $Extract -Recurse -File | Select-Object Name, Length
```

獨立驗證工具會檢查 CRC、危險或重複路徑、唯一且位於根目錄的非空
`yt_fetch.exe`。ZIP 無法讀取、SHA-256 不符、工具驗證失敗或 Windows 內建
`Expand-Archive` 失敗時，Release 為 `FAIL`。每次使用唯一暫存目錄，避免舊檔案讓結果
誤判為成功。驗收結束後，確認暫存資料夾僅含可安全刪除的公開測試產物；刪除由維護者
當輪確認後處理。

## 三、無帳號桌面 smoke（代理可執行）

用解壓後的 `yt_fetch.exe` 啟動 GUI；不可改用 source mode。下列項目不連線下載、不涉及登入：

| 項目 | 操作與預期 |
| --- | --- |
| 啟動 | 視窗出現、標題與圖示正確，沒有 traceback 或空白畫面。 |
| 預設畫面 | 下載設定、批次清單、進度、結果與日誌區可見；文字沒有截斷或重疊。 |
| 語言 | 切換中／英文後主要按鈕、表單驗證與說明一致；切回原語言後無殘留錯字。 |
| 快速設定 | 選擇 `720p`／`480p` profile 後，只更新預期的畫質、速率或間隔欄位。 |
| 表單防呆 | 對空頻道、`count=0`、非數字數量、負速率、錯誤日期與最小長度大於最大長度，各顯示可理解錯誤且不啟動下載。 |
| 說明與更新 | About／使用說明可開啟；更新檢查失敗時有可理解提示且 GUI 不閃退。 |
| 結束 | 關閉 GUI 後，確認本次 `yt_fetch.exe` 程序結束且未留下卡住的對話框。 |

任何檔案選擇視窗都只能瀏覽測試資料夾；不要選取 cookies、個人文件或真實下載目錄作為驗收證據。

## 四、使用者主持的少量下載 round-trip

這一節需要使用者當輪同意，並自行輸入一個公開或自己已授權觀看的測試頻道。建議設定：

```text
count = 1
include shorts = false
ratelimit = 3 MB/s
sleep = 2 seconds
```

驗收順序：

1. 使用者確認頻道與內容授權；若需要登入，使用者親自完成受控瀏覽器登入。
2. 只啟動一次下載，確認進度、日誌與結果列出一個 video id、標題及檔案路徑。
3. 確認輸出位於 `download/<頻道名稱>/`，檔名含 `[video_id]`，且 archive 有對應紀錄。
4. 使用相同設定再跑一次，確認不重新下載同一支影片（冪等性）。
5. 若測到已授權會員內容，另記錄「帳號原本已有權觀看」；未授權、私密或受限內容只應被拒絕／跳過，不能當作成功條件。

代理可在使用者明確授權後觀察上述非敏感結果；不應查看 cookies 內容、帳號頁面或下載影片內容。

## 五、額外情境與 Gate

| 情境 | 何時執行 | 合格條件 |
| --- | --- | --- |
| 批次頻道檔 | 修改批次流程時 | 公開測試清單逐一循序處理；單一失敗不阻斷其他列。 |
| 字幕 | 修改字幕選項時 | 有提供字幕的公開測試影片產生預期語言檔；無字幕時正常完成。 |
| ffmpeg | 修改格式或 ffmpeg 偵測時 | 狀態頁正確顯示目前來源；不為測試而改動系統 PATH。 |
| cookies／受控登入 | 修改 `chrome_cdp_cookies.py` 時 | 使用者親自完成登入；公開影片、已授權內容與無權內容分別記錄。 |
| 新版 Release | 每個 `v*` tag | 本文件第一至四節均為 PASS，或清楚列出 BLOCKED 與原因。 |

任何含外部服務、登入、實際檔案下載、刪除下載產物或發佈 Release 的動作，都必須有本輪明確授權；不可從過往驗收推定授權。

## 驗收紀錄模板

```markdown
## vX.Y.Z / commit <sha> / YYYY-MM-DD

| 項目 | 結果 | 非敏感證據或阻塞原因 |
| --- | --- | --- |
| pytest / style / compile / help | PASS/FAIL | <版本與摘要> |
| Release SHA-256 / ZIP CRC 與版面 / Expand-Archive | PASS/FAIL | <檔名與 sha 前 12 碼> |
| GUI 無帳號 smoke | PASS/FAIL | <觀察摘要> |
| 公開頻道單支下載與冪等 | PASS/FAIL/BLOCKED | <不含頻道帳號資訊的摘要> |
| 已授權內容 | PASS/FAIL/BLOCKED | <只記授權狀態與結果> |
| 批次／字幕／ffmpeg | PASS/FAIL/BLOCKED | <受影響情境> |
| 清理 | PASS/BLOCKED | <已確認的本機測試產物範圍> |
```

本文件只保留最新驗收狀態；程式問題、修復 commit 與後續建議則更新至根目錄的 `REPO_REVIEW.md`。
