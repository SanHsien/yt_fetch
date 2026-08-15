# CLAUDE.md

Claude Code 在本專案工作時，先讀 [`AGENTS.md`](AGENTS.md)。專案定位、安全邊界、架構、REVIEW 規則與驗證方式都以 `AGENTS.md` 為唯一主要規則來源；本檔只補 Claude Code 的工作習慣。

## 回覆與修改原則

- 使用繁體中文，先說明改了什麼、驗證了什麼。
- 小步修改，不因為能重構就重構。
- 涉及 CLI 參數、URL 正規化、候選影片篩選、cookies 或授權存取判斷時，必須補或更新對應測試。
- GUI 修改若無法在 Windows 實機開啟驗證，要明確標示未驗證範圍。
- 不要把 `REPO_REVIEW.md` 當成一般 bug ledger；依 `AGENTS.md` 的 REVIEW / CHANGELOG 規則處理。

## 高風險區

修改以下區域前先讀相關文件：

- cookies / 受控登入：`SECURITY.md`、`chrome_cdp_cookies.py`
- Windows GUI / Release：`docs/COMPUTER_USE_VALIDATION.md`
- 打包與發行：`docs/RELEASING.md`
- 架構與核心資料流：`docs/ARCHITECTURE.md`

完成後至少執行與變更範圍相符的 pytest；格式與 lint 指令見 `AGENTS.md`。
