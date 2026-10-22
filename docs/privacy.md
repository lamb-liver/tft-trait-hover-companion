# 隱私權政策 / Privacy Policy

最後更新：2026-10-22。適用：Chrome 擴充功能「雲頂羈絆提示（TFT Trait Hover）」與搭配的本機程式 `ebs.py`。

## 繁體中文

**一句話：畫面只在你自己的電腦上處理，我們不收集、不上傳、不保存任何個人資料。**

### 會處理什麼
- **分頁畫面**：只有在你按下工具列圖示（或快捷鍵）後，擴充功能才會用 Chrome 的 `tabCapture` 擷取「目前這個」Twitch 或 YouTube 分頁的畫面。每一幀只送到你自己電腦上的 `http://127.0.0.1:8766`（本機 `ebs.py`），在記憶體裡比對完就丟掉，不寫入硬碟，也不會傳到網際網路。比對結果只有時間、圖示編號和框的位置。
- **分頁聲音**：Chrome 擷取分頁時會把分頁靜音，擴充功能只在本機把聲音播回來，不錄音、不傳送。
- **設定**：來源、延遲、頻道名稱、中繼網址存在 `chrome.storage.local`，只在你的瀏覽器裡。
- **主播中繼（選用）**：如果你在設定裡選了「主播中繼」，擴充功能會連到你填的 WebSocket 網址（預設為作者架設的中繼），只**接收**主播送出的圖示編號與框，不會送出你的畫面或瀏覽紀錄。中繼伺服器和一般網站一樣，連線時會看到你的 IP 位址。中繼程式本身不記錄它；中繼架在 Cloudflare Workers 上，Cloudflare 可能依其[隱私權政策](https://www.cloudflare.com/privacypolicy/)處理連線紀錄。

### 不會做的事
- 不收集姓名、帳號、Email、瀏覽紀錄、Cookie 或任何可識別個人的資料。
- 不使用分析工具、不放廣告、不出售或分享資料給第三方。
- 不顯示勝率、平均名次、推薦或對手資訊。

### 資料使用聲明
擴充功能取得的資料只用於上述單一用途（在播放器上顯示羈絆與海克斯的名稱與公開敘述），並遵守 Chrome Web Store 使用者資料政策，包括「有限使用」（Limited Use）規定。

### 聯絡
問題請在 https://github.com/lamb-liver/tft-trait-hover-companion/issues 回報。

## English

**In short: frames are processed only on your own computer. We do not collect, upload or store personal data.**

### What is processed
- **Tab frames**: only after you click the toolbar icon (or press the shortcut) does the extension use Chrome `tabCapture` on the current Twitch or YouTube tab. Each frame is sent only to `http://127.0.0.1:8766` on your own computer (the local `ebs.py`), matched in memory and discarded. Nothing is written to disk or sent to the internet. The result is only a time, icon ids and box positions.
- **Tab audio**: Chrome mutes a captured tab; the extension plays the audio back locally. It is not recorded or sent.
- **Settings**: source, delay, channel name and relay URL are kept in `chrome.storage.local`, in your browser only.
- **Streamer relay (optional)**: if you choose the relay source, the extension connects to the WebSocket URL you set (by default a relay run by the author) and only **receives** icon ids and boxes sent by the streamer. It does not send your frames or browsing history. Like any server, the relay sees your IP address when you connect. The relay code does not log it; the relay runs on Cloudflare Workers, and Cloudflare may process connection logs under its [privacy policy](https://www.cloudflare.com/privacypolicy/).

### What we do not do
- No names, accounts, e-mail, browsing history, cookies or other personally identifiable data.
- No analytics, no ads, no sale or sharing of data with third parties.
- No win rates, average placements, recommendations or opponent information.

### Limited Use
The use of information received by this extension is limited to the single purpose above (showing trait and augment names and public descriptions on the player) and adheres to the Chrome Web Store User Data Policy, including the Limited Use requirements.

### Contact
https://github.com/lamb-liver/tft-trait-hover-companion/issues
