# 接手狀態

更新日期：2026-06-28

## 專案概況

`yt_fetch` 是 Python CLI，用 `yt-dlp` 從指定 YouTube 頻道下載最新公開影片。專案目前維持單檔架構，主要維護重點是 CLI 穩定性、跨平台安裝、YouTube URL 格式支援、公開影片/Shorts 篩選與冪等下載。

## 目前入口

- 主程式：`yt_fetch.py`
- 測試：`tests/test_smoke.py`
- 使用者文件：`README.md`
- 貢獻文件：`CONTRIBUTING.md`
- 安全文件：`SECURITY.md`
- Agent 指引：`AGENTS.md`、`CLAUDE.md`
- 技能入口：`SKILL.md`

## 本次接手文件補齊

- 新增 `AGENTS.md`：Codex 工作邊界、技術摘要、常用指令。
- 新增 `CLAUDE.md`：Claude Code 工作邊界與開發原則。
- 新增 `SKILL.md`：可重用技能入口。
- 新增 `NOTICE.md`：授權、使用聲明與免責。
- 新增 `docs/ARCHITECTURE.md`：架構與資料流。
- 新增 `docs/DEVELOPMENT.md`：建置、測試、CI 對齊。
- 新增 `docs/third-party-youtube-tooling.md`：第三方工具與風險邊界。

## 已知注意事項

- `download/` 是本機輸出，不進版控。
- cookies 檔案可能含敏感資訊，不能提交。
- 下載真實影片不適合放入自動化測試。
- YouTube 頁面與 yt-dlp 行為會變動，相關 bug 需要先確認 yt-dlp 是否為最新版。
- Python packaging metadata 需要符合新版 setuptools 驗證規則，否則 `pip install -e ".[dev]"` 會失敗。

## 建議下一步

1. 為 `normalize_channel_url()` 補更多輸入格式測試。
2. 為 Shorts 篩選與公開影片判斷補純函式測試。
3. 將下載流程中可測的 yt-dlp option 組裝邏輯抽出，降低真實網路測試需求。
4. 觀察是否需要支援設定檔；目前先維持 CLI 與環境變數。
