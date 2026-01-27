# 貢獻指南

感謝您對 yt_fetch 專案的關注！我們歡迎各種形式的貢獻。

## 如何貢獻

### 回報問題

如果您發現了 bug 或有改進建議，請：

1. 先檢查 [Issues](https://github.com/SanHsien/yt_fetch/issues) 確認問題尚未被回報
2. 使用 [Bug 回報模板](https://github.com/SanHsien/yt_fetch/issues/new?template=bug_report.md) 建立新的 Issue
3. 提供詳細的錯誤訊息、重現步驟和環境資訊

### 提出功能建議

1. 使用 [功能建議模板](https://github.com/SanHsien/yt_fetch/issues/new?template=feature_request.md) 建立新的 Issue
2. 清楚描述功能的使用情境和預期行為

### 提交程式碼

1. **Fork 專案**
   ```bash
   # 在 GitHub 上 Fork 專案
   ```

2. **建立分支**
   ```bash
   git clone https://github.com/您的用戶名/yt_fetch.git
   cd yt_fetch
   git checkout -b feature/您的功能名稱
   # 或
   git checkout -b fix/修復的問題描述
   ```

3. **進行修改**
   - 遵循現有的程式碼風格
   - 添加必要的註解
   - 確保程式碼可以正常執行

4. **提交變更**
   ```bash
   git add .
   git commit -m "描述您的變更"
   git push origin feature/您的功能名稱
   ```

5. **建立 Pull Request**
   - 在 GitHub 上建立 Pull Request
   - 使用 [PR 模板](https://github.com/SanHsien/yt_fetch/compare) 填寫詳細說明
   - 確保所有檢查都通過（本地與 CI）

## 程式碼規範

### Python 風格

- 使用 4 個空格縮排（不使用 Tab）
- 遵循 PEP 8 風格指南
- 函數和類別使用有意義的名稱
- 添加必要的 docstring

### 提交訊息規範

使用清晰的提交訊息：

```
類型: 簡短描述

詳細說明（可選）
```

類型包括：
- `feat`: 新功能
- `fix`: Bug 修復
- `docs`: 文件更新
- `style`: 程式碼格式（不影響功能）
- `refactor`: 重構
- `test`: 測試相關
- `chore`: 建置/工具相關

範例：
```
feat: 添加批次下載多個頻道的功能

- 支援從檔案讀取頻道清單
- 添加進度顯示
- 更新 README 文件
```

## 測試

在提交 PR 前，請確保：

- [ ] 程式碼在 Python 3.7+ 上可以正常執行
- [ ] 已測試相關功能
- [ ] 沒有引入新的錯誤或警告
- [ ] 文件已更新（如果適用）

建議在本地執行以下指令來對齊 CI：

```bash
# 安裝開發工具（若尚未安裝）
python -m pip install pytest black isort flake8

# 執行測試與基本程式碼檢查
pytest -q
black --check yt_fetch.py
isort --check-only yt_fetch.py
flake8 yt_fetch.py
```

## 審查流程

1. 提交 PR 後，GitHub Actions 會自動執行檢查
2. 維護者會審查您的程式碼
3. 可能需要根據回饋進行修改
4. 審查通過後，變更會被合併到主分支

## 問題？

如果您有任何問題，請：

- 在 [Issues](https://github.com/SanHsien/yt_fetch/issues) 中提問
- 查看現有的文件和範例

再次感謝您的貢獻！🎉

