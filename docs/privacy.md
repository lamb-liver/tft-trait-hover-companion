# 隱私權政策 / Privacy Policy

最後更新：2026-10-24。適用：Chrome 擴充功能「TFT羈絆提示（TFT Trait Hover）」0.4.0 起的版本（0.4.1 起名稱為 TFT羈絆提示），以及選用的本機程式 `ebs.py`。

## 繁體中文

**一句話：畫面只在你的瀏覽器裡比對，不離開你的電腦。我們不收集、不上傳、不保存任何個人資料。**

### 會處理什麼
- **分頁畫面**：只有在你按下工具列圖示（或快捷鍵）後，擴充功能才會用 Chrome 的 `tabCapture` 擷取「目前這個」Twitch 或 YouTube 分頁的畫面。預設在擴充功能內部（瀏覽器裡的 WebAssembly）比對，每一幀在記憶體裡比對完就丟掉，不寫入硬碟，也不送到任何伺服器。比對結果只有圖示編號和框的位置。
- **選用的本機程式**：只有在設定裡把來源改成「本機 ebs.py（備用）」時，畫面才會送到你自己電腦上的 `http://127.0.0.1:8766`（本機回送位址，不經網路），同樣在記憶體比對後丟掉。
- **分頁聲音**：Chrome 擷取分頁時會把分頁靜音，擴充功能只在本機把聲音播回來，不錄音、不傳送。
- **設定**：來源、延遲、頻道名稱、中繼網址存在 `chrome.storage.local`，只在你的瀏覽器裡。
- **實況主中繼（選用，預設關閉）**：選了「實況主中繼」時，擴充功能會連到你填的 WebSocket 網址（預設為作者架設的中繼），只**接收**實況主送出的圖示編號與框，不送出你的畫面或瀏覽紀錄。中繼伺服器連線時會看到你的 IP 位址；中繼程式不記錄它，但中繼架在 Cloudflare Workers 上，Cloudflare 可能依其[隱私權政策](https://www.cloudflare.com/privacypolicy/)處理連線紀錄。

### 不會做的事
- 不收集姓名、帳號、Email、瀏覽紀錄、Cookie 或任何可識別個人的資料。
- 不使用分析工具、不放廣告、不出售或分享資料給第三方。
- 只顯示遊戲內的名稱與公開敘述，不做推薦、不追蹤對手。

### 資料使用聲明
擴充功能取得的資料只用於單一用途（在播放器上顯示羈絆與海克斯的名稱與公開敘述），並遵守 Chrome Web Store 使用者資料政策，包括「有限使用」（Limited Use）規定。

### 聯絡
https://github.com/lamb-liver/tft-trait-hover-companion/issues

## English

**In short: frames are matched inside your browser and never leave your computer. We do not collect, upload or store personal data.**

### What is processed
- **Tab frames**: only after you click the toolbar icon (or press the shortcut) does the extension use Chrome `tabCapture` on the current Twitch or YouTube tab. By default each frame is matched inside the extension (WebAssembly in your browser), in memory, and discarded. Nothing is written to disk or sent to any server. The result is only icon ids and box positions.
- **Optional local program**: only if you switch the source to "local ebs.py (fallback)" are frames sent to `http://127.0.0.1:8766` on your own computer (loopback, never the network), where they are matched in memory and discarded.
- **Tab audio**: Chrome mutes a captured tab; the extension plays it back locally. It is not recorded or sent.
- **Settings**: source, delay, channel name and relay URL stay in `chrome.storage.local` in your browser.
- **Streamer relay (optional, off by default)**: if you choose the relay source, the extension connects to the WebSocket URL you set (by default a relay run by the author) and only **receives** icon ids and boxes sent by the streamer. It never sends your frames or browsing history. The relay sees your IP address when you connect; the relay code does not log it, but it runs on Cloudflare Workers, and Cloudflare may process connection logs under its [privacy policy](https://www.cloudflare.com/privacypolicy/).

### What we do not do
- No names, accounts, e-mail, browsing history, cookies or other personally identifiable data.
- No analytics, no ads, no sale or sharing of data with third parties.
- Only in-game names and public descriptions; no recommendations or opponent tracking.

### Limited Use
The use of information received by this extension is limited to the single purpose above (showing trait and augment names and public descriptions on the player) and adheres to the Chrome Web Store User Data Policy, including the Limited Use requirements.

### Contact
https://github.com/lamb-liver/tft-trait-hover-companion/issues
