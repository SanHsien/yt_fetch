# 專案覆核與建議

覆核日期：2026-07-12（Asia/Taipei）
覆核基準：`main` / GitHub `origin/main` `984e37b1d12b3cb20324e94e4e3c87f1a02441bb`（v1.9.1）

## 結論

專案的基礎品質良好：CLI、GUI、受控登入、發行與文件入口都有明確責任分工，且本地自動化檢查完整通過。不過目前有兩項行為和專案宣告的存取邊界不一致，應在下一次功能修正前優先處理；另一項 cookies 防護可再收緊。

## 本次實測

- `python -m pytest -q`：**102 passed**。
- Black、isort、flake8、`py_compile`：通過。
- `python yt_fetch.py --help`：通過。
- GitHub Actions：最新 `984e37b` 的「程式碼檢查」與「建置 Windows EXE」均成功。
- GitHub Release：`v1.9.1` 已發布，含 Windows zip 與對應 SHA-256 檔。
- 工作樹在寫入本檔前為乾淨狀態；`git diff --check` 通過。

未執行真實下載或登入：這會觸及個人帳號、cookies 與 YouTube 外部服務，應在修正後由有授權帳號以少量影片做人工驗證。

## 優先修正

### P1：已授權會員內容可能在下載前被錯誤排除

`_extract_entries()` 固定以 flat 模式讀清單，但 `filter_downloadable_entries()` 隨即透過 `is_public_video()` 排除任何 `availability != "public"` 的項目。若 yt-dlp 在 flat 清單將會員內容標成 `subscriber_only`（或其他需登入狀態），該影片不會進入實際下載階段，因此也不會使用使用者自己的 cookies 判斷其既有權限。

這和 README、CHANGELOG 對「自己已付費／訂閱的會員影片可在登入後下載」及 v1.7.2「存取權限留到實際下載階段」的說法相衝突。現有會員回填測試的 fake entry 沒有 `availability`，尚未覆蓋這個情境。

建議：將候選篩選拆成「明確不可下載」（私人、刪除、無 ID）與「需要登入才可能可下載」兩類；後者只在已提供合法 cookies 時保留到 yt-dlp 實際驗證，未授權時仍讓 yt-dlp 拒絕並跳過。補上 `availability="subscriber_only"` 的有／無 cookies 回歸測試，以及「不嘗試 private」測試。

### P1：`--channel` 未限制為 YouTube 來源

`normalize_channel_url()` 對任何以 `http` 起始的字串直接原樣回傳，因此 `--channel https://非-youtube-網站/...` 也會交給 yt-dlp。這與專案僅處理使用者指定 YouTube 頻道的宗旨不一致，亦會讓輸出、篩選與著作權提示被誤用到其他站點。

建議：使用 `urllib.parse.urlparse()` 驗證 scheme 為 HTTPS，host 僅允許 `youtube.com`、其子網域及必要的短網址入口；其他 URL 應以明確錯誤拒絕。保留 `@handle` 與 `UC...` 輸入。新增非 YouTube URL、偽造 host（如 `youtube.com.example`）、HTTP 與合法 YouTube playlist／channel URL 測試。

## 後續改善

### P2：受控登入的 CDP 權限與 cookies 最小化

受控 Chrome 以 `--remote-allow-origins=*` 啟動，而 CDP 程式會讀取全部 cookies 並完整寫入本機 `cookies.txt`。目前 remote-debugging port 會由本機隨機連接埠取得，風險較低；但這組設定仍不符合登入憑證應採最小權限的原則。

建議：明確加入 `--remote-debugging-address=127.0.0.1`、移除萬用 origin（自製 WebSocket client 未送 `Origin`，應先驗證不需此旗標）；輸出前只保留 YouTube 登入及下載所需網域的 cookies。另補命令列旗標與 cookie 網域 allowlist 的測試。這是安全強化，不代表目前已知有外洩事件。

### P3：yt-dlp options 有重複鍵值

`build_ytdlp_options()` 中 `retries`、`fragment_retries`、`file_access_retries`、`download_archive`、字幕設定、`progress_hooks` 與 `playlistend` 被重複宣告。Python 會以後面的值覆寫前者，執行結果目前相同，但會增加之後修改一處卻誤以為已生效的風險。

建議：刪除重複區塊，並保留既有 options 建構測試。

### P3：交接文件的測試數過期

`docs/HANDOFF.md` 仍記錄「目前測試數為 96」，本次實測為 102；同檔也留有 v1.3.0 Release 已發布的歷史敘述，和現行 v1.9.1 的交接狀態混在一起。

建議：將測試數更新為 102，並把舊 release 敘述改為「目前 v1.9.1 已發布」或移到 CHANGELOG，讓 HANDOFF 只保留現況與下一步。

## 建議執行順序

1. 先以測試鎖住 P1 的會員 `availability` 與 YouTube URL 邊界，再做最小修正。
2. 使用自己的測試帳號／公開測試頻道，人工確認：公開影片、已授權會員影片、未授權會員影片、私人影片四種結果。
3. 收緊 CDP 旗標與 cookies 網域範圍，重新執行本地檢查與 Windows EXE 建置。
4. 最後同步更新 HANDOFF 與使用者文件，建立新的修正版 Release。
