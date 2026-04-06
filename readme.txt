安裝依賴項：
pip install -r requirements.txt

啟動工具：
pip install streamlit

streamlit run app.py
or
python -m streamlit run app.py



============================================================
GitHub Actions 與 Workflow 自動化部署操作說明書
============================================================
建立日期：2026-04-05
適用系統：macOS / Windows
目的：將本地代碼推送至 GitHub 並啟用 GitHub Actions 自動化執行

------------------------------------------------------------
第一階段：準備 GitHub 存取金鑰 (Token)
------------------------------------------------------------
由於 GitHub 不支援密碼上傳，必須使用 Personal Access Token (PAT)：

1. 登入 GitHub > Settings > Developer settings。
2. 選擇 Personal access tokens > Tokens (classic)。
3. 點擊 Generate new token (classic)。
4. 設定名稱（如：pitt），並務必勾選以下權限：
   - [x] repo (全部)
   - [x] workflow (上傳自動化腳本的關鍵)
5. 點擊產生後，立即複製「ghp_」開頭的代碼並存於備忘錄（離開網頁後將無法再次查看）。

------------------------------------------------------------
第二階段：設定專案 Secrets (API Keys)
------------------------------------------------------------
若程式需要使用外部 API（如 OpenAI），請勿將 Key 寫在程式碼中：

1. 進入 GitHub 倉庫頁面 > Settings。
2. 左側選單：Security > Secrets and variables > Actions。
3. 點擊 New repository secret。
4. Name 輸入變數名稱（例如：OPENAI_API_KEY）。
5. Value 貼入您的 API Key 明文。

------------------------------------------------------------
第三階段：本地 Git 指令上傳流程
------------------------------------------------------------
開啟終端機 (Terminal)，進入專案根目錄執行以下指令：

1. 初始化與提交：
   cd /您的專案路徑/news
   git init
   git add .
   git commit -m "Initial commit with workflow"

2. 設定遠端倉庫網址（包含 Token 以免除重複輸入）：
   git remote add origin https://<您的帳號>:<您的Token>@github.com/<您的帳號>/AItools.git
   # 若已存在 origin，請改用：
   git remote set-url origin https://<您的帳號>:<您的Token>@github.com/<您的帳號>/AItools.git

3. 推送至 GitHub：
   git push -u origin main --force

------------------------------------------------------------
第四階段：驗證與手動執行 Workflow
------------------------------------------------------------
1. 進入 GitHub 倉庫頁面，點擊上方 Actions 分頁。
2. 若路徑正確 (.github/workflows/xxx.yml)，左側會顯示工作流名稱。
3. 手動觸發：
   - 點擊工作流名稱（如：Hourly News Update）。
   - 點擊右側 Run workflow 藍色按鈕。
   - 點擊綠色 Run workflow 確認。
4. 狀態檢查：
   - 黃色轉圈：正在執行 (In progress)。
   - 綠色勾勾：執行成功 (Success)。
   - 紅色叉叉：執行失敗 (Failure)，請點入查看 Error Log。

------------------------------------------------------------
注意事項
------------------------------------------------------------
* 隱藏檔案：在 Mac Finder 中若看不到 .github 資料夾，請按「Command + Shift + .」顯示。
* 權限報錯：若推送時出現 "refusing to update workflow"，代表 Token 沒勾選 workflow 權限。
* 定時延遲：GitHub Actions 的定時任務 (Cron) 通常會有 10-30 分鐘的延遲，屬正常現象。
============================================================
