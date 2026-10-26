# 安裝說明 / Install guide

## 繁體中文

### 方法一：Chrome 線上應用程式商店（審核通過後）
審核中。通過後會在 README 附上不公開項目的連結，點「加到 Chrome」即可，之後自動更新。

### 方法二：手動載入（搶先測試）
適用 Mac 與 Windows 的桌面版 Chrome（Edge、Brave 等 Chromium 瀏覽器通常也可以）。

1. 從 [Releases](https://github.com/lamb-liver/tft-trait-hover-companion/releases) 下載 `tft-trait-hover-0.4.6.zip`。
2. 解壓縮：
   - **Mac**：在 Finder 雙擊 zip，把產生的資料夾移到固定位置，例如「文件」。
   - **Windows**：在檔案總管對 zip 按右鍵 →「全部解壓縮」，選固定位置，例如「文件」。
3. Chrome 網址列輸入 `chrome://extensions` 並按 Enter。
4. 開啟右上角「開發人員模式」。
5. 按左上角「載入未封裝項目」，選擇含有 `manifest.json` 的資料夾。
6. 建議點工具列的拼圖圖示，把「TFT羈絆提示」釘選到工具列。

注意事項：
- 資料夾之後不要刪除或搬移，否則擴充功能會失效。
- 手動載入不會自動更新。有新版時下載新的 zip、覆蓋同一個資料夾，再到 `chrome://extensions` 按擴充功能卡片上的重新載入。
- Chrome 啟動時可能提示「停用開發人員模式擴充功能」，按保留即可。
- 商店版上架後，建議移除手動載入的版本，改裝商店版。

### 疑難排解
- 角標「!」：拿不到分頁畫面。回到直播分頁再點一次工具列圖示。
- 有「讀」但沒有框：把播放器放大或全螢幕。大廳、選秀等沒有羈絆欄的畫面本來就不顯示。
- 快捷鍵沒反應：到 `chrome://extensions/shortcuts` 設定一次。

### 選用本機程式
0.4.0 起不需要。若要用舊版的本機比對：需要 Python 3.9 以上，在此 repo 資料夾執行
```
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt      # Windows：.venv\Scripts\pip
.venv/bin/python companion.py fetch
.venv/bin/python ebs.py --extension-id <擴充功能 ID>
```
再到擴充功能設定把來源改成「本機 ebs.py（備用）」。

## English

### Option 1: Chrome Web Store (after review)
Under review. The unlisted store link will be added to the README; it updates automatically.

### Option 2: Load unpacked (early testing)
Desktop Chrome on Mac or Windows (other Chromium browsers usually work too).

1. Download `tft-trait-hover-0.4.6.zip` from [Releases](https://github.com/lamb-liver/tft-trait-hover-companion/releases).
2. Unzip: **Mac** – double-click in Finder; **Windows** – right-click → Extract All. Keep the folder somewhere permanent.
3. Open `chrome://extensions`.
4. Turn on **Developer mode**.
5. Click **Load unpacked** and select the folder containing `manifest.json`.

Notes: don't move or delete the folder; unpacked installs don't auto-update (replace the folder and click reload); Chrome may warn about developer-mode extensions at startup – keep it.

### Optional local program
Not needed since 0.4.0. Requires Python 3.9+: create a venv, `pip install -r requirements.txt`, run `companion.py fetch`, then `ebs.py --extension-id <ID>`, and switch the source to "local ebs.py (fallback)" in the extension settings.

---
作者：羊肝（[lambliver.dev](https://lambliver.dev)）。問題回報：[Issues](https://github.com/lamb-liver/tft-trait-hover-companion/issues)
