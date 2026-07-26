# Repo Review

覆核日期：2026-07-26

覆核範圍：`v1.9.2` 發行候選、Windows EXE、GitHub Actions、CodeQL、文件與發佈流程

## 結論

- 先前 review 的兩項 P1 與三項 P2 已修正，沒有仍阻擋 `v1.9.2` 的程式問題。
- `v1.9.2` 適合作為 patch release：修正已授權內容候選被提早排除、安全收緊、依賴更新與
  CI／Release 工具鏈維護，沒有不相容介面變更。
- 自動測試、本機候選 EXE 與 GitHub 掃描均已重驗；真實下載、受控登入與帳號權限情境仍依
  `docs/COMPUTER_USE_VALIDATION.md` 由使用者主持，不能以 mock 或畫面 smoke 代替。

## 已修正問題

### P1：合法 cookies 下的會員／Premium 候選被提早排除

現在只有在實際提供可用 cookies 時，才保留 `subscriber_only`、`premium_only` 與
`needs_auth` 候選交由 YouTube 驗證帳號原有權限；私人與未列出影片仍一律拒絕。cookies
載入失敗回退公開模式後，`match_filter` 與候選準備也會立即恢復為公開內容規則。

- 修復：`ea75f8b`（2026-07-26）
- 回歸：有／無 cookies、私人內容永不嘗試、fallback 與完整下載協調流程

### P1：`--channel` 接受任意 HTTP／外部 URL

完整 URL 現在只接受 HTTPS 的 YouTube host（含 `youtu.be`），並拒絕 HTTP、外部主機、
內嵌帳密、非標準連接埠與無效 port；CLI 會以可理解錯誤與退出碼 2 結束。

- 修復：`ea75f8b`（2026-07-26）
- 回歸：合法 host、惡意相似 host、HTTP、credentials 與 port

### P2：受控 Chrome 與 cookies 權限過寬

Chrome CDP 現在只監聽 `127.0.0.1`，不再使用萬用 remote origin；Netscape cookies 匯出只
保留 `youtube.com`、`google.com`、`googlevideo.com` 及其子網域，排除其他瀏覽 cookies。

- 修復：`5e1715a`（2026-07-26）
- 回歸：loopback 啟動參數、萬用 origin 不存在、允許網域集合與第三方網域排除

### P2：已發布 EXE 的 `yt-dlp` 落後

依賴下限已更新至 `yt-dlp>=2026.7.4`，本機候選 EXE 的 About 也實際顯示內嵌
`yt-dlp 2026.7.4`；`imageio-ffmpeg 0.6.0` 仍為目前最新版。

- 修復：`3cee0f8`（2026-07-26）

### P2：缺少程式碼掃描基線

已新增 Python CodeQL `security-extended` workflow。第一輪掃描正確抓到測試中的三個
`py/incomplete-url-substring-sanitization` high alert；測試改為解析 Netscape 欄位並比較完整
網域集合，不再用 URL 子字串斷言。重新掃描成功，`main` 的 CodeQL open alerts 與 Secret
Scanning open alerts 都是 0。

- workflow：`5e1715a`（2026-07-26）
- alert 修正：`cb550d5`（2026-07-26）
- CodeQL run：`30192709674`
- 程式碼檢查 run：`30192709665`

### 其他本輪修正

- `download/`、CLI 數值邊界、Release ZIP 驗證與桌面驗收基線：`cafb8c6`
  （2026-07-26）。
- GitHub Actions `checkout`／`setup-python` 升級至 v7：`b90816f`
  （2026-07-26）。
- Release workflow 升級 `upload-artifact@v7`、`action-gh-release@v3`：`3cee0f8`
  （2026-07-26）。
- 忽略依賴新鮮度 Markdown 報告，避免維護產物誤入 Git：`acf1f65`
  （2026-07-26）。

## 對先前 review 的更正

- `build_ytdlp_options()` 沒有重複組裝 options；目前只有一個集中建構入口，原「重複設定」屬
  誤判，因此沒有為了對清單而改動程式。
- Tkinter 的 UI Automation tree 仍以容器節點為主，但 Computer Use 可使用每次重抓的畫面
  做安全 fallback。候選 EXE 的最大化繁中／英文畫面、About、表單防呆都已實測，未發現文字
  截斷、重疊或錯誤版本資訊；這是已知工具限制，不是本版 GUI defect。

## 本次驗證

| 類別 | 結果 | 證據 |
| --- | --- | --- |
| pytest | PASS | 136 passed |
| black / isort / flake8 | PASS | 全部通過 |
| py_compile / vermin / CLI help | PASS | vermin 最低需求 3.8，低於專案 3.10 基線 |
| 依賴新鮮度 | PASS | `yt-dlp 2026.7.4`、`imageio-ffmpeg 0.6.0` 均為最新 |
| 本機 PyInstaller 候選 | PASS | `dist/yt_fetch.exe` 成功建置，非空 |
| Windows 無帳號 GUI smoke | PASS | 啟動、繁中／英文切換、About 版本、`count=0` 阻擋、正常結束 |
| GitHub 程式碼檢查 | PASS | run `30192709665` |
| GitHub CodeQL | PASS | run `30192709674`；open alerts 0 |
| GitHub Secret Scanning | PASS | open alerts 0 |
| 真實公開下載與冪等 | BLOCKED | 尚未由使用者提供本輪授權測試頻道 |
| 已授權會員／登入／拒絕情境 | BLOCKED | 必須由使用者親自登入並主持 |

## 發佈與後續 Gate

1. 推送 `v1.9.2` 發行 commit，等 `main` 的程式碼檢查與 CodeQL 通過。
2. 推送 `v1.9.2` tag，等待 Windows Release workflow 完成。
3. 從 GitHub Release 重新下載 ZIP 與 `.sha256`，驗證 SHA-256、CRC、唯一根目錄 EXE 與
   Windows `Expand-Archive`。
4. 依 `docs/COMPUTER_USE_VALIDATION.md` 對「實際 Release 資產」重跑無帳號 GUI smoke。
5. 真實下載與登入情境維持 `BLOCKED`，直到使用者以自己的公開／已授權內容主持驗收。

本文件維持 latest-only；Release 完成後，以實際 run、資產雜湊與桌面驗收結果覆寫上述發佈
狀態，不另保留過期候選結論。
